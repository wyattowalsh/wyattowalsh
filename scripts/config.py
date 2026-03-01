from pathlib import Path
from typing import List, Optional, Union

import yaml  # type: ignore
from pydantic import BaseModel, Field, HttpUrl, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Logging within this module is removed. Functions will raise exceptions.
# Lines broken for length where necessary.


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
    title: str = "Wyatt Walsh"
    subtitle: str = "Software Engineer & AI Enthusiast"
    output_path: str = ".github/assets/img/banner.svg"
    width: int = 1200
    height: int = 630
    optimize_with_svgo: bool = True


class TypedUrl(BaseModel):
    url: HttpUrl
    label: str = "Website"  # Default label if not provided


class VCardDataModel(BaseModel):
    displayname: str = "Wyatt Walsh"
    n_givenname: str = "Wyatt"
    n_familyname: str = "Walsh"
    fn: str = "Wyatt Walsh"
    org: str = "Personal Portfolio Project"
    title: str = "Developer & Tech Enthusiast"
    tel_work_voice: str = "2096022545"
    email_internet: str = "wyattowalsh@gmail.com"
    url_work: Optional[List[TypedUrl]] = Field(
        default=[
            TypedUrl(url=HttpUrl("https://www.w4w.dev/"), label="Website"),
            TypedUrl(
                url=HttpUrl("https://www.linkedin.com/in/wyattowalsh"),
                label="LinkedIn"
            ),
            TypedUrl(
                url=HttpUrl("https://www.github.com/wyattowalsh"),
                label="GitHub"
            ),
        ],
        description="Work-related URLs with labels."
    )


class QRCodeSettings(BaseModel):
    output_filename: str = "qr.png"
    output_dir: str = ".github/assets/img"
    default_background_path: Optional[str] = ".github/assets/img/icon.svg"
    default_scale: int = 25
    error_correction: str = "H"  # L, M, Q, H


class WordCloudSettingsModel(BaseModel):
    output_dir: str = ".github/assets/img"
    output_filename: str = "word_cloud.png"
    prompt: Optional[str] = Field(
        default="My Tech Skills: Python, JavaScript, Cloud, AI, DevOps, SQL, React",
        description="Default prompt for word cloud generation."
    )
    stopwords: Optional[List[str]] = Field(
        default_factory=list,  # type: ignore
        description="List of stopwords for word clouds."
    )


class SkillEntry(BaseModel):
    """A single technology/skill badge."""

    name: str = Field(..., description="Display name for the badge")
    slug: Optional[str] = Field(
        None, description="Simple Icons slug for logo"
    )
    logo_path: Optional[str] = Field(
        None,
        description="Path to local SVG for custom logo (base64-encoded into badge URL)",
    )
    color: str = Field(
        "555555", description="Hex color without # prefix"
    )
    logo_color: Optional[str] = Field(
        None,
        description=(
            "Override logoColor per skill. Only applies when using "
            "slug (Simple Icons); ignored when logo_path is set."
        ),
    )
    url: Optional[str] = Field(
        None, description="Click-through link URL"
    )

    @field_validator("logo_path")
    @classmethod
    def validate_logo_path(cls, v: Optional[str]) -> Optional[str]:
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
    def validate_url_scheme(cls, v: Optional[str]) -> Optional[str]:
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
    skills: List[SkillEntry] = Field(default_factory=list)


class SkillCategory(BaseModel):
    """A top-level category with skills and optional subcategories."""

    name: str = Field(..., description="Category display name")
    skills: List[SkillEntry] = Field(default_factory=list)
    subcategories: List[SkillSubcategory] = Field(default_factory=list)


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
    categories: List[SkillCategory] = Field(default_factory=list)


class ProjectConfig(BaseSettings):
    """Project-specific configuration, loaded from a YAML file."""

    project_name: str = "My Awesome Project"
    author_email: Optional[str] = None
    version: str = "0.1.0"

    banner_settings: Optional[BannerSettings] = Field(
        default_factory=BannerSettings
    )
    v_card_data: Optional[VCardDataModel] = Field(
        default_factory=VCardDataModel
    )
    qr_code_settings: Optional[QRCodeSettings] = Field(
        default_factory=QRCodeSettings
    )
    word_cloud_settings: Optional[WordCloudSettingsModel] = Field(
        default_factory=WordCloudSettingsModel
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
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if data is None:  # File is empty or only comments/whitespace
                if path == DEFAULT_CONFIG_PATH:
                    # Empty default config file, so create and save defaults
                    print(
                        f"Default config file '{path}' is empty. "
                        "Populating with default values."
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
            raise IOError(f"Error loading config from {path}: {e}") from e
    else:
        # File does not exist
        if path == DEFAULT_CONFIG_PATH:
            # Default config file does not exist, so create and save defaults
            try:
                print(
                    f"Default config file '{path}' not found. "
                    "Creating with default values."
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
        with open(path, "r", encoding="utf-8") as f:
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
                config.model_dump(mode="python"),
                f,
                sort_keys=False,
                indent=2,
                default_flow_style=False,  # Encourage block style
            )
    except Exception as e:
        raise IOError(f"Failed to save config to {path}: {e}") from e


if __name__ == "__main__":
    print(f"--- Testing ProjectConfig ({DEFAULT_CONFIG_PATH}) ---")
    initial_cfg: Optional[ProjectConfig] = None
    try:
        print("Attempting to load existing config...")
        initial_cfg = load_config()
        print("Loaded config (existing or newly created default).")
    except (FileNotFoundError, ValueError, IOError) as e_load:
        print(
            f"Error loading config: {e_load}. "
            "This shouldn't happen if default creation works."
        )
        initial_cfg = ProjectConfig()
        print("Using in-memory default config due to load failure.")

    if initial_cfg:
        print("Current config (loaded or default):")
        # For display, we can dump it as YAML string to test that part too
        try:
            yaml_str_display = yaml.dump(
                initial_cfg.model_dump(mode="python"), 
                indent=2, 
                sort_keys=False
            )
            print(yaml_str_display)
        except Exception as e_display:
            print(
                "Could not serialize current config to YAML for display: "
                f"{e_display}"
            )
            print(initial_cfg.model_dump_json(indent=2))

        initial_cfg.project_name = "Updated Project Name via Test Script"
        if initial_cfg.banner_settings:
            initial_cfg.banner_settings.title = (
                "Updated Banner Title via Test Script"
            )

        print("\nAttempting to save modified config...")
        try:
            save_config(initial_cfg)
            print(f"Saved updated config to {DEFAULT_CONFIG_PATH}.")
        except IOError as e_save_mod:
            print(f"Error saving modified config: {e_save_mod}")

        print("\nAttempting to reload config for verification...")
        try:
            reloaded_cfg = load_config()
            print("Reloaded config:")
            yaml_str_reloaded = yaml.dump(
                reloaded_cfg.model_dump(mode="python"), 
                indent=2, 
                sort_keys=False
            )
            print(yaml_str_reloaded)

            assert reloaded_cfg.project_name == (
                "Updated Project Name via Test Script"
            )
            if reloaded_cfg.banner_settings:
                assert (
                    reloaded_cfg.banner_settings.title ==
                    "Updated Banner Title via Test Script"
                )
            print("Assertion successful: Reloaded matches saved.")
        except (FileNotFoundError, ValueError, IOError) as e_reload:
            print(f"Error reloading/asserting: {e_reload}")
    else:
        print("Critical error: initial_cfg is None after load attempts.")
