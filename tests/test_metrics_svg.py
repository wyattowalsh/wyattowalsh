"""Tests for metrics SVG validation and recovery helpers."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from scripts.metrics_svg import (
    SvgRecoveryAction,
    SvgValidationStatus,
    is_placeholder_svg,
    main,
    recover_svg_file,
    validate_svg_content,
    validate_svg_file,
)

VALID_SVG = dedent(
    """\
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 80">
      <rect width="200" height="80" fill="#0d1117" />
      <text x="12" y="40" fill="#c9d1d9">Healthy metrics card</text>
    </svg>
    """
)

PLACEHOLDER_SVG = dedent(
    """\
    <?xml version="1.0" encoding="UTF-8"?>
    <svg xmlns="http://www.w3.org/2000/svg"
         width="800"
         height="200"
         viewBox="0 0 800 200"
         role="img"
         aria-label="Metrics unavailable">
      <rect width="100%" height="100%" rx="8" fill="#0d1117"/>
      <text x="50%" y="45%" fill="#c9d1d9">Metrics temporarily unavailable</text>
      <text x="50%" y="65%" fill="#8b949e">Check workflow logs for details</text>
    </svg>
    """
)


def _svg_with_text(text: str) -> str:
    return dedent(
        f"""\
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 80">
          <text x="12" y="40">{text}</text>
        </svg>
        """
    )


def test_validate_svg_content_accepts_valid_svg() -> None:
    result = validate_svg_content(VALID_SVG)

    assert result.status == SvgValidationStatus.VALID
    assert result.is_valid is True
    assert result.is_placeholder is False


@pytest.mark.parametrize(
    ("svg_text", "expected_status"),
    [
        ("", SvgValidationStatus.EMPTY),
        ("<svg><g></svg>", SvgValidationStatus.MALFORMED),
    ],
)
def test_validate_svg_content_rejects_empty_or_malformed(
    svg_text: str,
    expected_status: SvgValidationStatus,
) -> None:
    result = validate_svg_content(svg_text)

    assert result.status == expected_status
    assert result.is_valid is False


@pytest.mark.parametrize(
    ("error_text", "detail_fragment"),
    [
        ("Insufficient token scopes", "Insufficient token scopes"),
        ("TypeError: Cannot read properties of undefined", "TypeError"),
        ("invalid_grant", "invalid_grant"),
    ],
)
def test_validate_svg_content_rejects_known_error_payloads(
    error_text: str,
    detail_fragment: str,
) -> None:
    result = validate_svg_content(_svg_with_text(error_text))

    assert result.status == SvgValidationStatus.ERROR_PAYLOAD
    assert result.is_valid is False
    assert detail_fragment in result.detail


def test_placeholder_svg_is_detected_and_rejected() -> None:
    result = validate_svg_content(PLACEHOLDER_SVG)

    assert is_placeholder_svg(PLACEHOLDER_SVG) is True
    assert result.status == SvgValidationStatus.PLACEHOLDER
    assert result.is_valid is False
    assert result.is_placeholder is True


def test_validate_svg_file_rejects_missing_file(tmp_path: Path) -> None:
    result = validate_svg_file(tmp_path / "missing.svg")

    assert result.status == SvgValidationStatus.MISSING
    assert result.is_valid is False


def test_recover_svg_file_preserves_previous_valid_asset(tmp_path: Path) -> None:
    new_asset = tmp_path / "metrics.svg"
    previous_asset = tmp_path / "metrics.previous.svg"
    new_asset.write_text(_svg_with_text("Insufficient token scopes"), encoding="utf-8")
    previous_asset.write_text(VALID_SVG, encoding="utf-8")

    result = recover_svg_file(new_asset, previous_asset)

    assert result.action == SvgRecoveryAction.PRESERVED_PREVIOUS
    assert result.current.status == SvgValidationStatus.ERROR_PAYLOAD
    assert result.previous is not None
    assert result.previous.status == SvgValidationStatus.VALID
    assert result.final.status == SvgValidationStatus.VALID
    assert result.recovered is True
    assert new_asset.read_text(encoding="utf-8") == VALID_SVG


def test_recover_svg_file_rejects_without_valid_previous(tmp_path: Path) -> None:
    new_asset = tmp_path / "metrics.svg"
    previous_asset = tmp_path / "metrics.previous.svg"
    new_asset.write_text(_svg_with_text("invalid_grant"), encoding="utf-8")
    previous_asset.write_text(PLACEHOLDER_SVG, encoding="utf-8")

    result = recover_svg_file(new_asset, previous_asset)

    assert result.action == SvgRecoveryAction.REJECTED
    assert result.previous is not None
    assert result.previous.status == SvgValidationStatus.PLACEHOLDER
    assert result.final.status == SvgValidationStatus.ERROR_PAYLOAD
    assert result.recovered is False


def test_main_validate_returns_expected_exit_codes(tmp_path: Path) -> None:
    valid_asset = tmp_path / "valid.svg"
    invalid_asset = tmp_path / "invalid.svg"
    valid_asset.write_text(VALID_SVG, encoding="utf-8")
    invalid_asset.write_text(_svg_with_text("TypeError: broken"), encoding="utf-8")

    assert main(["validate", str(valid_asset)]) == 0
    assert main(["validate", str(invalid_asset)]) == 1
