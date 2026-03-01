"""
Advanced Word Cloud Generation Module

This module provides a comprehensive, configurable, and aesthetically-focused
system for generating word cloud images from various text sources. It leverages
the 'wordcloud' library for core generation, 'Pillow' (PIL) for image
manipulation, and Pydantic V2 for validated configuration. The design
emphasizes flexibility, ease of use, modern software engineering best
practices (OOP, DRY), and the creation of visually appealing outputs based
on color theory and data visualization principles.

Key Features:
- **Comprehensive Pydantic V2 Configuration**: Uses `WordCloudSettings` for
  clear, validated, and easy-to-manage settings, promoting type safety and
  explicit control over every aspect of the word cloud generation.
- **Advanced Appearance Customization**: Offers extensive control over:
    - Fonts (custom TTF/OTF files).
    - Color Schemes: Matplotlib colormaps, multiple built-in custom color
      functions (primary, analogous, complementary, triadic), and direct
      palette overrides.
    - Background Colors: Supports CSS color formats, including RGBA for
      transparent backgrounds.
    - Word Layout: Control over horizontal/vertical preference, scaling,
      padding, and relative scaling of word sizes.
- **Image Masking**: Supports PNG images (recommended) and SVGs (with
  appropriate system libraries like librsvg or CairoSVG for Pillow) as masks
  to create word clouds in specific shapes. Masks are intelligently processed.
- **Multiple Input Methods**: Generate word clouds from:
    - Direct text strings.
    - Pre-computed word frequencies (dictionaries).
    - Lists of words with optional weights.
- **Dynamic and Informative Logging**: Integrates with the project's
  centralized logging setup (`scripts.utils.get_logger`) for detailed
  operational insights, warnings, and easier debugging.
- **Object-Oriented Design**: Employs a `WordCloudGenerator` class
  encapsulating the generation logic, promoting reusability, testability,
  and maintainability.
- **Aesthetic Enhancements & Color Theory**: Includes custom color functions
  designed with color harmony principles (analogous, complementary, triadic)
  to produce visually engaging word clouds suitable for professional contexts.
- **Helper Utilities & Examples**: Provides predefined default paths and
  comprehensive example implementations in the `if __name__ == "__main__":`
  block for common use cases and showcasing advanced features.

Primary Goal:
To offer a reliable, developer-friendly, and highly customizable tool for
creating sophisticated and visually appealing word clouds, suitable for project
documentation, README files, presentations, data visualization dashboards, or
any context where visual representation of text data is beneficial.
"""

from __future__ import annotations

import random
import re  # Add re for parsing list items
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, Union
import functools # Added for functools.partial

# Third-Party Imports
import matplotlib.colors as mcolors
import numpy as np
from PIL import Image
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    FilePath,
    field_validator,
    model_validator,
)
from wordcloud import STOPWORDS, WordCloud  # type: ignore

# Local Application/Library Specific Imports
from .utils import get_logger

# Initialize a dedicated logger for this module.
logger = get_logger(module=__name__)

# ------------------------------------------------------------------------------
# Constants & Defaults
# ------------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ASSETS_DIR = PROJECT_ROOT / ".github" / "assets"
DEFAULT_FONTS_DIR = DEFAULT_ASSETS_DIR / "fonts"
DEFAULT_IMG_DIR = DEFAULT_ASSETS_DIR / "img"  # Used for various images
DEFAULT_MASKS_DIR = DEFAULT_ASSETS_DIR / "img"  # Default mask location

DEFAULT_FONT_PATH_STR = str(DEFAULT_FONTS_DIR / "Montserrat-ExtraBold.ttf")
DEFAULT_FONT_PATH: Optional[Path] = (
    Path(DEFAULT_FONT_PATH_STR)
    if Path(DEFAULT_FONT_PATH_STR).exists()
    else None
)

# icon.svg assumed as mask; PNGs are generally more robust.
DEFAULT_MASK_PATH_STR = str(DEFAULT_MASKS_DIR / "icon.svg")
DEFAULT_MASK_PATH: Optional[Path] = (
    Path(DEFAULT_MASK_PATH_STR)
    if Path(DEFAULT_MASK_PATH_STR).exists()
    else None
)
DEFAULT_OUTPUT_DIR = DEFAULT_IMG_DIR / "wordclouds"  # Output sub-dir

# Specific paths for profile assets
PROFILE_IMG_OUTPUT_DIR = DEFAULT_ASSETS_DIR / "img"
TOPICS_MD_PATH = DEFAULT_ASSETS_DIR / "topics.md"
LANGUAGES_MD_PATH = DEFAULT_ASSETS_DIR / "languages.md"

# ------------------------------------------------------------------------------
# Pydantic Configuration Models for Word Cloud Settings
# ------------------------------------------------------------------------------


