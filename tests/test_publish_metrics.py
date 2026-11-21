"""Finalizer transition and failure checks using real staged metric artifacts."""

import json
from pathlib import Path

import pytest

from scripts._publish_metrics import MANIFEST_NAME, publish_metrics
from scripts.config import ReadmeSectionsSettings
from scripts.readme_sections import ReadmeSectionGenerator
from scripts.supplemental_metrics import ASSET_SPECS
from scripts.wakatime_readme import MARKER_END, MARKER_START, WAKA_SVG_POINTER


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
    (metrics / MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")
    if enabled:
        (waka / "waka-section.md").write_text(WAKA_SVG_POINTER, encoding="utf-8")
        (waka / "wakatime.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'aria-label="WakaTime coding activity">'
            "<text>WakaTime</text></svg>",
            encoding="utf-8",
        )
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
        for name in ("metrics-music.svg", "metrics-posts.svg", "wakatime.svg"):
            assert (dest / name).is_file() == enabled
        for name in ("metrics-languages.svg", "metrics-habits.svg"):
            assert (dest / name).read_bytes() == (stages[0] / name).read_bytes()
        content = generator._postprocess_static_sections(
            readme.read_text(encoding="utf-8"), readme_path=readme
        )
        readme.write_text(content, encoding="utf-8")
        assert (WAKA_SVG_POINTER in content) == enabled
        for filename in ("metrics-music.svg", "metrics-posts.svg", "wakatime.svg"):
            assert (f'src=".github/assets/img/{filename}"' in content) == enabled
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
