from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple
from urllib import error, request


DEFAULT_AGENT_POOL: List[Dict[str, Any]] = [
    {
        "id": "ollama_statistical",
        "label": "Ollama Statistical",
        "profile": "ollama_default",
        "backend": "ollama",
        "allow_ollama_backup": True,
        "endpoint": "http://127.0.0.1:11434/api/generate",
        "model": "llama3",
        "variables": {"temperature": 0.3, "top_p": 0.9, "max_tokens": 300},
    },
    {
        "id": "gpt4all_local",
        "label": "DeepSeek Coder via Ollama (Temp GPT4All Slot)",
        "profile": "deepseeker_coder_local",
        "backend": "ollama",
        "allow_ollama_backup": True,
        "endpoint": "http://127.0.0.1:11434/api/generate",
        "model": "deepseek-coder:6.7b",
        "variables": {"temperature": 0.2, "top_p": 0.95, "max_tokens": 300},
    },
    {
        "id": "ollama_heuristic",
        "label": "Ollama Heuristic",
        "profile": "ollama_default",
        "backend": "ollama",
        "allow_ollama_backup": False,
        "endpoint": "http://127.0.0.1:11434/api/generate",
        "model": "mistral",
        "variables": {"temperature": 0.12, "top_p": 0.82, "max_tokens": 280},
    },
    {
        "id": "scientific_baseline",
        "label": "Scientific Baseline",
        "profile": "plainjain_native",
        "backend": "heuristic",
        "endpoint": "local",
        "model": "deterministic-baseline",
        "variables": {"temperature": 0.0, "top_p": 1.0, "max_tokens": 180},
    },
]


def _ollama_enabled() -> bool:
    raw = str(os.getenv("SARA_ALLOW_OLLAMA", "")).strip().lower()
    return raw in {"1", "true", "yes", "on", "enabled"}


def _ollama_policy_mode() -> str:
    raw = str(os.getenv("SARA_OLLAMA_POLICY", "")).strip().lower()
    if raw in {"full", "allow", "on", "enabled"}:
        return "full"
    if raw in {"backup", "fallback", "limited"}:
        return "backup"
    if _ollama_enabled():
        return "full"
    return "off"


def _ollama_allowed_for_agent(agent: Dict[str, Any]) -> bool:
    mode = _ollama_policy_mode()
    if mode == "full":
        return True
    if mode == "backup":
        return bool(agent.get("allow_ollama_backup", False))
    return False


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _score(seed: str, agent_id: str) -> float:
    key = f"{agent_id}|{seed}".encode("utf-8")
    h = hashlib.sha256(key).hexdigest()
    n = int(h[:8], 16)
    return round((n % 10000) / 100.0, 2)


def _profiles_path() -> str:
    return os.path.join(os.path.dirname(__file__), "data", "agent_profiles.json")


def _load_agent_pool() -> List[Dict[str, Any]]:
    path = _profiles_path()
    if not os.path.exists(path):
        return DEFAULT_AGENT_POOL
    try:
        with open(path, "r", encoding="utf-8") as f:
            parsed = json.load(f)
        pool = parsed.get("agents", [])
        if isinstance(pool, list) and pool:
            return pool
    except Exception:
        pass
    return DEFAULT_AGENT_POOL


def _post_json(url: str, payload: Dict[str, Any], timeout: int = 6) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
    with request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_json(url: str, timeout: int = 4) -> Dict[str, Any]:
    req = request.Request(url, method="GET")
    with request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
        if not body.strip():
            return {}
        return json.loads(body)


def _call_ollama(agent: Dict[str, Any], prompt: str) -> Tuple[str, str, str]:
    endpoint = str(agent.get("endpoint", ""))
    vars_cfg = agent.get("variables", {})
    payload = {
        "model": agent.get("model", "llama3"),
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": float(vars_cfg.get("temperature", 0.3)),
            "top_p": float(vars_cfg.get("top_p", 0.9)),
            "num_predict": int(vars_cfg.get("max_tokens", 300)),
        },
    }
    data = _post_json(endpoint, payload)
    return str(data.get("response", "")).strip(), "live", ""


def _call_openai_compat(agent: Dict[str, Any], prompt: str) -> Tuple[str, str, str]:
    endpoint = str(agent.get("endpoint", ""))
    vars_cfg = agent.get("variables", {})
    payload = {
        "model": agent.get("model", "gpt4all"),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": float(vars_cfg.get("temperature", 0.2)),
        "top_p": float(vars_cfg.get("top_p", 0.95)),
        "max_tokens": int(vars_cfg.get("max_tokens", 300)),
    }
    data = _post_json(endpoint, payload)
    choices = data.get("choices", [])
    if not choices:
        return "", "live", "empty choices"
    content = choices[0].get("message", {}).get("content", "")
    return str(content).strip(), "live", ""


