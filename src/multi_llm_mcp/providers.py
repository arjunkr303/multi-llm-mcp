"""
Provider configuration and client factory for multi-llm-gateway.

Each provider entry maps to an OpenAI-compatible API endpoint.
API keys are read exclusively from environment variables — never hardcoded.
"""

import os
from openai import OpenAI

__all__ = ["PROVIDERS", "get_client"]

# ──────────────────────────────────────────────
# Provider registry
# ──────────────────────────────────────────────
# To add a new provider, just add an entry here.
# key_env=None means no API key is needed (e.g. local Ollama).

PROVIDERS: dict[str, dict] = {
    "nvidia": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "key_env": "NVIDIA_API_KEY",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "key_env": "OPENROUTER_API_KEY",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "key_env": None,
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "key_env": "GROQ_API_KEY",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "key_env": "DEEPSEEK_API_KEY",
    },
}

# ──────────────────────────────────────────────
# Client cache & factory
# ──────────────────────────────────────────────
# Clients are cached so HTTP connection pools are reused across calls.

_client_cache: dict[str, OpenAI] = {}

DEFAULT_TIMEOUT = 120.0  # seconds


def get_client(provider: str) -> OpenAI:
    """Return a cached OpenAI-compatible client for the given provider.

    Raises ValueError if the provider is unknown or its API key is missing.
    """
    if provider not in PROVIDERS:
        raise ValueError(
            f"Unknown provider '{provider}'. "
            f"Available: {', '.join(PROVIDERS.keys())}"
        )

    if provider in _client_cache:
        return _client_cache[provider]

    cfg = PROVIDERS[provider]
    api_key = (
        os.environ.get(cfg["key_env"], "")
        if cfg["key_env"]
        else "not-needed"
    )

    if cfg["key_env"] and not api_key:
        raise ValueError(
            f"Missing environment variable {cfg['key_env']}. "
            f"Set it in your .env file or export it in your shell."
        )

    client = OpenAI(
        base_url=cfg["base_url"],
        api_key=api_key,
        timeout=DEFAULT_TIMEOUT,
    )
    _client_cache[provider] = client
    return client