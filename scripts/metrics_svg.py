"""Validate and recover generated metrics SVG assets."""

from __future__ import annotations

import argparse
import re
import shutil
import xml.etree.ElementTree as xml_etree
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final

from .utils import get_logger

logger = get_logger(module=__name__)

ERROR_SIGNAL_PATTERNS: Final[tuple[tuple[str, re.Pattern[str]], ...]] = (
    (
        "insufficient-token-scopes",
        re.compile(r"Insufficient token scopes", re.IGNORECASE),
    ),
    (
        "repository-sections-disabled",
        re.compile(
            r"Repository and collaborations sections disabled",
            re.IGNORECASE,
        ),
    ),
    ("api-error", re.compile(r"API error:\s*(401|403)", re.IGNORECASE)),
    ("bad-credentials", re.compile(r"Bad credentials", re.IGNORECASE)),
    (
        "authentication-error",
        re.compile(r"authentication(?: failed| error)?", re.IGNORECASE),
    ),
    ("forbidden", re.compile(r"forbidden", re.IGNORECASE)),
    ("unauthorized", re.compile(r"unauthorized", re.IGNORECASE)),
    ("unexpected-error", re.compile(r"Unexpected error", re.IGNORECASE)),
    ("type-error", re.compile(r"TypeError", re.IGNORECASE)),
    ("spotify-invalid-grant", re.compile(r"invalid_grant", re.IGNORECASE)),
)

PLACEHOLDER_TEXT_MARKERS: Final[tuple[str, ...]] = (
    "Metrics temporarily unavailable",
    "Check workflow logs for details",
)
PLACEHOLDER_ARIA_LABEL: Final[str] = "metrics unavailable"
MEMORY_PATH: Final[Path] = Path("<memory>")


class SvgValidationStatus(StrEnum):
    """Outcome of SVG validation."""

    VALID = "valid"
    MISSING = "missing"
    EMPTY = "empty"
    MALFORMED = "malformed"
    INVALID_ROOT = "invalid-root"
    ERROR_PAYLOAD = "error-payload"
    PLACEHOLDER = "placeholder"


class SvgRecoveryAction(StrEnum):
    """Outcome of a recovery attempt."""

    ACCEPTED_CURRENT = "accepted-current"
    PRESERVED_PREVIOUS = "preserved-previous"
    REJECTED = "rejected"


@dataclass(frozen=True)
class SvgValidationResult:
    """Structured validation result for a metrics SVG."""

    path: Path
    status: SvgValidationStatus
    detail: str

    @property
    def is_valid(self) -> bool:
        return self.status == SvgValidationStatus.VALID

    @property
    def is_placeholder(self) -> bool:
        return self.status == SvgValidationStatus.PLACEHOLDER

    def to_dict(self) -> dict[str, str | bool]:
        return {
            "path": str(self.path),
            "status": self.status.value,
            "detail": self.detail,
            "is_valid": self.is_valid,
            "is_placeholder": self.is_placeholder,
        }


@dataclass(frozen=True)
class SvgRecoveryResult:
    """Structured outcome for SVG preservation/recovery."""

    action: SvgRecoveryAction
    current: SvgValidationResult
    final: SvgValidationResult
    previous: SvgValidationResult | None = None
    detail: str = ""

    @property
    def recovered(self) -> bool:
        return self.action == SvgRecoveryAction.PRESERVED_PREVIOUS

    def to_dict(self) -> dict[str, object]:
        return {
            "action": self.action.value,
            "detail": self.detail,
            "current": self.current.to_dict(),
            "final": self.final.to_dict(),
            "previous": None if self.previous is None else self.previous.to_dict(),
            "recovered": self.recovered,
        }


def detect_metrics_error_signal(svg_text: str) -> tuple[str, str] | None:
    """Return the first known metrics error signal found in *svg_text*."""

    for signal_name, pattern in ERROR_SIGNAL_PATTERNS:
        match = pattern.search(svg_text)
        if match is not None:
            return signal_name, match.group(0)
    return None


def is_placeholder_svg(svg_text: str) -> bool:
    """Return whether *svg_text* matches the placeholder SVG content."""

    normalized = svg_text.casefold()
    if PLACEHOLDER_ARIA_LABEL in normalized:
        return True
    return all(marker.casefold() in normalized for marker in PLACEHOLDER_TEXT_MARKERS)


def _local_name(tag: str) -> str:
    """Extract an XML local name from a namespaced tag."""

    return tag.rsplit("}", maxsplit=1)[-1]


