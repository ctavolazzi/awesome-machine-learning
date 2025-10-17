"""Generate a polished SVG bar chart summarizing resource counts per section."""
from __future__ import annotations

import argparse
import html
import logging
from pathlib import Path
from typing import Iterable, Sequence, Tuple

from . import resource_loader

LOGGER = logging.getLogger(__name__)

DEFAULT_OUTPUT = Path("resource_section_summary.svg")
SVG_WIDTH = 1040
SVG_PADDING = 48
ROW_MIN_HEIGHT = 64
ROW_VERTICAL_PADDING = 28
BAR_HEIGHT = 24
BAR_BACKGROUND_HEIGHT = 34
AXIS_COLOR = "#1f2933"
GRID_COLOR = "#d2d6dc"
BAR_COLOR = "url(#barGradient)"
BAR_STROKE = "#467bff"
BACKGROUND_EVEN = "#f5f7ff"
BACKGROUND_ODD = "#ffffff"
FONT_FAMILY = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
LABEL_COLUMN_MIN = 220
LABEL_COLUMN_MAX = 460
LABEL_COLUMN_PADDING = 24
COUNT_COLUMN_WIDTH = 110
ROW_NUMBER_WIDTH = 32
FOREIGNOBJECT_VERTICAL_INSET = 12
CHAR_WIDTH_ESTIMATE = 7
LINE_HEIGHT = 20
TITLE_FONT_SIZE = 22
SUBTITLE_FONT_SIZE = 14
TICK_MIN_SPACING = 80


def add_cli_arguments(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument(
        "--category",
        choices=sorted(resource_loader.available_categories()),
        default="frameworks",
        help="Resource category to visualize (default: frameworks).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Where to write the generated chart (default: {DEFAULT_OUTPUT}).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Only include the top N sections sorted by resource count.",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        help="Alternative repository root containing the curated markdown files.",
    )
    return parser


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create an SVG bar chart showing how many resources exist in each section.",
    )
    return add_cli_arguments(parser)


def _sorted_sections(summary: Sequence[Tuple[str, int]], limit: int | None) -> Iterable[Tuple[str, int]]:
    ordered = sorted(summary, key=lambda item: item[1], reverse=True)
    if limit is not None:
        ordered = ordered[:limit]
    return ordered


