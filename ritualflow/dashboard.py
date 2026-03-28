"""Dashboard stats: count generated child pages and update the stats callout block."""

from datetime import date, timedelta

from ritualflow.config import (
    NOTION_TOKEN,
    RITUALFLOW_STATS_BLOCK_ID,
)
from ritualflow.habits import get_active_habits
from ritualflow.utils import notion_list_children, notion_update_block


def _monday_of_week(d: date) -> date:
    """Return the Monday of the week containing d."""
    return d - timedelta(days=d.weekday())


def _count_child_pages() -> tuple[int, int]:
    """Count generated child pages for this week and all time.

    Iterates all active habits, lists their child pages, and filters
    by creation date (created_time from the Notion API).

    Returns (week_count, total_count).
    """
    today = date.today()
    monday = _monday_of_week(today)

    week_count = 0
    total_count = 0

    try:
        habits = get_active_habits()
    except Exception:
        return 0, 0

    for habit in habits:
        try:
            children = notion_list_children(NOTION_TOKEN, habit.id)
            for block in children:
                if block.get("type") != "child_page":
                    continue
                total_count += 1
                created = block.get("created_time", "")[:10]
                if created:
                    created_date = date.fromisoformat(created)
                    if created_date >= monday:
                        week_count += 1
        except Exception:
            continue

    return week_count, total_count


def update_stats() -> bool:
    """Count generated pages and update the stats callout block on the main page.

    Returns True on success, False if not configured or on error.
    """
    if not RITUALFLOW_STATS_BLOCK_ID:
        return False

    week_total, all_total = _count_child_pages()

    week_line = f"This week: {week_total} generated"
    total_line = f"Total: {all_total} generated"
    stats_text = f"{week_line}\n{total_line}"

    try:
        notion_update_block(
            NOTION_TOKEN,
            RITUALFLOW_STATS_BLOCK_ID,
            {
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": stats_text}}],
                    "icon": {"type": "emoji", "emoji": "\U0001f4ca"},
                    "color": "blue_background",
                },
            },
        )
        print(f"  [dashboard] Stats updated: {stats_text.replace(chr(10), ' | ')}")
        return True
    except Exception as e:
        print(f"  [warn] Could not update stats block: {e}")
        return False
