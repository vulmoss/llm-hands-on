"""Loopback-only teaching app. Every record, session and internal service is synthetic."""

import html
import json
import secrets
import sqlite3
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from urllib.request import ProxyHandler, build_opener

FRONTEND = Path(__file__).resolve().parents[3] / "05-security/web-ai-course/frontend"
SESSIONS = {"alice-lab": "alice", "bob-lab": "bob"}
ORDERS = {"1": {"owner": "alice", "item": "A-book"}, "2": {"owner": "bob", "item": "B-book"}}


class App:
    def __init__(self, fixed=False):
        self.fixed = fixed
        self.profile = {"name": "Alice", "role": "reader"}
        self.email = "alice@example.test"
        self.files = {"readme.txt": "public", "../private.txt": "LAB_PRIVATE_MARKER"}
        self.objects = {"public.txt": "public", "private.txt": "LAB_OBJECT_MARKER"}
        self.oauth_states = {}
        self.lock = threading.Lock()
        self.internal_url = ""

    def handle(self, method, target, headers, body):
        parts = urlsplit(target)
        query = parse_qs(parts.query, keep_blank_values=True)
        value = lambda name, default="": query.get(name, [default])[0]  # noqa: E731
        cookie = headers.get("Cookie", "")
        session = dict(item.strip().split("=", 1) for item in cookie.split(";") if "=" in item).get(
            "sid", ""
        )
        user = SESSIONS.get(session)
        response_headers = {"Content-Type": "application/json"}

        def reply(status, result):
            return status, response_headers, json.dumps(result, ensure_ascii=False).encode()

        if parts.path == "/health":
            return reply(
                200, {"lab": "web-ai-course", "mode": "fixed" if self.fixed else "vulnerable"}
            )
        if parts.path == "/login":
            response_headers["Set-Cookie"] = "sid=alice-lab; HttpOnly; SameSite=Lax; Path=/"
            return reply(200, {"note": "Synthetic Alice session, not production authentication"})
        if parts.path.startswith("/frontend/") and method == "GET":
            name = parts.path.removeprefix("/frontend/") or "index.html"
            allowed = {"index.html", "app.js", "app.js.map", "lazy.js"}
            if name not in allowed or not (FRONTEND / name).is_file():
                return reply(404, {"error": "fixture not found"})
            response_headers["Content-Type"] = (
                "text/html; charset=utf-8" if name.endswith(".html") else "application/javascript"
            )
            return 200, response_headers, (FRONTEND / name).read_bytes()
        if parts.path == "/orders" and method == "GET":
            order = ORDERS.get(value("id"))
            if not user:
                return reply(401, {"error": "login required"})
            if not order:
                return reply(404, {"error": "missing"})
            if self.fixed and order["owner"] != user:
                return reply(403, {"error": "owner mismatch"})
            return reply(200, order)
        if parts.path == "/profile" and method == "POST":
            if not user:
                return reply(401, {"error": "login required"})
            if self.fixed and set(body) - {"name"}:
                return reply(400, {"error": "unknown writable field"})
            self.profile.update(body)
            return reply(200, self.profile)
        if parts.path == "/search" and method == "GET":
            with sqlite3.connect(":memory:") as db:
                db.executescript(
                    "CREATE TABLE notes(title TEXT, published INT);"
                    "INSERT INTO notes VALUES('public',1),('LAB_DRAFT_MARKER',0);"
                )
                term = value("q")
                if self.fixed:
                    rows = db.execute(
                        "SELECT title FROM notes WHERE published=1 AND title=?", (term,)
                    ).fetchall()
                else:
                    try:
                        rows = db.execute(
                            f"SELECT title FROM notes WHERE published=1 AND title='{term}'"
                        ).fetchall()
                    except sqlite3.Error:
                        return reply(400, {"error": "query failed"})
            return reply(200, {"titles": [row[0] for row in rows]})
        if parts.path == "/reflect" and method == "GET":
            response_headers["Content-Type"] = "text/html; charset=utf-8"
            text = value("q")
            if self.fixed:
                text = html.escape(text)
            return 200, response_headers, ("<!doctype html><p>" + text + "</p>").encode()
        if parts.path == "/email" and method == "POST":
            if not user:
                return reply(401, {"error": "login required"})
            if self.fixed and (
                headers.get("Origin") != "http://" + headers.get("Host", "")
                or headers.get("X-CSRF-Token") != "lab-csrf-alice"
            ):
                return reply(403, {"error": "CSRF check failed"})
            self.email = body.get("email", self.email)
            return reply(200, {"email": self.email})
        if parts.path == "/cors" and method in {"GET", "OPTIONS"}:
            origin = headers.get("Origin", "")
            if origin and (not self.fixed or origin == "https://dashboard.example.test"):
                response_headers.update(
                    {
                        "Access-Control-Allow-Origin": origin,
                        "Access-Control-Allow-Credentials": "true",
                        "Vary": "Origin",
                    }
                )
            return reply(200, {"note": "Browser enforces CORS; curl does not"})
        if parts.path == "/redirect" and method == "GET":
            target_url = value("next", "/frontend/index.html")
            if self.fixed and target_url not in {"/frontend/index.html", "/health"}:
                return reply(400, {"error": "destination not allowed"})
            if "\r" in target_url or "\n" in target_url:
                return reply(400, {"error": "invalid header"})
            response_headers["Location"] = target_url
            return reply(302, {"redirect": target_url})
        if parts.path == "/oauth/start" and method == "GET":
            if not user:
                return reply(401, {"error": "login required"})
            state = secrets.token_urlsafe(16)
            self.oauth_states[session] = state
            return reply(200, {"state": state, "note": "state-only model; no real IdP"})
        if parts.path == "/oauth/callback" and method == "GET":
            if self.fixed and (
                not user
                or session not in self.oauth_states
                or not secrets.compare_digest(value("state"), self.oauth_states[session])
            ):
                return reply(403, {"error": "state/session/replay rejected"})
            if value("code") != "lab-code":
                return reply(400, {"error": "synthetic code required"})
            self.oauth_states.pop(session, None)
            return reply(200, {"linked": "lab-account"})
        if parts.path == "/fetch" and method == "GET":
            service = value("service", "public")
            if service not in {"public", "internal"}:
                return reply(400, {"error": "only two built-in lab services exist"})
            if self.fixed and service != "public":
                return reply(403, {"error": "service denied"})
            if service == "public":
                return reply(200, {"content": "public fixture"})
            # Real HTTP to our ephemeral callback; never accepts a caller supplied URL.
            with build_opener(ProxyHandler({})).open(self.internal_url, timeout=3) as response:
                return reply(200, {"content": response.read(1000).decode()})
        if parts.path == "/download" and method == "GET":
            name = value("name")
            if self.fixed and name not in {"readme.txt"}:
                return reply(403, {"error": "file not allowed"})
            if name not in self.files:
                return reply(404, {"error": "missing"})
            return reply(200, {"content": self.files[name]})
        if parts.path == "/upload" and method == "POST":
            name = body.get("name", "")
            content = body.get("content", "")
            if not isinstance(name, str) or not isinstance(content, str):
                return reply(400, {"error": "string fields required"})
            if self.fixed and ("/" in name or "\\" in name or not name.endswith(".txt")):
                return reply(400, {"error": "plain text basename required"})
            # Virtual filesystem: no uploaded content is executed or written to the OS.
            self.files[name] = content
            return reply(201, {"name": name, "bytes": len(content.encode())})
        if parts.path == "/objects" and method == "GET":
            name = value("key")
            if self.fixed and name != "public.txt" and user != "alice":
                return reply(403, {"error": "private object"})
            if name not in self.objects:
                return reply(404, {"error": "missing"})
            return reply(200, {"content": self.objects[name]})
        if parts.path == "/checkout" and method == "POST":
            qty = body.get("quantity", 1)
            if type(qty) is not int or (self.fixed and not 1 <= qty <= 10):
                return reply(400, {"error": "quantity must be integer 1..10"})
            price = 100 if self.fixed else body.get("unit_price", 100)
            if type(price) is not int:
                return reply(400, {"error": "integer price required"})
            return reply(200, {"total": qty * price, "unit": "cents", "charged": False})
        return reply(404, {"error": "unknown route"})


