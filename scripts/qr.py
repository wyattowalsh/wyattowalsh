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

from pathlib import Path
from typing import List, Optional, Union

import segno
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from segno import helpers

# Import VCardDataModel from config.py
from scripts.config import VCardDataModel

# Import the logger from utils.py
from scripts.utils import get_logger

logger = get_logger(module=__name__)

# Part 1: Utility Logic and Data Models

# Remove the local VCardData model, as we'll use the one from config.py
# class VCardData(BaseModel):
# ... (removed local VCardData definition) ...

class QRCodeGenerator:
    """
    Handles the generation and saving of QR codes, focusing on artistic vCard
    QR codes.
    """

    def __init__(
        self,
        default_background_path: Path,
        default_output_dir: Path,
        default_scale: int = 25,
    ):
        """
        Initializes the QRCodeGenerator.

        Args:
            default_background_path: Default path to the background SVG image.
            default_output_dir: Default directory to save generated QR codes.
            default_scale: Default scale factor for the QR code.

        Raises:
            FileNotFoundError: If the default_background_path does not exist.
            OSError: If the default_output_dir cannot be created.
        """
        self.default_background_path = default_background_path
        self.default_output_dir = default_output_dir
        self.default_scale = default_scale

        if not self.default_background_path.is_file():
            msg = f"Default background SVG not found: {self.default_background_path}"
            logger.error(msg)
            raise FileNotFoundError(msg)
        try:
            self.default_output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            msg = (
                f"Could not create output directory {self.default_output_dir}: {e}"
            )
            logger.error(msg)
            raise

    def generate_artistic_vcard_qr(
        self,
        vcard_details: VCardDataModel,
        output_filename: str,
        background_path: Optional[Path] = None,
        scale: Optional[int] = None,
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
        output_path = self.default_output_dir / output_filename

        if not bg_path.is_file():
            msg = f"Background SVG for QR code not found: {bg_path}"
            logger.error(msg)
            raise FileNotFoundError(msg)

        if error_correction not in ("L", "M", "Q", "H"):
            msg = f"Invalid QR error correction level: {error_correction}"
            logger.error(msg)
            raise ValueError(
                "Error correction level must be one of 'L', 'M', 'Q', 'H'."
            )

        try:
            # Pass arguments directly to make_vcard_data
            # segno handles None values by omitting those vCard fields.
            # Explicitly convert Pydantic HttpUrl to str for `segno`
            urls_as_str: Union[List[str], str, None] = None
            if isinstance(vcard_details.url_work, list):
                urls_as_str = [str(u) for u in vcard_details.url_work]
            elif vcard_details.url_work:
                urls_as_str = str(vcard_details.url_work)

            card_payload = helpers.make_vcard_data(
                name=f"{vcard_details.n_familyname},{vcard_details.n_givenname}",
                displayname=vcard_details.displayname,
                email=vcard_details.email_internet,
                phone=vcard_details.tel_work_voice,
                url=urls_as_str,
                org=vcard_details.org,
                title=vcard_details.title,
            )

            qrcode = segno.make(card_payload, error=error_correction, micro=False)

            logger.info(
                "Generating artistic QR code to %s with background %s",
                output_path,
                bg_path,
            )
            # Ensure .to_artistic is callable or handle appropriately
            if hasattr(qrcode, "to_artistic") and callable(qrcode.to_artistic):
                qrcode.to_artistic(
                    background=str(bg_path),
                    target=str(output_path),
                    scale=current_scale,
                    # Additional artistic parameters can be specified here
                    # E.g., kind='png' (default), border, dark module color, etc.
                )
            else:
                # Fallback or error if .to_artistic is not available as expected
                logger.error(
                    "qrcode object does not have a callable 'to_artistic' method."
                )
                # As a simple fallback, save as standard PNG, though this loses
                # artistry:
                # qrcode.save(str(output_path), scale=current_scale, kind='png')
                # Or, raise an error if artistic rendering is critical:
                raise AttributeError("Artistic QR rendering not available.")

            logger.info("Successfully generated QR code: %s", output_path)
            return output_path
        except FileNotFoundError:  # Should be caught by earlier check
            logger.error("File operation failed: Background or target path issue.")
            raise
        except ValueError as ve:  # For invalid error_correction or segno issues
            logger.error("Value error during QR generation: %s", ve)
            raise
        except Exception as e:
            logger.error(
                "An unexpected error during QR code generation: %s",
                e,
                exc_info=True,  # exc_info=True logs the full traceback
            )
            raise


# Part 2: Specific Logic and Instantiation

# Define the specific vCard data for Wyatt Walsh using the VCardDataModel
# Ensure HttpUrl is used for URL strings for Pydantic validation and type
# safety
wyatt_vcard_info = VCardDataModel(
    n_familyname="Walsh",
    n_givenname="Wyatt",
    fn="Wyatt O. Walsh",
    displayname="Wyatt Walsh",
    email_internet="wyattowalsh@gmail.com",
    tel_work_voice="2096022545",
    url_work=[
        "https://www.w4w.dev/",
        "https://www.linkedin.com/in/wyattowalsh",
        "https://www.github.com/wyattowalsh",
    ],
    org="Personal Portfolio Project",
    title="Developer & Tech Enthusiast"
)

if __name__ == "__main__":
    # Define paths relative to the project root for portability
    # Assumes this script is in 'scripts/' directory relative to project root.
    try:
        project_root = Path(__file__).resolve().parent.parent
        default_bg_svg_path = project_root / ".github" / "assets" / "img" / "icon.svg"
        default_output_directory = project_root / ".github" / "assets" / "img"

        # Initialize the QR code generator
        qr_gen = QRCodeGenerator(
            default_background_path=default_bg_svg_path,
            default_output_dir=default_output_directory,
            default_scale=25,  # Default scale for the artistic QR code
        )

        # Generate the QR code for Wyatt Walsh
        generated_file_path = qr_gen.generate_artistic_vcard_qr(
            vcard_details=wyatt_vcard_info,
            output_filename="qr.png",
            # Specific overrides can be passed here:
            # background_path=Path("custom/path/to/bg.svg"),
            # scale=30,
            # error_correction='M'
        )
        logger.info("Script finished. QR code available at: %s", generated_file_path)

    except FileNotFoundError as fnf_error:
        logger.error("Setup or file error: %s", fnf_error)
    except ValueError as val_error:
        logger.error("Data validation or configuration error: %s", val_error)
    except Exception as e_main:
        logger.error(
            "An unexpected error occurred in the main execution block: %s",
            e_main,
            exc_info=True,
        )
        # exc_info=True in logger.error will include traceback
        # exc_info=True in logger.error will include traceback