def validate_svg_content(
    svg_text: str,
    *,
    source: Path | None = None,
) -> SvgValidationResult:
    """Validate raw SVG content and classify common metrics failures."""

    path = source if source is not None else MEMORY_PATH
    if not svg_text.strip():
        return SvgValidationResult(
            path=path,
            status=SvgValidationStatus.EMPTY,
            detail="SVG content is empty.",
        )

    error_signal = detect_metrics_error_signal(svg_text)
    if error_signal is not None:
        signal_name, matched_text = error_signal
        return SvgValidationResult(
            path=path,
            status=SvgValidationStatus.ERROR_PAYLOAD,
            detail=(
                f"SVG contains known metrics failure signal "
                f"{signal_name!r}: {matched_text!r}."
            ),
        )

    if is_placeholder_svg(svg_text):
        return SvgValidationResult(
            path=path,
            status=SvgValidationStatus.PLACEHOLDER,
            detail="SVG matches the known placeholder content.",
        )

    try:
        root = xml_etree.fromstring(svg_text)
    except xml_etree.ParseError as exc:
        return SvgValidationResult(
            path=path,
            status=SvgValidationStatus.MALFORMED,
            detail=f"SVG is not well-formed XML: {exc}.",
        )

    if _local_name(root.tag) != "svg":
        return SvgValidationResult(
            path=path,
            status=SvgValidationStatus.INVALID_ROOT,
            detail=f"Expected <svg> root element, found <{_local_name(root.tag)}>.",
        )

    return SvgValidationResult(
        path=path,
        status=SvgValidationStatus.VALID,
        detail="SVG is well-formed and contains no known metrics failure signals.",
    )


def validate_svg_file(svg_path: Path) -> SvgValidationResult:
    """Validate an SVG file on disk."""

    if not svg_path.exists():
        return SvgValidationResult(
            path=svg_path,
            status=SvgValidationStatus.MISSING,
            detail="SVG file does not exist.",
        )

    if not svg_path.is_file():
        return SvgValidationResult(
            path=svg_path,
            status=SvgValidationStatus.MALFORMED,
            detail="SVG path is not a regular file.",
        )

    try:
        svg_text = svg_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return SvgValidationResult(
            path=svg_path,
            status=SvgValidationStatus.MALFORMED,
            detail=f"SVG file is not valid UTF-8 text: {exc}.",
        )
    except OSError as exc:
        return SvgValidationResult(
            path=svg_path,
            status=SvgValidationStatus.MALFORMED,
            detail=f"SVG file could not be read: {exc}.",
        )

    return validate_svg_content(svg_text, source=svg_path)


def recover_svg_file(
    svg_path: Path,
    previous_path: Path | None = None,
) -> SvgRecoveryResult:
    """Preserve the previous valid asset when the new SVG is unusable."""

    current = validate_svg_file(svg_path)
    if current.is_valid:
        return SvgRecoveryResult(
            action=SvgRecoveryAction.ACCEPTED_CURRENT,
            current=current,
            final=current,
            detail="Generated SVG passed validation.",
        )

    previous = validate_svg_file(previous_path) if previous_path is not None else None
    if previous is not None and previous.is_valid and previous_path is not None:
        shutil.copyfile(previous_path, svg_path)
        final = validate_svg_file(svg_path)
        return SvgRecoveryResult(
            action=SvgRecoveryAction.PRESERVED_PREVIOUS,
            current=current,
            final=final,
            previous=previous,
            detail=("Replaced invalid generated SVG with the previous valid asset."),
        )

    return SvgRecoveryResult(
        action=SvgRecoveryAction.REJECTED,
        current=current,
        final=current,
        previous=previous,
        detail="Generated SVG is invalid and no previous valid asset was available.",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate and recover GitHub metrics SVG assets.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate a metrics SVG file.",
    )
    validate_parser.add_argument("svg_path", type=Path, help="SVG file to validate.")

    recover_parser = subparsers.add_parser(
        "recover",
        help="Recover an invalid SVG by restoring a previous valid asset.",
    )
    recover_parser.add_argument("svg_path", type=Path, help="Generated SVG file.")
    recover_parser.add_argument(
        "--previous",
        type=Path,
        required=True,
        help="Path to the previous valid SVG asset.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for metrics SVG validation and recovery."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "validate":
        result = validate_svg_file(args.svg_path)
        if result.is_valid:
            logger.info("{path}: {detail}", path=result.path, detail=result.detail)
            return 0
        logger.warning(
            "{path}: {status} — {detail}",
            path=result.path,
            status=result.status.value,
            detail=result.detail,
        )
        return 1

    recovery = recover_svg_file(args.svg_path, previous_path=args.previous)
    if recovery.final.is_valid:
        if recovery.recovered:
            logger.warning(
                "{path}: {detail}",
                path=recovery.final.path,
                detail=recovery.detail,
            )
        else:
            logger.info(
                "{path}: {detail}",
                path=recovery.final.path,
                detail=recovery.detail,
            )
        return 0

    logger.error(
        "{path}: {detail}",
        path=recovery.final.path,
        detail=recovery.detail,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
