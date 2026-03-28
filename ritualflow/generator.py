"""Generate content for habits using the Anthropic API or Claude Code CLI as fallback."""

import os
import subprocess
from datetime import date

from ritualflow.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL
from ritualflow.habits import Habit
from ritualflow.templates import get_template


def generate_content(habit: Habit, ref_date: date | None = None) -> str:
    """Generate content for a habit. Tries the Anthropic API first, falls back to Claude Code CLI."""
    d = ref_date or date.today()
    date_str = d.strftime("%B %d, %Y")
    prompt = _build_prompt(habit, date_str)

    # Try Anthropic API first
    if ANTHROPIC_API_KEY:
        try:
            return _generate_via_api(prompt)
        except Exception as e:
            error_msg = str(e)
            if "credit balance" in error_msg or "billing" in error_msg.lower():
                print("  [info] API credits unavailable, falling back to Claude Code CLI...")
            else:
                print(f"  [warn] API error: {error_msg}, falling back to Claude Code CLI...")

    # Fallback: Claude Code CLI
    return _generate_via_claude_code(prompt)


def _generate_via_api(prompt: str) -> str:
    """Generate content using the Anthropic API directly."""
    import anthropic

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def _generate_via_claude_code(prompt: str) -> str:
    """Generate content using the Claude Code CLI (uses Claude Pro subscription)."""
    # Remove CLAUDECODE (nested session guard) and ANTHROPIC_API_KEY
    # so Claude Code uses its own Claude Pro auth instead of the API key
    KEYS_TO_REMOVE = {"CLAUDECODE", "ANTHROPIC_API_KEY"}
    env = {k: v for k, v in os.environ.items() if k not in KEYS_TO_REMOVE}

    result = subprocess.run(
        ["claude", "-p", prompt, "--model", "haiku", "--allowedTools", "WebSearch,WebFetch"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=300,
        encoding="utf-8",
        errors="replace",
        env=env,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Claude Code CLI failed (code {result.returncode}): "
            f"{result.stderr or result.stdout}"
        )

    output = result.stdout.strip()
    if not output:
        raise RuntimeError("Claude Code CLI returned empty output")

    return output


def _build_prompt(habit: Habit, date_str: str) -> str:
    """Build the generation prompt: custom prompt takes priority over category template."""
    # Custom prompt wins — always use it if defined
    if habit.prompt:
        return (
            f"{habit.prompt}\n\n"
            f"Date: {date_str}\n"
            f"Use web search to find the latest information if the topic requires current data.\n"
            f"Never say you can't access the internet or that your knowledge is outdated.\n"
            f"Always produce the final content directly — never ask the user to choose.\n"
            f"Format the output as clean Notion-compatible Markdown with headers, "
            f"bullet points, and sections. Make it engaging and well-structured."
        )

    # Fallback: category template
    template = get_template(habit.category)
    if template:
        return template.replace("{date}", date_str)

    return (
        f"Generate content about: {habit.name}\n\n"
        f"Date: {date_str}\n"
        f"Format the output as clean Notion-compatible Markdown."
    )
