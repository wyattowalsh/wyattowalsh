from pathlib import Path
from typing import Literal

import yaml  # type: ignore
from pydantic import BaseModel, Field, HttpUrl, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .word_clouds.readability import LayoutReadabilitySettings
from .utils import get_logger

# Lines broken for length where necessary.

logger = get_logger(module=__name__)


class Settings(BaseSettings):
    """Global application settings, loaded from environment variables."""

    app_name: str = "ReadmeCLI"
    log_level: str = Field("INFO", validation_alias="LOG_LEVEL")
    debug_mode: bool = Field(False, validation_alias="DEBUG_MODE")

    log_text_dir: Path = Field(default_factory=lambda: Path("logs/text"))
    log_json_dir: Path = Field(default_factory=lambda: Path("logs/json"))
    log_rotation: str = "10 MB"
    log_retention: str = "10 days"
    log_compression: str = "zip"

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class BannerSettings(BaseModel):
    title: str = "Your Name"
    subtitle: str = "Software Engineer & AI Enthusiast"
    output_path: str = ".github/assets/img/banner.svg"
    width: int = 1200
    height: int = 630
    optimize_with_svgo: bool = True


class TypedUrl(BaseModel):
    url: HttpUrl
    label: str = "Website"  # Default label if not provided


class VCardDataModel(BaseModel):
    displayname: str = "Your Name"
    n_givenname: str = "Your"
    n_familyname: str = "Name"
    fn: str = "Wyatt Walsh"
    org: str = "Personal Portfolio Project"
    title: str = "Developer & Tech Enthusiast"
    tel_work_voice: str = ""
    email_internet: str = ""
    url_work: list[TypedUrl] | None = Field(
        default=[],
        description="Work-related URLs with labels."
    )


class QRCodeSettings(BaseModel):
    output_filename: str = "qr.png"
    output_dir: str = ".github/assets/img"
    default_background_path: str | None = None
    default_scale: int = 25
    error_correction: str = "H"  # L, M, Q, H


class WordCloudSettingsModel(BaseModel):
    output_dir: str = ".github/assets/img"
    output_filename: str = "word_cloud.png"
    max_words: int = Field(
        default=1000,
        ge=1,
        description="Maximum number of terms to render in generated word clouds.",
    )
    prompt: str | None = Field(
        default="My Tech Skills: Python, JavaScript, Cloud, AI, DevOps, SQL, React",
        description="Default prompt for word cloud generation."
    )
    stopwords: list[str] | None = Field(
        default_factory=list,  # type: ignore
        description="List of stopwords for word clouds."
    )
    layout_readability: LayoutReadabilitySettings = Field(
        default_factory=LayoutReadabilitySettings,
        description="Shared readability/orientation tuning for word-cloud layouts.",
    )


