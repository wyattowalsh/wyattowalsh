from pathlib import Path


def _read_readme():
    p = Path(__file__).resolve().parents[1] / "README.md"
    return p.read_text(encoding='utf-8')


def test_gfm_callouts_and_footnotes_in_readme():
    """Presence/placement of GFM callouts and footnotes in README generation outputs."""
    txt = _read_readme()
    # Expect GFM-style callout and a footnote marker to be present
    assert "> [!NOTE]" in txt and "[^1]" in txt, (
        "Expected GFM callouts (> [!NOTE]) and footnotes ([^1]) in README outputs"
    )


def test_living_art_in_dropdown():
    """Living-art mapping should be rendered inside a dropdown/disclosure (<details>) structure."""
    txt = _read_readme()
    loc = txt.find("living-art")
    assert loc != -1, "living-art mapping not found in README"
    before = txt.rfind("<details", 0, loc)
    after = txt.find("</details>", loc)
    assert before != -1 and after != -1, (
        "Expected living-art mapping to be wrapped inside a <details>...</details> disclosure"
    )


def test_marker_safety_invariants():
    """Marker-safety: managed marker block delimiters must remain intact and ordered."""
    txt = _read_readme()
    start = "<!-- BEGIN MANAGED MARKER -->"
    end = "<!-- END MANAGED MARKER -->"
    assert start in txt and end in txt, "Managed marker block delimiters missing"
    assert txt.index(start) < txt.index(end), "Managed marker block order corrupted"
