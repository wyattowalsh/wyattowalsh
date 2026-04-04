import json
from pathlib import Path

import pytest

pytest.importorskip(
    "numpy", reason="scripts.art.animate imports scripts.art.ink_garden"
)

from scripts.art import animate  # noqa: E402
from scripts.art.artifacts import (  # noqa: E402
    LIVING_ART_STYLE_KEYS,
    sync_living_art_artifacts,
)


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
    topo_calls: list[dict] = []

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
            out_path.write_bytes(b"GIF89a")

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
    topo_calls: list[dict] = []

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
        (tmp_path / f"living-{style}.gif").write_bytes(b"GIF89a")

    manifest_path, gallery_path, manifest = sync_living_art_artifacts(tmp_path)
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    gallery = gallery_path.read_text(encoding="utf-8")

    assert manifest == manifest_data
    assert manifest_data["counts"] == {
        "timelapse_gif": 6,
    }
    assert manifest_data["total_assets"] == 6
    assert all(asset["channel"] == "timelapse_gif" for asset in manifest_data["assets"])
    actual_styles = {a["style"] for a in manifest_data["assets"]}
    assert actual_styles == set(LIVING_ART_STYLE_KEYS)
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
        (source_dir / f"living-{style}.gif").write_bytes(b"GIF89a")

    # Legacy showcase collateral should survive the public mirror refresh.
    (public_dir / "inkgarden-growth.gif").write_bytes(b"GIF89a")
    (public_dir / "living-old.gif").write_bytes(b"GIF89a")

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
