#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter
from typing import Any, Dict, Iterable, List


def _default_ledger_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, "..", "logs", "plainjain_replay_ledger.ndjson"))


def _load_entries(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except Exception:
                continue
            if isinstance(item, dict):
                rows.append(item)
    return rows


def _match(entry: Dict[str, Any], field: str, value: str) -> bool:
    return str(entry.get(field, "")).strip() == value


def _filter_entries(
    entries: Iterable[Dict[str, Any]],
    replay_key: str,
    correlation_id: str,
    prompt_hash: str,
    output_hash: str,
) -> List[Dict[str, Any]]:
    filtered: List[Dict[str, Any]] = []
    for entry in entries:
        if replay_key and not _match(entry, "replay_key", replay_key):
            continue
        if correlation_id and not _match(entry, "correlation_id", correlation_id):
            continue
        if prompt_hash and not str(entry.get("prompt_hash", "")).startswith(prompt_hash):
            continue
        if output_hash and not str(entry.get("output_hash", "")).startswith(output_hash):
            continue
        filtered.append(entry)
    return filtered


def _build_summary(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not entries:
        return {
            "count": 0,
            "continuity_score": 0.0,
            "message": "no matching entries",
        }

    output_hashes = [str(e.get("output_hash", "")) for e in entries if e.get("output_hash")]
    profile_counts = Counter(str(e.get("selected_profile", "")) for e in entries)
    mode_counts = Counter(str(e.get("executor_mode", "")) for e in entries)

    unique_outputs = len(set(output_hashes)) if output_hashes else 0
    continuity_score = 1.0 if len(entries) <= 1 else (1.0 / max(1, unique_outputs))

    return {
        "count": len(entries),
        "unique_output_hashes": unique_outputs,
        "continuity_score": round(float(continuity_score), 4),
        "profiles": dict(profile_counts),
        "executor_modes": dict(mode_counts),
        "latest_ts": str(entries[-1].get("ts", "")),
    }


def _write_csv(path: str, rows: List[Dict[str, Any]]) -> str:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    fieldnames = [
        "ts",
        "engine",
        "correlation_id",
        "machine_profile_id",
        "selected_profile",
        "executor_mode",
        "probabilistic_enabled",
        "replay_mode",
        "replay_key",
        "replay_seed",
        "seed_used",
        "prompt_hash",
        "output_hash",
        "token_count",
        "unique_token_count",
    ]
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Query plainjain replay ledger records.")
    parser.add_argument("--ledger", default=_default_ledger_path(), help="Path to replay ledger NDJSON file")
    parser.add_argument("--replay-key", default="", help="Exact replay_key filter")
    parser.add_argument("--correlation-id", default="", help="Exact correlation_id filter")
    parser.add_argument("--prompt-hash", default="", help="Prompt hash prefix filter")
    parser.add_argument("--output-hash", default="", help="Output hash prefix filter")
    parser.add_argument("--limit", type=int, default=20, help="Max records to return")
    parser.add_argument("--latest-first", action="store_true", help="Sort descending by ts")
    parser.add_argument("--summary-only", action="store_true", help="Print summary only")
    parser.add_argument("--csv", default="", help="Optional CSV output path for selected records")
    args = parser.parse_args()

    entries = _load_entries(args.ledger)
    filtered = _filter_entries(
        entries,
        replay_key=str(args.replay_key or "").strip(),
        correlation_id=str(args.correlation_id or "").strip(),
        prompt_hash=str(args.prompt_hash or "").strip(),
        output_hash=str(args.output_hash or "").strip(),
    )

    filtered.sort(key=lambda x: str(x.get("ts", "")), reverse=bool(args.latest_first))

    summary = _build_summary(filtered)
    limit = max(1, int(args.limit))
    selected = filtered[:limit]

    csv_path = str(args.csv or "").strip()
    csv_written = ""
    if csv_path:
        csv_written = _write_csv(csv_path, selected)

    if args.summary_only:
        payload: Dict[str, Any] = {"ledger": args.ledger, "summary": summary}
        if csv_written:
            payload["csv"] = csv_written
        print(json.dumps(payload, indent=2))
        return 0

    payload = {"ledger": args.ledger, "summary": summary, "records": selected}
    if csv_written:
        payload["csv"] = csv_written
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
