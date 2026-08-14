import json
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from PIL import Image

pytest.importorskip(
    "numpy", reason="scripts.art.animate imports scripts.art.ink_garden"
)

from scripts.art import animate  # noqa: E402
from scripts.art import artifacts as artifact_helpers
from scripts.art.artifacts import (  # noqa: E402
    LIVING_ART_BYTE_BUDGETS,
    LIVING_ART_STYLE_KEYS,
    build_living_art_manifest,
    publish_living_art_fleet,
    stage_living_art_fleet,
    sync_living_art_artifacts,
    validate_living_art_byte_budgets,
)


def _write_test_gif(
    path: Path,
    *,
    size: tuple[int, int] = (4, 3),
    loop: int | None = 0,
    durations: tuple[int, ...] = (12_000, 12_000),
    color_offset: int = 0,
) -> None:
    if not durations:
        raise ValueError("A test GIF needs at least one frame duration")
    frames = [
        Image.new(
            "RGB",
            size,
            color=(
                (color_offset + (index * 61)) % 256,
                (color_offset + 83 + (index * 37)) % 256,
                (color_offset + 167 + (index * 19)) % 256,
            ),
        )
        for index in range(len(durations))
    ]
    loop_options: dict[str, object] = {} if loop is None else {"loop": loop}
    frames[0].save(
        path,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=list(durations),
        **loop_options,
    )


def _write_canonical_fleet(directory: Path, *, color_offset: int = 0) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for index, name in enumerate(sorted(LIVING_ART_BYTE_BUDGETS)):
        _write_test_gif(
            directory / name,
            size=(400, 400),
            color_offset=color_offset + index,
        )


def _file_snapshot(directory: Path) -> dict[str, bytes]:
    return {
        path.name: path.read_bytes() for path in directory.iterdir() if path.is_file()
    }


def _stub_svg() -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<defs><linearGradient id="grad"><stop offset="0%" '
        'stop-color="#111"/></linearGradient></defs>'
        '<g id="layer"><circle id="dot" cx="50" cy="50" r="20" fill="url(#grad)"/></g>'
        "</svg>"
    )


def test_build_stacked_svg_has_narrative_css_and_frame_groups() -> None:
    svg = animate._build_stacked_svg(  # noqa: SLF001
        frame_svgs=[_stub_svg(), _stub_svg(), _stub_svg()],
        delays=[0.0, 7.5, 25.5],
        transition=1.2,
        total_duration=30.0,
    )

    assert "Narrative growth animation: 3-act timing" in svg
    assert "@keyframes emerge" in svg
    assert "@keyframes grow" in svg
    assert "@keyframes bloom" in svg
    assert svg.count('<g class="f f') == 3
    assert 'class="f f0"' in svg
    assert 'class="f f1"' in svg
    assert 'class="f f2"' in svg


def test_main_svg_mode_writes_expected_living_artifacts(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        animate,
        "PROFILES",
        {"wyatt": {"label": "stub-profile", "repos": [], "contributions_monthly": {}}},
    )
    monkeypatch.setattr(animate, "compute_maturity", lambda _metrics: 0.5)
    monkeypatch.setattr(
        animate.ink_garden, "generate", lambda *_args, **_kwargs: _stub_svg()
    )
    monkeypatch.setattr(
        animate.topography, "generate", lambda *_args, **_kwargs: _stub_svg()
    )
    monkeypatch.setattr(
        animate.genetic_landscape, "generate", lambda *_args, **_kwargs: _stub_svg()
    )
    monkeypatch.setattr(
        animate.physarum, "generate", lambda *_args, **_kwargs: _stub_svg()
    )
    monkeypatch.setattr(
        animate.lenia, "generate", lambda *_args, **_kwargs: _stub_svg()
    )
    monkeypatch.setattr(
        animate.ferrofluid, "generate", lambda *_args, **_kwargs: _stub_svg()
    )
    monkeypatch.setattr(
        animate.sys,
        "argv",
        ["animate", "--svg", "--frames", "4", "--profile", "wyatt"],
    )

    animate.main()

    output_dir = tmp_path / ".github" / "assets" / "img"
    for style in LIVING_ART_STYLE_KEYS:
        path = output_dir / f"{style}-growth-animated.svg"
        assert path.is_file(), f"Missing expected animated artifact: {path}"
        svg_text = path.read_text(encoding="utf-8")
        assert "Narrative growth animation: 3-act timing" in svg_text
        assert svg_text.count('<g class="f f') == 4


def test_main_svg_mode_disables_topography_timeline_for_static_frames(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        animate,
        "PROFILES",
        {"wyatt": {"label": "stub-profile", "repos": [], "contributions_monthly": {}}},
    )
    monkeypatch.setattr(animate, "compute_maturity", lambda _metrics: 0.5)
    monkeypatch.setattr(
        animate.ink_garden, "generate", lambda *_args, **_kwargs: _stub_svg()
    )
    monkeypatch.setattr(
        animate.genetic_landscape, "generate", lambda *_args, **_kwargs: _stub_svg()
    )
    monkeypatch.setattr(
        animate.physarum, "generate", lambda *_args, **_kwargs: _stub_svg()
    )
    monkeypatch.setattr(
        animate.lenia, "generate", lambda *_args, **_kwargs: _stub_svg()
    )
    monkeypatch.setattr(
        animate.ferrofluid, "generate", lambda *_args, **_kwargs: _stub_svg()
    )
    topo_calls: list[dict[str, Any]] = []

    def _capture_topo(*_args, **kwargs):
        topo_calls.append(kwargs)
        return _stub_svg()

    monkeypatch.setattr(animate.topography, "generate", _capture_topo)
    monkeypatch.setattr(
        animate.sys,
        "argv",
        ["animate", "--svg", "--frames", "4", "--profile", "wyatt"],
    )

    animate.main()

    assert len(topo_calls) == 4
    for kwargs in topo_calls:
        assert kwargs.get("timeline") is False


def test_main_gif_mode_disables_topography_timeline(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    class _FakePalImage:
        def convert(self, _mode: str):
            return self

        def quantize(self, **_kwargs):
            return self

        def save(self, out_path, **_kwargs) -> None:
            frame_count = 1 + len(_kwargs.get("append_images", []))
            frames = [
                Image.new(
                    "RGB",
                    (2, 2),
                    color=((index * 67) % 256, 40, 180),
                )
                for index in range(frame_count)
            ]
            frames[0].save(
                out_path,
                format="GIF",
                save_all=True,
                append_images=frames[1:],
                duration=_kwargs.get("duration", 100),
                loop=_kwargs.get("loop", 0),
            )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        animate,
        "PROFILES",
        {"wyatt": {"label": "stub-profile", "repos": [], "contributions_monthly": {}}},
    )
    monkeypatch.setattr(animate, "compute_maturity", lambda _metrics: 0.5)
    monkeypatch.setattr(
        animate, "svg_to_png", lambda *_args, **_kwargs: _FakePalImage()
    )
    monkeypatch.setattr(
        animate.ink_garden, "generate", lambda *_args, **_kwargs: _stub_svg()
    )
    monkeypatch.setattr(
        animate.genetic_landscape, "generate", lambda *_args, **_kwargs: _stub_svg()
    )
    monkeypatch.setattr(
        animate.physarum, "generate", lambda *_args, **_kwargs: _stub_svg()
    )
    monkeypatch.setattr(
        animate.lenia, "generate", lambda *_args, **_kwargs: _stub_svg()
    )
    monkeypatch.setattr(
        animate.ferrofluid, "generate", lambda *_args, **_kwargs: _stub_svg()
    )
    topo_calls: list[dict[str, Any]] = []

    def _capture_topo(*_args, **kwargs):
        topo_calls.append(kwargs)
        return _stub_svg()

    monkeypatch.setattr(animate.topography, "generate", _capture_topo)
    monkeypatch.setattr(
        animate.sys,
        "argv",
        ["animate", "--frames", "3", "--profile", "wyatt", "--only", "topo"],
    )

    animate.main()

    assert len(topo_calls) == 3
    for kwargs in topo_calls:
        assert kwargs.get("timeline") is False


