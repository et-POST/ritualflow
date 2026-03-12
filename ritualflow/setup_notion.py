"""Setup the Notion database and populate with example habits."""

import json
import urllib.request

from notion_client import Client

from ritualflow.config import NOTION_TOKEN, RITUALFLOW_OUTPUT_PAGE_ID


def _notion_patch(token: str, path: str, body: dict) -> dict:
    """Direct PATCH to Notion API — bypasses notion-client SDK bugs with properties."""
    req = urllib.request.Request(
        f"https://api.notion.com/v1/{path}",
        data=json.dumps(body).encode(),
        method="PATCH",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


EXAMPLE_HABITS = [
    {
        "name": "Daily Tech Quiz",
        "frequency": "daily",
        "prompt": "Generate a 5-question tech quiz on a random programming topic",
        "category": "tech",
    },
    {
        "name": "Fun Fact du Jour",
        "frequency": "daily",
        "prompt": "Generate a surprising and educational fun fact",
        "category": "fun",
    },
    {
        "name": "Decouverte Paris",
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

# Habit name → SELECT options for the Generated DB
HABIT_SELECT_OPTIONS = [
    {"name": "Daily Tech Quiz",    "color": "blue"},
    {"name": "Fun Fact du Jour",   "color": "yellow"},
    {"name": "Decouverte Paris",   "color": "green"},
    {"name": "Weekly Tech Digest", "color": "purple"},
]


def setup_database(parent_page_id: str | None = None) -> str:
    """Create the RitualFlow habits database and return its ID."""
    client = Client(auth=NOTION_TOKEN)
    parent_id = parent_page_id or RITUALFLOW_OUTPUT_PAGE_ID

    if not parent_id:
        raise RuntimeError(
            "No parent page ID. Set RITUALFLOW_OUTPUT_PAGE_ID or pass --parent-page-id."
        )

    db = client.databases.create(
        parent={"type": "page_id", "page_id": parent_id},
        title=[{"type": "text", "text": {"content": "RitualFlow - Habits"}}],
        icon={"type": "emoji", "emoji": "\u26a1"},
        properties={
            "Name": {"title": {}},
            "Frequency": {
                "select": {
                    "options": [
                        {"name": "daily",   "color": "blue"},
                        {"name": "weekly",  "color": "green"},
                        {"name": "monthly", "color": "purple"},
                    ]
                }
            },
            "Prompt": {"rich_text": {}},
            "Category": {
                "select": {
                    "options": [
                        {"name": "tech",    "color": "blue"},
                        {"name": "culture", "color": "orange"},
                        {"name": "wellness","color": "green"},
                        {"name": "fun",     "color": "yellow"},
                    ]
                }
            },
            "Active": {"checkbox": {}},
            "Output Page": {"rich_text": {}},
            "Last Run": {"date": {}},
        },
    )

    db_id = db["id"]
    print(f"Created Habits database: {db_id}")

    # Populate with example habits
    for habit in EXAMPLE_HABITS:
        client.pages.create(
            parent={"database_id": db_id},
            properties={
                "Name":      {"title": [{"text": {"content": habit["name"]}}]},
                "Frequency": {"select": {"name": habit["frequency"]}},
                "Prompt":    {"rich_text": [{"text": {"content": habit["prompt"]}}]},
                "Category":  {"select": {"name": habit["category"]}},
                "Active":    {"checkbox": True},
            },
        )
        print(f"  Added habit: {habit['name']}")

    print(f"\nHabits DB ready! Add to .env:\nRITUALFLOW_DB_ID={db_id}")
    return db_id


def setup_generated_db(parent_page_id: str | None = None) -> str:
    """Create the RitualFlow - Generated database. Returns the Notion block ID."""
    client = Client(auth=NOTION_TOKEN)
    parent_id = parent_page_id or RITUALFLOW_OUTPUT_PAGE_ID

    if not parent_id:
        raise RuntimeError(
            "No parent page ID. Set RITUALFLOW_OUTPUT_PAGE_ID or pass --parent-page-id."
        )

    # Step 1: Create with minimal properties — the SDK ignores extra properties on create.
    db = client.databases.create(
        parent={"type": "page_id", "page_id": parent_id},
        title=[{"type": "text", "text": {"content": "RitualFlow - Generated"}}],
        icon={"type": "emoji", "emoji": "\U0001f4d6"},
        is_inline=True,
        properties={"Name": {"title": {}}},
    )
    collection_id = db["id"]
    print(f"  Collection ID (API): {collection_id}")

    # Step 2: With is_inline=True, Notion creates a block in the parent page whose ID
    # differs from the collection ID. The block ID is what Notion shows in its URL.
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

    # Step 3: Add properties via direct HTTP — bypasses the SDK bug where
    # databases.update() silently ignores the properties argument.
    _notion_patch(NOTION_TOKEN, f"databases/{block_id}", {
        "properties": {
            "Key": {"rich_text": {}},
            "Habit": {
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
    })
    print("  Properties added: Key, Habit, Frequency, Date, Lu")

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
