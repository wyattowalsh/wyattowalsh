from pathlib import Path
from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest

# import pytest # Pytest is a framework, not a library to import here
from pydantic import HttpUrl

from scripts.config import VCardDataModel as ConfigVCardDataModel
from scripts.qr import QRCodeGenerator
from scripts.qr import logger as qr_logger

# Cairo (system dependency) check for integration test
# Try to import cairocffi and perform a basic operation to see if libcairo is
# truly available
cairo_library_available = False
try:
    import cairocffi  # type: ignore

    # Accessing version string is a good check if cairocffi itself can load
    # and interact with libcairo
    cairocffi.cairo_version_string()
    cairo_library_available = True
except (ImportError, OSError):
    # ImportError if cairocffi not installed, OSError if libcairo missing
    # If basic import/version check fails, try a more involved operation
    try:
        from cairocffi import FORMAT_ARGB32, Context, ImageSurface  # type: ignore
        surface = ImageSurface(FORMAT_ARGB32, 1, 1)
        # This operation would fail if libcairo not loadable
        ctx = Context(surface)
        cairo_library_available = True  # If it gets here, cairo is usable
    except (ImportError, OSError):
        # Still false if the more involved check also fails
        cairo_library_available = False


@pytest.fixture
def mock_project_root(tmp_path: Path) -> Path:
    """Creates a mock project root with necessary dummy files/dirs."""
    assets_img_dir = tmp_path / ".github" / "assets" / "img"
    assets_img_dir.mkdir(parents=True, exist_ok=True)

    # Create a dummy icon.svg for background
    dummy_svg_content = '<svg width="10" height="10"></svg>'
    (assets_img_dir / "icon.svg").write_text(dummy_svg_content)

    return tmp_path


@pytest.fixture
def default_vcard_data() -> ConfigVCardDataModel:
    """Returns a default VCardDataModel instance for testing."""
    return ConfigVCardDataModel(
        n_familyname="Doe",
        n_givenname="John",
        fn="John Doe",
        displayname="John Doe Display",
        email_internet="john.doe@example.com",
        tel_work_voice="1234567890",
        url_work=[
            {"url": "http://example.com", "label": "Website"},
            {"url": "http://johndoe.dev", "label": "DevSite"}
        ],
        org="Example Corp",
        title="Tester"
    )


@pytest.fixture
def qr_generator_instance(
    mock_project_root: Path, caplog: Any
) -> Generator[QRCodeGenerator, None, None]:
    """Initializes QRCodeGenerator with mock paths and configures logger."""
    bg_path = mock_project_root / ".github" / "assets" / "img" / "icon.svg"
    output_dir = (
        mock_project_root / ".github" / "assets" / "img" / "qrcodes_test"
    )

    # Configure scripts.qr.logger to be captured by caplog at INFO level
    # This setup ensures that logs emitted by qr_logger are available in
    # caplog.text.
    original_handlers = list(qr_logger._core.handlers.keys())
    for handler_id in original_handlers:
        qr_logger.remove(handler_id)

    # Using a simple formatter for caplog to make assertions easier
    qr_logger.add(caplog.handler, format="{message}", level="INFO")

    yield QRCodeGenerator(
        default_background_path=bg_path,
        default_output_dir=output_dir,
        default_scale=10
    )

    # Teardown: remove the handler added for caplog
    # This is a guess, assuming caplog.handler is the last one added.
    # A more robust way would be to store the handler_id returned by add()
    try:
        qr_logger.remove()
    except ValueError:
        pass
    for handler_id in original_handlers:
        pass


# Tests for QRCodeGenerator Initialization
def test_qr_generator_initialization_success(mock_project_root: Path) -> None:
    """Test successful initialization of QRCodeGenerator."""
    bg_path = mock_project_root / ".github" / "assets" / "img" / "icon.svg"
    output_dir = mock_project_root / "output_qr"

    generator = QRCodeGenerator(
        default_background_path=bg_path,
        default_output_dir=output_dir,
        default_scale=20
    )
    assert generator.default_background_path == bg_path
    assert generator.default_output_dir == output_dir
    assert output_dir.exists()  # Check if output dir was created
    assert generator.default_scale == 20