class WordCloudSettings(BaseModel):
    """
    Configuration settings for generating a word cloud using Pydantic V2.

    This model defines all configurable parameters with type validation,
    sensible defaults, and detailed descriptions. It enforces strict schema
    adherence (`extra='forbid') and re-validates on assignment
    (`validate_assignment=True`).
    """

    model_config = ConfigDict(
        validate_assignment=True, extra="forbid", arbitrary_types_allowed=True
    )

    text: Optional[str] = Field(
        default=None,
        description=(
            "Primary input text for word cloud. If None, 'prompt' or "
            "'frequencies' must be used."
        ),
    )
    width: int = Field(
        default=1200,
        ge=100,
        description="Width of the output image in pixels (min: 100).",
    )
    height: int = Field(
        default=800,
        ge=100,
        description="Height of the output image in pixels (min: 100).",
    )
    background_color: str = Field(
        default="rgba(255, 255, 255, 0)",  # Default to transparent white
        description=(
            "Background color (CSS format, e.g., 'white', '#FFF', "
            "'rgb(0,0,0)', 'rgba(0,0,0,0)' for transparent)."
        ),
    )
    mask_path: Optional[FilePath] = Field(
        default=DEFAULT_MASK_PATH,
        description=(
            "Path to an image file (PNG recommended, SVG needs Pillow backend "
            "like librsvg) for masking. If None, rectangular."
        ),
    )
    font_path: Optional[FilePath] = Field(
        default=DEFAULT_FONT_PATH,
        description=(
            "Path to a .ttf or .otf font file. If None, WordCloud's default "
            "font is used."
        ),
    )
    colormap: Optional[str] = Field(
        default="viridis",
        description=(
            "Matplotlib colormap name (e.g., 'viridis', 'plasma'). "
            "Ignored if 'custom_color_func_name' or 'color_palette_override' "
            "(with compatible func) is used. See: "
            "https://matplotlib.org/stable/gallery/color/"
            "colormap_reference.html"
        ),
    )
    custom_color_func_name: Optional[str] = Field(
        default=None,
        description=(
            "Name of a registered custom color function "
            "(e.g., 'primary_color_func'). Overrides 'colormap'. "
            "Can work with 'color_palette_override'."
        ),
    )
    color_palette_override: Optional[List[str]] = Field(
        default=None,
        description=(
            "A list of hex color strings. If provided and "
            "'custom_color_func_name' is 'primary_color_func' (or similar), "
            "this palette will be used for word coloring."
        ),
    )
    stopwords: List[str] = Field(
        default_factory=list,
        description=(
            "List of stopwords to exclude, added to WordCloud's defaults."
        ),
    )
    max_words: int = Field(
        default=200,
        ge=10,
        description="Maximum number of words to display (min: 10).",
    )
    contour_width: float = Field(
        default=0.0,
        ge=0.0,
        description=(
            "Width of the contour around the mask shape (0 for no contour)."
        ),
    )
    contour_color: str = Field(
        default="#1EAE98",  # Default: Vibrant Teal
        description=(
            "Color of the mask contour (CSS format), if contour_width > 0."
        ),
    )
    min_font_size: int = Field(
        default=12,
        ge=4,
        description="Minimum font size for the smallest words (min: 4).",
    )
    max_font_size: Optional[int] = Field(
        default=None,
        description=(
            "Maximum font size for largest words. If None, auto-determined by "
            "WordCloud."
        ),
    )
    prefer_horizontal: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description=(
            "Ratio of words drawn horizontally "
            "(0.0 to 1.0; 1.0 is all horizontal)."
        ),
    )
    scale: float = Field(
        default=1.2,
        ge=0.1,
        description="Scaling factor for word sizes and spacing (min: 0.1).",
    )
    padding: int = Field(
        default=2,
        ge=0,
        description="Padding around each word in pixels (min: 0).",
    )
    relative_scaling: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description=(
            "Importance of word frequency vs. rank for font size "
            "(0: rank, 1: frequency)."
        ),
    )
    output_dir: Path = Field(
        default=DEFAULT_OUTPUT_DIR,
        description=(
            "Directory where the generated word cloud image will be saved."
        ),
    )
    output_filename: str = Field(
        default="word_cloud.svg",
        description=(
            "Filename for the output image (e.g., 'my_cloud.svg'). "
            "Auto-appends extension based on 'output_format' if needed."
        ),
    )
    output_format: Literal["png", "svg"] = Field(
        default="svg",
        description="Output format for the word cloud: 'png' or 'svg'."
    )
    prompt: Optional[str] = Field(
        default=None,
        description=(
            "Optional fallback text if 'text' is None and no 'frequencies' "
            "are given."
        ),
    )

    @field_validator("mask_path", "font_path", mode="before")
    @classmethod
    def _validate_file_path_exists(
        cls,
        v: Optional[Union[str, Path]],
        info: Any,  # Pydantic V2: use FieldValidationInfo if needed
    ) -> Optional[Path]:
        """Validates that 'mask_path' and 'font_path' exist and are files
        if provided."""
        field_name = info.field_name
        if v is None:
            logger.debug(
                f"Path for '{field_name}' is None, skipping existence check."
            )
            return None

        p = Path(v).resolve()
        if not p.exists():
            err_msg = f"Path for '{field_name}' does not exist: {p}."
            logger.error(err_msg)
            raise ValueError(err_msg)
        if not p.is_file():
            err_msg = f"Path for '{field_name}' is not a file: {p}."
            logger.error(err_msg)
            raise ValueError(err_msg)

        logger.debug(f"Path for '{field_name}' validated successfully: {p}")
        return p

    @model_validator(mode="after")
    def _validate_output_filename_ext(self) -> "WordCloudSettings":
        """Ensures output_filename has a valid image extension matching
        output_format, defaulting to .png or .svg respectively."""
        filename_lower = self.output_filename.lower()
        target_extension = f".{self.output_format}"

        # Check if it already has the correct extension
        if filename_lower.endswith(target_extension):
            return self

        # Check if it has any other known image/vector extension
        known_extensions = (
            ".png", ".jpg", ".jpeg", ".gif",
            ".bmp", ".tiff", ".svg"
        )
        current_ext_found = ""
        for ext in known_extensions:
            if filename_lower.endswith(ext):
                current_ext_found = ext
                break

        original_name_stem = self.output_filename
        if current_ext_found:
            # Strip the incorrect extension
            original_name_stem = self.output_filename[:-len(current_ext_found)]

        self.output_filename = original_name_stem + target_extension
        logger.warning(
            f"Output filename '{self.output_filename}' was adjusted to "
            f"'{self.output_filename}' to match output_format "
            f"'{self.output_format}'."
        )
        return self

    def get_full_output_path(self) -> Path:
        """
        Constructs the full absolute path for the output image,
        ensuring directory exists.
        """
        output_dir_path = Path(self.output_dir)
        if not output_dir_path.is_absolute():
            output_dir_path = (PROJECT_ROOT / output_dir_path).resolve()

        output_dir_path.mkdir(parents=True, exist_ok=True)
        full_path = (output_dir_path / self.output_filename).resolve()
        logger.debug(f"Determined full output path: {full_path}")
        return full_path


# ------------------------------------------------------------------------------
# Custom Color Functions for Word Clouds
# ------------------------------------------------------------------------------


def primary_color_func(
    word: str,
    font_size: Optional[int],
    position: Tuple[int, int],
    orientation: Optional[int],
    random_state: Optional[random.Random] = None,
    color_palette: Optional[List[str]] = None,
    **kwargs: Any,
) -> str:
    """
    Generates word colors based on a primary color or a provided palette.

    If `color_palette` is given, randomly selects from it. Otherwise, varies
    the lightness of a predefined primary hex color (#1EAE98, a vibrant teal).
    Aims for a modern, clean aesthetic.
    """
    if color_palette and random_state:
        return random_state.choice(color_palette)

    default_primary_hex = "#1EAE98"  # Vibrant Teal
    base_lightness = 0.65

    h, s, _ = mcolors.rgb_to_hsv(mcolors.to_rgb(default_primary_hex))

    final_l: float
    if random_state:
        adj_l = base_lightness + random_state.uniform(-0.30, 0.20)
        final_l = max(0.35, min(0.85, adj_l))  # Clamp lightness
    else:
        final_l = base_lightness

    r_val, g_val, b_val = mcolors.hsv_to_rgb((h, s, final_l))
    return mcolors.to_hex((r_val, g_val, b_val))


