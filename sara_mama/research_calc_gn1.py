# shunt header: sara_mama_research_calc_gn1
# pillar: sara_mama
# generation: gen1-baseline
# purpose: Symbol translation + headless SHI proof runner for Mama research mode

"""
SARA Mama Research Calculator Gen1

Two responsibilities:
1. SymbolTranslator  — converts research/math notation (LaTeX fragments, shortcodes,
                       Unicode symbols) to sympy-compatible ASCII strings so the user
                       never needs to ask an AI to reframe notation.

2. ShiProofRunner    — headless version of shiproof.py generator logic callable as a
                       plain Python API (no Tkinter). Produces the same test-block
                       data that shiproof writes to Excel, but returns DataFrames so
                       Mama can log, persist, or forward them elsewhere.

Both are wired into PlainJainMama.run_research_calc() at the bottom of
sara_mamagen1.py.
"""

from __future__ import annotations

import itertools
import json
import os
import re
import hashlib
import uuid
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    import pandas as pd  # type: ignore
    _PANDAS_OK = True
except Exception:
    _PANDAS_OK = False

# ---------------------------------------------------------------------------
# Traditional + Business calculators
# ---------------------------------------------------------------------------


try:
    import sympy as sp  # type: ignore
    _SYMPY_OK = True
except Exception:
    _SYMPY_OK = False


# ---------------------------------------------------------------------------
# SymbolTranslator
# ---------------------------------------------------------------------------

# Ordered list of (pattern, replacement) pairs applied left-to-right.
# Patterns are plain-text shortcodes or Unicode chars; replacements are
# sympy-compatible ASCII expressions.
_SYMBOL_RULES: List[Tuple[str, str]] = [
    # --- Greek letters (backslash shortcode and Unicode) ---
    (r"\\alpha",    "alpha"),
    (r"\\beta",     "beta"),
    (r"\\gamma",    "gamma"),
    (r"\\delta",    "delta"),
    (r"\\epsilon",  "epsilon"),
    (r"\\zeta",     "zeta"),
    (r"\\eta",      "eta"),
    (r"\\theta",    "theta"),
    (r"\\iota",     "iota"),
    (r"\\kappa",    "kappa"),
    (r"\\lambda",   "lambda_"),   # lambda is a Python keyword
    (r"\\mu",       "mu"),
    (r"\\nu",       "nu"),
    (r"\\xi",       "xi"),
    (r"\\pi",       "pi"),
    (r"\\rho",      "rho"),
    (r"\\sigma",    "sigma"),
    (r"\\tau",      "tau"),
    (r"\\upsilon",  "upsilon"),
    (r"\\phi",      "phi"),
    (r"\\chi",      "chi"),
    (r"\\psi",      "psi"),
    (r"\\omega",    "omega"),
    # Unicode Greek
    (r"α", "alpha"), (r"β", "beta"), (r"γ", "gamma"), (r"δ", "delta"),
    (r"ε", "epsilon"), (r"ζ", "zeta"), (r"η", "eta"), (r"θ", "theta"),
    (r"λ", "lambda_"), (r"μ", "mu"), (r"ν", "nu"), (r"π", "pi"),
    (r"ρ", "rho"), (r"σ", "sigma"), (r"τ", "tau"), (r"φ", "phi"),
    (r"ψ", "psi"), (r"ω", "omega"),

    # --- Constants ---
    (r"\\inf",  "oo"),
    (r"\\oo",   "oo"),
    (r"\\infty","oo"),
    (r"∞",      "oo"),
    (r"\\e\b",  "E"),   # Euler's number
    (r"\\I\b",  "I"),   # imaginary unit

    # --- Arithmetic convenience ---
    (r"\^",         "**"),          # caret exponent to Python
    (r"\\frac\{([^}]+)\}\{([^}]+)\}", r"((\1)/(\2))"),  # \frac{a}{b}
    (r"\\sqrt\{([^}]+)\}",           r"sqrt(\1)"),      # \sqrt{x}
    (r"x\^2\b",    "x**2"),         # common quick-type

    # --- Calculus ---
    # \partial f/x  →  diff(f, x)
    (r"\\partial\s+(\w+)\s*/\s*(\w+)", r"diff(\1, \2)"),
    # \d f/dx       →  diff(f, x)
    (r"\\d\s+(\w+)\s*/\s*d(\w+)",      r"diff(\1, \2)"),
    # ∂ f/x

    (r"∂\s*(\w+)\s*/\s*(\w+)",         r"diff(\1, \2)"),
    # \int a,b,expr,x  →  Integral(expr, (x,a,b))
    (r"\\int\s+([\w.]+)\s*,\s*([\w.]+)\s*,\s*([^,]+)\s*,\s*(\w+)",
     r"Integral(\3, (\4, \1, \2))"),
    # \sum i,n,expr  →  Sum(expr, (i,0,n))
    (r"\\sum\s+(\w+)\s*,\s*([\w.]+)\s*,\s*(.+)",
     r"Sum(\3, (\1, 0, \2))"),
    # ∫ and Σ shortcuts
    (r"∫",  "Integral"),
    (r"Σ",  "Sum"),
    (r"∂",  "diff"),

    # --- Comparison / display-only cleanup ---
    (r"≈",   ""),   # approximate — strip for eval
    (r"≠",   ""),
    (r"≤",   "<="),
    (r"≥",   ">="),
    (r"×",   "*"),
    (r"÷",   "/"),
    (r"·",   "*"),
    (r"√",   "sqrt"),
]