def test_qr_generator_initialization_missing_background(
    mock_project_root: Path,
    qr_generator_instance: QRCodeGenerator,
    caplog: Any
) -> None:
    """Test initialization failure if default background SVG is missing."""
    missing_bg_path = mock_project_root / "non_existent_bg.svg"
    output_dir = mock_project_root / "output_qr"

    # qr_logger is already configured by qr_generator_instance fixture
    # caplog.set_level(logging.ERROR) # Not needed if qr_logger directly uses
    # caplog.handler

    with pytest.raises(
        FileNotFoundError,
        match=f"Default background SVG not found: {missing_bg_path}"
    ):
        QRCodeGenerator(  # Call directly to test constructor logging
            default_background_path=missing_bg_path,
            default_output_dir=output_dir
        )
    # assert f"Default background SVG not found: {missing_bg_path}" in caplog.text
    expected_error_message = f"Default background SVG not found: {missing_bg_path}"
    assert any(
        record.message == expected_error_message and record.levelname == "ERROR"
        for record in caplog.records
    )


@patch("pathlib.Path.mkdir")
def test_qr_generator_initialization_oserror_on_mkdir(
    mock_mkdir: MagicMock, mock_project_root: Path, caplog: Any
) -> None:
    """Test initialization failure if output directory creation fails."""
    bg_path = mock_project_root / ".github" / "assets" / "img" / "icon.svg"
    output_dir = mock_project_root / "uncreatable_output_dir"
    mock_mkdir.side_effect = OSError("Test OS Error")

    # qr_logger configured via fixture or ensure re-config if instance not used
    # Ensure caplog handler is attached for this specific test if not using
    # fixture that already does it.
    # Adding it again might lead to duplicate logs if not careful.
    # For this test, assuming we want a clean slate if qr_generator_instance
    # is not used which is not the case here, but good to be aware.
    # We can clear and re-add if necessary, or trust the fixture.

    # Given qr_generator_instance fixture is used in some tests but not all,
    # and this test doesn't use it, we might need to re-configure logger here.
    # However, the pattern in other tests is to use qr_generator_instance OR
    # to call QRCodeGenerator directly. For direct calls, the logger state is
    # important.

    # If qr_generator_instance IS NOT USED, we must ensure caplog is connected.
    # If we assume qr_logger is globally available and we just want to tap
    # into it:
    try:
        qr_logger.remove()
    except ValueError:
        pass
    qr_logger.add(caplog.handler, format="{message}")

    with pytest.raises(OSError, match="Test OS Error"):
        QRCodeGenerator(
            default_background_path=bg_path,
            default_output_dir=output_dir
        )
    assert (
        f"Could not create output directory {output_dir}: Test OS Error"
        in caplog.text
    )


# Tests for generate_artistic_vcard_qr
@patch("segno.make")
def test_generate_artistic_vcard_qr_success_defaults(
    mock_segno_make: MagicMock,
    qr_generator_instance: QRCodeGenerator,
    default_vcard_data: ConfigVCardDataModel,
    mock_project_root: Path,
    caplog: Any
) -> None:
    """Test successful generation with default settings."""
    mock_qr_object = MagicMock()
    mock_segno_make.return_value = mock_qr_object

    output_filename = "test_qr.png"
    expected_output_path = (
        qr_generator_instance.default_output_dir / output_filename
    )

    generated_path = qr_generator_instance.generate_artistic_vcard_qr(
        vcard_details=default_vcard_data,
        output_filename=output_filename
    )

    assert generated_path == expected_output_path
    mock_segno_make.assert_called_once()
    args, kwargs = mock_segno_make.call_args
    # Extract the vcard string from the call arguments
    vcard_string = args[0]
    assert f"FN:{default_vcard_data.fn}" in vcard_string
    assert f"DISPLAYNAME:{default_vcard_data.displayname}" in vcard_string
    # assert f"EMAIL;TYPE=INTERNET,PREF:{default_vcard_data.email_internet}" in vcard_string
    email_str = (
        f"EMAIL;TYPE=INTERNET,PREF:{default_vcard_data.email_internet}"
    )
    assert email_str in vcard_string
    assert f"ORG:{default_vcard_data.org}" in vcard_string
    assert "item1.URL:http://example.com/" in vcard_string
    assert "item1.X-ABLabel:Website" in vcard_string
    assert "item2.URL:http://johndoe.dev/" in vcard_string
    assert "item2.X-ABLabel:DevSite" in vcard_string
    assert kwargs['error'] == "H"
    assert not kwargs['micro']

    mock_qr_object.to_artistic.assert_called_once_with( # type: ignore
        background=str(qr_generator_instance.default_background_path),
        target=str(expected_output_path),
        scale=qr_generator_instance.default_scale
    )
    # log_text = caplog.text
    expected_log_msg_content = (
        f"Generating artistic QR code to {expected_output_path} "
        f"with background {qr_generator_instance.default_background_path}"
    )
    # assert expected_log_msg_content in log_text
    assert any(
        record.message == expected_log_msg_content and record.levelname == "INFO"
        for record in caplog.records
    )
    assert any(
        record.message == f"Successfully generated QR code: {expected_output_path}" and record.levelname == "INFO"
        for record in caplog.records
    )


