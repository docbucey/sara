"""
Exit 0 if CONTROL dispatch loads (same import chain as /health needs).
Run from SARA repo root: python verify_dispatch.py
"""
from __future__ import annotations

import os
import sys
import traceback


def main() -> int:
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)
    if root not in sys.path:
        sys.path.insert(0, root)
    try:
        from sara_control.dispatch_con import dispatch  # noqa: F401

        print("OK: dispatch_con imported (CONTROL can load).")
        return 0
    except Exception:
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
