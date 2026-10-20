---
name: multi-llm
description: Delegate coding questions, code reviews, test generation, refactoring suggestions, or second opinions to external LLMs (NVIDIA NIM, OpenRouter, Groq, DeepSeek, or a local Ollama) with zero dependencies. Use this skill whenever the user asks for another model's take, an independent review, a senior-engineer-style critique, tests written by a different model, privacy-preserving offline analysis of proprietary code, or when faster/cheaper inference for a subtask would help — even if they don't name a specific LLM or provider.
---

# Multi-LLM delegation

Delegate a subtask to an external LLM by running the bundled script. It works
with only Python installed — no pip installs, no server process, no MCP setup.

## When to delegate (and when not to)

Delegate when a second independent perspective adds value: reviewing your own
work, stress-testing an argument, generating a variant implementation, or
getting specialized reasoning (e.g. a large-context model over many files).
Do not delegate trivial lookups you can answer directly, and do not delegate
work that requires reading this user's filesystem — paste the relevant code
into the prompt instead, because the external model cannot see any files.

## How to call it

```
python "<skill-dir>/scripts/ask_llm.py" --provider <p> --model <m> --system-prompt "<persona>" --prompt "<task + code>"
```

Pin `<skill-dir>` to the actual directory containing this SKILL.md. For long
code, write it to a temp file and pass `--prompt-file <path>` (or pipe: use
`--prompt-file -`). Read the script's stdout as the model's answer; stderr
carries errors. Exit codes: 0 success, 1 misconfiguration (e.g. missing API
key), 2 CLI usage error or network/API failure.

## Provider routing

| Situation | Provider | Model | Temp |
|---|---|---|---|
| Fast, cheap review or quick question | `groq` | `llama-3.1-8b-instant` | 0.1 |
| Test generation, careful code edits | `deepseek` | `deepseek-coder` | 0.0 |
| Many files / large context, strongest reasoning | `openrouter` | `anthropic/claude-3.5-sonnet` | 0.0 |
| Proprietary code that must not leave the machine | `ollama` | `codellama` (any pulled model) | 0.0 |
| Big open-weights model | `nvidia` | `meta/llama-3.2-11b-vision-instruct` | 0.0 |

Default when the user has no preference: check `--list-providers` first, and
prefer the fastest provider whose key is actually present — typically `groq`,
else `nvidia`, else `ollama` (no key needed).

Model names drift — older ones get retired (NVIDIA marks dead models with
HTTP 410) and providers publish new ones. Note that NVIDIA's `/v1/models`
catalog also lists models the calling account may not actually be enabled
for: a 404 "Function ... Not found for account" means that model is not
available to you — pick another from the catalog. Query the live catalog,
then fall back on errors:

```
python "<skill-dir>/scripts/ask_llm.py" --list-providers
# which keys are present; list live models (NVIDIA example), then try the newest suitable one:
curl https://integrate.api.nvidia.com/v1/models -H "Authorization: Bearer $NVIDIA_API_KEY"
```

If a call fails with a model error (404/410), pick another candidate from the
catalog instead of retrying the same name. NVIDIA NIM models can also take
1-3 minutes on first call while cold/queued — retry with `--timeout 300`
before assuming the provider is down.

## Persona presets (pass as `--system-prompt`)

- **Reviewer** — "You are a senior staff engineer. Review the code for bugs,
  edge cases, performance problems, and security issues. Cite specific lines,
  then give a prioritized list of fixes."
- **Test engineer** — "You are a test engineer. Produce pytest cases covering
  happy path, edge cases, and failure modes. Output one complete test file,
  no prose."
- **Refactor advisor** — "You are a refactoring specialist. Propose a cleaner
  structure for this code with rationale, and show the refactored version."
- **Architect** — "You are a systems architect. Evaluate the following design
  or layout for scalability, maintainability, and simplicity. Be concrete."

Use temperature 0.0 for anything producing code; raise toward 0.7 only for
brainstorming or naming.

## Rules

1. Always paste the actual code or text into the prompt — never reference a
   file by path, since the external model has no filesystem access.
2. Sanitize first: the prompt content leaves the machine via the chosen
   provider (except Ollama). If it contains secrets or credentials, use
   `ollama` or redact.
3. One focused question per call beats one giant prompt. Batch code review
   into a single review call, but don't mix "review" and "write tests" task
   types in the same request.
4. Treat the reply as advisory. Verify claims against the real code before
   applying edits, and say which model produced the advice when summarizing.
