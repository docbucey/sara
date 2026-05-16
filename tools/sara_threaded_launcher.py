#!/usr/bin/env python3
"""
Local-only helper: start SARA CONTROL HTTP in a background thread and (optionally)
ping /health on another thread. Not part of pillar routing — dev / tray convenience.

  python tools/sara_threaded_launcher.py
  python tools/sara_threaded_launcher.py --root "C:\\Users\\you\\Documents\\coding projects\\SARA"

Requires: same Python env you use for SARA (venv recommended). Stops on Ctrl+C.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path


def _default_sara_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _health_worker(host: str, port: int, stop: threading.Event) -> None:
    url = f"http://{host}:{port}/health"
    # Wait for server to bind
    time.sleep(2.0)
    while not stop.is_set():
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                body = resp.read(512).decode("utf-8", errors="replace")
                status = resp.status
            print(f"[launcher] health OK ({status}): {body[:120]!r}")
        except (urllib.error.URLError, OSError) as e:
            print(f"[launcher] health not ready: {e}")
        if stop.wait(timeout=10.0):
            break


def main() -> int:
    ap = argparse.ArgumentParser(description="Threaded local launcher for SARA CONTROL HTTP.")
    ap.add_argument("--root", type=Path, default=None, help="SARA repo root (default: parent of tools/)")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=5050)
    ap.add_argument("--no-health", action="store_true", help="Do not start /health polling thread")
    args = ap.parse_args()

    root = (args.root or _default_sara_root()).resolve()
    script = root / "sara_control" / "server_con.py"
    if not script.is_file():
        print(f"Missing server script: {script}", file=sys.stderr)
        return 1

    venv_py = root / "venv" / "Scripts" / "python.exe"
    exe = str(venv_py) if venv_py.is_file() else sys.executable

    proc_holder: dict[str, subprocess.Popen | None] = {"p": None}
    stop = threading.Event()

    def run_server() -> None:
        proc_holder["p"] = subprocess.Popen(
            [exe, str(script), "--http"],
            cwd=str(root),
        )
        code = proc_holder["p"].wait()
        print(f"[launcher] server process exited code={code}")
        stop.set()

    th_server = threading.Thread(target=run_server, name="sara-http-server", daemon=False)
    th_server.start()

    th_health: threading.Thread | None = None
    if not args.no_health:
        th_health = threading.Thread(
            target=_health_worker,
            args=(args.host, args.port, stop),
            name="sara-health-poll",
            daemon=True,
        )
        th_health.start()

    print(f"[launcher] started HTTP thread; root={root}")
    print(f"[launcher] try  http://{args.host}:{args.port}/health")
    try:
        while th_server.is_alive():
            time.sleep(0.25)
    except KeyboardInterrupt:
        print("\n[launcher] Ctrl+C — terminating server…")
        p = proc_holder.get("p")
        if p is not None and p.poll() is None:
            p.terminate()
            try:
                p.wait(timeout=8)
            except subprocess.TimeoutExpired:
                p.kill()
        stop.set()
        th_server.join(timeout=10)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
