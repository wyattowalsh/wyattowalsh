"""Contracts for the Markdown gallery and its final-frame JPEGs."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path

import pytest
from PIL import Image

from scripts.art import gallery
from scripts.art.artifacts import MANIFEST_FILENAME, build_living_art_manifest
from scripts.art.roster import SHIPPED_STYLE_KEYS

IMAGE_DIR = Path(".github/assets/img")
STILLS_DIR = IMAGE_DIR / "living-stills"


def _write_manifest(images: Path) -> None:
    manifest = build_living_art_manifest(images)
    (images / MANIFEST_FILENAME).write_text(json.dumps(manifest), encoding="utf-8")


@pytest.fixture
def fleet(tmp_path: Path) -> Path:
    images = tmp_path / IMAGE_DIR
    images.mkdir(parents=True)
    for index, style in enumerate(SHIPPED_STYLE_KEYS):
        first = Image.new("RGB", (400, 400), (20, 22, 24))
        last = Image.new("RGB", (400, 400), (10, 90, 150 + index))
        gif = images / f"living-{style}.gif"
        first.save(gif, save_all=True, append_images=[last], duration=12000, loop=0)
        gif.with_suffix(".mp4").write_bytes(b"linked fixture")
    _write_manifest(images)
    return tmp_path


def _outputs(root: Path) -> dict[str, bytes]:
    paths = list((root / STILLS_DIR).glob("*"))
    if (root / "LIVING_ART.md").exists():
        paths.append(root / "LIVING_ART.md")
    return {path.name: path.read_bytes() for path in paths}


def test_gallery_publication_refreshes_stills_and_repeats_without_writes(
    fleet: Path,
) -> None:
    images = fleet / IMAGE_DIR
    protected = {p: p.read_bytes() for p in images.iterdir()}
    with ThreadPoolExecutor(max_workers=2) as workers:
        list(workers.map(gallery.publish_gallery, [fleet, fleet]))
    assert _outputs(fleet).keys() == {
        "LIVING_ART.md",
        *(f"living-{key}.jpg" for key in SHIPPED_STYLE_KEYS),
    }
    assert protected == {p: p.read_bytes() for p in protected}
    times = {p: p.stat().st_mtime_ns for p in (fleet / STILLS_DIR).iterdir()}
    times[fleet / "LIVING_ART.md"] = (fleet / "LIVING_ART.md").stat().st_mtime_ns
    gallery.publish_gallery(fleet)
    assert times == {p: p.stat().st_mtime_ns for p in times}
    assert not list(fleet.glob(".gallery-*"))

    for index, style in enumerate(SHIPPED_STYLE_KEYS):
        gif = images / f"living-{style}.gif"
        digest = sha256(protected[gif]).hexdigest()
        with Image.open(fleet / STILLS_DIR / f"living-{style}.jpg") as frame:
            assert frame.format == "JPEG" and frame.size == (400, 400)
            assert frame.info["comment"] == f"{gif.name} sha256={digest}".encode()
            assert frame.convert("RGB").getpixel((0, 0)) == pytest.approx(
                (10, 90, 150 + index), abs=2
            )

    # A GIF comment changes the source digest without changing final-frame pixels.
    source = images / "living-topo.gif"
    changed = protected[source][:-1] + bytes.fromhex("21 fe 02 76 32 00 3b")
    source.write_bytes(changed)
    _write_manifest(images)
    before = _outputs(fleet)
    gallery.publish_gallery(fleet)
    after = _outputs(fleet)
    changed_files = {name for name in before if before[name] != after[name]}
    assert changed_files == {"living-topo.jpg"}
    with Image.open(fleet / STILLS_DIR / "living-topo.jpg") as jpeg:
        assert sha256(changed).hexdigest().encode() in jpeg.info["comment"]


@pytest.mark.parametrize(
    "invalid",
    [
        "manifest",
        "missing-gif",
        "extra-gif",
        "missing-film",
        "symlink-manifest",
        "symlink-gallery",
        "symlink-stills",
        "symlink-image-dir",
        "mixed-stills",
        "jpeg-budget",
        "total-budget",
        "input-changed",
    ],
)
def test_invalid_gallery_inputs_leave_publications_untouched(
    fleet: Path, monkeypatch: pytest.MonkeyPatch, invalid: str
) -> None:
    images = fleet / IMAGE_DIR
    stills = fleet / STILLS_DIR
    stills.mkdir()
    (stills / "living-topo.jpg").write_bytes(b"previous")
    (fleet / "LIVING_ART.md").write_text("previous gallery")
    manifest = images / MANIFEST_FILENAME
    if invalid == "manifest":
        contents = json.loads(manifest.read_bytes())
        contents["assets"][0]["sha256"] = "0" * 64
        manifest.write_text(json.dumps(contents))
    elif invalid == "missing-gif":
        (images / "living-lenia.gif").unlink()
    elif invalid == "extra-gif":
        (images / "living-unknown.gif").touch()
    elif invalid == "missing-film":
        (images / "living-lenia.mp4").unlink()
    elif invalid == "symlink-manifest":
        manifest.rename(images / "other.json")
        manifest.symlink_to(images / "other.json")
    elif invalid == "symlink-gallery":
        (fleet / "LIVING_ART.md").rename(fleet / "other.md")
        (fleet / "LIVING_ART.md").symlink_to(fleet / "other.md")
    elif invalid == "symlink-stills":
        stills.rename(images / "other")
        stills.symlink_to(images / "other")
    elif invalid == "symlink-image-dir":
        images.rename(images.with_name("other"))
        images.symlink_to(images.with_name("other"))
    elif invalid == "mixed-stills":
        (stills / "unexpected.jpg").write_bytes(b"keep")
    elif invalid == "jpeg-budget":
        monkeypatch.setattr(gallery, "MAX_JPEG_BYTES", 1)
    elif invalid == "total-budget":
        monkeypatch.setattr(gallery, "MAX_TOTAL_JPEG_BYTES", 1)
    else:
        monkeypatch.setattr(
            gallery,
            "verify_published_gifs",
            lambda _: {f"living-{style}.gif": "0" * 64 for style in SHIPPED_STYLE_KEYS},
        )
    before = _outputs(fleet)
    with pytest.raises(ValueError):
        gallery.publish_gallery(fleet)
    assert before == _outputs(fleet)
    assert not list(fleet.glob(".gallery-*"))


@pytest.mark.parametrize("prior", ["none", "partial"])
def test_gallery_restores_prior_outputs_on_write_failure(
    fleet: Path, monkeypatch: pytest.MonkeyPatch, prior: str
) -> None:
    stills = fleet / STILLS_DIR
    if prior == "partial":
        stills.mkdir()
        (stills / "living-inkgarden.jpg").write_bytes(b"previous")
        (fleet / "LIVING_ART.md").write_text("previous")
    before = _outputs(fleet)
    replace = Path.replace

    def fail_last(staged: Path, target: Path) -> Path:
        if staged.name == "LIVING_ART.md":
            raise OSError("injected gallery write failure")
        return replace(staged, target)

    monkeypatch.setattr(Path, "replace", fail_last)
    with pytest.raises(OSError, match="injected"):
        gallery.publish_gallery(fleet)
    assert _outputs(fleet) == before
    assert stills.exists() == (prior == "partial")
    assert not list(fleet.glob(".gallery-*"))
