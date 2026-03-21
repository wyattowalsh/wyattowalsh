"""Tests for scripts.techs — technology proficiency parser."""
from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

SAMPLE_MD = (
    "## Programming Languages\n"
    "- Python (Level: 5) - Primary\n"
    "- Go (Level: 3)\n"
    "\n"
    "## Cloud & DevOps\n"
    "- Docker (Level: 4)\n"
)


class TestTechnologyModel:
    def test_valid_technology_model(self):
        from scripts.techs import Technology

        tech = Technology(name="Python", level=5, category="Languages", notes="Primary")
        assert tech.name == "Python"
        assert tech.level == 5
        assert tech.category == "Languages"
        assert tech.notes == "Primary"

    def test_technology_optional_fields_default_none(self):
        from scripts.techs import Technology

        tech = Technology(name="Go", level=3)
        assert tech.category is None
        assert tech.notes is None

    def test_level_constraint_min(self):
        from scripts.techs import Technology

        with pytest.raises(ValidationError):
            Technology(name="X", level=0)  # ge=1

    def test_level_constraint_max(self):
        from scripts.techs import Technology

        with pytest.raises(ValidationError):
            Technology(name="X", level=6)  # le=5

    def test_level_boundary_valid_min(self):
        from scripts.techs import Technology

        tech = Technology(name="X", level=1)
        assert tech.level == 1

    def test_level_boundary_valid_max(self):
        from scripts.techs import Technology

        tech = Technology(name="X", level=5)
        assert tech.level == 5

    def test_empty_name_allowed(self):
        """Pydantic does not enforce non-empty str by default."""
        from scripts.techs import Technology

        tech = Technology(name="", level=3)
        assert tech.name == ""


class TestParseTechnologyLine:
    def test_parse_valid_line_with_notes(self):
        from scripts.techs import parse_technology_line

        result = parse_technology_line("- Python (Level: 5) - Primary", "Languages")
        assert result is not None
        assert result.name == "Python"
        assert result.level == 5
        assert result.notes == "Primary"
        assert result.category == "Languages"

    def test_parse_valid_line_without_notes(self):
        from scripts.techs import parse_technology_line

        result = parse_technology_line("- Go (Level: 3)", "Languages")
        assert result is not None
        assert result.name == "Go"
        assert result.level == 3
        assert result.notes is None

    def test_parse_valid_line_none_category(self):
        from scripts.techs import parse_technology_line

        result = parse_technology_line("- Rust (Level: 4)", None)
        assert result is not None
        assert result.name == "Rust"
        assert result.category is None

    def test_parse_section_header_returns_none(self):
        from scripts.techs import parse_technology_line

        result = parse_technology_line("## Section Header", "Languages")
        assert result is None

    def test_parse_empty_line_returns_none(self):
        from scripts.techs import parse_technology_line

        result = parse_technology_line("", "Languages")
        assert result is None

    def test_parse_plain_text_returns_none(self):
        from scripts.techs import parse_technology_line

        result = parse_technology_line("Just some text", "Languages")
        assert result is None

    def test_parse_missing_level_returns_none(self):
        from scripts.techs import parse_technology_line

        result = parse_technology_line("- Python", "Languages")
        assert result is None

    def test_parse_out_of_range_level_returns_none(self):
        """parse_technology_line guards level in [1,5]; level=0 or 6 returns None."""
        from scripts.techs import parse_technology_line

        result = parse_technology_line("- Python (Level: 6)", "Languages")
        assert result is None

        result = parse_technology_line("- Python (Level: 0)", "Languages")
        assert result is None

    def test_parse_preserves_multiword_name(self):
        from scripts.techs import parse_technology_line

        result = parse_technology_line("- Apache Kafka (Level: 4) - Streaming", "Data")
        assert result is not None
        assert result.name == "Apache Kafka"
        assert result.notes == "Streaming"

    def test_parse_leading_whitespace_ignored(self):
        from scripts.techs import parse_technology_line

        result = parse_technology_line("  - Python (Level: 5)", "Languages")
        assert result is not None
        assert result.name == "Python"

    @given(st.text(min_size=0, max_size=200))
    @settings(max_examples=200, deadline=None)
    def test_never_crashes(self, line: str):
        from scripts.techs import parse_technology_line

        result = parse_technology_line(line, "TestCategory")
        assert result is None or hasattr(result, "name")

    @given(st.text(min_size=0, max_size=200))
    @settings(max_examples=100, deadline=None)
    def test_never_crashes_with_none_category(self, line: str):
        from scripts.techs import parse_technology_line

        result = parse_technology_line(line, None)
        assert result is None or hasattr(result, "name")


