"""Read habit definitions from Notion database."""

from dataclasses import dataclass
from notion_client import Client

from ritualflow.config import NOTION_TOKEN, RITUALFLOW_DS_ID


@dataclass
class Habit:
    id: str
    name: str
    frequency: str  # daily, weekly, monthly
    prompt: str
    category: str
    active: bool
    output_page_id: str | None


def _get_notion_client() -> Client:
    return Client(auth=NOTION_TOKEN)


def get_active_habits(frequency: str | None = None) -> list[Habit]:
    """Query the RitualFlow data source for active habits, optionally filtered by frequency."""
    client = _get_notion_client()

    filter_conditions = [{"property": "Active", "checkbox": {"equals": True}}]
    if frequency:
        filter_conditions.append(
            {"property": "Frequency", "select": {"equals": frequency}}
        )

    if len(filter_conditions) == 1:
        notion_filter = filter_conditions[0]
    else:
        notion_filter = {"and": filter_conditions}

    results = client.data_sources.query(
        data_source_id=RITUALFLOW_DS_ID,
        filter=notion_filter,
    )

    habits = []
    for page in results["results"]:
        props = page["properties"]
        name = _get_title(props.get("Name", {}))
        freq = _get_select(props.get("Frequency", {}))
        prompt = _get_rich_text(props.get("Prompt", {}))
        category = _get_select(props.get("Category", {}))
        output_page_id = _get_rich_text(props.get("Output Page", {})) or None

        habits.append(
            Habit(
                id=page["id"],
                name=name,
                frequency=freq,
                prompt=prompt,
                category=category,
                active=True,
                output_page_id=output_page_id,
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
