"""Observed HTTP evidence, independent of AI conclusions."""

import hashlib
import json
import time
from dataclasses import asdict
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from .server import running


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None


def request(base, method, path, headers=None, body=None):
    headers = {k: v.replace("{base}", base) for k, v in (headers or {}).items()}
    payload = None if body is None else json.dumps(body).encode()
    req = Request(base + path, data=payload, method=method, headers=headers)
    if payload is not None:
        req.add_header("Content-Type", "application/json")
    try:
        response = build_opener(ProxyHandler({}), NoRedirect()).open(req, timeout=5)
    except HTTPError as exc:
        response = exc
    with response:
        return {
            "status": response.status,
            "headers": dict(response.headers),
            "body": response.read(32768).decode(),
        }


def check_attack(case, result, fixed):
    if result["status"] != (case.fixed_status if fixed else case.vulnerable_status):
        return False
    if case.marker and ((case.marker in result["body"]) == fixed):
        return False
    if case.id == "cors":
        reflected = result["headers"].get("Access-Control-Allow-Origin") == case.headers["Origin"]
        credentials = result["headers"].get("Access-Control-Allow-Credentials") == "true"
        return (not reflected) if fixed else (reflected and credentials)
    if case.id == "redirect":
        return (
            ("Location" not in result["headers"])
            if fixed
            else result["headers"].get("Location") == "https://other.example.test"
        )
    return True


def run_cases(cases):
    started = time.monotonic()
    records = []
    for case in cases:
        record = {"id": case.id, "title": case.title, "limitation": case.limitation, "modes": {}}
        for fixed in (False, True):
            with running(fixed) as (base, _app):
                result = request(base, case.method, case.path, case.headers, case.body)
                control = request(
                    base,
                    case.control_method,
                    case.control_path,
                    case.control_headers,
                    case.control_body,
                )
            record["modes"]["fixed" if fixed else "vulnerable"] = {
                "request": {
                    "method": case.method,
                    "path": case.path,
                    "body": case.body,
                    "headers": case.headers,
                },
                "response": result,
                "normal_control": control,
                "passed": check_attack(case, result, fixed)
                and control["status"] == case.control_status,
            }
        records.append(record)
    definitions = json.dumps([asdict(c) for c in cases], sort_keys=True).encode()
    return {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "kind": "local-http-controls",
        "cases_sha256": hashlib.sha256(definitions).hexdigest(),
        "seconds": round(time.monotonic() - started, 3),
        "cases": records,
        "passed": all(m["passed"] for r in records for m in r["modes"].values()),
    }
