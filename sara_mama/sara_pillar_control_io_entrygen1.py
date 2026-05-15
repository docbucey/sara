# shunt header: sara_pillar_control_io_entry_gen1
# pillar: sara_mama
# purpose: user-facing entry to run full 4-pillar harness checks via control I/O routing

from __future__ import annotations

import json
import os
import importlib.util
import sys
import types
from datetime import datetime, timezone
from itertools import permutations
from typing import Dict, List, Tuple, Any


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _repo_root() -> str:
    # this file: .../NBS/claywork/saragen0finish/sara_mama/<file>
    here = os.path.dirname(__file__)
    return os.path.abspath(os.path.join(here, "..", "..", ".."))


def _pillar_targets(root: str) -> Dict[str, str]:
    base = os.path.join(root, "claywork", "saragen0finish")
    return {
        "core": os.path.join(base, "sara_core", "sara_coregn1.py"),
        "control": os.path.join(base, "sara_control", "sara_controlgen1.py"),
        "mama": os.path.join(base, "sara_mama", "sara_mamagen1.py"),
        "security": os.path.join(base, "sara_security", "sara_securitygn1.py"),
    }


def _control_file(root: str) -> str:
    return os.path.join(root, "claywork", "saragen0finish", "sara_control", "sara_controlgen1.py")


def _read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _ensure_file(path: str, label: str) -> None:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing {label}: {path}")


def _load_control_module(root: str):
    con_path = _control_file(root)
    _ensure_file(con_path, "control route module")

    # Compatibility shim for legacy import name in sara_controlgen1.py.
    if "Sara_core" not in sys.modules:
        shim = types.ModuleType("Sara_core")
        shim.create_nbs_file = lambda *args, **kwargs: {"success": False, "error": "shim: unavailable in control-io test mode"}
        shim.NBS_BASE_DIR = os.path.join(root, "nbs_projects")
        shim.SYSTEM_CORE_PROJECT_NAME = "system_core"
        sys.modules["Sara_core"] = shim

    spec = importlib.util.spec_from_file_location("sara_controlgen1", con_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load control module: {con_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ControlIORouter:
    """
    Control I/O router for pillar checks.

    User enters through Mama. Every harness call goes through this router,
    so Core/Mama/Security are never invoked directly from user entry.
    """

    def __init__(self, repo_root: str):
        self.repo_root = repo_root
        self.targets = _pillar_targets(repo_root)
        self.control = _load_control_module(repo_root)

    def route_harness_check(self, pillar: str) -> Dict[str, Any]:
        if pillar not in self.targets:
            return {
                "pillar": pillar,
                "status": "FAIL",
                "reason": "CONTROL_IO:unknown-pillar",
            }

        result = self.control.control_route_harness_con(self.repo_root, self.targets[pillar])
        return {
            "pillar": pillar,
            "status": result.get("status", "UNKNOWN"),
            "reason": result.get("local", {}).get("reason", "no-reason"),
            "details": result,
        }


def _route_matrix() -> List[Tuple[str, ...]]:
    # "Every possible way" at pillar ordering level: all 4! route orders.
    pillars = ("mama", "control", "core", "security")
    return list(permutations(pillars, 4))


def sara_user_entry_full_pillar_test(max_routes: int = 24) -> Dict[str, Any]:
    """
    User-facing Mama entry point for full 4-pillar harness checks.

    Behavior:
    - Acts like SARA user interface through Mama.
    - Routes each pillar check through Control I/O.
    - Evaluates route-order permutations up to max_routes.
    """
    root = _repo_root()
    router = ControlIORouter(root)

    routes = _route_matrix()[: max(1, min(max_routes, 24))]
    route_runs: List[Dict[str, Any]] = []

    for idx, route in enumerate(routes, start=1):
        step_results = []
        for pillar in route:
            step_results.append(router.route_harness_check(pillar))

        route_status = "PASS" if all(s.get("status") == "PASS" for s in step_results) else "FAIL"
        route_runs.append(
            {
                "route_id": idx,
                "route": list(route),
                "status": route_status,
                "steps": step_results,
            }
        )

    overall_status = "PASS" if all(r.get("status") == "PASS" for r in route_runs) else "FAIL"

    summary = {
        "ts": _iso_now(),
        "entry_pillar": "mama",
        "routing_authority": "control_io",
        "route_count": len(route_runs),
        "overall_status": overall_status,
        "routes": route_runs,
    }

    logs_dir = os.path.join(root, "claywork", "saragen0finish", "sara_mama", "logs")
    os.makedirs(logs_dir, exist_ok=True)
    out_path = os.path.join(logs_dir, "pillar_control_io_test_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return {"status": overall_status, "report_path": out_path, "route_count": len(route_runs)}


if __name__ == "__main__":
    result = sara_user_entry_full_pillar_test(max_routes=24)
    print("=" * 60)
    print("SARA USER ENTRY: FULL 4-PILLAR CONTROL I/O TEST")
    print("=" * 60)
    print(f"status     : {result['status']}")
    print(f"routes     : {result['route_count']}")
    print(f"report     : {result['report_path']}")
    print("=" * 60)

# shunt_header: sara_pillar_control_io_entry_gen1_base
# evolution anchor: add new route policies via evolve without breaking base report schema
