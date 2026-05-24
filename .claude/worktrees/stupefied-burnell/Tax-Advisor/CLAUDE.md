# Tax-Advisor

Swiss Tax Advisor agent for Canton Schwyz, built with the Claude Agent SDK (Python).

## Project structure

- `main.py` — Main entry point. Contains system prompt, CLI argument handling, and interactive conversation loop using `ClaudeSDKClient`.
- `requirements.txt` — Python dependencies (claude-agent-sdk, python-dotenv).
- `.env` — API key (not committed). Copy from `.env.example`.

## Tech stack

- Python 3.12
- claude-agent-sdk (latest)
- python-dotenv for environment config
- Virtual environment at `.venv/`

## Key patterns

- Uses `ClaudeSDKClient` (not `query()`) for multi-turn conversations with session continuity.
- Permission mode is `bypassPermissions` since the agent only uses read-only tools (`Read`, `Glob`, `Grep`).
- System prompt contains Canton Schwyz-specific tax rules and deduction limits.
- Supports both PDF analysis mode (via CLI argument) and interactive mode.

## Running

```bash
source .venv/bin/activate
python main.py /path/to/steuererklaerung.pdf
```

Cannot be run from within a Claude Code session (nested session check on `CLAUDECODE` env var).
