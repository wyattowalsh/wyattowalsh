"""Lossless GIF optimization and same-host transactional publication.

Repository-owned writers coordinate through a stable per-output ``flock`` node.
They build and optionally optimize a private same-directory stage, then publish
it with one atomic rename. Readers therefore observe the old or new complete
GIF, never an in-place partial write.

The lock is advisory and local to one host. A final revision comparison catches
non-cooperating changes observed before publication, but macOS and Linux expose
no portable expected-version compare-and-replace primitive. Consequently, an
unrelated process that ignores the lock can still race in the narrow interval
between that comparison and ``os.replace``. Publication is process-crash safe;
this module does not claim power-loss durability or multi-host/NFS exclusion.
"""

from __future__ import annotations

import fcntl
import hashlib
import io
import math
import os
import shutil
import stat
import subprocess
import tempfile
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from PIL import Image, UnidentifiedImageError

from ..utils import get_logger

logger = get_logger(module=__name__)

_GIFSICLE_TIMEOUT_SECONDS = 180
_GIF_OUTPUT_LOCK_TIMEOUT_SECONDS = 240.0
_GIF_OUTPUT_LOCK_POLL_SECONDS = 0.05
_GIF_OUTPUT_DEFAULT_MODE = 0o644
_PUBLISH_STAGE_SUFFIX = ".publish.tmp"
_GIFSICLE_CANDIDATE_SUFFIX = ".gifsicle.tmp"


@dataclass(frozen=True, slots=True)
class _GifFingerprint:
    """Byte and rendered-frame identity for one GIF file."""

    byte_size: int
    file_sha256: str
    dimensions: tuple[int, int]
    frame_count: int
    durations_ms: tuple[int, ...]
    loop: int | None
    frame_sha256: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _GifOptimizationResult:
    """Auditable outcome from one optional GIF optimization attempt."""

    replaced: bool
    reason: str
    source_size: int
    output_size: int
    source_sha256: str
    output_sha256: str


@dataclass(frozen=True, slots=True)
class _GifOutputRevision:
    """Best-effort identity and content revision for a public output path."""

    exists: bool
    device: int | None = None
    inode: int | None = None
    size: int | None = None
    mtime_ns: int | None = None
    mode: int | None = None
    sha256: str | None = None


class _ConcurrentGifOutputError(RuntimeError):
    """The public GIF changed during a staged publication transaction."""


class _GifOutputLockTimeout(TimeoutError):
    """The per-output publication lock was not acquired before its deadline."""


class _UnsafeGifOutputError(OSError):
    """A publication path or lock node violates the regular-file contract."""


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(file_path: Path) -> str:
    digest = hashlib.sha256()
    with file_path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_open_file(file_obj: BinaryIO) -> str:
    """Hash a binary file object from its beginning without closing it."""
    digest = hashlib.sha256()
    file_obj.seek(0)
    for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
        digest.update(chunk)
    return digest.hexdigest()