@patch("segno.make")
def test_generate_artistic_vcard_qr_custom_settings(
    mock_segno_make: MagicMock,
    qr_generator_instance: QRCodeGenerator,
    default_vcard_data: ConfigVCardDataModel,
    mock_project_root: Path
) -> None:
    """
    Test successful generation with custom scale, background, and error
    correction.
    """
    mock_qr_object = MagicMock()
    mock_segno_make.return_value = mock_qr_object

    custom_bg_filename = "custom_bg.svg"
    custom_bg_path = (
        mock_project_root / ".github" / "assets" / "img" / custom_bg_filename
    )
    custom_bg_path.write_text("<svg id='custom'></svg>")

    output_filename = "custom_qr.png"
    custom_scale = 15
    custom_error_correction = "M"
    expected_output_path = (
        qr_generator_instance.default_output_dir / output_filename
    )

    generated_path = qr_generator_instance.generate_artistic_vcard_qr(
        vcard_details=default_vcard_data,
        output_filename=output_filename,
        background_path=custom_bg_path,
        scale=custom_scale,
        error_correction=custom_error_correction
    )

    assert generated_path == expected_output_path
    mock_segno_make.assert_called_once()
    _, kwargs = mock_segno_make.call_args
    assert kwargs['error'] == custom_error_correction

    mock_qr_object.to_artistic.assert_called_once_with( # type: ignore
        background=str(custom_bg_path),
        target=str(expected_output_path),
        scale=custom_scale
    )

    # Ensure the vcard string is constructed correctly
    mock_segno_make.assert_called_once()
    args, _ = mock_segno_make.call_args
    vcard_string = args[0]

    # assert f"N:{default_vcard_data.n_familyname};{default_vcard_data.n_givenname}" \\
    #     in vcard_string
    name_str = (
        f"N:{default_vcard_data.n_familyname};"
        f"{default_vcard_data.n_givenname}"
    )
    assert name_str in vcard_string
    assert f"FN:{default_vcard_data.fn}" in vcard_string
    assert f"DISPLAYNAME:{default_vcard_data.displayname}" in vcard_string
    # assert f"EMAIL;TYPE=INTERNET,PREF:{default_vcard_data.email_internet}" \\
    #     in vcard_string
    email_str = (
        f"EMAIL;TYPE=INTERNET,PREF:{default_vcard_data.email_internet}"
    )
    assert email_str in vcard_string
    # assert f"TEL;TYPE=WORK,VOICE:{default_vcard_data.tel_work_voice}" \\
    #     in vcard_string
    tel_str = f"TEL;TYPE=WORK,VOICE:{default_vcard_data.tel_work_voice}"
    assert tel_str in vcard_string
    assert f"ORG:{default_vcard_data.org}" in vcard_string
    assert f"TITLE:{default_vcard_data.title}" in vcard_string
    if default_vcard_data.url_work:
        for i, typed_url_item in enumerate(default_vcard_data.url_work):
            assert f"item{i+1}.URL:{typed_url_item.url}" in vcard_string
            # assert f"item{i+1}.X-ABLabel:{typed_url_item.label}" in vcard_string
            label_str = f"item{i+1}.X-ABLabel:{typed_url_item.label}"
            assert label_str in vcard_string


def test_generate_artistic_vcard_qr_missing_custom_background(
    qr_generator_instance: QRCodeGenerator,
    default_vcard_data: ConfigVCardDataModel,
    mock_project_root: Path,
    caplog: Any
) -> None:
    """
    Test generation failure if a custom background SVG is specified but
    missing.
    """
    missing_custom_bg = mock_project_root / "non_existent_custom_bg.svg"
    with pytest.raises(
        FileNotFoundError,
        match=f"Background SVG for QR code not found: {missing_custom_bg}"
    ):
        qr_generator_instance.generate_artistic_vcard_qr(
            vcard_details=default_vcard_data,
            output_filename="test.png",
            background_path=missing_custom_bg
        )
    assert (
        f"Background SVG for QR code not found: {missing_custom_bg}"
        in caplog.text
    )


def test_generate_artistic_vcard_qr_invalid_error_correction(
    qr_generator_instance: QRCodeGenerator,
    default_vcard_data: ConfigVCardDataModel,
    caplog: Any
) -> None:
    """Test generation failure with an invalid error correction level."""
    invalid_error_level = "X"
    with pytest.raises(
        ValueError,
        match="Error correction level must be one of 'L', 'M', 'Q', 'H'."
    ):
        qr_generator_instance.generate_artistic_vcard_qr(
            vcard_details=default_vcard_data,
            output_filename="test.png",
            error_correction=invalid_error_level
        )
    assert (
        f"Invalid QR error correction level: {invalid_error_level}"
        in caplog.text
    )


