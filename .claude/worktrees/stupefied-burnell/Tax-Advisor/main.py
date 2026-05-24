import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from claude_agent_sdk import (
    AssistantMessage,
    CLINotFoundError,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ProcessError,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
)

load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    print("Error: ANTHROPIC_API_KEY not set.")
    print("Copy .env.example to .env and add your key from https://console.anthropic.com/")
    sys.exit(1)

if os.getenv("CLAUDECODE"):
    print("Error: Cannot run inside a Claude Code session (nested sessions not supported).")
    print("Please run this from a separate terminal window.")
    sys.exit(1)

SYSTEM_PROMPT = """\
You are an expert Swiss tax advisor specializing in Canton Schwyz taxation.
Your role is to review a taxpayer's Steuererklärung (tax declaration) and identify
errors, omissions, or optimization opportunities.

## Your expertise

- Swiss federal tax law (DBG / LIFD) and Canton Schwyz tax law (StG SZ)
- Canton Schwyz tax rates, deductions, and allowances for the current tax year
- Common mistakes Swiss taxpayers make on their declarations

## Canton Schwyz specifics

- Canton Schwyz has one of the lowest tax rates in Switzerland.
- Flat cantonal tax rate: the cantonal simple tax rate is applied with a cantonal
  multiplier (Steuerfuss) that varies by municipality (Gemeinde).
- Key deductions available in Schwyz:
  - Professional expenses (Berufsauslagen): commuting, meals, further education
  - Insurance premiums (Versicherungsprämien): health, life, accident insurance
  - Pillar 3a contributions: max CHF 7,056 (employed with pension fund) or 20% of
    net income up to CHF 35,280 (self-employed without pension fund) — verify against
    the year's actual limits
  - Pillar 2 buy-ins (Einkäufe BVG)
  - Mortgage interest and maintenance costs for property owners
  - Charitable donations (min CHF 100, up to 20% of net income)
  - Child deductions and childcare costs
  - Medical expenses exceeding a threshold
  - Debt interest deductions

## When reviewing a Steuererklärung

1. **Read the PDF carefully** — examine every page and field.
2. **Check for completeness**: Are all income sources declared? (salary, side income,
   rental income, investment income, etc.)
3. **Verify deductions**: Are all eligible deductions claimed? Are amounts within
   legal limits?
4. **Cross-check calculations**: Do totals add up? Are tax-relevant amounts correctly
   transferred between sections?
5. **Flag potential errors**: Identify anything that looks incorrect, inconsistent,
   or suboptimal.
6. **Suggest optimizations**: Point out deductions the taxpayer may have missed.

## Response format

Structure your analysis as:
- **Summary**: Brief overview of the declaration
- **Potential errors**: List any values that appear incorrect
- **Missing deductions**: Deductions the taxpayer could claim but didn't
- **Optimization suggestions**: Ways to legally reduce the tax burden
- **Warnings**: Anything that could trigger an audit or penalty

Always respond in the same language the user writes to you (German or English).
Be precise with amounts and reference specific line items or sections of the declaration.
"""


async def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <path-to-steuererklaerung.pdf>")
        print("       python main.py  (interactive mode without PDF)")
        pdf_path = None
    else:
        pdf_path = Path(sys.argv[1]).resolve()
        if not pdf_path.exists():
            print(f"Error: File not found: {pdf_path}")
            sys.exit(1)
        if not pdf_path.suffix.lower() == ".pdf":
            print(f"Warning: Expected a PDF file, got: {pdf_path.suffix}")

    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        allowed_tools=["Read", "Glob", "Grep"],
        permission_mode="bypassPermissions",
        max_turns=30,
    )

    try:
        client_ctx = ClaudeSDKClient(options=options)
    except CLINotFoundError:
        print("Error: Claude Code CLI not found.")
        print("Install it with: npm install -g @anthropic-ai/claude-code")
        sys.exit(1)

    async with client_ctx as client:
        # Build the initial prompt
        if pdf_path:
            initial_prompt = (
                f"Please read and analyze my Steuererklärung (tax declaration) for "
                f"Canton Schwyz. The PDF is located at: {pdf_path}\n\n"
                f"Read the entire PDF, then provide a thorough review identifying any "
                f"errors, missing deductions, and optimization opportunities."
            )
        else:
            initial_prompt = (
                "Hello! I'm ready to help you review your Canton Schwyz "
                "Steuererklärung. Please tell me what you'd like to discuss, "
                "or provide the path to your tax declaration PDF."
            )

        print("=" * 60)
        print("  Swiss Tax Advisor — Canton Schwyz")
        print("=" * 60)

        if pdf_path:
            print(f"\nAnalyzing: {pdf_path}")
        print()

        # Send initial prompt
        await client.query(initial_prompt)

        # Process the initial analysis
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text, end="")
                    elif isinstance(block, ToolUseBlock):
                        print(f"\n[Reading: {block.input.get('file_path', '...')}]\n")
            elif isinstance(message, ResultMessage):
                if message.is_error:
                    print(f"\nError: {message.result}")
                if message.total_cost_usd is not None:
                    print(f"\n\n(Cost: ${message.total_cost_usd:.4f})")
        print()

        # Interactive follow-up loop
        while True:
            print("-" * 60)
            try:
                user_input = input("Follow-up question (or 'quit' to exit): ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if not user_input or user_input.lower() in ("quit", "exit", "q"):
                print("Goodbye!")
                break

            await client.query(user_input)

            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(block.text, end="")
                        elif isinstance(block, ToolUseBlock):
                            print(
                                f"\n[Reading: {block.input.get('file_path', '...')}]\n"
                            )
                elif isinstance(message, ResultMessage):
                    if message.is_error:
                        print(f"\nError: {message.result}")
                    if message.total_cost_usd is not None:
                        print(f"\n\n(Cost: ${message.total_cost_usd:.4f})")
            print()


if __name__ == "__main__":
    asyncio.run(main())
