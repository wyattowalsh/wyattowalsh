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
        re.compile(
            r"(?:^|[\s:>-])Insufficient token scopes(?:$|[.!()])",
            re.IGNORECASE,
        ),
    ),
    (
        "repository-sections-disabled",
        re.compile(
            r"(?:^|[\s:>-])Repository and collaborations sections disabled"
            r"(?:$|[.!()])",
            re.IGNORECASE,
        ),
    ),
    (
        "api-error",
        re.compile(r"(?:^|[\s:>-])API error:\s*(401|403)\b.*", re.IGNORECASE),
    ),
    (
        "bad-credentials",
        re.compile(
            r"(?:^|[\s:>-])Bad credentials(?:$|[.!()])",
            re.IGNORECASE,
        ),
    ),
    (
        "authentication-error",
        re.compile(
            r"(?:^|[\s:>-])authentication(?: failed| error)?(?:$|[.!()])",
            re.IGNORECASE,
        ),
    ),
    (
        "forbidden",
        re.compile(
            r"(?:^|[\s:>-])Forbidden(?:$|[.!()]|\s+\(\d{3}\))",
            re.IGNORECASE,
        ),
    ),
    (
        "unauthorized",
        re.compile(
            r"(?:^|[\s:>-])Unauthorized(?:$|[.!()]|\s+\(\d{3}\))",
            re.IGNORECASE,
        ),
    ),
    (
        "unexpected-error",
        re.compile(
            r"(?:^|[\s:>-])Unexpected error(?:$|[:.!()])",
            re.IGNORECASE,
        ),
    ),
    (
        "type-error",
        re.compile(r"(?:^|[\s:>-])TypeError(?:$|[:.!()]|\s+[A-Z])"),
    ),
    (
        "spotify-invalid-grant",
        re.compile(
            r"(?:^|[\s:>-])invalid_grant(?:$|[.!()])",
            re.IGNORECASE,
        ),
    ),
)

PLACEHOLDER_TEXT_MARKERS: Final[tuple[str, ...]] = (
    "Metrics temporarily unavailable",
    "Check workflow logs for details",
)
PLACEHOLDER_ARIA_LABEL: Final[str] = "metrics unavailable"
MEMORY_PATH: Final[Path] = Path("<memory>")
NON_RENDERED_SVG_TAGS: Final[frozenset[str]] = frozenset(
    {
        "clippath",
        "defs",
        "desc",
        "filter",
        "lineargradient",
        "marker",
        "mask",
        "metadata",
        "pattern",
        "radialgradient",
        "style",
        "symbol",
        "title",
    },
)
STRUCTURAL_SVG_TAGS: Final[frozenset[str]] = frozenset({"g"})
LENGTH_VALUE_PATTERN: Final[re.Pattern[str]] = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)")


class SvgValidationStatus(StrEnum):
    """Outcome of SVG validation."""

    VALID = "valid"
    MISSING = "missing"
    EMPTY = "empty"
    MALFORMED = "malformed"
    INVALID_ROOT = "invalid-root"
    CONTENTLESS = "contentless"
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


def _normalize_text(text: str) -> str:
    """Collapse internal whitespace to simplify text matching."""

    return " ".join(text.split())


def detect_metrics_error_signal(visible_text: str) -> tuple[str, str] | None:
    """Return the first known metrics error signal found in visible SVG text."""

    normalized_text = _normalize_text(visible_text)
    for signal_name, pattern in ERROR_SIGNAL_PATTERNS:
        match = pattern.search(normalized_text)
        if match is not None:
            return signal_name, normalized_text
    return None


def is_placeholder_svg(svg_text: str) -> bool:
    """Return whether *svg_text* matches the placeholder SVG content."""

    normalized = _normalize_text(svg_text).casefold()
    if PLACEHOLDER_ARIA_LABEL in normalized:
        return True

    try:
        root = xml_etree.fromstring(svg_text)
    except xml_etree.ParseError:
        return all(
            marker.casefold() in normalized
            for marker in PLACEHOLDER_TEXT_MARKERS
        )

    visible_text = _extract_visible_svg_text(root).casefold()
    return all(marker.casefold() in visible_text for marker in PLACEHOLDER_TEXT_MARKERS)


