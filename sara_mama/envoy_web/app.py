from __future__ import annotations

import json
import os
import random
import secrets
import hashlib
import importlib.util
from datetime import datetime, timezone, timedelta
from functools import wraps
from typing import Any, Dict, List

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from agents import backend_health, run_agents


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
RUNS_FILE = os.path.join(DATA_DIR, "blind_runs.json")
EVENT_FILE = os.path.join(DATA_DIR, "envoy_events.ndjson")
PROFILE_FILE = os.path.join(DATA_DIR, "security_profile.json")

SECRET_KEY = os.environ.get("SARA_ENVOY_SECRET", secrets.token_hex(24))
REVEAL_WINDOW_MINUTES = int(os.environ.get("SARA_REVEAL_WINDOW_MINUTES", "20"))
LOCAL_ONLY_MODE = os.environ.get("SARA_LOCAL_ONLY", "1") == "1"

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
API_TOKENS: Dict[str, str] = {}
ENFORCE_AUTH_ALL_ENDPOINTS = os.environ.get("SARA_ENFORCE_AUTH_ALL", "0") == "1"


def _load_profile() -> Dict[str, Any]:
    if not os.path.exists(PROFILE_FILE):
        profile = {
            "remote_username": "md",
            "remote_password": "trial-pass-123",
            "local_bypass": False,
            "updated_ts": _iso_now(),
        }
        with open(PROFILE_FILE, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2)
        return profile
    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_profile(profile: Dict[str, Any]) -> None:
    profile["updated_ts"] = _iso_now()
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)


PROFILE = _load_profile()


def _effective_username() -> str:
    return os.environ.get("SARA_ENVOY_USERNAME", PROFILE.get("remote_username", "md"))


def _effective_password() -> str:
    return os.environ.get("SARA_ENVOY_PASSWORD", PROFILE.get("remote_password", "trial-pass-123"))


def _is_local_request() -> bool:
    remote = (request.remote_addr or "").strip()
    return remote in {"127.0.0.1", "::1", "localhost"}


def _try_load_security():
    try:
        sec_path = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "sara_security", "sara_securitygn1.py"))
        if not os.path.exists(sec_path):
            return None
        spec = importlib.util.spec_from_file_location("sara_securitygn1", sec_path)
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:
        return None


SECURITY_MODULE = _try_load_security()


def _security_gate(action: str, content: str = "") -> tuple[bool, str]:
    if SECURITY_MODULE is None:
        return True, "security-module-unavailable:allow"

    try:
        if hasattr(SECURITY_MODULE, "king_sovereignty_check"):
            if not SECURITY_MODULE.king_sovereignty_check("USER_AUTH_CONFIRMED"):
                if hasattr(SECURITY_MODULE, "sheriff_audit"):
                    SECURITY_MODULE.sheriff_audit("envoy.gate", "king", "DENY", "KING:sovereignty-failed")
                return False, "KING:sovereignty-failed"

        if hasattr(SECURITY_MODULE, "paladin_gate"):
            allowed, reason = SECURITY_MODULE.paladin_gate(content or action)
            decision = "ALLOW" if allowed else "DENY"
            if hasattr(SECURITY_MODULE, "sheriff_audit"):
                SECURITY_MODULE.sheriff_audit("envoy.gate", "paladin", decision, str(reason))
            return bool(allowed), str(reason)
    except Exception as e:
        return False, f"SECURITY:exception:{type(e).__name__}"

    return True, "security-default-allow"