def _resolve_logical_output(output_path: Path) -> Path:
    """Return a stable logical path without following the final component."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_parent = output_path.parent.resolve(strict=True)
    if not resolved_parent.is_dir():
        raise _UnsafeGifOutputError(
            f"GIF output parent is not a directory: {resolved_parent}"
        )
    return resolved_parent / output_path.name


def _gif_output_revision(output_path: Path) -> _GifOutputRevision:
    """Capture one stable best-effort revision without following symlinks."""
    try:
        path_before = output_path.lstat()
    except FileNotFoundError:
        return _GifOutputRevision(exists=False)

    if not stat.S_ISREG(path_before.st_mode):
        raise _UnsafeGifOutputError(
            f"GIF output must be a regular file, not a symlink or special node: "
            f"{output_path}"
        )

    open_flags = os.O_RDONLY | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(output_path, open_flags)
    except FileNotFoundError as exc:
        raise _ConcurrentGifOutputError(
            f"GIF output changed while its revision was captured: {output_path}"
        ) from exc
    except OSError as exc:
        raise _UnsafeGifOutputError(
            f"Unable to open GIF output without following links: {output_path}"
        ) from exc

    with os.fdopen(descriptor, "rb") as file_obj:
        descriptor_before = os.fstat(file_obj.fileno())
        if not stat.S_ISREG(descriptor_before.st_mode):
            raise _UnsafeGifOutputError(
                f"GIF output descriptor is not a regular file: {output_path}"
            )
        digest = _sha256_open_file(file_obj)
        descriptor_after = os.fstat(file_obj.fileno())
        try:
            path_after = output_path.lstat()
        except FileNotFoundError as exc:
            raise _ConcurrentGifOutputError(
                f"GIF output changed while its revision was captured: {output_path}"
            ) from exc

    stable_identity = (
        path_before.st_dev,
        path_before.st_ino,
        path_before.st_size,
        path_before.st_mtime_ns,
    )
    if (
        stable_identity
        != (
            descriptor_before.st_dev,
            descriptor_before.st_ino,
            descriptor_before.st_size,
            descriptor_before.st_mtime_ns,
        )
        or stable_identity
        != (
            descriptor_after.st_dev,
            descriptor_after.st_ino,
            descriptor_after.st_size,
            descriptor_after.st_mtime_ns,
        )
        or stable_identity
        != (
            path_after.st_dev,
            path_after.st_ino,
            path_after.st_size,
            path_after.st_mtime_ns,
        )
        or not stat.S_ISREG(path_after.st_mode)
    ):
        raise _ConcurrentGifOutputError(
            f"GIF output changed while its revision was captured: {output_path}"
        )

    return _GifOutputRevision(
        exists=True,
        device=descriptor_after.st_dev,
        inode=descriptor_after.st_ino,
        size=descriptor_after.st_size,
        mtime_ns=descriptor_after.st_mtime_ns,
        mode=stat.S_IMODE(descriptor_after.st_mode),
        sha256=digest,
    )


def _open_gif_output_lock(output_path: Path) -> tuple[int, Path]:
    """Open the stable, private lock node for one logical output path."""
    effective_user_id = os.geteuid()
    lock_root = Path(tempfile.gettempdir()) / (
        f"wyattowalsh-gif-locks-{effective_user_id}"
    )
    lock_root.mkdir(mode=0o700, exist_ok=True)

    directory_flags = (
        os.O_RDONLY
        | os.O_CLOEXEC
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        directory_descriptor = os.open(lock_root, directory_flags)
    except OSError as exc:
        raise _UnsafeGifOutputError(
            f"Unable to open GIF lock directory securely: {lock_root}"
        ) from exc

    try:
        root_status = os.fstat(directory_descriptor)
        if (
            not stat.S_ISDIR(root_status.st_mode)
            or root_status.st_uid != effective_user_id
            or stat.S_IMODE(root_status.st_mode) & 0o077
        ):
            raise _UnsafeGifOutputError(
                f"GIF lock directory must be user-owned and private: {lock_root}"
            )

        lock_key = hashlib.sha256(os.fsencode(output_path)).hexdigest()
        lock_name = f"{lock_key}.lock"
        lock_flags = (
            os.O_CREAT | os.O_RDWR | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)
        )
        try:
            lock_descriptor = os.open(
                lock_name,
                lock_flags,
                0o600,
                dir_fd=directory_descriptor,
            )
        except OSError as exc:
            raise _UnsafeGifOutputError(
                f"Unable to open GIF lock node securely: {lock_root / lock_name}"
            ) from exc
    finally:
        os.close(directory_descriptor)

    try:
        lock_status = os.fstat(lock_descriptor)
        lock_is_safe = (
            stat.S_ISREG(lock_status.st_mode)
            and lock_status.st_uid == effective_user_id
            and not stat.S_IMODE(lock_status.st_mode) & 0o077
        )
    except BaseException:
        os.close(lock_descriptor)
        raise
    if not lock_is_safe:
        os.close(lock_descriptor)
        raise _UnsafeGifOutputError(
            f"GIF lock node must be a user-owned private regular file: "
            f"{lock_root / lock_name}"
        )
    return lock_descriptor, lock_root / lock_name


@contextmanager
def _locked_gif_output(
    output_path: Path,
    *,
    timeout_seconds: float,
) -> Iterator[None]:
    """Hold the stable advisory lock for one logical output."""
    if not math.isfinite(timeout_seconds) or timeout_seconds < 0:
        raise ValueError("GIF output lock timeout must be finite and non-negative")

    lock_descriptor, lock_path = _open_gif_output_lock(output_path)
    deadline = time.monotonic() + timeout_seconds
    acquired = False
    try:
        while True:
            try:
                fcntl.flock(lock_descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except InterruptedError:
                continue
            except BlockingIOError as exc:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise _GifOutputLockTimeout(
                        f"Timed out after {timeout_seconds:.3f}s waiting to publish "
                        f"{output_path} via {lock_path}"
                    ) from exc
                time.sleep(min(_GIF_OUTPUT_LOCK_POLL_SECONDS, remaining))

        yield
    finally:
        try:
            if acquired:
                fcntl.flock(lock_descriptor, fcntl.LOCK_UN)
        finally:
            os.close(lock_descriptor)


def _is_abandoned_gif_stage(name: str, *, output_name: str) -> bool:
    """Return whether a filename belongs to this output's private transaction."""
    stage_prefix = f".{output_name}."
    return name.startswith(stage_prefix) and (
        name.endswith(_PUBLISH_STAGE_SUFFIX)
        or (
            f"{_PUBLISH_STAGE_SUFFIX}." in name
            and name.endswith(_GIFSICLE_CANDIDATE_SUFFIX)
        )
    )


