"""
SARA Control — Server loop and control artifact writers.
Extracted from sara_controlgen1.py.
"""
import os
import sys
import json
from datetime import datetime, timezone

# Ensure SARA project root is importable so `sara_control.*`, `sara_sdk.*`, etc. resolve
_HERE = os.path.dirname(os.path.abspath(__file__))
_SARA_ROOT = os.path.dirname(_HERE)
if _SARA_ROOT not in sys.path:
    sys.path.insert(0, _SARA_ROOT)


def _write_control_artifacts(status: str, reached: bool, reason: str) -> None:
    """Write/update the three pillar artifact JSON files for CONTROL."""
    _here = os.path.dirname(os.path.abspath(__file__))
    _local = {
        "pillar": "sara_control",
        "file": "sara_controlgen1.py",
        "status": status,
        "reached": reached,
        "reason": reason,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _distant = {
        "pillar": "sara_control",
        "file": "sara_controlgen1.py",
        "status": status,
        "reached": reached,
        "note": reason,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _master = {
        "pillar": "sara_control",
        "final_status": status,
        "local": _local,
        "distant": _distant,
    }
    for fname, obj in [("result.meta.json", _local), ("distant_end.json", _distant), ("master_result.json", _master)]:
        try:
            with open(os.path.join(_here, fname), "w", encoding="utf-8") as f:
                json.dump(obj, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


_INTERACTIVE_COMMANDS = [
    # Session management
    "session_start",
    "heartbeat",
    "identity_resolve",
    "append_event",
    "end_session",
    "checkpoint",
    # Routing & orchestration
    "route_io",
    "route_bucey_shunt",
    "route_amip",
    # Learning & ingestion
    "learn_overlay",
    "ingest_artifacts",
    "extract_concepts",
    "query_concepts",
    "ingest_chat",
    # Security
    "harness_route",
    "security_check",
    # Workflow protocols
    "wfh_protocol",
    "vnce_lifecycle",
    "start_vnce_session",
    "resume_vnce_session",
    "abbucey_protocol",
    "refinement_loop_executor",
    "job_ready_pipeline_entry",
    # Mechanic adapters (external desktop client; not shipped with SARA)
    "mechanic_smoke_check",
    "mechanic_calendar_run",
    "mechanic_email_run",
    "mechanic_sheets_run",
    "mechanic_export_run",
    "mechanic_voice_run",
    "mechanic_model_run",
    # Office suite
    "write_docx",
    "edit_docx",
    "write_xlsx",
    "edit_xlsx",
    "write_xlsx_formula",
    "write_xlsx_chart",
    "write_pdf",
    "write_pptx",
    "read_pptx",
    "compose_image",
    "edit_image",
    # AI-assisted drafting
    "ai_generate",
    "ai_draft_docx",
    "ai_draft_xlsx",
    # Communication
    "send_email",
    "fetch_email",
    "send_sms",
    "voip_call",
    "create_meet",
    # Web
    "web_browse",
    "web_search",
    # Calendar
    "calendar_list",
    "calendar_create",
    # Accountant
    "invoice_create",
    "invoice_list",
    "invoice_get",
    "invoice_update",
    "invoice_payment",
    "invoice_pdf",
    "expense_add",
    "expense_list",
    "expense_summary",
    "ledger_post",
    "ledger_balance",
    "chart_of_accounts",
    "report_trial_balance",
    "report_pnl",
    "report_balance_sheet",
    "report_cash_flow",
    # POS Terminal
    "pos_product_add",
    "pos_product_update",
    "pos_product_list",
    "pos_product_lookup",
    "pos_inventory_adjust",
    "pos_low_stock",
    "pos_cart_create",
    "pos_cart_add",
    "pos_cart_remove",
    "pos_cart_discount",
    "pos_cart_total",
    "pos_cart_void",
    "pos_checkout",
    "pos_refund",
    "pos_receipt",
    "pos_sales_today",
    "pos_sales_range",
    "pos_top_products",
    "pos_end_of_day",
    # Morning routine (news + Fiverr batching; web UI)
    "morning_routine_get_config",
    "morning_routine_set_config",
    "morning_routine_fetch_feeds",
    "morning_routine_news_search",
    "morning_routine_gigs_add",
    "morning_routine_gigs_list",
    "morning_routine_gigs_clear",
    "morning_routine_cluster",
    "morning_routine_filter_gigs",
    "morning_routine_ai_batch",
    "ada_voice_profile_get",
    "ada_voice_profile_set",
    "stellar_time_snapshot",
    "stellar_time_dut1",
    "stellar_observer_set",
    "stellar_observer_get",
    # Calculations
    "mama_calc_run",
    "mama_traditional_calc_run",
    "mama_business_calc_run",
    "mama_research_calc_run",
    # Biometric / ADA
    "biometric_status",
    # System
    "goodbye",
]


def _print_banner() -> None:
    print()
    print("=" * 52)
    print("  SARA — Sentient Adaptive Reasoning Architecture")
    print("=" * 52)


def _print_help() -> None:
    print("\nAvailable commands:")
    for cmd in _INTERACTIVE_COMMANDS:
        print(f"  {cmd}")
    print("\nType a command name to dispatch it, or 'goodbye' to exit.\n")


def control_server() -> None:
    from sara_control.dispatch_con import dispatch

    _print_banner()

    try:
        from sara_control.shunt_con import launch_all_pillars
        print("\n[SARA] Launching pillars...")
        pillar_result = launch_all_pillars({})
        for pillar, status in pillar_result.get("launched_pillars", {}).items():
            tag = "OK" if "error" not in status else "WARN"
            print(f"  [{tag}] {pillar}: {status.get('info', status.get('error', 'ready'))}")
    except Exception as e:
        print(f"  [WARN] Pillar launch skipped: {e}")

    _write_control_artifacts("ACTIVE", True, "control_server started")
    print("\n[SARA] Control server ready.")
    _print_help()

    try:
        while True:
            try:
                raw = input("[SARA] > ").strip()
            except EOFError:
                break
            if not raw:
                continue

            parts = raw.split(None, 1)
            command = parts[0].lower()
            extra_json = parts[1] if len(parts) > 1 else ""

            if command == "goodbye":
                _write_control_artifacts("SHUTDOWN", True, "goodbye")
                print("[SARA] Shutting down. Goodbye!")
                break

            if command == "help":
                _print_help()
                continue

            if command not in _INTERACTIVE_COMMANDS:
                print(f"[SARA] Unknown command: {command}")
                _print_help()
                continue

            kwargs = {}
            if extra_json:
                try:
                    kwargs = json.loads(extra_json)
                except json.JSONDecodeError:
                    print(f'[SARA] Invalid JSON arguments — pass a JSON object after the command, e.g.:')
                    print(f'  {command} {{"key": "value"}}')
                    continue

            try:
                result = dispatch(command, auth_token="", **kwargs)
            except Exception as e:
                result = {"success": False, "error": str(e)}

            print(json.dumps(result, indent=2, default=str))

    except KeyboardInterrupt:
        _write_control_artifacts("INTERRUPTED", True, "KeyboardInterrupt")
        print("\n[SARA] Interrupted. Goodbye!")


if __name__ == "__main__":
    if "--http" in sys.argv:
        import argparse

        _hp = argparse.ArgumentParser(add_help=False)
        _hp.add_argument("--http", action="store_true")
        _hp.add_argument("--host", default="127.0.0.1")
        _hp.add_argument("--port", type=int, default=5050)
        _http_args, _ = _hp.parse_known_args()

        # Diagnostic: test dispatch import before launching server
        print("[SARA] Testing CONTROL dispatch import...")
        try:
            from sara_control.dispatch_con import dispatch as _test_dispatch
            print("[SARA] dispatch_con loaded OK")
        except Exception as _diag_e:
            print(f"[SARA] dispatch_con FAILED: {_diag_e}")
            import traceback
            traceback.print_exc()

        try:
            from sara_control.sara_control_http import run_server
        except ImportError:
            try:
                from sara_control_http import run_server
            except Exception as _e:
                print(f"[SARA] HTTP bridge not available: {_e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)
        run_server(_http_args.host, _http_args.port)
    else:
        control_server()