def test_sync_living_art_artifacts_writes_manifest_and_gallery(tmp_path: Path) -> None:
    for style in LIVING_ART_STYLE_KEYS:
        _write_test_gif(tmp_path / f"living-{style}.gif")

    with patch(
        "scripts.art.artifacts.LIVING_ART_CANONICAL_DIMENSIONS",
        (4, 3),
    ):
        manifest_path, gallery_path, manifest = sync_living_art_artifacts(tmp_path)
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    gallery = gallery_path.read_text(encoding="utf-8")

    assert manifest == manifest_data
    assert manifest_data["manifest_version"] == 2
    assert manifest_data["counts"] == {
        "timelapse_gif": 6,
    }
    assert manifest_data["total_assets"] == 6
    assert manifest_data["total_bytes"] == sum(
        asset["bytes"] for asset in manifest_data["assets"]
    )
    assert all(asset["channel"] == "timelapse_gif" for asset in manifest_data["assets"])
    actual_styles = {a["style"] for a in manifest_data["assets"]}
    assert actual_styles == set(LIVING_ART_STYLE_KEYS)
    for asset in manifest_data["assets"]:
        assert asset["backend"] == "repo"
        assert asset["media_type"] == "image/gif"
        assert asset["url"] is None
        assert asset["width"] == 4
        assert asset["height"] == 3
        assert asset["frames"] == 2
        assert asset["duration_ms"] == 24_000
        assert asset["durations_ms"] == [12_000, 12_000]
        assert asset["loop"] == 0
        assert len(asset["sha256"]) == 64
    assert "Living Art Preview Gallery" in gallery
    assert "Compatibility GIFs" not in gallery
    assert "Source SVGs" not in gallery
    assert "growth.gif" not in gallery
    for style in LIVING_ART_STYLE_KEYS:
        assert f"living-{style}.gif" in gallery


