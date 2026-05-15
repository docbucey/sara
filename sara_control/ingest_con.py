"""
SARA Control — Ingest artifacts, concept extraction, concept query, chat parsing/ingestion.
Extracted from sara_controlgen1.py.
"""
import os
import re
import json
import hashlib
import shutil
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

try:
    from sara_control.loader_con import _load_core_module, _load_gen1_security
    _core = _load_core_module()
    if _core is None:
        raise ImportError("Core module file not found")
    create_nbs_file = _core.create_nbs_file
    NBS_BASE_DIR = _core.NBS_BASE_DIR
    SYSTEM_CORE_PROJECT_NAME = _core.SYSTEM_CORE_PROJECT_NAME
except Exception:
    _core = None
    def create_nbs_file(project_name, relative_path, content, meta=None):
        return {"success": False, "error": "Core not loaded"}
    NBS_BASE_DIR = os.path.join(os.path.expanduser("~"), "sara_nbs")
    SYSTEM_CORE_PROJECT_NAME = "sara_core_project"

try:
    _sec = _load_gen1_security()
    dispatch_security = _sec.dispatch_security
except Exception:
    def dispatch_security(command, auth_token="", **kwargs):
        return {"success": True, "command": command, "result": {"allowed": True, "valid": True, "reason": "SEC:FALLBACK:ALLOW"}}

from sara_control.session_con import start_session_con, append_event_con, array_normalize_con, _iso_now_con
from sara_control.governor_con import (
    ControlIngestBufferGuard, ControlSystemStrainBudget,
    _user_interactive_active_con, _run_preview_worker_con,
)


