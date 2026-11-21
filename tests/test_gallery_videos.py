"""Verify the assembler and finalizer transfer GIF/film pairs from one run."""

from pathlib import Path

import pytest

from scripts.art.artifacts import publish_gallery_videos, stage_gallery_videos
from scripts.art.roster import SHIPPED_STYLE_KEYS


@pytest.mark.parametrize(
    "defect", ["healthy", "missing", "swapped", "old-gif", "unknown", "incomplete-mp4"]
)
def test_video_transfer(tmp_path: Path, defect: str) -> None:
    parts, stage, target = (tmp_path / d for d in ("parts", "stage", "out"))
    parts.mkdir()
    target.mkdir()
    films = [f"living-{style}.mp4" for style in SHIPPED_STYLE_KEYS]
    for name in films:
        (parts / name).write_bytes(b"\x00\x00\x00\x20ftypisom" + name.encode())
        (parts / name).with_suffix(".gif").write_bytes(b"GIF89a" + name.encode())
        (target / name).write_bytes(b"existing")
    if defect == "incomplete-mp4":
        (parts / films[0]).write_bytes(b"error")
        with pytest.raises(ValueError, match="MP4 header"):
            stage_gallery_videos(parts, stage)
        assert not stage.exists()
        return
    stage_gallery_videos(parts, stage)
    if defect == "missing":
        (stage / films[0]).unlink()
    elif defect == "swapped":
        (stage / films[0]).write_bytes((stage / films[1]).read_bytes())
    elif defect == "old-gif":
        (parts / films[0]).with_suffix(".gif").write_bytes(b"stale GIF")
    elif defect == "unknown":
        (stage / "extra").touch()
    if defect != "healthy":
        with pytest.raises(ValueError):
            publish_gallery_videos(parts, stage, target)
        assert all((target / name).read_bytes() == b"existing" for name in films)
        return
    for _ in range(2):
        publish_gallery_videos(parts, stage, target)
        assert all(
            (target / name).read_bytes() == (parts / name).read_bytes()
            for name in films
        )
