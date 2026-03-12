"""Dashboard stats: query Generated DB and update the stats callout block."""

from datetime import date, timedelta

from notion_client import Client

from ritualflow.config import (
    NOTION_TOKEN,
    RITUALFLOW_GENERATED_DB_ID,
    RITUALFLOW_STATS_BLOCK_ID,
)


def _get_notion_client() -> Client:
    return Client(auth=NOTION_TOKEN)


def _monday_of_week(d: date) -> date:
    """Return the Monday of the week containing d."""
    return d - timedelta(days=d.weekday())


def _query_generated(client: Client, start_date: str, end_date: str) -> list[dict]:
    """Query the Generated database for entries in [start_date, end_date]."""
    if not RITUALFLOW_GENERATED_DB_ID:
        return []
    try:
        results = client.databases.query(
            database_id=RITUALFLOW_GENERATED_DB_ID,
            filter={
                "and": [
                    {"property": "Date", "date": {"on_or_after": start_date}},
                    {"property": "Date", "date": {"on_or_before": end_date}},
                ]
            },
        )
        return results.get("results", [])
    except Exception as e:
        print(f"  [warn] Could not query Generated DB: {e}")
        return []


def _count_stats(pages: list[dict]) -> tuple[int, int]:
    """Return (total, read) from a list of Generated DB page entries."""
    total = len(pages)
    read = sum(
        1 for p in pages
        if p.get("properties", {}).get("Lu", {}).get("checkbox", False)
    )
    return total, read


def _format_stats_text(
    week_total: int, week_read: int,
    month_total: int, month_read: int,
) -> str:
    def pct(read, total):
        if total == 0:
            return "--"
        return f"{round(read / total * 100)}%"

    week_line = (
        f"Cette semaine : {week_total} g\u00e9n\u00e9r\u00e9e{'s' if week_total != 1 else ''}"
        f" \u00b7 {week_read}/{week_total} lue{'s' if week_read != 1 else ''}"
        f" ({pct(week_read, week_total)})"
    )
    month_line = (
        f"Ce mois : {month_total} g\u00e9n\u00e9r\u00e9e{'s' if month_total != 1 else ''}"
        f" \u00b7 {month_read}/{month_total} lue{'s' if month_read != 1 else ''}"
        f" ({pct(month_read, month_total)})"
    )
    return f"{week_line}\n{month_line}"


def update_stats() -> bool:
    """Query Generated DB and update the stats callout block on the main page.

    Returns True on success, False if not configured or on error.
    """
    if not RITUALFLOW_GENERATED_DB_ID or not RITUALFLOW_STATS_BLOCK_ID:
        return False

    client = _get_notion_client()
    today = date.today()

    # Week range: Monday → Sunday
    monday = _monday_of_week(today)
    sunday = monday + timedelta(days=6)

    # Month range: 1st → last day
    if today.month == 12:
        next_month_first = date(today.year + 1, 1, 1)
    else:
        next_month_first = date(today.year, today.month + 1, 1)
    last_day = next_month_first - timedelta(days=1)
    month_start = date(today.year, today.month, 1)

    week_pages  = _query_generated(client, monday.isoformat(), sunday.isoformat())
    month_pages = _query_generated(client, month_start.isoformat(), last_day.isoformat())

    week_total,  week_read  = _count_stats(week_pages)
    month_total, month_read = _count_stats(month_pages)

    stats_text = _format_stats_text(week_total, week_read, month_total, month_read)

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
