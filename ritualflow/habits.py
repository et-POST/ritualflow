"""Read habit definitions from Notion database."""

from dataclasses import dataclass
import click
from ritualflow.config import NOTION_TOKEN, RITUALFLOW_GENERATED_DB_ID
from ritualflow.utils import notion_query_db


@dataclass
class Habit:
    id: str
    name: str
    frequency: str  # daily, weekly, monthly
    prompt: str
    category: str
    active: bool


def get_active_habits(frequency: str | None = None) -> list[Habit]:
    """Query the RitualFlow data source for active habits, optionally filtered by frequency."""
    filter_conditions = [{"property": "Active", "checkbox": {"equals": True}}]
    if frequency:
        filter_conditions.append(
            {"property": "Frequency", "select": {"equals": frequency}}
        )

    if len(filter_conditions) == 1:
        notion_filter = filter_conditions[0]
    else:
        notion_filter = {"and": filter_conditions}

    if not RITUALFLOW_GENERATED_DB_ID:
        raise click.ClickException(
            "RITUALFLOW_GENERATED_DB_ID not set. Run 'ritualflow setup' and update your .env."
        )

    try:
        pages = notion_query_db(NOTION_TOKEN, RITUALFLOW_GENERATED_DB_ID, filter=notion_filter)
    except Exception:
        raise click.ClickException(
            f"Could not access database {RITUALFLOW_GENERATED_DB_ID}.\n"
            "  Did you update RITUALFLOW_GENERATED_DB_ID in .env after running setup?\n"
            "  Make sure the database is shared with your Notion integration."
        )

    habits = []
    for page in pages:
        props = page["properties"]
        name = _get_title(props.get("Name", {}))
        freq = _get_select(props.get("Frequency", {}))
        prompt = _get_rich_text(props.get("Prompt", {}))
        category = _get_select(props.get("Category", {}))

        habits.append(
            Habit(
                id=page["id"],
                name=name,
                frequency=freq,
                prompt=prompt,
                category=category,
                active=True,
            )
        )

    return habits


def _get_title(prop: dict) -> str:
    parts = prop.get("title", [])
    return "".join(p.get("plain_text", "") for p in parts)


def _get_rich_text(prop: dict) -> str:
    parts = prop.get("rich_text", [])
    return "".join(p.get("plain_text", "") for p in parts)


def _get_select(prop: dict) -> str:
    sel = prop.get("select")
    return sel["name"] if sel else ""