def _call_llamacpp(agent: Dict[str, Any], prompt: str) -> Tuple[str, str, str]:
    endpoint = str(agent.get("endpoint", ""))
    vars_cfg = agent.get("variables", {})
    payload = {
        "prompt": prompt,
        "temperature": float(vars_cfg.get("temperature", 0.15)),
        "top_p": float(vars_cfg.get("top_p", 0.9)),
        "n_predict": int(vars_cfg.get("max_tokens", 300)),
    }
    data = _post_json(endpoint, payload)
    content = data.get("content", "")
    return str(content).strip(), "live", ""


def _call_heuristic(agent: Dict[str, Any], prompt: str) -> Tuple[str, str, str]:
    reduced = " ".join(prompt.split())[:220]
    out = f"Heuristic baseline summary: observed proof input='{reduced}'"
    return out, "local", ""


def _agent_output(agent: Dict[str, Any], prompt: str) -> Tuple[str, str, str]:
    backend = str(agent.get("backend", "heuristic"))
    try:
        if backend == "ollama":
            if not _ollama_allowed_for_agent(agent):
                return _call_heuristic(agent, prompt)
            return _call_ollama(agent, prompt)
        if backend == "openai_compat":
            return _call_openai_compat(agent, prompt)
        if backend == "llamacpp":
            return _call_llamacpp(agent, prompt)
        return _call_heuristic(agent, prompt)
    except (error.URLError, TimeoutError, ValueError, KeyError, json.JSONDecodeError) as e:
        fallback = f"Fallback output: backend={backend} unavailable; {type(e).__name__}"
        return fallback, "fallback", str(e)
    except Exception as e:
        fallback = f"Fallback output: backend={backend} failed; {type(e).__name__}"
        return fallback, "fallback", str(e)


def run_agents(prompt: str) -> List[Dict[str, object]]:
    prompt = (prompt or "").strip()
    if not prompt:
        prompt = "empty-proof-prompt"

    agent_pool = _load_agent_pool()
    results: List[Dict[str, object]] = []
    for agent in agent_pool:
        output, source_mode, error_text = _agent_output(agent, prompt)
        score_seed = f"{prompt}|{output}|{source_mode}"
        score = _score(score_seed, str(agent.get("id", "unknown")))
        pass_fail = "PASS" if score >= 50.0 else "FAIL"
        reason = f"score={score}; source={source_mode}"
        if error_text:
            reason = reason + f"; note={error_text[:120]}"
        results.append(
            {
                "agent_id": str(agent.get("id", "unknown")),
                "agent_label": str(agent.get("label", "unknown")),
                "profile": str(agent.get("profile", "plainjain_native")),
                "backend": str(agent.get("backend", "heuristic")),
                "source_mode": source_mode,
                "score": score,
                "status": pass_fail,
                "reason": reason,
                "output": output,
                "ts": _iso_now(),
            }
        )

    results.sort(key=lambda item: float(item["score"]), reverse=True)
    return results


def backend_health() -> List[Dict[str, Any]]:
    """Returns connector health for each configured agent backend."""
    statuses: List[Dict[str, Any]] = []
    pool = _load_agent_pool()
    for agent in pool:
        backend = str(agent.get("backend", "heuristic"))
        endpoint = str(agent.get("endpoint", ""))
        rec: Dict[str, Any] = {
            "agent_id": str(agent.get("id", "unknown")),
            "label": str(agent.get("label", "unknown")),
            "backend": backend,
            "endpoint": endpoint,
            "status": "unknown",
            "note": "",
        }

        try:
            if backend == "heuristic":
                rec["status"] = "ready"
                rec["note"] = "local deterministic baseline"
            elif backend == "ollama":
                if not _ollama_allowed_for_agent(agent):
                    rec["status"] = "disabled"
                    rec["note"] = "blocked by SARA_OLLAMA_POLICY"
                    statuses.append(rec)
                    continue
                tags = _get_json("http://127.0.0.1:11434/api/tags")
                model = str(agent.get("model", ""))
                names = [m.get("name", "") for m in tags.get("models", []) if isinstance(m, dict)]
                rec["status"] = "ready" if any(model in n for n in names) else "degraded"
                rec["note"] = "model found" if rec["status"] == "ready" else "ollama up, model not found"
            elif backend == "openai_compat":
                _post_json(endpoint, {
                    "model": agent.get("model", "gpt4all"),
                    "messages": [{"role": "user", "content": "health"}],
                    "max_tokens": 1,
                    "temperature": 0,
                }, timeout=5)
                rec["status"] = "ready"
                rec["note"] = "responded to probe"
            elif backend == "llamacpp":
                _post_json(endpoint, {
                    "prompt": "health",
                    "n_predict": 1,
                    "temperature": 0,
                }, timeout=5)
                rec["status"] = "ready"
                rec["note"] = "responded to probe"
            else:
                rec["status"] = "degraded"
                rec["note"] = "unknown backend type"
        except Exception as e:
            rec["status"] = "down"
            rec["note"] = f"{type(e).__name__}: {str(e)[:120]}"

        statuses.append(rec)

    return statuses
