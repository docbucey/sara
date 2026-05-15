"""UX adaptation, native runtime knob resolution, and runtime policy for MAMA."""

from typing import Any, Dict, Optional

from .reasoning_mama import _build_reasoning_overlay
from .osh_mama import _phase1_osh_surface_mama
from .biometrics_mama import _extract_biometric_context_mama, _predict_contextual_state_mama
from .plainjain_mama import _load_plainjain_executor_mod_mama


def adapt_amip_ux_mama(
    amip_payload: Optional[Dict[str, Any]] = None,
    result: Optional[Dict[str, Any]] = None,
    input_buffer=None,
) -> Dict[str, Any]:
    """Return a deterministic low-strain UX profile for interactive vs night_shift requests."""
    request = dict(amip_payload or {})
    budget = dict(request.get("resource_budget") or {})
    mode = str(request.get("mode") or "interactive").strip().lower()
    if mode not in {"interactive", "night_shift"}:
        mode = "interactive"
    strain = str(budget.get("strain") or "medium").strip().lower()
    if strain not in {"low", "medium", "high"}:
        strain = "medium"

    if mode == "night_shift":
        ux_profile = {
            "voice_first": True,
            "low_click": True,
            "full_feedback": False,
            "animations": False,
            "cognitive_load": "reduced",
            "status_style": "quiet_summary",
        }
    else:
        ux_profile = {
            "voice_first": True,
            "low_click": True,
            "full_feedback": True,
            "animations": False,
            "cognitive_load": "guided",
            "status_style": "interactive_summary",
        }

    reasoning_overlay = _build_reasoning_overlay(request=request, result=result, mode=mode, strain=strain)

    result_block = dict(result or {})
    control_generation_policy = result_block.get("generation_policy") if isinstance(result_block.get("generation_policy"), dict) else {}
    payload_block = request.get("payload") if isinstance(request.get("payload"), dict) else {}
    payload_generation_controls = payload_block.get("generation_controls") if isinstance(payload_block.get("generation_controls"), dict) else {}
    selected_profile = str(
        control_generation_policy.get("selected_profile")
        or payload_block.get("generation_profile")
        or "stable_probabilistic"
    )
    effective_controls = control_generation_policy.get("effective_controls") if isinstance(control_generation_policy.get("effective_controls"), dict) else payload_generation_controls
    if not isinstance(effective_controls, dict):
        effective_controls = {}

    generation_surface = {
        "requested_profile": str(control_generation_policy.get("requested_profile") or payload_block.get("generation_profile") or ""),
        "selected_profile": selected_profile,
        "probabilistic_enabled": bool(control_generation_policy.get("probabilistic_enabled", selected_profile != "strict_deterministic")),
        "repeatability_required": bool(payload_block.get("requires_repeatability", False)),
        "replay_mode": bool(payload_block.get("replay_mode", False) or payload_block.get("requires_repeatability", False)),
        "replay_key": str(payload_block.get("replay_key") or ""),
        "replay_seed": payload_block.get("replay_seed"),
        "effective_controls": effective_controls,
        "fallback_chain": list(control_generation_policy.get("fallback_chain") or []),
        "policy_reasons": list(control_generation_policy.get("reasons") or []),
    }

    phase1_surface = _phase1_osh_surface_mama(result)
    biometric_context = _extract_biometric_context_mama(
        amip_payload=amip_payload, result=result, input_buffer=input_buffer,
    )
    contextual_prediction = _predict_contextual_state_mama(
        context_bundle=biometric_context,
        mode=mode,
        strain=strain,
    )

    voice_io: Dict[str, Any] = {}
    try:
        from .ada_voice_mama import apply_voice_io_to_ux, get_effective_ada_voice_io

        voice_io = get_effective_ada_voice_io()
        ux_profile = apply_voice_io_to_ux(ux_profile, voice_io)
    except Exception:
        pass

    return {
        "status": "READY",
        "mode": mode,
        "strain": strain,
        "routing_intent": str(request.get("routing_intent") or ""),
        "correlation_id": str(request.get("correlation_id") or ""),
        "ux_profile": ux_profile,
        "ada_voice_io": voice_io,
        "generation_surface": generation_surface,
        "phase1_surface": phase1_surface,
        "biometric_context": biometric_context,
        "contextual_prediction": contextual_prediction,
        "reasoning_overlay": reasoning_overlay,
        "reasoning_visible": bool(reasoning_overlay.get("visible")),
        "result_status": str((result or {}).get("status") or (result or {}).get("success") or "pending"),
    }


