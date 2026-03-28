# RitualFlow

**AI-powered habit automation for Notion** — automatically generate personalized content (quizzes, digests, discoveries...) based on habits you define in a Notion database.

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue)
![Notion API](https://img.shields.io/badge/Notion-API-black)
![Claude AI](https://img.shields.io/badge/Claude-AI-orange)

## How it works

```
[Notion DB: Habits] --> [RitualFlow CLI] --> [Notion: Generated Pages]
                             |      |
                      Anthropic API  Notion API
                      (generation)   (read/write)
```

1. **Define habits** in a Notion database — each with a name, frequency, prompt, and category
2. **Run RitualFlow** — it reads your habits, generates AI content via Claude, and writes rich Notion pages
3. **Track progress** — a live stats callout on your Notion page shows weekly and all-time generation counts

Generated pages are stored as child pages under each habit, with automatic deduplication and a link feed on your main page.

## Features

- **Smart content generation** — custom prompts or built-in templates (tech quiz, fun facts, place discovery, weekly digest)
- **Multiple frequencies** — daily, weekly, monthly habits with period-aware deduplication
- **Anthropic API + CLI fallback** — uses the API if available, falls back to Claude Code CLI (Pro subscription)
- **Rich Notion pages** — markdown-to-Notion conversion with headings, bullets, toggles, quotes, code, bold/italic
- **Live dashboard** — stats callout updated after each run
- **Web search** — generated content can use live web data via Claude's tools
- **GitHub Actions** — fully automated scheduling out of the box

## Quick Start

### 1. Install

```bash
git clone https://github.com/your-username/ritualflow.git
cd ritualflow
pip install -e .
```

### 2. Configure

Create a `.env` file (see `.env.example`):

```env
# Required
NOTION_TOKEN=your_notion_integration_token
RITUALFLOW_OUTPUT_PAGE_ID=your_notion_page_id

# Optional — falls back to Claude Code CLI if not set
ANTHROPIC_API_KEY=your_anthropic_api_key
```

**Notion setup:**
1. Create a [Notion integration](https://www.notion.so/my-integrations) and copy the token
2. Create a page in Notion for RitualFlow
3. Share the page with your integration
4. Copy the page ID from the URL

### 3. Setup

```bash
ritualflow setup
```

This creates:
- A **RitualFlow - Habits** database (inline, with example habits)
- A **stats callout block** on your main page
- Auto-updates your `.env` with the generated IDs

### 4. Add habits

```bash
ritualflow add "Daily Tech Quiz" --freq daily --prompt "Generate a 5-question quiz on a random programming topic" --category tech
ritualflow add "Paris Discovery" --freq monthly --prompt "Suggest an interesting place to discover in Paris" --category wellness
```

### 5. Run

```bash
# Run all active habits
ritualflow run

# Run only daily habits
ritualflow run --frequency daily

# Preview without writing to Notion
ritualflow run --dry-run

# Force regeneration (skip deduplication)
ritualflow run --force
```

## CLI Reference

| Command | Description |
|---------|-------------|
| `ritualflow setup` | Create the Notion database and stats block |
| `ritualflow run` | Generate content for active habits |
| `ritualflow add NAME` | Add a new habit |
| `ritualflow delete NAME` | Delete a habit (with confirmation) |
| `ritualflow status` | Show habits with current period status |
| `ritualflow history` | Show generated pages per habit |

### Options

```
run:
  --frequency [daily|weekly|monthly]  Run only habits of this frequency
  --dry-run                           Preview without writing
  --force                             Regenerate even if already exists

add:
  --freq [daily|weekly|monthly]       Frequency (required)
  --prompt TEXT                       AI prompt (required)
  --category [tech|wellness|culture|fun]  Category (default: tech)

delete:
  --yes / -y                          Skip confirmation

status:
  --all                               Include inactive habits

history:
  --limit / -n N                      Max pages to show (default: 10)
  --all                               Include inactive habits
```

## Notion Structure

After setup, your Notion page looks like this:

```
RitualFlow Page
├── [Stats Callout]  — "This week: 3 generated | Total: 12 generated"
├── [Link to page]   — most recent generated page
├── [Link to page]   — ...
├── RitualFlow - Habits (database)
│   ├── Daily Tech Quiz        (active, daily)
│   │   ├── Daily Tech Quiz – 28 mars 2026     (child page)
│   │   └── Daily Tech Quiz – 27 mars 2026     (child page)
│   ├── Paris Discovery        (active, monthly)
│   │   └── Paris Discovery – Mars 2026        (child page)
│   └── Weekly Digest          (active, weekly)
│       └── Weekly Digest – Semaine 13, 2026   (child page)
```

### Database schema

| Property  | Type     | Description                    |
|-----------|----------|--------------------------------|
| Name      | Title    | Habit name                     |
| Frequency | Select   | daily / weekly / monthly       |
| Prompt    | Rich Text| AI generation instructions     |
| Category  | Select   | tech / wellness / culture / fun|
| Active    | Checkbox | Enable/disable the habit       |

## Automation with GitHub Actions

The included workflow (`.github/workflows/ritualflow.yml`) runs automatically:

- **Every day at 8:00 AM UTC** — runs daily habits
- **Mondays** — also runs weekly habits
- **1st of the month** — also runs monthly habits
- **Manual trigger** — run on demand with optional frequency filter

### Setup

Add these secrets to your GitHub repository:

| Secret | Description |
|--------|-------------|
| `NOTION_TOKEN` | Notion integration token |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `RITUALFLOW_DB_ID` | Generated database ID |
| `RITUALFLOW_OUTPUT_PAGE_ID` | Main Notion page ID |

## Built-in Templates

RitualFlow includes prompt templates for common habit types:

- **Tech Quiz** — 5-question QCM with hidden answers (toggle blocks)
- **Fun Fact** — surprising fact with context and sources
- **Place Discovery** — Paris location with practical info
- **Weekly Digest** — tech trends, tool of the week, worth reading

Custom prompts override templates — write any prompt you want.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `NOTION_TOKEN` | Yes | Notion integration token |
| `RITUALFLOW_OUTPUT_PAGE_ID` | Yes | Main Notion page ID |
| `ANTHROPIC_API_KEY` | No | Anthropic API key (falls back to Claude CLI) |
| `RITUALFLOW_GENERATED_DB_ID` | Auto | Habits database ID (set by `setup`) |
| `RITUALFLOW_STATS_BLOCK_ID` | Auto | Stats callout block ID (set by `setup`) |
| `ANTHROPIC_MODEL` | No | Model for API calls (default: `claude-haiku-4-5`) |
| `CLAUDE_CLI_MODEL` | No | Model for CLI fallback (default: `haiku`) |

## Tech Stack

- **Python 3.11+**
- **[Anthropic SDK](https://github.com/anthropics/anthropic-sdk-python)** — AI content generation
- **[Notion Client](https://github.com/ramnes/notion-sdk-py)** + **httpx** — Notion API interaction
- **[Click](https://click.palletsprojects.com/)** — CLI framework
- **[python-dotenv](https://github.com/theskumar/python-dotenv)** — Environment management

## License

MIT