@patch("segno.make")
def test_generate_artistic_vcard_qr_segno_make_exception(
    mock_segno_make: MagicMock,
    qr_generator_instance: QRCodeGenerator,
    default_vcard_data: ConfigVCardDataModel,
    caplog: Any
) -> None:
    """Test handling of exceptions from segno.make()."""
    mock_segno_make.side_effect = ValueError("Segno internal error")
    with pytest.raises(ValueError, match="Segno internal error"):
        qr_generator_instance.generate_artistic_vcard_qr(
            vcard_details=default_vcard_data,
            output_filename="test.png"
        )
    assert (
        "Value error during QR generation: Segno internal error" in caplog.text
    )


@patch("segno.make")
def test_generate_artistic_vcard_qr_to_artistic_exception(
    mock_segno_make: MagicMock,
    qr_generator_instance: QRCodeGenerator,
    default_vcard_data: ConfigVCardDataModel,
    caplog: Any
) -> None:
    """Test handling of exceptions from qrcode.to_artistic()."""
    mock_qr_object = MagicMock()
    mock_qr_object.to_artistic.side_effect = Exception(
        "Artistic render failed"
    )
    mock_segno_make.return_value = mock_qr_object

    with pytest.raises(Exception, match="Artistic render failed"):
        qr_generator_instance.generate_artistic_vcard_qr(
            vcard_details=default_vcard_data,
            output_filename="test.png"
        )
    # assert (
    #     "Artistic render failed" in caplog.text
    # )
    expected_error_msg = (
        "An unexpected error during QR code generation: Artistic render failed"
    )
    assert any(
        record.message == expected_error_msg and record.levelname == "ERROR"
        for record in caplog.records
    )


@patch("segno.make")
def test_generate_artistic_vcard_qr_to_artistic_not_callable(
    mock_segno_make: MagicMock,
    qr_generator_instance: QRCodeGenerator,
    default_vcard_data: ConfigVCardDataModel,
    caplog: Any
) -> None:
    """
    Test handling if qrcode.to_artistic is not callable.
    """
    mock_qr_object = MagicMock()
    # Make 'to_artistic' an attribute that is not callable, e.g., a string
    mock_qr_object.to_artistic = "this is not a method"
    mock_segno_make.return_value = mock_qr_object

    with pytest.raises(
        AttributeError,
        match="Artistic QR rendering not available."
    ):
        qr_generator_instance.generate_artistic_vcard_qr(
            vcard_details=default_vcard_data,
            output_filename="test.png"
        )
    assert (
        "qrcode object does not have a callable 'to_artistic' method."
    ) in caplog.text


@patch("segno.helpers.make_vcard_data")
@patch("segno.make")
def test_vcard_payload_construction_all_fields(
    mock_segno_make: MagicMock,
    mock_make_vcard_data: MagicMock,
    qr_generator_instance: QRCodeGenerator,
    default_vcard_data: ConfigVCardDataModel
) -> None:
    """
    Test that all VCardDataModel fields are passed to segno's make_vcard_data.
    """
    qr_generator_instance.generate_artistic_vcard_qr(
        vcard_details=default_vcard_data,
        output_filename="payload_test.png"
    )

    # Since we are now manually building the vCard string,
    # mock_make_vcard_data should not be called.
    mock_make_vcard_data.assert_not_called()

    # Instead, verify the contents of the string passed to segno.make
    mock_segno_make.assert_called_once()
    args, _ = mock_segno_make.call_args
    vcard_string = args[0]

    assert f"N:{default_vcard_data.n_familyname};{default_vcard_data.n_givenname}" in vcard_string
    assert f"FN:{default_vcard_data.fn}" in vcard_string
    assert f"DISPLAYNAME:{default_vcard_data.displayname}" in vcard_string
    assert f"EMAIL;TYPE=INTERNET,PREF:{default_vcard_data.email_internet}" in vcard_string
    assert f"TEL;TYPE=WORK,VOICE:{default_vcard_data.tel_work_voice}" in vcard_string
    assert f"ORG:{default_vcard_data.org}" in vcard_string
    assert f"TITLE:{default_vcard_data.title}" in vcard_string
    if default_vcard_data.url_work:
        for i, typed_url_item in enumerate(default_vcard_data.url_work):
            assert f"item{i+1}.URL:{typed_url_item.url}" in vcard_string
            assert f"item{i+1}.X-ABLabel:{typed_url_item.label}" in vcard_string


