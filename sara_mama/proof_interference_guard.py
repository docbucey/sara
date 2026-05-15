#!/usr/bin/env python3
"""Proof interference guard for Mama scientific runs.

Usage:
  python proof_interference_guard.py init
  python proof_interference_guard.py check
  python proof_interference_guard.py status

This tool snapshots hashes of proof-critical files and detects drift.
If drift is detected during proof mode, exit code is non-zero.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _base_dir() -> str:
    return os.path.dirname(__file__)


def _logs_dir() -> str:
    d = os.path.join(_base_dir(), "logs")
    os.makedirs(d, exist_ok=True)
    return d


def _baseline_path() -> str:
    return os.path.join(_logs_dir(), "proof_guard_baseline.json")


def _manifest_path() -> str:
    return os.path.join(_base_dir(), "proof_guard_manifest.json")


def _default_manifest() -> Dict[str, List[str]]:
    return {
        "proof_files": [
            "sara_mamagen1.py",
            "sara_pillar_control_io_entrygen1.py",
            "sara_mama_spec_sheet.mak",
            "ai_llc/plainjainllm.slam",
            "ai_llc/deepseeker_coder_bridge.slam",
        ]
    }


def _ensure_manifest() -> Dict[str, List[str]]:
    mp = _manifest_path()
    if not os.path.exists(mp):
        with open(mp, "w", encoding="utf-8") as f:
            json.dump(_default_manifest(), f, indent=2)
    with open(mp, "r", encoding="utf-8") as f:
        return json.load(f)


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _collect_hashes() -> Dict[str, str]:
    mf = _ensure_manifest()
    out: Dict[str, str] = {}
    for rel in mf.get("proof_files", []):
        abs_path = os.path.join(_base_dir(), rel)
        if os.path.exists(abs_path):
            out[rel] = _sha256(abs_path)
        else:
            out[rel] = "MISSING"
    return out


def cmd_init() -> int:
    data = {
        "ts": _iso_now(),
        "mode": "proof",
        "hashes": _collect_hashes(),
    }
    with open(_baseline_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"baseline_written={_baseline_path()}")
    return 0


def cmd_check() -> int:
    bp = _baseline_path()
    if not os.path.exists(bp):
        print("baseline_missing: run init first")
        return 2

    with open(bp, "r", encoding="utf-8") as f:
        baseline = json.load(f)

    current = _collect_hashes()
    old = baseline.get("hashes", {})

    changed = []
    for rel, old_hash in old.items():
        new_hash = current.get(rel, "MISSING")
        if new_hash != old_hash:
            changed.append({"file": rel, "was": old_hash, "now": new_hash})

    if changed:
        print("proof_guard=FAIL")
        print(json.dumps({"changed": changed}, indent=2))
        return 1

    print("proof_guard=PASS")
    return 0


def cmd_status() -> int:
    bp = _baseline_path()
    mp = _manifest_path()
    print(json.dumps({
        "baseline_exists": os.path.exists(bp),
        "baseline_path": bp,
        "manifest_path": mp,
        "manifest_exists": os.path.exists(mp),
    }, indent=2))
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    cmd = sys.argv[1].lower().strip()
    if cmd == "init":
        return cmd_init()
    if cmd == "check":
        return cmd_check()
    if cmd == "status":
        return cmd_status()
    print(f"unknown_command={cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
