import json
from pathlib import Path

import pytest

pytest.importorskip(
    "numpy", reason="scripts.art.animate imports scripts.art.ink_garden"
)

from scripts.art import animate  # noqa: E402
from scripts.art.artifacts import sync_living_art_artifacts  # noqa: E402


def _stub_svg() -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        "<defs><linearGradient id=\"grad\"><stop offset=\"0%\" "
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
        animate.sys,
        "argv",
        ["animate", "--svg", "--frames", "4", "--profile", "wyatt"],
    )

    animate.main()

    output_dir = tmp_path / ".github" / "assets" / "img"
    inkgarden = output_dir / "inkgarden-growth-animated.svg"
    topography = output_dir / "topo-growth-animated.svg"

    assert inkgarden.is_file(), f"Missing expected animated artifact: {inkgarden}"
    assert topography.is_file(), f"Missing expected animated artifact: {topography}"

    inkgarden_svg = inkgarden.read_text(encoding="utf-8")
    topography_svg = topography.read_text(encoding="utf-8")
    for svg in (inkgarden_svg, topography_svg):
        assert "Narrative growth animation: 3-act timing" in svg
        assert svg.count('<g class="f f') == 4


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
    for name, payload in {
        "inkgarden-growth-animated.svg": "<svg />",
        "inkgarden-growth.gif": "GIF89a",
        "topo-growth-animated.svg": "<svg />",
        "living-topo.gif": "GIF89a",
    }.items():
        path = tmp_path / name
        if name.endswith(".gif"):
            path.write_bytes(payload.encode())
        else:
            path.write_text(payload, encoding="utf-8")

    manifest_path, gallery_path, manifest = sync_living_art_artifacts(tmp_path)
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    gallery = gallery_path.read_text(encoding="utf-8")

    assert manifest == manifest_data
    assert manifest_data["counts"] == {
        "source_svg": 2,
        "compatibility_gif": 1,
        "timelapse_gif": 1,
    }
    assert manifest_data["total_assets"] == 4
    assert any(
        asset["name"] == "inkgarden-growth-animated.svg"
        for asset in manifest_data["assets"]
    )
    assert "Living Art Preview Gallery" in gallery
    assert "inkgarden-growth-animated.svg" in gallery
    assert "living-topo.gif" in gallery

