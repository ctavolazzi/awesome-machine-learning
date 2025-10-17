from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from examples.resource_explorer import resource_loader


def test_available_categories_exposes_expected_files():
    categories = resource_loader.available_categories()
    assert "books" in categories
    assert categories["books"].name == "books.md"


def test_load_sections_returns_data():
    sections = resource_loader.load_sections("books")
    # Ensure that at least one section has entries.
    assert any(entries for entries in sections.values())


def test_find_resources_can_search_by_keyword():
    hits = resource_loader.find_resources("books", query="Deep Learning", limit=20)
    assert any("Deep Learning" in hit.description for hit in hits)


def test_load_collection_normalizes_entries():
    collection = resource_loader.load_collection("books")

    assert collection.category == "books"
    assert collection.total_sections > 0
    assert collection.total_resources > 0
    first_section = collection.sections[0]
    assert isinstance(first_section.resources[0], resource_loader.CuratedResource)
    assert first_section.resources[0].title
    assert first_section.resources[0].url


def test_summarize_sections_ignores_empty_entries():
    sections = {
        "Filled Section": ["Item 1", "Item 2"],
        "Empty Section": [],
    }
    summary = resource_loader.summarize_sections(sections)
    assert summary == {"Filled Section": 2}


def test_section_summary_matches_summarize_sections():
    sections = resource_loader.load_sections("courses")
    summary = resource_loader.section_summary("courses")
    for section_name, entries in sections.items():
        if entries:
            assert summary[section_name] == len(entries)


def test_format_hits_draws_unicode_table():
    hits = [
        resource_loader.ResourceHit(
            section="Alpha",
            resource=resource_loader.CuratedResource(
                title="First", url="https://example.com/first"
            ),
        ),
        resource_loader.ResourceHit(
            section="Beta",
            resource=resource_loader.CuratedResource(
                title="Second",
                url="https://example.com/second",
                summary="A sequel",
            ),
        ),
    ]
    table = resource_loader.format_hits(hits)
    assert table.startswith("┌")
    assert "Alpha" in table
    assert "Second" in table


def test_format_sections_includes_counts():
    output = resource_loader.format_sections("frameworks")
    assert "Section" in output
    assert "Resources" in output


def test_display_section_name_trims_root_path():
    assert (
        resource_loader.display_section_name(
            "Awesome Machine Learning / Python / Natural Language Processing"
        )
        == "Python › Natural Language Processing"
    )
    assert resource_loader.display_section_name("General") == "General"