def make_handler(app):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_GET(self):
            self.dispatch()

        def do_POST(self):
            self.dispatch()

        def do_OPTIONS(self):
            self.dispatch()

        def dispatch(self):
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if size < 0 or size > 16384:
                    raise ValueError("body size")
                body = json.loads(self.rfile.read(size)) if size else {}
                if not isinstance(body, dict):
                    raise ValueError("object body required")
                with app.lock:
                    status, headers, content = app.handle(
                        self.command, self.path, self.headers, body
                    )
            except (ValueError, UnicodeError):
                status, headers, content = 400, {}, b'{"error":"invalid request"}'
            self.send_response(status)
            for key, value in headers.items():
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

    return Handler


@contextmanager
def running(fixed=False, port=0):
    class Internal(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"LAB_INTERNAL_MARKER")

    internal = ThreadingHTTPServer(("127.0.0.1", 0), Internal)
    it = threading.Thread(target=lambda: internal.serve_forever(poll_interval=0.05), daemon=True)
    it.start()
    app = App(fixed)
    app.internal_url = f"http://127.0.0.1:{internal.server_port}/"
    server = None
    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(app))
        thread = threading.Thread(
            target=lambda: server.serve_forever(poll_interval=0.05), daemon=True
        )
        thread.start()
        yield f"http://127.0.0.1:{server.server_port}", app
    finally:
        if server:
            server.shutdown()
            server.server_close()
            thread.join()
        internal.shutdown()
        internal.server_close()
        it.join()