def _clean_abandoned_gif_stages(output_path: Path) -> None:
    """Remove only transaction-owned stale stages while holding the output lock."""
    for child in output_path.parent.iterdir():
        if not _is_abandoned_gif_stage(child.name, output_name=output_path.name):
            continue
        try:
            child_status = child.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISREG(child_status.st_mode) or stat.S_ISLNK(child_status.st_mode):
            child.unlink(missing_ok=True)


def _unlink_private_stage(stage_path: Path) -> None:
    """Unlink only the regular file or symlink created for this transaction."""
    try:
        stage_status = stage_path.lstat()
    except FileNotFoundError:
        return
    if stat.S_ISREG(stage_status.st_mode) or stat.S_ISLNK(stage_status.st_mode):
        stage_path.unlink(missing_ok=True)


@contextmanager
def _gif_output_transaction(
    output_path: Path,
    *,
    lock_timeout_seconds: float = _GIF_OUTPUT_LOCK_TIMEOUT_SECONDS,
) -> Iterator[Path]:
    """Build privately and atomically publish one complete GIF.

    All repository-owned writers of ``output_path`` must use this transaction.
    The stable advisory lock serializes those writers on one host. A revision
    comparison rejects a non-cooperating change observed before the public
    rename, but cannot turn portable ``os.replace`` into a filesystem CAS.
    """
    logical_output = _resolve_logical_output(output_path)
    with _locked_gif_output(
        logical_output,
        timeout_seconds=lock_timeout_seconds,
    ):
        initial_revision = _gif_output_revision(logical_output)
        _clean_abandoned_gif_stages(logical_output)
        stage_descriptor, stage_name = tempfile.mkstemp(
            prefix=f".{logical_output.name}.",
            suffix=_PUBLISH_STAGE_SUFFIX,
            dir=logical_output.parent,
        )
        os.close(stage_descriptor)
        stage_path = Path(stage_name)

        try:
            yield stage_path
            stage_revision = _gif_output_revision(stage_path)
            if not stage_revision.exists:
                raise _UnsafeGifOutputError(
                    f"Private GIF stage disappeared before validation: {stage_path}"
                )
            stage_fingerprint = _gif_fingerprint(stage_path)
            verified_stage_revision = _gif_output_revision(stage_path)
            if (
                verified_stage_revision != stage_revision
                or verified_stage_revision.sha256 != stage_fingerprint.file_sha256
            ):
                raise _ConcurrentGifOutputError(
                    f"Private GIF stage changed during validation: {stage_path}"
                )

            current_revision = _gif_output_revision(logical_output)
            if current_revision != initial_revision:
                raise _ConcurrentGifOutputError(
                    f"GIF output changed before publication; retaining current file: "
                    f"{logical_output}"
                )

            output_mode = (
                initial_revision.mode
                if initial_revision.mode is not None
                else _GIF_OUTPUT_DEFAULT_MODE
            )
            os.chmod(stage_path, output_mode)
            os.replace(stage_path, logical_output)
        finally:
            _unlink_private_stage(stage_path)