# Palette metadata for UI consumers (Tkinter toolbar, web picker, etc.)
# Each entry: (display_symbol, tooltip, insert_text)
SYMBOL_PALETTE: List[Tuple[str, str, str]] = [
    # Greek
    ("α", "alpha",    "\\alpha"),
    ("β", "beta",     "\\beta"),
    ("γ", "gamma",    "\\gamma"),
    ("δ", "delta",    "\\delta"),
    ("λ", "lambda",   "\\lambda"),
    ("μ", "mu",       "\\mu"),
    ("π", "pi",       "\\pi"),
    ("σ", "sigma",    "\\sigma"),
    ("θ", "theta",    "\\theta"),
    ("ω", "omega",    "\\omega"),
    ("φ", "phi",      "\\phi"),
    # Calculus / operators
    ("∂", "partial",      "\\partial "),
    ("∫", "integral",     "\\int 0,1,expr,x"),
    ("Σ", "summation",    "\\sum i,n,expr"),
    ("√", "sqrt",         "\\sqrt{x}"),
    ("∞", "infinity",     "\\inf"),
    # Arithmetic
    ("²", "squared",      "**2"),
    ("³", "cubed",        "**3"),
    ("×", "multiply",     "*"),
    ("÷", "divide",       "/"),
    ("·", "dot multiply", "*"),
    # Fractions
    ("½", "one-half",  "(1/2)"),
    ("⅓", "one-third", "(1/3)"),
    ("¼", "one-quarter","(1/4)"),
]


class SymbolTranslator:
    """
    Converts research/math notation to sympy-safe ASCII.

    Usage:
        t = SymbolTranslator()
        clean = t.translate("shi = (∂memory/runtime + \\alpha) / \\sqrt{footprint}")
        expr  = sympy.sympify(clean)
    """

    def __init__(self, extra_rules: Optional[List[Tuple[str, str]]] = None):
        self._rules: List[Tuple[re.Pattern, str]] = []
        all_rules = list(_SYMBOL_RULES)
        if extra_rules:
            all_rules.extend(extra_rules)
        for pattern, replacement in all_rules:
            try:
                self._rules.append((re.compile(pattern), replacement))
            except re.error:
                # Plain literal — escape it
                self._rules.append((re.compile(re.escape(pattern)), replacement))

    def translate(self, text: str) -> str:
        """Apply all translation rules in order, return sympy-ready string."""
        result = str(text or "")
        for compiled, replacement in self._rules:
            result = compiled.sub(replacement, result)
        return result.strip()

    def translate_formula(self, formula: str) -> Tuple[str, str, str]:
        """
        Split 'lhs = rhs', translate rhs, return (lhs, translated_rhs, original).
        Falls back to ('Result', translated_whole, original) if no '='.
        """
        original = formula
        translated = self.translate(formula)
        if "=" in translated:
            lhs, rhs = translated.split("=", 1)
            return lhs.strip(), rhs.strip(), original
        return "Result", translated.strip(), original

    @staticmethod
    def palette() -> List[Tuple[str, str, str]]:
        """Return symbol palette entries for UI toolbars: (symbol, tooltip, insert_text)."""
        return list(SYMBOL_PALETTE)

    @staticmethod
    def shortcode_help() -> str:
        """Return a human-readable shortcode reference string."""
        lines = [
            "Symbol Shortcodes (type these in formula box):",
            "  \\alpha \\beta \\gamma \\delta \\lambda \\mu \\pi \\sigma \\theta \\omega \\phi",
            "  \\inf  or  \\oo      → infinity (sympy oo)",
            "  \\sqrt{x}           → sqrt(x)",
            "  \\frac{a}{b}        → (a)/(b)",
            "  x^{2}  or  x**2    → x**2",
            "  \\partial f/x       → diff(f, x)",
            "  \\int 0,1,expr,x    → Integral(expr, (x,0,1))",
            "  \\sum i,n,expr      → Sum(expr, (i,0,n))",
            "  Unicode: α β γ δ λ μ π σ θ ω φ ∞ ∂ ∫ Σ √ × ÷ ≤ ≥",
        ]
        return "\n".join(lines)


