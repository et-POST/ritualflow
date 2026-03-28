"""Prompt templates for different habit types."""

TEMPLATES: dict[str, str] = {
    "tech_quiz": """Generate a tech quiz in Notion-compatible Markdown.

Topic: Pick a random interesting tech topic (programming languages, frameworks, algorithms, networking, databases, cloud, security, etc.). Vary the topic each time.

Format the output EXACTLY like this (Markdown):

# 🧠 Tech Quiz — [Topic Name]

**Date:** {date}
**Difficulty:** [Beginner/Intermediate/Advanced]

---

## Question 1
[Question text]

<details>
<summary>Show Answer</summary>

**Answer:** [Correct answer]
**Explanation:** [Brief explanation]

</details>

## Question 2
[Question text]

A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]

<details>
<summary>Show Answer</summary>

**Answer:** [Correct letter and text]
**Explanation:** [Brief explanation]

</details>

Generate exactly 5 questions. Mix open-ended and multiple-choice. Make them educational and engaging.
""",
    "fun_fact": """Generate an interesting and surprising fun fact in Notion-compatible Markdown.

Pick a random domain: science, history, nature, space, psychology, geography, technology, art, music, food, animals, etc. Be creative and surprising.

Format the output EXACTLY like this:

# 💡 Fun Fact — {date}

## Did you know?

[State the fun fact in 1-2 compelling sentences]

---

### Why is this interesting?

[2-3 sentences explaining the context and why it matters]

### Want to learn more?

[1-2 sentences with a pointer to where to learn more about this topic]

---

*Category: [domain]*
""",
    "place_discovery": """Generate a place to discover in Paris in Notion-compatible Markdown.

Pick a real, interesting place in Paris. It can be well-known or a hidden gem: a museum, a park, a street, a neighborhood, a restaurant, a cafe, a viewpoint, a market, an architectural landmark, etc. Vary between popular and lesser-known spots.

Format the output EXACTLY like this:

# 📍 Discover — [Place Name]

**Month:** {date}
**Neighborhood:** [Arrondissement / Area name]
**Type:** [Museum / Park / Cafe / Street / Market / etc.]

---

## About this place

[3-4 sentences describing the place, its history, and what makes it special]

## Why visit?

[2-3 bullet points on what makes it worth visiting]

## Practical info

- **Address:** [Full address]
- **Best time to visit:** [Time of day / season]
- **Budget:** [Free / € / €€ / €€€]
- **Getting there:** [Nearest metro station]

---

*Tip: [One insider tip for getting the most out of the visit]*
""",
    "weekly_digest": """Generate a weekly tech digest summary in Notion-compatible Markdown.

Cover the most interesting trends, releases, and news in technology this week. Include topics like: new framework releases, AI developments, developer tools, industry news, open-source highlights.

Format the output EXACTLY like this:

# 📰 Weekly Tech Digest

**Week:** {date}

---

## 🔥 Top Stories

### 1. [Story title]
[2-3 sentence summary]

### 2. [Story title]
[2-3 sentence summary]

### 3. [Story title]
[2-3 sentence summary]

---

## 🛠️ Tool of the Week

**[Tool name]** — [One-line description]
[2-3 sentences on why it's useful and who it's for]

---

## 💭 Thought of the Week

> [An insightful quote or observation about technology]

*[Attribution]*

---

## 📚 Worth Reading

- [Article/resource title and brief description]
- [Article/resource title and brief description]
""",
}


def get_template(category: str) -> str | None:
    """Return the prompt template for a given category, or None for custom habits."""
    mapping = {
        "tech": "tech_quiz",
        "culture": "fun_fact",
        "wellness": "place_discovery",
        "fun": "fun_fact",
    }
    key = mapping.get(category.lower())
    return TEMPLATES.get(key) if key else None