def _local_name(tag: str) -> str:
    """Extract an XML local name from a namespaced tag."""

    return tag.rsplit("}", maxsplit=1)[-1]


def _extract_svg_text_fragments(root: xml_etree.Element[str]) -> tuple[str, ...]:
    """Return non-empty visible text fragments from an SVG tree."""

    def _collect_visible_text(
        element: xml_etree.Element[str],
        *,
        parent_hidden: bool = False,
    ) -> list[str]:
        local_name = _local_name(element.tag).casefold()
        element_hidden = parent_hidden or (
            element is not root and local_name in NON_RENDERED_SVG_TAGS
        )

        fragments: list[str] = []
        if not element_hidden:
            text = (element.text or "").strip()
            if text:
                fragments.append(text)

        for child in element:
            fragments.extend(_collect_visible_text(child, parent_hidden=element_hidden))
            if not element_hidden:
                tail = (child.tail or "").strip()
                if tail:
                    fragments.append(tail)

        return fragments

    return tuple(_collect_visible_text(root))


def _extract_visible_svg_text(root: xml_etree.Element[str]) -> str:
    """Return normalized visible text extracted from an SVG tree."""

    return _normalize_text(" ".join(_extract_svg_text_fragments(root)))


def _has_positive_length(value: str | None) -> bool:
    """Return whether an SVG length-like attribute is present and positive."""

    if value is None:
        return False

    match = LENGTH_VALUE_PATTERN.search(value.strip())
    if match is None:
        return False

    return float(match.group(0)) > 0


def _has_rendered_attributes(
    element: xml_etree.Element[str],
    local_name: str,
) -> bool:
    """Return whether *element* has attributes consistent with visible content."""

    if local_name in {"text", "tspan", "textpath"}:
        return False

    if local_name == "path":
        return bool((element.attrib.get("d") or "").strip())

    if local_name in {"polyline", "polygon"}:
        return bool((element.attrib.get("points") or "").strip())

    if local_name in {"use", "image"}:
        href = element.attrib.get("href") or element.attrib.get(
            "{http://www.w3.org/1999/xlink}href",
        )
        return bool((href or "").strip())

    if local_name in {"rect", "foreignobject"}:
        has_positive_width = _has_positive_length(element.attrib.get("width"))
        has_positive_height = _has_positive_length(element.attrib.get("height"))
        return has_positive_width and has_positive_height

    if local_name == "circle":
        return _has_positive_length(element.attrib.get("r"))

    if local_name == "ellipse":
        return _has_positive_length(element.attrib.get("rx")) and _has_positive_length(
            element.attrib.get("ry"),
        )

    if local_name == "line":
        return (
            (element.attrib.get("x1") != element.attrib.get("x2"))
            or (element.attrib.get("y1") != element.attrib.get("y2"))
        ) and all(
            key in element.attrib
            for key in ("x1", "x2", "y1", "y2")
        )

    return bool(element.attrib)


def _has_meaningful_svg_content(root: xml_etree.Element[str]) -> bool:
    """Return whether an SVG tree contains visible or textual content."""

    for element in root.iter():
        if element is root:
            continue

        local_name = _local_name(element.tag).casefold()
        if local_name in NON_RENDERED_SVG_TAGS:
            continue

        if (element.text or "").strip():
            return True

        if local_name in STRUCTURAL_SVG_TAGS:
            continue

        if _has_rendered_attributes(element, local_name):
            return True

    return False


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

    error_signal = detect_metrics_error_signal(_extract_visible_svg_text(root))
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

    if not _has_meaningful_svg_content(root):
        return SvgValidationResult(
            path=path,
            status=SvgValidationStatus.CONTENTLESS,
            detail="SVG contains no meaningful rendered or textual content.",
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