def ingest_artifacts_con(con_project: str = SYSTEM_CORE_PROJECT_NAME,
                         con_sources: Optional[List[str]] = None,
                         con_narrative_path: Optional[str] = None,
                         con_tags: Optional[List[str]] = None,
                         con_preview_bytes: int = 2048,
                         con_max_buffer_percent: float = 3.0,
                         con_distributed_workers: Optional[int] = None,
                         con_interactive_guard: bool = True,
                         con_user_idle_seconds: int = 90,
                         con_security_token: str = "",
                         con_envoy_mode: bool = False,
                         con_use_windows_defender: bool = True) -> Dict[str, Any]:
    """
    Create NBS artifact_wrapper files for artifacts found in source folders.
    Supports markdown, logs, text, Python code, JSON/NBS, and zip archives.
    """
    con_sources = con_sources or []
    for i, p in enumerate(con_sources):
        if isinstance(p, str):
            con_sources[i] = os.path.abspath(p)

    if not con_narrative_path:
        con_start = start_session_con(con_project, con_session_note="Artifact ingestion session start")
        if not con_start.get("success"):
            return con_start
        con_narrative_path = con_start["reference"]["file_path"]

    include_exts = {
        ".json", ".nbs", ".md", ".markdown", ".log", ".txt", ".py", ".zip",
        ".csv", ".pdf", ".docx", ".xls", ".xlsx",
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp",
        ".mp4", ".mov", ".avi", ".mkv", ".webm",
        ".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac",
        ".stl", ".obj",
    }
    text_like_exts = {".md", ".markdown", ".log", ".txt", ".py", ".json", ".nbs", ".csv"}
    artifacts_created: List[Dict[str, Any]] = []
    artifacts_skipped: List[Dict[str, Any]] = []
    parser_status_counts: Dict[str, int] = {}
    strain_mode_counts: Dict[str, int] = {}

    con_art_dir = os.path.join(NBS_BASE_DIR, con_project, "artifacts")
    os.makedirs(con_art_dir, exist_ok=True)
    con_clean_dir = os.path.join(NBS_BASE_DIR, con_project, "ingest_clean")
    os.makedirs(con_clean_dir, exist_ok=True)

    buffer_guard = ControlIngestBufferGuard(max_percent=con_max_buffer_percent)
    strain_budget = ControlSystemStrainBudget(max_percent=con_max_buffer_percent)
    interactive_user_active = (
        _user_interactive_active_con(con_user_idle_seconds) if con_interactive_guard else False
    )

    def _sanitize_name_con(s: str) -> str:
        return "".join(ch if ch.isalnum() or ch in ("_", "-") else "_" for ch in s)[:80]

    candidates: List[Dict[str, Any]] = []
    for src in con_sources:
        if not src or not os.path.exists(src):
            continue
        for root, dirs, files in os.walk(src):
            for fname in files:
                _, ext = os.path.splitext(fname)
                ext_l = ext.lower()
                if ext_l not in include_exts:
                    continue
                candidates.append({"src_path": os.path.join(root, fname), "fname": fname, "ext": ext_l})

    def _process_candidate(item: Dict[str, Any]) -> Dict[str, Any]:
        fpath = item["src_path"]
        fname = item["fname"]
        ext_l = item["ext"]
        try:
            fsize = os.path.getsize(fpath)
        except Exception:
            return {"success": False, "artifact_path": fpath, "error": "size-read-failed"}

        hash_input = f"{fpath}:{fsize}:{os.path.getmtime(fpath)}".encode("utf-8", errors="ignore")
        h = hashlib.sha256(hash_input).hexdigest()[:24]
        clean_name = f"clean_{h}_{_sanitize_name_con(fname)}"
        clean_path = os.path.join(con_clean_dir, clean_name)
        try:
            if not os.path.exists(clean_path):
                shutil.copy2(fpath, clean_path)
        except Exception as e:
            return {"success": False, "artifact_path": fpath, "error": f"clean-copy-failed:{e}"}

        sec_command = "scan_envoy" if con_envoy_mode else "scan_file"
        sec = dispatch_security(sec_command, auth_token=con_security_token, file_path=clean_path, file_ext=ext_l, max_file_bytes=100 * 1024 * 1024, use_windows_defender=con_use_windows_defender)
        sec_ok = bool(sec.get("success"))
        sec_result = sec.get("result", {}) if isinstance(sec, dict) else {}
        if not sec_ok or not sec_result.get("allowed", False):
            return {"success": False, "artifact_path": fpath, "clean_path": clean_path, "error": sec_result.get("reason", "SEC:DENY:scan-failed"), "security": sec}

        preview_plan = strain_budget.preview_plan(preview_bytes=con_preview_bytes, ext_l=ext_l, buffer_guard=buffer_guard, interactive_user_active=interactive_user_active)
        preview_char_cap = int(max(256, preview_plan["preview_bytes"])) if preview_plan["preview_bytes"] else 0
        preview_str: Optional[str] = None
        preview_bytes_reserved = int(min(max(256, max(preview_char_cap, 256)), max(1024, buffer_guard.max_bytes // 10)))
        parser_status = str(preview_plan["parser_status"])
        image_meta: Dict[str, Any] = {}
        strain_snapshot = preview_plan["snapshot"]

        if preview_plan["allow_preview"]:
            if buffer_guard.try_acquire(preview_bytes_reserved):
                try:
                    if ext_l in text_like_exts:
                        with open(clean_path, "r", encoding="utf-8", errors="ignore") as f:
                            preview_str = f.read(preview_char_cap)
                        parser_status = "preview_text"
                    elif preview_plan["offload"]:
                        worker_result = _run_preview_worker_con(clean_path, ext_l, preview_char_cap)
                        preview_str = worker_result.get("preview")
                        image_meta = worker_result.get("image_meta", {}) or {}
                        parser_status = str(worker_result.get("parser_status", "preview_worker_failed"))
                    elif ext_l == ".xls":
                        parser_status = "xls_metadata_only"
                finally:
                    buffer_guard.release(preview_bytes_reserved)
            else:
                parser_status = "buffer_guard_limit"

        con_content = {
            "artifact_type": "file",
            "path": fpath,
            "clean_path": clean_path,
            "ext": ext_l,
            "size": fsize,
            "preview": preview_str,
            "parser_status": parser_status,
            "memory_guard": {**buffer_guard.usage(), **strain_snapshot},
            "image_meta": image_meta,
            "security_scan": sec_result,
            "tags": array_normalize_con(con_tags or ["artifact", ext_l.strip(".")]),
        }

        rel_name = f"artifact_{int(datetime.now(timezone.utc).timestamp() * 1000)}_{h}_{_sanitize_name_con(fname)}_gen0_1.0_nbs.json"
        rel_path = os.path.join("artifacts", rel_name)

        write_res = create_nbs_file(
            project_name=con_project,
            relative_path=rel_path,
            content=con_content,
            meta={"nbs_type": "artifact_wrapper", "tags": ["artifact", ext_l.strip(".")], "source": "control", "project_name": con_project},
        )
        if not write_res.get("success"):
            return {"success": False, "artifact_path": fpath, "error": "wrapper-write-failed"}

        return {
            "success": True,
            "artifact_path": fpath,
            "clean_path": clean_path,
            "wrapper_path": write_res["reference"]["file_path"],
            "ext": ext_l,
            "size": fsize,
            "parser_status": parser_status,
            "strain_mode": preview_plan["mode"],
        }

    base_worker_count = con_distributed_workers
    if base_worker_count is None:
        base_worker_count = min(4, max(1, (os.cpu_count() or 2)))
    worker_plan = strain_budget.recommended_worker_count(base_worker_count, buffer_guard, interactive_user_active=interactive_user_active)
    worker_count = int(worker_plan["worker_count"])

    if candidates:
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = [executor.submit(_process_candidate, item) for item in candidates]
            for fut in as_completed(futures):
                result = fut.result()
                ps = str(result.get("parser_status", "unknown"))
                parser_status_counts[ps] = parser_status_counts.get(ps, 0) + 1
                sm = str(result.get("strain_mode", worker_plan["mode"]))
                strain_mode_counts[sm] = strain_mode_counts.get(sm, 0) + 1
                if result.get("success"):
                    artifacts_created.append(result)
                else:
                    artifacts_skipped.append(result)

    con_event = {
        "event_type": "ingest_artifacts",
        "sources": array_normalize_con(con_sources),
        "distributed_workers": worker_count,
        "requested_workers": base_worker_count,
        "max_buffer_percent": con_max_buffer_percent,
        "interactive_guard": con_interactive_guard,
        "interactive_user_active": interactive_user_active,
        "user_idle_seconds_threshold": con_user_idle_seconds,
        "strain_mode": worker_plan["mode"],
        "strain_mode_counts": strain_mode_counts,
        "strain_snapshot": worker_plan["snapshot"],
        "parser_status_counts": parser_status_counts,
        "envoy_mode": con_envoy_mode,
        "scanned": len(candidates),
        "count": len(artifacts_created),
        "skipped": len(artifacts_skipped),
        "artifacts": artifacts_created[:50],
        "skipped_artifacts": artifacts_skipped[:50],
        "note": "Created artifact_wrapper NBS files using adaptive distributed ingest, disk-first clean cache, and offloaded heavy previews",
    }
    con_app = append_event_con(con_project, con_narrative_path, con_event)
    if not con_app.get("success"):
        return con_app

    return {
        "success": True,
        "narrative_path": con_narrative_path,
        "count": len(artifacts_created),
        "skipped": len(artifacts_skipped),
        "distributed_workers": worker_count,
        "requested_workers": base_worker_count,
        "strain_mode": worker_plan["mode"],
        "strain_mode_counts": strain_mode_counts,
        "parser_status_counts": parser_status_counts,
        "max_buffer_percent": con_max_buffer_percent,
        "interactive_guard": con_interactive_guard,
        "interactive_user_active": interactive_user_active,
        "envoy_mode": con_envoy_mode,
    }


def extract_concepts_con(
    con_project: str = SYSTEM_CORE_PROJECT_NAME,
    con_sources: Optional[List[str]] = None,
    con_keywords: Optional[List[str]] = None,
    con_narrative_path: Optional[str] = None,
    con_max_files: int = 50000,
    con_max_snips_per_file: int = 5,
    con_max_buffer_percent: float = 3.0,
    con_distributed_workers: Optional[int] = None,
    con_interactive_guard: bool = True,
    con_user_idle_seconds: int = 90,
) -> Dict[str, Any]:
    """Deterministic concept extractor that scans text-like artifacts for keyword hits."""
    con_sources = con_sources or []
    for i, p in enumerate(con_sources):
        if isinstance(p, str):
            con_sources[i] = os.path.abspath(p)
    con_keywords = [k.strip() for k in (con_keywords or []) if str(k).strip()]
    if not con_keywords:
        return {"success": False, "error": "con_keywords required"}

    if not con_narrative_path:
        con_start = start_session_con(con_project, con_session_note="Concept extraction session start")
        if not con_start.get("success"):
            return con_start
        con_narrative_path = con_start["reference"]["file_path"]

    include_exts = {".md", ".markdown", ".log", ".txt"}
    concepts_dir = os.path.join(NBS_BASE_DIR, con_project, "concepts")
    os.makedirs(concepts_dir, exist_ok=True)

    def _find_snips(path: str) -> List[Dict[str, Any]]:
        snips: List[Dict[str, Any]] = []
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception:
            return snips
        lower_lines = [ln.lower() for ln in lines]
        for idx, low in enumerate(lower_lines):
            if any(kw.lower() in low for kw in con_keywords):
                start = max(0, idx - 1)
                end = min(len(lines), idx + 2)
                snip_text = "".join(lines[start:end]).strip()
                snips.append({"path": path, "line": idx + 1, "context": snip_text})
                if len(snips) >= con_max_snips_per_file:
                    break
        return snips

    def _sanitize(s: str) -> str:
        return "".join(ch if ch.isalnum() or ch in ("_", "-") else "_" for ch in s)[:80]

    total_files = 0
    total_hits = 0
    concept_records: List[Dict[str, Any]] = []

    re_is_pattern = re.compile(r"\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b\s*(is|=|->|—|-)\s*(.+)")
    re_alias_pattern = re.compile(r"\b(aka|also known as|alias)\b\s*[:=\-]?\s*(.+)", re.IGNORECASE)
    re_heading_entity = re.compile(r"^(#+|[-*]\s*)\s*([A-Z][a-z]+\s+[A-Z][a-z]+)\s*[:—-]?\s*(.+)?$")
    re_labeled = re.compile(r"^(Concept|Conclusion|Identity)\s*[:]\s*([A-Z][a-z]+\s+[A-Z][a-z]+)\s*(is|=|->|—|-)\s*(.+)$", re.IGNORECASE)

    def _extract_identity_claims(text: str, focus_entities: List[str]) -> List[Dict[str, Any]]:
        claims: List[Dict[str, Any]] = []
        for m in re_is_pattern.finditer(text):
            entity = m.group(1)
            if focus_entities and entity.lower() not in [e.lower() for e in focus_entities]:
                continue
            predicate = m.group(2)
            obj = m.group(3).strip()
            claims.append({"type": "identity", "entity": entity, "predicate": predicate, "object": obj, "statement": f"{entity} {predicate} {obj}"})
        for m in re_heading_entity.finditer(text):
            entity = m.group(2)
            if focus_entities and entity.lower() not in [e.lower() for e in focus_entities]:
                continue
            tail = (m.group(3) or "").strip()
            if tail:
                claims.append({"type": "identity", "entity": entity, "predicate": "is", "object": tail, "statement": f"{entity} is {tail}"})
        for m in re_labeled.finditer(text):
            entity = m.group(2)
            if focus_entities and entity.lower() not in [e.lower() for e in focus_entities]:
                continue
            predicate = m.group(3)
            obj = m.group(4).strip()
            claims.append({"type": "identity", "entity": entity, "predicate": predicate, "object": obj, "statement": f"{entity} {predicate} {obj}"})
        for m in re_alias_pattern.finditer(text):
            alias = m.group(2).strip()
            if alias:
                claims.append({"type": "alias", "alias": alias, "statement": f"alias: {alias}"})
        return claims

    candidates: List[str] = []
    for src in con_sources:
        if not src or not os.path.exists(src):
            continue
        for root, dirs, files in os.walk(src):
            for fname in files:
                if len(candidates) >= con_max_files:
                    break
                _, ext = os.path.splitext(fname)
                if ext.lower() in include_exts:
                    candidates.append(os.path.join(root, fname))
            if len(candidates) >= con_max_files:
                break

    total_files = len(candidates)
    buffer_guard = ControlIngestBufferGuard(max_percent=con_max_buffer_percent)
    strain_budget = ControlSystemStrainBudget(max_percent=con_max_buffer_percent)
    interactive_user_active = (_user_interactive_active_con(con_user_idle_seconds) if con_interactive_guard else False)
    base_worker_count = con_distributed_workers
    if base_worker_count is None:
        base_worker_count = min(4, max(1, (os.cpu_count() or 2)))
    worker_plan = strain_budget.recommended_worker_count(base_worker_count, buffer_guard, interactive_user_active=interactive_user_active)
    worker_count = int(worker_plan["worker_count"])

    focus_entities = [kw for kw in (con_keywords or []) if len(kw.split()) >= 2]

    def _scan_concept_file(fpath: str) -> Dict[str, Any]:
        snips = _find_snips(fpath)
        statements = [s["context"] for s in snips]
        identity_claims: List[Dict[str, Any]] = []
        for ctx in statements:
            identity_claims.extend(_extract_identity_claims(ctx, focus_entities))
        return {"file": fpath, "snips": snips, "statements": statements, "identity_claims": identity_claims, "hits": len(snips)}

    scan_results: List[Dict[str, Any]] = []
    if candidates:
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = [executor.submit(_scan_concept_file, p) for p in candidates]
            for fut in as_completed(futures):
                scan_results.append(fut.result())

    for item in sorted(scan_results, key=lambda x: x.get("file", "")):
        snips = item.get("snips", [])
        if not snips:
            continue
        total_hits += int(item.get("hits", 0))
        identity_claims = item.get("identity_claims", [])
        statements = item.get("statements", [])
        fpath = item.get("file", "")
        fname = os.path.basename(fpath)

        concept_payload = {"keywords": con_keywords, "statement": array_normalize_con(statements), "confidence": ["observed_in_artifacts"]}
        if identity_claims:
            concept_payload.update({
                "type": [c.get("type") for c in identity_claims],
                "entity": list({c.get("entity") for c in identity_claims if c.get("entity")}),
                "predicate": list({c.get("predicate") for c in identity_claims if c.get("predicate")}),
                "object": list({c.get("object") for c in identity_claims if c.get("object")}),
                "aliases": list({c.get("alias") for c in identity_claims if c.get("type") == "alias" and c.get("alias")}),
            })

        record = {"concept": concept_payload, "sources": snips, "tags": ["concept", "extracted"] + (["identity"] if identity_claims else [])}
        ts = int(datetime.now(timezone.utc).timestamp())
        rel_name = f"concept_{ts}_{_sanitize(fname)}_gen0_1.0_nbs.json"
        rel_path = os.path.join("concepts", rel_name)
        write_res = create_nbs_file(project_name=con_project, relative_path=rel_path, content=record,
            meta={"nbs_type": "concept_record", "tags": ["concept", "extracted"] + (["identity"] if identity_claims else []), "source": "control", "project_name": con_project})
        if write_res.get("success"):
            concept_records.append({"wrapper_path": write_res["reference"]["file_path"], "file": fpath, "hits": len(snips)})

    con_event = {
        "event_type": "concept_extracted",
        "keywords": array_normalize_con(con_keywords),
        "total_files": total_files,
        "total_hits": total_hits,
        "requested_workers": base_worker_count,
        "distributed_workers": worker_count,
        "max_buffer_percent": con_max_buffer_percent,
        "interactive_guard": con_interactive_guard,
        "interactive_user_active": interactive_user_active,
        "user_idle_seconds_threshold": con_user_idle_seconds,
        "strain_mode": worker_plan["mode"],
        "strain_snapshot": worker_plan["snapshot"],
        "records": concept_records[:50],
    }
    con_app = append_event_con(con_project, con_narrative_path, con_event)
    if not con_app.get("success"):
        return con_app

    return {"success": True, "narrative_path": con_narrative_path, "records_count": len(concept_records), "total_hits": total_hits, "requested_workers": base_worker_count, "distributed_workers": worker_count, "strain_mode": worker_plan["mode"]}


def query_concepts_con(
    con_project: str = SYSTEM_CORE_PROJECT_NAME,
    con_keywords: Optional[List[str]] = None,
    con_limit: int = 50,
) -> Dict[str, Any]:
    """Query concept_record NBS files for keyword hits and return statements with provenance."""
    con_keywords = [k.strip().lower() for k in (con_keywords or []) if str(k).strip()]
    if not con_keywords:
        return {"success": False, "error": "con_keywords required"}
    concepts_dir = os.path.join(NBS_BASE_DIR, con_project, "concepts")
    if not os.path.exists(concepts_dir):
        return {"success": True, "matches": []}
    matches: List[Dict[str, Any]] = []
    for fname in os.listdir(concepts_dir):
        if not fname.endswith("_gen0_1.0_nbs.json"):
            continue
        fpath = os.path.join(concepts_dir, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                obj = json.load(f)
        except Exception:
            continue
        content = obj.get("content", {}) if isinstance(obj, dict) else {}
        concept = content.get("concept", {}) if isinstance(content, dict) else {}
        statements = concept.get("statement", [])
        if isinstance(statements, str):
            statements = [statements]
        tags = content.get("tags", [])
        entity = concept.get("entity", [])
        if isinstance(entity, str):
            entity = [entity]
        objs = concept.get("object", [])
        if isinstance(objs, str):
            objs = [objs]
        haystacks: List[str] = []
        haystacks.extend(statements or [])
        haystacks.extend(entity or [])
        haystacks.extend(objs or [])
        found = False
        for st in haystacks:
            low = str(st).lower()
            if all(kw in low for kw in con_keywords):
                found = True
                break
        if found:
            matches.append({"concept_file": fpath, "statements": statements, "sources": content.get("sources", []), "entity": entity, "object": objs, "tags": tags})
            if len(matches) >= con_limit:
                break
    return {"success": True, "matches": matches}


def parse_chat_con(con_path: str) -> Dict[str, Any]:
    """Parse a general chat log/markdown/text file into a normalized transcript."""
    if not os.path.exists(con_path):
        return {"success": False, "error": f"File not found: {con_path}"}
    try:
        with open(con_path, "r", encoding="utf-8", errors="ignore") as f:
            txt = f.read()
    except Exception as e:
        return {"success": False, "error": f"Read error: {e}"}

    lines = txt.splitlines()
    transcript: List[Dict[str, Any]] = []
    role_re = re.compile(r"^(?:[-*]\s*)?(User|Assistant|System|SARA)\s*:\s*(.*)$", re.IGNORECASE)
    ts_re = re.compile(r"(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?)")

    labeled = False
    for ln in lines:
        m = role_re.match(ln)
        if m:
            labeled = True
            role = m.group(1).lower()
            text = m.group(2).strip()
            when = None
            mts = ts_re.search(ln)
            if mts:
                when = mts.group(1)
            transcript.append({"role": role, "text": text, "when": when})
    if not labeled:
        para = []
        for ln in lines:
            if ln.strip():
                para.append(ln)
            else:
                if para:
                    transcript.append({"role": "unknown", "text": "\n".join(para), "when": None})
                    para = []
        if para:
            transcript.append({"role": "unknown", "text": "\n".join(para), "when": None})
    return {"success": True, "transcript": transcript}


def emit_transcript_nbs_con(con_project: str, transcript: List[Dict[str, Any]], source_path: str) -> Dict[str, Any]:
    """Write a narrative_timeline NBS where each chat turn is an event."""
    events = []
    for idx, turn in enumerate(transcript):
        events.append({
            "when": turn.get("when") or _iso_now_con(),
            "event_type": "chat_turn",
            "role": turn.get("role"),
            "text": turn.get("text"),
            "meta": {"turn_index": idx, "source_path": source_path},
        })
    content = {
        "narrative_type": "chat_transcript",
        "timestamp": _iso_now_con(),
        "project_name": con_project,
        "events": events,
    }
    rel = os.path.join("narrative", f"chat_transcript_{int(datetime.now(timezone.utc).timestamp())}_gen0_1.0_nbs.json")
    return create_nbs_file(
        project_name=con_project,
        relative_path=rel,
        content=content,
        meta={"nbs_type": "narrative_timeline", "tags": ["narrative", "chat", "transcript"], "source": "control", "project_name": con_project},
    )


def ingest_chat_con(con_project: str, con_paths: List[str]) -> Dict[str, Any]:
    """Pipeline: parse each chat file -> emit transcript NBS -> extract concepts."""
    created = []
    for p in con_paths:
        if not isinstance(p, str) or not os.path.exists(p):
            continue
        parsed = parse_chat_con(p)
        if not parsed.get("success"):
            continue
        t = parsed.get("transcript", [])
        wr = emit_transcript_nbs_con(con_project, t, p)
        if wr.get("success"):
            created.append(wr["reference"]["file_path"])
    conc = extract_concepts_con(con_project, con_sources=list({os.path.dirname(p) for p in con_paths}), con_keywords=["clark", "kent", "aka", "alias", "conclusion", "concept"])
    return {"success": True, "transcripts": created, "concepts": conc}
