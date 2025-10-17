"""Tests for the HTML dashboard generator."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from examples.resource_explorer import app, dashboard


@pytest.mark.parametrize("category", ["frameworks", "books"])
def test_render_dashboard_contains_expected_sections(category: str) -> None:
    html_output = dashboard.render_dashboard_html(
        category,
        top_sections=5,
        max_resources=5,
    )

    assert f"{category.title()} Resource Navigator" in html_output
    assert "Section coverage" in html_output
    assert "Featured resources" in html_output
    assert "Resources tracked" in html_output
    assert "Populated sections" in html_output
    assert "<a href=" in html_output


def test_write_dashboard_creates_file(tmp_path: Path) -> None:
    output_path = tmp_path / "dashboard.html"
    artifact = dashboard.write_dashboard(
        output_path,
        category="frameworks",
        top_sections=3,
        max_resources=4,
    )

    assert artifact.html_path == output_path
    assert artifact.chart_path.exists()
    assert output_path.exists()
    contents = output_path.read_text(encoding="utf-8")
    assert "Frameworks Resource Navigator" in contents
    assert "metric-grid" in contents
    assert artifact.chart_path.read_text(encoding="utf-8").startswith("<svg")


def test_app_dashboard_command(tmp_path: Path) -> None:
    output_path = tmp_path / "demo.html"
    exit_code = app.main(
        [
            "dashboard",
            "--output",
            str(output_path),
            "--category",
            "books",
            "--top-sections",
            "3",
            "--max-resources",
            "3",
        ]
    )

    assert exit_code == 0
    assert output_path.exists()
    assert output_path.with_name("demo_chart.svg").exists()
