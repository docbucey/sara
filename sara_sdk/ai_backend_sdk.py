"""SDK AI Backend: pluggable AI backend registry and dispatch."""
import json
import os
import urllib.request
import urllib.error
from typing import Any, Callable, Dict, Optional


class SARA_AIBackend:
    """Generic AI backend interface for SARA. Plug in any LLM or API."""

    def __init__(self):
        self.backends: Dict[str, Callable] = {}
        self.default_backend: Optional[str] = None

    def register_backend(self, name: str, handler: Callable[[str, Optional[Dict[str, Any]]], str], is_default: bool = False):
        self.backends[name] = handler
        if is_default or self.default_backend is None:
            self.default_backend = name

    def ask(self, prompt: str, context: Optional[Dict[str, Any]] = None, backend: Optional[str] = None) -> str:
        backend = backend or self.default_backend
        if backend not in self.backends:
            return f"[AI backend '{backend}' not available]"
        return self.backends[backend](prompt, context or {})

    # dispatch_con.py calls .generate() — alias to .ask()
    def generate(self, prompt: str, context: Optional[Dict[str, Any]] = None, backend: Optional[str] = None) -> str:
        return self.ask(prompt, context, backend)

    @property
    def available_backends(self) -> list:
        return list(self.backends.keys())


def dummy_backend(prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
    return f"[DUMMY AI] {prompt} (context: {context})"


def ollama_backend(prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
    """Call Ollama's local HTTP API at http://localhost:11434/api/generate."""
    ctx = context or {}
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    model = ctx.get("model") or os.getenv("SARA_OLLAMA_MODEL", "llama3.2")
    system_prompt = ctx.get("system_prompt", "You are SARA, a helpful assistant.")
    url = f"{host}/api/generate"

    body = json.dumps({
        "model": model,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
    }).encode("utf-8")

    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "").strip() or "[Ollama returned empty response]"
    except urllib.error.URLError as e:
        return f"[Ollama unavailable: {e.reason}. Is Ollama running?]"
    except Exception as e:
        return f"[Ollama error: {e}]"


# ─── Cloud + OpenAI-compatible backends (stdlib only, zero extra packages) ───

def openai_backend(prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
    """ChatGPT via OpenAI API. Requires OPENAI_API_KEY env var."""
    ctx = context or {}
    key = os.getenv("OPENAI_API_KEY", "")
    if not key:
        return "[OpenAI backend not configured: set OPENAI_API_KEY env var]"
    model  = ctx.get("model") or os.getenv("SARA_OPENAI_MODEL", "gpt-4o-mini")
    system = ctx.get("system_prompt", "You are SARA, a helpful assistant.")
    body = json.dumps({
        "model": model,
        "messages": [{"role": "system", "content": system},
                     {"role": "user",   "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[OpenAI error: {e}]"


def claude_backend(prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
    """Anthropic Claude. Requires ANTHROPIC_API_KEY env var."""
    ctx = context or {}
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        return "[Claude backend not configured: set ANTHROPIC_API_KEY env var]"
    model  = ctx.get("model") or os.getenv("SARA_CLAUDE_MODEL", "claude-3-haiku-20240307")
    system = ctx.get("system_prompt", "You are SARA, a helpful assistant.")
    body = json.dumps({
        "model": model,
        "max_tokens": 1024,
        "system": system,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read().decode("utf-8"))
            return data["content"][0]["text"].strip()
    except Exception as e:
        return f"[Claude error: {e}]"


def gemini_backend(prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
    """Google Gemini. Requires GOOGLE_API_KEY env var."""
    ctx = context or {}
    key = os.getenv("GOOGLE_API_KEY", "")
    if not key:
        return "[Gemini backend not configured: set GOOGLE_API_KEY env var]"
    model = ctx.get("model") or os.getenv("SARA_GEMINI_MODEL", "gemini-1.5-flash")
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}]
    }).encode("utf-8")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        return f"[Gemini error: {e}]"


def openai_compat_backend(prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
    """Any OpenAI-compatible server: LM Studio, LocalAI, text-generation-webui, etc.
    Set SARA_OPENAI_COMPAT_URL (e.g. http://localhost:1234/v1) and optionally
    SARA_OPENAI_COMPAT_KEY and SARA_OPENAI_COMPAT_MODEL."""
    ctx = context or {}
    base = os.getenv("SARA_OPENAI_COMPAT_URL", "").rstrip("/")
    if not base:
        return "[OpenAI-compat backend not configured: set SARA_OPENAI_COMPAT_URL env var]"
    key   = os.getenv("SARA_OPENAI_COMPAT_KEY", "local")
    model = ctx.get("model") or os.getenv("SARA_OPENAI_COMPAT_MODEL", "local-model")
    system = ctx.get("system_prompt", "You are SARA, a helpful assistant.")
    body = json.dumps({
        "model": model,
        "messages": [{"role": "system", "content": system},
                     {"role": "user",   "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[OpenAI-compat error: {e}]"


# ─── Backend registry + auto-selection ───────────────────────────────────────
#
# Priority order (first available wins):
#   1. GGUF model file in SARA/models/      → local   (runs inside SARA, zero network)
#   2. Ollama running locally               → ollama  (no API key, runs on your machine)
#   3. SARA_OPENAI_COMPAT_URL set           → openai_compat (LM Studio, LocalAI, etc.)
#   4. OPENAI_API_KEY set                   → openai  (ChatGPT — needs internet + key)
#   5. ANTHROPIC_API_KEY set                → claude  (needs internet + key)
#   6. GOOGLE_API_KEY set                   → gemini  (needs internet + key)
#   7. Nothing available                    → dummy   (always works, echoes back)
#
# Any of the above can be forced: SARA_AI_BACKEND=ollama (or local, openai, claude…)

ai_backend = SARA_AIBackend()
ai_backend.register_backend("dummy",        dummy_backend)
ai_backend.register_backend("ollama",       ollama_backend)
ai_backend.register_backend("openai",       openai_backend)
ai_backend.register_backend("claude",       claude_backend)
ai_backend.register_backend("gemini",       gemini_backend)
ai_backend.register_backend("openai_compat", openai_compat_backend)

def _auto_select_backend() -> str:
    """Return the name of the best available backend."""
    forced = os.getenv("SARA_AI_BACKEND", "").strip().lower()
    if forced:
        return forced

    # Try local GGUF first — no network, no key, runs inside SARA
    try:
        from sara_sdk.local_llm_sdk import discover_models as _disc
        if _disc():
            return "local"
    except Exception:
        try:
            from .local_llm_sdk import discover_models as _disc
            if _disc():
                return "local"
        except Exception:
            pass

    # Ollama running locally?
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2):
            return "ollama"
    except Exception:
        pass

    # OpenAI-compatible local server (LM Studio, LocalAI, etc.)
    if os.getenv("SARA_OPENAI_COMPAT_URL", ""):
        return "openai_compat"

    # Cloud APIs — only if key is present
    if os.getenv("OPENAI_API_KEY", ""):
        return "openai"
    if os.getenv("ANTHROPIC_API_KEY", ""):
        return "claude"
    if os.getenv("GOOGLE_API_KEY", ""):
        return "gemini"

    return "dummy"

# Register local backend if llama-cpp-python is available
try:
    from sara_sdk.local_llm_sdk import local_llm_backend
    ai_backend.register_backend("local", local_llm_backend)
except ImportError:
    try:
        from .local_llm_sdk import local_llm_backend
        ai_backend.register_backend("local", local_llm_backend)
    except Exception:
        pass

ai_backend.default_backend = _auto_select_backend()
