"""Write generated content as Notion pages in the Generated database."""

import re
from datetime import date

from notion_client import Client

from ritualflow.config import NOTION_TOKEN, RITUALFLOW_OUTPUT_PAGE_ID, RITUALFLOW_STATS_BLOCK_ID
from ritualflow.habits import Habit
from ritualflow.utils import notion_list_children

# Notion API hard limit for children blocks per request
NOTION_BLOCK_LIMIT = 100

MONTHS_FR = [
    "", "janvier", "f\u00e9vrier", "mars", "avril", "mai", "juin",
    "juillet", "ao\u00fbt", "septembre", "octobre", "novembre", "d\u00e9cembre",
]


def _get_notion_client() -> Client:
    return Client(auth=NOTION_TOKEN)


def _make_display_title(habit: Habit, ref_date: date | None = None) -> str:
    """Return a human-readable page title based on frequency and date."""
    d = ref_date or date.today()
    if habit.frequency == "daily":
        return f"{habit.name} \u2013 {d.day} {MONTHS_FR[d.month]} {d.year}"
    elif habit.frequency == "weekly":
        iso = d.isocalendar()
        return f"{habit.name} \u2013 Semaine {iso.week:02d}, {iso.year}"
    elif habit.frequency == "monthly":
        return f"{habit.name} \u2013 {MONTHS_FR[d.month].capitalize()} {d.year}"
    return f"{habit.name} \u2013 {d.isoformat()}"


def page_exists(habit: Habit, ref_date: date | None = None) -> str | None:
    """Check if a child page with this title already exists under the habit.

    Returns the page URL or None.
    """
    display_title = _make_display_title(habit, ref_date)

    try:
        children = notion_list_children(NOTION_TOKEN, habit.id)
        for block in children:
            if block.get("type") == "child_page":
                if block["child_page"]["title"] == display_title:
                    page_id = block["id"].replace("-", "")
                    return f"https://www.notion.so/{page_id}"
    except Exception as e:
        print(f"  [warn] Could not check existing pages for '{habit.name}': {e}")

    return None


def create_page(habit: Habit, content: str, ref_date: date | None = None) -> str:
    """Create a child page under the habit row. Returns the page URL."""
    client = _get_notion_client()
    display_title = _make_display_title(habit, ref_date)

    # Build all blocks from markdown content
    all_blocks = _markdown_to_blocks(content)

    # Create the page as a child of the habit row
    first_batch = all_blocks[:NOTION_BLOCK_LIMIT]
    page = client.pages.create(
        parent={"page_id": habit.id},
        icon={"type": "emoji", "emoji": _category_emoji(habit.category)},
        properties={
            "title": {"title": [{"text": {"content": display_title}}]},
        },
        children=first_batch,
    )
    page_id = page["id"]

    # Append remaining blocks in batches (Notion limit: 100 per request)
    remaining = all_blocks[NOTION_BLOCK_LIMIT:]
    while remaining:
        batch = remaining[:NOTION_BLOCK_LIMIT]
        client.blocks.children.append(block_id=page_id, children=batch)
        remaining = remaining[NOTION_BLOCK_LIMIT:]

    # Add a link to the generated page on the main RitualFlow page
    _link_on_main_page(client, page_id)

    return page["url"]


def _link_on_main_page(client: Client, page_id: str):
    """Insert a link_to_page block right after the stats callout on the main page.

    Newest links appear at the top of the list.
    """
    if not RITUALFLOW_OUTPUT_PAGE_ID:
        return
    try:
        kwargs = {
            "block_id": RITUALFLOW_OUTPUT_PAGE_ID,
            "children": [
                {
                    "object": "block",
                    "type": "link_to_page",
                    "link_to_page": {
                        "type": "page_id",
                        "page_id": page_id,
                    },
                }
            ],
        }
        # Insert right after the stats callout so newest links are on top
        if RITUALFLOW_STATS_BLOCK_ID:
            kwargs["after"] = RITUALFLOW_STATS_BLOCK_ID
        client.blocks.children.append(**kwargs)
    except Exception as e:
        print(f"  [warn] Could not add link to main page: {e}")


