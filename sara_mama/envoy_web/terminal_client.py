#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import urllib.request
import urllib.error


BASE_URL = "http://127.0.0.1:8787"


def _post(path: str, payload: dict, token: str = "") -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        BASE_URL + path,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-SARA-Token": token,
        },
    )
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        try:
            payload = json.loads(body)
        except Exception:
            payload = {"error": body or str(e)}
        return {"success": False, "http_status": e.code, "response": payload}


def _get(path: str, token: str = "") -> dict:
    req = urllib.request.Request(
        BASE_URL + path,
        method="GET",
        headers={"X-SARA-Token": token},
    )
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        try:
            payload = json.loads(body)
        except Exception:
            payload = {"error": body or str(e)}
        return {"success": False, "http_status": e.code, "response": payload}


def main() -> int:
    if len(sys.argv) < 2:
        print("usage:")
        print("  terminal_client.py login <username> <password>")
        print("  terminal_client.py health <token>")
        print("  terminal_client.py run <token> <prompt>")
        print("  terminal_client.py runs <token>")
        print("  terminal_client.py reveal <token> <run_id> <password>")
        print("  terminal_client.py compare <token> <run_id>")
        return 2

    cmd = sys.argv[1].lower().strip()

    if cmd == "login" and len(sys.argv) >= 4:
        out = _post("/api/login", {"username": sys.argv[2], "password": sys.argv[3]})
        print(json.dumps(out, indent=2))
        return 0

    if cmd == "run" and len(sys.argv) >= 4:
        token = sys.argv[2]
        prompt = " ".join(sys.argv[3:])
        out = _post("/api/run", {"prompt": prompt, "blind_mode": True}, token=token)
        print(json.dumps(out, indent=2))
        return 0

    if cmd == "health" and len(sys.argv) >= 3:
        token = sys.argv[2]
        out = _get("/api/health", token=token)
        print(json.dumps(out, indent=2))
        return 0

    if cmd == "runs" and len(sys.argv) >= 3:
        out = _get("/api/runs", token=sys.argv[2])
        print(json.dumps(out, indent=2))
        return 0

    if cmd == "reveal" and len(sys.argv) >= 5:
        token = sys.argv[2]
        run_id = sys.argv[3]
        password = sys.argv[4]
        out = _post(f"/api/reveal/{run_id}", {"password": password}, token=token)
        print(json.dumps(out, indent=2))
        return 0

    if cmd == "compare" and len(sys.argv) >= 4:
        token = sys.argv[2]
        run_id = sys.argv[3]
        out = _get(f"/api/compare/{run_id}", token=token)
        print(json.dumps(out, indent=2))
        return 0

    print("invalid command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
