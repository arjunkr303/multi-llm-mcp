# multi-llm skill

Standalone agent skill version of [multi-llm-mcp](../README.MD) — lets any
agent delegate coding tasks to NVIDIA NIM, OpenRouter, Groq, DeepSeek, or a
local Ollama by running one script. **Zero dependencies** (Python stdlib only).
The MCP server under `src/` is unaffected; use either or both.

## What's here

```
multi-llm-skill/
├── SKILL.md           # skill metadata + instructions the agent loads on trigger
├── scripts/
│   └── ask_llm.py     # the CLI the agent actually runs
└── README.md          # this file
```

## Install

### Claude Code / Claude Desktop (skills)

Copy the folder into your skills directory:

```bash
# All projects (global)
~/.claude/skills/multi-llm/

# or, project-scoped
.claude/skills/multi-llm/
```

### OpenCode

```bash
~/.config/opencode/skill/multi-llm/    # global
.opencode/skill/multi-llm/             # project-scoped
```

Also register the CLI as an allowed/shell-executable command per your harness
config if it prompts before running scripts.

### Any other agent harness

Agents without native skill support (Cursor, Codex CLI, Cline, Gemini CLI,
aider, ...) don't auto-discover SKILL.md — you add one line telling them
where to find it, with the essentials inline. Copy the folder anywhere
(e.g. `tools/multi-llm-skill/`) and paste the snippet below into the rules
file the agent reads: `AGENTS.md`, `CLAUDE.md`, `.cursorrules`,
`.windsurfrules`, or the system prompt. Then replace
`<PATH-TO-THIS-FOLDER>` with the real path.

````markdown
## External LLM delegation (multi-llm skill)

When the user asks for a second opinion, independent code review, tests from
another model, or designated provider/model use, delegate to an external LLM:

```bash
python "<PATH-TO-THIS-FOLDER>/scripts/ask_llm.py" --help                       # full usage
python "<PATH-TO-THIS-FOLDER>/scripts/ask_llm.py" --list-providers            # check which keys exist
python "<PATH-TO-THIS-FOLDER>/scripts/ask_llm.py" --provider groq --prompt "..."   # quick task
```

Routing: groq = fast/cheap; deepseek = tests & code; openrouter = large context;
ollama = private/offline (no key needed); nvidia = open-weights. Model names
drift — on 404/410 pick another model from the provider's /v1/models catalog.

Rules: paste the actual code in --prompt (or --prompt-file for large input;
the model has no filesystem access). Use temp 0.0 for code. Treat replies as
advisory — verify before editing. Use ollama for code that must not leave the
machine. Read <PATH-TO-THIS-FOLDER>/SKILL.md for full persona presets and
task-type guidance.
````

Chat-only LLMs that cannot run shell commands can still use this skill's
persona presets and routing tables as prompt-engineering guidance manually;
only the automation needs shell access.

## API keys

Keys are read from environment variables first, then from a `.env` file in the
current directory, the skill folder, or the repo root. You only need a key for
providers you use — `ollama` needs none.

```env
NVIDIA_API_KEY=nvapi-...
OPENROUTER_API_KEY=sk-or-v1-...
GROQ_API_KEY=gsk_...
DEEPSEEK_API_KEY=sk-...
```

## Try it manually

```bash
# list providers
python scripts/ask_llm.py --list-providers

# quick question (defaults: groq / llama-3.1-8b-instant)
python scripts/ask_llm.py --prompt "Explain what a context manager is in Python."

# routed by task type
python scripts/ask_llm.py --provider deepseek --model deepseek-coder --system-prompt "You are a test engineer." --prompt-file review.txt

# pipe a large file in on stdin (--prompt-file - reads stdin)
cat big_code.py | python scripts/ask_llm.py --prompt-file -

# list live model IDs from a provider's catalog (names drift!)
curl https://api.groq.com/openai/v1/models -H "Authorization: Bearer $GROQ_API_KEY"

# fully private / offline (requires local Ollama with a pulled model)
python scripts/ask_llm.py --provider ollama --model codellama --prompt "Refactor this function: ..."
```

## MCP vs skill — when to use which

| | MCP server (`src/`) | This skill |
|---|---|---|
| Best for | IDEs with MCP clients (Cursor, VS Code, Claude Desktop) | Any agent with shell access; no per-client registration |
| Execution | stdio server process | One Python script run per call |
| Dependency setup | `pip install -e .` + venv | None |

Both call the same OpenAI-compatible provider endpoints and read the same
`.env` keys, so they can coexist independently.