def _build_ticks(max_count: int, scale: float) -> list[int]:
    """Return a sorted list of tick values that stay visually separated."""

    anchors = {0, max_count}
    if max_count > 1:
        anchors.add(max(1, max_count // 2))
    if max_count > 3:
        anchors.add(max(1, max_count // 4))
        anchors.add(max(1, (3 * max_count) // 4))

    ticks = sorted(anchors)
    filtered: list[int] = []
    last_pos = None
    for tick in ticks:
        position = tick * scale
        if last_pos is None or position - last_pos >= TICK_MIN_SPACING:
            filtered.append(tick)
            last_pos = position
    if filtered[-1] != max_count:
        filtered.append(max_count)
    return filtered


def render_svg_chart(
    category: str,
    *,
    limit: int | None = None,
    source_root: Path | None = None,
) -> str:
    """Return an SVG string representing the section counts for ``category``."""

    summary = resource_loader.section_summary(category, source_root=source_root)
    if not summary:
        raise ValueError(f"No populated sections found for category '{category}'")

    ordered_sections = list(_sorted_sections(summary.items(), limit))
    max_count = max(count for _, count in ordered_sections)

    row_count = len(ordered_sections)

    def estimate_text_width(label: str) -> int:
        parts = label.split(" › ")
        return max(len(part) for part in parts) * CHAR_WIDTH_ESTIMATE

    def wrap_label(label: str, *, max_chars: int) -> list[str]:
        words = label.split()
        if not words:
            return [""]

        lines: list[str] = []
        current = words[0]

        for word in words[1:]:
            candidate = f"{current} {word}"
            if len(candidate) <= max_chars:
                current = candidate
                continue

            if len(current) > max_chars:
                # Hard wrap the very long token so it never bleeds into the bar area.
                while len(current) > max_chars:
                    lines.append(current[:max_chars])
                    current = current[max_chars:]

            lines.append(current)
            current = word

        while len(current) > max_chars:
            lines.append(current[:max_chars])
            current = current[max_chars:]

        if current:
            lines.append(current)

        return lines or [""]

    def multiline_text(
        *,
        text_id: str,
        role: str,
        placement: str,
        x: float,
        center_y: float,
        fill: str,
        lines: Sequence[str],
        text_anchor: str = "start",
        indent: str = "  ",
    ) -> str:
        safe_lines = [html.escape(part) for part in lines]
        total_height = LINE_HEIGHT * len(safe_lines)
        first_line_y = center_y - (total_height - LINE_HEIGHT) / 2
        body = [
            f"{indent}<text id='{text_id}' data-role='{role}' data-placement='{placement}' x='{x}' y='{first_line_y}' "
            f"fill='{fill}' text-anchor='{text_anchor}'>",
            f"{indent}  {safe_lines[0]}",
        ]
        for line in safe_lines[1:]:
            body.append(f"{indent}  <tspan x='{x}' dy='{LINE_HEIGHT}'>{line}</tspan>")
        body.append(f"{indent}</text>")
        return "\n".join(body)

    labels = [resource_loader.display_section_name(section) for section, _ in ordered_sections]
    max_label_width = max(estimate_text_width(label) for label in labels)
    max_word_width = max(
        (len(word) for label in labels for word in label.split()),
        default=0,
    ) * CHAR_WIDTH_ESTIMATE
    label_column_width = max(
        LABEL_COLUMN_MIN,
        min(
            LABEL_COLUMN_MAX,
            max(max_label_width, max_word_width) + LABEL_COLUMN_PADDING * 2 + ROW_NUMBER_WIDTH,
        ),
    )

    text_area_width = max(60, label_column_width - ROW_NUMBER_WIDTH - LABEL_COLUMN_PADDING)
    max_chars_per_line = max(12, text_area_width // CHAR_WIDTH_ESTIMATE)
    wrapped_labels = [wrap_label(label, max_chars=max_chars_per_line) for label in labels]
    row_heights = [
        max(
            ROW_MIN_HEIGHT,
            LINE_HEIGHT * len(lines) + ROW_VERTICAL_PADDING,
        )
        for lines in wrapped_labels
    ]
    bar_area_height = sum(row_heights)
    svg_height = bar_area_height + SVG_PADDING * 2

    label_box_x = SVG_PADDING
    label_number_x = label_box_x + 12
    label_x = label_box_x + ROW_NUMBER_WIDTH + 12
    bar_x = SVG_PADDING + label_column_width
    count_x = SVG_WIDTH - SVG_PADDING
    available_chart_width = max(120, count_x - bar_x - COUNT_COLUMN_WIDTH)
    scale = available_chart_width / max_count

    tick_values = _build_ticks(max_count, scale)

    svg_lines = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{SVG_WIDTH}' height='{svg_height}' viewBox='0 0 {SVG_WIDTH} {svg_height}'>",
        "  <defs>",
        "    <linearGradient id='barGradient' x1='0%' y1='0%' x2='100%' y2='0%'>",
        "      <stop offset='0%' stop-color='#85a5ff' stop-opacity='0.95' />",
        "      <stop offset='100%' stop-color='#3c6ff7' stop-opacity='1' />",
        "    </linearGradient>",
        "  </defs>",
        "  <style>"
        f"    text {{ font-family: {FONT_FAMILY}; fill: {AXIS_COLOR}; font-size: 15px; }}"
        "    .count { font-weight: 600; font-size: 16px; }"
        "    .label-wrapper {"
        "      height: 100%;"
        "      display: flex;"
        "      align-items: center;"
        "    }"
        "    .label {"
        f"      font-family: {FONT_FAMILY};"
        "      font-size: 15px;"
        "      line-height: 1.45;"
        "      color: #1f2933;"
        "      margin: 0;"
        "      word-break: break-word;"
        "    }"
        "    .label-fallback {"
        "      display: none;"
        "    }"
        "  </style>",
        "  <rect width='100%' height='100%' fill='white' />",
        f"  <text x='{SVG_WIDTH / 2}' y='{SVG_PADDING - 20}' text-anchor='middle' font-size='{TITLE_FONT_SIZE}px' font-weight='600'>{category.title()} resources by section</text>",
        f"  <text x='{SVG_WIDTH / 2}' y='{SVG_PADDING + 2}' text-anchor='middle' font-size='{SUBTITLE_FONT_SIZE}px' opacity='0.75'>Sorted by total resources · {row_count} sections shown</text>",
    ]

    grid_y_top = SVG_PADDING - 14
    grid_y_bottom = SVG_PADDING + bar_area_height + 14
    for tick in tick_values:
        tick_x = bar_x + tick * scale
        svg_lines.append(
            f"  <line x1='{tick_x}' y1='{grid_y_top}' x2='{tick_x}' y2='{grid_y_bottom}' stroke='{GRID_COLOR}' stroke-width='0.75' opacity='0.45' stroke-dasharray='4 6' />"
        )
        svg_lines.append(
            f"  <text x='{tick_x}' y='{grid_y_top - 8}' text-anchor='middle' font-size='12px' opacity='0.7'>{tick}</text>"
        )

    cumulative_height = SVG_PADDING
    for index, ((section, count), label_lines, row_height) in enumerate(
        zip(ordered_sections, wrapped_labels, row_heights)
    ):
        row_top = cumulative_height
        cumulative_height += row_height
        width = max(6, int(count * scale))
        height = BAR_HEIGHT
        background_color = BACKGROUND_EVEN if index % 2 == 0 else BACKGROUND_ODD

        svg_lines.append(
            f"  <g data-row='{index}' transform='translate(0,{row_top})'>"
        )
        svg_lines.append(
            f"    <rect x='{label_box_x}' y='0' width='{label_column_width}' height='{row_height}' fill='{background_color}' rx='12' ry='12' opacity='0.95' />"
        )
        svg_lines.append(
            f"    <text x='{label_number_x}' y='{row_height / 2}' text-anchor='start' dominant-baseline='middle' font-size='12px' opacity='0.7'>{index + 1:02d}</text>"
        )
        label_foreign_x = label_box_x + ROW_NUMBER_WIDTH + LABEL_COLUMN_PADDING / 2
        label_foreign_width = label_column_width - ROW_NUMBER_WIDTH - LABEL_COLUMN_PADDING
        label_foreign_height = max(16, row_height - FOREIGNOBJECT_VERTICAL_INSET * 2)
        label_foreign_y = max(0, (row_height - label_foreign_height) / 2)
        safe_label = html.escape(labels[index]).replace("\n", "<br />")
        svg_lines.append(
            f"    <foreignObject x='{label_foreign_x}' y='{label_foreign_y}' width='{label_foreign_width}' height='{label_foreign_height}'>"
        )
        svg_lines.append(
            "      <div xmlns='http://www.w3.org/1999/xhtml' class='label-wrapper'>"
            f"<p class='label' data-role='section' data-placement='column'>{safe_label}</p></div>"
        )
        svg_lines.append("    </foreignObject>")
        svg_lines.append(
            multiline_text(
                text_id=f"section-{index}",
                role="section",
                placement="column",
                x=label_x,
                center_y=row_height / 2,
                fill=AXIS_COLOR,
                lines=label_lines,
                text_anchor="start",
                indent="    ",
            ).replace("<text", "<text class='label-fallback'", 1)
        )
        bar_background_y = max(4, (row_height - BAR_BACKGROUND_HEIGHT) / 2)
        bar_fill_y = max(4, (row_height - BAR_HEIGHT) / 2)
        svg_lines.append(
            f"    <rect x='{bar_x}' y='{bar_background_y}' width='{available_chart_width}' height='{BAR_BACKGROUND_HEIGHT}' fill='#eef2ff' rx='16' ry='16' opacity='0.6' />"
        )
        svg_lines.append(
            f"    <rect x='{bar_x}' y='{bar_fill_y}' width='{width}' height='{height}' rx='12' ry='12' fill='{BAR_COLOR}' stroke='{BAR_STROKE}' stroke-width='0.75' opacity='0.95' />"
        )
        svg_lines.append(
            f"    <text class='count' data-role='count' x='{count_x}' y='{row_height / 2}' text-anchor='end' dominant-baseline='middle'>{count}</text>"
        )
        svg_lines.append("  </g>")

    svg_lines.append("</svg>")
    return "\n".join(svg_lines)


def run_cli(args: argparse.Namespace) -> int:
    svg = render_svg_chart(
        args.category,
        limit=args.limit,
        source_root=args.source_root,
    )
    output_path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg, encoding="utf-8")
    LOGGER.info("Wrote visualization to %s", output_path.resolve())
    print(f"Wrote visualization to {output_path.resolve()}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    return run_cli(args)


if __name__ == "__main__":  # pragma: no cover - manual invocation entry point
    raise SystemExit(main())
