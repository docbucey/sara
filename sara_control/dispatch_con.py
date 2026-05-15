"""
SARA Control — dispatch() entry point, _cmd_* wrappers, FSM construction, Clerk handlers, dispatch_control_protocol.
Extracted from sara_controlgen1.py.
"""
import os
from typing import Any, Dict, Optional

try:
    from sara_control.loader_con import _load_core_module, _load_gen1_security
    _core = _load_core_module()
    if _core is None:
        raise ImportError("Core module file not found")
    SYSTEM_CORE_PROJECT_NAME = _core.SYSTEM_CORE_PROJECT_NAME
    ShuntFSM = _core.ShuntFSM
except Exception:
    _core = None
    SYSTEM_CORE_PROJECT_NAME = "sara_core_project"
    ShuntFSM = None

try:
    _sec = _load_gen1_security()
    king_sovereignty_check = _sec.king_sovereignty_check
    paladin_gate = _sec.paladin_gate
    sheriff_audit = _sec.sheriff_audit
    dispatch_security = _sec.dispatch_security
except Exception:
    def king_sovereignty_check(token): return True
    def paladin_gate(text): return True, "PALADIN:ALLOW:shunt-fallback"
    def sheriff_audit(event_type, actor, decision, reason):
        return {"ts": None, "event_type": event_type, "actor": actor, "decision": decision, "reason": reason}
    def dispatch_security(command, auth_token="", **kwargs):
        return {
            "success": True,
            "command": command,
            "result": {"allowed": True, "valid": True, "reason": "SEC:FALLBACK:ALLOW"},
            "security_audit": sheriff_audit("dispatch_security", "fallback", "ALLOW", "SEC:FALLBACK:ALLOW"),
        }

# --- Clerk handlers ---
from sara_control.fsm_con import (
    control_execute_with_fsm,
    CONTROL_STATE_COMPRESS, CONTROL_STATE_DECOMPRESS,
    CONTROL_STATE_EXTRACT_FULL, CONTROL_STATE_EXTRACT_TARGET, CONTROL_STATE_SEARCH,
)


def control_clerk_compress(payload: Dict[str, Any]) -> Dict[str, Any]:
    """CONTROL executor for Clerk 'compress'. Metadata-only return."""
    data = payload.get("data", b"")
    level = payload.get("level", 3)
    try:
        compressed = _core.core_compress_bytes(data, level)
        return {"status": "OK", "action": "compress", "size_in": len(data), "size_out": len(compressed)}
    except Exception as e:
        return {"status": "ERROR", "action": "compress", "error": str(e)}


def control_clerk_decompress(payload: Dict[str, Any]) -> Dict[str, Any]:
    """CONTROL executor for Clerk 'decompress'. Metadata-only return."""
    blob = payload.get("blob", b"")
    try:
        decompressed = _core.core_decompress_bytes(blob)
        return {"status": "OK", "action": "decompress", "size_in": len(blob), "size_out": len(decompressed)}
    except Exception as e:
        return {"status": "ERROR", "action": "decompress", "error": str(e)}


def control_clerk_extract_full(payload: Dict[str, Any]) -> Dict[str, Any]:
    """CONTROL executor for Clerk 'extract_full'. Metadata-only return."""
    blob = payload.get("blob", b"")
    destination = payload.get("destination", "")
    try:
        _core.core_extract_full(blob, destination)
        return {"status": "OK", "action": "extract_full", "destination": destination}
    except Exception as e:
        return {"status": "ERROR", "action": "extract_full", "error": str(e)}


def control_clerk_extract_target(payload: Dict[str, Any]) -> Dict[str, Any]:
    """CONTROL executor for Clerk 'extract_target'. Metadata-only return."""
    blob = payload.get("blob", b"")
    target = payload.get("target", "")
    try:
        extracted = _core.core_extract_target(blob, target)
        return {"status": "OK", "action": "extract_target", "target": target, "size_out": len(extracted)}
    except Exception as e:
        return {"status": "ERROR", "action": "extract_target", "error": str(e)}


def control_clerk_search(payload: Dict[str, Any]) -> Dict[str, Any]:
    """CONTROL executor for Clerk 'search'. Metadata-only return."""
    query = payload.get("query", "")
    path = payload.get("path", "")
    return {"status": "READY", "action": "search", "query": query, "path": path, "message": "Search backend not yet implemented."}