def analogous_color_func(
    word: str,
    font_size: Optional[int],
    position: Tuple[int, int],
    orientation: Optional[int],
    random_state: Optional[random.Random] = None,
    base_hue: float = 0.5,  # Default: Cyan/Teal region (0-1 HSV scale)
    hue_range: float = 0.1,
    saturation_range: Tuple[float, float] = (0.6, 0.9),
    lightness_range: Tuple[float, float] = (0.4, 0.7),
    **kwargs: Any,
) -> str:
    """
    Generates analogous colors centered around a `base_hue`.
    Analogous colors are adjacent on the color wheel, creating harmonious
    visuals.
    """
    current_random_state = random_state if random_state else random.Random()

    hue_offset = current_random_state.uniform(-hue_range, hue_range)
    hue = (base_hue + hue_offset) % 1.0  # Ensure hue is within [0, 1)

    saturation = current_random_state.uniform(
        saturation_range[0], saturation_range[1]
    )
    lightness = current_random_state.uniform(
        lightness_range[0], lightness_range[1]
    )

    r_val, g_val, b_val = mcolors.hsv_to_rgb((hue, saturation, lightness))
    return mcolors.to_hex((r_val, g_val, b_val))


def complementary_color_func(
    word: str,
    font_size: Optional[int],
    position: Tuple[int, int],
    orientation: Optional[int],
    random_state: Optional[random.Random] = None,
    base_hue: float = 0.58,  # Default: A nice blue/cyan
    saturation_range: Tuple[float, float] = (0.65, 0.95),
    lightness_range: Tuple[float, float] = (0.45, 0.75),
    **kwargs: Any,
) -> str:
    """
    Generates colors from a base hue and its complement.
    Complementary colors are opposite on the color wheel, creating high
    contrast.
    """
    current_random_state = random_state if random_state else random.Random()

    chosen_hue = (
        base_hue
        if current_random_state.random() < 0.6
        else (base_hue + 0.5) % 1.0
    )

    saturation = current_random_state.uniform(
        saturation_range[0], saturation_range[1]
    )
    lightness = current_random_state.uniform(
        lightness_range[0], lightness_range[1]
    )
    final_hue = (
        chosen_hue + current_random_state.uniform(-0.02, 0.02)
    ) % 1.0

    r_val, g_val, b_val = mcolors.hsv_to_rgb(
        (final_hue, saturation, lightness)
    )
    return mcolors.to_hex((r_val, g_val, b_val))


def triadic_color_func(
    word: str,
    font_size: Optional[int],
    position: Tuple[int, int],
    orientation: Optional[int],
    random_state: Optional[random.Random] = None,
    base_hue: float = 0.7,  # Default: A purple/violet
    saturation_range: Tuple[float, float] = (0.6, 0.9),
    lightness_range: Tuple[float, float] = (0.4, 0.75),
    **kwargs: Any,
) -> str:
    """
    Generates colors from a triadic scheme based on `base_hue`.
    Triadic colors are evenly spaced around the color wheel.
    """
    current_random_state = random_state if random_state else random.Random()

    hue_choices = [
        base_hue,
        (base_hue + 1 / 3) % 1.0,
        (base_hue + 2 / 3) % 1.0,
    ]
    chosen_hue_base = current_random_state.choice(hue_choices)

    saturation = current_random_state.uniform(
        saturation_range[0], saturation_range[1]
    )
    lightness = current_random_state.uniform(
        lightness_range[0], lightness_range[1]
    )
    final_hue = (
        chosen_hue_base + current_random_state.uniform(-0.02, 0.02)
    ) % 1.0

    r_val, g_val, b_val = mcolors.hsv_to_rgb(
        (final_hue, saturation, lightness)
    )
    return mcolors.to_hex((r_val, g_val, b_val))


CUSTOM_COLOR_FUNCTIONS: Dict[str, Callable[..., str]] = {
    "primary_color_func": primary_color_func,
    "analogous_color_func": analogous_color_func,
    "complementary_color_func": complementary_color_func,
    "triadic_color_func": triadic_color_func,
}

# ------------------------------------------------------------------------------
# Markdown Parsing for Word Cloud Frequencies
# ------------------------------------------------------------------------------