def _category_emoji(category: str) -> str:
    return {
        "tech":    "\U0001f9e0",  # 🧠
        "culture": "\U0001f4a1",  # 💡
        "wellness":"\U0001f4cd",  # 📍
        "fun":     "\U0001f389",  # 🎉
    }.get(category.lower(), "\u2728")  # ✨


def _markdown_to_blocks(markdown: str) -> list[dict]:
    """Convert markdown text to Notion API block objects."""
    lines = markdown.split("\n")
    blocks = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # Horizontal rule
        if stripped in ("---", "***", "___"):
            blocks.append({"object": "block", "type": "divider", "divider": {}})
            i += 1
            continue

        # Details/toggle block
        if stripped.startswith("<details>"):
            toggle_title, toggle_children, i = _parse_details(lines, i)
            blocks.append(
                {
                    "object": "block",
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"type": "text", "text": {"content": toggle_title}}],
                        "children": toggle_children,
                    },
                }
            )
            continue

        if stripped in ("</details>", "</summary>"):
            i += 1
            continue

        # Headings
        if stripped.startswith("### "):
            blocks.append(_heading_block(stripped[4:], 3))
            i += 1
            continue
        if stripped.startswith("## "):
            blocks.append(_heading_block(stripped[3:], 2))
            i += 1
            continue
        if stripped.startswith("# "):
            blocks.append(_heading_block(stripped[2:], 1))
            i += 1
            continue

        # Blockquote
        if stripped.startswith("> "):
            blocks.append({
                "object": "block",
                "type": "quote",
                "quote": {"rich_text": _parse_rich_text(stripped[2:])},
            })
            i += 1
            continue

        # Bullet point
        if stripped.startswith("- "):
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": _parse_rich_text(stripped[2:])},
            })
            i += 1
            continue

        # Numbered list
        num_match = re.match(r"^(\d+)[.)]\s+(.*)", stripped)
        if num_match:
            text = num_match.group(2)
            blocks.append({
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": _parse_rich_text(text)},
            })
            i += 1
            continue

        # Paragraph
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": _parse_rich_text(stripped)},
        })
        i += 1

    return blocks


def _parse_details(lines: list[str], start: int) -> tuple[str, list[dict], int]:
    """Parse <details><summary>...</summary>...</details> into a toggle block."""
    i = start + 1
    title = "Show Answer"
    children = []

    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith("<summary>"):
            title = stripped.replace("<summary>", "").replace("</summary>", "").strip()
            i += 1
            break
        i += 1

    while i < len(lines):
        stripped = lines[i].strip()
        if stripped == "</details>":
            i += 1
            break
        if stripped and stripped not in ("</summary>",):
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": _parse_rich_text(stripped)},
            })
        i += 1

    return title, children, i


def _heading_block(text: str, level: int) -> dict:
    key = f"heading_{level}"
    return {
        "object": "block",
        "type": key,
        key: {"rich_text": _parse_rich_text(text)},
    }


def _parse_rich_text(text: str) -> list[dict]:
    """Parse inline markdown (**bold**, *italic*, `code`) into Notion rich text."""
    segments = []
    pattern = re.compile(r"(\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)")
    last_end = 0

    for match in pattern.finditer(text):
        if match.start() > last_end:
            plain = text[last_end:match.start()]
            if plain:
                segments.append({"type": "text", "text": {"content": plain}})

        if match.group(2):  # **bold**
            segments.append({
                "type": "text",
                "text": {"content": match.group(2)},
                "annotations": {"bold": True},
            })
        elif match.group(3):  # *italic*
            segments.append({
                "type": "text",
                "text": {"content": match.group(3)},
                "annotations": {"italic": True},
            })
        elif match.group(4):  # `code`
            segments.append({
                "type": "text",
                "text": {"content": match.group(4)},
                "annotations": {"code": True},
            })

        last_end = match.end()

    if last_end < len(text):
        remaining = text[last_end:]
        if remaining:
            segments.append({"type": "text", "text": {"content": remaining}})

    if not segments:
        segments.append({"type": "text", "text": {"content": text}})

    return segments
