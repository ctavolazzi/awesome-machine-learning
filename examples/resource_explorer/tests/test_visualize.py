"""Tests for the visualization helpers."""
from __future__ import annotations

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from examples.resource_explorer import visualize


def test_render_svg_chart_marks_count_and_sections(monkeypatch: pytest.MonkeyPatch) -> None:
    summary = {
        "Tiny": 200,
        "Very Long Section Name › With Extra Parts": 5,
    }

    monkeypatch.setattr(
        visualize.resource_loader,
        "section_summary",
        lambda category, source_root=None: summary,
    )
    monkeypatch.setattr(
        visualize.resource_loader,
        "display_section_name",
        lambda name: name,
    )

    svg = visualize.render_svg_chart("frameworks")

    assert "data-role='count'" in svg
    assert "data-role='section'" in svg
    assert "data-placement='column'" in svg
    assert "<foreignObject" in svg
    assert "class='label'" in svg
    assert "<tspan" in svg
    assert "Tiny" in svg
    assert "Very Long Section Name" in svg
    assert "stroke-width='0.75'" in svg
