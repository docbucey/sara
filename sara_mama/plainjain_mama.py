"""PlainJainMama baseline class, model profiles, and proof runner for MAMA."""

import importlib.util
import os
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from .ledger_mama import MamaLedger
from .jargon_mama import AdaptiveJargonLexicon

try:
    from research_calc_gn1 import (  # type: ignore
        BusinessCalculator,
        ShiProofRunner,
        SymbolTranslator,
        TraditionalCalculator,
        run_research_calc_proof,
    )
    _RESEARCH_CALC_OK = True
except Exception:
    try:
        import sys as _sys, os as _os
        _sys.path.insert(0, _os.path.dirname(__file__))
        from research_calc_gn1 import (  # type: ignore  # noqa: E402
            BusinessCalculator,
            ShiProofRunner,
            SymbolTranslator,
            TraditionalCalculator,
            run_research_calc_proof,
        )
        _RESEARCH_CALC_OK = True
    except Exception:
        _RESEARCH_CALC_OK = False


def _load_plainjain_executor_mod_mama():
    executor_path = os.path.join(os.path.dirname(__file__), "ai_llc", "plainjain_executor.py")
    if not os.path.exists(executor_path):
        return None
    spec = importlib.util.spec_from_file_location("sara_plainjain_executor_runtime", executor_path)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


MODEL_PROFILES: Dict[str, Dict[str, Any]] = {
    "plainjain_native": {
        "kind": "internal",
        "source": "ai_llc/plainjainllm.slam",
        "notes": "NBS-weighted native path using resonance, stability, provenance",
    },
    "deepseeker_coder_local": {
        "kind": "bridge",
        "source": "ai_llc/deepseeker_coder_bridge.slam",
        "notes": "DeepSeek Coder first expansion profile for local lab testing",
    },
    "ollama_default": {
        "kind": "bridge",
        "source": "ai_llc/ollama_bridge.slam",
        "notes": "Traditional external model bridge for text generation (opt-in only via SARA_ALLOW_OLLAMA)",
    },
}


