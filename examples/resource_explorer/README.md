# Resource Explorer Example Project

This directory contains a small Python project that demonstrates how you can
programmatically explore the curated lists that power the Awesome Machine Learning
repository and even build simple visualizations from the data.

The consolidated CLI (invoked via `python -m examples.resource_explorer.app`) surfaces a handful of convenient commands:

- Inspect the available categories and the Markdown files that back them.
- List the sections present in a category (for example, the programming language
  breakdown within the main `README.md`).
- Search for resources across any category, optionally filtering by section and
  limiting the number of returned results.

## Quickstart

1. Create and activate a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Run the explorer to list the supported categories:

   ```bash
    python -m examples.resource_explorer.app browse --list-categories
   ```

   The command prints a compact table so you can immediately see which Markdown
   file backs each category:

   ```
   ┌────────────┬──────────────────────┐
   │ Category   │ Source Markdown      │
   ├────────────┼──────────────────────┤
   │ blogs      │ blogs.md             │
   │ books      │ books.md             │
   │ …          │ …                    │
   └────────────┴──────────────────────┘
   ```

3. Inspect the sections available in the main frameworks list:

   ```bash
   python -m examples.resource_explorer.app browse --category frameworks --list-sections
   ```

4. Search for deep learning books:

   ```bash
   python -m examples.resource_explorer.app --category books --search "deep learning" --limit 5
   ```

   Search results are rendered as a numbered table that keeps long section names
   and descriptions aligned for quick scanning:

   ```
   ┌───┬──────────────────────────────────────┬───────────────────────────────────────────────┐
   │ # │ Section                              │ Description                                   │
   ├───┼──────────────────────────────────────┼───────────────────────────────────────────────┤
   │ 1 │ Machine Learning & Deep Learning     │ Deep Learning by Ian Goodfellow, et al.       │
   │ 2 │ Machine Learning & Deep Learning     │ Deep Learning with Python by François Chollet │
   └───┴──────────────────────────────────────┴───────────────────────────────────────────────┘
   ```

The CLI uses substring matching, so you can pass a portion of a section title (for
example, `--section Python`) to focus on a subset of the list. When running the
search command without a `--limit`, all matching resources will be displayed. You can
also redirect the explorer toward an alternative checkout or curated dataset by
supplying `--source-root /path/to/markdown-root`.

## Visualizing Section Coverage

You can generate a horizontal bar chart showing how many entries exist in each
section of a resource category. The command below analyzes the main frameworks
list and writes the visualization to `resource_section_summary.svg` in the
current working directory:

```bash
python -m examples.resource_explorer.app chart --category frameworks
```

Pass `--limit` to restrict the chart to the top N sections or `--output` to
control where the image is saved. The refreshed visualization dedicates a
numbered label column with alternating backgrounds, wraps breadcrumb-style
names across multiple lines, automatically expands row heights so the text
never collides with neighboring bars, overlays dashed tick guides, and keeps
counts right-aligned so the chart stays legible even when sections have long
names or very small totals.

## Building a Browser-Friendly Dashboard

When you want a shareable overview that feels closer to a polished product, run
the dashboard generator subcommand. It produces a single HTML file featuring the section
coverage chart alongside resource cards rendered with generous spacing, a
high-contrast gradient layout, and typographic tweaks that improve legibility on
both light and dark themes:

```bash
python -m examples.resource_explorer.app dashboard --category frameworks --output dashboard.html
```

Open the generated `dashboard.html` in your browser to explore the curated data
without touching the command line. A hero strip at the top surfaces real-time
metrics—resource totals, populated sections, and how many cards the filters
will show—so stakeholders immediately understand the scope of the data pull.
The page adapts to light and dark themes, highlights the applied filters directly
in the header subtitle, and presents chart/table content with subtle borders so
long labels stay readable. The command also emits a sibling SVG chart file
(`dashboard_chart.svg`) that mirrors the embedded visualization so you can reuse it in
slide decks. Use `--top-sections`, `--max-resources`, `--section`, `--search`, and
`--source-root` to fine-tune the contents to your audience. Set `--max-resources 0`
if you want to showcase every matching resource instead of the curated default grid.

### Where to Find the Front-End Output

Every run of the dashboard command writes the rendered interface to the path you
pass via `--output`. For a ready-to-open example, inspect
`docs/resource_explorer_dashboard_sample.html` in the repository root—the file is
checked in so you can preview the MVP without generating it yourself. The
command also refreshes `docs/resource_explorer_dashboard_sample_chart.svg` so the
embedded visualization stays in sync with the HTML.

## Running Tests

A small test suite is included to ensure that the parser and query helpers continue to
work as the curated lists evolve. Execute the tests from the repository root:

```bash
pytest examples/resource_explorer/tests
```