class SkillEntry(BaseModel):
    """A single technology/skill badge."""

    name: str = Field(..., description="Display name for the badge")
    slug: str | None = Field(
        None, description="Simple Icons slug for logo"
    )
    logo_path: str | None = Field(
        None,
        description="Path to local SVG for custom logo (base64-encoded into badge URL)",
    )
    color: str = Field(
        "555555", description="Hex color without # prefix"
    )
    logo_color: str | None = Field(
        None,
        description=(
            "Override logoColor per skill. Only applies when using "
            "slug (Simple Icons); ignored when logo_path is set."
        ),
    )
    url: str | None = Field(
        None, description="Click-through link URL"
    )

    @field_validator("logo_path")
    @classmethod
    def validate_logo_path(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not v:
            raise ValueError("logo_path must not be empty")
        if ".." in Path(v).parts:
            raise ValueError(
                f"logo_path must not contain '..': {v}"
            )
        return v

    @field_validator("url")
    @classmethod
    def validate_url_scheme(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not v.lower().startswith(("http://", "https://")):
            raise ValueError(
                f"url must use http:// or https:// scheme: {v}"
            )
        return v


class SkillSubcategory(BaseModel):
    """A subcategory containing skills."""

    name: str = Field(..., description="Subcategory display name")
    skills: list[SkillEntry] = Field(default_factory=list)


class SkillCategory(BaseModel):
    """A top-level category with skills and optional subcategories."""

    name: str = Field(..., description="Category display name")
    skills: list[SkillEntry] = Field(default_factory=list)
    subcategories: list[SkillSubcategory] = Field(default_factory=list)


class SkillsSettings(BaseModel):
    """Configuration for skills/tech stack badge generation."""

    style: str = Field(
        "for-the-badge", description="shields.io badge style"
    )
    logo_color: str = Field(
        "white", description="Default logoColor for all badges"
    )
    readme_path: str = Field(
        "README.md", description="Path to README for injection"
    )
    section_title: str = Field(
        "Tech Stack",
        description=(
            "Section heading used only when collapsible=True "
            "(rendered as <summary> text). For collapsible=False "
            "(the default), add the heading manually in README.md "
            "outside the <!-- SKILLS:START/END --> markers."
        ),
    )
    collapsible: bool = Field(
        False, description="Wrap in <details> tag"
    )
    categories: list[SkillCategory] = Field(default_factory=list)


class ReadmeSocialLink(BaseModel):
    """Config for a social badge link in README."""

    label: str = Field(..., description="Badge label text")
    url: str = Field(..., description="Destination URL")
    color: str = Field("555555", description="Badge color hex (without #)")
    logo: str | None = Field(
        None, description="Simple Icons slug for shields.io logo"
    )
    logo_color: str = Field("white", description="Badge logo color")

    @field_validator("url")
    @classmethod
    def validate_url_scheme(cls, v: str) -> str:
        if not v.lower().startswith(("http://", "https://", "mailto:")):
            raise ValueError(
                f"url must use http://, https://, or mailto: scheme: {v}"
            )
        return v


class ReadmeFeaturedRepo(BaseModel):
    """Repository to feature in README card section."""

    full_name: str = Field(
        ..., description="GitHub repository full name (owner/repo)"
    )


class ReadmeSvgCardStyleSettings(BaseModel):
    """Visual style controls for per-card README SVG rendering."""

    variant: Literal["gh-card", "legacy"] = Field(
        "gh-card",
        description=(
            "Per-card rendering variant. Use 'gh-card' for the dedicated "
            "family renderer or 'legacy' for the shared block renderer."
        ),
    )
    transparent_canvas: bool = Field(
        True,
        description=(
            "When variant='legacy', render each per-card SVG without an outer "
            "background canvas."
        ),
    )
    show_title: bool = Field(
        False,
        description=(
            "When variant='legacy', render section title text above each "
            "per-card SVG."
        ),
    )


class ReadmeSvgFamilyCardStyles(BaseModel):
    """Family-specific style controls for README per-card SVG assets."""

    default: ReadmeSvgCardStyleSettings = Field(
        default_factory=ReadmeSvgCardStyleSettings
    )
    connect: ReadmeSvgCardStyleSettings = Field(
        default_factory=ReadmeSvgCardStyleSettings
    )
    featured: ReadmeSvgCardStyleSettings = Field(
        default_factory=ReadmeSvgCardStyleSettings
    )
    blog: ReadmeSvgCardStyleSettings = Field(
        default_factory=ReadmeSvgCardStyleSettings
    )


class ReadmeSvgSettings(BaseModel):
    """Settings for optional SVG assets used by README dynamic sections."""

    enabled: bool = Field(
        False, description="Enable generation of SVG section assets."
    )
    output_dir: str = Field(
        ".github/assets/img/readme",
        description="Directory where README SVG assets are written.",
    )
    top_contact: bool = Field(
        True, description="Generate SVG asset for the top contact block."
    )
    featured_projects: bool = Field(
        True, description="Generate SVG asset for featured project cards."
    )
    blog_posts: bool = Field(
        True, description="Generate SVG asset for blog post cards."
    )
    card_styles: ReadmeSvgFamilyCardStyles = Field(
        default_factory=ReadmeSvgFamilyCardStyles,
        description=(
            "Family-specific per-card style switches used by README SVG "
            "rendering."
        ),
    )


class ReadmeSectionsSettings(BaseModel):
    """Configuration for dynamic README sections."""

    readme_path: str = Field(
        "README.md", description="Path to README for section injection"
    )
    badge_style: str = Field(
        "for-the-badge", description="shields.io style for social badges"
    )
    social_links: list[ReadmeSocialLink] = Field(
        default_factory=list
    )
    featured_repos: list[ReadmeFeaturedRepo] = Field(
        default_factory=list
    )
    blog_feed_url: str = Field(
        "", description="RSS/Atom feed URL for blog posts"
    )
    blog_post_limit: int = Field(
        5, ge=1, le=10, description="Number of latest blog posts to render"
    )
    svg: ReadmeSvgSettings = Field(default_factory=ReadmeSvgSettings)


class ProjectConfig(BaseSettings):
    """Project-specific configuration, loaded from a YAML file."""

    project_name: str = "My Awesome Project"
    author_email: str | None = None
    version: str = "0.1.0"

    banner_settings: BannerSettings | None = Field(
        default_factory=BannerSettings
    )
    v_card_data: VCardDataModel | None = Field(
        default_factory=VCardDataModel
    )
    qr_code_settings: QRCodeSettings | None = Field(
        default_factory=QRCodeSettings
    )
    word_cloud_settings: WordCloudSettingsModel | None = Field(
        default_factory=WordCloudSettingsModel
    )
    readme_sections_settings: ReadmeSectionsSettings | None = Field(
        default_factory=ReadmeSectionsSettings
    )

    # ProjectConfig is intended to be loaded from a file,
    # not env vars directly.
    model_config = SettingsConfigDict(extra="ignore")


# Changed default config path to ./config.yaml
DEFAULT_CONFIG_PATH = Path("./config.yaml")


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> ProjectConfig:
    """Loads project config from YAML. Creates default if missing/empty
    at default path."""
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if data is None:  # File is empty or only comments/whitespace
                if path == DEFAULT_CONFIG_PATH:
                    # Empty default config file, so create and save defaults
                    logger.info(
                        "Default config file {path!r} is empty. "
                        "Populating with defaults.",
                        path=path,
                    )
                    default_cfg = ProjectConfig()
                    save_config(default_cfg, path)
                    return default_cfg
                else:
                    # Non-default config file is empty, which is an issue
                    raise ValueError(f"YAML file is empty: {path}")
            return ProjectConfig(**data)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {path}: {e}") from e
        except ValidationError as e:
            raise ValueError(f"Invalid config data in {path}:\\n{e}") from e
        except Exception as e:
            raise OSError(f"Error loading config from {path}: {e}") from e
    else:
        # File does not exist
        if path == DEFAULT_CONFIG_PATH:
            # Default config file does not exist, so create and save defaults
            try:
                logger.info(
                    "Default config file {path!r} not found. "
                    "Creating with defaults.",
                    path=path,
                )
                default_cfg = ProjectConfig()
                save_config(default_cfg, path)
                return default_cfg
            except Exception as e_create:
                raise FileNotFoundError(
                    f"Config file not found: {path}. Attempt to create "
                    f"default failed: {e_create}"
                ) from e_create
        # Non-default config file does not exist
        raise FileNotFoundError(f"Config file not found: {path}")


DEFAULT_SKILLS_PATH = Path("./skills.yaml")


def load_skills(path: Path = DEFAULT_SKILLS_PATH) -> SkillsSettings:
    """Loads skills config from a YAML file."""
    if not path.exists():
        raise FileNotFoundError(f"Skills file not found: {path}")
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data is None:
            raise ValueError(f"Skills YAML file is empty: {path}")
        return SkillsSettings(**data)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {path}: {e}") from e
    except ValidationError as e:
        raise ValueError(f"Invalid skills data in {path}:\n{e}") from e


def save_config(
    config: ProjectConfig, path: Path = DEFAULT_CONFIG_PATH
) -> None:
    """Saves project config to YAML. Raises errors on failure."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(
                config.model_dump(mode="json"),
                f,
                sort_keys=False,
                indent=2,
                default_flow_style=False,  # Encourage block style
            )
    except Exception as e:
        raise OSError(f"Failed to save config to {path}: {e}") from e


# NOTE: dev/test scaffolding — consider moving to a standalone script
if __name__ == "__main__":
    logger.info("--- Testing ProjectConfig ({path}) ---", path=DEFAULT_CONFIG_PATH)
    initial_cfg: ProjectConfig | None = None
    try:
        logger.info("Attempting to load existing config...")
        initial_cfg = load_config()
        logger.info("Loaded config (existing or newly created default).")
    except (OSError, FileNotFoundError, ValueError) as e_load:
        logger.error(
            "Error loading config: {e}. "
            "This shouldn't happen if default creation works.",
            e=e_load,
        )
        initial_cfg = ProjectConfig()
        logger.info("Using in-memory default config due to load failure.")

    if initial_cfg:
        logger.info("Current config (loaded or default):")
        # For display, we can dump it as YAML string to test that part too
        try:
            yaml_str_display = yaml.dump(
                initial_cfg.model_dump(mode="python"),
                indent=2,
                sort_keys=False,
            )
            logger.debug("Config YAML:\n{yaml_str}", yaml_str=yaml_str_display)
        except Exception as e_display:
            logger.warning(
                "Could not serialize current config to YAML for display: {e}",
                e=e_display,
            )
            logger.debug("Config JSON: {json}", json=initial_cfg.model_dump_json(indent=2))

        initial_cfg.project_name = "Updated Project Name via Test Script"
        if initial_cfg.banner_settings:
            initial_cfg.banner_settings.title = (
                "Updated Banner Title via Test Script"
            )

        logger.info("Attempting to save modified config...")
        try:
            save_config(initial_cfg)
            logger.info("Saved updated config to {path}.", path=DEFAULT_CONFIG_PATH)
        except OSError as e_save_mod:
            logger.error("Error saving modified config: {e}", e=e_save_mod)

        logger.info("Attempting to reload config for verification...")
        try:
            reloaded_cfg = load_config()
            logger.info("Reloaded config:")
            yaml_str_reloaded = yaml.dump(
                reloaded_cfg.model_dump(mode="python"),
                indent=2,
                sort_keys=False,
            )
            logger.debug("Reloaded YAML:\n{yaml_str}", yaml_str=yaml_str_reloaded)

            if reloaded_cfg.project_name != "Updated Project Name via Test Script":
                logger.error(
                    "Mismatch: project_name is {actual!r}, expected "
                    "'Updated Project Name via Test Script'",
                    actual=reloaded_cfg.project_name,
                )
            elif (
                reloaded_cfg.banner_settings
                and reloaded_cfg.banner_settings.title
                != "Updated Banner Title via Test Script"
            ):
                logger.error(
                    "Mismatch: banner title is {actual!r}, expected "
                    "'Updated Banner Title via Test Script'",
                    actual=reloaded_cfg.banner_settings.title,
                )
            else:
                logger.info("Verification successful: Reloaded matches saved.")
        except (OSError, FileNotFoundError, ValueError) as e_reload:
            logger.error("Error reloading/verifying: {e}", e=e_reload)
    else:
        logger.error("Critical error: initial_cfg is None after load attempts.")
