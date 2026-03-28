"""Dashboard stats: count generated child pages and update the stats callout block."""

from datetime import date, timedelta

from notion_client import Client

from ritualflow.config import (
    NOTION_TOKEN,
    RITUALFLOW_GENERATED_DB_ID,
    RITUALFLOW_STATS_BLOCK_ID,
)
from ritualflow.habits import get_active_habits
from ritualflow.utils import notion_query_db


def _get_notion_client() -> Client:
    return Client(auth=NOTION_TOKEN)


def _monday_of_week(d: date) -> date:
    """Return the Monday of the week containing d."""
    return d - timedelta(days=d.weekday())


def _count_child_pages_by_period(client: Client) -> tuple[int, int]:
    """Count generated child pages for this week and this month.

    Iterates all active habits, lists their child pages, and filters
    by creation date (created_time from the Notion API).

    Returns (week_count, month_count).
    """
    today = date.today()
    monday = _monday_of_week(today)
    month_start = date(today.year, today.month, 1)

    week_count = 0
    month_count = 0

    try:
        habits = get_active_habits()
    except Exception:
        return 0, 0

    for habit in habits:
        try:
            children = client.blocks.children.list(block_id=habit.id)
            for block in children.get("results", []):
                if block.get("type") != "child_page":
                    continue
                created = block.get("created_time", "")[:10]  # "2026-03-14"
                if not created:
                    continue
                created_date = date.fromisoformat(created)
                if created_date >= month_start:
                    month_count += 1
                if created_date >= monday:
                    week_count += 1
        except Exception:
            continue

    return week_count, month_count


def update_stats() -> bool:
    """Count generated pages and update the stats callout block on the main page.

    Returns True on success, False if not configured or on error.
    """
    if not RITUALFLOW_STATS_BLOCK_ID:
        return False

    client = _get_notion_client()

    week_total, month_total = _count_child_pages_by_period(client)

    week_line = f"Cette semaine : {week_total} générée{'s' if week_total != 1 else ''}"
    month_line = f"Ce mois : {month_total} générée{'s' if month_total != 1 else ''}"
    stats_text = f"{week_line}\n{month_line}"

    try:
        client.blocks.update(
            block_id=RITUALFLOW_STATS_BLOCK_ID,
            callout={
                "rich_text": [{"type": "text", "text": {"content": stats_text}}],
                "icon": {"type": "emoji", "emoji": "\U0001f4ca"},
                "color": "blue_background",
            },
        )
        print(f"  [dashboard] Stats updated: {stats_text.replace(chr(10), ' | ')}")
        return True
    except Exception as e:
        print(f"  [warn] Could not update stats block: {e}")
        return False
