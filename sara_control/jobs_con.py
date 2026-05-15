"""
SARA Control — Job pipeline: intake, feasibility, spec sheet, refinement, checkpoints, drift, closeout.
Extracted from sara_controlgen1.py.
"""
from typing import Any, Dict, List, Optional

from sara_control.session_con import array_normalize_con


def job_intake_filter(job_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Deterministically filter WFH gig jobs for remote, deliverable-based, BOSGAME-compatible work."""
    payload = dict(job_payload or {})
    posting_text = str(payload.get("job_posting") or payload.get("posting") or payload.get("input") or "")
    lowered = posting_text.lower()

    accept_checks = {
        "fully_remote": any(token in lowered for token in ["fully remote", "remote", "work from home", "wfh"]),
        "deliverable_based": any(token in lowered for token in ["deliverable", "output", "spreadsheet", "excel file", "report", "transcript"]),
        "async_or_flexible": any(token in lowered for token in ["flexible", "asynchronous", "async", "own schedule"]),
        "bosgame_executable": not any(token in lowered for token in ["on-site", "onsite", "office", "travel required"]),
    }
    reject_hits = [
        token for token in [
            "in-person",
            "on-site",
            "onsite",
            "phone calls",
            "call center",
            "meetings required",
            "leadership",
            "manage team",
            "undefined deliverable",
        ] if token in lowered
    ]

    if reject_hits:
        decision = "REJECT"
    elif all(accept_checks.values()):
        decision = "ACCEPT"
    else:
        decision = "HUMAN-REQUIRED"

    return {
        "decision": decision,
        "accept_checks": accept_checks,
        "reject_hits": reject_hits,
        "job_source": payload.get("job_source", "unknown"),
    }


def job_feasibility_classifier(job_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Return YES / NO / HUMAN-REQUIRED from explicit home-execution and low-strain criteria only."""
    payload = dict(job_payload or {})
    posting_text = str(payload.get("job_posting") or payload.get("posting") or payload.get("input") or "")
    lowered = posting_text.lower()

    positive = {
        "home_based": any(token in lowered for token in ["remote", "work from home", "fully remote"]),
        "low_strain": any(token in lowered for token in ["data entry", "transcription", "categorization", "tagging", "spreadsheet", "research", "form filling"]),
        "deterministic_deliverable": any(token in lowered for token in ["deliverable", "updated excel file", "spreadsheet", "list", "transcript", "report"]),
        "bosgame_sara_vnce_compatible": not any(token in lowered for token in ["in-person", "travel required", "heavy phone", "meeting-heavy"]),
    }

    if all(positive.values()):
        decision = "YES"
    elif not positive["home_based"] or not positive["bosgame_sara_vnce_compatible"]:
        decision = "NO"
    else:
        decision = "HUMAN-REQUIRED"

    return {"decision": decision, "criteria": positive}


def spec_sheet_generator(job_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Extract a deterministic spec sheet from explicit job content only."""
    payload = dict(job_payload or {})
    if payload.get("spec_sheet") or payload.get("specification"):
        sheet = dict(payload.get("spec_sheet") or payload.get("specification") or {})
    else:
        posting_text = str(payload.get("job_posting") or payload.get("posting") or payload.get("input") or "")
        lowered = posting_text.lower()
        deliverable_type = "spreadsheet" if any(token in lowered for token in ["spreadsheet", "excel", "rows", "columns"]) else "structured_text"
        task_tree = []
        if "duplicate" in lowered:
            task_tree.append("remove duplicates")
        if "standardize" in lowered or "format" in lowered:
            task_tree.append("normalize formats")
        if "data entry" in lowered:
            task_tree.insert(0, "enter structured data")
        if not task_tree:
            task_tree.append("review explicit deliverable instructions")
        sheet = {
            "job_source": payload.get("job_source", "unknown"),
            "job_type": payload.get("job_type") or "low-judgment-structured-task",
            "deliverable_type": deliverable_type,
            "task_tree": task_tree,
            "required_inputs": array_normalize_con(payload.get("required_inputs") or []),
            "expected_outputs": array_normalize_con(payload.get("expected_outputs") or ["completed deliverable"]),
            "acceptance_criteria": array_normalize_con(payload.get("acceptance_criteria") or ["matches explicit posting requirements"]),
            "estimated_time_window": payload.get("estimated_time_window", "unspecified"),
            "accuracy_threshold": payload.get("accuracy_threshold", "posting_defined"),
            "human_required_flags": array_normalize_con(payload.get("human_required_flags") or []),
        }
    return {"status": "SPEC_READY", "spec_sheet": sheet}


def refinement_state_tracker(job_payload: Optional[Dict[str, Any]] = None, previous_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Persist deterministic ABBucey refinement state without freeform mutation."""
    payload = dict(job_payload or {})
    prior = dict(previous_state or {})
    corrections = array_normalize_con(payload.get("corrections") or prior.get("corrections") or [])
    operator_decisions = array_normalize_con(payload.get("operator_decisions") or prior.get("operator_decisions") or [])
    deliverable_formats = array_normalize_con(payload.get("deliverable_formats") or prior.get("deliverable_formats") or [])
    spec_sheet_drafts = array_normalize_con(payload.get("spec_sheet_drafts") or prior.get("spec_sheet_drafts") or [payload.get("spec_sheet") or payload.get("specification") or {}])
    state = {
        "job_posting": payload.get("job_posting") or prior.get("job_posting") or payload.get("posting") or payload.get("input") or "",
        "extracted_requirements": payload.get("extracted_requirements") or prior.get("extracted_requirements") or payload.get("requirements") or {},
        "operator_decisions": operator_decisions,
        "corrections": corrections,
        "spec_sheet_drafts": spec_sheet_drafts,
        "deliverable_formats": deliverable_formats,
        "workflow_state": payload.get("workflow_state") or prior.get("workflow_state") or "STATE_CREATED",
        "state_transition": "STATE_UPDATED" if previous_state else "STATE_CREATED",
    }
    if payload.get("freeze_state"):
        state["workflow_state"] = "STATE_FROZEN"
        state["state_transition"] = "STATE_FROZEN"
    return state


def human_checkpoint_router(refinement_state: Dict[str, Any], checkpoint: str) -> Dict[str, Any]:
    """Route only the defined ABBucey human checkpoints."""
    allowed_checkpoints = {
        "feasibility_confirmation",
        "spec_sheet_approval",
        "deliverable_format_approval",
        "final_closeout",
    }
    checkpoint_name = str(checkpoint or "").strip().lower()
    if checkpoint_name not in allowed_checkpoints:
        return {
            "status": "CHECKPOINT_BLOCKED",
            "reason": "undefined_checkpoint",
            "checkpoint": checkpoint_name,
        }
    approvals = array_normalize_con(refinement_state.get("operator_decisions") or [])
    approved = any(str(item).strip().lower() == checkpoint_name for item in approvals)
    return {
        "status": "CHECKPOINT_APPROVED" if approved else "CHECKPOINT_REQUIRED",
        "checkpoint": checkpoint_name,
        "workflow_state": refinement_state.get("workflow_state", "STATE_CREATED"),
    }


def drift_prevention_layer(refinement_state: Dict[str, Any]) -> Dict[str, Any]:
    """Detect repeated corrections, conflicting instructions, and circular refinement deterministically."""
    corrections = [str(item).strip().lower() for item in array_normalize_con(refinement_state.get("corrections") or []) if str(item).strip()]
    repeated = len(corrections) != len(set(corrections))
    conflicting = bool(refinement_state.get("conflicting_instructions", False))
    circular = int(refinement_state.get("rework_cycles", 0) or 0) > 1
    entropy_flag = bool(refinement_state.get("entropy_change_detected", False))
    if repeated or conflicting or circular or entropy_flag:
        updated = dict(refinement_state)
        updated["workflow_state"] = "STATE_FROZEN"
        return {
            "status": "FROZEN_FOR_CLARIFICATION" if not conflicting else "CONFLICT_DETECTED",
            "state": updated,
            "reasons": {
                "repeated_corrections": repeated,
                "conflicting_instructions": conflicting,
                "circular_refinement": circular,
                "entropy_change_detected": entropy_flag,
            },
        }
    return {"status": "STABLE", "state": refinement_state, "reasons": {}}


def deliverable_plan_generator(refinement_state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a deterministic deliverable plan from the approved spec sheet only."""
    drafts = array_normalize_con(refinement_state.get("spec_sheet_drafts") or [])
    latest_spec = drafts[-1] if drafts else {}
    if not latest_spec:
        return {"status": "HUMAN_REVIEW_REQUIRED", "reason": "missing_spec_sheet", "plan": {}}
    plan = {
        "deliverable_type": latest_spec.get("deliverable_type") if isinstance(latest_spec, dict) else None,
        "task_tree": latest_spec.get("task_tree", []) if isinstance(latest_spec, dict) else [],
        "expected_outputs": latest_spec.get("expected_outputs", []) if isinstance(latest_spec, dict) else [],
        "acceptance_criteria": latest_spec.get("acceptance_criteria", []) if isinstance(latest_spec, dict) else [],
        "pending_tasks": array_normalize_con(refinement_state.get("pending_tasks") or []),
        "human_required_tasks": array_normalize_con(refinement_state.get("human_required_tasks") or []),
        "closeout_state": refinement_state.get("closeout_state", "ready"),
    }
    return {"status": "PLAN_READY", "plan": plan}


def job_ready_pipeline_closeout(refinement_result: Dict[str, Any], deliverable_plan: Dict[str, Any]) -> Dict[str, Any]:
    """Finalize the deterministic job-ready pipeline without activating ABBucey."""
    return {
        "status": "READY_FOR_EXECUTION",
        "activation_state": "held",
        "refinement_state": refinement_result.get("refinement_state", {}),
        "deliverable_plan": deliverable_plan,
        "closeout": "pipeline_stopped_before_activation",
    }


def refinement_loop_executor(job_payload: Optional[Dict[str, Any]] = None, previous_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Execute the fixed ABBucey refinement loop deterministically without activating ABBucey."""
    state = refinement_state_tracker(job_payload=job_payload, previous_state=previous_state)
    drift = drift_prevention_layer(state)
    if drift.get("status") != "STABLE":
        return {
            "status": "WAITING_FOR_CHECKPOINT",
            "loop_step": 4,
            "refinement_state": drift.get("state", state),
            "drift": drift,
        }

    checkpoint_one = human_checkpoint_router(state, "feasibility_confirmation")
    if checkpoint_one.get("status") != "CHECKPOINT_APPROVED":
        return {
            "status": "WAITING_FOR_CHECKPOINT",
            "loop_step": 4,
            "refinement_state": state,
            "checkpoint": checkpoint_one,
        }

    frozen_state = refinement_state_tracker(job_payload={**dict(job_payload or {}), "freeze_state": True}, previous_state=state)
    deliverable_plan = deliverable_plan_generator(frozen_state)
    checkpoint_two = human_checkpoint_router(frozen_state, "deliverable_format_approval")
    if checkpoint_two.get("status") != "CHECKPOINT_APPROVED":
        return {
            "status": "WAITING_FOR_CHECKPOINT",
            "loop_step": 8,
            "refinement_state": frozen_state,
            "deliverable_plan": deliverable_plan,
            "checkpoint": checkpoint_two,
        }

    return {
        "status": "READY_FOR_CLOSEOUT",
        "loop_step": 11,
        "refinement_state": frozen_state,
        "deliverable_plan": deliverable_plan,
        "activation_state": "held",
    }


def job_ready_pipeline_entry(job_payload: Optional[Dict[str, Any]] = None, previous_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Run the fixed ABBucey job-ready pipeline deterministically and stop before activation."""
    payload = dict(job_payload or {})

    intake = job_intake_filter(payload)
    if intake.get("decision") == "REJECT":
        return {
            "status": "REJECTED",
            "pipeline_step": 2,
            "job_intake_filter": intake,
            "activation_state": "held",
        }

    feasibility = job_feasibility_classifier(payload)
    if feasibility.get("decision") == "NO":
        return {
            "status": "NOT_FEASIBLE",
            "pipeline_step": 3,
            "job_intake_filter": intake,
            "job_feasibility_classifier": feasibility,
            "activation_state": "held",
        }

    spec_result = spec_sheet_generator(payload)
    merged_payload = dict(payload)
    if spec_result.get("status") == "SPEC_READY":
        merged_payload["spec_sheet"] = spec_result.get("spec_sheet", {})
        merged_payload.setdefault("spec_sheet_drafts", [spec_result.get("spec_sheet", {})])

    refinement_result = refinement_loop_executor(merged_payload, previous_state=previous_state)
    if refinement_result.get("status") != "READY_FOR_CLOSEOUT":
        return {
            "status": refinement_result.get("status", "WAITING_FOR_CHECKPOINT"),
            "pipeline_step": 8,
            "job_intake_filter": intake,
            "job_feasibility_classifier": feasibility,
            "spec_sheet_generator": spec_result,
            "refinement_loop_executor": refinement_result,
            "activation_state": "held",
        }

    deliverable_plan = refinement_result.get("deliverable_plan") or deliverable_plan_generator(refinement_result.get("refinement_state", {}))
    closeout = job_ready_pipeline_closeout(refinement_result, deliverable_plan)
    return {
        "status": closeout.get("status", "READY_FOR_EXECUTION"),
        "pipeline_step": 10,
        "job_intake_filter": intake,
        "job_feasibility_classifier": feasibility,
        "spec_sheet_generator": spec_result,
        "refinement_loop_executor": refinement_result,
        "deliverable_plan_generator": deliverable_plan,
        "job_ready_pipeline_closeout": closeout,
        "activation_state": "held",
    }
