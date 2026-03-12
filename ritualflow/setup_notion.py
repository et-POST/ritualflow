"""Setup the RitualFlow - Generated Notion database."""

from notion_client import Client

from ritualflow.config import NOTION_TOKEN, RITUALFLOW_OUTPUT_PAGE_ID



EXAMPLE_HABITS = [
    {
        "name": "Daily Tech Quiz",
        "frequency": "daily",
        "prompt": "Generate a 5-question tech quiz on a random programming topic",
        "category": "tech",
    },
    {
        "name": "Discover Paris",
        "frequency": "monthly",
        "prompt": "Suggest an interesting place to discover in Paris",
        "category": "wellness",
    },
    {
        "name": "Weekly Tech Digest",
        "frequency": "weekly",
        "prompt": "Generate a weekly summary of tech trends and news",
        "category": "tech",
    },
]

# SELECT options for the Habit column in the Generated DB
HABIT_SELECT_OPTIONS = [
    {"name": "Daily Tech Quiz",    "color": "blue"},
    {"name": "Fun Fact du Jour",   "color": "yellow"},
    {"name": "Decouverte Paris",   "color": "green"},
    {"name": "Weekly Tech Digest", "color": "purple"},
]


def add_habit(name: str, frequency: str, prompt: str, category: str) -> str:
    """Add a habit entry to the Habits database. Returns the new page ID."""
    if not RITUALFLOW_DB_ID:
        raise RuntimeError("RITUALFLOW_DB_ID is not set in .env")
    client = Client(auth=NOTION_TOKEN)
    page = client.pages.create(
        parent={"database_id": RITUALFLOW_DB_ID},
        properties={
            "Name":      {"title": [{"text": {"content": name}}]},
            "Frequency": {"select": {"name": frequency}},
            "Prompt":    {"rich_text": [{"text": {"content": prompt}}]},
            "Category":  {"select": {"name": category}},
            "Active":    {"checkbox": True},
        },
    )
    return page["id"]


def setup_database(parent_page_id: str | None = None) -> str:
    """Create the RitualFlow - Generated database. Returns the Notion block ID."""
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
                    "select": {"options": HABIT_SELECT_OPTIONS}
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
    collection_id = db["id"]
    print(f"  Collection ID (API): {collection_id}")

    # With is_inline=True, Notion creates a block in the parent page whose ID differs
    # from the collection ID. The block ID is what Notion shows in its URL.
    # We fetch it by listing the parent page's children.
    block_id = collection_id
    try:
        children = client.blocks.children.list(block_id=parent_id)
        for block in children.get("results", []):
            if block.get("type") == "child_database":
                title = block.get("child_database", {}).get("title", "")
                if "Generated" in title:
                    block_id = block["id"]
                    break
    except Exception as e:
        print(f"  [warn] Could not fetch block ID, falling back to collection ID: {e}")

    print(f"Created Generated database: {block_id}")

    # Populate the Habits DB with example habits
    for habit in EXAMPLE_HABITS:
        client.pages.create(
            parent={"database_id": collection_id},
            properties={
                "Name":      {"title": [{"text": {"content": habit["name"]}}]},
                "Frequency": {"select": {"name": habit["frequency"]}},
                "Prompt":    {"rich_text": [{"text": {"content": habit["prompt"]}}]},
                "Category":  {"select": {"name": habit["category"]}},
                "Active":    {"checkbox": False},
            },
        )
        print(f"  Added habit: {habit['name']}")

    return block_id


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
