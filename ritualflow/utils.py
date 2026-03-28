"""Utilities for Notion API calls."""

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