class PlainJainMama:
    """
    PlainJain-first Mama baseline.

    Gen1 intent:
    - Keep a stable memory contract.
    - Route to different model profiles using the same lesson/provenance structure.
    """

    def __init__(self, ledger: Optional[MamaLedger] = None):
        self.ledger = ledger or MamaLedger()
        self.jargon = AdaptiveJargonLexicon(base_dir=os.path.dirname(__file__))

    def list_model_profiles(self) -> List[str]:
        return sorted(MODEL_PROFILES.keys())

    def choose_profile(self, preferred: Optional[str] = None) -> str:
        if preferred and preferred in MODEL_PROFILES:
            return preferred
        return "plainjain_native"

    def extract_lesson(self, attempt: Dict[str, Any]) -> str:
        status = str(attempt.get("status", "unknown")).upper()
        reason = str(attempt.get("reason", "no-reason"))
        if status == "PASS":
            return f"reuse-path:{reason}"
        return f"avoid-path:{reason}"

    def create_memory_packet(self,
                             task_type: str,
                             attempt: Dict[str, Any],
                             preferred_profile: Optional[str] = None) -> Dict[str, Any]:
        profile = self.choose_profile(preferred_profile)
        lesson = self.extract_lesson(attempt)
        status = str(attempt.get("status", "unknown")).upper()
        reason = str(attempt.get("reason", "no-reason"))

        ledger_entry = self.ledger.append_attempt(
            task_type=task_type,
            status=status,
            reason=reason,
            model_profile=profile,
            lesson=lesson,
            provenance={
                "base_spec": "plainjainllm.slam",
                "profile_source": MODEL_PROFILES[profile]["source"],
            },
        )

        return {
            "mama_packet": {
                "task_type": task_type,
                "status": status,
                "reason": reason,
                "lesson": lesson,
                "selected_profile": profile,
                "profile_notes": MODEL_PROFILES[profile]["notes"],
                "ledger_ref": {
                    "ts": ledger_entry["ts"],
                    "path": self.ledger.ledger_path,
                },
            }
        }

    def teach_jargon(self, terms: Iterable[str], mode: str = "research") -> Dict[str, Any]:
        """Allow end users to teach evolving jargon terms at runtime."""
        return self.jargon.teach_terms(terms=terms, mode=mode)

    def check_text_quality(self,
                           text: str,
                           mode: str = "research",
                           user_jargon: Optional[Iterable[str]] = None,
                           auto_learn: bool = False) -> Dict[str, Any]:
        """Spell and grammar check that preserves user-taught jargon."""
        return self.jargon.check_text(
            text=text,
            mode=mode,
            user_jargon=user_jargon,
            auto_learn=auto_learn,
        )

    def run_research_calc(self,
                          formula: str,
                          samples: int = 500) -> Dict[str, Any]:
        """
        Evaluate a formula string through the research calculator.

        Accepts symbol shortcodes and Unicode math notation transparently:
            \\alpha, \\sqrt{x}, \\frac{a}{b}, \\partial f/x, \u221e, \u03b1, \u2202, \u222b, \u03a3 ...

        Returns a full run-result dict including per-block DataFrames,
        falsifiability flags, boundary/NaN counts, and derivative maps.
        If research_calc_gn1 is unavailable returns an error dict.
        """
        if not _RESEARCH_CALC_OK:
            return {
                "status": "ERROR",
                "error": "research_calc_gn1 not available \u2013 ensure sara_mama dir is on sys.path",
                "formula_original": formula,
            }
        runner = ShiProofRunner(samples=samples)
        return runner.run(formula)

    def run_traditional_calc(self,
                             expression: str,
                             variables: Optional[Dict[str, Any]] = None,
                             rows: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Run traditional scientific calculator mode.

        - If rows are provided: evaluate expression across all rows.
        - Else: evaluate single expression with optional variable substitutions.
        """
        if not _RESEARCH_CALC_OK:
            return {
                "status": "ERROR",
                "error": "research_calc_gn1 not available \u2013 ensure sara_mama dir is on sys.path",
                "expression_original": expression,
            }
        calc = TraditionalCalculator()
        if rows is not None:
            return calc.evaluate_rows(expression=expression, rows=rows)
        return calc.evaluate(expression=expression, variables=variables)

    def run_business_calc(self,
                          operation: str,
                          inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run business calculator mode.

        Supported operation values include:
        roi, gross_margin, profit_margin, break_even_units,
        compound_growth, loan_payment, npv, cagr, markup,
        discount_price, formula.
        """
        if not _RESEARCH_CALC_OK:
            return {
                "status": "ERROR",
                "error": "research_calc_gn1 not available \u2013 ensure sara_mama dir is on sys.path",
                "operation": operation,
            }
        calc = BusinessCalculator()
        return calc.calculate(operation=operation, inputs=inputs)

    def validate_real_world_formula(self,
                                    formula: str,
                                    observations: List[Dict[str, Any]],
                                    observed_col: str,
                                    abs_tolerance: float = 0.05,
                                    rel_tolerance: float = 0.05,
                                    scenario_label: str = "real_world",
                                    units_map: Optional[Dict[str, str]] = None,
                                    uncertainty_col: Optional[str] = None,
                                    uncertainty_abs_default: float = 0.0,
                                    uncertainty_rel_default: float = 0.0,
                                    strict_units: bool = False,
                                    outlier_policy: str = "none",
                                    baseline_formula: Optional[str] = None,
                                    verdict_version: str = "v1",
                                    run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate a formula against measured real-world observations.

        Each observation row should include all input variables used in the
        formula plus one measured output column (observed_col).

        Example row for SHI:
            {"memory": 12.0, "footprint": 3.0, "runtime": 2.0,
             "enumerator": 1.0, "shi_observed": 5.1}
        """
        if not _RESEARCH_CALC_OK:
            return {
                "status": "ERROR",
                "error": "research_calc_gn1 not available \u2013 ensure sara_mama dir is on sys.path",
                "formula_original": formula,
            }

        runner = ShiProofRunner(samples=16)
        return runner.validate_real_world_observations(
            formula=formula,
            observations=observations,
            observed_col=observed_col,
            abs_tolerance=abs_tolerance,
            rel_tolerance=rel_tolerance,
            scenario_label=scenario_label,
            units_map=units_map,
            uncertainty_col=uncertainty_col,
            uncertainty_abs_default=uncertainty_abs_default,
            uncertainty_rel_default=uncertainty_rel_default,
            strict_units=strict_units,
            outlier_policy=outlier_policy,
            baseline_formula=baseline_formula,
            verdict_version=verdict_version,
            run_id=run_id,
        )

    def validate_real_world_formula_from_excel(self,
                                               formula: str,
                                               excel_path: str,
                                               observed_col: str,
                                               sheet_name: Optional[str] = None,
                                               abs_tolerance: float = 0.05,
                                               rel_tolerance: float = 0.05,
                                               scenario_label: Optional[str] = None,
                                               units_map: Optional[Dict[str, str]] = None,
                                               report_output_path: Optional[str] = None,
                                               uncertainty_col: Optional[str] = None,
                                               uncertainty_abs_default: float = 0.0,
                                               uncertainty_rel_default: float = 0.0,
                                               strict_units: bool = False,
                                               outlier_policy: str = "none",
                                               baseline_formula: Optional[str] = None,
                                               verdict_version: str = "v1",
                                               run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        One-step Excel flow for real-world scientific validation.

        Reads measured rows from an Excel sheet, validates formula fit,
        and optionally exports a report (.xlsx/.csv/.json).
        """
        if not _RESEARCH_CALC_OK:
            return {
                "status": "ERROR",
                "error": "research_calc_gn1 not available \u2013 ensure sara_mama dir is on sys.path",
                "formula_original": formula,
            }

        runner = ShiProofRunner(samples=16)
        result = runner.validate_real_world_excel(
            formula=formula,
            excel_path=excel_path,
            observed_col=observed_col,
            sheet_name=sheet_name,
            abs_tolerance=abs_tolerance,
            rel_tolerance=rel_tolerance,
            scenario_label=scenario_label,
            units_map=units_map,
            uncertainty_col=uncertainty_col,
            uncertainty_abs_default=uncertainty_abs_default,
            uncertainty_rel_default=uncertainty_rel_default,
            strict_units=strict_units,
            outlier_policy=outlier_policy,
            baseline_formula=baseline_formula,
            verdict_version=verdict_version,
            run_id=run_id,
        )

        if report_output_path and result.get("status") == "PASS":
            result["report_export"] = runner.export_validation_report(
                validation_result=result,
                output_path=report_output_path,
            )

        return result

    def translate_formula_symbols(self, formula: str) -> str:
        """
        Translate symbol shortcodes/Unicode in a formula to sympy ASCII
        without running test blocks. Useful for formula preview/validation.
        """
        if not _RESEARCH_CALC_OK:
            return formula
        return SymbolTranslator().translate(formula)

    def symbol_palette(self) -> List[Any]:
        """Return symbol palette entries for UI toolbar consumers."""
        if not _RESEARCH_CALC_OK:
            return []
        return SymbolTranslator.palette()

    def symbol_shortcode_help(self) -> str:
        """Return a human-readable shortcode reference."""
        if not _RESEARCH_CALC_OK:
            return "research_calc_gn1 not loaded"
        return SymbolTranslator.shortcode_help()


def run_mama_proof() -> Dict[str, Any]:
    """Small proof path used for first startup and harness-era validation."""
    mama = PlainJainMama()
    packet = mama.create_memory_packet(
        task_type="startup_proof",
        attempt={"status": "PASS", "reason": "plainjain-baseline-initialized"},
        preferred_profile="plainjain_native",
    )
    jargon_seed = mama.teach_jargon(["jargonese", "ShuntFSM", "paladin_gate"], mode="coding")
    quality = mama.check_text_quality(
        text="This is jargonese and ShuntFSM protocol text with paladin_gate wired in.",
        mode="coding",
    )
    calc_proof: Dict[str, Any] = {"status": "SKIPPED"}
    if _RESEARCH_CALC_OK:
        try:
            calc_proof = run_research_calc_proof()
        except Exception as e:
            calc_proof = {"status": "ERROR", "error": str(e)}

    return {
        "status": "PASS",
        "reason": "MAMA:plainjain-base-ready",
        "packet": packet,
        "jargon_seed": jargon_seed,
        "quality": {
            "valid": quality.get("valid", False),
            "known_jargon_count": quality.get("known_jargon_count", 0),
            "lexicon_path": quality.get("lexicon_path"),
        },
        "research_calc": {
            "status": calc_proof.get("status"),
            "translation_score": calc_proof.get("translation_score"),
            "palette_size": calc_proof.get("palette_size"),
            "runner_status": calc_proof.get("runner", {}).get("status"),
        },
    }
