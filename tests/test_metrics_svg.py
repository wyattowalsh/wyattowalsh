"""Tests for metrics SVG validation and recovery helpers."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from scripts.metrics_svg import (
    STUB_SVG_MAX_BYTES,
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


CONTENTLESS_SVG = '<svg xmlns="http://www.w3.org/2000/svg"></svg>'
METADATA_ONLY_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg"><title>Only metadata</title></svg>'
)
STRUCTURAL_ONLY_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg"><g id="container"/></svg>'
)
RESOURCE_ONLY_SVG = dedent(
    """\
    <svg xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="gradient" />
      </defs>
    </svg>
    """
)
DEGENERATE_TEXT_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg"><text x="1" y="1"/></svg>'
)
DEGENERATE_RECT_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg"><rect width="0" height="0"/></svg>'
)
DEGENERATE_PATH_SVG = '<svg xmlns="http://www.w3.org/2000/svg"><path d=""/></svg>'
SPLIT_ERROR_SVG = dedent(
    """\
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 80">
      <text x="12" y="40">
        <tspan>Insufficient token</tspan>
        <tspan>scopes</tspan>
      </text>
    </svg>
    """
)
TAIL_SPLIT_ERROR_SVG = dedent(
    """\
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 80">
      <text x="12" y="40">
        Insufficient <tspan>token</tspan> scopes
      </text>
    </svg>
    """
)
SPLIT_PLACEHOLDER_SVG = dedent(
    """\
    <svg xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Metrics unavailable">
      <text x="12" y="40">
        <tspan>Metrics temporarily</tspan>
        <tspan>unavailable</tspan>
      </text>
      <text x="12" y="64">
        <tspan>Check workflow logs</tspan>
        <tspan>for details</tspan>
      </text>
    </svg>
    """
)
TAIL_SPLIT_PLACEHOLDER_SVG = dedent(
    """\
    <svg xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Metrics unavailable">
      <text x="12" y="40">
        Metrics temporarily <tspan>unavailable</tspan>
      </text>
      <text x="12" y="64">
        Check workflow <tspan>logs</tspan> for details
      </text>
    </svg>
    """
)
TINY_PLACEHOLDER_BAR_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="13">'
    '<rect width="480" height="13" fill="#000000"/>'
    "</svg>"
)


def _lowlighter_regen_stub(*, target_bytes: int = 401) -> str:
    """Build a compact lowlighter 'will be regenerated' stub of *target_bytes*."""

    if target_bytes < 1:
        raise ValueError("target_bytes must be positive")

    prefix = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="13">'
        '<rect width="100%" height="100%" fill="#000000"/>'
        "<text>"
    )
    marker = "This metrics instance will be regenerated automatically in a few moments"
    suffix = "</text></svg>"
    pad = target_bytes - len((prefix + marker + suffix).encode("utf-8"))
    if pad < 0:
        raise ValueError(f"target_bytes={target_bytes} is smaller than the stub core")
    return f"{prefix}{marker}{' ' * pad}{suffix}"


REGEN_STUB_SVG = _lowlighter_regen_stub(target_bytes=401)


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
        (CONTENTLESS_SVG, SvgValidationStatus.CONTENTLESS),
        (METADATA_ONLY_SVG, SvgValidationStatus.CONTENTLESS),
        (STRUCTURAL_ONLY_SVG, SvgValidationStatus.CONTENTLESS),
        (RESOURCE_ONLY_SVG, SvgValidationStatus.CONTENTLESS),
        (DEGENERATE_TEXT_SVG, SvgValidationStatus.CONTENTLESS),
        (DEGENERATE_RECT_SVG, SvgValidationStatus.CONTENTLESS),
        (DEGENERATE_PATH_SVG, SvgValidationStatus.CONTENTLESS),
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
        ("traffic: Insufficient token scopes", "traffic: Insufficient token scopes"),
        ("Bad credentials.", "Bad credentials."),
        ("TypeError", "TypeError"),
        ("TypeError Cannot read properties of undefined", "TypeError Cannot read"),
        ("TypeError: Cannot read properties of undefined", "TypeError"),
        ("Forbidden", "Forbidden"),
        ("Unauthorized", "Unauthorized"),
        ("traffic: Unauthorized (401)", "traffic: Unauthorized (401)"),
        ("Unexpected error: boom", "Unexpected error: boom"),
        ("invalid_grant", "invalid_grant"),
        ("Invalid refresh token", "Invalid refresh token"),
        ("API returned 400 (Invalid refresh token)", "Invalid refresh token"),
        ("Tweets unavailable", "Tweets unavailable"),
        (
            "This metrics instance will be regenerated automatically",
            "will be regenerated",
        ),
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


def test_validate_svg_content_allows_benign_error_like_words() -> None:
    result = validate_svg_content(
        _svg_with_text("Fix TypeError handling for forbidden states"),
    )

    assert result.status == SvgValidationStatus.VALID
    assert result.is_valid is True


def test_validate_svg_content_rejects_split_error_text() -> None:
    result = validate_svg_content(SPLIT_ERROR_SVG)

    assert result.status == SvgValidationStatus.ERROR_PAYLOAD
    assert result.is_valid is False


def test_validate_svg_content_rejects_tail_split_error_text() -> None:
    result = validate_svg_content(TAIL_SPLIT_ERROR_SVG)

    assert result.status == SvgValidationStatus.ERROR_PAYLOAD
    assert result.is_valid is False


def test_validate_svg_content_rejects_embedded_unexpected_error_panel() -> None:
    result = validate_svg_content(
        _svg_with_text("Recent coding habits Unexpected error Starred topics"),
    )

    assert result.status == SvgValidationStatus.ERROR_PAYLOAD
    assert result.is_valid is False


def test_validate_svg_content_rejects_embedded_scope_error_panel() -> None:
    result = validate_svg_content(
        _svg_with_text("0 Watchers Insufficient token scopes 8 Languages"),
    )

    assert result.status == SvgValidationStatus.ERROR_PAYLOAD
    assert result.is_valid is False


def test_placeholder_svg_is_detected_and_rejected() -> None:
    result = validate_svg_content(PLACEHOLDER_SVG)

    assert is_placeholder_svg(PLACEHOLDER_SVG) is True
    assert result.status == SvgValidationStatus.PLACEHOLDER
    assert result.is_valid is False
    assert result.is_placeholder is True


def test_placeholder_svg_is_detected_when_text_is_split() -> None:
    result = validate_svg_content(SPLIT_PLACEHOLDER_SVG)

    assert is_placeholder_svg(SPLIT_PLACEHOLDER_SVG) is True
    assert result.status == SvgValidationStatus.PLACEHOLDER
    assert result.is_valid is False


def test_placeholder_svg_is_detected_when_tail_text_is_split() -> None:
    result = validate_svg_content(TAIL_SPLIT_PLACEHOLDER_SVG)

    assert is_placeholder_svg(TAIL_SPLIT_PLACEHOLDER_SVG) is True
    assert result.status == SvgValidationStatus.PLACEHOLDER
    assert result.is_valid is False


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


def test_main_recover_logs_accepted_fallback_without_warning(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    current_asset = tmp_path / "metrics.svg"
    previous_asset = tmp_path / "metrics.previous.svg"
    current_asset.write_text(_svg_with_text("Bad credentials"), encoding="utf-8")
    previous_asset.write_text(VALID_SVG, encoding="utf-8")

    with caplog.at_level("INFO"):
        assert (
            main(
                [
                    "recover",
                    str(current_asset),
                    "--previous",
                    str(previous_asset),
                ]
            )
            == 0
        )

    assert current_asset.read_text(encoding="utf-8") == VALID_SVG
    assert not [record for record in caplog.records if record.levelname == "WARNING"]


def test_lowlighter_regen_stub_is_exactly_401_bytes() -> None:
    assert len(REGEN_STUB_SVG.encode("utf-8")) == 401
    assert 401 <= STUB_SVG_MAX_BYTES


def test_validate_svg_content_rejects_will_be_regenerated_stub() -> None:
    result = validate_svg_content(REGEN_STUB_SVG)

    assert result.is_valid is False
    assert result.status == SvgValidationStatus.ERROR_PAYLOAD
    assert "will-be-regenerated" in result.detail


def test_validate_svg_content_rejects_tiny_placeholder_bar() -> None:
    result = validate_svg_content(TINY_PLACEHOLDER_BAR_SVG)

    assert result.is_valid is False
    assert result.status == SvgValidationStatus.PLACEHOLDER
    assert "placeholder bar" in result.detail


def test_recover_svg_file_rejects_401_byte_stub_without_previous(
    tmp_path: Path,
) -> None:
    new_asset = tmp_path / "metrics.extra.svg"
    new_asset.write_text(REGEN_STUB_SVG, encoding="utf-8")

    result = recover_svg_file(new_asset)

    assert result.action == SvgRecoveryAction.REJECTED
    assert result.current.status == SvgValidationStatus.ERROR_PAYLOAD
    assert result.final.is_valid is False
    assert new_asset.read_text(encoding="utf-8") == REGEN_STUB_SVG


def test_recover_svg_file_replaces_401_byte_stub_with_previous(
    tmp_path: Path,
) -> None:
    new_asset = tmp_path / "metrics.extra.svg"
    previous_asset = tmp_path / "metrics.extra.previous.svg"
    new_asset.write_text(REGEN_STUB_SVG, encoding="utf-8")
    previous_asset.write_text(VALID_SVG, encoding="utf-8")

    result = recover_svg_file(new_asset, previous_asset)

    assert result.action == SvgRecoveryAction.PRESERVED_PREVIOUS
    assert result.current.status == SvgValidationStatus.ERROR_PAYLOAD
    assert result.final.status == SvgValidationStatus.VALID
    assert new_asset.read_text(encoding="utf-8") == VALID_SVG


def test_main_validate_rejects_401_byte_stub(tmp_path: Path) -> None:
    stub_asset = tmp_path / "metrics.extra.svg"
    stub_asset.write_text(REGEN_STUB_SVG, encoding="utf-8")

    assert main(["validate", str(stub_asset)]) == 1


COMMITTED_LOWLIGHTER_SVGS = (
    Path(".github/assets/img/metrics.svg"),
    Path(".github/assets/img/metrics.additional.svg"),
    Path(".github/assets/img/metrics.extra.svg"),
)


def test_fact_lowlighter_audit_committed_svgs_reject_regen_bar() -> None:
    """fact-lowlighter-audit: shipped production SVGs are real cards, not stubs."""
    primary, additional, extra = COMMITTED_LOWLIGHTER_SVGS
    for path in COMMITTED_LOWLIGHTER_SVGS:
        assert path.is_file(), f"missing production lowlighter SVG: {path}"
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        assert "will be regenerated" not in lowered
        assert path.stat().st_size > STUB_SVG_MAX_BYTES
        result = validate_svg_file(path)
        assert result.is_valid is True, f"{path}: {result.status} {result.detail}"
        assert result.status == SvgValidationStatus.VALID

    primary_text = primary.read_text(encoding="utf-8")
    extra_text = extra.read_text(encoding="utf-8")
    additional_text = additional.read_text(encoding="utf-8")
    assert "Most used languages" in primary_text
    assert "Featured repositories" in additional_text
    assert 'class="people"' in additional_text
    assert "Overall issues and pull requests status" in extra_text
    assert "followup" in extra_text.lower()