def _gif_fingerprint(file_path: Path) -> _GifFingerprint:
    """Fingerprint GIF bytes and every fully composited RGBA frame."""
    payload = file_path.read_bytes()
    try:
        with Image.open(io.BytesIO(payload)) as image:
            if image.format != "GIF":
                raise ValueError(f"Not a GIF image: {file_path}")

            dimensions = image.size
            frame_count = int(getattr(image, "n_frames", 1))
            loop_value = image.info.get("loop")
            loop = int(loop_value) if isinstance(loop_value, (int, float)) else None
            durations: list[int] = []
            frame_hashes: list[str] = []

            for frame_index in range(frame_count):
                image.seek(frame_index)
                duration_value = image.info.get("duration", 0)
                duration = (
                    int(duration_value)
                    if isinstance(duration_value, (int, float))
                    else 0
                )
                rgba_frame = image.convert("RGBA")
                if rgba_frame.size != dimensions:
                    raise ValueError(
                        f"GIF frame {frame_index} has unexpected dimensions: "
                        f"{rgba_frame.size} != {dimensions}"
                    )
                durations.append(duration)
                frame_hashes.append(_sha256_bytes(rgba_frame.tobytes()))
    except (EOFError, OSError, UnidentifiedImageError) as exc:
        raise ValueError(f"Unable to decode GIF: {file_path}") from exc

    return _GifFingerprint(
        byte_size=len(payload),
        file_sha256=_sha256_bytes(payload),
        dimensions=dimensions,
        frame_count=frame_count,
        durations_ms=tuple(durations),
        loop=loop,
        frame_sha256=tuple(frame_hashes),
    )


def _preserves_playback_contract(
    source: _GifFingerprint,
    candidate: _GifFingerprint,
) -> bool:
    """Return whether a candidate renders exactly like its source GIF."""
    return (
        candidate.dimensions == source.dimensions
        and candidate.frame_count == source.frame_count
        and candidate.durations_ms == source.durations_ms
        and candidate.loop == source.loop
        and candidate.frame_sha256 == source.frame_sha256
    )


def _unchanged_result(
    source: _GifFingerprint,
    *,
    reason: str,
) -> _GifOptimizationResult:
    return _GifOptimizationResult(
        replaced=False,
        reason=reason,
        source_size=source.byte_size,
        output_size=source.byte_size,
        source_sha256=source.file_sha256,
        output_sha256=source.file_sha256,
    )