def _load_runs() -> List[Dict[str, Any]]:
    if not os.path.exists(RUNS_FILE):
        return []
    with open(RUNS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_runs(runs: List[Dict[str, Any]]) -> None:
    with open(RUNS_FILE, "w", encoding="utf-8") as f:
        json.dump(runs, f, indent=2)


def _event(event_type: str, payload: Dict[str, Any]) -> None:
    rec = {"ts": _iso_now(), "event_type": event_type, "payload": payload}
    with open(EVENT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def _token_fingerprint(token: str) -> str:
    if not token:
        return "none"
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return digest[:12]


def _auth_context() -> Dict[str, Any]:
    header_token = request.headers.get("X-SARA-Token", "").strip()
    return {
        "remote": request.remote_addr,
        "auth_mode": "token" if header_token else "session",
        "token_fingerprint": _token_fingerprint(header_token),
        "session_auth_ts": session.get("auth_ts"),
    }


def _ts_add_minutes(ts: str, minutes: int) -> str:
    return (datetime.fromisoformat(ts) + timedelta(minutes=minutes)).isoformat()


def _ts_expired(ts: str) -> bool:
    try:
        return datetime.now(timezone.utc) > datetime.fromisoformat(ts)
    except Exception:
        return True


def _auth_required(fn):
    @wraps(fn)
    def _wrapped(*args, **kwargs):
        if LOCAL_ONLY_MODE and not _is_local_request():
            return jsonify({"success": False, "error": "local-only mode active"}), 403

        header_token = request.headers.get("X-SARA-Token", "").strip()
        token_ok = bool(header_token and header_token in API_TOKENS)
        if LOCAL_ONLY_MODE and _is_local_request():
            session["authenticated"] = True
            session.setdefault("auth_ts", _iso_now())
            session["local_mode"] = True
            return fn(*args, **kwargs)

        if (not ENFORCE_AUTH_ALL_ENDPOINTS) and PROFILE.get("local_bypass", False) and _is_local_request():
            session["authenticated"] = True
            session.setdefault("auth_ts", _iso_now())
            session["local_bypass"] = True
            return fn(*args, **kwargs)
        if not session.get("authenticated") and not token_ok:
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "error": "unauthorized"}), 401
            return redirect(url_for("login_page"))
        return fn(*args, **kwargs)

    return _wrapped


def _try_load_mama():
    # Load existing Mama module for training capture if available.
    try:
        import importlib.util

        mama_path = os.path.abspath(os.path.join(BASE_DIR, "..", "sara_mamagen1.py"))
        spec = importlib.util.spec_from_file_location("sara_mamagen1", mama_path)
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:
        return None


MAMA_MODULE = _try_load_mama()


def _capture_learning(run_record: Dict[str, Any]) -> None:
    if MAMA_MODULE is None:
        return
    try:
        mama = MAMA_MODULE.PlainJainMama()
        best = run_record["results"][0]
        mama.create_memory_packet(
            task_type="scientific_blind_test",
            attempt={
                "status": "PASS" if best["status"] == "PASS" else "FAIL",
                "reason": f"best_agent={best['agent_id']}:{best['reason']}",
            },
            preferred_profile=best.get("profile", "plainjain_native"),
        )
    except Exception:
        pass


@app.get("/")
def root() -> Any:
    if LOCAL_ONLY_MODE and _is_local_request():
        session["authenticated"] = True
        return redirect(url_for("dashboard"))
    if session.get("authenticated"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login_page"))


@app.get("/login")
def login_page() -> Any:
    if LOCAL_ONLY_MODE and _is_local_request():
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.post("/api/login")
def api_login() -> Any:
    if LOCAL_ONLY_MODE and _is_local_request():
        session["authenticated"] = True
        session["auth_ts"] = _iso_now()
        api_token = secrets.token_hex(24)
        API_TOKENS[api_token] = _iso_now()
        _event("auth.login.local_mode", _auth_context())
        return jsonify({"success": True, "api_token": api_token, "local_mode": True})

    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))
    if (not ENFORCE_AUTH_ALL_ENDPOINTS) and PROFILE.get("local_bypass", False) and _is_local_request():
        session["authenticated"] = True
        session["auth_ts"] = _iso_now()
        session["local_bypass"] = True
        api_token = secrets.token_hex(24)
        API_TOKENS[api_token] = _iso_now()
        _event("auth.login.local_bypass", _auth_context())
        return jsonify({"success": True, "api_token": api_token, "local_bypass": True})

    expected_user = _effective_username()
    expected_pass = _effective_password()
    if not username:
        username = expected_user
    if username != expected_user or password != expected_pass:
        _event("auth.login.fail", _auth_context())
        return jsonify({"success": False, "error": "invalid credentials"}), 403

    session["authenticated"] = True
    session["auth_ts"] = _iso_now()
    api_token = secrets.token_hex(24)
    API_TOKENS[api_token] = _iso_now()
    _event("auth.login.success", _auth_context())
    return jsonify({"success": True, "api_token": api_token})


@app.post("/api/logout")
@_auth_required
def api_logout() -> Any:
    header_token = request.headers.get("X-SARA-Token", "").strip()
    if header_token and header_token in API_TOKENS:
        API_TOKENS.pop(header_token, None)
    session.clear()
    return jsonify({"success": True})


