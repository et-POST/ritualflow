"""Utilities for Notion API calls."""

from typing import Any

import httpx


NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
NOTION_TIMEOUT = 30  # seconds


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
        timeout=NOTION_TIMEOUT,
    )
    response.raise_for_status()
    return response.json().get("results", [])


def _notion_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }


def notion_list_children(token: str, block_id: str) -> list[dict]:
    """List children blocks of a Notion block via direct HTTP.

    Handles pagination (Notion returns max 100 blocks per request).
    Returns the full list of child blocks.
    """
    all_blocks: list[dict] = []
    url = f"{NOTION_API_BASE}/blocks/{block_id}/children?page_size=100"

    while url:
        response = httpx.get(url, headers=_notion_headers(token), timeout=NOTION_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        all_blocks.extend(data.get("results", []))
        if data.get("has_more") and data.get("next_cursor"):
            url = f"{NOTION_API_BASE}/blocks/{block_id}/children?page_size=100&start_cursor={data['next_cursor']}"
        else:
            url = None

    return all_blocks


def notion_update_block(token: str, block_id: str, block_data: dict) -> dict:
    """Update a Notion block via direct HTTP — bypasses notion-client SDK bugs.

    block_data should be the block type payload, e.g. {"callout": {...}}.
    """
    response = httpx.patch(
        f"{NOTION_API_BASE}/blocks/{block_id}",
        headers=_notion_headers(token),
        json=block_data,
        timeout=NOTION_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()