class TraditionalCalculator:
    """Traditional scientific calculator with symbol translation support."""

    def __init__(self):
        if not _SYMPY_OK:
            raise ImportError("sympy is required for TraditionalCalculator")
        self.translator = SymbolTranslator()

    def evaluate(self, expression: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            translated = self.translator.translate(expression)
            expr = sp.sympify(translated)
            subs = {str(k): float(v) for k, v in dict(variables or {}).items()}
            value = float(expr.subs(subs).evalf()) if subs else float(expr.evalf())
            return {
                "status": "PASS",
                "mode": "traditional",
                "expression_original": expression,
                "expression_translated": translated,
                "variables": subs,
                "value": value,
                "is_boundary": bool(np.isnan(value) or np.isinf(value)),
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "mode": "traditional",
                "expression_original": expression,
                "error": f"traditional_eval_error:{e}",
            }

    def evaluate_rows(self, expression: str, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        out_rows: List[Dict[str, Any]] = []
        boundary_count = 0
        for idx, row in enumerate(rows or []):
            res = self.evaluate(expression=expression, variables=row)
            if bool(res.get("is_boundary", False)):
                boundary_count += 1
            out_rows.append(
                {
                    "row_index": idx,
                    "inputs": dict(row or {}),
                    "status": res.get("status"),
                    "value": res.get("value"),
                    "is_boundary": res.get("is_boundary", False),
                    "error": res.get("error"),
                }
            )

        return {
            "status": "PASS",
            "mode": "traditional",
            "expression_original": expression,
            "row_count": len(out_rows),
            "boundary_count": boundary_count,
            "rows": out_rows,
        }


class BusinessCalculator:
    """Business-mode calculator for practical finance and operations metrics."""

    def __init__(self):
        self.traditional = TraditionalCalculator() if _SYMPY_OK else None

    @staticmethod
    def _f(x: Any, default: float = 0.0) -> float:
        try:
            return float(x)
        except Exception:
            return default

    def calculate(self, operation: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        op = str(operation or "").strip().lower()
        data = dict(inputs or {})
        try:
            if op == "roi":
                gain = self._f(data.get("gain"))
                cost = self._f(data.get("cost"))
                if cost == 0:
                    return {"status": "PASS", "mode": "business", "operation": op, "value": None, "is_boundary": True}
                value = (gain - cost) / cost
                return {"status": "PASS", "mode": "business", "operation": op, "value": value, "percent": value * 100.0}

            if op == "gross_margin":
                revenue = self._f(data.get("revenue"))
                cogs = self._f(data.get("cogs"))
                if revenue == 0:
                    return {"status": "PASS", "mode": "business", "operation": op, "value": None, "is_boundary": True}
                value = (revenue - cogs) / revenue
                return {"status": "PASS", "mode": "business", "operation": op, "value": value, "percent": value * 100.0}

            if op == "profit_margin":
                net_income = self._f(data.get("net_income"))
                revenue = self._f(data.get("revenue"))
                if revenue == 0:
                    return {"status": "PASS", "mode": "business", "operation": op, "value": None, "is_boundary": True}
                value = net_income / revenue
                return {"status": "PASS", "mode": "business", "operation": op, "value": value, "percent": value * 100.0}

            if op == "break_even_units":
                fixed = self._f(data.get("fixed_cost"))
                price = self._f(data.get("price_per_unit"))
                variable = self._f(data.get("variable_cost_per_unit"))
                denom = price - variable
                if denom == 0:
                    return {"status": "PASS", "mode": "business", "operation": op, "value": None, "is_boundary": True}
                return {"status": "PASS", "mode": "business", "operation": op, "value": fixed / denom}

            if op == "compound_growth":
                principal = self._f(data.get("principal"))
                rate = self._f(data.get("rate"))
                periods = self._f(data.get("periods"))
                return {"status": "PASS", "mode": "business", "operation": op, "value": principal * ((1.0 + rate) ** periods)}
        combos = list(itertools.product([0, 1], repeat=len(vars_list)))[: self.samples]
        data = []
        for combo in combos:
            row: Dict[str, Any] = {str(v): val for v, val in zip(vars_list, combo)}
            row[result_col] = self._eval_row(expr, row, result_col)
            data.append(row)
        return pd.DataFrame(data)

    def _linear(self, vars_list, expr, result_col) -> "pd.DataFrame":
        data = []
        for i in range(self.samples):
            row = {str(v): (i + 1) * (1.0 + idx * 0.2) for idx, v in enumerate(vars_list)}
            row[result_col] = self._eval_row(expr, row, result_col)
            data.append(row)
        return pd.DataFrame(data)

    def _log(self, vars_list, expr, result_col) -> "pd.DataFrame":
        data = []
        for i in range(1, self.samples + 1):
            row = {str(v): float(np.log(i * (idx + 1))) for idx, v in enumerate(vars_list)}
            row[result_col] = self._eval_row(expr, row, result_col)
            data.append(row)
        return pd.DataFrame(data)

    def _exp_growth(self, vars_list, expr, result_col) -> "pd.DataFrame":
        data = []
        half = len(vars_list) // 2
        for i in range(self.samples):
            row = {}
            for idx, v in enumerate(vars_list):
                row[str(v)] = float(np.exp(0.02 * i)) if idx < half else float(np.exp(0.01 * i))
            row[result_col] = self._eval_row(expr, row, result_col)
            data.append(row)
        return pd.DataFrame(data)

    def _radioactive(self, vars_list, expr, result_col) -> "pd.DataFrame":
        data = []
        half = len(vars_list) // 2
        for i in range(self.samples):
            row = {}
            for idx, v in enumerate(vars_list):
                noise = float(self._rng.uniform(0.8, 1.2))
                row[str(v)] = float(np.exp(0.02 * i)) * noise if idx < half else float(np.exp(0.015 * i))
            row[result_col] = self._eval_row(expr, row, result_col)
            data.append(row)
        return pd.DataFrame(data)

    @staticmethod
    def _hash_payload(payload: Any) -> str:
        try:
            raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
            return hashlib.sha256(raw).hexdigest()
        except Exception:
            return ""

    @staticmethod
    def _unit_family(unit: str) -> str:
        u = str(unit or "").strip().lower()
        if u in {"b", "kb", "mb", "gb", "tb", "bytes"}:
            return "storage"
        if u in {"ns", "us", "ms", "s", "sec", "seconds", "min", "h", "hr"}:
            return "time"
        if u in {"count", "items", "n", ""}:
            return "count"
        if u in {"ratio", "%", "percent", "unitless"}:
            return "ratio"
        if u in {"usd", "eur", "gbp", "jpy", "cad", "aud"}:
            return "currency"
        return "other"

    def _validate_units(self, vars_list: List[str], observed_col: str, units_map: Dict[str, str], strict_units: bool) -> Dict[str, Any]:
        issues: List[str] = []
        normalized = dict(units_map or {})

        for v in vars_list:
            if v not in normalized:
                issues.append(f"missing_unit:{v}")
        if observed_col not in normalized:
            issues.append(f"missing_unit:{observed_col}")

        families = {k: self._unit_family(v) for k, v in normalized.items()}
        unknown = [k for k, fam in families.items() if fam == "other"]
        for k in unknown:
            issues.append(f"unknown_unit_family:{k}:{normalized.get(k)}")

        ok = (len([i for i in issues if i.startswith("missing_unit") or i.startswith("unknown_unit_family")]) == 0)
        if strict_units and not ok:
            return {"ok": False, "issues": issues, "families": families}
        return {"ok": True, "issues": issues, "families": families}

    @staticmethod
    def _apply_outlier_policy(rows: List[Dict[str, Any]], policy: str = "none") -> List[Dict[str, Any]]:
        p = str(policy or "none").strip().lower()
        if p == "none":
            return rows

        vals = [float(r.get("abs_error", 0.0)) for r in rows if r.get("status") == "evaluated" and r.get("abs_error") is not None]
        if len(vals) < 4:
            return rows
        q1 = float(np.percentile(vals, 25))
        q3 = float(np.percentile(vals, 75))
        iqr = q3 - q1
        low = q1 - 1.5 * iqr
        high = q3 + 1.5 * iqr

        if p == "trim":
            out = []
            for r in rows:
                if r.get("status") != "evaluated":
                    out.append(r)
                    continue
                ae = float(r.get("abs_error", 0.0))
                if low <= ae <= high:
                    out.append(r)
            return out

        if p == "winsorize":
            out = []
            for r in rows:
                nr = dict(r)
                if nr.get("status") == "evaluated" and nr.get("abs_error") is not None:
                    ae = float(nr.get("abs_error", 0.0))
                    nr["abs_error"] = min(max(ae, low), high)
                    expected = abs(float(nr.get("expected", 0.0)))
                    denom = expected if expected > 1e-12 else 1.0
                    nr["rel_error"] = float(nr["abs_error"]) / denom
                out.append(nr)
            return out

        return rows

    # ---- derivatives -------------------------------------------------------

    def _derivatives(self, expr, vars_list: List[str]) -> Dict[str, Tuple[Any, Any]]:
        result = {}
        for v in vars_list:
            sym = sp.Symbol(v)
            d1 = sp.diff(expr, sym)
            d2 = sp.diff(d1, sym)
            result[v] = (d1, d2)
        return result

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        try:
            if value is None:
                return None
            out = float(value)
            if np.isnan(out):
                return None
            return out
        except Exception:
            return None

    def _evaluate_expected(self, expr, row: Dict[str, Any]) -> Tuple[Optional[float], Optional[str]]:
        try:
            val = float(expr.subs(row).evalf())
            if np.isnan(val):
                return None, "boundary_nan"
            return val, None
        except ZeroDivisionError:
            return None, "division_by_zero"
        except Exception as e:
            return None, f"eval_error:{e}"

    # ---- public API --------------------------------------------------------

    def run(self, formula: str) -> Dict[str, Any]:
        """
        Run all five test blocks for the given formula.

        Returns:
            {
              "status": "PASS" | "ERROR",
              "formula_original": str,
              "formula_translated": str,
              "result_col": str,
              "vars": [str, ...],
              "blocks": {
                "Binary_PreFlight":     {"df": DataFrame, "falsifiable": bool, "boundary_count": int},
                "Linear_Scaling":       {...},
                "Logarithmic_Scaling":  {...},
                "Exponential_Growth":   {...},
                "Radioactive_Growth":   {...},
              },
              "derivatives": {var: {"d1": str, "d2": str}, ...},
              "error": str | None,
            }
        """
        try:
            lhs, rhs, original = self.translator.translate_formula(formula)
            expr = sp.sympify(rhs)
        except Exception as e:
            return {"status": "ERROR", "formula_original": formula,
                    "formula_translated": "", "error": str(e),
                    "blocks": {}, "derivatives": {}}

        vars_list = sorted(str(s) for s in expr.free_symbols)
        deriv_map = self._derivatives(expr, vars_list)
        translated = f"{lhs} = {rhs}"

        generators = [
            ("Binary_PreFlight",    self._binary),
            ("Linear_Scaling",      self._linear),
            ("Logarithmic_Scaling", self._log),
            ("Exponential_Growth",  self._exp_growth),
            ("Radioactive_Growth",  self._radioactive),
        ]

        blocks: Dict[str, Any] = {}
        for name, gen in generators:
            df = gen(vars_list, expr, lhs)
            df["Formula_Source"] = formula
            for v, (d1, d2) in deriv_map.items():
                df[f"d1_{v}"] = str(d1)
                df[f"d2_{v}"] = str(d2)

            valid = df[lhs].dropna()
            boundary_count = int(df[lhs].isna().sum())
            falsifiable = bool(valid.nunique() > 1)

            blocks[name] = {
                "df": df,
                "falsifiable": falsifiable,
                "boundary_count": boundary_count,
                "row_count": len(df),
            }

        return {
            "status": "PASS",
            "formula_original": formula,
            "formula_translated": translated,
            "result_col": lhs,
            "vars": vars_list,
            "blocks": blocks,
            "derivatives": {v: {"d1": str(d1), "d2": str(d2)} for v, (d1, d2) in deriv_map.items()},
            "error": None,
        }

    def validate_real_world_observations(
        self,
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
        run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Validate a formula against real-world measured data.

        Inputs:
            formula:
                Example: "shi = (memory + footprint) / (runtime + enumerator)"
            observations:
                List of row dicts with input variables + observed output.
            observed_col:
                Name of measured output column in each row.
            abs_tolerance / rel_tolerance:
                Row passes if absolute OR relative error is within tolerance.
            scenario_label:
                Free-form name, e.g. "stuberfield_wave_barrier".
            units_map:
                Optional mapping like {"runtime":"s", "memory":"MB", "shi":"ratio"}

        Returns:
            Detailed per-row report + aggregate confirmation metrics.
        """
        if not observations:
            return {
                "status": "ERROR",
                "error": "No observations provided",
                "scenario": scenario_label,
            }

        try:
            lhs, rhs, original = self.translator.translate_formula(formula)
            expr = sp.sympify(rhs)
        except Exception as e:
            return {
                "status": "ERROR",
                "error": f"formula_parse_error:{e}",
                "scenario": scenario_label,
                "formula_original": formula,
            }

        vars_list = sorted(str(s) for s in expr.free_symbols)

        unit_check = self._validate_units(vars_list, observed_col, dict(units_map or {}), strict_units)
        if strict_units and not unit_check.get("ok", False):
            return {
                "status": "ERROR",
                "error": "units_validation_failed",
                "unit_validation": unit_check,
                "scenario": scenario_label,
            }

        baseline_expr = None
        baseline_translated = None
        if baseline_formula:
            try:
                _bl_lhs, _bl_rhs, _bl_orig = self.translator.translate_formula(baseline_formula)
                baseline_expr = sp.sympify(_bl_rhs)
                baseline_translated = f"{_bl_lhs} = {_bl_rhs}"
            except Exception:
                baseline_expr = None

        per_row: List[Dict[str, Any]] = []
        confirmed_count = 0
        baseline_confirmed_count = 0
        boundary_count = 0
        missing_input_count = 0

        for idx, raw_row in enumerate(observations):
            row = dict(raw_row or {})
            row_inputs: Dict[str, Any] = {}
            missing_vars: List[str] = []

            for var in vars_list:
                val = self._safe_float(row.get(var))
                if val is None:
                    missing_vars.append(var)
                else:
                    row_inputs[var] = val

            measured = self._safe_float(row.get(observed_col))
            if missing_vars:
                missing_input_count += 1
                per_row.append({
                    "row_index": idx,
                    "status": "missing_inputs",
                    "missing_vars": missing_vars,
                    "measured": measured,
                    "confirmed": False,
                })
                continue

            expected, eval_error = self._evaluate_expected(expr, row_inputs)
            if expected is None:
                boundary_count += 1
                per_row.append({
                    "row_index": idx,
                    "status": "boundary_or_error",
                    "error": eval_error,
                    "inputs": row_inputs,
                    "measured": measured,
                    "confirmed": False,
                })
                continue

            if measured is None:
                per_row.append({
                    "row_index": idx,
                    "status": "missing_measured",
                    "inputs": row_inputs,
                    "expected": expected,
                    "confirmed": False,
                })
                continue

            abs_error = abs(measured - expected)
            denom = abs(expected) if abs(expected) > 1e-12 else 1.0
            rel_error = abs_error / denom
            u_abs = self._safe_float(row.get(uncertainty_col)) if uncertainty_col else None
            uncertainty_abs = float(u_abs if u_abs is not None else uncertainty_abs_default)
            uncertainty_rel = float(uncertainty_rel_default)

            effective_abs_tolerance = float(abs_tolerance) + max(0.0, uncertainty_abs)
            effective_rel_tolerance = float(rel_tolerance) + max(0.0, uncertainty_rel)

            confirmed = bool(abs_error <= effective_abs_tolerance or rel_error <= effective_rel_tolerance)
            if confirmed:
                confirmed_count += 1

            baseline_expected = None
            baseline_abs_error = None
            baseline_rel_error = None
            baseline_confirmed = None
            if baseline_expr is not None:
                baseline_expected, _ = self._evaluate_expected(baseline_expr, row_inputs)
                if baseline_expected is not None:
                    baseline_abs_error = abs(measured - baseline_expected)
                    b_denom = abs(baseline_expected) if abs(baseline_expected) > 1e-12 else 1.0
                    baseline_rel_error = baseline_abs_error / b_denom
                    baseline_confirmed = bool(
                        baseline_abs_error <= effective_abs_tolerance or baseline_rel_error <= effective_rel_tolerance
                    )
                    if baseline_confirmed:
                        baseline_confirmed_count += 1

            per_row.append({
                "row_index": idx,
                "status": "evaluated",
                "inputs": row_inputs,
                "measured": measured,
                "expected": expected,
                "abs_error": abs_error,
                "rel_error": rel_error,
                "uncertainty_abs": uncertainty_abs,
                "effective_abs_tolerance": effective_abs_tolerance,
                "effective_rel_tolerance": effective_rel_tolerance,
                "confirmed": confirmed,
                "baseline_expected": baseline_expected,
                "baseline_abs_error": baseline_abs_error,
                "baseline_rel_error": baseline_rel_error,
                "baseline_confirmed": baseline_confirmed,
            })

        per_row = self._apply_outlier_policy(per_row, outlier_policy)
        evaluated_rows = [r for r in per_row if r.get("status") == "evaluated"]
        total_rows = len(per_row)
        evaluated_count = len(evaluated_rows)
        confirmation_ratio = (confirmed_count / evaluated_count) if evaluated_count else 0.0
        baseline_confirmation_ratio = (baseline_confirmed_count / evaluated_count) if (evaluated_count and baseline_expr is not None) else None

        if evaluated_count == 0:
            verdict = "INSUFFICIENT_DATA"
        elif confirmation_ratio >= 0.80:
            verdict = "CONFIRMED_STRONG"
        elif confirmation_ratio >= 0.50:
            verdict = "PARTIAL_SUPPORT"
        else:
            verdict = "NOT_CONFIRMED"

        report = {
            "status": "PASS",
            "scenario": scenario_label,
            "formula_original": original,
            "formula_translated": f"{lhs} = {rhs}",
            "baseline_formula": baseline_formula,
            "baseline_translated": baseline_translated,
            "observed_col": observed_col,
            "variables": vars_list,
            "tolerance": {
                "abs": abs_tolerance,
                "rel": rel_tolerance,
            },
            "uncertainty": {
                "uncertainty_col": uncertainty_col,
                "default_abs": uncertainty_abs_default,
                "default_rel": uncertainty_rel_default,
            },
            "units": units_map or {},
            "unit_validation": unit_check,
            "policy": {
                "outlier_policy": outlier_policy,
                "strict_units": strict_units,
                "verdict_version": verdict_version,
            },
            "provenance": {
                "run_id": run_id or str(uuid.uuid4()),
                "formula_hash": self._hash_payload({"formula": original, "translated": f"{lhs}={rhs}"}),
                "dataset_hash": self._hash_payload(observations),
                "samples": len(observations),
                "seed": self.random_seed,
            },
            "summary": {
                "total_rows": total_rows,
                "evaluated_rows": evaluated_count,
                "confirmed_rows": confirmed_count,
                "confirmation_ratio": confirmation_ratio,
                "baseline_confirmed_rows": baseline_confirmed_count if baseline_expr is not None else None,
                "baseline_confirmation_ratio": baseline_confirmation_ratio,
                "boundary_rows": boundary_count,
                "missing_input_rows": missing_input_count,
                "verdict": verdict,
            },
            "counterexamples": [
                r for r in per_row
                if r.get("status") == "evaluated" and not bool(r.get("confirmed", False))
            ],
            "rows": per_row,
        }

        if _PANDAS_OK:
            try:
                report["rows_df"] = pd.DataFrame(per_row)
            except Exception:
                pass

        return report

    def validate_real_world_dataframe(
        self,
        formula: str,
        df: "pd.DataFrame",
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
        run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """DataFrame convenience wrapper around validate_real_world_observations()."""
        return self.validate_real_world_observations(
            formula=formula,
            observations=df.to_dict(orient="records"),
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

    def validate_real_world_excel(
        self,
        formula: str,
        excel_path: str,
        observed_col: str,
        sheet_name: Optional[str] = None,
        abs_tolerance: float = 0.05,
        rel_tolerance: float = 0.05,
        scenario_label: Optional[str] = None,
        units_map: Optional[Dict[str, str]] = None,
        uncertainty_col: Optional[str] = None,
        uncertainty_abs_default: float = 0.0,
        uncertainty_rel_default: float = 0.0,
        strict_units: bool = False,
        outlier_policy: str = "none",
        baseline_formula: Optional[str] = None,
        verdict_version: str = "v1",
        run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Load observations from Excel and run real-world formula validation."""
        if not _PANDAS_OK:
            return {"status": "ERROR", "error": "pandas is required for Excel validation"}
        if not os.path.exists(excel_path):
            return {"status": "ERROR", "error": f"excel_not_found:{excel_path}"}

        try:
            target_sheet = sheet_name if sheet_name is not None else 0
            df = pd.read_excel(excel_path, sheet_name=target_sheet)
        except Exception as e:
            return {"status": "ERROR", "error": f"excel_read_error:{e}", "excel_path": excel_path}

        if observed_col not in df.columns:
            return {
                "status": "ERROR",
                "error": f"observed_col_missing:{observed_col}",
                "excel_path": excel_path,
                "available_columns": [str(c) for c in df.columns],
            }

        scenario = scenario_label or f"excel:{os.path.basename(excel_path)}"
        result = self.validate_real_world_dataframe(
            formula=formula,
            df=df,
            observed_col=observed_col,
            abs_tolerance=abs_tolerance,
            rel_tolerance=rel_tolerance,
            scenario_label=scenario,
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
        result["source"] = {
            "excel_path": excel_path,
            "sheet_name": sheet_name if sheet_name is not None else 0,
            "row_count": int(len(df)),
        }
        return result

    def export_validation_report(
        self,
        validation_result: Dict[str, Any],
        output_path: str,
    ) -> Dict[str, Any]:
        """
        Export validation report to xlsx, csv, or json.

        - .xlsx: writes summary + rows sheets
        - .csv: writes row-level report
        - .json: writes full report payload
        """
        ext = os.path.splitext(output_path)[1].lower()
        try:
            if ext == ".json":
                serializable = dict(validation_result)
                if "rows_df" in serializable:
                    serializable["rows_df"] = None
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(serializable, f, indent=2, default=str)
            elif ext == ".csv":
                if _PANDAS_OK and "rows_df" in validation_result:
                    validation_result["rows_df"].to_csv(output_path, index=False)
                else:
                    pd.DataFrame(validation_result.get("rows", [])).to_csv(output_path, index=False)
            elif ext == ".xlsx":
                if not _PANDAS_OK:
                    return {"status": "ERROR", "error": "pandas required for xlsx export"}
                rows_df = validation_result.get("rows_df")
                if rows_df is None:
                    rows_df = pd.DataFrame(validation_result.get("rows", []))
                summary = validation_result.get("summary", {})
                meta = {
                    "scenario": validation_result.get("scenario"),
                    "formula_original": validation_result.get("formula_original"),
                    "formula_translated": validation_result.get("formula_translated"),
                    "observed_col": validation_result.get("observed_col"),
                    "status": validation_result.get("status"),
                    "verdict": summary.get("verdict"),
                    "confirmation_ratio": summary.get("confirmation_ratio"),
                }
                with pd.ExcelWriter(output_path) as writer:
                    pd.DataFrame([meta]).to_excel(writer, sheet_name="summary", index=False)
                    pd.DataFrame([summary]).to_excel(writer, sheet_name="metrics", index=False)
                    rows_df.to_excel(writer, sheet_name="rows", index=False)
            else:
                return {
                    "status": "ERROR",
                    "error": "unsupported_export_extension",
                    "supported": [".json", ".csv", ".xlsx"],
                }
        except Exception as e:
            return {"status": "ERROR", "error": f"report_export_error:{e}", "output_path": output_path}

        return {"status": "PASS", "output_path": output_path}

    def summary(self, run_result: Dict[str, Any]) -> str:
        """Return a compact human-readable summary of a run() result."""
        if run_result.get("status") != "PASS":
            return f"ERROR: {run_result.get('error', 'unknown')}"

        lines = [
            f"Formula   : {run_result['formula_original']}",
            f"Translated: {run_result['formula_translated']}",
            f"Variables : {', '.join(run_result['vars'])}",
            "",
        ]
        for name, block in run_result["blocks"].items():
            fals = "YES" if block["falsifiable"] else "NO"
            nan_note = f"  ← boundary points (∞/0-div)" if block["boundary_count"] else ""
            lines.append(
                f"  {name:<26} Falsifiable={fals}  Boundary NaN={block['boundary_count']}{nan_note}"
            )
        lines.append("")
        lines.append("Derivatives:")
        for v, d in run_result["derivatives"].items():
            lines.append(f"  d/d{v}: velocity={d['d1']}  waveform={d['d2']}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Module self-proof
# ---------------------------------------------------------------------------

def run_research_calc_proof() -> Dict[str, Any]:
    """Quick self-proof: translate SHI formula and run binary + linear blocks."""
    translator = SymbolTranslator()

    # Test translation of common symbols
    test_cases = [
        ("\\alpha + \\beta",       "alpha + beta"),
        ("∞",                      "oo"),
        ("\\sqrt{memory}",         "sqrt(memory)"),
        ("\\frac{a}{b}",           "(a)/(b)"),
        ("x^{2}",                  "x**2"),
        ("α × β",                  "alpha * beta"),
        ("∂f/x",                   "diff(f, x)"),
    ]

    translation_pass = 0
    translation_notes = []
    for raw, expected in test_cases:
        got = translator.translate(raw)
        ok = (got.strip() == expected.strip())
        if ok:
            translation_pass += 1
        translation_notes.append({"raw": raw, "expected": expected, "got": got, "ok": ok})

    # Test ShiProofRunner on SHI formula (only binary block to keep proof fast)
    shi_formula = "shi = (memory + footprint) / (runtime + enumerator)"
    runner_result: Dict[str, Any] = {"status": "SKIPPED"}
    real_world_result: Dict[str, Any] = {"status": "SKIPPED"}
    if _PANDAS_OK and _SYMPY_OK:
        runner = ShiProofRunner(samples=16)
        full = runner.run(shi_formula)
        runner_result = {
            "status": full["status"],
            "vars": full.get("vars", []),
            "blocks_ran": list(full.get("blocks", {}).keys()),
            "binary_falsifiable": full.get("blocks", {}).get("Binary_PreFlight", {}).get("falsifiable"),
            "error": full.get("error"),
        }

        # Real-world style observation check (small synthetic sample for proof)
        observed_rows = [
            {"memory": 10.0, "footprint": 5.0, "runtime": 2.0, "enumerator": 1.0, "shi_observed": 5.0},
            {"memory": 20.0, "footprint": 4.0, "runtime": 3.0, "enumerator": 1.0, "shi_observed": 6.1},
            {"memory": 5.0, "footprint": 2.0, "runtime": 0.0, "enumerator": 0.0, "shi_observed": None},
        ]
        rw = runner.validate_real_world_observations(
            formula=shi_formula,
            observations=observed_rows,
            observed_col="shi_observed",
            abs_tolerance=0.15,
            rel_tolerance=0.05,
            scenario_label="proof_real_world",
            units_map={"memory": "MB", "footprint": "MB", "runtime": "s", "enumerator": "count", "shi_observed": "ratio"},
        )
        real_world_result = {
            "status": rw.get("status"),
            "verdict": rw.get("summary", {}).get("verdict"),
            "confirmation_ratio": rw.get("summary", {}).get("confirmation_ratio"),
            "boundary_rows": rw.get("summary", {}).get("boundary_rows"),
        }

    overall = "PASS" if (translation_pass == len(test_cases) and runner_result.get("status") in ("PASS", "SKIPPED")) else "FAIL"
    return {
        "status": overall,
        "translation_score": f"{translation_pass}/{len(test_cases)}",
        "translation_notes": translation_notes,
        "runner": runner_result,
        "real_world": real_world_result,
        "palette_size": len(SYMBOL_PALETTE),
    }


if __name__ == "__main__":
    result = run_research_calc_proof()
    print("=" * 60)
    print("SARA Mama Research Calculator — Gen1 Proof")
    print("=" * 60)
    print(f"  Status          : {result['status']}")
    print(f"  Translation     : {result['translation_score']}")
    print(f"  Palette symbols : {result['palette_size']}")
    if result["runner"].get("status") == "PASS":
        print(f"  SHI Runner vars : {result['runner']['vars']}")
        print(f"  Blocks ran      : {result['runner']['blocks_ran']}")
        print(f"  Binary falsif.  : {result['runner']['binary_falsifiable']}")
    print("=" * 60)
    print(SymbolTranslator.shortcode_help())
