"""Utilities for exploring the curated resources in this repository.

This module provides helper functions that power the example
command-line explorer located in ``examples/resource_explorer``.
"""
from __future__ import annotations

import argparse
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

LOGGER = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]


_INLINE_LINK_PATTERN = re.compile(r"[\s\[]*\[[^\]]+\]\([^)]+\)")
_INLINE_BADGE_PATTERN = re.compile(r"[\s\[]*\[!\[[^\]]*\]\([^)]+\)\]\([^)]+\)")


def _clean_heading(title: str) -> str:
    """Return ``title`` with inline badge/link markup removed."""

    cleaned = _INLINE_BADGE_PATTERN.sub("", title)
    cleaned = _INLINE_LINK_PATTERN.sub("", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or title.strip()


def _strip_inline_links(fragment: str) -> str:
    """Remove badge/link markup from ``fragment`` and tidy whitespace."""

    cleaned = _INLINE_BADGE_PATTERN.sub("", fragment)
    cleaned = _INLINE_LINK_PATTERN.sub("", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.strip()
    if not cleaned:
        return ""
    cleaned = cleaned.lstrip(" []-–—:|.,;")
    cleaned = cleaned.rstrip(" []-–—:|.,;")
    if not cleaned:
        return ""
    return cleaned


def _category_files(source_root: Path | None = None) -> Dict[str, Path]:
    """Return the mapping of known categories to markdown files."""

    base = (source_root or REPO_ROOT).resolve()
    return {
        "frameworks": base / "README.md",
        "books": base / "books.md",
        "courses": base / "courses.md",
        "blogs": base / "blogs.md",
        "events": base / "events.md",
        "meetups": base / "meetups.md",
        "curriculum": base / "ml-curriculum.md",
    }


@dataclass(frozen=True)
class CuratedResource:
    """Normalized representation of a single curated resource."""

    title: str
    url: str
    summary: str | None = None

    def display_text(self) -> str:
        """Return a human-readable description suitable for CLI output."""

        base = f"{self.title} — {self.url}" if self.url else self.title
        if self.summary:
            return f"{base} ({self.summary})"
        return base


@dataclass(frozen=True)
class ResourceSection:
    """Collection of curated resources grouped under a section heading."""

    name: str
    resources: Tuple[CuratedResource, ...]

    @property
    def count(self) -> int:
        return len(self.resources)


@dataclass(frozen=True)
class ResourceCollection:
    """Normalized representation of resources for a given category."""

    category: str
    sections: Tuple[ResourceSection, ...]

    @property
    def total_resources(self) -> int:
        return sum(section.count for section in self.sections)

    @property
    def total_sections(self) -> int:
        return len(self.sections)

    def iter_resources(self) -> Iterable[Tuple[str, CuratedResource]]:
        for section in self.sections:
            for resource in section.resources:
                yield section.name, resource


@dataclass(frozen=True)
class ResourceHit:
    """Represents a single resource match returned by the explorer."""

    section: str
    resource: CuratedResource

    @property
    def description(self) -> str:
        return self.resource.display_text()


def available_categories(source_root: Path | None = None) -> Dict[str, Path]:
    """Return the mapping of known category names to Markdown files."""

    return _category_files(source_root).copy()


def _parse_markdown_sections(markdown_path: Path) -> Dict[str, List[str]]:
    """Parse a markdown document into sections mapped to bullet entries."""

    sections: Dict[str, List[str]] = {}
    heading_stack: List[str] = []

    def current_section() -> str:
        if heading_stack:
            return " / ".join(heading_stack)
        return "General"

    with markdown_path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.rstrip()
            if not line:
                continue

            if line.lstrip().startswith("#"):
                hashes = len(line) - len(line.lstrip("#"))
                title = line.lstrip("# ")
                title = _clean_heading(title)
                if hashes <= 0:
                    continue

                level = max(1, hashes)
                # Resize the stack to the current heading level before adding the new title.
                heading_stack[:] = heading_stack[: level - 1]
                heading_stack.append(title.strip())
                sections.setdefault(current_section(), [])
                continue

            stripped = line.lstrip()
            if stripped.startswith(("-", "*", "+")):
                entry = stripped.lstrip('-*+ ').strip()
                if not entry:
                    continue
                sections.setdefault(current_section(), []).append(entry)

    return sections


def load_sections(category: str, *, source_root: Path | None = None) -> Dict[str, List[str]]:
    """Load the parsed sections for a supported category."""

    category_files = _category_files(source_root)

    try:
        markdown_path = category_files[category]
    except KeyError as error:
        known = ", ".join(sorted(category_files))
        raise ValueError(f"Unknown category '{category}'. Known categories: {known}") from error

    if not markdown_path.exists():
        raise FileNotFoundError(f"Markdown file not found for category '{category}': {markdown_path}")

    return _parse_markdown_sections(markdown_path)


def _parse_resource_entry(raw_entry: str) -> CuratedResource:
    """Parse a markdown bullet entry into a :class:`CuratedResource`."""

    link_pattern = re.compile(r"\[(?P<title>[^\]]+)\]\((?P<url>[^)]+)\)")
    match = link_pattern.search(raw_entry)
    if not match:
        raise ValueError(
            "Resource entries must contain at least one Markdown link: "
            f"'{raw_entry}'"
        )

    title = match.group("title").strip()
    url = match.group("url").strip()
    if not title or not url:
        raise ValueError(f"Resource entry is missing a title or URL: '{raw_entry}'")

    prefix = raw_entry[: match.start()].strip(" -–—:\u2013\u2014")
    raw_suffix = raw_entry[match.end():]
    suffix = _strip_inline_links(raw_suffix)
    summary_parts = [part for part in (prefix, suffix) if part]
    if summary_parts:
        trailing_punct_match = re.search(r"[.!?]+", raw_suffix)
        if trailing_punct_match:
            punctuation = trailing_punct_match.group(0).strip()
            if punctuation and summary_parts[-1][-1] not in ".!?":
                summary_parts[-1] = summary_parts[-1] + punctuation[0]
    summary = " ".join(summary_parts) if summary_parts else None

    return CuratedResource(title=title, url=url, summary=summary)


def load_collection(category: str, *, source_root: Path | None = None) -> ResourceCollection:
    """Return a normalized :class:`ResourceCollection` for ``category``."""

    sections = load_sections(category, source_root=source_root)
    normalized_sections: List[ResourceSection] = []

    for name in sorted(sections):
        entries = sections[name]
        if not entries:
            continue

        resources: List[CuratedResource] = []
        for entry in entries:
            try:
                resource = _parse_resource_entry(entry)
            except ValueError as error:
                LOGGER.warning(
                    "Skipping entry in section '%s': %s",
                    name,
                    error,
                )
                continue
            resources.append(resource)

        if resources:
            normalized_sections.append(
                ResourceSection(name=name, resources=tuple(resources))
            )

    collection = ResourceCollection(category=category, sections=tuple(normalized_sections))
    LOGGER.info(
        "Loaded %s sections and %s resources for category '%s'",
        collection.total_sections,
        collection.total_resources,
        category,
    )
    return collection


def find_resources(
    category: str,
    *,
    section_filter: Sequence[str] | None = None,
    query: str | None = None,
    limit: int | None = None,
    source_root: Path | None = None,
) -> List[ResourceHit]:
    """Return a filtered list of resources for ``category``.

    Parameters
    ----------
    category:
        Category identifier (see :func:`available_categories`).
    section_filter:
        Optional sequence of section names that should be included. Matches are case-insensitive
        and are treated as substring checks against the fully qualified section path.
    query:
        Optional keyword filter applied to the resource description (case-insensitive substring).
    limit:
        Maximum number of results to return. ``None`` means unlimited.
    """

    collection = load_collection(category, source_root=source_root)

    hits: List[ResourceHit] = []
    query_lower = query.lower() if query else None
    normalized_filters = [f.lower() for f in section_filter] if section_filter else None

    for section in collection.sections:
        if normalized_filters and not any(f in section_name.lower() for f in normalized_filters):
            continue

        section_name = section.name
        for resource in section.resources:
            haystack = " ".join(
                part
                for part in (
                    resource.title,
                    resource.summary or "",
                    resource.url,
                )
                if part
            ).lower()

            if query_lower and query_lower not in haystack:
                continue
            hits.append(ResourceHit(section=section_name, resource=resource))
            if limit is not None and len(hits) >= limit:
                return hits

    return hits


def _render_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    """Return a unicode box table for ``rows`` with ``headers``."""

    if not rows:
        return ""

    normalized_rows = []
    for row in rows:
        if len(row) != len(headers):
            raise ValueError("Row length does not match headers")
        normalized_rows.append([str(cell) for cell in row])
    normalized_headers = [str(header) for header in headers]

    widths = [len(header) for header in normalized_headers]
    for row in normalized_rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def format_row(row: Sequence[str]) -> str:
        cells = [cell.ljust(widths[i]) for i, cell in enumerate(row)]
        return f"│ {' │ '.join(cells)} │"

    top = "┌" + "┬".join("─" * (width + 2) for width in widths) + "┐"
    header_line = format_row(normalized_headers)
    divider = "├" + "┼".join("─" * (width + 2) for width in widths) + "┤"
    body = [format_row(row) for row in normalized_rows]
    bottom = "└" + "┴".join("─" * (width + 2) for width in widths) + "┘"

    return "\n".join([top, header_line, divider, *body, bottom])


def format_hits(hits: Iterable[ResourceHit]) -> str:
    """Format :class:`ResourceHit` objects as a printable table."""

    hit_rows: List[Tuple[str, str, str]] = []
    for index, hit in enumerate(hits, start=1):
        hit_rows.append(
            (
                str(index),
                hit.section,
                hit.description,
            )
        )

    if not hit_rows:
        return "No matching resources found."

    return _render_table(("#", "Section", "Description"), hit_rows)


def format_categories(source_root: Path | None = None) -> str:
    """Return a table describing the known resource categories."""

    rows = []
    for name, path in sorted(_category_files(source_root).items()):
        try:
            relative = path.relative_to(REPO_ROOT)
        except ValueError:
            relative = path
        rows.append((name, str(relative)))
    return _render_table(("Category", "Source Markdown"), rows)


def format_sections(category: str, *, source_root: Path | None = None) -> str:
    """Return a table summarizing section counts for ``category``."""

    sections = load_sections(category, source_root=source_root)
    rows: List[Tuple[str, str]] = []
    for name in sorted(sections):
        entries = sections[name]
        if entries:
            rows.append((name, str(len(entries))))

    if not rows:
        return "No populated sections were found for this category."

    return _render_table(("Section", "Resources"), rows)


def summarize_sections(sections: Mapping[str, Sequence[str]] | ResourceCollection) -> Dict[str, int]:
    """Return a mapping of section names to entry counts.

    Empty sections are omitted from the result so downstream consumers can
    focus on populated categories when creating visualizations.
    """

    summary: Dict[str, int] = {}
    if isinstance(sections, ResourceCollection):
        for section in sections.sections:
            if section.count:
                summary[section.name] = section.count
        return summary

    for section_name, entries in sections.items():
        count = len(entries)
        if count:
            summary[section_name] = count
    return summary


def display_section_name(raw: str) -> str:
    """Return a cleaned, human-friendly representation of ``raw``."""

    parts = [part.strip() for part in raw.split(" / ") if part.strip()]
    if len(parts) > 1 and parts[0].lower() == "awesome machine learning":
        parts = parts[1:]
    return " › ".join(parts) if parts else raw


def section_summary(category: str, *, source_root: Path | None = None) -> Dict[str, int]:
    """Convenience wrapper that summarizes populated sections for ``category``."""

    return summarize_sections(load_collection(category, source_root=source_root))


def add_cli_arguments(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Attach CLI arguments for browsing resources to ``parser``."""

    parser.add_argument(
        "--category",
        choices=sorted(_category_files()),
        default="frameworks",
        help="Resource category to explore (default: frameworks).",
    )
    parser.add_argument(
        "--section",
        action="append",
        dest="sections",
        help="Optional section filter. Can be specified multiple times.",
    )
    parser.add_argument(
        "--search",
        help="Case-insensitive keyword search applied to resource descriptions.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of results to display.",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        help="Optional alternative root directory containing the markdown lists.",
    )
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="List available categories and exit.",
    )
    parser.add_argument(
        "--list-sections",
        action="store_true",
        help="List sections for the selected category and exit.",
    )
    return parser


def build_argument_parser() -> argparse.ArgumentParser:
    """Create the argument parser used by the example CLI application."""

    parser = argparse.ArgumentParser(
        description="Explore the curated Awesome Machine Learning resources from the command line.",
    )
    return add_cli_arguments(parser)


def run_cli(args: argparse.Namespace) -> int:
    """Execute the CLI logic using parsed ``args``."""

    if args.list_categories:
        print(format_categories(source_root=args.source_root))
        return 0

    if args.list_sections:
        print(format_sections(args.category, source_root=args.source_root))
        return 0

    hits = find_resources(
        args.category,
        section_filter=args.sections,
        query=args.search,
        limit=args.limit,
        source_root=args.source_root,
    )
    print(format_hits(hits))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the CLI application."""

    parser = build_argument_parser()
    args = parser.parse_args(argv)

    return run_cli(args)


if __name__ == "__main__":  # pragma: no cover - manual invocation entry point
    sys.exit(main())
