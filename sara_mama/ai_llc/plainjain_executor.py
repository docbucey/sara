from __future__ import annotations

import hashlib
import os
import random
import re
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[A-Za-z][A-Za-z0-9_\-']*", text or "")


def _normalize_prompt(payload: Dict[str, Any]) -> str:
    prompt = str(
        payload.get("prompt")
        or payload.get("content")
        or payload.get("value")
        or payload.get("text")
        or ""
    ).strip()
    if prompt:
        return prompt

    doc = payload.get("document_context") if isinstance(payload.get("document_context"), dict) else {}
    fallback = " ".join(
        [
            str(doc.get("focus_scope") or ""),
            str(doc.get("document_id") or ""),
            str(doc.get("document_version") or ""),
        ]
    ).strip()
    return fallback or "No prompt supplied."


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_replay_ledger(entry: Dict[str, Any], ledger_path: Optional[str] = None) -> Dict[str, Any]:
    base_dir = os.path.dirname(__file__)
    logs_dir = os.path.abspath(os.path.join(base_dir, "..", "logs"))
    os.makedirs(logs_dir, exist_ok=True)
    path = ledger_path or os.path.join(logs_dir, "plainjain_replay_ledger.ndjson")
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return {"path": path, "ts": entry.get("ts")}


def execute_plainjain(
    payload: Optional[Dict[str, Any]] = None,
    runtime_knobs: Optional[Dict[str, Any]] = None,
    machine_profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    payload = dict(payload or {})
    runtime_knobs = dict(runtime_knobs or {})
    machine_profile = dict(machine_profile or {})

    prompt = _normalize_prompt(payload)
    tokens = _tokenize(prompt)
    unique_tokens = sorted({t.lower() for t in tokens})

    profile = str(runtime_knobs.get("selected_profile") or "stable_probabilistic")
    executor_mode = str(runtime_knobs.get("executor_mode") or "stable")
    probabilistic = bool(runtime_knobs.get("probabilistic_enabled", profile != "strict_deterministic"))

    replay_mode = bool(runtime_knobs.get("replay_mode", False))
    replay_key = str(runtime_knobs.get("replay_key") or "")
    replay_ledger_enabled = bool(runtime_knobs.get("replay_ledger_enabled", replay_mode))
    replay_ledger_path = runtime_knobs.get("replay_ledger_path")
    correlation_id = str(runtime_knobs.get("correlation_id") or "")
    prompt_hash_full = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    replay_material = f"{prompt_hash_full}|{profile}|{executor_mode}|{replay_key}"
    replay_seed = int(hashlib.sha256(replay_material.encode("utf-8")).hexdigest()[:8], 16)

    seed = runtime_knobs.get("seed")
    if replay_mode:
        seed = replay_seed
    elif seed is None and probabilistic:
        seed = int.from_bytes(os.urandom(4), "big")
    elif seed is None:
        seed = 7

    rng = random.Random(int(seed))

    stems = {
        "strict": [
            "Structured summary",
            "Deterministic synthesis",
            "Policy-aligned response",
        ],
        "stable": [
            "Guided synthesis",
            "Balanced response",
            "Low-variance generation",
        ],
        "creative": [
            "Expressive synthesis",
            "Exploratory response",
            "High-flex generation",
        ],
    }

    lane = stems.get(executor_mode, stems["stable"])
    headline = rng.choice(lane)
    sample_terms = unique_tokens[:6]
    terms_line = ", ".join(sample_terms) if sample_terms else "none"

    digest = prompt_hash_full[:12]
    generated_text = (
        f"{headline}: {prompt[:220]}\n"
        f"Focus terms: {terms_line}\n"
        f"Trace: {digest}"
    )

    output_hash = hashlib.sha256(generated_text.encode("utf-8")).hexdigest()[:16]
    ledger_ref: Dict[str, Any] = {}
    if replay_ledger_enabled:
        ledger_entry = {
            "ts": _iso_now(),
            "engine": "plainjain_executor",
            "correlation_id": correlation_id,
            "machine_profile_id": str(machine_profile.get("profile_id") or "default"),
            "selected_profile": profile,
            "executor_mode": executor_mode,
            "probabilistic_enabled": probabilistic,
            "replay_mode": replay_mode,
            "replay_key": replay_key,
            "replay_seed": int(replay_seed),
            "seed_used": int(seed),
            "prompt_hash": prompt_hash_full[:16],
            "output_hash": output_hash,
            "token_count": len(tokens),
            "unique_token_count": len(unique_tokens),
        }
        ledger_ref = _append_replay_ledger(ledger_entry, ledger_path=str(replay_ledger_path) if replay_ledger_path else None)

    return {
        "success": True,
        "engine": "plainjain_executor",
        "selected_profile": profile,
        "executor_mode": executor_mode,
        "probabilistic_enabled": probabilistic,
        "replay_mode": replay_mode,
        "replay_key": replay_key,
        "replay_seed": int(replay_seed),
        "replay_ledger_enabled": replay_ledger_enabled,
        "replay_ledger_ref": ledger_ref,
        "seed_used": int(seed),
        "token_count": len(tokens),
        "unique_token_count": len(unique_tokens),
        "output_hash": output_hash,
        "generated_text": generated_text,
        "machine_profile_id": str(machine_profile.get("profile_id") or "default"),
    }
