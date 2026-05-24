# Swiss Tax Advisor — Canton Schwyz

AI-powered tax declaration review tool that reads your Steuererklärung PDF and identifies errors, missing deductions, and optimization opportunities specific to Canton Schwyz.

Built with the [Claude Agent SDK](https://docs.claude.com/en/api/agent-sdk/overview).

## Setup

```bash
# Create and activate virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and add your key from https://console.anthropic.com/
```

Requires [Claude Code CLI](https://docs.claude.com/en/api/agent-sdk/overview) (`npm install -g @anthropic-ai/claude-code`).

## Usage

Analyze a tax declaration PDF:

```bash
python main.py /path/to/steuererklaerung.pdf
```

Interactive mode (no PDF):

```bash
python main.py
```

After the initial analysis, you can ask follow-up questions — the agent remembers context from the conversation.

## What it checks

- Completeness of income declarations (salary, side income, rental, investments)
- Deduction eligibility and limits (Pillar 3a, professional expenses, insurance premiums, etc.)
- Calculation consistency across sections
- Canton Schwyz-specific rules and municipal tax multipliers (Steuerfuss)
- Optimization opportunities to legally reduce tax burden
