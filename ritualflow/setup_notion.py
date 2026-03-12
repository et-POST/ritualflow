"""Setup the RitualFlow - Generated Notion database."""

from notion_client import Client

from ritualflow.config import NOTION_TOKEN, RITUALFLOW_GENERATED_DB_ID, RITUALFLOW_OUTPUT_PAGE_ID


EXAMPLE_HABITS = [
    {
        "name": "Tech Quiz (example)",
        "frequency": "daily",
        "prompt": "Generate a 5-question tech quiz on a random programming topic",
        "category": "tech",
    },
    {
        "name": "Discover Paris (example)",
        "frequency": "monthly",
        "prompt": "Suggest an interesting place to discover in Paris",
        "category": "wellness",
    },
    {
        "name": "Tech Digest (example)",
        "frequency": "weekly",
        "prompt": "Generate a weekly summary of tech trends and news",
        "category": "tech",
    },
]


def add_habit(name: str, frequency: str, prompt: str, category: str, active: bool = True, database_id: str | None = None) -> str:
    """Add a habit entry to the habits database. Returns the new page ID."""
    db_id = database_id or RITUALFLOW_GENERATED_DB_ID
    if not db_id:
        raise RuntimeError("No database ID — set RITUALFLOW_GENERATED_DB_ID in .env or pass database_id.")
    client = Client(auth=NOTION_TOKEN)
    page = client.pages.create(
        parent={"database_id": db_id},
        properties={
            "Name":      {"title": [{"text": {"content": name}}]},
            "Frequency": {"select": {"name": frequency}},
            "Prompt":    {"rich_text": [{"text": {"content": prompt}}]},
            "Category":  {"select": {"name": category}},
            "Active":    {"checkbox": active},
        },
    )
    return page["id"]


def setup_database(parent_page_id: str | None = None) -> str:
    """Create the RitualFlow database. Returns db_id."""
    client = Client(auth=NOTION_TOKEN)
    parent_id = parent_page_id or RITUALFLOW_OUTPUT_PAGE_ID

    if not parent_id:
        raise RuntimeError(
            "No parent page ID. Set RITUALFLOW_OUTPUT_PAGE_ID or pass --parent-page-id."
        )

    db = client.databases.create(
        parent={"type": "page_id", "page_id": parent_id},
        title=[{"type": "text", "text": {"content": "RitualFlow - Generated"}}],
        icon={"type": "emoji", "emoji": "\U0001f4d6"},
        is_inline=True,
        initial_data_source={
            "properties": {
                "Name": {"title": {}},
                "Active": {"checkbox": {}},
                "Prompt": {"rich_text": {}},
                "Category": {
                    "select": {
                        "options": [
                            {"name": "tech", "color": "blue"},
                            {"name": "wellness", "color": "green"},
                            {"name": "culture", "color": "purple"},
                        ]
                    }
                },
                "Frequency": {
                    "select": {
                        "options": [
                            {"name": "daily",   "color": "blue"},
                            {"name": "weekly",  "color": "green"},
                            {"name": "monthly", "color": "purple"},
                        ]
                    }
                },
                "Date": {"date": {}},
                "Lu": {"checkbox": {}},
            }
        },
    )
    db_id = db["id"]
    print(f"  DB ID: {db_id}")

    # Populate with example habits
    for habit in EXAMPLE_HABITS:
        try:
            add_habit(
                name=habit["name"],
                frequency=habit["frequency"],
                prompt=habit["prompt"],
                category=habit["category"],
                database_id=db_id,
                active=False,
            )
            print(f"  Added habit: {habit['name']}")
        except Exception as e:
            print(f"  [warn] Could not add habit '{habit['name']}': {e}")
            break

    return db_id


def setup_stats_block(page_id: str) -> str:
    """Append a stats callout block to the main RitualFlow page. Returns its block ID."""
    client = Client(auth=NOTION_TOKEN)

    result = client.blocks.children.append(
        block_id=page_id,
        children=[
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": (
                                    "Cette semaine : -- g\u00e9n\u00e9r\u00e9es \u00b7 --/-- lues\n"
                                    "Ce mois : -- g\u00e9n\u00e9r\u00e9es \u00b7 --/-- lues"
                                )
                            },
                        }
                    ],
                    "icon": {"type": "emoji", "emoji": "\U0001f4ca"},
                    "color": "blue_background",
                },
            }
        ],
    )

    block_id = result["results"][0]["id"]
    print(f"Created stats block: {block_id}")
    return block_id