def parse_markdown_for_word_cloud_frequencies(
    md_file_path: Path,
) -> Dict[str, float]:
    """
    Parses a Markdown file to extract terms and their frequencies for a
    word cloud.

    Terms are extracted from list items (e.g., '- TermName' or
    '- [Term Name](link)'). Frequencies are the count of each unique term.

    Args:
        md_file_path: Path to the Markdown file (e.g., topics.md,
                      languages.md).

    Returns:
        A dictionary mapping terms (str) to their frequencies (float).

    Raises:
        FileNotFoundError: If the specified Markdown file does not exist.
        IOError: If there's an error reading the file.

    Example Markdown structure:
        ## Some Category
        - Python
        - [JavaScript](some_url) - description
        - Python

    Example output:
        {"Python": 2.0, "JavaScript": 1.0}
    """
    if not md_file_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {md_file_path}")

    logger.info(f"Parsing {md_file_path.name} for word cloud frequencies")

    term_frequencies: Dict[str, float] = defaultdict(float)  # Use defaultdict

    try:
        with open(md_file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except IOError as e:
        logger.error(f"Error reading file {md_file_path}: {e}")
        raise

    lines = content.split('\n')
    # Regex to capture the term from lines like:
    # - Term
    # - [Term Name](...)
    # - [Term Name]
    # It will try to capture the content inside brackets if present,
    # otherwise, the text after '- '.
    term_pattern = re.compile(r"""
        ^\s*-\s+                # Starts with '- ' (with optional leading whitespace)
        (?:
            \[([^\]]+)\]        # Alt 1: Capture content in brackets (e.g., [Term])
            .*                  # Consume URL, description, anything after brackets
            |                   # OR
            ([^\s].+?)          # Alt 2: Capture plain text (non-greedy)
            (?:\s+-\s+.*)?      # Optionally ignore ' - description'
        )
        $                       # End of line
    """, re.VERBOSE)

    for line in lines:
        line = line.strip()
        match = term_pattern.match(line)
        if match:
            # Prefer content in brackets (group 1), else plain term (group 2)
            term = match.group(1) or match.group(2)
            if term:
                cleaned_term = term.strip()
                # Basic filtering for very short/non-descriptive terms
                if len(cleaned_term) > 1 and cleaned_term.lower() not in [
                    "readme", "license", "docs", "blog", "site", "test",
                    "demo", "example", "examples", "template", "templates",
                    "script", "scripts", "tool", "tools", "util", "utils",
                    "lib", "libs", "framework", "app", "cli", "api", "sdk",
                    "plugin", "theme", "config", "core", "main", "data",
                    "model", "models", "package",
                ]:
                    term_frequencies[cleaned_term] += 1.0
                    logger.debug(
                        f"Found term: '{cleaned_term}', "
                        f"new count: {term_frequencies[cleaned_term]}"
                    )
        elif (
            line.startswith("## ") 
            and line[3:].strip().lower() == "contents"
        ):
            logger.debug("Skipping 'Contents' section.")

    # Log summary statistics
    if term_frequencies:
        total_unique_terms = len(term_frequencies)
        total_occurrences = sum(term_frequencies.values())
        logger.info(
            f"Parsed {total_unique_terms} unique terms with a total of "
            f"{total_occurrences:.0f} occurrences from {md_file_path.name}."
        )
    else:
        logger.warning(f"No terms found in {md_file_path.name}")

    return dict(
        term_frequencies
    )  # Convert back to dict, good practice


# ------------------------------------------------------------------------------
# Core Word Cloud Generation Logic
# ------------------------------------------------------------------------------


class WordCloudGenerator:
    """
    Manages the creation and customization of word cloud images.

    This class encapsulates the logic for loading settings, processing image
    masks, and utilizing the WordCloud library to generate and save word
    cloud images. It is designed to be highly configurable and reusable.
    """

    def __init__(
        self, base_settings: Optional[WordCloudSettings] = None
    ) -> None:  # Corrected comment spacing
        """
        Initializes the WordCloudGenerator.

        Args:
            base_settings: An optional `WordCloudSettings` object.
                           If None, default settings will be used.
        """
        self.settings = base_settings if base_settings else WordCloudSettings()

        mask_name = "None"
        font_name = "Default"

        current_mask_path = self.settings.mask_path
        if isinstance(current_mask_path, Path):
            if current_mask_path.is_file():
                mask_name = current_mask_path.name
            else:
                # Path object exists but is not a file (e.g., a directory)
                logger.warning(
                    f"Configured mask_path '{current_mask_path}' exists but is not a file. Masking may fail or be disabled."
                )
                # mask_name remains "None" or could be set to indicate an issue
        elif current_mask_path is not None:
            # This case should ideally be caught by Pydantic's FilePath validation
            # if the input was a non-None, non-Path value.
            logger.warning(
                f"Configured mask_path '{current_mask_path}' is not a valid Path object after settings initialization. Type: {type(current_mask_path)}. Masking disabled."
            )

        current_font_path = self.settings.font_path
        if isinstance(current_font_path, Path):
            if current_font_path.is_file():
                font_name = current_font_path.name
            else:
                logger.warning(
                    f"Configured font_path '{current_font_path}' exists but is not a file. Default font may be used."
                )
        elif current_font_path is not None:
            logger.warning(
                f"Configured font_path '{current_font_path}' is not a valid Path object after settings initialization. Type: {type(current_font_path)}. Default font may be used."
            )

        logger.info(
            "WordCloudGenerator initialized. Base settings:\n"
            f"  Output: {self.settings.output_dir} "
            f"({self.settings.width}x{self.settings.height})\n"
            f"  Mask: {mask_name}, Font: {font_name}"
        )

    def _load_mask(self, mask_path: Path) -> Optional[np.ndarray]:
        """
        Loads image and prepares it as NumPy array mask for word cloud shape.

        Handles img conversion, resizing, compositing for transparency,
        and potential inversion for correct WordCloud processing.

        Note:
            Pillow's SVG support (via `Image.open()`) depends on external
            libraries like `librsvg` (Linux/macOS) or `CairoSVG` (Python).
            If these are not available, SVG mask loading might fail or produce
            unexpected results. PNG masks are generally more robust.

        Args:
            mask_path: The `Path` to the mask image file (pre-validated).

        Returns:
            A NumPy array of the processed image mask, or None on failure.
        """
        try:
            logger.debug(f"Loading mask from validated path: {mask_path}")
            mask_image = Image.open(mask_path).convert("RGBA")

            min_dim_px = 256
            if mask_image.width < min_dim_px or mask_image.height < min_dim_px:
                scale = max(
                    min_dim_px / mask_image.width,
                    min_dim_px / mask_image.height
                )
                new_dims = (
                    int(mask_image.width * scale),
                    int(mask_image.height * scale),
                )
                mask_image = mask_image.resize(
                    new_dims, Image.Resampling.LANCZOS
                )
                logger.info(
                    f"Resized mask '{mask_path.name}' to {new_dims} "
                    "for detail."
                )

            bg = Image.new("RGBA", mask_image.size, (255, 255, 255, 255))
            composite = Image.alpha_composite(bg, mask_image)
            mask_array = np.array(composite.convert("L"))

            if np.mean(mask_array) > (255 * 0.85):  # If predominantly light
                mask_array = 255 - mask_array  # Invert
                logger.info(
                    f"Mask '{mask_path.name}' inverted for "
                    "WordCloud processing."
                )

            logger.info(
                f"Mask '{mask_path.name}' loaded. Shape: {mask_array.shape}"
            )
            return mask_array

        except FileNotFoundError:  # Should be caught by Pydantic
            logger.error(f"Mask file not found at runtime: {mask_path}.")
            return None
        except Image.UnidentifiedImageError:
            logger.error(
                f"Cannot identify image file (Pillow error) for mask "
                f"'{mask_path.name}'. Ensure it's a valid image format that "
                f"Pillow can process. For SVGs, ensure librsvg or CairoSVG "
                f"is available to Pillow."
            )
            return None
        except Exception as e:
            logger.error(
                f"Error loading/processing mask '{mask_path.name}': {e}",
                exc_info=True
            )
            if ".svg" in mask_path.name.lower():
                logger.warning(
                    "SVG mask processing failed. Ensure a suitable backend "
                    "(librsvg/CairoSVG) is installed and accessible by "
                    "Pillow, or use a PNG mask instead."
                )
            return None

    def _get_active_color_logic(
        self, settings: WordCloudSettings
    ) -> Tuple[Optional[Callable[..., str]], Optional[str]]:
        """
        Determines the active color function and colormap based on settings.

        Priority:
        1. `custom_color_func_name` (with optional `color_palette_override`).
        2. `colormap` (if no custom function).
        3. WordCloud default if neither is specified.

        Returns:
            A tuple: (color_function, colormap_string).
            - `color_function`: The callable for coloring (or None).
                                This could be a functools.partial object.
            - `colormap_string`: The name of the colormap (or None).
        """
        active_color_func: Optional[Callable[..., str]] = None
        active_colormap: Optional[str] = None

        if settings.custom_color_func_name:
            func = CUSTOM_COLOR_FUNCTIONS.get(settings.custom_color_func_name)
            if func:
                # Prepare kwargs for the custom color function
                custom_func_kwargs: Dict[str, Any] = {}
                if (
                    settings.color_palette_override
                    and settings.custom_color_func_name == "primary_color_func"
                ):
                    custom_func_kwargs["color_palette"] = (
                        settings.color_palette_override
                    )
                # Add other potential kwargs needed by custom color funcs from settings
                # For example, if analogous_color_func needs base_hue from settings:
                # if settings.custom_color_func_name == "analogous_color_func":
                #     if settings.base_hue_for_analogous is not None: # Assuming a new setting
                #         custom_func_kwargs["base_hue"] = settings.base_hue_for_analogous

                if custom_func_kwargs:
                    active_color_func = functools.partial(func, **custom_func_kwargs)
                    logger.debug(
                        f"Using custom color func (partial): "
                        f"{settings.custom_color_func_name} "
                        f"with bound kwargs: {custom_func_kwargs}"
                    )
                else:
                    active_color_func = func
                    logger.debug(
                        f"Using custom color func (direct): "
                        f"{settings.custom_color_func_name}"
                    )
            else:
                logger.warning(
                    f"Custom color function "
                    f"'{settings.custom_color_func_name}' "
                    "not found. Falling back."
                )

        if not active_color_func and settings.colormap:
            active_colormap = settings.colormap
            logger.debug(f"Using colormap: {active_colormap}")
        elif not active_color_func and not settings.colormap:
            logger.debug(
                "No custom color function or colormap specified. "
                "WordCloud will use its default."
            )
            # WordCloud library uses 'viridis' if color_func and colormap are None.
            # No need to set active_colormap = None explicitly if that's the desired default.

        return active_color_func, active_colormap

    def generate(
        self,
        text_input: Optional[str] = None,
        frequencies: Optional[Dict[str, float]] = None,
        override_settings_dict: Optional[Dict[str, Any]] = None,
    ) -> Optional[Path]:
        """
        Generates and saves a word cloud image.

        Uses raw text, pre-calculated frequencies, or fallback prompt.
        Settings can be temporarily overridden.

        Args:
            text_input: Raw text for the cloud. Used if `frequencies` is None.
            frequencies: Dict of word frequencies (word: count/weight).
                         If provided, `text_input` is ignored.
            override_settings_dict: Dict to temporarily override base settings.

        Returns:
            Path to the generated image file if successful, otherwise None.
        """
        active_settings = self.settings
        if override_settings_dict:
            logger.debug(
                f"Applying override settings: {override_settings_dict}"
            )
            try:
                updated_data = self.settings.model_dump()
                updated_data.update(override_settings_dict)
                active_settings = WordCloudSettings(**updated_data)
                logger.info("Override settings applied for this generation.")
            except Exception as e:
                logger.error(
                    f"Invalid override settings: {e}. Using original.",
                    exc_info=True
                )

        final_text_data = (
            text_input or active_settings.text or active_settings.prompt
        )
        if not final_text_data and not frequencies:
            logger.error(
                "Cannot generate: No text (direct, settings, prompt) or "
                "frequencies provided."
            )
            return None

        mask_array: Optional[np.ndarray] = None
        mask_path_for_log: str = "None (Rectangular)" # Default if no valid mask

        current_mask_path = active_settings.mask_path
        if isinstance(current_mask_path, Path):
            if current_mask_path.is_file():
                mask_array = self._load_mask(current_mask_path)
                mask_path_for_log = current_mask_path.name
                if mask_array is None:
                    logger.warning(
                        f"Mask loading failed for '{mask_path_for_log}'. "
                        "Generating rectangular cloud."
                    )
                    mask_path_for_log = f"{current_mask_path.name} (Failed Load)"
            else:
                logger.warning(
                    f"Configured mask_path '{current_mask_path}' exists but is not a file. Generating rectangular cloud."
                )
                mask_path_for_log = f"{current_mask_path.name} (Not a File)"
        elif current_mask_path is not None: # Should be caught by Pydantic
            logger.warning(
                f"Configured mask_path '{current_mask_path}' is invalid type: {type(current_mask_path)}. Rectangular cloud."
            )
            mask_path_for_log = f"Invalid Path ({type(current_mask_path)})"


        font_path_str: Optional[str] = None
        font_path_for_log: str = "Default (WordCloud)"

        current_font_path = active_settings.font_path
        if isinstance(current_font_path, Path):
            if current_font_path.is_file():
                font_path_str = str(current_font_path)
                font_path_for_log = current_font_path.name
            else:
                logger.warning(
                    f"Configured font_path '{current_font_path}' exists but is not a file. Using WordCloud default font."
                )
                font_path_for_log = f"{current_font_path.name} (Not a File)"
        elif current_font_path is not None: # Should be caught by Pydantic
            logger.warning(
                f"Configured font_path '{current_font_path}' is invalid type: {type(current_font_path)}. Using WordCloud default font."
            )
            font_path_for_log = f"Invalid Path ({type(current_font_path)})"


        all_stopwords = STOPWORDS.copy()
        if active_settings.stopwords:
            all_stopwords.update(s.lower() for s in active_settings.stopwords)
        logger.debug(
            f"Using {len(all_stopwords)} stopwords (defaults + custom)."
        )

        # Get the actual color function and colormap string
        resolved_color_func, resolved_colormap_str = (
            self._get_active_color_logic(active_settings)
        )

        bg_color_val = str(active_settings.background_color)
        bg_color_lower = bg_color_val.lower()

        is_transparent = "rgba(" in bg_color_lower and \
                         bg_color_lower.strip().endswith(",0)")
        wc_mode = "RGBA" if is_transparent else "RGB"
        actual_background_color = active_settings.background_color
        if is_transparent:
            logger.debug(
                f"Using RGBA mode, transparent bg "
                f"('{actual_background_color}')."
            )
        else:
            logger.debug(
                f"Using {wc_mode} mode, background: "
                f"'{actual_background_color}'."
            )

        try:
            logger.info("Initializing WordCloud object...")
            wc_params = {
                "width": active_settings.width,
                "height": active_settings.height,
                "background_color": actual_background_color,
                "mask": mask_array,
                "font_path": font_path_str,
                "stopwords": all_stopwords,
                "max_words": active_settings.max_words,
                "contour_width": active_settings.contour_width,
                "contour_color": active_settings.contour_color,
                "min_font_size": active_settings.min_font_size,
                "max_font_size": active_settings.max_font_size,
                "prefer_horizontal": active_settings.prefer_horizontal,
                "scale": active_settings.scale,
                "relative_scaling": active_settings.relative_scaling,
                "color_func": resolved_color_func, # Use the resolved function
                "colormap": resolved_colormap_str, # Use the resolved colormap name
                "mode": wc_mode,
                # **extra_wc_kwargs, # Removed: No longer passing unknown kwargs
            }
            logger.debug(f"WordCloud parameters: {wc_params}")

            wc = WordCloud(**wc_params)

            if frequencies:
                logger.info(
                    f"Generating from {len(frequencies)} pre-computed "
                    f"frequencies."
                )
                wc.generate_from_frequencies(frequencies)
            elif final_text_data:
                text_snippet = final_text_data[:100].replace("\n", " ") + (
                    "..." if len(final_text_data) > 100 else ""
                )
                logger.info(f'Generating from text: "{text_snippet}"')
                wc.generate(str(final_text_data))
            else:
                logger.error(
                    "WordCloud generate() called without frequencies or text."
                )
                return None

            output_path = active_settings.get_full_output_path()
            logger.info(f"Attempting to save word cloud to: {output_path}")

            if active_settings.output_format == "svg":
                svg_output = wc.to_svg(
                    embed_font=True,
                    optimize_embedded_font=True
                )
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(svg_output)
                logger.info(
                    "SVG word cloud successfully generated and saved: "
                    f"{output_path}"
                )
            else:  # Default to PNG
                wc.to_file(str(output_path))
                logger.info(
                    "PNG word cloud successfully generated and saved: "
                    f"{output_path}"
                )
            return output_path

        except Exception as e:
            logger.error(
                f"Core WordCloud generation failed: {e}", exc_info=True
            )
            if font_path_str and "font" in str(e).lower():
                logger.error(
                    f"Font issue with '{font_path_for_log}'. Check validity."
                )
            if (
                mask_array is not None
                and "mask" in str(e).lower()
            ):
                logger.error(
                    f"Mask issue with '{mask_path_for_log}'. "
                    f"Check validity."
                )
            return None

    def generate_from_list(
        self,
        items: List[str],
        weights: Optional[Dict[str, float]] = None,
        override_settings_dict: Optional[Dict[str, Any]] = None,
    ) -> Optional[Path]:
        """
        Generates a word cloud from a list of items, with optional weights.

        Args:
            items: List of strings (words/phrases).
            weights: Optional dict mapping items to frequencies/weights.
                     If None, frequencies are derived from item counts.
            override_settings_dict: Dict to temporarily override settings.

        Returns:
            Path to the generated image if successful, else None.
        """
        current_overrides = (
            override_settings_dict.copy() if override_settings_dict else {}
        )
        if not items:
            logger.warning(
                "Empty list for 'generate_from_list'. Using fallback prompt."
            )
            current_overrides.setdefault(
                "prompt", "No items provided for word cloud generation."
            )
            return self.generate(
                text_input=None,
                frequencies=None,
                override_settings_dict=current_overrides,
            )

        freq: Dict[str, float]
        if weights:
            freq = {
                item: weights.get(item, 1.0)
                for item in set(items)
            }  # Ensure all unique items from list are covered
            logger.info(
                f"Using provided weights for {len(freq)} unique items."
            )
        else:
            item_counts = Counter(items)
            freq = {item: float(count) for item, count in item_counts.items()}
            logger.info(
                f"Calculated frequencies for {len(freq)} unique items."
            )

        sample_freq = dict(list(freq.items())[:5])
        logger.debug(
            f"Frequencies for list-based generation (sample): {sample_freq}"
        )

        return self.generate(
            frequencies=freq, override_settings_dict=current_overrides
        )


# ------------------------------------------------------------------------------
# Example Usage and Helper Functions for Demonstration
# ------------------------------------------------------------------------------


def generate_example_tech_word_cloud(
    output_dir_override: Optional[Path] = None,
    output_filename_override: str = "example_tech_word_cloud.png",
) -> Optional[Path]:
    """
    Generates an example technology-themed word cloud.

    This demonstration uses a predefined list of tech terms.
    """
    logger.info(
        "Attempting to generate an example technology-themed word cloud..."
    )

    tech_items: List[str] = [
        "Python", "JavaScript", "TypeScript", "Java", "Go", "Rust", "Scala",
        "React", "Angular", "Vue.js", "Svelte", "Node.js", "Express.js",
        "FastAPI", "Django", "Flask", "Spring Boot", "Docker", "Kubernetes",
        "Terraform", "Ansible", "AWS", "Azure", "GCP", "PostgreSQL", "MySQL",
        "MongoDB", "Redis", "Cassandra", "Kafka", "RabbitMQ", "Spark",
        "Hadoop", "Airflow", "Machine Learning", "Deep Learning", "NLP",
        "Computer Vision", "PyTorch", "TensorFlow", "scikit-learn", "CI/CD",
        "Git", "Jenkins", "GitLab CI", "GitHub Actions", "Agile", "Scrum",
        "DevOps", "Microservices", "Serverless", "GraphQL", "REST",
    ]
    # Simple weighting: more common/foundational terms get higher weights
    tech_weights: Dict[str, float] = {
        item: random.uniform(1.0, 3.0)
        + (
            5.0
            if item in ["Python", "JavaScript", "Docker", "Kubernetes", "AWS"]
            else 0
        )
        for item in tech_items
    }
    # Add some repetitions for frequency effect
    tech_items.extend(
        ["Python"] * 5 + ["JavaScript"] * 3 + ["Docker"] * 2
    )

    tech_cloud_overrides: Dict[str, Any] = {
        "output_dir": output_dir_override or DEFAULT_OUTPUT_DIR,
        "output_filename": output_filename_override,
        "colormap": "plasma",
        "contour_width": 1.0,
        "contour_color": "#FFFFFF",
        "min_font_size": 10,
        "scale": 1.1,
        "prefer_horizontal": 0.9,
        "custom_color_func_name": "analogous_color_func",
        "background_color": "rgba(20, 20, 30, 0.9)",
        "font_path": (
            DEFAULT_FONT_PATH
            if DEFAULT_FONT_PATH and DEFAULT_FONT_PATH.exists()
            else None
        ),
        "mask_path": (
            DEFAULT_MASK_PATH
            if DEFAULT_MASK_PATH and DEFAULT_MASK_PATH.exists()
            else None
        ),
        "stopwords": [
            "Programming", "Language", "Framework", "Library", "Tool",
            "Database", "Service", "System", "Platform", "Development",
            "Management", "API", "Data", "Learning",
        ],
        "max_words": 150,
        "width": 1600,
        "height": 1000,
    }

    generator = WordCloudGenerator()

    logger.info(
        f"Generating tech word cloud with {len(set(tech_items))} unique "
        "technologies using predefined list."
    )
    return generator.generate_from_list(
        items=tech_items,
        weights=tech_weights,
        override_settings_dict=tech_cloud_overrides,
    )


# This block executes when the script is run directly for demonstration
# AND for generating official profile assets.
if __name__ == "__main__":
    logger.info("Executing WordCloudGenerator script...")
    main_generator = WordCloudGenerator()  # Reusable generator instance

    # --- Generate Official Profile Word Clouds ---
    logger.info("--- Generating Official Profile Word Clouds ---")

    # 1. Topics Word Cloud
    logger.info("Attempting to generate Topics word cloud for profile...")
    if TOPICS_MD_PATH.exists():
        topic_frequencies = parse_markdown_for_word_cloud_frequencies(
            TOPICS_MD_PATH
        )
        if topic_frequencies:
            topic_overrides = {
                "output_dir": PROFILE_IMG_OUTPUT_DIR,
                "output_filename": "wordcloud_by_topic.svg",
                "output_format": "svg",
                "background_color": "rgba(255, 255, 255, 0)",
                "colormap": "viridis",
                "custom_color_func_name": "analogous_color_func",
                "font_path": (
                    DEFAULT_FONT_PATH
                    if DEFAULT_FONT_PATH and DEFAULT_FONT_PATH.exists()
                    else None
                ),
                "width": 1200,
                "height": 800,
                "max_words": 100,
                "contour_width": 0.5,
                "contour_color": "#DDDDDD",
                "stopwords": [
                    "project", "projects", "list", "awesome", "using",
                    "application", "platform",
                ],
            }
            path_topic_wc = main_generator.generate(
                frequencies=topic_frequencies,
                override_settings_dict=topic_overrides
            )
            if path_topic_wc:
                logger.info(
                    "Profile Topics Word Cloud generated: "
                    f"{path_topic_wc.name}"
                )
            else:
                logger.error(
                    "Failed to generate Profile Topics Word Cloud."
                )
        else:
            logger.warning(
                f"No frequencies parsed from {TOPICS_MD_PATH.name}, "
                "skipping topics word cloud."
            )
    else:
        logger.error(
            f"Topics Markdown file not found: {TOPICS_MD_PATH}. "
            "Cannot generate topics word cloud."
        )

    # 2. Languages Word Cloud
    logger.info("Attempting to generate Languages word cloud for profile...")
    if LANGUAGES_MD_PATH.exists():
        language_frequencies = parse_markdown_for_word_cloud_frequencies(
            LANGUAGES_MD_PATH
        )
        if language_frequencies:
            language_overrides = {
                "output_dir": PROFILE_IMG_OUTPUT_DIR,
                "output_filename": "wordcloud_by_language.svg",
                "output_format": "svg",
                "background_color": "rgba(255, 255, 255, 0)",
                "custom_color_func_name": "primary_color_func",
                "color_palette_override": [
                    "#4B8BBE", "#306998", "#FFE873", "#FFD43B",
                    "#646464", "#F1502F", "#00A0B0",
                ],
                "font_path": (
                    DEFAULT_FONT_PATH
                    if DEFAULT_FONT_PATH and DEFAULT_FONT_PATH.exists()
                    else None
                ),
                "width": 1200,
                "height": 800,
                "max_words": 75,
                "contour_width": 0.5,
                "contour_color": "#AAAAAA",
                "stopwords": [
                    "language", "languages", "code", "script",
                    "file", "files",
                ],
            }
            path_lang_wc = main_generator.generate(
                frequencies=language_frequencies,
                override_settings_dict=language_overrides,
            )
            if path_lang_wc:
                logger.info(
                    "Profile Languages Word Cloud generated: "
                    f"{path_lang_wc.name}"
                )
            else:
                logger.error(
                    "Failed to generate Profile Languages Word Cloud."
                )
        else:
            logger.warning(
                f"No frequencies parsed from {LANGUAGES_MD_PATH.name}, "
                "skipping languages word cloud."
            )
    else:
        logger.error(
            f"Languages Markdown file not found: {LANGUAGES_MD_PATH}. "
            "Cannot generate languages word cloud."
        )

    # --- Generate Example Word Clouds for Demonstration ---
    logger.info("\n--- Generating Example Word Clouds for Demonstration ---")
    example_output_dir = PROJECT_ROOT / "logs" / "wordcloud_examples"
    example_output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(
        f"Example word cloud outputs will be saved to: {example_output_dir}"
    )

    # Example 1: Simple text-based, rectangular, using colormap (PNG)
    logger.info("Running Example 1: Simple text cloud with colormap (PNG).")
    simple_text = (
        "Python Pydantic FastAPI Loguru Rich Typer JavaScript TypeScript "
        "React Node.js Next.js AWS Docker Kubernetes SQL CI/CD Agile Scrum "
        "DevOps MachineLearning AI DataScience NumPy Pandas Matplotlib "
        "SoftwareDesign ProblemSolving Collaboration Communication Teamwork "
        "Innovation Cloud"
    )
    ex1_overrides = {
        "text": simple_text,
        "output_dir": example_output_dir,
        "output_filename": "example_1_simple_text_colormap.png",
        "output_format": "png",
        "background_color": "rgba(10, 20, 30, 0.95)",
        "colormap": "Pastel1",
        "mask_path": None,
        "font_path": (
            DEFAULT_FONT_PATH
            if DEFAULT_FONT_PATH and DEFAULT_FONT_PATH.exists()
            else None
        ),
        "contour_width": 0,
        "custom_color_func_name": None,
        "max_words": 75,
        "width": 1000,
        "height": 600,
    }
    path_ex1 = main_generator.generate(override_settings_dict=ex1_overrides)
    if path_ex1:
        logger.info(f"Example 1 (PNG) generated: {path_ex1.name}")
    else:
        logger.error("Example 1 (PNG) failed.")

    # Example 1.1: Simple text-based, rectangular, using colormap (SVG)
    logger.info("Running Example 1.1: Simple text cloud with colormap (SVG).")
    ex1_svg_overrides = ex1_overrides.copy()
    ex1_svg_overrides["output_filename"] = "example_word_cloud_1_text.svg"
    ex1_svg_overrides["output_format"] = "svg"

    path_ex1_svg = main_generator.generate(
        override_settings_dict=ex1_svg_overrides  # Shortened
    )
    if path_ex1_svg:
        logger.info(f"Example 1.1 (SVG) generated: {path_ex1_svg.name}")
    else:
        logger.error("Example 1.1 (SVG) failed.")

    # Example 2: Tech word cloud (helper func, predefined data) - SVG
    logger.info(
        "Running Example 2: Tech-themed cloud (predefined data) - SVG."
    )
    # Modify generate_example_tech_word_cloud to accept output_format
    # For now, we'll create a specific SVG version here.
    tech_items: List[str] = [
        "Python", "JavaScript", "TypeScript", "Java", "Go", "Rust", "Scala",
        "React", "Angular", "Vue.js", "Svelte", "Node.js", "Express.js",
        "FastAPI", "Django", "Flask", "Spring Boot", "Docker", "Kubernetes",
        "Terraform", "Ansible", "AWS", "Azure", "GCP", "PostgreSQL", "MySQL",
        "MongoDB", "Redis", "Cassandra", "Kafka", "RabbitMQ", "Spark",
        "Hadoop", "Airflow", "Machine Learning", "Deep Learning", "NLP",
        "Computer Vision", "PyTorch", "TensorFlow", "scikit-learn", "CI/CD",
        "Git", "Jenkins", "GitLab CI", "GitHub Actions", "Agile", "Scrum",
        "DevOps", "Microservices", "Serverless", "GraphQL", "REST",
    ]
    tech_weights: Dict[str, float] = {
        item: random.uniform(1.0, 3.0)
        + (
            5.0
            if item in ["Python", "JavaScript", "Docker", "Kubernetes", "AWS"]
            else 0
        )
        for item in tech_items
    }
    tech_items.extend(
        ["Python"] * 5 + ["JavaScript"] * 3 + ["Docker"] * 2
    )

    tech_cloud_svg_overrides: Dict[str, Any] = {
        "output_dir": example_output_dir,
        "output_filename": "example_2_tech_cloud_analogous.svg",
        "output_format": "svg",
        "colormap": "plasma",
        "contour_width": 1.0,
        "contour_color": "#FFFFFF",
        "min_font_size": 10,
        "scale": 1.1,
        "prefer_horizontal": 0.9,
        "custom_color_func_name": "analogous_color_func",
        "background_color": "rgba(20, 20, 30, 0.9)",
        "font_path": (
            DEFAULT_FONT_PATH
            if DEFAULT_FONT_PATH and DEFAULT_FONT_PATH.exists()
            else None
        ),
        "mask_path": (
            DEFAULT_MASK_PATH
            if DEFAULT_MASK_PATH and DEFAULT_MASK_PATH.exists()
            else None
        ),
        "stopwords": [
            "Programming", "Language", "Framework", "Library", "Tool",
            "Database", "Service", "System", "Platform", "Development",
            "Management", "API", "Data", "Learning",
        ],
        "max_words": 150,
        "width": 1600,
        "height": 1000,
    }
    path_ex2_svg = main_generator.generate_from_list(
        items=tech_items,
        weights=tech_weights,
        override_settings_dict=tech_cloud_svg_overrides,
    )
    if path_ex2_svg:
        logger.info(f"Example 2 (SVG) generated: {path_ex2_svg.name}")
    else:
        logger.warning("Example 2 (SVG) failed (check logs).")

    # Example 3: Creative cloud (primary_color_func & palette override, SVG)
    logger.info(
        "Running Example 3: Creative cloud (SVG)."
    )
    creative_text = (
        "DesignThinking UserExperience UI UX Figma Sketch AdobeXD Prototyping "
        "Wireframing UserResearch Accessibility GraphicDesign Typography "
        "ColorTheory Branding Innovation VisualDesign InteractionDesign "
        "Empathy Creativity Storytelling JourneyMapping PersonaDevelopment"
    )
    custom_palette = ["#FF6B6B", "#FFD166", "#06D6A0", "#118AB2", "#073B4C"]
    ex3_overrides = {
        "text": creative_text,
        "output_dir": example_output_dir,
        "output_filename": "example_3_creative_primary_palette.svg",
        "output_format": "svg",
        "mask_path": (
            DEFAULT_MASK_PATH
            if DEFAULT_MASK_PATH and DEFAULT_MASK_PATH.exists()
            else None
        ),
        "font_path": (
            DEFAULT_FONT_PATH
            if DEFAULT_FONT_PATH and DEFAULT_FONT_PATH.exists()
            else None
        ),
        "custom_color_func_name": "primary_color_func",
        "color_palette_override": custom_palette,
        "contour_width": 1.0,
        "contour_color": "#E0E0E0",
        "background_color": "rgba(250, 250, 255, 0)",
        "min_font_size": 15,
        "scale": 1.1,
        "relative_scaling": 0.4,
        "stopwords": ["Design", "User"],
        "max_words": 100,
    }
    if ex3_overrides["mask_path"] is None:
        logger.warning(
            "Example 3 (SVG): Default mask not found, will be rectangular."
        )
    if ex3_overrides["font_path"] is None:
        logger.warning(
            "Example 3 (SVG): Default font not found, using WordCloud default."
        )

    path_ex3 = main_generator.generate(override_settings_dict=ex3_overrides)
    if path_ex3:
        logger.info(f"Example 3 (SVG) generated: {path_ex3.name}")
    else:
        logger.error("Example 3 (SVG) failed.")

    # Example 4: List with weights, using complementary_color_func (SVG)
    logger.info(
        "Running Example 4: List with weights, complementary colors (SVG)."
    )
    list_items = [
        "Python", "JS", "Java", "C++", "Go", "Rust", "Swift", "Kotlin",
        "PHP", "Ruby",
    ]
    list_weights = {lang: 10 - i * 0.75 for i, lang in enumerate(list_items)}
    ex4_overrides = {
        "output_dir": example_output_dir,
        "output_filename": "example_4_list_complementary.svg",
        "output_format": "svg",
        "custom_color_func_name": "complementary_color_func",
        "background_color": "rgba(30,30,30,1)",
        "mask_path": None,
        "width": 900,
        "height": 600,
        "font_path": (
            DEFAULT_FONT_PATH
            if DEFAULT_FONT_PATH and DEFAULT_FONT_PATH.exists()
            else None
        ),
        "contour_width": 0.5,
        "contour_color": "#CCC",
    }
    path_ex4 = main_generator.generate_from_list(
        items=list_items, weights=list_weights,
        override_settings_dict=ex4_overrides
    )
    if path_ex4:
        logger.info(f"Example 4 (SVG) generated: {path_ex4.name}")
    else:
        logger.error("Example 4 (SVG) failed.")

    # Example 5: Triadic colors with different base hue (SVG)
    logger.info("Running Example 5: Triadic colors, different base hue (SVG).")
    ex5_text = (
        "Synergy Blockchain Web3 Metaverse Decentralization DAO NFT "
        "SmartContracts Ethereum Solana Polygon Polkadot FinTech RegTech"
    )
    ex5_overrides = {
        "text": ex5_text,
        "output_dir": example_output_dir,
        "output_filename": "example_5_triadic_blockchain.svg",
        "output_format": "svg",
        "custom_color_func_name": "triadic_color_func",
        "background_color": "white",
        "mask_path": (
            DEFAULT_MASK_PATH
            if DEFAULT_MASK_PATH and DEFAULT_MASK_PATH.exists()
            else None
        ),
        "font_path": (
            DEFAULT_FONT_PATH
            if DEFAULT_FONT_PATH and DEFAULT_FONT_PATH.exists()
            else None
        ),
        "width": 1200,
        "height": 700,
        "max_words": 50,
        "scale": 1.3,
    }
    if ex5_overrides["mask_path"] is None:
        logger.warning(
            "Example 5 (SVG): Default mask not found, will be rectangular."
        )

    path_ex5 = main_generator.generate(override_settings_dict=ex5_overrides)
    if path_ex5:
        logger.info(f"Example 5 (SVG) generated: {path_ex5.name}")
    else:
        logger.error("Example 5 (SVG) failed.")

    logger.info(
        f"WordCloudGenerator script demonstration finished. Outputs in "
        f"'{example_output_dir}'."
    )
    logger.info(
        f"Official profile word clouds (if generated) are in "
        f"'{PROFILE_IMG_OUTPUT_DIR}'."
    )