@app.get("/dashboard")
@_auth_required
def dashboard() -> Any:
    return render_template("dashboard.html")


@app.get("/api/profile/remote-credentials")
@_auth_required
def api_profile_remote_get() -> Any:
    effective_local_bypass = False if ENFORCE_AUTH_ALL_ENDPOINTS else bool(PROFILE.get("local_bypass", False))
    return jsonify({
        "success": True,
        "profile": {
            "remote_username": PROFILE.get("remote_username", "md"),
            "local_bypass": effective_local_bypass,
            "local_bypass_locked": bool(ENFORCE_AUTH_ALL_ENDPOINTS),
            "updated_ts": PROFILE.get("updated_ts"),
        },
    })


@app.post("/api/profile/remote-credentials")
@_auth_required
def api_profile_remote_set() -> Any:
    if not _is_local_request():
        return jsonify({"success": False, "error": "profile update allowed only from local trusted browser"}), 403

    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))
    local_bypass = False if ENFORCE_AUTH_ALL_ENDPOINTS else bool(payload.get("local_bypass", False))

    if not username or not password:
        return jsonify({"success": False, "error": "username and password are required"}), 400

    PROFILE["remote_username"] = username
    PROFILE["remote_password"] = password
    PROFILE["local_bypass"] = local_bypass
    _save_profile(PROFILE)
    _event("profile.remote_credentials.updated", {"auth": _auth_context(), "local_bypass": local_bypass})

    return jsonify({"success": True})


@app.get("/api/health")
@_auth_required
def api_health() -> Any:
    allowed, reason = _security_gate("health-check", "backend health check")
    if not allowed:
        return jsonify({"success": False, "error": f"security denied: {reason}"}), 403

    checks = backend_health()
    overall = "ready" if all(c.get("status") == "ready" for c in checks) else "degraded"
    _event("backend.health", {"overall": overall, "auth": _auth_context()})
    return jsonify({"success": True, "overall": overall, "checks": checks})


@app.post("/api/chat/setup")
@_auth_required
def api_chat_setup() -> Any:
    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message", "")).strip()
    if not message:
        return jsonify({"success": False, "error": "message is required"}), 400

    allowed, reason = _security_gate("chat-setup", message)
    if not allowed:
        _event("chat.setup.denied", {"reason": reason, "auth": _auth_context()})
        return jsonify({"success": False, "error": f"security denied: {reason}"}), 403

    reply = (
        "SARA setup channel received your note. "
        "I logged this as a practical training setup item in Mama memory."
    )

    if MAMA_MODULE is not None:
        try:
            mama = MAMA_MODULE.PlainJainMama()
            mama.create_memory_packet(
                task_type="chat_setup",
                attempt={"status": "PASS", "reason": f"chat:{message[:140]}"},
                preferred_profile="plainjain_native",
            )
        except Exception:
            pass

    _event("chat.setup", {"chars": len(message), "auth": _auth_context()})
    return jsonify({"success": True, "reply": reply})


@app.post("/api/run")
@_auth_required
def api_run() -> Any:
    payload = request.get_json(silent=True) or {}
    prompt = str(payload.get("prompt", "")).strip()
    blind_mode = bool(payload.get("blind_mode", True))

    allowed, reason = _security_gate("run-blind-test", prompt)
    if not allowed:
        _event("run.denied", {"reason": reason, "auth": _auth_context()})
        return jsonify({"success": False, "error": f"security denied: {reason}"}), 403

    results = run_agents(prompt)
    run_id = f"run-{secrets.token_hex(4)}"

    label_order = ["Agent-A", "Agent-B", "Agent-C", "Agent-D"]
    shuffled = results[:]
    random.Random(run_id).shuffle(shuffled)

    blind_slots = []
    for idx, item in enumerate(shuffled):
        blind_slots.append(
            {
                "slot": label_order[idx],
                "agent_id": item["agent_id"],
                "agent_label": item["agent_label"],
                "profile": item["profile"],
                "score": item["score"],
                "status": item["status"],
                "reason": item["reason"],
                "output": item["output"],
            }
        )

    run_record = {
        "run_id": run_id,
        "ts": _iso_now(),
        "reveal_deadline_ts": _ts_add_minutes(_iso_now(), REVEAL_WINDOW_MINUTES),
        "reveal_uses": 0,
        "prompt": prompt,
        "blind_mode": blind_mode,
        "revealed": False,
        "results": results,
        "blind_slots": blind_slots,
        "auth_context": _auth_context(),
    }

    runs = _load_runs()
    runs.insert(0, run_record)
    _save_runs(runs[:100])
    _capture_learning(run_record)

    _event("run.created", {"run_id": run_id, "blind_mode": blind_mode, "auth": _auth_context()})

    response_slots = []
    if blind_mode:
        for slot in blind_slots:
            response_slots.append(
                {
                    "slot": slot["slot"],
                    "status": slot["status"],
                    "reason": slot["reason"],
                    "output": slot["output"],
                }
            )
    else:
        for slot in blind_slots:
            response_slots.append(
                {
                    "slot": slot["slot"],
                    "agent_label": slot["agent_label"],
                    "status": slot["status"],
                    "reason": slot["reason"],
                    "output": slot["output"],
                }
            )

    return jsonify({
        "success": True,
        "run_id": run_id,
        "slots": response_slots,
        "reveal_deadline_ts": run_record["reveal_deadline_ts"],
        "reveal_window_minutes": REVEAL_WINDOW_MINUTES,
    })