def _optimize_gif_with_gifsicle(
    owned_stage_path: Path,
    *,
    executable: str = "gifsicle",
    timeout_seconds: int = _GIFSICLE_TIMEOUT_SECONDS,
) -> _GifOptimizationResult:
    """Optimize a caller-owned private stage when smaller and pixel-exact.

    This helper deliberately does not synchronize a public output path. Its
    caller must own ``owned_stage_path`` exclusively, normally by obtaining it
    from ``_gif_output_transaction``. The stage remains untouched unless the
    candidate preserves dimensions, frame count, per-frame durations, loop
    behavior, and every composited RGBA frame.
    """
    source = _gif_fingerprint(owned_stage_path)
    resolved_executable = shutil.which(executable)
    if resolved_executable is None:
        logger.debug("{} unavailable; retaining {}", executable, owned_stage_path.name)
        return _unchanged_result(source, reason="optimizer-unavailable")

    owned_stage_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=f"{owned_stage_path.name}.",
        suffix=_GIFSICLE_CANDIDATE_SUFFIX,
        dir=owned_stage_path.parent,
        delete=False,
    ) as candidate_file:
        candidate_path = Path(candidate_file.name)

    try:
        try:
            process = subprocess.run(
                [
                    resolved_executable,
                    "--optimize=3",
                    "--no-warnings",
                    "--no-ignore-errors",
                    "--output",
                    str(candidate_path),
                    str(owned_stage_path),
                ],
                check=False,
                capture_output=True,
                timeout=timeout_seconds,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            logger.warning(
                "GIF optimization could not run for {}: {}",
                owned_stage_path.name,
                type(exc).__name__,
            )
            return _unchanged_result(source, reason="optimizer-failed")

        if process.returncode != 0:
            logger.warning(
                "GIF optimization exited {} for {}; retaining source",
                process.returncode,
                owned_stage_path.name,
            )
            return _unchanged_result(source, reason="optimizer-failed")

        try:
            candidate = _gif_fingerprint(candidate_path)
        except (OSError, ValueError) as exc:
            logger.warning(
                "GIF optimizer produced an invalid candidate for {}: {}",
                owned_stage_path.name,
                type(exc).__name__,
            )
            return _unchanged_result(source, reason="invalid-candidate")

        if not _preserves_playback_contract(source, candidate):
            logger.warning(
                "GIF optimizer changed the playback contract for {}; retaining source",
                owned_stage_path.name,
            )
            return _unchanged_result(source, reason="playback-contract-changed")

        if candidate.byte_size >= source.byte_size:
            logger.debug(
                "GIF optimizer did not shrink {} ({} >= {} bytes)",
                owned_stage_path.name,
                candidate.byte_size,
                source.byte_size,
            )
            return _unchanged_result(source, reason="no-size-improvement")

        if _sha256_file(owned_stage_path) != source.file_sha256:
            logger.warning(
                "Source GIF changed during optimization for {}; retaining current file",
                owned_stage_path.name,
            )
            current = _gif_fingerprint(owned_stage_path)
            return _unchanged_result(current, reason="source-changed")

        if _sha256_file(candidate_path) != candidate.file_sha256:
            logger.warning(
                "Candidate GIF changed during verification for {}; retaining source",
                owned_stage_path.name,
            )
            return _unchanged_result(source, reason="candidate-changed")

        os.chmod(
            candidate_path,
            stat.S_IMODE(owned_stage_path.stat().st_mode),
        )
        os.replace(candidate_path, owned_stage_path)
        if _sha256_file(owned_stage_path) != candidate.file_sha256:
            raise OSError(
                f"Private GIF stage replacement checksum failed: {owned_stage_path}"
            )

        saved_bytes = source.byte_size - candidate.byte_size
        logger.info(
            "Losslessly optimized {}: {} -> {} bytes (saved {})",
            owned_stage_path.name,
            source.byte_size,
            candidate.byte_size,
            saved_bytes,
        )
        return _GifOptimizationResult(
            replaced=True,
            reason="optimized",
            source_size=source.byte_size,
            output_size=candidate.byte_size,
            source_sha256=source.file_sha256,
            output_sha256=candidate.file_sha256,
        )
    finally:
        candidate_path.unlink(missing_ok=True)