class TestLoadTechnologies:
    def test_load_from_file(self, tmp_path):
        from scripts.techs import load_technologies

        md = tmp_path / "techs.md"
        md.write_text(SAMPLE_MD)
        techs = load_technologies(md)
        assert len(techs) == 3
        assert techs[0].name == "Python"
        assert techs[0].category == "Programming Languages"
        assert techs[1].name == "Go"
        assert techs[1].category == "Programming Languages"
        assert techs[2].name == "Docker"
        assert techs[2].category == "Cloud & DevOps"

    def test_load_from_file_preserves_levels(self, tmp_path):
        from scripts.techs import load_technologies

        md = tmp_path / "techs.md"
        md.write_text(SAMPLE_MD)
        techs = load_technologies(md)
        assert techs[0].level == 5
        assert techs[1].level == 3
        assert techs[2].level == 4

    def test_load_from_file_preserves_notes(self, tmp_path):
        from scripts.techs import load_technologies

        md = tmp_path / "techs.md"
        md.write_text(SAMPLE_MD)
        techs = load_technologies(md)
        assert techs[0].notes == "Primary"
        assert techs[1].notes is None

    def test_load_missing_file_returns_empty_list(self, tmp_path):
        """load_technologies catches FileNotFoundError internally and returns []."""
        from scripts.techs import load_technologies

        result = load_technologies(tmp_path / "missing.md")
        assert result == []

    def test_load_empty_file_returns_empty_list(self, tmp_path):
        from scripts.techs import load_technologies

        md = tmp_path / "techs.md"
        md.write_text("")
        techs = load_technologies(md)
        assert techs == []

    def test_load_only_headers_no_items(self, tmp_path):
        from scripts.techs import load_technologies

        md = tmp_path / "techs.md"
        md.write_text("## Programming Languages\n## Cloud & DevOps\n")
        techs = load_technologies(md)
        assert techs == []

    def test_load_skips_invalid_lines(self, tmp_path):
        from scripts.techs import load_technologies

        content = (
            "## Programming Languages\n"
            "- Python (Level: 5)\n"
            "- NotAValidEntry\n"
            "- Go (Level: 3)\n"
        )
        md = tmp_path / "techs.md"
        md.write_text(content)
        techs = load_technologies(md)
        assert len(techs) == 2
        names = [t.name for t in techs]
        assert "Python" in names
        assert "Go" in names

    def test_load_custom_category(self, tmp_path):
        """Categories not in PREDEFINED_CATEGORIES are still loaded correctly."""
        from scripts.techs import load_technologies

        content = "## My Custom Category\n- SomeTool (Level: 2)\n"
        md = tmp_path / "techs.md"
        md.write_text(content)
        techs = load_technologies(md)
        assert len(techs) == 1
        assert techs[0].category == "My Custom Category"

    def test_load_returns_list_type(self, tmp_path):
        from scripts.techs import load_technologies

        md = tmp_path / "techs.md"
        md.write_text(SAMPLE_MD)
        result = load_technologies(md)
        assert isinstance(result, list)

    def test_load_uncategorized_entry(self, tmp_path):
        """Lines with valid format before any ## header are parsed as Uncategorized."""
        from scripts.techs import load_technologies

        content = "- Python (Level: 5) - Orphan\n"
        md = tmp_path / "techs.md"
        md.write_text(content)
        techs = load_technologies(md)
        assert len(techs) == 1
        assert techs[0].name == "Python"
        assert techs[0].category == "Uncategorized"
