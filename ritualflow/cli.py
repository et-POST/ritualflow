"""RitualFlow CLI — AI-powered habit automation for Notion."""

import sys
import io
import click

from ritualflow.config import validate_config

# Fix Windows console encoding for emoji support
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def _update_env(key: str, value: str):
    """Update or add a key=value in the .env file."""
    from pathlib import Path
    from dotenv import find_dotenv

    # Use dotenv's search (walks up from cwd), fall back to project root
    found = find_dotenv(usecwd=True)
    env_path = Path(found) if found else Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        env_path.write_text(f"{key}={value}\n", encoding="utf-8")
        return

    lines = env_path.read_text(encoding="utf-8").splitlines()
    found = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            found = True
            break
    if not found:
        lines.append(f"{key}={value}")

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


@click.group()
def main():
    """RitualFlow - AI-powered habit automation for Notion."""
    pass


@main.command()
@click.option("--frequency", type=click.Choice(["daily", "weekly", "monthly"]), help="Run only habits of this frequency.")
@click.option("--dry-run", is_flag=True, help="Show what would be generated without writing to Notion.")
@click.option("--force", is_flag=True, help="Regenerate even if a page already exists for this period.")
def run(frequency: str | None, dry_run: bool, force: bool):
    """Execute due habits and generate content."""
    validate_config()

    from ritualflow.habits import get_active_habits
    from ritualflow.generator import generate_content
    from ritualflow.writer import page_exists, create_page
    from ritualflow.dashboard import update_stats

    habits = get_active_habits(frequency)

    if not habits:
        click.echo("No active habits found" + (f" for frequency '{frequency}'" if frequency else "") + ".")
        return

    click.echo(f"Found {len(habits)} active habit(s).\n")

    any_created = False
    for habit in habits:
        click.echo(f"[{habit.frequency}] {habit.name}")

        existing_url = page_exists(habit)
        if existing_url and not force:
            click.echo(f"  >> Already generated: {existing_url}\n")
            continue

        click.echo(f"  [prompt] {habit.prompt!r}")
        click.echo("  -> Generating content...")
        content = generate_content(habit)

        if dry_run:
            click.echo(f"  [DRY RUN] Would create page with {len(content)} chars")
            click.echo(f"  Preview:\n{content[:300]}...\n")
            continue

        click.echo("  -> Creating Notion page...")
        url = create_page(habit, content)
        click.echo(f"  OK: {url}\n")
        any_created = True

    if any_created and not dry_run:
        update_stats()

    click.echo("All habits processed.")


@main.command()
@click.option("--parent-page-id", help="Notion page ID to create the databases under.")
def setup(parent_page_id: str | None):
    """Create the RitualFlow databases and stats block in Notion."""
    validate_config()

    from ritualflow.config import RITUALFLOW_OUTPUT_PAGE_ID
    from ritualflow.setup_notion import setup_database, setup_stats_block

    pid = parent_page_id or RITUALFLOW_OUTPUT_PAGE_ID
    if not pid:
        click.echo("Error: provide --parent-page-id or set RITUALFLOW_OUTPUT_PAGE_ID in .env")
        return

    click.echo("Creating Generated database...")
    db_id = setup_database(pid)

    click.echo("Creating stats callout block on main page...")
    block_id = setup_stats_block(pid)

    # Auto-update .env with the new IDs and reload in-process config
    _update_env("RITUALFLOW_GENERATED_DB_ID", db_id)
    _update_env("RITUALFLOW_STATS_BLOCK_ID", block_id)

    from ritualflow.config import reload_config
    reload_config()

    click.echo("\n" + "=" * 60)
    click.echo("Setup complete! .env updated automatically:")
    click.echo("=" * 60)
    click.echo(f"RITUALFLOW_GENERATED_DB_ID={db_id}")
    click.echo(f"RITUALFLOW_STATS_BLOCK_ID={block_id}")
    click.echo("=" * 60)



