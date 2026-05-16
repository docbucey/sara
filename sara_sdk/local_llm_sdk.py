"""
SARA SDK — Local LLM Engine
Loads GGUF models directly via llama-cpp-python. No Ollama needed.

Model discovery order:
  1. Explicit path in SARA_MODEL_PATH env var
  2. Any .gguf file in SARA_ROOT/models/
  3. Ollama cache at ~/.ollama/models/ (parses manifests, finds weight blobs)

Install: pip install llama-cpp-python
On CPU-only machines this works out of the box. For GPU add:
  CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python
"""

import json
import os
import glob as _glob
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _ollama_cache_dir() -> Path:
    return Path.home() / ".ollama" / "models"


def _find_ollama_model_blobs() -> List[Tuple[str, Path]]:
    """Parse Ollama manifests to find model weight blob paths."""
    cache = _ollama_cache_dir()
    manifests_root = cache / "manifests" / "registry.ollama.ai" / "library"
    if not manifests_root.exists():
        return []

    results = []
    for manifest_file in manifests_root.rglob("*"):
        if not manifest_file.is_file():
            continue
        try:
            data = json.loads(manifest_file.read_text(encoding="utf-8"))
            layers = data.get("layers", [])
            for layer in layers:
                if layer.get("mediaType") == "application/vnd.ollama.image.model":
                    digest = layer["digest"]
                    blob_name = digest.replace(":", "-")
                    blob_path = cache / "blobs" / blob_name
                    if blob_path.exists():
                        model_name = "/".join(manifest_file.relative_to(manifests_root).parts)
                        results.append((model_name, blob_path))
        except Exception:
            continue
    return results


def _find_gguf_files() -> List[Path]:
    """Find .gguf files in SARA_ROOT/models/ or relative to this module."""
    candidates = []

    # Relative to this file (works from thumb drive / any drive letter)
    _this_dir = Path(__file__).resolve().parent
    candidates.append(_this_dir.parent / "models")

    explicit = os.environ.get("SARA_ROOT", "")
    if explicit:
        candidates.append(Path(explicit) / "models")

    # Legacy fallback
    candidates.append(
        Path.home() / "Documents" / "coding projects" / "SARA" / "models"
    )

    found = []
    seen = set()
    for d in candidates:
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.gguf")):
            rp = p.resolve()
            if rp not in seen:
                seen.add(rp)
                found.append(rp)
    return found


def discover_models() -> List[Dict[str, str]]:
    """Return all discoverable local models with name and path."""
    found = []

    explicit = os.environ.get("SARA_MODEL_PATH", "")
    if explicit and os.path.isfile(explicit):
        found.append({"name": "explicit", "path": explicit, "source": "env"})

    for p in _find_gguf_files():
        found.append({"name": p.stem, "path": str(p), "source": "models_dir"})

    for name, blob in _find_ollama_model_blobs():
        found.append({"name": name, "path": str(blob), "source": "ollama_cache"})

    return found


_LOADED_MODEL = None
_LOADED_PATH = None


def _get_or_load_model(model_path: Optional[str] = None):
    """Load a GGUF model (cached singleton). Returns llama_cpp.Llama instance."""
    global _LOADED_MODEL, _LOADED_PATH

    if model_path is None:
        models = discover_models()
        if not models:
            raise RuntimeError(
                "No local models found. Place a .gguf file in SARA/models/ "
                "or set SARA_MODEL_PATH env var."
            )
        model_path = models[0]["path"]

    if _LOADED_MODEL is not None and _LOADED_PATH == model_path:
        return _LOADED_MODEL

    from llama_cpp import Llama

    n_ctx = int(os.environ.get("SARA_CTX_SIZE", "2048"))
    n_threads = int(os.environ.get("SARA_THREADS", "0")) or None

    _LOADED_MODEL = Llama(
        model_path=model_path,
        n_ctx=n_ctx,
        n_threads=n_threads,
        verbose=False,
    )
    _LOADED_PATH = model_path
    return _LOADED_MODEL


def local_llm_generate(
    prompt: str,
    system_prompt: str = "You are SARA, a helpful assistant.",
    max_tokens: int = 512,
    temperature: float = 0.7,
    model_path: Optional[str] = None,
) -> str:
    """Generate text from a local GGUF model. No network calls."""
    try:
        model = _get_or_load_model(model_path)
    except ImportError:
        return "[llama-cpp-python not installed. Run: pip install llama-cpp-python]"
    except RuntimeError as e:
        return f"[{e}]"
    except Exception as e:
        return f"[Model load error: {e}]"

    try:
        result = model.create_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        choices = result.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "").strip()
        return "[Model returned empty response]"
    except Exception as e:
        return f"[Generation error: {e}]"


def local_llm_backend(prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
    """AI backend function matching SARA_AIBackend.register_backend signature."""
    ctx = context or {}
    return local_llm_generate(
        prompt=prompt,
        system_prompt=ctx.get("system_prompt", "You are SARA, a helpful assistant."),
        max_tokens=int(ctx.get("max_tokens", 512)),
        temperature=float(ctx.get("temperature", 0.7)),
        model_path=ctx.get("model_path"),
    )
