"""
Generates an artistic vCard QR code PNG image.

This script creates a vCard QR code containing contact information and
renders it as a PNG image with a specified SVG image as a background.
It utilizes the 'segno' library for QR code generation and artistic
rendering.

The script is structured into:
1.  Data models for vCard information using Pydantic for validation and
    clarity.
2.  A QRCodeGenerator class responsible for the QR code generation logic,
    promoting reusability and separation of concerns.
3.  A main execution block that utilizes these components to generate the
    QR code with predefined data for a specific contact.

Key improvements:
-   Uses Pydantic for robust vCard data modeling and validation.
-   Employs an object-oriented approach with a QRCodeGenerator class.
-   Improved error handling, particularly for file paths.
-   Clear separation of utility/data modeling logic from specific
    instantiation.
-   Enhanced type hinting and docstrings for better maintainability.
"""

from pathlib import Path, PureWindowsPath
from stat import S_ISREG

import segno
from PIL import PngImagePlugin

# Import VCardDataModel from config.py
from .config import VCardDataModel
from .utils import get_logger

logger = get_logger(module=__name__)


def _validate_output_filename(output_filename: str) -> str:
    """Return a safe, bare PNG filename before any output-path mutation."""
    output_path = Path(output_filename)
    windows_path = PureWindowsPath(output_filename)
    if (
        not output_filename
        or output_filename in {".", ".."}
        or "/" in output_filename
        or "\\" in output_filename
        or output_path.is_absolute()
        or windows_path.is_absolute()
        or bool(windows_path.drive)
        or output_path.name != output_filename
        or output_path.suffix != ".png"
    ):
        raise ValueError(
            "QR output filename must be a bare .png filename without path "
            f"separators or parent components: {output_filename!r}"
        )
    return output_filename


def _remove_output_target(output_path: Path) -> None:
    """Remove exactly one prior QR output without traversing directories."""
    try:
        output_path.unlink()
    except FileNotFoundError:
        return


def _cleanup_output_target(output_path: Path) -> None:
    """Best-effort cleanup for failed QR rendering without recursion."""
    try:
        _remove_output_target(output_path)
    except OSError:
        try:
            if not output_path.is_symlink() and output_path.is_dir():
                output_path.rmdir()
        except OSError:
            pass


def _validate_png_output(output_path: Path) -> None:
    """Require a freshly rendered, regular PNG file at ``output_path``."""
    try:
        output_stat = output_path.lstat()
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"QR renderer did not create an output: {output_path}"
        ) from exc

    if not S_ISREG(output_stat.st_mode):
        raise RuntimeError(f"QR renderer did not create a regular file: {output_path}")
    if output_stat.st_size == 0:
        raise RuntimeError(f"QR renderer did not create a non-empty PNG: {output_path}")

    try:
        with output_path.open("rb") as generated_file:
            # Pillow emits chunk-level DEBUG records through stdlib logging.
            # Suppress only this module while verifying: pytest's live logging
            # can otherwise bind a Click-isolated stream that is already closed.
            png_logger_was_disabled = PngImagePlugin.logger.disabled
            PngImagePlugin.logger.disabled = True
            try:
                generated_image = PngImagePlugin.PngImageFile(generated_file)
                generated_image.verify()
            finally:
                PngImagePlugin.logger.disabled = png_logger_was_disabled
    except (OSError, SyntaxError, ValueError) as exc:
        raise RuntimeError(
            f"QR renderer created an invalid PNG: {output_path}"
        ) from exc


def _validate_or_remove_png_output(output_path: Path) -> None:
    """Validate a QR output and remove any invalid file-like artifact."""
    try:
        _validate_png_output(output_path)
    except (OSError, RuntimeError):
        _cleanup_output_target(output_path)
        raise