@patch("segno.helpers.make_vcard_data")
@patch("segno.make")
def test_vcard_payload_construction_minimal_fields(
    mock_segno_make: MagicMock,
    mock_make_vcard_data: MagicMock,
    qr_generator_instance: QRCodeGenerator
) -> None:
    """Test that VCardDataModel with minimal fields is handled correctly."""
    minimal_vcard_details = ConfigVCardDataModel(
        n_familyname="Minimal",
        n_givenname="Person",
        fn="Minimal Person FN",
        displayname="Minimal Person Display",
        email_internet="",
        tel_work_voice="",
        url_work=None,
        org="",
        title=""
    )

    qr_generator_instance.generate_artistic_vcard_qr(
        vcard_details=minimal_vcard_details,
        output_filename="minimal_payload_test.png"
    )
    # Since we are now manually building the vCard string,
    # mock_make_vcard_data should not be called.
    mock_make_vcard_data.assert_not_called()

    # Verify the contents of the string passed to segno.make
    mock_segno_make.assert_called_once()
    args, _ = mock_segno_make.call_args
    vcard_string = args[0]

    assert "N:Minimal;Person" in vcard_string
    assert "FN:Minimal Person FN" in vcard_string
    assert "DISPLAYNAME:Minimal Person Display" in vcard_string
    assert "EMAIL" not in vcard_string  # Should be omitted if empty
    assert "TEL" not in vcard_string    # Should be omitted if empty
    assert "URL" not in vcard_string    # Should be omitted if None
    assert "ORG" not in vcard_string    # Should be omitted if empty
    assert "TITLE" not in vcard_string  # Should be omitted if empty


@patch("segno.helpers.make_vcard_data")
@patch("segno.make")
def test_vcard_payload_construction_multiple_urls(
    mock_segno_make: MagicMock,
    mock_make_vcard_data: MagicMock,
    qr_generator_instance: QRCodeGenerator
) -> None:
    """
    Test construction with multiple URLs and other fields explicitly None.
    """
    multi_url_vcard_details = ConfigVCardDataModel(
        n_familyname="Url",
        n_givenname="Test",
        fn="Url Test FN",
        displayname="Url Test Display",
        url_work=[
            {"url": "http://url1.example.com", "label": "URL1"},
            {"url": "https://url2.example.org/path", "label": "URL2"}
        ],
        email_internet="",
        tel_work_voice="",
        org="",
        title=""
    )
    qr_generator_instance.generate_artistic_vcard_qr(
        vcard_details=multi_url_vcard_details,
        output_filename="multiurl_test.png"
    )
    mock_make_vcard_data.assert_not_called()

    mock_segno_make.assert_called_once()
    args, _ = mock_segno_make.call_args
    vcard_string = args[0]

    assert "N:Url;Test" in vcard_string
    assert "FN:Url Test FN" in vcard_string
    # Ensure url_work is not None before indexing for type safety
    if multi_url_vcard_details.url_work:
        assert f"item1.URL:{multi_url_vcard_details.url_work[0].url}" \
            in vcard_string
        assert f"item1.X-ABLabel:{multi_url_vcard_details.url_work[0].label}" \
            in vcard_string
        assert f"item2.URL:{multi_url_vcard_details.url_work[1].url}" \
            in vcard_string
        assert f"item2.X-ABLabel:{multi_url_vcard_details.url_work[1].label}" \
            in vcard_string


@pytest.mark.skipif(
    not cairo_library_available,
    reason="Cairo library (libcairo) could not be loaded by cairocffi."
)
def test_generate_artistic_vcard_qr_integration(
    qr_generator_instance: QRCodeGenerator,
    default_vcard_data: ConfigVCardDataModel,
    mock_project_root: Path
) -> None:
    """
    An integration-style test that actually generates a small QR code file.
    """
    output_filename = "integration_test_qr.png"
    expected_output_path = (
        qr_generator_instance.default_output_dir / output_filename
    )

    qr_generator_instance.default_output_dir.mkdir(parents=True, exist_ok=True)

    generated_path = qr_generator_instance.generate_artistic_vcard_qr(
        vcard_details=default_vcard_data,
        output_filename=output_filename,
        scale=1
    )

    assert generated_path == expected_output_path
    assert expected_output_path.exists()
    assert expected_output_path.is_file()
    assert expected_output_path.stat().st_size > 0

    expected_output_path.unlink()

    # To test that unlink works, we can assert that the file does NOT exist.
    assert not expected_output_path.exists()
