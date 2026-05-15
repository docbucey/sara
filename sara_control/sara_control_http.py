"""
sara_control_http.py
SARA CONTROL — HTTP Bridge Server
Wraps control_shunt_entrypoint() in a lightweight HTTP server so external
clients (Smithy/Godot, CLI tools, web UI, test harnesses) can POST BuceyShunt
envelopes and receive JSON responses.

Default: http://127.0.0.1:5050/shunt
Web UI:  http://127.0.0.1:5050/

No external dependencies — uses Python stdlib http.server only.

Usage:
    python sara_control_http.py
    python sara_control_http.py --port 5050 --host 127.0.0.1
"""

import sys
import os
import json
import argparse
import uuid
import traceback
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- Pillar import ---
_HERE = os.path.dirname(os.path.abspath(__file__))
_SARA_ROOT = os.path.dirname(_HERE)
_WEB_DIR = os.path.join(_SARA_ROOT, "sara_web")
if _SARA_ROOT not in sys.path:
    sys.path.insert(0, _SARA_ROOT)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

_CONTROL_LOAD_ERROR = ""
_dispatch_fn = None
_CONTROL_LOADED = False

try:
    from sara_control.dispatch_con import dispatch as _dispatch_fn

    _CONTROL_LOADED = True
except Exception:
    try:
        from .dispatch_con import dispatch as _dispatch_fn

        _CONTROL_LOADED = True
    except Exception:
        try:
            from dispatch_con import dispatch as _dispatch_fn

            _CONTROL_LOADED = True
        except Exception:
            _CONTROL_LOADED = False
            _dispatch_fn = None
            _CONTROL_LOAD_ERROR = traceback.format_exc()

if not _CONTROL_LOADED:
    _short = (_CONTROL_LOAD_ERROR or "unknown")[:2000]
    print("[SARA CONTROL HTTP] WARNING: dispatch import failed. First 2000 chars:")
    print(_short)

# --- Constants ---
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5050
_SERVER_VERSION = "1.0.0"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _error_response(code: int, message: str) -> dict:
    return {
        "success": False,
        "error": message,
        "server": "sara_control_http",
        "timestamp": _iso_now(),
    }


class SaraControlHandler(BaseHTTPRequestHandler):
    """Handles all inbound HTTP requests to the SARA CONTROL bridge."""

    def log_message(self, format, *args):
        pass

    def _cors_headers(self) -> None:
        origin = self.headers.get("Origin", "")
        if origin.startswith("http://127.0.0.1") or origin.startswith("http://localhost"):
            self.send_header("Access-Control-Allow-Origin", origin)
        else:
            self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, status_code: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, filepath: str, content_type: str) -> None:
        try:
            with open(filepath, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self._cors_headers()
            self.end_headers()
            self.wfile.write(body)
        except FileNotFoundError:
            self._send_json(404, _error_response(404, "File not found"))

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        if self.path == "/health":
            body = {
                "status": "ok",
                "server": "sara_control_http",
                "version": _SERVER_VERSION,
                "control_loaded": _CONTROL_LOADED,
                "timestamp": _iso_now(),
            }
            if not _CONTROL_LOADED and _CONTROL_LOAD_ERROR:
                # So clients (and humans) see the real import failure, not guesswork.
                body["control_load_error"] = _CONTROL_LOAD_ERROR[:8000]
            self._send_json(200, body)
        elif self.path in ("/", "/index.html"):
            self._send_file(os.path.join(_WEB_DIR, "index.html"), "text/html; charset=utf-8")
        elif self.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
        else:
            safe = self.path.lstrip("/").replace("..", "")
            candidate = os.path.join(_WEB_DIR, safe)
            if os.path.isfile(candidate) and os.path.commonpath([_WEB_DIR, candidate]) == _WEB_DIR:
                ext_map = {".html": "text/html", ".css": "text/css", ".js": "application/javascript",
                           ".png": "image/png", ".svg": "image/svg+xml", ".ico": "image/x-icon"}
                ext = os.path.splitext(candidate)[1].lower()
                self._send_file(candidate, ext_map.get(ext, "application/octet-stream"))
            else:
                self._send_json(404, _error_response(404, f"Unknown path: {self.path}"))

    def do_POST(self) -> None:
        if self.path != "/shunt":
            self._send_json(404, _error_response(404, f"Unknown path: {self.path}"))
            return

        # --- Read body ---
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            self._send_json(400, _error_response(400, "Empty request body"))
            return

        raw = self.rfile.read(length)
        try:
            envelope = json.loads(raw.decode("utf-8"))
        except Exception as e:
            self._send_json(400, _error_response(400, f"JSON parse error: {e}"))
            return

        # --- Source restriction: only localhost ---
        client_host = self.client_address[0]
        if client_host not in ("127.0.0.1", "::1"):
            self._send_json(403, _error_response(403, "Remote connections not permitted"))
            return

        # --- CONTROL unavailable ---
        if not _CONTROL_LOADED or _dispatch_fn is None:
            self._send_json(503, _error_response(503, f"CONTROL module not loaded: {_CONTROL_LOAD_ERROR}"))
            return

        # --- Extract command and kwargs ---
        command = str(envelope.get("command", envelope.get("intent", "route_io"))).strip()
        auth_token = str(envelope.get("auth_token", ""))

        kwargs = {}
        payload_dict = envelope.get("payload")
        if isinstance(payload_dict, dict):
            kwargs.update(payload_dict)
            kwargs["payload"] = payload_dict
        for k, v in envelope.items():
            if k not in ("command", "intent", "auth_token", "payload",
                         "source_pillar", "target_pillar", "requires_response",
                         "shunt_id", "timestamp", "context_tags"):
                kwargs[k] = v

        # --- Dispatch through FSM ---
        try:
            result = _dispatch_fn(command, auth_token=auth_token, **kwargs)
        except Exception as e:
            self._send_json(500, _error_response(500, f"Dispatch exception: {e}"))
            return

        self._send_json(200, {
            "success": result.get("success", False),
            "timestamp": _iso_now(),
            "result": result,
        })


def run_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    server = HTTPServer((host, port), SaraControlHandler)
    print(f"[SARA CONTROL HTTP] Listening on http://{host}:{port}")
    print(f"[SARA CONTROL HTTP] Web UI:  http://{host}:{port}/")
    print(f"[SARA CONTROL HTTP] API:     http://{host}:{port}/shunt")
    print(f"[SARA CONTROL HTTP] Health:  http://{host}:{port}/health")
    print(f"[SARA CONTROL HTTP] CONTROL loaded: {_CONTROL_LOADED}")
    print("[SARA CONTROL HTTP] Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[SARA CONTROL HTTP] Shutting down.")
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SARA CONTROL HTTP Bridge")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Bind port (default: 5050)")
    args = parser.parse_args()
    run_server(args.host, args.port)
