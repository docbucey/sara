"""SARA MAMA — The Gate. Human interface, biometric adaptation, and presentation."""

try:
    from .shunt_mama import mama_shunt_entrypoint
except ImportError:
    pass

try:
    from .slm_mama import mama_slm_entrypoint
except ImportError:
    pass

try:
    from .ux_adapt_mama import adapt_amip_ux_mama
except ImportError:
    pass

try:
    from .biometrics_mama import (
        _extract_biometric_context_mama, _predict_contextual_state_mama,
        RawInputEvent, HidBiometricProfile, InputBuffer,
        analyze_hid_stream, get_fatigue_color,
    )
except ImportError:
    pass

try:
    from .reasoning_mama import _extract_validated_reasoning, _build_reasoning_overlay
except ImportError:
    pass

try:
    from .osh_mama import _phase1_osh_surface_mama
except ImportError:
    pass

try:
    from .presentation_mama import summarize_bucey_shunt_mama, present_amipi_result_mama
except ImportError:
    pass

try:
    from .jargon_mama import AdaptiveJargonLexicon
except ImportError:
    pass

try:
    from .ledger_mama import MamaLedger
except ImportError:
    pass

try:
    from .plainjain_mama import PlainJainMama, run_mama_proof
except ImportError:
    pass

try:
    from .clerk_mama import dispatch_clerk_protocol
except ImportError:
    pass

try:
    from .biometric_learning_mama import (
        run_biometric_learning_cycle,
        get_biometric_status,
        store_baseline,
        store_drill_result,
        build_biometric_recommendation_shunt,
    )
except ImportError:
    pass
