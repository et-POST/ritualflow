"""Configuration management for RitualFlow."""

import os
from dotenv import load_dotenv

load_dotenv(override=True)

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
RITUALFLOW_DB_ID = os.getenv("RITUALFLOW_DB_ID")
RITUALFLOW_DS_ID = os.getenv("RITUALFLOW_DS_ID")
RITUALFLOW_OUTPUT_PAGE_ID = os.getenv("RITUALFLOW_OUTPUT_PAGE_ID")

# Generated pages database (new structure)
RITUALFLOW_GENERATED_DB_ID = os.getenv("RITUALFLOW_GENERATED_DB_ID")
# Block ID of the stats callout on the main RitualFlow page
RITUALFLOW_STATS_BLOCK_ID  = os.getenv("RITUALFLOW_STATS_BLOCK_ID")

ANTHROPIC_MODEL = "claude-haiku-4-5"


def validate_config():
    """Check that all required env vars are set.

    ANTHROPIC_API_KEY is optional: if absent or out of credits,
    the generator falls back to the Claude Code CLI automatically.
    """
    missing = []
    if not NOTION_TOKEN:
        missing.append("NOTION_TOKEN")
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")