def test_sync_living_art_artifacts_mirrors_docs_public_showcase(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / ".github" / "assets" / "img"
    public_dir = tmp_path / "docs" / "public" / "showcase"
    source_dir.mkdir(parents=True)
    public_dir.mkdir(parents=True)

    for style in LIVING_ART_STYLE_KEYS:
        _write_test_gif(source_dir / f"living-{style}.gif")

    # Legacy showcase collateral should survive the public mirror refresh.
    (public_dir / "inkgarden-growth.gif").write_bytes(b"GIF89a")
    (public_dir / "living-old.gif").write_bytes(b"GIF89a")

    with patch(
        "scripts.art.artifacts.LIVING_ART_CANONICAL_DIMENSIONS",
        (4, 3),
    ):
        sync_living_art_artifacts(source_dir, public_surface_dir=public_dir)

    public_manifest = json.loads(
        (public_dir / "living-art-manifest.json").read_text(encoding="utf-8")
    )
    public_gallery = (public_dir / "living-art-preview.html").read_text(
        encoding="utf-8"
    )

    assert not (public_dir / "living-old.gif").exists()
    assert (public_dir / "inkgarden-growth.gif").exists()
    assert public_manifest["counts"] == {"timelapse_gif": 6}
    assert public_manifest["output_dir"] == str(public_dir)
    for style in LIVING_ART_STYLE_KEYS:
        assert (public_dir / f"living-{style}.gif").exists()
        assert f"living-{style}.gif" in public_gallery


def test_living_art_byte_budgets_accept_reviewed_fleet(tmp_path: Path) -> None:
    for style in LIVING_ART_STYLE_KEYS:
        _write_test_gif(tmp_path / f"living-{style}.gif", size=(400, 400))

    manifest = build_living_art_manifest(tmp_path)

    validate_living_art_byte_budgets(manifest)


@pytest.mark.parametrize(
    ("invalid_metadata", "expected_diagnostic"),
    [
        (
            {"width": 200, "height": 200},
            "living-lenia.gif: dimensions=200x200 required=400x400",
        ),
        ({"loop": 1}, "living-lenia.gif: loop=1 required=0"),
        ({"loop": None}, "living-lenia.gif: loop=None required=0"),
        (
            {
                "frames": 1,
                "duration_ms": 24_000,
                "durations_ms": [24_000],
            },
            "living-lenia.gif: frames=1 required=2..120",
        ),
        (
            {
                "duration_ms": 23_990,
                "durations_ms": [11_990, 12_000],
            },
            "living-lenia.gif: duration_ms=23990 required>=24000",
        ),
        (
            {
                "frames": 121,
                "duration_ms": 24_200,
                "durations_ms": [200] * 121,
            },
            "living-lenia.gif: frames=121 required=2..120",
        ),
        (
            {
                "duration_ms": 24_000,
                "durations_ms": [0, 24_000],
            },
            r"living-lenia.gif: nonpositive frame durations at indexes=\[0\]",
        ),
    ],
)
def test_living_art_media_contract_rejects_invalid_metadata(
    tmp_path: Path,
    invalid_metadata: dict[str, Any],
    expected_diagnostic: str,
) -> None:
    for style in LIVING_ART_STYLE_KEYS:
        _write_test_gif(tmp_path / f"living-{style}.gif", size=(400, 400))
    manifest = build_living_art_manifest(tmp_path)
    target = next(
        asset for asset in manifest["assets"] if asset["name"] == "living-lenia.gif"
    )
    target.update(invalid_metadata)

    with pytest.raises(ValueError, match=expected_diagnostic):
        validate_living_art_byte_budgets(manifest)


def test_living_art_media_contract_rejects_a_missing_loop_extension(
    tmp_path: Path,
) -> None:
    for style in LIVING_ART_STYLE_KEYS:
        _write_test_gif(
            tmp_path / f"living-{style}.gif",
            size=(400, 400),
            loop=None if style == "lenia" else 0,
        )
    manifest = build_living_art_manifest(tmp_path)
    target = next(
        asset for asset in manifest["assets"] if asset["name"] == "living-lenia.gif"
    )

    assert target["loop"] is None
    with pytest.raises(ValueError, match="living-lenia.gif: loop=None required=0"):
        validate_living_art_byte_budgets(manifest)


@pytest.mark.parametrize("name", ["living-junk.gif", "living-topo-dark.gif"])
def test_living_art_manifest_rejects_unbudgeted_gifs(tmp_path: Path, name: str) -> None:
    _write_test_gif(tmp_path / name)

    if name == "living-junk.gif":
        with pytest.raises(
            ValueError, match=r"Unsupported living-art GIF: living-junk"
        ):
            build_living_art_manifest(tmp_path)
        return

    manifest = build_living_art_manifest(tmp_path)
    with pytest.raises(
        ValueError, match=r"unexpected canonical asset: living-topo-dark\.gif"
    ):
        validate_living_art_byte_budgets(manifest, budgets={})


def test_living_art_byte_budgets_report_path_and_total(tmp_path: Path) -> None:
    for style in LIVING_ART_STYLE_KEYS:
        _write_test_gif(tmp_path / f"living-{style}.gif")
    manifest = build_living_art_manifest(tmp_path)
    target_name = next(iter(LIVING_ART_BYTE_BUDGETS))
    target = next(asset for asset in manifest["assets"] if asset["name"] == target_name)
    target["bytes"] = 101

    with pytest.raises(ValueError) as error:
        with patch(
            "scripts.art.artifacts.LIVING_ART_CANONICAL_DIMENSIONS",
            (4, 3),
        ):
            validate_living_art_byte_budgets(
                manifest,
                budgets={name: 100 for name in LIVING_ART_BYTE_BUDGETS},
                total_budget=100,
            )

    message = str(error.value)
    assert f"{target_name}: observed=101 budget=100" in message
    assert "canonical total:" in message


def test_sync_living_art_artifacts_checks_budgets_before_writing_index(
    tmp_path: Path,
) -> None:
    for style in LIVING_ART_STYLE_KEYS:
        _write_test_gif(tmp_path / f"living-{style}.gif")

    budgets = dict.fromkeys(LIVING_ART_BYTE_BUDGETS, 1)
    with (
        patch("scripts.art.artifacts.LIVING_ART_BYTE_BUDGETS", budgets),
        patch("scripts.art.artifacts.LIVING_ART_TOTAL_BYTE_BUDGET", len(budgets)),
        patch("scripts.art.artifacts.LIVING_ART_CANONICAL_DIMENSIONS", (4, 3)),
    ):
        with pytest.raises(
            ValueError,
            match="Living-art media/byte contract violation",
        ):
            sync_living_art_artifacts(tmp_path)

    assert not (tmp_path / "living-art-manifest.json").exists()
    assert not (tmp_path / "living-art-preview.html").exists()


def test_explicit_empty_budget_mapping_is_authoritative() -> None:
    validate_living_art_byte_budgets(
        {"assets": []},
        budgets={},
        total_budget=0,
    )

    with pytest.raises(
        ValueError,
        match="unexpected canonical asset: living-lenia.gif",
    ):
        validate_living_art_byte_budgets(
            {"assets": [{"name": "living-lenia.gif", "bytes": 1}]},
            budgets={},
            total_budget=0,
        )


@pytest.mark.parametrize(
    ("manifest", "budgets", "expected_diagnostic"),
    [
        ({}, {}, "has no asset list"),
        ({"assets": [None]}, {}, "non-object asset"),
        (
            {"assets": [{"name": 7, "bytes": 1}]},
            {},
            "invalid name/bytes metadata",
        ),
        ({"assets": []}, None, "missing canonical assets"),
        (
            {
                "assets": [
                    {
                        "name": "one.gif",
                        "bytes": 1,
                        "width": 400,
                        "height": 400,
                        "loop": 0,
                    },
                    {
                        "name": "one.gif",
                        "bytes": 1,
                        "width": 400,
                        "height": 400,
                        "loop": 0,
                    },
                ]
            },
            {"one.gif": 2},
            "duplicate canonical assets: one.gif",
        ),
    ],
)
def test_living_art_budget_validator_rejects_malformed_manifests(
    manifest: dict[str, Any],
    budgets: dict[str, int] | None,
    expected_diagnostic: str,
) -> None:
    with pytest.raises(ValueError, match=expected_diagnostic):
        validate_living_art_byte_budgets(
            manifest,
            budgets=budgets,
            total_budget=10,
        )


def test_manifest_rejects_a_non_gif_with_a_canonical_name(tmp_path: Path) -> None:
    Image.new("RGB", (400, 400)).save(
        tmp_path / "living-lenia.gif",
        format="PNG",
    )

    with pytest.raises(ValueError, match="asset is not a GIF"):
        build_living_art_manifest(tmp_path)


def test_empty_manifest_renders_empty_gallery_and_skips_directories(
    tmp_path: Path,
) -> None:
    (tmp_path / "unrelated-directory").mkdir()

    manifest = build_living_art_manifest(tmp_path)
    gallery = artifact_helpers._render_gallery(manifest)  # noqa: SLF001

    assert manifest["total_assets"] == 0
    assert "No living-art assets were found" in gallery


def test_stable_manifest_comparison_excludes_only_run_specific_fields() -> None:
    baseline = {
        "manifest_version": 2,
        "generated_at": "first",
        "output_dir": "first-output",
        "total_assets": 6,
    }
    another_run = {
        **baseline,
        "generated_at": "second",
        "output_dir": "second-output",
    }

    artifact_helpers._assert_stable_manifests_match(  # noqa: SLF001
        baseline,
        another_run,
        context="test equivalent runs",
    )

    with pytest.raises(ValueError, match="stable payload mismatch"):
        artifact_helpers._assert_stable_manifests_match(  # noqa: SLF001
            baseline,
            {**another_run, "total_assets": 5},
            context="test material drift",
        )


def test_stage_living_art_fleet_is_exact_six_and_media_only(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    stage_dir = tmp_path / "artifact" / "living-art"
    _write_canonical_fleet(source_dir)
    (source_dir / "banner.svg").write_text("<svg/>", encoding="utf-8")
    (source_dir / "living-art-manifest.json").write_text(
        '{"manifest_version": 1}',
        encoding="utf-8",
    )
    (source_dir / "living-art-preview.html").write_text(
        "stale",
        encoding="utf-8",
    )
    stage_dir.mkdir(parents=True)

    source_manifest = stage_living_art_fleet(source_dir, stage_dir)

    assert source_manifest["total_assets"] == 6
    assert {path.name for path in stage_dir.iterdir()} == set(LIVING_ART_BYTE_BUDGETS)
    assert all(path.is_file() and not path.is_symlink() for path in stage_dir.iterdir())
    assert not (stage_dir / "living-art-manifest.json").exists()
    assert not (stage_dir / "living-art-preview.html").exists()


@pytest.mark.parametrize("source_shape", ["missing", "file", "symlink"])
def test_stage_living_art_fleet_rejects_a_non_real_source_directory(
    tmp_path: Path,
    source_shape: str,
) -> None:
    source_dir = tmp_path / "source"
    if source_shape == "file":
        source_dir.write_text("not a directory", encoding="utf-8")
    elif source_shape == "symlink":
        real_source = tmp_path / "real-source"
        _write_canonical_fleet(real_source)
        source_dir.symlink_to(real_source, target_is_directory=True)

    with pytest.raises(ValueError, match="living-art producer source"):
        stage_living_art_fleet(source_dir, tmp_path / "stage")


@pytest.mark.parametrize("stage_shape", ["overlap", "symlink", "file", "nonempty"])
def test_stage_living_art_fleet_rejects_an_unsafe_destination(
    tmp_path: Path,
    stage_shape: str,
) -> None:
    source_dir = tmp_path / "source"
    _write_canonical_fleet(source_dir)
    stage_dir = tmp_path / "stage"
    if stage_shape == "overlap":
        stage_dir = source_dir / "stage"
    elif stage_shape == "symlink":
        real_stage = tmp_path / "real-stage"
        real_stage.mkdir()
        stage_dir.symlink_to(real_stage, target_is_directory=True)
    elif stage_shape == "file":
        stage_dir.write_text("not a directory", encoding="utf-8")
    else:
        stage_dir.mkdir()
        (stage_dir / "sentinel").write_text("do not replace", encoding="utf-8")

    with pytest.raises(ValueError):
        stage_living_art_fleet(source_dir, stage_dir)


@pytest.mark.parametrize("destination_shape", ["symlink", "file", "managed-directory"])
def test_surface_destination_guard_rejects_unsafe_shapes(
    tmp_path: Path,
    destination_shape: str,
) -> None:
    destination = tmp_path / "surface"
    if destination_shape == "symlink":
        target = tmp_path / "target"
        target.mkdir()
        destination.symlink_to(target, target_is_directory=True)
    elif destination_shape == "file":
        destination.write_text("not a directory", encoding="utf-8")
    else:
        destination.mkdir()
        (destination / "living-art-manifest.json").mkdir()

    with pytest.raises(ValueError):
        artifact_helpers._validate_surface_destination(  # noqa: SLF001
            destination,
            label="test surface",
        )


def test_stage_living_art_fleet_prevalidates_before_touching_stage(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "source"
    stage_dir = tmp_path / "stage"
    _write_canonical_fleet(source_dir)
    (source_dir / "living-topo.gif").unlink()
    stage_dir.mkdir()

    with pytest.raises(ValueError, match="missing=.*living-topo.gif"):
        stage_living_art_fleet(source_dir, stage_dir)

    assert list(stage_dir.iterdir()) == []


@pytest.mark.parametrize(
    "invalid_stage",
    [
        "missing",
        "unexpected",
        "non_regular",
        "symlink",
        "corrupt",
        "wrong_dimensions",
        "wrong_loop",
        "one_frame",
        "too_short",
        "zero_frame_duration",
        "too_many_frames",
        "over_budget",
    ],
)
def test_publish_living_art_fleet_rejects_invalid_stage_before_mutation(
    tmp_path: Path,
    invalid_stage: str,
) -> None:
    stage_dir = tmp_path / "stage"
    output_dir = tmp_path / "checkout" / ".github" / "assets" / "img"
    public_dir = tmp_path / "checkout" / "docs" / "public" / "showcase"
    _write_canonical_fleet(stage_dir)
    output_dir.mkdir(parents=True)
    public_dir.mkdir(parents=True)
    (output_dir / "living-art-manifest.json").write_text("primary stale")
    (output_dir / "banner.svg").write_text("primary collateral")
    (public_dir / "living-art-preview.html").write_text("public stale")
    (public_dir / "inkgarden-growth.gif").write_bytes(b"public collateral")
    output_before = _file_snapshot(output_dir)
    public_before = _file_snapshot(public_dir)

    target = stage_dir / "living-lenia.gif"
    if invalid_stage == "missing":
        target.unlink()
    elif invalid_stage == "unexpected":
        _write_test_gif(stage_dir / "living-unknown.gif", size=(400, 400))
    elif invalid_stage == "non_regular":
        target.unlink()
        target.mkdir()
    elif invalid_stage == "symlink":
        external_target = tmp_path / "external.gif"
        _write_test_gif(external_target, size=(400, 400))
        target.unlink()
        target.symlink_to(external_target)
    elif invalid_stage == "corrupt":
        target.write_bytes(b"GIF89a")
    elif invalid_stage == "wrong_dimensions":
        _write_test_gif(target, size=(399, 400))
    elif invalid_stage == "wrong_loop":
        _write_test_gif(target, size=(400, 400), loop=1)
    elif invalid_stage == "one_frame":
        _write_test_gif(target, size=(400, 400), durations=(24_000,))
    elif invalid_stage == "too_short":
        _write_test_gif(target, size=(400, 400), durations=(40, 60))
    elif invalid_stage == "zero_frame_duration":
        _write_test_gif(target, size=(400, 400), durations=(0, 24_000))
    elif invalid_stage == "too_many_frames":
        _write_test_gif(target, size=(400, 400), durations=(200,) * 121)
    else:
        padding = LIVING_ART_BYTE_BUDGETS[target.name] + 1 - target.stat().st_size
        with target.open("ab") as stream:
            stream.write(b"\0" * padding)

    with pytest.raises((OSError, ValueError)):
        publish_living_art_fleet(
            stage_dir,
            output_dir,
            public_surface_dir=public_dir,
        )

    assert _file_snapshot(output_dir) == output_before
    assert _file_snapshot(public_dir) == public_before


def test_publish_living_art_fleet_prevalidates_both_destinations(
    tmp_path: Path,
) -> None:
    stage_dir = tmp_path / "stage"
    output_dir = tmp_path / "checkout" / ".github" / "assets" / "img"
    public_dir = tmp_path / "checkout" / "docs" / "public" / "showcase"
    _write_canonical_fleet(stage_dir)
    output_dir.mkdir(parents=True)
    public_dir.mkdir(parents=True)
    (output_dir / "living-art-manifest.json").write_text(
        "primary sentinel",
        encoding="utf-8",
    )
    (public_dir / "living-art-preview.html").mkdir()
    output_before = _file_snapshot(output_dir)

    with pytest.raises(ValueError, match="public living-art destination"):
        publish_living_art_fleet(
            stage_dir,
            output_dir,
            public_surface_dir=public_dir,
        )

    assert _file_snapshot(output_dir) == output_before


@pytest.mark.parametrize("overlap", ["stage-output", "destination-pair"])
def test_publish_living_art_fleet_rejects_overlapping_surfaces(
    tmp_path: Path,
    overlap: str,
) -> None:
    stage_dir = tmp_path / "stage"
    _write_canonical_fleet(stage_dir)
    if overlap == "stage-output":
        output_dir = stage_dir / "output"
        public_dir = tmp_path / "public"
    else:
        output_dir = tmp_path / "surface"
        public_dir = output_dir

    with pytest.raises(ValueError, match="must not overlap"):
        publish_living_art_fleet(
            stage_dir,
            output_dir,
            public_surface_dir=public_dir,
        )


def test_publish_living_art_fleet_regenerates_both_surfaces(tmp_path: Path) -> None:
    source_dir = tmp_path / "producer"
    stage_dir = tmp_path / "downloaded-artifact"
    checkout = tmp_path / "checkout"
    output_dir = checkout / ".github" / "assets" / "img"
    public_dir = checkout / "docs" / "public" / "showcase"
    _write_canonical_fleet(source_dir)
    stage_living_art_fleet(source_dir, stage_dir)
    output_dir.mkdir(parents=True)
    public_dir.mkdir(parents=True)

    for directory in (output_dir, public_dir):
        (directory / "living-art-manifest.json").write_text(
            '{"manifest_version": 1, "total_assets": 999}',
            encoding="utf-8",
        )
        (directory / "living-art-preview.html").write_text(
            "stale gallery",
            encoding="utf-8",
        )
        (directory / "living-old.gif").write_bytes(b"stale gif")
    (output_dir / "banner.svg").write_text("primary collateral", encoding="utf-8")
    (public_dir / "inkgarden-growth.gif").write_bytes(b"public collateral")

    manifest_path, gallery_path, manifest = publish_living_art_fleet(
        stage_dir,
        output_dir,
        public_surface_dir=public_dir,
    )

    primary_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    public_manifest = json.loads(
        (public_dir / "living-art-manifest.json").read_text(encoding="utf-8")
    )
    assert manifest == primary_manifest
    assert manifest_path == output_dir / "living-art-manifest.json"
    assert gallery_path == output_dir / "living-art-preview.html"
    assert primary_manifest["manifest_version"] == 2
    assert primary_manifest["total_assets"] == 6
    assert public_manifest["total_assets"] == 6
    assert {
        key: value
        for key, value in primary_manifest.items()
        if key not in {"generated_at", "output_dir"}
    } == {
        key: value
        for key, value in public_manifest.items()
        if key not in {"generated_at", "output_dir"}
    }
    assert gallery_path.read_text(encoding="utf-8") == (
        public_dir / "living-art-preview.html"
    ).read_text(encoding="utf-8")
    for name in LIVING_ART_BYTE_BUDGETS:
        expected_bytes = (stage_dir / name).read_bytes()
        assert (output_dir / name).read_bytes() == expected_bytes
        assert (public_dir / name).read_bytes() == expected_bytes
    assert not (output_dir / "living-old.gif").exists()
    assert not (public_dir / "living-old.gif").exists()
    assert (output_dir / "banner.svg").read_text() == "primary collateral"
    assert (public_dir / "inkgarden-growth.gif").read_bytes() == b"public collateral"


@pytest.mark.parametrize(
    "failure_phase",
    ["primary_replace", "companion_generation", "public_sync"],
)
def test_publish_living_art_fleet_rolls_back_both_managed_surfaces(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    failure_phase: str,
) -> None:
    stage_dir = tmp_path / "stage"
    output_dir = tmp_path / "checkout" / ".github" / "assets" / "img"
    public_dir = tmp_path / "checkout" / "docs" / "public" / "showcase"
    _write_canonical_fleet(stage_dir, color_offset=10)
    _write_canonical_fleet(output_dir, color_offset=140)
    sync_living_art_artifacts(output_dir, public_surface_dir=public_dir)
    (output_dir / "living-old.gif").write_bytes(b"old primary managed asset")
    (output_dir / "banner.svg").write_bytes(b"primary collateral")
    (output_dir / "user-notes").mkdir()
    (output_dir / "user-notes" / "keep.txt").write_bytes(b"nested primary collateral")
    (public_dir / "living-old.gif").write_bytes(b"old public managed asset")
    (public_dir / "inkgarden-growth.gif").write_bytes(b"public collateral")
    (public_dir / "user-notes").mkdir()
    (public_dir / "user-notes" / "keep.txt").write_bytes(b"nested public collateral")
    output_before = _file_snapshot(output_dir)
    public_before = _file_snapshot(public_dir)
    failure_message = f"injected {failure_phase} failure"
    triggered = False

    if failure_phase == "primary_replace":
        real_copy = artifact_helpers._copy_file_atomic  # noqa: SLF001

        def _fail_primary_replace(source: Path, destination: Path) -> None:
            nonlocal triggered
            if (
                not triggered
                and destination.parent == output_dir
                and destination.name == "living-genetic.gif"
            ):
                triggered = True
                raise OSError(failure_message)
            real_copy(source, destination)

        monkeypatch.setattr(
            artifact_helpers,
            "_copy_file_atomic",
            _fail_primary_replace,
        )
    elif failure_phase == "companion_generation":
        real_write = artifact_helpers._write_text_atomic  # noqa: SLF001

        def _fail_companion_generation(path: Path, content: str) -> None:
            nonlocal triggered
            real_write(path, content)
            if (
                not triggered
                and path.parent == output_dir
                and path.name == "living-art-preview.html"
            ):
                triggered = True
                raise OSError(failure_message)

        monkeypatch.setattr(
            artifact_helpers,
            "_write_text_atomic",
            _fail_companion_generation,
        )
    else:
        real_sync = artifact_helpers._sync_public_surface  # noqa: SLF001

        def _fail_public_sync(
            source_dir: Path,
            manifest: dict[str, Any],
            public_surface_dir: Path,
        ) -> dict[str, Any]:
            nonlocal triggered
            public_manifest = real_sync(
                source_dir,
                manifest,
                public_surface_dir,
            )
            if not triggered and public_surface_dir == public_dir:
                triggered = True
                raise OSError(failure_message)
            return public_manifest

        monkeypatch.setattr(
            artifact_helpers,
            "_sync_public_surface",
            _fail_public_sync,
        )

    with pytest.raises(OSError, match=failure_message):
        publish_living_art_fleet(
            stage_dir,
            output_dir,
            public_surface_dir=public_dir,
        )

    assert triggered
    assert _file_snapshot(output_dir) == output_before
    assert _file_snapshot(public_dir) == public_before
    assert (output_dir / "user-notes" / "keep.txt").read_bytes() == (
        b"nested primary collateral"
    )
    assert (public_dir / "user-notes" / "keep.txt").read_bytes() == (
        b"nested public collateral"
    )


def test_publish_living_art_fleet_surfaces_incomplete_rollback(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    stage_dir = tmp_path / "stage"
    output_dir = tmp_path / "checkout" / ".github" / "assets" / "img"
    public_dir = tmp_path / "checkout" / "docs" / "public" / "showcase"
    _write_canonical_fleet(stage_dir, color_offset=10)
    _write_canonical_fleet(output_dir, color_offset=140)
    sync_living_art_artifacts(output_dir, public_surface_dir=public_dir)
    (output_dir / "banner.svg").write_bytes(b"primary collateral")
    (public_dir / "inkgarden-growth.gif").write_bytes(b"public collateral")
    public_before = _file_snapshot(public_dir)
    real_write = artifact_helpers._write_text_atomic  # noqa: SLF001
    real_copy = artifact_helpers._copy_file_atomic  # noqa: SLF001

    def _fail_companion_generation(path: Path, content: str) -> None:
        real_write(path, content)
        if path.parent == output_dir and path.name == "living-art-preview.html":
            raise OSError("injected companion generation failure")

    def _fail_primary_rollback(source: Path, destination: Path) -> None:
        if (
            source.parent.name == "rollback-primary"
            and destination.parent == output_dir
            and destination.name == "living-ferrofluid.gif"
        ):
            raise OSError("injected primary rollback failure")
        real_copy(source, destination)

    monkeypatch.setattr(
        artifact_helpers,
        "_write_text_atomic",
        _fail_companion_generation,
    )
    monkeypatch.setattr(
        artifact_helpers,
        "_copy_file_atomic",
        _fail_primary_rollback,
    )

    with pytest.raises(
        RuntimeError,
        match=(
            "Living-art publication failed and rollback was incomplete: "
            ".*injected companion generation failure.*"
            "injected primary rollback failure"
        ),
    ):
        publish_living_art_fleet(
            stage_dir,
            output_dir,
            public_surface_dir=public_dir,
        )

    assert _file_snapshot(public_dir) == public_before
    assert (output_dir / "banner.svg").read_bytes() == b"primary collateral"


@pytest.mark.parametrize(
    ("corrupt_target", "expected_diagnostic"),
    [
        ("living-art-manifest.json", "persisted manifest differs"),
        ("living-art-preview.html", "persisted gallery differs"),
    ],
)
def test_sync_living_art_artifacts_rejects_a_corrupt_persisted_companion(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    corrupt_target: str,
    expected_diagnostic: str,
) -> None:
    _write_canonical_fleet(tmp_path)
    real_write = artifact_helpers._write_text_atomic  # noqa: SLF001

    def _corrupt_companion(path: Path, content: str) -> None:
        real_write(path, content)
        if path.name == corrupt_target:
            replacement = "{}" if path.suffix == ".json" else "corrupt gallery"
            real_write(path, replacement)

    monkeypatch.setattr(artifact_helpers, "_write_text_atomic", _corrupt_companion)

    with pytest.raises(ValueError, match=expected_diagnostic):
        sync_living_art_artifacts(tmp_path)


@pytest.mark.parametrize("payload", ["not json", "[]"])
def test_manifest_reader_rejects_invalid_persisted_objects(
    tmp_path: Path,
    payload: str,
) -> None:
    path = tmp_path / "living-art-manifest.json"
    path.write_text(payload, encoding="utf-8")

    with pytest.raises(ValueError, match="living-art manifest"):
        artifact_helpers._read_manifest(path)  # noqa: SLF001


def test_main_svg_mode_propagates_generator_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        animate,
        "PROFILES",
        {"wyatt": {"label": "stub", "repos": [], "contributions_monthly": {}}},
    )
    monkeypatch.setattr(animate, "compute_maturity", lambda _m: 0.5)
    monkeypatch.setattr(animate.ink_garden, "generate", lambda *_a, **_kw: _stub_svg())
    monkeypatch.setattr(
        animate.genetic_landscape, "generate", lambda *_a, **_kw: _stub_svg()
    )
    monkeypatch.setattr(animate.physarum, "generate", lambda *_a, **_kw: _stub_svg())
    monkeypatch.setattr(animate.lenia, "generate", lambda *_a, **_kw: _stub_svg())
    monkeypatch.setattr(animate.ferrofluid, "generate", lambda *_a, **_kw: _stub_svg())

    def _failing(*_a, **_kw):
        raise RuntimeError("Simulated generator failure")

    monkeypatch.setattr(animate.topography, "generate", _failing)
    monkeypatch.setattr(
        animate.sys,
        "argv",
        ["animate", "--svg", "--frames", "2", "--profile", "wyatt"],
    )

    with pytest.raises(RuntimeError, match="Simulated generator failure"):
        animate.main()


def _accretion_metrics(
    *,
    repos: int,
    stars: int,
    commits: int,
    followers: int,
) -> dict[str, Any]:
    repo_entries = []
    languages: dict[str, int] = {}
    for index in range(repos):
        language = "Python" if index % 2 == 0 else "Go"
        repo_entries.append(
            {
                "name": f"repo-{index}",
                "language": language,
                "stars": max(1, stars // max(1, repos - index)),
                "forks": 1 + index,
                "topics": ["ai" if index % 2 == 0 else "cli"],
                "description": f"Repo {index}",
                "age_months": 4 + index * 3,
                "date": f"2024-01-{index + 1:02d}T12:00:00Z",
            }
        )
        languages[language] = languages.get(language, 0) + 800 * (index + 1)
    return {
        "label": "Dialect Accretion",
        "account_created": "2023-01-01T00:00:00Z",
        "repos": repo_entries,
        "repo_visual_order": [repo["name"] for repo in repo_entries],
        "stars": stars,
        "forks": repos,
        "followers": followers,
        "watchers": repos * 2,
        "public_repos": repos,
        "network_count": repos * 2,
        "total_commits": commits,
        "total_prs": max(1, repos * 3),
        "total_issues": repos * 2,
        "total_repos_contributed": repos,
        "public_gists": repos,
        "pr_review_count": repos,
        "contributions_last_year": max(8, commits // 4),
        "contributions_monthly": {"2024-01": max(4, commits // 20)},
        "contributions_daily": {
            f"2024-01-{day:02d}": 1 + (day % 3) for day in range(1, 6)
        },
        "languages": languages,
        "language_count": len(languages),
        "language_diversity": 0.4 + repos * 0.1,
        "topic_clusters": {"ai": max(1, repos // 2), "cli": max(0, repos // 2)},
        "repo_recency_bands": {"fresh": 1, "recent": max(0, repos - 1)},
        "releases": [],
        "recent_merged_prs": [],
        "commit_hour_distribution": {12: 4, 18: 2},
        "star_velocity": {
            "recent_rate": max(0.2, stars / 20.0),
            "peak_rate": max(0.4, stars / 12.0),
            "trend": "rising",
        },
        "contribution_streaks": {
            "current_streak_months": 1,
            "longest_streak_months": 2,
            "streak_active": True,
        },
        "issue_stats": {"open_count": 1, "closed_count": 3},
        "open_issues_count": 1,
    }


def _dialect_attrs(svg: str) -> dict[str, Any]:
    match = re.search(r'<g id="accretion-dialect"([^>]*)>', svg)
    assert match, "Missing accretion dialect register"
    attrs = match.group(1)

    def _attr(name: str) -> str:
        found = re.search(rf'{re.escape(name)}="([^"]*)"', attrs)
        assert found, f"Missing {name} on accretion dialect"
        return found.group(1)

    return {
        "family": _attr("data-dialect"),
        "style": _attr("data-style"),
        "repos": int(_attr("data-accretion-repos")),
        "stars": int(_attr("data-accretion-stars")),
        "commits": int(_attr("data-accretion-commits")),
        "followers": int(_attr("data-accretion-followers")),
        "star_scale": float(_attr("data-accretion-star-scale")),
        "commit_scale": float(_attr("data-accretion-commit-scale")),
        "follower_scale": float(_attr("data-accretion-follower-scale")),
        "repo_scale": float(_attr("data-accretion-repo-scale")),
    }


def _channel_marks(svg: str, channel: str) -> int:
    match = re.search(
        rf'data-channel="{re.escape(channel)}"[^>]*data-mark-count="(\d+)"',
        svg,
    )
    assert match, f"Missing {channel} accretion marks"
    return int(match.group(1))


def test_repo_identity_seed_is_stable_when_list_order_changes() -> None:
    from scripts.art.shared.seeds import repo_identity_seed

    older = {"name": "agents", "created_at": "2024-01-01"}
    newer = {"name": "nbadb", "created_at": "2025-06-01"}
    first = repo_identity_seed(42, older)
    assert first == repo_identity_seed(
        42,
        {"name": "agents", "created_at": "2024-01-01"},
    )
    assert first != repo_identity_seed(42, newer)
    assert repo_identity_seed(42, older) == repo_identity_seed(
        42,
        {"name": "agents", "created_at": "2024-01-01", "stars": 99},
    )


def test_shared_daily_spine_from_account_creation_enforces_monotonic_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts.art import daily_snapshots as daily_snapshots_module
    from scripts.art.daily_snapshots import (
        build_daily_snapshots,
        sample_frames,
        validate_snapshot_monotonic_contract,
    )
    from scripts.art.timelapse import ALL_STYLES

    account_created = date(2024, 1, 1)
    terminal_day = date(2024, 1, 20)
    monkeypatch.setattr(
        daily_snapshots_module,
        "_timeline_end_day",
        lambda *, include_today: terminal_day,
    )
    history = {
        "account_created": f"{account_created.isoformat()}T00:00:00Z",
        "repos": [
            {"date": "2024-01-01", "name": "seed"},
            {"date": "2024-01-10", "name": "growth"},
        ],
        "stars": [
            {"date": "2024-01-04T10:00:00Z", "user": "a"},
            {"date": "2024-01-14T10:00:00Z", "user": "b"},
        ],
        "forks": [],
        "contributions_daily": {
            (account_created + timedelta(days=offset)).isoformat(): 2
            for offset in range(20)
        },
        "contributions_monthly": {"2024-01": 40},
    }
    metrics = {
        "followers": 24,
        "total_commits": 180,
        "languages": {"Python": 400},
        "top_repos": [
            {"name": "seed", "language": "Python", "stars": 8},
            {"name": "growth", "language": "Python", "stars": 5},
        ],
        "releases": [],
        "recent_merged_prs": [],
    }

    snapshots = build_daily_snapshots(history, metrics, include_today=True)
    expected_days = [
        account_created + timedelta(days=offset)
        for offset in range((terminal_day - account_created).days + 1)
    ]

    assert [snap.day for snap in snapshots] == expected_days
    assert snapshots[0].day == account_created
    assert snapshots[-1].day == terminal_day
    validate_snapshot_monotonic_contract(snapshots)

    sampled = sample_frames(snapshots, max_frames=8)
    validate_snapshot_monotonic_contract(sampled)
    sampled_days = [snap.day for snap in sampled]
    assert sampled[0].day == snapshots[0].day
    assert sampled[-1].day == snapshots[-1].day
    assert sampled_days == sorted(set(sampled_days))
    assert ALL_STYLES == [
        "inkgarden",
        "topo",
        "genetic",
        "physarum",
        "lenia",
        "ferrofluid",
    ]


@pytest.mark.parametrize(
    "style",
    ["inkgarden", "topo", "genetic", "physarum", "lenia", "ferrofluid"],
)
def test_style_dialects_make_accretion_readable(
    style: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.art.topography as topography_module
    from scripts.art.ferrofluid import generate as generate_ferrofluid
    from scripts.art.genetic_landscape import generate as generate_genetic
    from scripts.art.ink_garden import generate as generate_ink_garden
    from scripts.art.lenia import generate as generate_lenia
    from scripts.art.physarum import generate as generate_physarum
    from scripts.art.shared import STYLE_DIALECTS
    from scripts.art.topography import generate as generate_topography

    monkeypatch.setattr(topography_module, "TOPOGRAPHY_GRID_SIZE", 48)
    generators = {
        "inkgarden": generate_ink_garden,
        "topo": generate_topography,
        "genetic": generate_genetic,
        "physarum": generate_physarum,
        "lenia": generate_lenia,
        "ferrofluid": generate_ferrofluid,
    }
    frames = (
        _accretion_metrics(repos=1, stars=2, commits=20, followers=1),
        _accretion_metrics(repos=2, stars=24, commits=400, followers=18),
        _accretion_metrics(repos=4, stars=120, commits=2400, followers=80),
    )
    svgs = [
        generators[style](metrics, seed=f"{style}-dialect", timeline=False)
        for metrics in frames
    ]
    parsed = [_dialect_attrs(svg) for svg in svgs]

    assert [row["style"] for row in parsed] == [style, style, style]
    assert [row["family"] for row in parsed] == [STYLE_DIALECTS[style]] * 3
    assert [row["repos"] for row in parsed] == [1, 2, 4]
    assert [row["stars"] for row in parsed] == [2, 24, 120]
    assert [row["commits"] for row in parsed] == [20, 400, 2400]
    assert [row["followers"] for row in parsed] == [1, 18, 80]
    for channel in ("repos", "stars", "commits", "followers"):
        marks = [_channel_marks(svg, channel) for svg in svgs]
        assert marks == sorted(marks), f"{style} {channel} marks {marks}"
        assert marks[-1] > marks[0]
    assert parsed[0]["star_scale"] < parsed[1]["star_scale"] < parsed[2]["star_scale"]
    assert (
        parsed[0]["commit_scale"]
        < parsed[1]["commit_scale"]
        < parsed[2]["commit_scale"]
    )
    assert (
        parsed[0]["follower_scale"]
        < parsed[1]["follower_scale"]
        < parsed[2]["follower_scale"]
    )


def test_living_art_dialects_remain_visually_distinct(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.art.topography as topography_module
    from scripts.art.ferrofluid import generate as generate_ferrofluid
    from scripts.art.genetic_landscape import generate as generate_genetic
    from scripts.art.ink_garden import generate as generate_ink_garden
    from scripts.art.lenia import generate as generate_lenia
    from scripts.art.physarum import generate as generate_physarum
    from scripts.art.shared import STYLE_DIALECTS
    from scripts.art.topography import generate as generate_topography

    monkeypatch.setattr(topography_module, "TOPOGRAPHY_GRID_SIZE", 48)
    metrics = _accretion_metrics(repos=3, stars=40, commits=600, followers=22)
    generators = {
        "inkgarden": generate_ink_garden,
        "topo": generate_topography,
        "genetic": generate_genetic,
        "physarum": generate_physarum,
        "lenia": generate_lenia,
        "ferrofluid": generate_ferrofluid,
    }
    families = {
        style: _dialect_attrs(generator(metrics, seed=style, timeline=False))["family"]
        for style, generator in generators.items()
    }
    assert families == STYLE_DIALECTS
    assert len(set(families.values())) == 6


def _svg_root_attr(svg: str, name: str) -> str:
    match = re.search(rf"<svg\b[^>]*\b{re.escape(name)}=\"([^\"]*)\"", svg)
    assert match, f"Missing {name} on svg root"
    return match.group(1)


def _max_halo_radius(svg: str) -> float:
    radii = [
        float(radius)
        for radius in re.findall(
            r'data-role="lenia-seed-halo"[^>]*data-kind="repo"[^>]* r="([0-9.]+)"',
            svg,
        )
    ]
    if not radii:
        radii = [
            float(radius)
            for radius in re.findall(
                r'data-kind="repo"[^>]*data-role="lenia-seed-halo"[^>]* r="([0-9.]+)"',
                svg,
            )
        ]
    assert radii, "Missing repo Lenia halos"
    return max(radii)


def test_leased_style_knobs_track_isolated_channels(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.art.topography as topography_module
    from scripts.art.ferrofluid import generate as generate_ferrofluid
    from scripts.art.genetic_landscape import generate as generate_genetic
    from scripts.art.lenia import generate as generate_lenia
    from scripts.art.topography import generate as generate_topography

    monkeypatch.setattr(topography_module, "TOPOGRAPHY_GRID_SIZE", 48)

    def _render(generator, **counts: int) -> str:
        return generator(
            _accretion_metrics(**counts),
            seed="isolated-knobs",
            timeline=False,
        )

    base = {"repos": 2, "stars": 8, "commits": 40, "followers": 1}
    more_followers = {**base, "followers": 90}
    more_commits = {**base, "commits": 3200}
    more_stars = {**base, "stars": 180}

    topo_low = _render(generate_topography, **base)
    topo_high = _render(generate_topography, **more_followers)
    assert float(_svg_root_attr(topo_high, "data-settlement-scale")) > float(
        _svg_root_attr(topo_low, "data-settlement-scale")
    )
    assert int(_svg_root_attr(topo_high, "data-settlement-count")) > int(
        _svg_root_attr(topo_low, "data-settlement-count")
    )
    assert float(_svg_root_attr(topo_high, "data-settlement-gain")) > float(
        _svg_root_attr(topo_low, "data-settlement-gain")
    )

    genetic_low = _render(generate_genetic, **base)
    genetic_followers = _render(generate_genetic, **more_followers)
    genetic_commits = _render(generate_genetic, **more_commits)
    assert int(_svg_root_attr(genetic_followers, "data-colony-count")) > int(
        _svg_root_attr(genetic_low, "data-colony-count")
    )
    assert float(_svg_root_attr(genetic_followers, "data-colony-gain")) > float(
        _svg_root_attr(genetic_low, "data-colony-gain")
    )
    assert int(_svg_root_attr(genetic_commits, "data-generations")) > int(
        _svg_root_attr(genetic_low, "data-generations")
    )

    lenia_low = _render(generate_lenia, **base)
    lenia_stars = _render(generate_lenia, **more_stars)
    lenia_commits = _render(generate_lenia, **more_commits)
    lenia_followers = _render(generate_lenia, **more_followers)
    assert _max_halo_radius(lenia_stars) > _max_halo_radius(lenia_low)
    assert float(_svg_root_attr(lenia_stars, "data-halo-scale")) > float(
        _svg_root_attr(lenia_low, "data-halo-scale")
    )
    assert float(_svg_root_attr(lenia_commits, "data-field-gain")) > float(
        _svg_root_attr(lenia_low, "data-field-gain")
    )
    assert float(_svg_root_attr(lenia_commits, "data-simulation-mix")) > float(
        _svg_root_attr(lenia_low, "data-simulation-mix")
    )
    assert int(_svg_root_attr(lenia_commits, "data-sim-steps")) > int(
        _svg_root_attr(lenia_low, "data-sim-steps")
    )
    assert int(_svg_root_attr(lenia_followers, "data-satellite-count")) > int(
        _svg_root_attr(lenia_low, "data-satellite-count")
    )
    assert float(_svg_root_attr(lenia_followers, "data-extent-gain")) > float(
        _svg_root_attr(lenia_low, "data-extent-gain")
    )

    ferro_low = _render(generate_ferrofluid, **base)
    ferro_high = _render(generate_ferrofluid, **more_commits)
    ferro_low_match = re.search(r'data-ripple-count="(\d+)"', ferro_low)
    ferro_high_match = re.search(r'data-ripple-count="(\d+)"', ferro_high)
    assert ferro_low_match and ferro_high_match
    assert int(ferro_high_match.group(1)) > int(ferro_low_match.group(1))
    assert ferro_low.count('data-role="ferro-ripple"') > 0
    assert ferro_high.count('data-role="ferro-ripple"') > ferro_low.count(
        'data-role="ferro-ripple"'
    )
    assert float(_svg_root_attr(ferro_high, "data-ripple-gain")) > float(
        _svg_root_attr(ferro_low, "data-ripple-gain")
    )


def _count_inkgarden_plants(svg: str) -> int:
    return len(re.findall(r'<g class="repo-tree">', svg))


def _count_physarum_food_nodes(svg: str) -> int:
    return svg.count('data-role="physarum-node-core"')


def _ferro_dipole_xs(svg: str) -> list[float]:
    return [
        float(value)
        for value in re.findall(
            r'data-role="ferro-dipole"[^>]*\scx="([0-9.]+)"',
            svg,
        )
    ]


def _max_physarum_node_radius(svg: str) -> float:
    radii = [
        float(value)
        for value in re.findall(
            r'data-role="physarum-node-core"[^>]*\sr="([0-9.]+)"',
            svg,
        )
    ]
    assert radii, "Missing physarum food nodes"
    return max(radii)


def _count_inkgarden_fireflies(svg: str) -> int:
    match = re.search(r'<g id="fireflies">(.*?)</g>', svg, flags=re.DOTALL)
    if match is None:
        return 0
    return match.group(1).count("<circle")


def test_early_spine_dialects_keep_repo_accretion_readable() -> None:
    from scripts.art.ferrofluid import generate as generate_ferrofluid
    from scripts.art.ink_garden import generate as generate_ink_garden
    from scripts.art.physarum import generate as generate_physarum

    frames = (
        _accretion_metrics(repos=1, stars=2, commits=20, followers=1),
        _accretion_metrics(repos=2, stars=24, commits=400, followers=18),
        _accretion_metrics(repos=4, stars=120, commits=2400, followers=80),
    )
    ink_svgs = [
        generate_ink_garden(metrics, seed="ink-accretion", timeline=False)
        for metrics in frames
    ]
    phys_svgs = [
        generate_physarum(metrics, seed="phys-accretion", timeline=False)
        for metrics in frames
    ]
    ferro_svgs = [
        generate_ferrofluid(metrics, seed="ferro-accretion", timeline=False)
        for metrics in frames
    ]

    ink_plants = [_count_inkgarden_plants(svg) for svg in ink_svgs]
    phys_nodes = [_count_physarum_food_nodes(svg) for svg in phys_svgs]
    assert ink_plants[0] >= 1
    assert phys_nodes[0] >= 1
    assert ink_plants == sorted(ink_plants)
    assert phys_nodes == sorted(phys_nodes)
    assert ink_plants[-1] > ink_plants[0]
    assert phys_nodes[-1] > phys_nodes[0]

    t2_xs = _ferro_dipole_xs(ferro_svgs[-1])
    assert len(t2_xs) == 4
    ordered = sorted(t2_xs)
    gaps = [right - left for left, right in zip(ordered, ordered[1:])]
    assert min(gaps) >= 36.0


def test_ink_and_physarum_knobs_track_stars_and_followers() -> None:
    from scripts.art.ink_garden import generate as generate_ink_garden
    from scripts.art.physarum import generate as generate_physarum

    base = {"repos": 2, "stars": 8, "commits": 40, "followers": 1}
    more_followers = {**base, "followers": 90}
    more_stars = {**base, "stars": 180}

    ink_low = generate_ink_garden(
        _accretion_metrics(**base), seed="ink-knobs", timeline=False
    )
    ink_followers = generate_ink_garden(
        _accretion_metrics(**more_followers), seed="ink-knobs", timeline=False
    )
    assert _count_inkgarden_fireflies(ink_followers) > _count_inkgarden_fireflies(
        ink_low
    )

    phys_low = generate_physarum(
        _accretion_metrics(**base), seed="phys-knobs", timeline=False
    )
    phys_stars = generate_physarum(
        _accretion_metrics(**more_stars), seed="phys-knobs", timeline=False
    )
    assert _max_physarum_node_radius(phys_stars) > _max_physarum_node_radius(phys_low)
