"""Finalizer transition and failure checks using real staged metric artifacts."""

import json
from pathlib import Path

import pytest

from scripts._publish_metrics import MANIFEST_NAME, publish_metrics
from scripts.config import ReadmeSectionsSettings
from scripts.profile_metric_family import (
    METRIC_NAMES,
    metric_files,
    write_metric_detail,
)
from scripts.readme_sections import ReadmeSectionGenerator
from scripts.supplemental_metrics import ASSET_SPECS
from scripts.wakatime_readme import MARKER_END, MARKER_START, WAKA_SVG_POINTER


def _write_siblings(directory: Path, name: str) -> None:
    (directory / f"summary-{name}.svg").write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg"><desc>{name} summary</desc>'
        f"<text>{name}</text></svg>",
        encoding="utf-8",
    )
    write_metric_detail(
        directory,
        name,
        f"<details>\n<summary>Read the data</summary>\n\n"
        f"[Full chart](.github/assets/img/{name}.svg)\n\n</details>",
    )


def _stages(root: Path, enabled: bool) -> tuple[Path, Path]:
    metrics = root / "metrics"
    waka = root / "waka"
    metrics.mkdir(parents=True)
    waka.mkdir()
    manifest = {}
    for key, spec in ASSET_SPECS.items():
        active = not spec.optional or (enabled and key != "activity")
        name = f"{spec.asset_name}.svg"
        manifest[key] = {
            "asset_name": spec.asset_name,
            "filename": name,
            "enabled": active,
            "optional": spec.optional,
            "title": spec.title,
            "required_markers": spec.required_markers,
        }
        if active:
            (metrics / name).write_text(
                f'<svg xmlns="http://www.w3.org/2000/svg"><text>'
                f"{' '.join(spec.required_markers)}</text></svg>",
                encoding="utf-8",
            )
            if spec.asset_name in METRIC_NAMES:
                _write_siblings(metrics, spec.asset_name)
    (metrics / MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")
    if enabled:
        (waka / "waka-section.md").write_text(WAKA_SVG_POINTER, encoding="utf-8")
        (waka / "wakatime.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'aria-label="WakaTime coding activity">'
            "<text>WakaTime</text></svg>",
            encoding="utf-8",
        )
        _write_siblings(waka, "wakatime")
    else:
        (waka / "waka-section.skipped").write_text("Key missing\n", encoding="utf-8")
    return metrics, waka


def test_publication_reconciles_enabled_disabled_enabled(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    template = Path(__file__).resolve().parents[1] / "README.md"
    readme.write_bytes(template.read_bytes())
    generator = ReadmeSectionGenerator(ReadmeSectionsSettings(readme_path=str(readme)))
    on = _stages(tmp_path / "enabled", True)
    off = _stages(tmp_path / "disabled", False)
    dest = tmp_path / ".github/assets/img"
    dest.mkdir(parents=True)
    unrelated = dest / "unrelated.svg"
    unrelated.write_bytes(b"keep")
    states: dict[bool, str] = {}
    for enabled, stages in [(True, on), (False, off), (False, off), (True, on)]:
        publish_metrics(*stages, readme)
        for name in (*metric_files("metrics-music"), "metrics-posts.svg"):
            assert (dest / name).is_file() == enabled
        for name in ("metrics-languages.svg", "metrics-habits.svg"):
            assert (dest / name).read_bytes() == (stages[0] / name).read_bytes()
        content = generator._postprocess_static_sections(
            readme.read_text(encoding="utf-8"), readme_path=readme
        )
        readme.write_text(content, encoding="utf-8")
        assert WAKA_SVG_POINTER in content
        assert all(
            (dest / name).read_bytes() == (on[1] / name).read_bytes()
            for name in metric_files("wakatime")
        )
        assert 'src=".github/assets/img/summary-wakatime.svg"' in content
        assert (
            'src=".github/assets/img/summary-metrics-music.svg"' in content
        ) == enabled
        assert content.count(MARKER_START) == content.count(MARKER_END) == 1
        assert states.setdefault(enabled, content) == content
        assert unrelated.read_bytes() == b"keep"


@pytest.mark.parametrize(
    "defect",
    [
        "unknown-file",
        "empty-manifest",
        "missing-enabled",
        "disabled-present",
        "false-required",
        "wrong-filename",
        "empty-waka",
        "mixed-waka",
        "mixed-habits-summary",
        "missing-music-detail",
        "invalid-waka",
        "misplaced-waka-label",
        "missing-waka",
        "wrong-section",
        "duplicate-key",
    ],
)
def test_rejected_transfer_preserves_previous_files(
    tmp_path: Path, defect: str
) -> None:
    metrics, waka = _stages(tmp_path / "stage", True)
    manifest_path = metrics / MANIFEST_NAME
    if defect == "unknown-file":
        (metrics / "unexpected.svg").touch()
    elif defect == "empty-manifest":
        manifest_path.write_text("{}", encoding="utf-8")
    elif defect == "duplicate-key":
        text = manifest_path.read_text(encoding="utf-8")
        manifest_path.write_text('{"activity": {},' + text[1:], encoding="utf-8")
    elif defect == "missing-enabled":
        (metrics / "metrics-music.svg").unlink()
    elif defect in {"disabled-present", "false-required", "wrong-filename"}:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if defect == "wrong-filename":
            manifest["posts"]["filename"] = "metrics-habits.svg"
        else:
            key = "music" if defect == "disabled-present" else "languages"
            manifest[key]["enabled"] = False
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    elif defect == "mixed-habits-summary":
        (metrics / "summary-metrics-habits.svg").write_bytes(
            (metrics / "summary-metrics-languages.svg").read_bytes()
        )
    elif defect == "missing-music-detail":
        (metrics / "detail-metrics-music.md").unlink()
    elif defect == "empty-waka":
        for entry in waka.iterdir():
            entry.unlink()
    elif defect == "mixed-waka":
        (waka / "waka-section.skipped").touch()
    elif defect == "invalid-waka":
        (waka / "wakatime.svg").write_bytes(b"invalid")
    elif defect == "misplaced-waka-label":
        (waka / "wakatime.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<text aria-label="WakaTime coding activity">Other card</text></svg>',
            encoding="utf-8",
        )
    elif defect == "missing-waka":
        (waka / "wakatime.svg").unlink()
    else:
        (waka / "waka-section.md").write_text("unknown section", encoding="utf-8")

    readme = tmp_path / "README.md"
    original = f"{MARKER_START}\nold\n{MARKER_END}\n"
    readme.write_text(original, encoding="utf-8")
    dest = tmp_path / ".github/assets/img"
    dest.mkdir(parents=True)
    sentinel = dest / "metrics-languages.svg"
    sentinel.write_bytes(b"prior")
    with pytest.raises(ValueError):
        publish_metrics(metrics, waka, readme)
    assert readme.read_text(encoding="utf-8") == original
    assert list(dest.iterdir()) == [sentinel]
    assert sentinel.read_bytes() == b"prior"


def test_initial_waka_skip_and_incomplete_saved_family(tmp_path: Path) -> None:
    metrics, waka = _stages(tmp_path / "stage", False)
    readme = tmp_path / "README.md"
    readme.write_text(f"{MARKER_START}\n{MARKER_END}\n", encoding="utf-8")
    publish_metrics(metrics, waka, readme)
    images = tmp_path / ".github/assets/img"
    assert not any((images / f).exists() for f in metric_files("wakatime"))
    assert WAKA_SVG_POINTER not in readme.read_text()
    (images / "wakatime.svg").write_text("incomplete", encoding="utf-8")
    before = {p.name: p.read_bytes() for p in images.iterdir()}
    with pytest.raises(ValueError, match="Incomplete profile metric family"):
        publish_metrics(metrics, waka, readme)
    assert {p.name: p.read_bytes() for p in images.iterdir()} == before


def test_chart_dates_follow_each_saved_family(tmp_path: Path) -> None:
    from datetime import date

    from scripts.profile_metric_family import read_metric_family, render_metric_section

    metrics, _ = _stages(tmp_path / "stage", False)
    for name, day in (("metrics-habits", 22), ("metrics-languages", 20)):
        _, body, _ = read_metric_family(metrics, name)
        write_metric_detail(metrics, name, body, saved=date(2026, 8, day))
    section = render_metric_section(metrics)
    assert "Languages 2026-08-20" in section and "GitHub activity 2026-08-22" in section
    assert "WakaTime" not in section and "Spotify" not in section
    (metrics / "summary-metrics-habits.svg").write_bytes(
        (metrics / "summary-metrics-languages.svg").read_bytes()
    )
    with pytest.raises(ValueError, match="Mismatched profile metric family"):
        render_metric_section(metrics)


@pytest.mark.parametrize(
    ("include_music", "include_waka", "sources"),
    [
        (False, False, "GitHub"),
        (False, True, "GitHub and WakaTime"),
        (True, False, "GitHub and Spotify"),
        (True, True, "GitHub, WakaTime and Spotify"),
    ],
)
def test_snapshot_caption_names_only_published_sources(
    tmp_path: Path, include_music: bool, include_waka: bool, sources: str
) -> None:
    from datetime import date

    from scripts.profile_metric_family import read_metric_family, render_metric_section

    metrics, waka = _stages(tmp_path / "stage", True)
    if not include_music:
        for filename in metric_files("metrics-music"):
            (metrics / filename).unlink()
    if include_waka:
        for filename in metric_files("wakatime"):
            (metrics / filename).write_bytes((waka / filename).read_bytes())
    for name in METRIC_NAMES:
        if (metrics / f"{name}.svg").is_file():
            _, body, _ = read_metric_family(metrics, name)
            write_metric_detail(metrics, name, body, saved=date(2026, 8, 7))
    caption = render_metric_section(metrics).splitlines()[0]
    assert caption == f"**August 7, 2026** · {sources}"


@pytest.mark.parametrize("missing", ["METRICS", "FREQUENCIES"])
def test_configured_profile_requires_each_marker_pair_before_collection(
    tmp_path: Path, missing: str
) -> None:
    from scripts.config import load_config

    settings = load_config().readme_sections_settings
    assert settings is not None and settings.profile_cards is not None
    readme = tmp_path / "README.md"
    profile = Path(__file__).resolve().parents[1] / "README.md"
    source = profile.read_text()
    for edge in ("START", "END"):
        source = source.replace(f"<!-- README:{missing}:{edge} -->", "")
    readme.write_text(source)
    settings.readme_path = str(readme)
    with pytest.raises(ValueError, match="ordered README marker pair"):
        ReadmeSectionGenerator(settings).generate(require_markers=True)
    assert readme.read_text() == source