@main.command()
@click.argument("name")
@click.option("--freq", type=click.Choice(["daily", "weekly", "monthly"]), required=True, help="Frequency of the habit.")
@click.option("--prompt", required=True, help="The AI prompt used to generate content.")
@click.option("--category", type=click.Choice(["tech", "wellness", "culture", "fun"]), default="tech", help="Category of the habit.")
def add(name: str, freq: str, prompt: str, category: str):
    """Add a new habit to the database."""
    validate_config()

    from ritualflow.setup_notion import add_habit

    try:
        page_id = add_habit(name=name, frequency=freq, prompt=prompt, category=category)
        click.echo(f"Habit '{name}' added ({freq}, {category}).")
    except Exception as e:
        raise click.ClickException(str(e))


@main.command()
@click.argument("name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt.")
def delete(name: str, yes: bool):
    """Delete a habit by name."""
    validate_config()

    from ritualflow.setup_notion import delete_habit

    if not yes:
        click.confirm(f"Delete habit '{name}'?", abort=True)

    try:
        found = delete_habit(name)
        if found:
            click.echo(f"Habit '{name}' deleted.")
        else:
            click.echo(f"Habit '{name}' not found.")
    except Exception as e:
        raise click.ClickException(str(e))


@main.command()
@click.argument("name", required=False)
@click.option("--limit", "-n", default=10, help="Max pages to show per habit.")
@click.option("--all", "show_all", is_flag=True, help="Include inactive habits.")
def history(name: str | None, limit: int, show_all: bool):
    """Show generated pages for a habit (or all habits)."""
    validate_config()

    from ritualflow.habits import get_active_habits
    from ritualflow.utils import notion_list_children
    from ritualflow.config import NOTION_TOKEN

    habits = get_active_habits(include_inactive=show_all)
    if not habits:
        click.echo("No habits found. Run 'ritualflow setup' first.")
        return

    if name:
        habits = [h for h in habits if h.name.lower() == name.lower()]
        if not habits:
            click.echo(f"Habit '{name}' not found.")
            return

    for habit in habits:
        click.echo(f"\n[{habit.frequency}] {habit.name}")
        click.echo("-" * 50)

        try:
            children = notion_list_children(NOTION_TOKEN, habit.id)
            pages = [
                b for b in children
                if b.get("type") == "child_page"
            ]
        except Exception:
            click.echo("  (could not list pages)")
            continue

        if not pages:
            click.echo("  (no pages yet)")
            continue

        # Sort by created_time descending (most recent first)
        pages.sort(key=lambda b: b.get("created_time", ""), reverse=True)

        for page in pages[:limit]:
            title = page.get("child_page", {}).get("title", "Untitled")
            created = page.get("created_time", "")[:10]
            page_id = page["id"].replace("-", "")
            url = f"https://www.notion.so/{page_id}"
            click.echo(f"  {created}  {title}")
            click.echo(f"           {url}")

        remaining = len(pages) - limit
        if remaining > 0:
            click.echo(f"  ... and {remaining} more (use -n {len(pages)} to see all)")

    click.echo("")


@main.command()
@click.option("--all", "show_all", is_flag=True, help="Include inactive habits.")
def status(show_all: bool):
    """Show the current state of all habits."""
    validate_config()

    from ritualflow.habits import get_active_habits
    from ritualflow.writer import page_exists
    from ritualflow.utils import notion_list_children
    from ritualflow.config import NOTION_TOKEN

    habits = get_active_habits(include_inactive=show_all)

    if not habits:
        click.echo("No habits found. Run 'ritualflow setup' first.")
        return

    click.echo(f"\n{'Name':<25} {'Freq':<10} {'Active':<9} {'Now?':<10} {'Pages'}")
    click.echo("-" * 68)

    for h in habits:
        active = "✓" if h.active else "✗"
        done = "YES" if page_exists(h) is not None else "pending"
        # Count child pages under the habit
        total = 0
        try:
            children = notion_list_children(NOTION_TOKEN, h.id)
            total = sum(1 for b in children if b.get("type") == "child_page")
        except Exception:
            pass
        click.echo(f"{h.name:<25} {h.frequency:<10} {active:<9} {done:<10} {total}")

    click.echo("")


if __name__ == "__main__":
    main()
