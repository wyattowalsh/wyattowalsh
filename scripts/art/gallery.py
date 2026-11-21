"""Publish the GitHub Markdown gallery and its motion-safe final-frame previews."""

from __future__ import annotations

import fcntl
import os
from contextlib import ExitStack
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL.GifImagePlugin import GifImageFile

from .artifacts import verify_published_gifs
from .roster import SHIPPED_STYLE_KEYS, shipped_legends

_IMAGE_DIR = Path(".github/assets/img")
_STILLS_DIR = _IMAGE_DIR / "living-stills"
_GALLERY = Path("LIVING_ART.md")
# The reviewed six-frame baseline was 233 kB. Allow some headroom at 400 x 400.
MAX_JPEG_BYTES = 72_000
MAX_TOTAL_JPEG_BYTES = 300_000
_PREVIEWS = {
    "inkgarden": (
        "Read the garden",
        "Repositories grow into trees, with thicker trunks for commits "
        "and flowers for stars.",
    ),
    "topo": (
        "Read the map",
        "Hills mark repositories on a contour map. Stars give the summits height.",
    ),
    "genetic": (
        "Read the landscape",
        "Repositories form fitness peaks, with generations stacked "
        "across the landscape.",
    ),
    "physarum": (
        "Read the vein network",
        "A branching network of veins joins the food nodes "
        "that represent repositories.",
    ),
    "lenia": (
        "Read the living field",
        "Each repository seeds an organism in a continuous field. "
        "Followers influence how far it spreads.",
    ),
    "ferrofluid": (
        "Read the magnetic field",
        "Each repository forms a magnetic tower. "
        "Stars lift the spikes and commits send ripples through the pool.",
    ),
}


def render_gallery() -> str:
    """Compose the gallery in shipped roster order, including each signal legend."""
    legends = shipped_legends()
    profile = "[Back to Wyatt’s profile](README.md#wyatt-walsh)"
    index = " · ".join(
        f"[{legend.title}](#{legend.title.lower().replace(' ', '-')})"
        for _, legend in legends
    )
    lines = [
        "# Living Art",
        "",
        profile,
        "",
        "Six timelapses trace my GitHub history. Each frame shows the account "
        "up to one sampled day. A new repository can take root as a tree in "
        "one film and rise as a hill in another.",
        "",
        index,
        "",
    ]
    for style, legend in legends:
        title = legend.title
        summary, alt = _PREVIEWS[style]
        gif = _IMAGE_DIR / f"living-{style}.gif"
        mp4 = gif.with_suffix(".mp4")
        still = _STILLS_DIR / gif.with_suffix(".jpg").name
        lines.extend(
            [
                f"## {title}",
                "",
                legend.metaphor,
                "",
                "<details open>",
                f"<summary>Show or hide the {title} preview</summary>",
                "",
                f'<p><a href="{mp4}"><picture>',
                '  <source media="(prefers-reduced-motion: no-preference)" '
                f'srcset="{gif}">',
                f'  <img src="{still}" width="400" height="400" '
                f'alt="{alt} Open {title} as an MP4.">',
                "</picture></a></p>",
                "",
                "</details>",
                "",
                f"[Watch {title} (MP4)]({mp4}) · [Open GIF]({gif})",
                "",
                "<details>",
                f"<summary>{summary}</summary>",
                "",
                *(
                    f"- **{signal.title()}:** {mapping}"
                    for signal, mapping in legend.mapping.model_dump().items()
                ),
                "",
                "</details>",
                "",
            ]
        )
    lines.extend([f"[Back to the gallery index](#living-art) · {profile}", ""])
    return "\n".join(lines)


def _final_frame(path: Path, digest: str) -> bytes:
    # Decode the very bytes we hashed so an input replacement cannot mislabel a JPEG.
    source = path.read_bytes()
    if sha256(source).hexdigest() != digest:
        raise ValueError(
            f"Gallery source changed during preview generation: {path.name}"
        )
    output = BytesIO()
    with GifImageFile(BytesIO(source)) as gif:
        gif.seek(gif.n_frames - 1)
        gif.convert("RGB").save(
            output,
            format="JPEG",
            quality=86,
            subsampling=0,
            optimize=True,
            comment=f"{path.name} sha256={digest}".encode("ascii"),
        )
    content = output.getvalue()
    if len(content) > MAX_JPEG_BYTES:
        raise ValueError(f"Gallery JPEG exceeds {MAX_JPEG_BYTES} bytes: {path.name}")
    return content


def _publish(root: Path) -> None:
    images = root / _IMAGE_DIR
    stills = root / _STILLS_DIR
    gallery = root / _GALLERY
    if any(
        (root / directory).is_symlink()
        for directory in (_IMAGE_DIR, *_IMAGE_DIR.parents)
    ):
        raise ValueError("Gallery image directory must not pass through a symlink")
    if stills.is_symlink() or (stills.exists() and not stills.is_dir()):
        raise ValueError(f"Expected a regular gallery stills directory: {stills}")
    if gallery.is_symlink() or (gallery.exists() and not gallery.is_file()):
        raise ValueError(f"Expected a regular gallery Markdown file: {gallery}")
    expected_stills = {f"living-{style}.jpg" for style in SHIPPED_STYLE_KEYS}
    if stills.exists():
        for entry in stills.iterdir():
            if (
                entry.name not in expected_stills
                or entry.is_symlink()
                or not entry.is_file()
            ):
                raise ValueError(f"Unexpected gallery stills entry: {entry.name}")

    hashes = verify_published_gifs(images)
    outputs: dict[Path, bytes] = {}
    for style in SHIPPED_STYLE_KEYS:
        gif = images / f"living-{style}.gif"
        film = gif.with_suffix(".mp4")
        if film.is_symlink() or not film.is_file() or not film.stat().st_size:
            raise ValueError(f"Missing regular MP4 link destination: {film.name}")
        outputs[stills / gif.with_suffix(".jpg").name] = _final_frame(
            gif, hashes[gif.name]
        )
    if sum(map(len, outputs.values())) > MAX_TOTAL_JPEG_BYTES:
        raise ValueError(
            f"Gallery stills exceed the {MAX_TOTAL_JPEG_BYTES} byte fleet budget"
        )
    outputs[gallery] = render_gallery().encode("utf-8")

    # All seven outputs have validated before touching any destination. Other
    # publishers of this gallery wait on its stable root-directory lock.
    with (
        TemporaryDirectory(prefix=".gallery-", dir=root) as scratch,
        ExitStack() as rollback,
    ):
        stage = Path(scratch)
        if not stills.exists():
            stills.mkdir()
            rollback.callback(stills.rmdir)
        for target, content in outputs.items():
            if target.exists() and target.read_bytes() == content:
                continue
            staged = stage / target.name
            staged.write_bytes(content)
            if target.exists():
                backup = staged.with_suffix(".previous")
                os.link(target, backup)
                staged.replace(target)
                rollback.callback(backup.replace, target)
            else:
                staged.replace(target)
                rollback.callback(target.unlink)
            if target.read_bytes() != content:
                raise OSError(f"Gallery publication readback failed: {target.name}")
        rollback.pop_all()


def publish_gallery(root: Path = Path(".")) -> None:
    """Generate only the Markdown and six stills from the completed published fleet."""
    root = root.resolve(strict=True)
    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        _publish(root)
    finally:
        os.close(descriptor)


if __name__ == "__main__":
    publish_gallery()
