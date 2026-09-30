"""
multi-llm-gateway — MCP server for delegating tasks to multiple LLM providers.

Exposes tools that any MCP-compatible IDE agent can call to query cloud or
local LLMs. Supports NVIDIA NIM, OpenRouter, Groq, DeepSeek, and Ollama.
"""

from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from .providers import get_client, PROVIDERS

load_dotenv()

mcp = FastMCP("multi-llm-gateway")


# ──────────────────────────────────────────────
# Tools
# ──────────────────────────────────────────────


@mcp.tool()
def ask_llm(
    prompt: str,
    system_prompt: str = "You are a helpful coding assistant.",
    provider: str = "ollama",
    model: str = "llama3",
    temperature: float = 0.0,
    max_tokens: int = 4096,
) -> str:
    """Delegate a coding question, code review, or subtask to an external LLM.

    Use this when you want a second opinion, a different model's reasoning,
    or access to a model not otherwise available (e.g. a larger context
    window model via OpenRouter, or a specialized coding model via NVIDIA NIM).

    Args:
        prompt: The question, code snippet, or task description.
        system_prompt: Role/context for the model
                       (e.g. "You are a senior Rust reviewer").
        provider: One of 'nvidia', 'openrouter', 'ollama', 'groq', 'deepseek'.
        model: Model name as recognized by the chosen provider.
        temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative).
                     Use 0.0 for code generation, higher for brainstorming.
        max_tokens: Maximum number of tokens in the response.

    Returns:
        The model's text response.
    """
    client = get_client(provider)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
