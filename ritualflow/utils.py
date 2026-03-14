"""Utilities for key generation, deduplication, and Notion API calls."""

from datetime import datetime, date
from typing import Any

import httpx


NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def notion_query_db(token: str, database_id: str, filter: dict | None = None) -> list[dict]:
    """Query a Notion database via direct HTTP — bypasses notion-client SDK bugs.

    Returns the list of page results.
    """
    body: dict[str, Any] = {}
    if filter:
        body["filter"] = filter

    response = httpx.post(
        f"{NOTION_API_BASE}/databases/{database_id}/query",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        },
        json=body,
    )
    response.raise_for_status()
    return response.json().get("results", [])


def make_habit_key(habit_name: str, frequency: str, ref_date: date | None = None) -> str:
    """Generate a unique key for a habit based on its name and the current period.

    Daily:   {habit_name}-2026-03-08
    Weekly:  {habit_name}-2026-W10
    Monthly: {habit_name}-2026-03
    """
    d = ref_date or date.today()
    slug = habit_name.strip().lower().replace(" ", "-")

    if frequency == "daily":
        return f"{slug}-{d.isoformat()}"
    elif frequency == "weekly":
        iso = d.isocalendar()
        return f"{slug}-{iso.year}-W{iso.week:02d}"
    elif frequency == "monthly":
        return f"{slug}-{d.year}-{d.month:02d}"
    else:
        raise ValueError(f"Unknown frequency: {frequency}")


def format_date_for_notion(d: date | None = None) -> str:
    """Return an ISO date string for Notion date properties."""
    return (d or date.today()).isoformat()