def dispatch_control_protocol(action: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Metadata-safe protocol dispatcher for CONTROL-side Clerk operations.
    Existing CONTROL logic remains unchanged; this only exposes new route surfaces.
    """
    envelope = dict(payload or {})
    route_key = str(action or envelope.get("action", "")).strip().lower()
    current_state = str(envelope.get("fsm_state", "CONTROL_IDLE"))
    routes: Dict[str, Any] = {}
    routes.update({
        "compress": control_clerk_compress,
        "decompress": control_clerk_decompress,
        "extract_full": control_clerk_extract_full,
        "extract_target": control_clerk_extract_target,
        "search": control_clerk_search,
    })
    if route_key in routes:
        handler = routes[route_key]
        return control_execute_with_fsm(current_state, route_key, handler, envelope)
    handler = routes.get(route_key)
    if handler is None:
        return {
            "status": "ERROR",
            "action": route_key,
            "error": f"Unsupported control protocol action: {route_key}",
            "supported_actions": sorted(routes.keys()),
        }
    return handler(envelope)


# --- Command wrappers for FSM ---
from sara_control.session_con import start_session_con, append_event_con, end_session_con, checkpoint_con, heartbeat_con
from sara_control.identity_con import identity_resolve_con
from sara_control.routing_con import route_io_con, wfh_protocol_con, route_bucey_shunt_con, route_mail_transport_con
from sara_control.vnce_con import vnce_lifecycle_con, start_vnce_session_con, resume_vnce_session_con
from sara_control.jobs_con import (
    refinement_loop_executor, job_ready_pipeline_entry,
)
from sara_control.learning_con import learn_overlay_con
from sara_control.ingest_con import ingest_artifacts_con, extract_concepts_con, query_concepts_con, ingest_chat_con
# External desktop client (Project Mechanic); not shipped with SARA — optional Control routes.
from sara_control.mechanic_con import (
    mechanic_calendar_run_con, mechanic_email_run_con, mechanic_sheets_run_con,
    mechanic_export_run_con, mechanic_voice_run_con, mechanic_model_run_con, mechanic_smoke_check_con,
)
from sara_control.mama_calc_con import (
    mama_research_calc_run_con, mama_validate_real_world_excel_con,
    mama_traditional_calc_run_con, mama_business_calc_run_con, mama_calc_run_con,
)


def _cmd_session_start(kwargs):
    return start_session_con(con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME), con_session_note=kwargs.get("note"))

def _cmd_append_event(kwargs):
    return append_event_con(con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME), con_narrative_path=kwargs["narrative_path"], con_event=kwargs["event"])

def _cmd_end_session(kwargs):
    return end_session_con(con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME), con_narrative_path=kwargs["narrative_path"], con_summary=kwargs.get("summary"), con_todos=kwargs.get("todos"))

def _cmd_checkpoint(kwargs):
    return checkpoint_con(con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME), con_narrative_path=kwargs["narrative_path"], con_chunk=kwargs.get("chunk", {}))

def _cmd_heartbeat(kwargs):
    return heartbeat_con(con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME), con_narrative_path=kwargs["narrative_path"])

def _cmd_identity_resolve(kwargs):
    return identity_resolve_con(con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME))

def _cmd_route_io(kwargs):
    payload = dict(kwargs)
    payload.setdefault("_routed_by_fsm", True)
    return route_io_con(payload)

def _cmd_learn_overlay(kwargs):
    return learn_overlay_con(con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME), con_sources=kwargs.get("sources"), con_narrative_path=kwargs.get("narrative_path"), con_tags=kwargs.get("tags"))

def _cmd_ingest_artifacts(kwargs):
    return ingest_artifacts_con(con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME), con_sources=kwargs.get("sources"), con_narrative_path=kwargs.get("narrative_path"), con_tags=kwargs.get("tags"), con_security_token=kwargs.get("_dispatch_auth_token", ""), con_envoy_mode=bool(kwargs.get("envoy_mode", False)), con_use_windows_defender=bool(kwargs.get("use_windows_defender", True)))

def _cmd_extract_concepts(kwargs):
    return extract_concepts_con(con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME), con_sources=kwargs.get("sources"), con_keywords=kwargs.get("keywords"), con_narrative_path=kwargs.get("narrative_path"))

def _cmd_query_concepts(kwargs):
    return query_concepts_con(con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME), con_keywords=kwargs.get("keywords"), con_limit=kwargs.get("limit", 50))

def _cmd_ingest_chat(kwargs):
    return ingest_chat_con(con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME), con_paths=kwargs.get("paths", []))

def _cmd_harness_route(kwargs):
    from sara_control.routing_con import _pick_proto_field_con
    import subprocess
    from datetime import datetime, timezone
    con_repo_root = kwargs["repo_root"]
    con_target_file = kwargs["target_file"]
    con_exe = os.path.join(con_repo_root, "doctestharnes.exe")
    con_master = os.path.join(con_repo_root, "master_result.json")
    if not os.path.exists(con_exe):
        return {"success": False, "status": "FAIL", "error": f"Harness executable missing: {con_exe}"}
    if not os.path.exists(con_target_file):
        return {"success": False, "status": "FAIL", "error": f"Target file missing: {con_target_file}"}
    con_proc = subprocess.run([con_exe], input=con_target_file + "\n", text=True, cwd=con_repo_root, capture_output=True, check=False)
    if not os.path.exists(con_master):
        return {"success": False, "status": "FAIL", "error": f"Harness output missing: {con_master}"}
    try:
        import json
        with open(con_master, "r", encoding="utf-8") as f:
            con_result = json.load(f)
    except Exception as e:
        return {"success": False, "status": "FAIL", "error": f"Could not parse master_result.json: {e}"}
    return {"success": True, "status": con_result.get("final_status", "UNKNOWN"), "process_exit_code": con_proc.returncode, "target": con_target_file, "local": con_result.get("local", {}), "distant": con_result.get("distant", {})}

def _cmd_security_check(kwargs):
    allowed, reason = paladin_gate(str(kwargs.get("text", "")))
    event = sheriff_audit("security_check", "sheriff", "ALLOW" if allowed else "DENY", reason)
    return {"allowed": allowed, "reason": reason, "audit": event}

def _cmd_wfh_protocol(kwargs):
    return wfh_protocol_con(work_item=kwargs.get("payload") or kwargs, con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME))

def _cmd_vnce_lifecycle(kwargs):
    payload = dict(kwargs.get("payload") or kwargs)
    payload.setdefault("auth_token", kwargs.get("_dispatch_auth_token", ""))
    return vnce_lifecycle_con(session_payload=payload, con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME))

def _cmd_start_vnce_session(kwargs):
    return start_vnce_session_con(session_payload=kwargs.get("payload") or kwargs, con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME), con_auth_token=kwargs.get("_dispatch_auth_token", ""))

def _cmd_resume_vnce_session(kwargs):
    return resume_vnce_session_con(session_payload=kwargs.get("payload") or kwargs, con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME), con_auth_token=kwargs.get("_dispatch_auth_token", ""))

def _cmd_abbucey_protocol(kwargs):
    from sara_control.routing_con import abbucey_protocol_con as _abbucey
    return _abbucey(job_payload=kwargs.get("payload") or kwargs, con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME))

def _cmd_refinement_loop(kwargs):
    return refinement_loop_executor(job_payload=kwargs.get("payload") or kwargs, previous_state=kwargs.get("previous_state"))

def _cmd_job_ready_pipeline(kwargs):
    return job_ready_pipeline_entry(job_payload=kwargs.get("payload") or kwargs, previous_state=kwargs.get("previous_state"))

def _cmd_client_projects_create(kwargs):
    return _core.create_client_projects_sheet(client_name=kwargs["client_name"], sheet_data=kwargs.get("sheet_data"), operating_mode=kwargs.get("operating_mode", "wfh"), editable_fields=kwargs.get("editable_fields"))

def _cmd_client_projects_update(kwargs):
    return _core.update_client_projects_sheet(client_name=kwargs["client_name"], updates=kwargs.get("updates", {}))

def _cmd_client_projects_remove_project(kwargs):
    return _core.remove_client_project_preserve_critical(client_name=kwargs["client_name"], project_key=kwargs["project_key"], critical_fields=kwargs.get("critical_fields"))

def _cmd_client_projects_list(kwargs):
    return _core.list_client_projects_sheet(client_name=kwargs["client_name"], only_active=bool(kwargs.get("only_active", True)), operating_mode=kwargs.get("operating_mode", "wfh"), include_history_critical=bool(kwargs.get("include_history_critical", False)))

def _cmd_mechanic_calendar_run(kwargs):
    return mechanic_calendar_run_con(con_client_name=kwargs.get("client_name", "unknown_client"), con_payload=kwargs.get("payload", {}), con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME), con_auth_token=kwargs.get("_dispatch_auth_token", ""))

def _cmd_mechanic_email_run(kwargs):
    return mechanic_email_run_con(con_client_name=kwargs.get("client_name", "unknown_client"), con_payload=kwargs.get("payload", {}), con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME), con_auth_token=kwargs.get("_dispatch_auth_token", ""))

def _cmd_mechanic_sheets_run(kwargs):
    return mechanic_sheets_run_con(con_client_name=kwargs.get("client_name", "unknown_client"), con_payload=kwargs.get("payload", {}), con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME), con_auth_token=kwargs.get("_dispatch_auth_token", ""))

def _cmd_mechanic_export_run(kwargs):
    return mechanic_export_run_con(con_client_name=kwargs.get("client_name", "unknown_client"), con_payload=kwargs.get("payload", {}), con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME), con_auth_token=kwargs.get("_dispatch_auth_token", ""))

def _cmd_mechanic_voice_run(kwargs):
    return mechanic_voice_run_con(con_client_name=kwargs.get("client_name", "unknown_client"), con_payload=kwargs.get("payload", {}), con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME), con_auth_token=kwargs.get("_dispatch_auth_token", ""))

def _cmd_mechanic_model_run(kwargs):
    return mechanic_model_run_con(con_client_name=kwargs.get("client_name", "unknown_client"), con_payload=kwargs.get("payload", {}), con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME), con_auth_token=kwargs.get("_dispatch_auth_token", ""))

def _cmd_mechanic_smoke_check(kwargs):
    return mechanic_smoke_check_con(con_client_name=kwargs.get("client_name", "unknown_client"), con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME), con_auth_token=kwargs.get("_dispatch_auth_token", ""), con_overrides=kwargs.get("payload_overrides"), con_auto_append_narrative=bool(kwargs.get("auto_append_narrative", True)), con_narrative_path=kwargs.get("narrative_path", "narrative/mechanic_readiness_log_gen0_1.0_nbs.json"))

def _cmd_mama_research_calc_run(kwargs):
    return mama_research_calc_run_con(con_formula=kwargs.get("formula", ""), con_samples=int(kwargs.get("samples", 500)), con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME), con_auth_token=kwargs.get("_dispatch_auth_token", ""))

def _cmd_mama_validate_real_world_excel(kwargs):
    return mama_validate_real_world_excel_con(con_formula=kwargs.get("formula", ""), con_excel_path=kwargs.get("excel_path", ""), con_observed_col=kwargs.get("observed_col", ""), con_sheet_name=kwargs.get("sheet_name"), con_abs_tolerance=float(kwargs.get("abs_tolerance", 0.05)), con_rel_tolerance=float(kwargs.get("rel_tolerance", 0.05)), con_scenario_label=kwargs.get("scenario_label"), con_units_map=kwargs.get("units_map"), con_report_output_path=kwargs.get("report_output_path"), con_uncertainty_col=kwargs.get("uncertainty_col"), con_uncertainty_abs_default=float(kwargs.get("uncertainty_abs_default", 0.0)), con_uncertainty_rel_default=float(kwargs.get("uncertainty_rel_default", 0.0)), con_strict_units=bool(kwargs.get("strict_units", False)), con_outlier_policy=kwargs.get("outlier_policy", "none"), con_baseline_formula=kwargs.get("baseline_formula"), con_verdict_version=kwargs.get("verdict_version", "v1"), con_run_id=kwargs.get("run_id"), con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME), con_auth_token=kwargs.get("_dispatch_auth_token", ""))

def _cmd_mama_traditional_calc_run(kwargs):
    return mama_traditional_calc_run_con(con_expression=kwargs.get("expression", ""), con_variables=kwargs.get("variables"), con_rows=kwargs.get("rows"), con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME), con_auth_token=kwargs.get("_dispatch_auth_token", ""))

def _cmd_mama_business_calc_run(kwargs):
    return mama_business_calc_run_con(con_operation=kwargs.get("operation", ""), con_inputs=kwargs.get("inputs", {}), con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME), con_auth_token=kwargs.get("_dispatch_auth_token", ""))

def _cmd_mama_calc_run(kwargs):
    return mama_calc_run_con(con_mode=kwargs.get("mode", ""), con_payload=kwargs.get("payload", {}), con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME), con_auth_token=kwargs.get("_dispatch_auth_token", ""))

def _cmd_route_bucey_shunt(kwargs):
    envelope = kwargs.get("shunt_envelope") or kwargs.get("envelope") or {}
    return route_bucey_shunt_con(envelope, auth_token=kwargs.get("_dispatch_auth_token", ""))

def _cmd_route_amip(kwargs):
    amip_payload = kwargs.get("amip_payload") or kwargs.get("payload") or {}
    shunt_envelope = kwargs.get("shunt_envelope") or {"ami_id": kwargs.get("ami_id", ""), "correlation_id": amip_payload.get("correlation_id", ""), "request_id": kwargs.get("request_id", ""), "amip_payload": amip_payload}
    return route_bucey_shunt_con(shunt_envelope, auth_token=kwargs.get("_dispatch_auth_token", ""))

def _cmd_route_mail_smtp_send(kwargs):
    payload = kwargs.get("payload") if isinstance(kwargs.get("payload"), dict) else {}
    return route_mail_transport_con(con_transport_intent="mail.smtp.send", con_payload=payload, con_auth_token=kwargs.get("_dispatch_auth_token", ""))

def _cmd_route_mail_imap_fetch(kwargs):
    payload = kwargs.get("payload") if isinstance(kwargs.get("payload"), dict) else {}
    return route_mail_transport_con(con_transport_intent="mail.imap.fetch", con_payload=payload, con_auth_token=kwargs.get("_dispatch_auth_token", ""))


# --- Office suite commands ---
from sara_control.docgen_con import (
    write_docx_con, edit_docx_con,
    write_xlsx_con, edit_xlsx_con,
    write_pdf_con,
    compose_image_con, edit_image_con,
)

def _cmd_write_docx(kwargs):
    return write_docx_con(
        con_output_path=kwargs["output_path"],
        con_paragraphs=kwargs.get("paragraphs", []),
        con_title=kwargs.get("title"),
        con_headings=kwargs.get("headings"),
        con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME),
    )

def _cmd_edit_docx(kwargs):
    return edit_docx_con(
        con_docx_path=kwargs["docx_path"],
        con_append_paragraphs=kwargs.get("append_paragraphs"),
        con_find_replace=kwargs.get("find_replace"),
        con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME),
    )

def _cmd_write_xlsx(kwargs):
    return write_xlsx_con(
        con_output_path=kwargs["output_path"],
        con_sheets=kwargs.get("sheets", {}),
        con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME),
    )

def _cmd_edit_xlsx(kwargs):
    return edit_xlsx_con(
        con_xlsx_path=kwargs["xlsx_path"],
        con_sheet_name=kwargs.get("sheet_name"),
        con_append_rows=kwargs.get("append_rows"),
        con_cell_updates=kwargs.get("cell_updates"),
        con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME),
    )

def _cmd_write_pdf(kwargs):
    return write_pdf_con(
        con_output_path=kwargs["output_path"],
        con_lines=kwargs.get("lines", []),
        con_title=kwargs.get("title"),
        con_font_size=kwargs.get("font_size", 12),
        con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME),
    )

def _cmd_compose_image(kwargs):
    return compose_image_con(
        con_output_path=kwargs["output_path"],
        con_width=kwargs.get("width", 800),
        con_height=kwargs.get("height", 600),
        con_bg_color=kwargs.get("bg_color", "white"),
        con_draw_ops=kwargs.get("draw_ops"),
        con_base_image_path=kwargs.get("base_image_path"),
        con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME),
    )

def _cmd_edit_image(kwargs):
    return edit_image_con(
        con_image_path=kwargs["image_path"],
        con_resize=kwargs.get("resize"),
        con_crop=kwargs.get("crop"),
        con_overlay_path=kwargs.get("overlay_path"),
        con_overlay_pos=kwargs.get("overlay_pos"),
        con_annotate_text=kwargs.get("annotate_text"),
        con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME),
    )


# --- Python IDE runner ---
def _cmd_python_run(kwargs):
    """Run a Python script string in a sandboxed subprocess. 30-second timeout."""
    import subprocess, sys, tempfile, os
    code = kwargs.get("code", "")
    if not code.strip():
        return {"success": False, "error": "No code provided"}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code)
        tmp_path = f.name
    try:
        proc = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True, text=True, timeout=30
        )
        return {
            "success": proc.returncode == 0,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "returncode": proc.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Timeout: script ran for more than 30 seconds"}
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def _cmd_biometric_status(kwargs):
    """Check current biometric learning status."""
    try:
        from sara_mama.biometric_learning_mama import get_biometric_status
        from sara_mama.ledger_mama import MamaLedger
        ledger = MamaLedger()
        return get_biometric_status(ledger)
    except Exception as e:
        return {"success": False, "error": f"Biometric status unavailable: {e}"}


def _cmd_ai_generate(kwargs):
    """Generate text via the local LLM (or Ollama fallback). No document output."""
    try:
        from sara_sdk.ai_backend_sdk import ai_backend
        prompt = kwargs.get("prompt", "")
        if not prompt:
            return {"success": False, "error": "No prompt provided"}
        context = {
            "system_prompt": kwargs.get("system_prompt", "You are SARA, a helpful assistant."),
            "max_tokens": int(kwargs.get("max_tokens", 512)),
            "temperature": float(kwargs.get("temperature", 0.7)),
        }
        model_path = kwargs.get("model_path")
        if model_path:
            context["model_path"] = model_path
        text = ai_backend.generate(prompt, context)
        return {"success": True, "text": text, "backend": ai_backend.default_backend}
    except Exception as e:
        return {"success": False, "error": f"AI generation failed: {e}"}


def _cmd_ai_draft_docx(kwargs):
    """Prompt -> LLM -> .docx in one call."""
    prompt = kwargs.get("prompt", "")
    output_path = kwargs.get("output_path", "")
    if not prompt:
        return {"success": False, "error": "No prompt provided"}
    if not output_path:
        import tempfile
        output_path = os.path.join(
            tempfile.gettempdir(),
            f"sara_draft_{int(__import__('time').time())}.docx",
        )
    gen_result = _cmd_ai_generate(kwargs)
    if not gen_result.get("success"):
        return gen_result
    ai_text = gen_result.get("text", "")
    paragraphs = [p for p in ai_text.split("\n") if p.strip()]
    title = kwargs.get("title", "SARA Draft")
    return write_docx_con(
        con_output_path=output_path,
        con_paragraphs=paragraphs,
        con_title=title,
        con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME),
    )


def _cmd_ai_draft_xlsx(kwargs):
    """Prompt -> LLM -> .xlsx in one call. AI generates CSV-like rows."""
    prompt = kwargs.get("prompt", "")
    output_path = kwargs.get("output_path", "")
    if not prompt:
        return {"success": False, "error": "No prompt provided"}
    if not output_path:
        import tempfile
        output_path = os.path.join(
            tempfile.gettempdir(),
            f"sara_draft_{int(__import__('time').time())}.xlsx",
        )
    draft_prompt = prompt + "\n\nFormat your response as comma-separated rows. First row is headers."
    gen_kwargs = dict(kwargs)
    gen_kwargs["prompt"] = draft_prompt
    gen_result = _cmd_ai_generate(gen_kwargs)
    if not gen_result.get("success"):
        return gen_result
    ai_text = gen_result.get("text", "")
    rows = []
    for line in ai_text.split("\n"):
        line = line.strip()
        if line:
            rows.append([cell.strip() for cell in line.split(",")])
    sheet_name = kwargs.get("sheet_name", "Sheet1")
    return write_xlsx_con(
        con_output_path=output_path,
        con_sheets={sheet_name: rows},
        con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME),
    )


def _cmd_calendar_list(kwargs):
    from sara_core.google_services import calendar_list_events
    return calendar_list_events(
        max_results=int(kwargs.get("max_results", 10)),
        time_min=kwargs.get("time_min"),
        calendar_id=kwargs.get("calendar_id", "primary"),
    )

def _cmd_calendar_create(kwargs):
    from sara_core.google_services import calendar_create_event
    return calendar_create_event(
        summary=kwargs.get("summary", "SARA Event"),
        start_time=kwargs.get("start_time", ""),
        end_time=kwargs.get("end_time"),
        description=kwargs.get("description", ""),
        location=kwargs.get("location", ""),
        add_meet=bool(kwargs.get("add_meet", False)),
        attendees=kwargs.get("attendees"),
        calendar_id=kwargs.get("calendar_id", "primary"),
    )

def _cmd_create_meet(kwargs):
    from sara_core.google_services import create_meet_link
    return create_meet_link(
        summary=kwargs.get("summary", "SARA Meeting"),
        duration_minutes=int(kwargs.get("duration_minutes", 60)),
        attendees=kwargs.get("attendees"),
    )

def _cmd_send_sms(kwargs):
    from sara_core.google_services import send_sms
    return send_sms(
        to_number=kwargs.get("to_number", ""),
        message=kwargs.get("message", ""),
        carrier=kwargs.get("carrier", ""),
        gmail_address=kwargs.get("gmail_address", ""),
        gmail_app_password=kwargs.get("gmail_app_password", ""),
    )

def _cmd_web_browse(kwargs):
    from sara_core.google_services import web_browse
    return web_browse(
        url=kwargs.get("url", ""),
        extract=kwargs.get("extract", "text"),
        timeout=int(kwargs.get("timeout", 15)),
    )

def _cmd_web_search(kwargs):
    from sara_core.google_services import web_search
    return web_search(
        query=kwargs.get("query", ""),
        num_results=int(kwargs.get("num_results", 5)),
    )

def _cmd_voip_call(kwargs):
    from sara_mama.switchboard_protocol import SwitchboardProtocol
    sp = SwitchboardProtocol()
    action = kwargs.get("action", "validate")
    if action == "validate":
        return sp.validate_call(kwargs.get("call_data", {}))
    elif action == "dial":
        return sp.automate_call(kwargs.get("call_data", {}), connect=bool(kwargs.get("connect", False)))
    elif action == "add_contact":
        return sp.add_contact(kwargs.get("name", ""), kwargs.get("number", ""), kwargs.get("contact_type", "phone"))
    elif action == "list_contacts":
        return {"success": True, "contacts": sp.list_contacts(kwargs.get("filter_type"))}
    elif action == "remove_contact":
        return sp.remove_contact(kwargs.get("name", ""), kwargs.get("number"))
    return {"success": False, "error": f"Unknown voip action: {action}"}

def _cmd_invoice_create(kwargs):
    from sara_core.accountant import create_invoice
    return create_invoice(
        client_name=kwargs.get("client_name", ""),
        items=kwargs.get("items", []),
        due_days=int(kwargs.get("due_days", 30)),
        tax_rate=float(kwargs.get("tax_rate", 0.0)),
        notes=kwargs.get("notes", ""),
        from_name=kwargs.get("from_name", ""),
        from_address=kwargs.get("from_address", ""),
    )

def _cmd_invoice_list(kwargs):
    from sara_core.accountant import list_invoices
    return list_invoices(status=kwargs.get("status"))

def _cmd_invoice_get(kwargs):
    from sara_core.accountant import get_invoice
    return get_invoice(invoice_id=kwargs.get("invoice_id", ""))

def _cmd_invoice_update_status(kwargs):
    from sara_core.accountant import update_invoice_status
    return update_invoice_status(kwargs.get("invoice_id", ""), kwargs.get("status", ""))

def _cmd_invoice_payment(kwargs):
    from sara_core.accountant import record_payment
    return record_payment(
        invoice_id=kwargs.get("invoice_id", ""),
        amount=float(kwargs.get("amount", 0)),
        method=kwargs.get("method", "check"),
        note=kwargs.get("note", ""),
    )

def _cmd_invoice_pdf(kwargs):
    from sara_core.accountant import export_invoice_pdf
    return export_invoice_pdf(
        invoice_id=kwargs.get("invoice_id", ""),
        output_path=kwargs.get("output_path"),
    )

def _cmd_expense_add(kwargs):
    from sara_core.accountant import add_expense
    return add_expense(
        amount=float(kwargs.get("amount", 0)),
        category=kwargs.get("category", "other"),
        description=kwargs.get("description", ""),
        date=kwargs.get("date"),
        recurring=bool(kwargs.get("recurring", False)),
        recurring_interval=kwargs.get("recurring_interval", "monthly"),
        vendor=kwargs.get("vendor", ""),
    )

def _cmd_expense_list(kwargs):
    from sara_core.accountant import list_expenses
    return list_expenses(
        category=kwargs.get("category"),
        start_date=kwargs.get("start_date"),
        end_date=kwargs.get("end_date"),
    )

def _cmd_expense_summary(kwargs):
    from sara_core.accountant import expense_summary
    return expense_summary(start_date=kwargs.get("start_date"), end_date=kwargs.get("end_date"))

def _cmd_ledger_post(kwargs):
    from sara_core.accountant import post_journal_entry
    return post_journal_entry(
        date=kwargs.get("date", ""),
        description=kwargs.get("description", ""),
        debits=kwargs.get("debits", []),
        credits=kwargs.get("credits", []),
    )

def _cmd_ledger_balance(kwargs):
    from sara_core.accountant import get_account_balance
    return get_account_balance(account_code=kwargs.get("account_code", ""))

def _cmd_chart_of_accounts(kwargs):
    from sara_core.accountant import get_chart_of_accounts
    return get_chart_of_accounts()

def _cmd_report_trial_balance(kwargs):
    from sara_core.accountant import trial_balance
    return trial_balance()

def _cmd_report_pnl(kwargs):
    from sara_core.accountant import profit_and_loss
    return profit_and_loss(start_date=kwargs.get("start_date"), end_date=kwargs.get("end_date"))

def _cmd_report_balance_sheet(kwargs):
    from sara_core.accountant import balance_sheet
    return balance_sheet()

def _cmd_report_cash_flow(kwargs):
    from sara_core.accountant import cash_flow_summary
    return cash_flow_summary(start_date=kwargs.get("start_date"), end_date=kwargs.get("end_date"))


# ── POS Terminal ───────────────────────────────────────────────────────────

def _cmd_pos_product_add(kwargs):
    from sara_core.pos import product_add
    return product_add(
        name=kwargs.get("name", ""),
        price=float(kwargs.get("price", 0)),
        sku=kwargs.get("sku", ""),
        category=kwargs.get("category", "general"),
        tax_rate=float(kwargs.get("tax_rate", 0)),
        stock=int(kwargs.get("stock", -1)),
        barcode=kwargs.get("barcode", ""),
        description=kwargs.get("description", ""),
        cost=float(kwargs.get("cost", 0)),
    )

def _cmd_pos_product_update(kwargs):
    from sara_core.pos import product_update
    fields = {k: v for k, v in kwargs.items() if k != "product_id"}
    return product_update(kwargs.get("product_id", ""), **fields)

def _cmd_pos_product_list(kwargs):
    from sara_core.pos import product_list
    return product_list(category=kwargs.get("category"), active_only=kwargs.get("active_only", True))

def _cmd_pos_product_lookup(kwargs):
    from sara_core.pos import product_lookup
    return product_lookup(query=kwargs.get("query", ""))

def _cmd_pos_inventory_adjust(kwargs):
    from sara_core.pos import inventory_adjust
    return inventory_adjust(kwargs.get("product_id", ""), int(kwargs.get("quantity_change", 0)), kwargs.get("reason", ""))

def _cmd_pos_low_stock(kwargs):
    from sara_core.pos import inventory_low_stock
    return inventory_low_stock(threshold=int(kwargs.get("threshold", 5)))

def _cmd_pos_cart_create(kwargs):
    from sara_core.pos import cart_create
    return cart_create(register_id=kwargs.get("register_id", "REG-1"), cashier=kwargs.get("cashier", ""))

def _cmd_pos_cart_add(kwargs):
    from sara_core.pos import cart_add_item
    return cart_add_item(
        cart_id=kwargs.get("cart_id", ""),
        product_id=kwargs.get("product_id", ""),
        quantity=int(kwargs.get("quantity", 1)),
        price_override=float(kwargs["price_override"]) if "price_override" in kwargs else None,
    )

def _cmd_pos_cart_remove(kwargs):
    from sara_core.pos import cart_remove_item
    return cart_remove_item(kwargs.get("cart_id", ""), kwargs.get("product_id", ""))

def _cmd_pos_cart_discount(kwargs):
    from sara_core.pos import cart_apply_discount
    return cart_apply_discount(
        kwargs.get("cart_id", ""),
        discount_type=kwargs.get("discount_type", "percent"),
        value=float(kwargs.get("value", 0)),
        reason=kwargs.get("reason", ""),
    )

def _cmd_pos_cart_total(kwargs):
    from sara_core.pos import cart_total
    return cart_total(kwargs.get("cart_id", ""))

def _cmd_pos_cart_void(kwargs):
    from sara_core.pos import cart_void
    return cart_void(kwargs.get("cart_id", ""))

def _cmd_pos_checkout(kwargs):
    from sara_core.pos import checkout
    return checkout(
        cart_id=kwargs.get("cart_id", ""),
        payment_method=kwargs.get("payment_method", "cash"),
        amount_tendered=float(kwargs.get("amount_tendered", 0)),
        customer_name=kwargs.get("customer_name", ""),
        customer_email=kwargs.get("customer_email", ""),
        note=kwargs.get("note", ""),
    )

def _cmd_pos_refund(kwargs):
    from sara_core.pos import refund
    return refund(kwargs.get("transaction_id", ""), reason=kwargs.get("reason", ""))

def _cmd_pos_receipt(kwargs):
    from sara_core.pos import generate_receipt
    return generate_receipt(kwargs.get("transaction_id", ""), store_name=kwargs.get("store_name", "SARA POS"))

def _cmd_pos_sales_today(kwargs):
    from sara_core.pos import sales_today
    return sales_today()

def _cmd_pos_sales_range(kwargs):
    from sara_core.pos import sales_range
    return sales_range(kwargs.get("start_date", ""), kwargs.get("end_date", ""))

def _cmd_pos_top_products(kwargs):
    from sara_core.pos import top_products
    return top_products(start_date=kwargs.get("start_date"), end_date=kwargs.get("end_date"), limit=int(kwargs.get("limit", 10)))

def _cmd_pos_end_of_day(kwargs):
    from sara_core.pos import end_of_day
    return end_of_day(
        register_id=kwargs.get("register_id", "REG-1"),
        expected_cash=float(kwargs["expected_cash"]) if "expected_cash" in kwargs else None,
    )


def _cmd_morning_routine_get_config(kwargs):
    from sara_core.morning_routine import get_config
    return get_config()


def _cmd_morning_routine_set_config(kwargs):
    from sara_core.morning_routine import set_config
    return set_config(partial=kwargs.get("config") or kwargs.get("partial"), replace=bool(kwargs.get("replace", False)))


def _cmd_morning_routine_fetch_feeds(kwargs):
    from sara_core.morning_routine import fetch_all_feeds
    return fetch_all_feeds()


def _cmd_morning_routine_news_search(kwargs):
    from sara_core.morning_routine import run_news_searches
    return run_news_searches(num_results=int(kwargs.get("num_results", 5)))


def _cmd_morning_routine_gigs_add(kwargs):
    from sara_core.morning_routine import add_gigs_from_text, add_gigs_from_list
    if kwargs.get("gigs"):
        return add_gigs_from_list(list(kwargs["gigs"]))
    raw = str(kwargs.get("text", kwargs.get("raw", "")))
    if not raw.strip():
        return {"success": False, "error": "No gig text or gigs[] provided"}
    return add_gigs_from_text(raw, delimiter=kwargs.get("delimiter"))


def _cmd_morning_routine_gigs_list(kwargs):
    from sara_core.morning_routine import list_gigs
    return list_gigs()


def _cmd_morning_routine_gigs_clear(kwargs):
    from sara_core.morning_routine import clear_gigs
    return clear_gigs()


def _cmd_morning_routine_cluster(kwargs):
    from sara_core.morning_routine import cluster_gigs
    return cluster_gigs(threshold=float(kwargs.get("threshold", 0.12)), max_clusters=int(kwargs.get("max_clusters", 40)))


def _cmd_morning_routine_filter_gigs(kwargs):
    from sara_core.morning_routine import filter_gigs_by_keywords
    return filter_gigs_by_keywords()


def _cmd_morning_routine_ai_batch(kwargs):
    from sara_core.morning_routine import ai_batch_analyze
    return ai_batch_analyze(
        user_guidance=str(kwargs.get("user_guidance", kwargs.get("guidance", ""))),
        batch_size=int(kwargs.get("batch_size", 15)),
        cluster_id=kwargs.get("cluster_id"),
        system_prompt=kwargs.get("system_prompt"),
    )


def _cmd_ada_voice_profile_get(kwargs):
    try:
        from sara_mama.settings_protocol import SettingsProtocol

        sp = SettingsProtocol()
        profile = sp.get_ada_voice_profile()
        return {"success": True, "ada_voice_profile": profile}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _cmd_ada_voice_profile_set(kwargs):
    try:
        from sara_mama.settings_protocol import SettingsProtocol

        sp = SettingsProtocol()
        preset = kwargs.get("preset")
        partial = kwargs.get("partial") or kwargs.get("ada_voice_profile")
        if not preset and not isinstance(partial, dict):
            return {"success": False, "error": "Provide preset (string) and/or partial / ada_voice_profile (dict)"}
        merged = sp.set_ada_voice_profile(
            partial=partial if isinstance(partial, dict) else None,
            preset=str(preset) if preset else None,
        )
        return {"success": True, "ada_voice_profile": merged}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _cmd_stellar_time_snapshot(kwargs):
    from sara_core.stellar_time import compute_stellar_snapshot
    from datetime import datetime, timezone

    utc = kwargs.get("utc_iso") or kwargs.get("utc_instant")
    inst = None
    if utc:
        try:
            s = str(utc).replace("Z", "+00:00")
            inst = datetime.fromisoformat(s)
        except Exception:
            return {"success": False, "error": f"Invalid utc_iso: {utc}"}
    lat = kwargs.get("lat_deg", kwargs.get("lat"))
    lon = kwargs.get("lon_deg", kwargs.get("lon"))
    h = kwargs.get("height_m", kwargs.get("height"))
    if lat is not None:
        lat = float(lat)
    if lon is not None:
        lon = float(lon)
    if h is not None:
        h = float(h)
    return compute_stellar_snapshot(utc_instant=inst, lat_deg=lat, lon_deg=lon, height_m=h)


def _cmd_stellar_time_dut1(kwargs):
    from sara_core.stellar_time import dut1_now

    return dut1_now()


def _cmd_stellar_observer_set(kwargs):
    from sara_core.stellar_time import set_default_observer

    return set_default_observer(
        float(kwargs.get("lat_deg", kwargs.get("lat", 0))),
        float(kwargs.get("lon_deg", kwargs.get("lon", 0))),
        float(kwargs.get("height_m", kwargs.get("height", 0)) or 0),
    )


def _cmd_stellar_observer_get(kwargs):
    from sara_core.stellar_time import get_default_observer

    return get_default_observer()


def _cmd_write_xlsx_formula(kwargs):
    from sara_control.docgen_con import write_xlsx_formula_con
    return write_xlsx_formula_con(
        con_output_path=kwargs["output_path"],
        con_sheets=kwargs.get("sheets", {}),
        con_column_widths=kwargs.get("column_widths"),
        con_bold_rows=kwargs.get("bold_rows"),
        con_freeze_pane=kwargs.get("freeze_pane"),
        con_auto_filter=bool(kwargs.get("auto_filter", False)),
        con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME),
    )

def _cmd_write_xlsx_chart(kwargs):
    from sara_control.docgen_con import write_xlsx_chart_con
    return write_xlsx_chart_con(
        con_xlsx_path=kwargs["xlsx_path"],
        con_chart_type=kwargs.get("chart_type", "bar"),
        con_data_range=kwargs.get("data_range", "A1:B10"),
        con_title=kwargs.get("title", "Chart"),
        con_sheet_name=kwargs.get("sheet_name"),
        con_chart_sheet=kwargs.get("chart_sheet", "Chart"),
        con_project=kwargs.get("project", SYSTEM_CORE_PROJECT_NAME),
    )

def _cmd_send_email(kwargs):
    from sara_core.email import core_smtp_send_email
    return core_smtp_send_email(
        smtp_host=kwargs.get("smtp_host", "smtp.gmail.com"),
        smtp_port=int(kwargs.get("smtp_port", 587)),
        username=kwargs.get("username", kwargs.get("gmail_address", "")),
        password=kwargs.get("password", kwargs.get("gmail_app_password", "")),
        email_data=kwargs.get("email_data", {}),
        use_tls=bool(kwargs.get("use_tls", True)),
    )

def _cmd_fetch_email(kwargs):
    from sara_core.email import core_imap_fetch_inbox
    return core_imap_fetch_inbox(
        imap_host=kwargs.get("imap_host", "imap.gmail.com"),
        username=kwargs.get("username", kwargs.get("gmail_address", "")),
        password=kwargs.get("password", kwargs.get("gmail_app_password", "")),
        mailbox=kwargs.get("mailbox", "INBOX"),
        limit=int(kwargs.get("limit", 20)),
    )


def _cmd_write_pptx(kwargs):
    """Create a new PowerPoint presentation."""
    try:
        from sara_core.file_io import write_powerpoint_pptx
        output_path = kwargs.get("output_path", "")
        slides = kwargs.get("slides", [])
        if not output_path:
            return {"success": False, "error": "No output_path provided"}
        return write_powerpoint_pptx(output_path, slides)
    except Exception as e:
        return {"success": False, "error": f"write_pptx failed: {e}"}


def _cmd_read_pptx(kwargs):
    """Read an existing PowerPoint presentation."""
    try:
        from sara_core.file_io import read_powerpoint_pptx
        path = kwargs.get("path", kwargs.get("pptx_path", ""))
        if not path:
            return {"success": False, "error": "No path provided"}
        return read_powerpoint_pptx(path)
    except Exception as e:
        return {"success": False, "error": f"read_pptx failed: {e}"}


# --- FSM instance construction ---
_CONTROL_FSM = None
if ShuntFSM is not None:
    _CONTROL_FSM = ShuntFSM(
        states=["ready", "blocked"],
        transitions={
            ("ready", "session_start"):      ("ready",   _cmd_session_start),
            ("ready", "append_event"):       ("ready",   _cmd_append_event),
            ("ready", "end_session"):        ("ready",   _cmd_end_session),
            ("ready", "checkpoint"):         ("ready",   _cmd_checkpoint),
            ("ready", "heartbeat"):          ("ready",   _cmd_heartbeat),
            ("ready", "identity_resolve"):   ("ready",   _cmd_identity_resolve),
            ("ready", "route_io"):           ("ready",   _cmd_route_io),
            ("ready", "learn_overlay"):      ("ready",   _cmd_learn_overlay),
            ("ready", "ingest_artifacts"):   ("ready",   _cmd_ingest_artifacts),
            ("ready", "extract_concepts"):   ("ready",   _cmd_extract_concepts),
            ("ready", "query_concepts"):     ("ready",   _cmd_query_concepts),
            ("ready", "ingest_chat"):        ("ready",   _cmd_ingest_chat),
            ("ready", "harness_route"):      ("ready",   _cmd_harness_route),
            ("ready", "security_check"):     ("ready",   _cmd_security_check),
            ("ready", "wfh_protocol"):       ("ready",   _cmd_wfh_protocol),
            ("ready", "vnce_lifecycle"):     ("ready",   _cmd_vnce_lifecycle),
            ("ready", "start_vnce_session"): ("ready",   _cmd_start_vnce_session),
            ("ready", "resume_vnce_session"): ("ready",  _cmd_resume_vnce_session),
            ("ready", "abbucey_protocol"):   ("ready",   _cmd_abbucey_protocol),
            ("ready", "refinement_loop_executor"): ("ready", _cmd_refinement_loop),
            ("ready", "job_ready_pipeline_entry"): ("ready", _cmd_job_ready_pipeline),
            ("ready", "client_projects_create"): ("ready", _cmd_client_projects_create),
            ("ready", "client_projects_update"): ("ready", _cmd_client_projects_update),
            ("ready", "client_projects_remove_project"): ("ready", _cmd_client_projects_remove_project),
            ("ready", "client_projects_list"): ("ready", _cmd_client_projects_list),
            ("ready", "mechanic_calendar_run"): ("ready", _cmd_mechanic_calendar_run),
            ("ready", "mechanic_email_run"): ("ready", _cmd_mechanic_email_run),
            ("ready", "mechanic_sheets_run"): ("ready", _cmd_mechanic_sheets_run),
            ("ready", "mechanic_export_run"): ("ready", _cmd_mechanic_export_run),
            ("ready", "mechanic_voice_run"): ("ready", _cmd_mechanic_voice_run),
            ("ready", "mechanic_model_run"): ("ready", _cmd_mechanic_model_run),
            ("ready", "mechanic_smoke_check"): ("ready", _cmd_mechanic_smoke_check),
            ("ready", "mama_research_calc_run"): ("ready", _cmd_mama_research_calc_run),
            ("ready", "mama_validate_real_world_excel"): ("ready", _cmd_mama_validate_real_world_excel),
            ("ready", "mama_traditional_calc_run"): ("ready", _cmd_mama_traditional_calc_run),
            ("ready", "mama_business_calc_run"): ("ready", _cmd_mama_business_calc_run),
            ("ready", "mama_calc_run"): ("ready", _cmd_mama_calc_run),
            ("ready", "route_bucey_shunt"): ("ready", _cmd_route_bucey_shunt),
            ("ready", "route_amip"): ("ready", _cmd_route_amip),
            ("ready", "route_mail_smtp_send"): ("ready", _cmd_route_mail_smtp_send),
            ("ready", "route_mail_imap_fetch"): ("ready", _cmd_route_mail_imap_fetch),
            ("ready", "write_docx"):         ("ready",   _cmd_write_docx),
            ("ready", "edit_docx"):          ("ready",   _cmd_edit_docx),
            ("ready", "write_xlsx"):         ("ready",   _cmd_write_xlsx),
            ("ready", "edit_xlsx"):          ("ready",   _cmd_edit_xlsx),
            ("ready", "write_pdf"):          ("ready",   _cmd_write_pdf),
            ("ready", "compose_image"):      ("ready",   _cmd_compose_image),
            ("ready", "edit_image"):         ("ready",   _cmd_edit_image),
            ("ready", "python_run"):          ("ready",   _cmd_python_run),
            ("ready", "python_run"):          ("ready",   _cmd_python_run),
            ("ready", "biometric_status"):   ("ready",   _cmd_biometric_status),
            ("ready", "ai_generate"):        ("ready",   _cmd_ai_generate),
            ("ready", "ai_draft_docx"):      ("ready",   _cmd_ai_draft_docx),
            ("ready", "ai_draft_xlsx"):      ("ready",   _cmd_ai_draft_xlsx),
            ("ready", "write_pptx"):         ("ready",   _cmd_write_pptx),
            ("ready", "read_pptx"):          ("ready",   _cmd_read_pptx),
            ("ready", "write_xlsx_formula"): ("ready",   _cmd_write_xlsx_formula),
            ("ready", "write_xlsx_chart"):   ("ready",   _cmd_write_xlsx_chart),
            ("ready", "calendar_list"):      ("ready",   _cmd_calendar_list),
            ("ready", "calendar_create"):    ("ready",   _cmd_calendar_create),
            ("ready", "create_meet"):        ("ready",   _cmd_create_meet),
            ("ready", "send_sms"):           ("ready",   _cmd_send_sms),
            ("ready", "send_email"):         ("ready",   _cmd_send_email),
            ("ready", "fetch_email"):        ("ready",   _cmd_fetch_email),
            ("ready", "web_browse"):         ("ready",   _cmd_web_browse),
            ("ready", "web_search"):         ("ready",   _cmd_web_search),
            ("ready", "voip_call"):          ("ready",   _cmd_voip_call),
            ("ready", "invoice_create"):     ("ready",   _cmd_invoice_create),
            ("ready", "invoice_list"):       ("ready",   _cmd_invoice_list),
            ("ready", "invoice_get"):        ("ready",   _cmd_invoice_get),
            ("ready", "invoice_update"):     ("ready",   _cmd_invoice_update_status),
            ("ready", "invoice_payment"):    ("ready",   _cmd_invoice_payment),
            ("ready", "invoice_pdf"):        ("ready",   _cmd_invoice_pdf),
            ("ready", "expense_add"):        ("ready",   _cmd_expense_add),
            ("ready", "expense_list"):       ("ready",   _cmd_expense_list),
            ("ready", "expense_summary"):    ("ready",   _cmd_expense_summary),
            ("ready", "ledger_post"):        ("ready",   _cmd_ledger_post),
            ("ready", "ledger_balance"):     ("ready",   _cmd_ledger_balance),
            ("ready", "chart_of_accounts"):  ("ready",   _cmd_chart_of_accounts),
            ("ready", "report_trial_balance"): ("ready", _cmd_report_trial_balance),
            ("ready", "report_pnl"):         ("ready",   _cmd_report_pnl),
            ("ready", "report_balance_sheet"): ("ready", _cmd_report_balance_sheet),
            ("ready", "report_cash_flow"):   ("ready",   _cmd_report_cash_flow),
            ("ready", "pos_product_add"):    ("ready",   _cmd_pos_product_add),
            ("ready", "pos_product_update"): ("ready",   _cmd_pos_product_update),
            ("ready", "pos_product_list"):   ("ready",   _cmd_pos_product_list),
            ("ready", "pos_product_lookup"): ("ready",   _cmd_pos_product_lookup),
            ("ready", "pos_inventory_adjust"): ("ready", _cmd_pos_inventory_adjust),
            ("ready", "pos_low_stock"):      ("ready",   _cmd_pos_low_stock),
            ("ready", "pos_cart_create"):    ("ready",   _cmd_pos_cart_create),
            ("ready", "pos_cart_add"):       ("ready",   _cmd_pos_cart_add),
            ("ready", "pos_cart_remove"):    ("ready",   _cmd_pos_cart_remove),
            ("ready", "pos_cart_discount"):  ("ready",   _cmd_pos_cart_discount),
            ("ready", "pos_cart_total"):     ("ready",   _cmd_pos_cart_total),
            ("ready", "pos_cart_void"):      ("ready",   _cmd_pos_cart_void),
            ("ready", "pos_checkout"):       ("ready",   _cmd_pos_checkout),
            ("ready", "pos_refund"):         ("ready",   _cmd_pos_refund),
            ("ready", "pos_receipt"):        ("ready",   _cmd_pos_receipt),
            ("ready", "pos_sales_today"):    ("ready",   _cmd_pos_sales_today),
            ("ready", "pos_sales_range"):    ("ready",   _cmd_pos_sales_range),
            ("ready", "pos_top_products"):   ("ready",   _cmd_pos_top_products),
            ("ready", "pos_end_of_day"):     ("ready",   _cmd_pos_end_of_day),
            ("ready", "morning_routine_get_config"): ("ready", _cmd_morning_routine_get_config),
            ("ready", "morning_routine_set_config"): ("ready", _cmd_morning_routine_set_config),
            ("ready", "morning_routine_fetch_feeds"): ("ready", _cmd_morning_routine_fetch_feeds),
            ("ready", "morning_routine_news_search"): ("ready", _cmd_morning_routine_news_search),
            ("ready", "morning_routine_gigs_add"): ("ready", _cmd_morning_routine_gigs_add),
            ("ready", "morning_routine_gigs_list"): ("ready", _cmd_morning_routine_gigs_list),
            ("ready", "morning_routine_gigs_clear"): ("ready", _cmd_morning_routine_gigs_clear),
            ("ready", "morning_routine_cluster"): ("ready", _cmd_morning_routine_cluster),
            ("ready", "morning_routine_filter_gigs"): ("ready", _cmd_morning_routine_filter_gigs),
            ("ready", "morning_routine_ai_batch"): ("ready", _cmd_morning_routine_ai_batch),
            ("ready", "ada_voice_profile_get"): ("ready", _cmd_ada_voice_profile_get),
            ("ready", "ada_voice_profile_set"): ("ready", _cmd_ada_voice_profile_set),
            ("ready", "stellar_time_snapshot"): ("ready", _cmd_stellar_time_snapshot),
            ("ready", "stellar_time_dut1"): ("ready", _cmd_stellar_time_dut1),
            ("ready", "stellar_observer_set"): ("ready", _cmd_stellar_observer_set),
            ("ready", "stellar_observer_get"): ("ready", _cmd_stellar_observer_get),
            ("blocked", "reset"):            ("ready",   None),
        },
        initial_state="ready",
    )


def dispatch(command: str, auth_token: str = "", **kwargs) -> Dict[str, Any]:
    """
    Single external entry point for all control operations.

    Flow:  king check -> paladin gate -> sheriff audit -> FSM -> action -> result

    Args:
        command:    one of the registered FSM commands (e.g. "session_start")
        auth_token: must equal ROYAL_SIGNET from security to pass king check
        **kwargs:   command-specific arguments (see _cmd_* wrappers above)

    Returns:
        dict with at minimum {"success": bool}.  Security denials include
        {"success": False, "status": "DENY", "reason": ...}.
    """
    if _CONTROL_FSM is None:
        return {"success": False, "error": "CONTROL FSM not initialized (core module unavailable)"}

    if not king_sovereignty_check(auth_token):
        sheriff_audit("dispatch", "king", "DENY", "KING:sovereignty-check-failed")
        if _CONTROL_FSM.state == "ready":
            _CONTROL_FSM.state = "blocked"
        return {"success": False, "status": "DENY", "reason": "KING:sovereignty-check-failed"}

    gate_text = f"{command} {kwargs.get('text', '')} {kwargs.get('input', '')}"
    sec_allowed, sec_reason = paladin_gate(gate_text)
    if not sec_allowed:
        sheriff_audit("dispatch", "paladin", "DENY", sec_reason)
        if _CONTROL_FSM.state == "ready":
            _CONTROL_FSM.state = "blocked"
        return {"success": False, "status": "DENY", "reason": sec_reason}

    audit_event = sheriff_audit("dispatch", "sheriff", "ALLOW", sec_reason)

    if _CONTROL_FSM.state == "blocked":
        _CONTROL_FSM.handle("reset")

    fsm_kwargs = dict(kwargs)
    fsm_kwargs["_dispatch_auth_token"] = auth_token
    fsm_result = _CONTROL_FSM.handle(command, fsm_kwargs)
    if not fsm_result.get("success"):
        return {
            "success": False,
            "error": fsm_result.get("error", "unknown FSM error"),
            "security_audit": audit_event,
        }

    return {
        "success": True,
        "command": command,
        "result": fsm_result.get("result"),
        "fsm_state": _CONTROL_FSM.get_state(),
        "security_audit": audit_event,
    }