class QRCodeGenerator:
    """
    Handles the generation and saving of QR codes, focusing on artistic vCard
    QR codes.
    """

    def __init__(
        self,
        default_background_path: Path | None,
        default_output_dir: Path,
        default_scale: int = 25,
    ):
        """
        Initializes the QRCodeGenerator.

        Args:
            default_background_path: Default path to the background SVG image.
                                     Pass None to skip background by default.
            default_output_dir: Default directory to save generated QR codes.
            default_scale: Default scale factor for the QR code.

        Raises:
            FileNotFoundError: If default_background_path is given but does
                               not exist.
            OSError: If the default_output_dir cannot be created.
        """
        self.default_background_path = default_background_path
        self.default_output_dir = default_output_dir
        self.default_scale = default_scale

        if self.default_background_path is not None:
            if not self.default_background_path.is_file():
                msg = (
                    f"Default background SVG not found: {self.default_background_path}"
                )
                logger.error(msg)
                raise FileNotFoundError(msg)
        try:
            self.default_output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            msg = f"Could not create output directory {self.default_output_dir}: {e}"
            logger.error(msg)
            raise

    def generate_artistic_vcard_qr(
        self,
        vcard_details: VCardDataModel,
        output_filename: str,
        background_path: Path | None = None,
        scale: int | None = None,
        error_correction: str = "H",
    ) -> Path:
        """
        Generates an artistic vCard QR code and saves it as a PNG file.

        Args:
            vcard_details: A VCardDataModel object with contact information.
            output_filename: The filename for the output PNG (e.g., "qr.png").
            background_path: Path to the SVG background image. Uses
                             generator's default if None.
            scale: Scale factor for the QR code. Uses generator's default
                   if None.
            error_correction: QR code error correction level.
                              Must be one of 'L', 'M', 'Q', 'H'.

        Returns:
            The path to the generated PNG file.

        Raises:
            FileNotFoundError: If background_path does not exist.
            ValueError: If error_correction level is invalid.
            Exception: For other QR code generation or saving failures.
        """
        bg_path = background_path or self.default_background_path
        current_scale = scale or self.default_scale
        validated_output_filename = _validate_output_filename(output_filename)
        output_path = self.default_output_dir / validated_output_filename

        # Clear the exact target before validating inputs so every invocation is
        # fail-closed with respect to stale output bytes.
        _remove_output_target(output_path)

        if bg_path is not None and not bg_path.is_file():
            msg = f"Background SVG for QR code not found: {bg_path}"
            logger.error(msg)
            raise FileNotFoundError(msg)

        if error_correction not in ("L", "M", "Q", "H"):
            msg = f"Invalid QR error correction level: {error_correction}"
            logger.error(msg)
            raise ValueError(
                "Error correction level must be one of 'L', 'M', 'Q', 'H'."
            )

        generation_complete = False
        try:
            # Manually construct vCard 3.0 string
            vcard_lines = [
                "BEGIN:VCARD",
                "VERSION:3.0",
                f"N:{vcard_details.n_familyname};{vcard_details.n_givenname};;;",
                f"FN:{vcard_details.fn}",
                f"DISPLAYNAME:{vcard_details.displayname}",
            ]
            if vcard_details.org:
                vcard_lines.append(f"ORG:{vcard_details.org}")
            if vcard_details.title:
                vcard_lines.append(f"TITLE:{vcard_details.title}")
            if vcard_details.email_internet:
                vcard_lines.append(
                    f"EMAIL;TYPE=INTERNET,PREF:{vcard_details.email_internet}"
                )
            if vcard_details.tel_work_voice:
                vcard_lines.append(
                    f"TEL;TYPE=WORK,VOICE:{vcard_details.tel_work_voice}"
                )

            if vcard_details.url_work:
                for i, typed_url_item in enumerate(vcard_details.url_work):
                    # For Apple compatibility and general labeling,
                    # use itemX.URL and itemX.X-ABLabel
                    vcard_lines.append(f"item{i + 1}.URL:{typed_url_item.url}")
                    vcard_lines.append(f"item{i + 1}.X-ABLabel:{typed_url_item.label}")

            # Add other fields as necessary, e.g., PHOTO, ADR

            vcard_lines.append("END:VCARD")
            card_payload = "\n".join(vcard_lines)

            qrcode = segno.make(card_payload, error=error_correction, micro=False)

            logger.info(
                f"Generating artistic QR code to {output_path} "
                f"with background {bg_path}"
            )
            # Ensure .to_artistic is callable or handle appropriately
            if (
                bg_path is not None
                and hasattr(qrcode, "to_artistic")
                and callable(qrcode.to_artistic)
            ):
                qrcode.to_artistic(
                    background=str(bg_path),
                    target=str(output_path),
                    scale=current_scale,
                    # Additional artistic parameters can be specified here
                    # E.g., kind='png' (default), border, dark module color,
                    # etc.
                )
            elif bg_path is None:
                # No background provided — save a standard QR PNG
                logger.info(
                    "No background path provided; saving plain QR code to "
                    f"{output_path}"
                )
                qrcode.save(str(output_path), scale=current_scale, kind="png")
            else:
                # Fallback or error if .to_artistic is not available
                # as expected
                logger.error(
                    "qrcode object does not have a callable 'to_artistic' method."
                )
                # As a simple fallback, save as standard PNG, though this loses
                # artistry:
                # qrcode.save(str(output_path), scale=current_scale,
                #             kind='png')
                # Or, raise an error if artistic rendering is critical:
                raise AttributeError("Artistic QR rendering not available.")

            _validate_or_remove_png_output(output_path)
            generation_complete = True
            logger.info(
                "Successfully generated QR code: {output_path}", output_path=output_path
            )
            return output_path
        except FileNotFoundError:  # Should be caught by earlier check
            logger.error("File operation failed: Background or target path issue.")
            raise
        except ValueError as ve:  # For invalid error_correction/segno issues
            logger.error("Value error during QR generation: {ve}", ve=ve)
            raise
        except Exception as e:
            logger.error(
                f"An unexpected error during QR code generation: {e}",
                exc_info=True,  # exc_info=True logs the full traceback
            )
            raise
        finally:
            if not generation_complete:
                _cleanup_output_target(output_path)


# Part 2: Specific Logic and Instantiation

# The specific vCard data for Wyatt Walsh will now be loaded from config
# (handled by the CLI/config loading mechanism)
# wyatt_vcard_info = VCardDataModel(...)

if __name__ == "__main__":
    # Define paths relative to the project root for portability
    # Assumes this script is in 'scripts/' directory relative to project root.
    try:
        project_root = Path(__file__).resolve().parent.parent
        default_bg_svg_path = None  # icon.svg removed; background is optional
        default_output_directory = project_root / ".github" / "assets" / "img"

        # Initialize the QR code generator
        qr_gen = QRCodeGenerator(
            default_background_path=default_bg_svg_path,
            default_output_dir=default_output_directory,
            default_scale=25,  # Default scale for the artistic QR code
        )

        logger.info(
            "Skipping direct QR generation in __main__ block of qr.py. Use CLI."
        )

    except FileNotFoundError as fnf_error:
        logger.error("Setup or file error: {fnf_error}", fnf_error=fnf_error)
    except ValueError as val_error:
        logger.error(
            "Data validation or configuration error: {val_error}", val_error=val_error
        )
    except Exception as e_main:
        logger.error(
            f"An unexpected error occurred in the main execution block: {e_main}",
            exc_info=True,
        )