def _resolve_native_runtime_knobs_mama(summary: Dict[str, Any]) -> Dict[str, Any]:
    generation_surface = summary.get("generation_surface") if isinstance(summary.get("generation_surface"), dict) else {}
    selected = str(generation_surface.get("selected_profile") or "stable_probabilistic")
    controls = generation_surface.get("effective_controls") if isinstance(generation_surface.get("effective_controls"), dict) else {}
    mode = str(summary.get("mode") or "interactive")
    strain = str(summary.get("strain") or "medium")

    presets: Dict[str, Dict[str, Any]] = {
        "strict_deterministic": {
            "sampling_width": 1,
            "propagation_depth": 1,
            "stability_threshold": 0.96,
            "temperature": 0.0,
            "top_p": 1.0,
            "seed": 7,
            "executor_mode": "strict",
        },
        "stable_probabilistic": {
            "sampling_width": 2,
            "propagation_depth": 2,
            "stability_threshold": 0.9,
            "temperature": 0.22,
            "top_p": 0.9,
            "seed": None,
            "executor_mode": "stable",
        },
        "creative_probabilistic": {
            "sampling_width": 3,
            "propagation_depth": 3,
            "stability_threshold": 0.84,
            "temperature": 0.68,
            "top_p": 0.95,
            "seed": None,
            "executor_mode": "creative",
        },
    }
    knobs = dict(presets.get(selected, presets["stable_probabilistic"]))
    for key in ("temperature", "top_p", "seed"):
        if key in controls:
            knobs[key] = controls[key]

    if mode == "night_shift":
        knobs["sampling_width"] = min(int(knobs.get("sampling_width", 2)), 2)
        knobs["propagation_depth"] = min(int(knobs.get("propagation_depth", 2)), 2)
    if strain in {"high", "critical", "constrained"}:
        knobs["sampling_width"] = 1
        knobs["propagation_depth"] = min(int(knobs.get("propagation_depth", 2)), 2)

    knobs["selected_profile"] = selected
    knobs["probabilistic_enabled"] = bool(generation_surface.get("probabilistic_enabled", selected != "strict_deterministic"))
    knobs["replay_mode"] = bool(generation_surface.get("replay_mode", False))
    knobs["replay_key"] = str(generation_surface.get("replay_key") or "")
    knobs["replay_ledger_enabled"] = True
    knobs["correlation_id"] = str(summary.get("correlation_id") or "")
    if generation_surface.get("replay_seed") is not None:
        knobs["seed"] = generation_surface.get("replay_seed")
    return knobs


def _apply_native_runtime_policy_mama(
    summary: Dict[str, Any],
    ai_result: Optional[Dict[str, Any]],
    amip_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    effective_result = dict(ai_result or {})
    runtime_knobs = _resolve_native_runtime_knobs_mama(summary)
    request_payload = (amip_payload or {}).get("payload") if isinstance((amip_payload or {}).get("payload"), dict) else {}
    machine_profile = (amip_payload or {}).get("machine_profile") if isinstance((amip_payload or {}).get("machine_profile"), dict) else {}

    if str(effective_result.get("selected_model") or "").strip().lower() in {"", "plainjain_native", "plainjain"}:
        model_output = effective_result.get("model_output") if isinstance(effective_result.get("model_output"), dict) else {}
        model_output.update({
            "runtime_policy_applied": True,
            "executor_mode": runtime_knobs.get("executor_mode"),
            "sampling_width": runtime_knobs.get("sampling_width"),
            "propagation_depth": runtime_knobs.get("propagation_depth"),
            "stability_threshold": runtime_knobs.get("stability_threshold"),
            "notes": str(model_output.get("notes") or "PlainJain native runtime controls applied by MAMA generation policy."),
        })

        executor_mod = _load_plainjain_executor_mod_mama()
        if executor_mod is not None and hasattr(executor_mod, "execute_plainjain"):
            try:
                native_exec = executor_mod.execute_plainjain(
                    payload=request_payload,
                    runtime_knobs=runtime_knobs,
                    machine_profile=machine_profile,
                )
                if isinstance(native_exec, dict):
                    model_output["generated_text"] = str(native_exec.get("generated_text") or model_output.get("generated_text") or "")
                    effective_result["native_execution"] = native_exec
            except Exception as e:
                effective_result["native_execution"] = {
                    "success": False,
                    "engine": "plainjain_executor",
                    "error": str(e),
                }

        effective_result["model_output"] = model_output
        effective_result["selected_model"] = "plainjain_native"

    effective_result["native_runtime"] = runtime_knobs
    return {"result": effective_result, "runtime_knobs": runtime_knobs}
