# multi-llm-mcp

An MCP server that lets any IDE agent delegate coding tasks to any LLM — cloud APIs or local models — through a single unified interface.

Instead of being locked into one model, your coding agent can call NVIDIA NIM, OpenRouter, Groq, DeepSeek, or a local Ollama model for a second opinion, code review, or specialized task.

---

## Features

- **5 providers out of the box** — NVIDIA NIM, OpenRouter, Groq, DeepSeek, Ollama
- **Local model support** — Use Ollama for fully offline, private coding assistance
- **Fine-grained control** — Set `temperature`, `max_tokens`, and `system_prompt` per call
- **Secure by design** — API keys stay in environment variables, never in code
- **Connection pooling** — Clients are cached for fast, efficient API calls
- **MCP standard** — Works with any MCP-compatible IDE (Claude Desktop, VS Code, Cursor, Windsurf, etc.)

## Supported Providers

| Provider | Type | Models |
|----------|------|--------|
| [Ollama](https://ollama.com/) | Local | Llama 3, CodeLlama, Mistral, Gemma, etc. |
| [NVIDIA NIM](https://build.nvidia.com/) | Cloud | Llama 3.1 405B, Mixtral, Code Llama, etc. |
| [OpenRouter](https://openrouter.ai/) | Cloud | Claude, GPT-4, Gemini, 200+ models |
| [Groq](https://groq.com/) | Cloud | Llama 3, Mixtral, Gemma (ultra-fast inference) |
| [DeepSeek](https://deepseek.com/) | Cloud | DeepSeek Coder, DeepSeek Chat |

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/arjunkr303/multi-llm-mcp.git
cd multi-llm-mcp

python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

pip install -e .
```

### 2. Configure API keys

```bash
cp .env.example .env
```

Edit `.env` and add your API keys. You only need keys for the providers you want to use. Ollama requires no API key.

```env
NVIDIA_API_KEY=your_nvidia_key_here
OPENROUTER_API_KEY=your_openrouter_key_here
GROQ_API_KEY=your_groq_key_here
DEEPSEEK_API_KEY=your_deepseek_key_here
```

### 3. Connect to your IDE

Add this to your MCP configuration:

**Claude Desktop** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "multi-llm-gateway": {
      "command": "/path/to/multi-llm-mcp/venv/bin/python",
      "args": ["-m", "multi_llm_mcp"]
    }
  }
}
```

**VS Code / Cursor** (`.vscode/mcp.json` or IDE MCP settings):
```json
{
  "mcpServers": {
    "multi-llm-gateway": {
      "command": "/path/to/multi-llm-mcp/venv/bin/python",
      "args": ["-m", "multi_llm_mcp"]
    }
  }
}
```

> Replace `/path/to/multi-llm-mcp` with the actual path where you cloned the repo.

### 4. Use it

Once connected, your IDE agent has access to the `ask_llm` tool. You can invoke it by prompting your agent naturally. The agent will call the MCP server behind the scenes.

#### Tool: `ask_llm`

Delegates a coding question, code review, or rewrite task to an external LLM.

**Parameters:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `prompt` | *(required)* | The question, code snippet, or task |
| `system_prompt` | `"You are a helpful coding assistant."` | Role context for the model |
| `provider` | `"ollama"` | Which provider to use |
| `model` | `"llama3"` | Model name for that provider |
| `temperature` | `0.0` | 0.0 = deterministic, 1.0 = creative |
| `max_tokens` | `4096` | Maximum response length |

#### Example Prompts

Use these prompts in your IDE chat to trigger the MCP tool:

**Rewrite code using a cloud model:**
```
Use NVIDIA's Llama 3.1 to rewrite the database query in db.py to use async/await.
```

**Get a code review from a different LLM:**
```
Ask Groq's Llama 3 to review src/multi_llm_mcp/server.py for performance issues and suggest improvements.
```

**Refactor with a local model (Ollama):**
```
Use Ollama to refactor the authentication logic in auth.py into smaller, testable functions.
```

**Generate tests using DeepSeek:**
```
Ask DeepSeek Coder to write unit tests for the parse_config function in utils.py.
```

**Get a second opinion on architecture:**
```
Use OpenRouter's Claude to evaluate whether the current project structure follows
best practices and suggest a better layout.
```

## Using with Ollama (Local Models)

For fully private, offline coding assistance:

```bash
# Install Ollama: https://ollama.com/download
ollama pull llama3
ollama pull codellama
```

Then use `provider: "ollama"` with any pulled model name. No API key needed.

## Security

- API keys are loaded from environment variables only
- `.env` is gitignored and never committed
- No secrets are hardcoded in source code
- All API communication happens server-side only

## Project Structure

```
multi-llm-mcp/
├── src/multi_llm_mcp/      # MCP server package
│   ├── __init__.py
│   ├── __main__.py         # entry point: python -m multi_llm_mcp
│   ├── server.py           # FastMCP server & the ask_llm tool
│   └── providers.py        # provider registry & client factory
├── tests/                  # pytest suite
├── pyproject.toml
├── .env.example
└── LICENSE
```

## Running Tests

```bash
pip install -e . pytest
pytest
```

## License

MIT — see [LICENSE](LICENSE) for details.

