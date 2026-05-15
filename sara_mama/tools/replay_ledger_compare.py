#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
from typing import Any, Dict, List, Tuple


def _load_entries(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    out: List[Dict[str, Any]] = []
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
                out.append(item)
    return out


def _filter(entries: List[Dict[str, Any]], replay_key: str, correlation_id: str) -> List[Dict[str, Any]]:
    filtered: List[Dict[str, Any]] = []
    for row in entries:
        if replay_key and str(row.get("replay_key", "")).strip() != replay_key:
            continue
        if correlation_id and str(row.get("correlation_id", "")).strip() != correlation_id:
            continue
        filtered.append(row)
    return filtered


def _group_latest_by_prompt_hash(entries: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    latest: Dict[str, Dict[str, Any]] = {}
    entries_sorted = sorted(entries, key=lambda r: str(r.get("ts", "")))
    for row in entries_sorted:
        prompt_hash = str(row.get("prompt_hash", "")).strip()
        if not prompt_hash:
            continue
        latest[prompt_hash] = row
    return latest


def _compare(a_rows: List[Dict[str, Any]], b_rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    a_map = _group_latest_by_prompt_hash(a_rows)
    b_map = _group_latest_by_prompt_hash(b_rows)

    shared = sorted(set(a_map.keys()) & set(b_map.keys()))
    only_a = sorted(set(a_map.keys()) - set(b_map.keys()))
    only_b = sorted(set(b_map.keys()) - set(a_map.keys()))

    comparisons: List[Dict[str, Any]] = []
    exact_matches = 0
    for prompt_hash in shared:
        a = a_map[prompt_hash]
        b = b_map[prompt_hash]
        a_out = str(a.get("output_hash", ""))
        b_out = str(b.get("output_hash", ""))
        match = bool(a_out and b_out and a_out == b_out)
        if match:
            exact_matches += 1
        comparisons.append(
            {
                "prompt_hash": prompt_hash,
                "match": match,
                "a_output_hash": a_out,
                "b_output_hash": b_out,
                "a_seed_used": a.get("seed_used"),
                "b_seed_used": b.get("seed_used"),
                "a_profile": a.get("selected_profile"),
                "b_profile": b.get("selected_profile"),
                "a_executor_mode": a.get("executor_mode"),
                "b_executor_mode": b.get("executor_mode"),
                "a_ts": a.get("ts"),
                "b_ts": b.get("ts"),
            }
        )

    total_shared = len(shared)
    continuity_score = (exact_matches / total_shared) if total_shared else 0.0
    summary = {
        "shared_prompt_hashes": total_shared,
        "exact_hash_matches": exact_matches,
        "cross_device_continuity_score": round(float(continuity_score), 4),
        "only_in_a": len(only_a),
        "only_in_b": len(only_b),
        "only_in_a_hashes": only_a[:20],
        "only_in_b_hashes": only_b[:20],
    }
    return comparisons, summary


def _write_csv(path: str, rows: List[Dict[str, Any]]) -> str:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    fieldnames = [
        "prompt_hash",
        "match",
        "a_output_hash",
        "b_output_hash",
        "a_seed_used",
        "b_seed_used",
        "a_profile",
        "b_profile",
        "a_executor_mode",
        "b_executor_mode",
        "a_ts",
        "b_ts",
    ]
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare replay ledgers across devices (desktop vs ARM).")
    parser.add_argument("--ledger-a", required=True, help="Path to first ledger (desktop)")
    parser.add_argument("--ledger-b", required=True, help="Path to second ledger (arm/wearable)")
    parser.add_argument("--replay-key", default="", help="Optional replay_key filter")
    parser.add_argument("--correlation-id", default="", help="Optional correlation_id filter")
    parser.add_argument("--limit", type=int, default=200, help="Max comparison rows to return")
    parser.add_argument("--summary-only", action="store_true", help="Only print summary")
    parser.add_argument("--csv", default="", help="Optional CSV output path")
    args = parser.parse_args()

    a_all = _load_entries(args.ledger_a)
    b_all = _load_entries(args.ledger_b)
    a_rows = _filter(a_all, str(args.replay_key or "").strip(), str(args.correlation_id or "").strip())
    b_rows = _filter(b_all, str(args.replay_key or "").strip(), str(args.correlation_id or "").strip())

    comparisons, summary = _compare(a_rows, b_rows)
    selected = comparisons[: max(1, int(args.limit))]

    csv_written = ""
    if str(args.csv or "").strip():
        csv_written = _write_csv(str(args.csv), selected)

    payload: Dict[str, Any] = {
        "ledger_a": args.ledger_a,
        "ledger_b": args.ledger_b,
        "filters": {
            "replay_key": str(args.replay_key or "").strip(),
            "correlation_id": str(args.correlation_id or "").strip(),
        },
        "summary": summary,
    }
    if csv_written:
        payload["csv"] = csv_written

    if not args.summary_only:
        payload["comparisons"] = selected

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
