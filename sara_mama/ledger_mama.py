"""MamaLedger and replay ledger query/compare wrappers for MAMA."""

import importlib.util
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MamaLedger:
    """Append-safe memory ledger for accepted and failed attempts."""

    def __init__(self, base_dir: Optional[str] = None):
        here = os.path.dirname(__file__)
        self.base_dir = base_dir or here
        self.logs_dir = os.path.join(self.base_dir, "logs")
        os.makedirs(self.logs_dir, exist_ok=True)
        self.ledger_path = os.path.join(self.logs_dir, "mama_attempt_ledger.ndjson")

    def append_attempt(self,
                       task_type: str,
                       status: str,
                       reason: str,
                       model_profile: str,
                       lesson: Optional[str] = None,
                       provenance: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        entry = {
            "ts": _iso_now(),
            "task_type": task_type,
            "status": status,
            "reason": reason,
            "model_profile": model_profile,
            "lesson": lesson,
            "provenance": provenance or {},
        }
        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        return entry


def query_replay_ledger_mama(
    replay_key: str = "",
    correlation_id: str = "",
    prompt_hash_prefix: str = "",
    output_hash_prefix: str = "",
    limit: int = 20,
    latest_first: bool = True,
    summary_only: bool = False,
    csv_path: str = "",
) -> Dict[str, Any]:
    """Convenience wrapper around replay_ledger_query tool for MAMA-side continuity inspection."""
    tool_path = os.path.join(os.path.dirname(__file__), "tools", "replay_ledger_query.py")
    if not os.path.exists(tool_path):
        return {
            "success": False,
            "error": "replay_ledger_query tool not found",
            "tool_path": tool_path,
        }

    try:
        spec = importlib.util.spec_from_file_location("sara_mama_replay_ledger_tool", tool_path)
        if spec is None or spec.loader is None:
            return {"success": False, "error": "unable to load replay_ledger_query tool"}
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        ledger_path = mod._default_ledger_path() if hasattr(mod, "_default_ledger_path") else ""
        entries = mod._load_entries(ledger_path) if hasattr(mod, "_load_entries") else []
        filtered = mod._filter_entries(
            entries,
            replay_key=str(replay_key or "").strip(),
            correlation_id=str(correlation_id or "").strip(),
            prompt_hash=str(prompt_hash_prefix or "").strip(),
            output_hash=str(output_hash_prefix or "").strip(),
        ) if hasattr(mod, "_filter_entries") else []

        filtered.sort(key=lambda x: str(x.get("ts", "")), reverse=bool(latest_first))
        selected = filtered[: max(1, int(limit))]
        summary = mod._build_summary(filtered) if hasattr(mod, "_build_summary") else {"count": len(filtered)}

        csv_written = ""
        if csv_path and hasattr(mod, "_write_csv"):
            csv_written = mod._write_csv(str(csv_path), selected)

        payload: Dict[str, Any] = {
            "success": True,
            "ledger": ledger_path,
            "summary": summary,
        }
        if csv_written:
            payload["csv"] = csv_written
        if not summary_only:
            payload["records"] = selected
        return payload
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "tool_path": tool_path,
        }


def compare_replay_ledgers_mama(
    ledger_a: str,
    ledger_b: str,
    replay_key: str = "",
    correlation_id: str = "",
    limit: int = 200,
    summary_only: bool = False,
    csv_path: str = "",
) -> Dict[str, Any]:
    """Compare two replay ledgers (desktop vs ARM/wearable) for continuity by prompt hash/output hash."""
    tool_path = os.path.join(os.path.dirname(__file__), "tools", "replay_ledger_compare.py")
    if not os.path.exists(tool_path):
        return {
            "success": False,
            "error": "replay_ledger_compare tool not found",
            "tool_path": tool_path,
        }

    try:
        spec = importlib.util.spec_from_file_location("sara_mama_replay_compare_tool", tool_path)
        if spec is None or spec.loader is None:
            return {"success": False, "error": "unable to load replay_ledger_compare tool"}
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        if not hasattr(mod, "_load_entries") or not hasattr(mod, "_filter") or not hasattr(mod, "_compare"):
            return {"success": False, "error": "replay_ledger_compare tool missing expected functions"}

        a_all = mod._load_entries(str(ledger_a))
        b_all = mod._load_entries(str(ledger_b))
        a_rows = mod._filter(a_all, str(replay_key or "").strip(), str(correlation_id or "").strip())
        b_rows = mod._filter(b_all, str(replay_key or "").strip(), str(correlation_id or "").strip())
        comparisons, summary = mod._compare(a_rows, b_rows)
        selected = comparisons[: max(1, int(limit))]

        csv_written = ""
        if csv_path and hasattr(mod, "_write_csv"):
            csv_written = mod._write_csv(str(csv_path), selected)

        payload: Dict[str, Any] = {
            "success": True,
            "ledger_a": str(ledger_a),
            "ledger_b": str(ledger_b),
            "summary": summary,
        }
        if csv_written:
            payload["csv"] = csv_written
        if not summary_only:
            payload["comparisons"] = selected
        return payload
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "tool_path": tool_path,
        }