@app.get("/api/runs")
@_auth_required
def api_runs() -> Any:
    runs = _load_runs()
    slim = []
    for run in runs[:25]:
        slim.append({
            "run_id": run["run_id"],
            "ts": run["ts"],
            "blind_mode": run["blind_mode"],
            "revealed": run.get("revealed", False),
            "reveal_deadline_ts": run.get("reveal_deadline_ts"),
            "reveal_uses": run.get("reveal_uses", 0),
        })
    return jsonify({"success": True, "runs": slim})


@app.get("/api/run/<run_id>")
@_auth_required
def api_run_detail(run_id: str) -> Any:
    runs = _load_runs()
    for run in runs:
        if run["run_id"] == run_id:
            if run["blind_mode"] and not run.get("revealed", False):
                if _ts_expired(run.get("reveal_deadline_ts", "")):
                    return jsonify({"success": False, "error": "blind reveal window expired"}), 410
                masked = []
                for slot in run["blind_slots"]:
                    masked.append({
                        "slot": slot["slot"],
                        "status": slot["status"],
                        "reason": slot["reason"],
                        "output": slot["output"],
                    })
                return jsonify({"success": True, "run": {"run_id": run_id, "blind_mode": True, "slots": masked}})
            return jsonify({"success": True, "run": run})
    return jsonify({"success": False, "error": "run not found"}), 404


@app.post("/api/reveal/<run_id>")
@_auth_required
def api_reveal(run_id: str) -> Any:
    payload = request.get_json(silent=True) or {}
    password = str(payload.get("password", ""))
    if password != _effective_password():
        return jsonify({"success": False, "error": "invalid credentials"}), 403

    runs = _load_runs()
    for run in runs:
        if run["run_id"] == run_id:
            if run.get("reveal_uses", 0) >= 1:
                return jsonify({"success": False, "error": "reveal already used for this run"}), 409
            if _ts_expired(run.get("reveal_deadline_ts", "")):
                return jsonify({"success": False, "error": "blind reveal window expired"}), 410
            run["revealed"] = True
            run["reveal_uses"] = 1
            run["revealed_at"] = _iso_now()
            run["reveal_auth_context"] = _auth_context()
            _save_runs(runs)
            _event("run.revealed", {"run_id": run_id, "auth": _auth_context()})
            return jsonify({"success": True})

    return jsonify({"success": False, "error": "run not found"}), 404


@app.get("/api/compare/<run_id>")
@_auth_required
def api_compare(run_id: str) -> Any:
    runs = _load_runs()
    for run in runs:
        if run["run_id"] == run_id:
            if run["blind_mode"] and not run.get("revealed", False):
                return jsonify({"success": False, "error": "reveal required first"}), 409

            ranked = sorted(run["results"], key=lambda x: float(x["score"]), reverse=True)
            return jsonify({
                "success": True,
                "run_id": run_id,
                "winner": ranked[0],
                "ranked": ranked,
            })

    return jsonify({"success": False, "error": "run not found"}), 404


if __name__ == "__main__":
    # Local-only mode keeps SARA on this machine unless explicitly disabled.
    host = "127.0.0.1" if LOCAL_ONLY_MODE else "0.0.0.0"
    app.run(host=host, port=8787, debug=False)
