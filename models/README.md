# SARA Local Models

Drop `.gguf` model files here. SARA will auto-detect and load the first one found.

## Recommended for low-end hardware (ThinkPad, 8GB RAM):

- **TinyLlama-1.1B** (~700MB) - fastest, basic capability
- **Phi-3-mini-4k** (~2.3GB Q4) - good balance of speed and quality
- **Gemma-2B** (~1.5GB Q4) - Google's small model

## Already installed via Ollama:

SARA also auto-discovers models from your Ollama cache at `~/.ollama/models/`.
No need to copy them here if Ollama already downloaded them.

## Override:

Set `SARA_MODEL_PATH=C:\path\to\model.gguf` to force a specific model.
