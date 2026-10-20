#!/usr/bin/env python3
"""
ask_llm.py — standalone CLI for delegating tasks to external LLMs.

Zero-dependency (stdlib only): talks to OpenAI-compatible chat endpoints of
NVIDIA NIM, OpenRouter, Groq, DeepSeek, and a local Ollama.

API keys are read from environment variables, or from a .env file in the
current directory / repo root. Keys are never hardcoded or logged.

Usage:
    python ask_llm.py --prompt "Review this code for bugs: <code>"
    python ask_llm.py --provider groq --model llama-3.1-8b-instant \
        --system-prompt "You are a senior staff engineer." \
        --prompt "Why is this function O(n^2)? <code>"
    cat big_code.py | python ask_llm.py --provider deepseek --prompt-file -

Exit codes:
    0 = success
    1 = runtime configuration error (missing API key)
    2 = CLI usage error (argparse), network error, or other API failure
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

# ──────────────────────────────────────────────
# Provider registry
# Each entry is an OpenAI-compatible chat endpoint.
# key_env=None means no API key is needed (local Ollama).
# ──────────────────────────────────────────────

PROVIDERS = {
    "nvidia":     {"base_url": "https://integrate.api.nvidia.com/v1", "key_env": "NVIDIA_API_KEY"},
    "openrouter": {"base_url": "https://openrouter.ai/api/v1",        "key_env": "OPENROUTER_API_KEY"},
    "ollama":     {"base_url": "http://localhost:11434/v1",           "key_env": None},
    "groq":       {"base_url": "https://api.groq.com/openai/v1",      "key_env": "GROQ_API_KEY"},
    "deepseek":   {"base_url": "https://api.deepseek.com",            "key_env": "DEEPSEEK_API_KEY"},
}

DEFAULT_SYSTEM_PROMPT = "You are a helpful coding assistant."
DEFAULT_TIMEOUT = 120.0  # seconds


# ──────────────────────────────────────────────
# Minimal .env loader (avoids python-dotenv dep)
# ──────────────────────────────────────────────

def load_dotenv() -> None:
    """Populate os.environ from a .env file if one exists nearby."""
    candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parent.parent / ".env",   # skill root
        Path(__file__).resolve().parent.parent.parent / ".env",  # repo root
    ]
    for env_path in candidates:
        if not env_path.is_file():
            continue
        try:
            for raw_line in env_path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key, value = key.strip(), value.strip().strip("'\"")
                # Real environment wins over .env file values.
                os.environ.setdefault(key, value)
        except OSError:
            continue
        break  # use the first .env found


# ──────────────────────────────────────────────
# API call
# ──────────────────────────────────────────────

def call_llm(provider: str, model: str, system_prompt: str, prompt: str,
             temperature: float, max_tokens: int, timeout: float) -> str:
    """Send one chat-completions request and return the model's text reply."""
    cfg = PROVIDERS[provider]
    api_key = ""
    if cfg["key_env"]:
        api_key = os.environ.get(cfg["key_env"], "")
        if not api_key:
            raise RuntimeError(
                f"Missing API key: set {cfg['key_env']} in your environment "
                f"or in a .env file."
            )

    url = cfg["base_url"].rstrip("/") + "/chat/completions"
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }).encode("utf-8")

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    # OpenRouter etiquette: attribute the calling app.
    if provider == "openrouter":
        headers["HTTP-Referer"] = "https://github.com/arjunkr303/multi-llm-mcp"
        headers["X-Title"] = "multi-llm-mcp"

    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            pass
        raise RuntimeError(f"HTTP {exc.code} from {provider}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Could not reach {provider} ({url}). "
            f"If this is ollama, make sure it is running: `ollama serve`"
        ) from exc
    except (TimeoutError, OSError) as exc:
        raise RuntimeError(
            f"{provider} did not respond within {timeout}s (connection may "
            f"be slow or the model may be cold/queued). Retry the same call "
            f"with a larger --timeout, e.g. --timeout 300."
        ) from exc

    try:
        return payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected response shape from {provider}: {payload}") from exc


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def read_prompt(args) -> str:
    """Resolve the prompt from --prompt, --prompt-file, or stdin."""
    if args.prompt_file is not None:
        if args.prompt_file == "-":
            return sys.stdin.read()
        return Path(args.prompt_file).read_text(encoding="utf-8")
    if args.prompt:
        return args.prompt
    # Nothing given: fall back to piped stdin (cat file.py | ask_llm.py).
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="ask_llm",
        description="Delegate a coding question/review/task to an external LLM.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Providers: " + ", ".join(PROVIDERS) + "\n"
            "Model names drift over time - check the provider's /v1/models\n"
            "catalog for live IDs. 404 on nvidia = model not enabled for your\n"
            "account; pick another from the catalog. Cold models can take\n"
            "minutes - retry with --timeout 300."
        ),
    )
    parser.add_argument("--prompt", "-p", help="The question, code snippet, or task")
    parser.add_argument("--prompt-file", help="File containing the prompt ('-' = stdin)")
    parser.add_argument("--system-prompt", "-s", default=DEFAULT_SYSTEM_PROMPT,
                        help=f"Role/context for the model (default: {DEFAULT_SYSTEM_PROMPT!r})")
    parser.add_argument("--provider", default="groq", choices=sorted(PROVIDERS),
                        help="LLM provider (default: groq)")
    parser.add_argument("--model", "-m", default="llama-3.1-8b-instant",
                        help="Model name recognized by the provider")
    parser.add_argument("--temperature", "-t", type=float, default=0.0,
                        help="0.0 = deterministic (code), up to 1.0 = creative (default: 0.0)")
    parser.add_argument("--max-tokens", type=int, default=4096,
                        help="Maximum response length (default: 4096)")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                        help="Request timeout in seconds (default: 120)")
    parser.add_argument("--list-providers", action="store_true",
                        help="Print the provider registry and exit")
    args = parser.parse_args()

    # Windows consoles are often not UTF-8; force it so UTF-8 replies never crash.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    if args.list_providers:
        load_dotenv()
        for name in sorted(PROVIDERS):
            cfg = PROVIDERS[name]
            if cfg["key_env"]:
                key = f"{cfg['key_env']} ({'present' if os.environ.get(cfg['key_env']) else 'MISSING'})"
            else:
                key = "no key needed (local)"
            print(f"{name:<11} {cfg['base_url']:<40} key: {key}")
        return 0

    load_dotenv()

    prompt = read_prompt(args)
    if not prompt.strip():
        parser.error("empty prompt: pass --prompt, --prompt-file, or pipe text on stdin")

    try:
        reply = call_llm(
            provider=args.provider,
            model=args.model,
            system_prompt=args.system_prompt,
            prompt=prompt,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            timeout=args.timeout,
        )
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        # Missing-key problems are config errors (1); anything after the
        # request was attempted is a network/API failure (2).
        return 1 if "Missing API key" in str(exc) else 2

    print(reply)
    return 0


if __name__ == "__main__":
    sys.exit(main())
