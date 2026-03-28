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

    env_path = Path(__file__).resolve().parent.parent / ".env"
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

    # Auto-update .env with the new IDs
    _update_env("RITUALFLOW_GENERATED_DB_ID", db_id)
    _update_env("RITUALFLOW_STATS_BLOCK_ID", block_id)

    click.echo("\n" + "=" * 60)
    click.echo("Setup complete! .env updated automatically:")
    click.echo("=" * 60)
    click.echo(f"RITUALFLOW_GENERATED_DB_ID={db_id}")
    click.echo(f"RITUALFLOW_STATS_BLOCK_ID={block_id}")
    click.echo("=" * 60)



@main.command()
def status():
    """Show the current state of all habits."""
    validate_config()

    from ritualflow.habits import get_active_habits
    from ritualflow.writer import page_exists
    from notion_client import Client
    from ritualflow.config import NOTION_TOKEN, RITUALFLOW_GENERATED_DB_ID

    habits = get_active_habits()

    if not habits:
        click.echo("No habits found. Run 'ritualflow setup' first.")
        return

    # Try to get read counts from Generated DB
    read_counts: dict[str, int] = {}
    total_counts: dict[str, int] = {}
    if RITUALFLOW_GENERATED_DB_ID:
        try:
            client = Client(auth=NOTION_TOKEN)
            results = client.databases.query(
                database_id=RITUALFLOW_GENERATED_DB_ID,
            )
            for page in results.get("results", []):
                props = page.get("properties", {})
                habit_sel = props.get("Habit", {}).get("select")
                habit_name = habit_sel["name"] if habit_sel else ""
                is_read = props.get("Lu", {}).get("checkbox", False)
                total_counts[habit_name] = total_counts.get(habit_name, 0) + 1
                if is_read:
                    read_counts[habit_name] = read_counts.get(habit_name, 0) + 1
        except Exception:
            pass

    click.echo(f"\n{'Name':<25} {'Freq':<10} {'Now?':<10} {'Lu / Total'}")
    click.echo("-" * 65)

    for h in habits:
        done = "YES" if page_exists(h) is not None else "pending"
        total = total_counts.get(h.name, 0)
        read  = read_counts.get(h.name, 0)
        lu_str = f"{read}/{total}" if total > 0 else "--"
        click.echo(f"{h.name:<25} {h.frequency:<10} {done:<10} {lu_str}")

    click.echo("")


if __name__ == "__main__":
    main()
