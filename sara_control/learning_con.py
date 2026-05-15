"""
SARA Control — LearnManager class and learn_overlay_con function.
Extracted from sara_controlgen1.py.
"""
import os
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional


class LearnManager:
    """
    Experiential learning loop for SARA.
    SARA learns by doing: tries actions/strategies, records outcomes, reflects, and adapts.

    Usage:
        learn_mgr = LearnManager()
        def try_fn(): ... # do something, return result
        def reflect_fn(result): ... # analyze result, return feedback/score
        def adapt_fn(feedback): ... # update strategy/model
        learn_mgr.experiential_learn(try_fn, reflect_fn, adapt_fn, n_trials=5)
    """
    def __init__(self):
        self.experiences = []

    def learn(self, data: Any, source: str = "manual"):
        self.experiences.append({'data': data, 'source': source, 'timestamp': datetime.now().isoformat()})
        return {'success': True, 'count': len(self.experiences)}

    def summarize(self):
        return {'total': len(self.experiences), 'samples': self.experiences[-3:]}

    def experiential_learn(self, try_fn, reflect_fn, adapt_fn, n_trials=3):
        """
        Run an experiential learning loop:
        - try_fn: function to perform an action/experiment, returns result
        - reflect_fn: function to analyze result, returns feedback/score
        - adapt_fn: function to update strategy/model based on feedback
        - n_trials: number of learning cycles
        """
        for trial in range(1, n_trials+1):
            result = try_fn()
            feedback = reflect_fn(result)
            adaptation = adapt_fn(feedback)
            self.experiences.append({
                'trial': trial,
                'result': result,
                'feedback': feedback,
                'adaptation': adaptation,
                'timestamp': datetime.now().isoformat()
            })
        return {'success': True, 'trials': n_trials, 'last': self.experiences[-1] if self.experiences else None}


def learn_overlay_con(con_project: str = "sara_core_project",
                      con_sources: Optional[List[str]] = None,
                      con_narrative_path: Optional[str] = None,
                      con_tags: Optional[List[str]] = None,
                      con_max_buffer_percent: float = 3.0,
                      con_distributed_workers: Optional[int] = None,
                      con_interactive_guard: bool = True,
                      con_user_idle_seconds: int = 90) -> Dict[str, Any]:
    """
    Learn overlay that ingests legacy/other-AI folders as read-only sources and
    logs a summary event into the provided narrative (or creates a new session if
    none is provided). This does NOT run any LLM; it inventories JSON/NBS-like
    files and records normalized pointers so other models can use them.

    Parameters:
      - con_sources: list of folder paths to scan (e.g., legacy projects)
      - con_narrative_path: existing narrative to append to; if None, starts a session
      - con_tags: additional tags for the learning event

    Returns dict with summary and a learn event appended to narrative.
    """
    from sara_control.session_con import start_session_con, append_event_con, array_normalize_con
    from sara_control.governor_con import ControlIngestBufferGuard, ControlSystemStrainBudget, _user_interactive_active_con

    con_sources = con_sources or []
    for i, p in enumerate(con_sources):
        if isinstance(p, str):
            con_sources[i] = os.path.abspath(p)

    if not con_narrative_path:
        con_start = start_session_con(con_project, con_session_note="Learning overlay session start")
        if not con_start.get("success"):
            return con_start
        con_narrative_path = con_start["reference"]["file_path"]

    con_inventory: List[Dict[str, Any]] = []
    exts = {".json", ".nbs"}
    candidates: List[Dict[str, str]] = []
    for src in con_sources:
        if not src or not os.path.exists(src):
            continue
        for root, dirs, files in os.walk(src):
            for fname in files:
                _, ext = os.path.splitext(fname)
                if ext.lower() in exts:
                    candidates.append({"path": os.path.join(root, fname), "ext": ext.lower()})

    buffer_guard = ControlIngestBufferGuard(max_percent=con_max_buffer_percent)
    strain_budget = ControlSystemStrainBudget(max_percent=con_max_buffer_percent)
    interactive_user_active = (
        _user_interactive_active_con(con_user_idle_seconds) if con_interactive_guard else False
    )

    base_worker_count = con_distributed_workers
    if base_worker_count is None:
        base_worker_count = min(4, max(1, (os.cpu_count() or 2)))
    worker_plan = strain_budget.recommended_worker_count(
        base_worker_count,
        buffer_guard,
        interactive_user_active=interactive_user_active,
    )
    worker_count = int(worker_plan["worker_count"])

    def _scan_overlay_file(item: Dict[str, str]) -> Dict[str, Any]:
        fpath = item["path"]
        ext_l = item["ext"]
        rec = {"path": fpath, "ext": ext_l, "size": None, "tags": []}
        try:
            rec["size"] = os.path.getsize(fpath)
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                head = f.read(5120)
            if "\"nbs_meta\"" in head and "\"content\"" in head:
                rec["tags"].append("gen0_like")
        except Exception:
            rec["tags"].append("scan_error")
        return rec

    if candidates:
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = [executor.submit(_scan_overlay_file, c) for c in candidates]
            for fut in as_completed(futures):
                con_inventory.append(fut.result())

    con_event = {
        "event_type": "learn_overlay",
        "sources": array_normalize_con(con_sources),
        "ingested": array_normalize_con(con_inventory),
        "tags": array_normalize_con(con_tags or ["overlay", "legacy", "read_only"]),
        "requested_workers": base_worker_count,
        "distributed_workers": worker_count,
        "max_buffer_percent": con_max_buffer_percent,
        "interactive_guard": con_interactive_guard,
        "interactive_user_active": interactive_user_active,
        "user_idle_seconds_threshold": con_user_idle_seconds,
        "strain_mode": worker_plan["mode"],
        "strain_snapshot": worker_plan["snapshot"],
        "note": "Indexed legacy/other-AI artifacts for overlay memory",
    }

    con_app = append_event_con(con_project, con_narrative_path, con_event)
    if not con_app.get("success"):
        return con_app

    return {
        "success": True,
        "narrative_path": con_narrative_path,
        "count_files": len(con_inventory),
        "requested_workers": base_worker_count,
        "distributed_workers": worker_count,
        "strain_mode": worker_plan["mode"],
        "sources": con_sources,
    }
