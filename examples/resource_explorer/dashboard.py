"""Generate a polished HTML dashboard for the resource explorer.

This module turns the same markdown-backed data plumbing used by the
command-line tools into a clean, single-page interface that readers can open
in a browser.  The goal is to provide an at-a-glance overview of a category
without introducing heavyweight dependencies or bespoke build steps.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import html
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from . import resource_loader, visualize

LOGGER = logging.getLogger(__name__)

DEFAULT_OUTPUT = Path("resource_dashboard.html")


def _escape(value: object) -> str:
    """HTML-escape ``value`` so it is safe to embed in the dashboard."""

    return html.escape(str(value), quote=True)


@dataclass(frozen=True)
class DashboardMetrics:
    """Aggregate counts showcased at the top of the dashboard."""

    total_sections: int
    total_resources: int
    featured_resources: int

    @property
    def average_per_section(self) -> float:
        if not self.total_sections:
            return 0.0
        return self.total_resources / self.total_sections


@dataclass(frozen=True)
class DashboardArtifact:
    """Describes the files produced by :func:`write_dashboard`."""

    html_path: Path
    chart_path: Path


def _format_section_table(summary: Sequence[tuple[str, int]]) -> str:
    """Return HTML for the section summary table."""

    if not summary:
        return "<p class=\"empty\">No populated sections found.</p>"

    rows = [
        "<tr><td>{name}</td><td>{count}</td></tr>".format(
            name=_escape(resource_loader.display_section_name(name)),
            count=_escape(count),
        )
        for name, count in summary
    ]
    table = [
        "<table class=\"section-table\">",
        "  <thead><tr><th>Section</th><th>Resources</th></tr></thead>",
        "  <tbody>",
        *[f"    {row}" for row in rows],
        "  </tbody>",
        "</table>",
    ]
    return "\n".join(table)


def _format_metric_tiles(metrics: DashboardMetrics) -> str:
    """Return HTML tiles summarizing dashboard metrics."""

    if metrics.total_resources == 0:
        return "<p class=\"empty\">No resources were discovered for this category.</p>"

    metric_cards = [
        (
            "Resources tracked",
            f"{metrics.total_resources:,}",
            "Entries parsed straight from the curated markdown files.",
        ),
        (
            "Populated sections",
            f"{metrics.total_sections:,}",
            "Unique sections containing at least one resource.",
        ),
        (
            "Resources shown",
            f"{metrics.featured_resources:,}",
            "Cards rendered below that respect your current filters.",
        ),
        (
            "Average per section",
            f"{metrics.average_per_section:,.1f}",
            "Quick heuristic for spotting coverage gaps.",
        ),
    ]

    tiles = [
        "<div class=\"metric-grid\">",
        *[
            "  <article class=\"metric-card\">"
            + f"<h3>{_escape(title)}</h3>"
            + f"<p class=\"metric-value\">{_escape(value)}</p>"
            + f"<p>{_escape(subtitle)}</p>"
            + "</article>"
            for title, value, subtitle in metric_cards
        ],
        "</div>",
    ]
    return "\n".join(tiles)


def _format_resource_cards(resources: Iterable[resource_loader.ResourceHit]) -> str:
    """Return HTML cards summarizing individual resources."""

    cards = []
    for hit in resources:
        cards.append(
            """
            <article class=\"resource-card\">
              <h3><a href={url}>{title}</a></h3>
              <p>{summary}</p>
            </article>
            """.strip().format(
                url=_escape(hit.resource.url),
                title=_escape(hit.resource.title),
                summary=_escape(
                    hit.resource.summary or "Visit the resource to learn more."
                ),
            )
        )

    if not cards:
        return "<p class=\"empty\">No matching resources found for this view.</p>"

    return "\n".join(cards)


def render_dashboard_html(
    category: str,
    *,
    top_sections: int | None = 8,
    max_resources: int | None = 24,
    section_filter: Sequence[str] | None = None,
    search: str | None = None,
    source_root: Path | None = None,
    svg_chart: str | None = None,
) -> str:
    """Return a fully rendered HTML dashboard for ``category``.

    Parameters
    ----------
    category:
        Category identifier handled by :mod:`resource_loader`.
    top_sections:
        Number of sections to display in the summary table ordered by resource
        count.  ``None`` means include every populated section.
    max_resources:
        Maximum number of resource cards to render in the detail grid. ``None``
        means include every matching resource.
    section_filter / search:
        Optional filters mirroring the CLI flags from :func:`find_resources`.
    """

    collection = resource_loader.load_collection(category, source_root=source_root)
    summary_map = resource_loader.summarize_sections(collection)
    ordered_summary = sorted(summary_map.items(), key=lambda item: item[1], reverse=True)

    if top_sections is not None:
        ordered_summary = ordered_summary[:top_sections]

    resource_limit: int | None
    if max_resources is None or max_resources <= 0:
        resource_limit = None
    else:
        resource_limit = max_resources

    hits = resource_loader.find_resources(
        category,
        section_filter=section_filter,
        query=search,
        limit=resource_limit,
        source_root=source_root,
    )

    metrics = DashboardMetrics(
        total_sections=collection.total_sections,
        total_resources=collection.total_resources,
        featured_resources=len(hits),
    )

    if svg_chart is None:
        svg_chart = visualize.render_svg_chart(
            category,
            limit=top_sections,
            source_root=source_root,
        )

    generated_at = _dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    subtitle_parts = [f"Category: {_escape(category.title())}"]
    if search:
        subtitle_parts.append(f"Keyword: {_escape(search)}")
    if section_filter:
        subtitle_parts.append(
            "Sections: "
            + ", ".join(_escape(part) for part in section_filter)
        )
    subtitle = " • ".join(subtitle_parts)

    html_parts = [
        "<!DOCTYPE html>",
        "<html lang=\"en\">",
        "<head>",
        "  <meta charset=\"utf-8\" />",
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />",
        f"  <title>{_escape(category.title())} Resources Dashboard</title>",
        "  <style>",
        "    :root {",
        "      color-scheme: light dark;",
        "      font-family: 'Inter', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;",
        "    }",
        "    body {",
        "      margin: 0;",
        "      background: #f8fafc;",
        "      color: #0f172a;",
        "      line-height: 1.6;",
        "    }",
        "    header {",
        "      background: linear-gradient(135deg, #1f78ff, #4f46e5);",
        "      color: white;",
        "      padding: 48px 16px 56px;",
        "      text-align: center;",
        "      box-shadow: 0 16px 40px rgba(30, 64, 175, 0.35);",
        "    }",
        "    header h1 { font-size: 2.6rem; margin: 0 0 12px; letter-spacing: -0.02em; }",
        "    header p { margin: 8px auto 0; font-size: 1.05rem; max-width: 720px; opacity: 0.92; }",
        "    a { color: #1d4ed8; text-decoration: none; }",
        "    a:hover, a:focus { text-decoration: underline; }",
        "    a:focus-visible { outline: 3px solid rgba(59, 130, 246, 0.5); outline-offset: 2px; border-radius: 4px; }",
        "    .overview {",
        "      max-width: 1100px;",
        "      margin: -64px auto 32px;",
        "      padding: 0 24px;",
        "    }",
        "    .metric-grid {",
        "      display: grid;",
        "      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));",
        "      gap: 24px;",
        "    }",
        "    .metric-card {",
        "      background: rgba(255, 255, 255, 0.96);",
        "      border-radius: 20px;",
        "      box-shadow: 0 24px 60px -20px rgba(15, 23, 42, 0.35);",
        "      padding: 26px;",
        "      border: 1px solid rgba(148, 163, 184, 0.2);",
        "    }",
        "    .metric-card h3 {",
        "      margin: 0;",
        "      font-size: 0.85rem;",
        "      text-transform: uppercase;",
        "      letter-spacing: 0.08em;",
        "      color: #64748b;",
        "    }",
        "    .metric-card .metric-value {",
        "      font-size: 2.1rem;",
        "      font-weight: 650;",
        "      color: #1e40af;",
        "      letter-spacing: -0.01em;",
        "      margin: 14px 0 10px;",
        "    }",
        "    .metric-card p { margin: 0; line-height: 1.55; color: #475569; }",
        "    main {",
        "      max-width: 1100px;",
        "      margin: 0 auto 56px;",
        "      padding: 0 24px;",
        "    }",
        "    .card {",
        "      background: rgba(255, 255, 255, 0.98);",
        "      border-radius: 24px;",
        "      box-shadow: 0 28px 70px -30px rgba(30, 41, 59, 0.55);",
        "      padding: 34px;",
        "      margin-bottom: 32px;",
        "      border: 1px solid rgba(148, 163, 184, 0.25);",
        "    }",
        "    .card h2 { margin-top: 0; font-size: 1.5rem; letter-spacing: -0.01em; color: #0f172a; }",
        "    .card p.meta { margin-top: -6px; color: #475569; font-size: 0.98rem; }",
        "    .chart { width: 100%; overflow-x: auto; padding: 18px 0; }",
        "    .chart svg { width: 100%; height: auto; border-radius: 14px; border: 1px solid rgba(148, 163, 184, 0.25); background: #ffffff; }",
        "    .section-table { width: 100%; border-collapse: collapse; }",
        "    .section-table th {",
        "      text-transform: uppercase;",
        "      letter-spacing: 0.07em;",
        "      font-size: 0.78rem;",
        "      color: #475569;",
        "      text-align: left;",
        "      padding: 12px 16px;",
        "      background: #eef2ff;",
        "    }",
        "    .section-table td {",
        "      padding: 14px 16px;",
        "      font-size: 0.97rem;",
        "      border-top: 1px solid rgba(148, 163, 184, 0.3);",
        "    }",
        "    .section-table tr:nth-child(even) td { background: rgba(226, 232, 240, 0.35); }",
        "    .resource-grid {",
        "      display: grid;",
        "      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));",
        "      gap: 24px;",
        "      margin-top: 28px;",
        "    }",
        "    .resource-card {",
        "      background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(238,242,255,0.9) 100%);",
        "      border-radius: 18px;",
        "      padding: 22px;",
        "      box-shadow: 0 18px 40px -18px rgba(30, 41, 59, 0.35);",
        "      display: flex;",
        "      flex-direction: column;",
        "      gap: 14px;",
        "      border: 1px solid rgba(148, 163, 184, 0.25);",
        "    }",
        "    .resource-card h3 {",
        "      margin: 0;",
        "      font-size: 1.08rem;",
        "      color: #1d4ed8;",
        "    }",
        "    .resource-card p {",
        "      margin: 0;",
        "      line-height: 1.55;",
        "      color: #334155;",
        "    }",
        "    footer {",
        "      max-width: 1100px;",
        "      margin: 0 auto 48px;",
        "      padding: 0 24px;",
        "      color: #475569;",
        "      font-size: 0.88rem;",
        "      text-align: center;",
        "    }",
        "    .empty {",
        "      color: #64748b;",
        "      font-style: italic;",
        "    }",
        "    @media (prefers-color-scheme: dark) {",
        "      :root { background-color: #0b1220; color: #e2e8f0; }",
        "      body { background: #0b1220; color: #e2e8f0; }",
        "      header { box-shadow: none; }",
        "      .metric-card { background: rgba(15, 23, 42, 0.9); box-shadow: 0 24px 60px -30px rgba(15, 23, 42, 0.95); border-color: rgba(148, 163, 184, 0.12); }",
        "      .card { background: rgba(15, 23, 42, 0.92); box-shadow: 0 24px 60px -30px rgba(15, 23, 42, 0.95); border-color: rgba(148, 163, 184, 0.12); }",
        "      .section-table th { background: rgba(30, 64, 175, 0.4); color: #cbd5f5; }",
        "      .section-table td { border-color: rgba(148, 163, 184, 0.25); }",
        "      .section-table tr:nth-child(even) td { background: rgba(30, 41, 59, 0.55); }",
        "      .resource-card { background: linear-gradient(180deg, rgba(30,41,59,0.9) 0%, rgba(17,24,39,0.85) 100%); border-color: rgba(148, 163, 184, 0.18); }",
        "      .resource-card h3 { color: #93c5fd; }",
        "      .resource-card p { color: #cbd5f5; }",
        "      .chart svg { background: rgba(15, 23, 42, 0.9); border-color: rgba(148, 163, 184, 0.2); }",
        "      footer { color: #94a3b8; }",
        "    }",
        "  </style>",
        "</head>",
        "<body>",
        "  <header>",
        f"    <h1>{_escape(category.title())} Resource Navigator</h1>",
        f"    <p>{subtitle}</p>",
        "  </header>",
        "  <section class=\"overview\">",
        f"    {_format_metric_tiles(metrics)}",
        "  </section>",
        "  <main>",
        "    <section class=\"card\">",
        "      <h2>Section coverage</h2>",
        "      <p class=\"meta\">Each bar represents a populated section within the curated markdown files.</p>",
        "      <div class=\"chart\">",
        f"        {svg_chart}",
        "      </div>",
        f"      {_format_section_table(ordered_summary)}",
        "    </section>",
        "    <section class=\"card\">",
        "      <h2>Featured resources</h2>",
        "      <p class=\"meta\">Sample entries pulled directly from the markdown content so you can inspect the tone and formatting before diving deeper.</p>",
        "      <div class=\"resource-grid\">",
        f"        {_format_resource_cards(hits)}",
        "      </div>",
        "    </section>",
        "  </main>",
        "  <footer>",
        f"    Generated on {generated_at} using the Awesome Machine Learning resource explorer.",
        "  </footer>",
        "</body>",
        "</html>",
    ]

    return "\n".join(html_parts)


def write_dashboard(
    output_path: Path,
    *,
    category: str = "frameworks",
    top_sections: int | None = 8,
    max_resources: int | None = 24,
    section_filter: Sequence[str] | None = None,
    search: str | None = None,
    source_root: Path | None = None,
) -> DashboardArtifact:
    """Render the dashboard and write it to ``output_path``."""

    LOGGER.info("Rendering dashboard for category '%s'", category)
    svg_chart = visualize.render_svg_chart(
        category,
        limit=top_sections,
        source_root=source_root,
    )
    html_output = render_dashboard_html(
        category,
        top_sections=top_sections,
        max_resources=max_resources,
        section_filter=section_filter,
        search=search,
        source_root=source_root,
        svg_chart=svg_chart,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_output, encoding="utf-8")
    LOGGER.info("Wrote dashboard HTML to %s", output_path.resolve())

    chart_path = output_path.with_name(f"{output_path.stem}_chart.svg")
    chart_path.write_text(svg_chart, encoding="utf-8")
    LOGGER.info("Wrote dashboard chart to %s", chart_path.resolve())

    return DashboardArtifact(html_path=output_path, chart_path=chart_path)


def add_cli_arguments(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Attach dashboard generation arguments to ``parser``."""

    parser.add_argument(
        "--category",
        choices=sorted(resource_loader.available_categories()),
        default="frameworks",
        help="Resource category to showcase (default: frameworks).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Where to write the generated dashboard (default: {DEFAULT_OUTPUT}).",
    )
    parser.add_argument(
        "--top-sections",
        type=int,
        help="Maximum number of sections to include in the chart and summary table.",
    )
    parser.add_argument(
        "--max-resources",
        type=int,
        default=24,
        help="Maximum number of resource cards to display in the detail grid (use 0 for unlimited).",
    )
    parser.add_argument(
        "--section",
        dest="sections",
        action="append",
        help="Optional section filter; may be supplied multiple times.",
    )
    parser.add_argument(
        "--search",
        help="Optional keyword search applied to resource descriptions.",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        help="Alternative repository root containing the curated markdown files.",
    )
    return parser


def build_argument_parser() -> argparse.ArgumentParser:
    """Return the CLI argument parser used for dashboard generation."""

    parser = argparse.ArgumentParser(
        description="Generate a static HTML dashboard showcasing the curated resources.",
    )
    return add_cli_arguments(parser)


def run_cli(args: argparse.Namespace) -> int:
    """Execute the dashboard CLI using ``args`` parsed from argparse."""

    artifact = write_dashboard(
        args.output,
        category=args.category,
        top_sections=args.top_sections,
        max_resources=args.max_resources,
        section_filter=args.sections,
        search=args.search,
        source_root=args.source_root,
    )
    print(
        "Generated dashboard:"
        f"\n  HTML : {artifact.html_path.resolve()}"
        f"\n  Chart: {artifact.chart_path.resolve()}"
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the dashboard CLI."""

    parser = build_argument_parser()
    args = parser.parse_args(argv)

    return run_cli(args)


if __name__ == "__main__":  # pragma: no cover - manual invocation entry point
    raise SystemExit(main())
