"""Tests for ProjectConfig validation and load_config behavior."""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from pydantic import ValidationError

from scripts.config import (
    DEFAULT_CONFIG_PATH,
    BannerSettings,
    ProjectConfig,
    QRCodeSettings,
    ReadmeSectionsSettings,
    ReadmeSvgSettings,
    SkillEntry,
    VCardDataModel,
    WordCloudSettingsModel,
    load_config,
    save_config,
)


# ---------------------------------------------------------------------------
# ProjectConfig / nested model defaults & construction
# ---------------------------------------------------------------------------


class TestProjectConfigDefaults:
    def test_defaults(self):
        cfg = ProjectConfig()
        assert cfg.project_name == "My Awesome Project"
        assert cfg.author_email is None
        assert cfg.version == "0.1.0"
        assert isinstance(cfg.banner_settings, BannerSettings)
        assert cfg.banner_settings.seed == 0
        assert isinstance(cfg.v_card_data, VCardDataModel)
        assert isinstance(cfg.qr_code_settings, QRCodeSettings)
        assert isinstance(cfg.word_cloud_settings, WordCloudSettingsModel)
        assert isinstance(cfg.readme_sections_settings, ReadmeSectionsSettings)

    def test_extra_fields_ignored(self):
        cfg = ProjectConfig(project_name="X", unknown_top_level="drop-me")
        assert cfg.project_name == "X"
        assert not hasattr(cfg, "unknown_top_level")

    def test_nested_banner_settings(self):
        cfg = ProjectConfig(
            banner_settings={
                "title": "Hello",
                "subtitle": "World",
                "width": 800,
                "height": 400,
                "optimize_with_svgo": False,
            }
        )
        assert cfg.banner_settings is not None
        assert cfg.banner_settings.title == "Hello"
        assert cfg.banner_settings.subtitle == "World"
        assert cfg.banner_settings.width == 800
        assert cfg.banner_settings.height == 400
        assert cfg.banner_settings.optimize_with_svgo is False
        assert cfg.banner_settings.seed == 0
        assert cfg.banner_settings.output_path == ".github/assets/img/banner.svg"

    def test_banner_settings_to_banner_config_adapter(self):
        from scripts.banner import BannerConfig

        settings = BannerSettings(
            title="Adapted",
            subtitle="Via adapter",
            width=900,
            height=400,
            seed=7,
        )
        cfg = settings.to_banner_config()
        assert isinstance(cfg, BannerConfig)
        assert cfg.title == "Adapted"
        assert cfg.subtitle == "Via adapter"
        assert cfg.width == 900
        assert cfg.height == 400
        assert cfg.seed == 7
        assert cfg.output_path == ".github/assets/img/banner.svg"

        overridden = settings.to_banner_config(title="CLI Title", seed=99)
        assert overridden.title == "CLI Title"
        assert overridden.seed == 99
        assert overridden.subtitle == "Via adapter"

        via_classmethod = BannerConfig.from_banner_settings(settings, dark_mode=True)
        assert via_classmethod.dark_mode is True
        assert via_classmethod.title == "Adapted"

    def test_nested_word_cloud_layout_readability(self):
        cfg = ProjectConfig(
            word_cloud_settings={
                "max_words": 50,
                "prompt": "Python, Rust",
                "stopwords": ["the", "a"],
                "layout_readability": {
                    "fallback_rotation": 15.0,
                    "large_word_threshold_ratio": 0.5,
                    "reading_flow_weight": 1.0,
                    "target_aspect_ratio": 2.0,
                    "landscape_bias_weight": 0.5,
                    "standard_rotations": [0.0, 90.0],
                    "large_word_rotations": [0.0],
                },
            }
        )
        assert cfg.word_cloud_settings is not None
        assert cfg.word_cloud_settings.max_words == 50
        assert cfg.word_cloud_settings.prompt == "Python, Rust"
        assert cfg.word_cloud_settings.stopwords == ["the", "a"]
        lr = cfg.word_cloud_settings.layout_readability
        assert lr.fallback_rotation == 15.0
        assert lr.large_word_threshold_ratio == 0.5
        assert lr.standard_rotations == [0.0, 90.0]
        assert lr.large_word_rotations == [0.0]

    def test_nested_readme_sections_svg_card_styles(self):
        cfg = ProjectConfig(
            readme_sections_settings={
                "blog_post_limit": 3,
                "social_links": [
                    {
                        "label": "GitHub",
                        "url": "https://github.com/example",
                        "color": "181717",
                        "logo": "github",
                    }
                ],
                "featured_repos": [{"full_name": "owner/repo"}],
                "svg": {
                    "enabled": True,
                    "output_dir": ".github/assets/img/readme",
                    "card_styles": {
                        "featured": {
                            "variant": "legacy",
                            "transparent_canvas": False,
                            "show_title": True,
                        }
                    },
                },
            }
        )
        assert cfg.readme_sections_settings is not None
        rs = cfg.readme_sections_settings
        assert rs.blog_post_limit == 3
        assert len(rs.social_links) == 1
        assert rs.social_links[0].label == "GitHub"
        assert rs.featured_repos[0].full_name == "owner/repo"
        assert isinstance(rs.svg, ReadmeSvgSettings)
        assert rs.svg.enabled is True
        featured = rs.svg.card_styles.featured
        assert featured.variant == "legacy"
        assert featured.transparent_canvas is False
        assert featured.show_title is True

    def test_nested_vcard_typed_urls(self):
        cfg = ProjectConfig(
            v_card_data={
                "displayname": "Ada Lovelace",
                "url_work": [
                    {"url": "https://example.com", "label": "Site"},
                ],
            }
        )
        assert cfg.v_card_data is not None
        assert cfg.v_card_data.displayname == "Ada Lovelace"
        assert cfg.v_card_data.url_work is not None
        assert len(cfg.v_card_data.url_work) == 1
        assert str(cfg.v_card_data.url_work[0].url) == "https://example.com/"
        assert cfg.v_card_data.url_work[0].label == "Site"


class TestProjectConfigTypeErrors:
    def test_invalid_version_type(self):
        with pytest.raises(ValidationError):
            ProjectConfig(version=123)

    def test_banner_width_must_be_int(self):
        with pytest.raises(ValidationError):
            ProjectConfig(banner_settings={"width": "wide"})

    def test_word_cloud_max_words_ge_one(self):
        with pytest.raises(ValidationError):
            ProjectConfig(word_cloud_settings={"max_words": 0})

    def test_blog_post_limit_bounds(self):
        with pytest.raises(ValidationError):
            ProjectConfig(readme_sections_settings={"blog_post_limit": 0})
        with pytest.raises(ValidationError):
            ProjectConfig(readme_sections_settings={"blog_post_limit": 11})

    def test_social_link_rejects_bad_url_scheme(self):
        with pytest.raises(ValidationError, match="http"):
            ProjectConfig(
                readme_sections_settings={
                    "social_links": [
                        {"label": "X", "url": "javascript:alert(1)"},
                    ]
                }
            )

    def test_svg_variant_literal(self):
        with pytest.raises(ValidationError):
            ProjectConfig(
                readme_sections_settings={
                    "svg": {
                        "card_styles": {
                            "default": {"variant": "not-a-variant"},
                        }
                    }
                }
            )

    def test_layout_readability_ratio_bounds(self):
        with pytest.raises(ValidationError):
            ProjectConfig(
                word_cloud_settings={
                    "layout_readability": {
                        "large_word_threshold_ratio": 1.5,
                    }
                }
            )

    def test_vcard_invalid_url(self):
        with pytest.raises(ValidationError):
            ProjectConfig(
                v_card_data={
                    "url_work": [{"url": "not-a-url", "label": "Bad"}],
                }
            )


# ---------------------------------------------------------------------------
# load_config — happy path & nested YAML
# ---------------------------------------------------------------------------


class TestLoadConfigHappyPath:
    def test_loads_valid_yaml(self, tmp_path: Path):
        path = tmp_path / "config.yaml"
        path.write_text(
            yaml.dump(
                {
                    "project_name": "Test Project",
                    "author_email": "dev@example.com",
                    "version": "1.2.3",
                    "banner_settings": {
                        "title": "Banner Title",
                        "width": 1000,
                    },
                }
            ),
            encoding="utf-8",
        )
        cfg = load_config(path)
        assert cfg.project_name == "Test Project"
        assert cfg.author_email == "dev@example.com"
        assert cfg.version == "1.2.3"
        assert cfg.banner_settings is not None
        assert cfg.banner_settings.title == "Banner Title"
        assert cfg.banner_settings.width == 1000

    def test_loads_nested_settings_from_yaml(self, tmp_path: Path):
        path = tmp_path / "nested.yaml"
        path.write_text(
            yaml.dump(
                {
                    "project_name": "Nested",
                    "word_cloud_settings": {
                        "max_words": 42,
                        "layout_readability": {
                            "fallback_rotation": 5.0,
                            "target_aspect_ratio": 1.5,
                        },
                    },
                    "readme_sections_settings": {
                        "blog_feed_url": "https://example.com/feed.xml",
                        "blog_post_limit": 7,
                        "svg": {"enabled": True},
                    },
                    "qr_code_settings": {
                        "default_scale": 10,
                        "error_correction": "Q",
                    },
                }
            ),
            encoding="utf-8",
        )
        cfg = load_config(path)
        assert cfg.project_name == "Nested"
        assert cfg.word_cloud_settings is not None
        assert cfg.word_cloud_settings.max_words == 42
        assert cfg.word_cloud_settings.layout_readability.fallback_rotation == 5.0
        assert cfg.word_cloud_settings.layout_readability.target_aspect_ratio == 1.5
        assert cfg.readme_sections_settings is not None
        assert cfg.readme_sections_settings.blog_feed_url == "https://example.com/feed.xml"
        assert cfg.readme_sections_settings.blog_post_limit == 7
        assert cfg.readme_sections_settings.svg.enabled is True
        assert cfg.qr_code_settings is not None
        assert cfg.qr_code_settings.default_scale == 10
        assert cfg.qr_code_settings.error_correction == "Q"

    def test_comment_only_non_default_treated_as_empty(self, tmp_path: Path):
        # Current behavior: empty non-default raises ValueError inside the
        # try block, then the broad except Exception re-wraps it as OSError.
        path = tmp_path / "comments.yaml"
        path.write_text("# only comments\n\n", encoding="utf-8")
        with pytest.raises(OSError, match="YAML file is empty"):
            load_config(path)


# ---------------------------------------------------------------------------
# load_config — missing / empty default path auto-create
# ---------------------------------------------------------------------------


class TestLoadConfigMissingAndEmptyDefault:
    def test_missing_non_default_raises_file_not_found(self, tmp_path: Path):
        missing = tmp_path / "missing.yaml"
        with pytest.raises(FileNotFoundError, match="Config file not found"):
            load_config(missing)

    def test_missing_default_auto_creates(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.chdir(tmp_path)
        assert not Path("./config.yaml").exists()
        cfg = load_config()
        assert isinstance(cfg, ProjectConfig)
        assert Path("./config.yaml").exists()
        assert cfg.project_name == "My Awesome Project"
        # Reloaded content matches what was written
        reloaded = load_config(DEFAULT_CONFIG_PATH)
        assert reloaded.project_name == cfg.project_name
        assert reloaded.version == cfg.version

    def test_empty_default_auto_creates(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.chdir(tmp_path)
        Path("./config.yaml").write_text("", encoding="utf-8")
        cfg = load_config(DEFAULT_CONFIG_PATH)
        assert isinstance(cfg, ProjectConfig)
        assert Path("./config.yaml").stat().st_size > 0
        data = yaml.safe_load(Path("./config.yaml").read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        assert data["project_name"] == "My Awesome Project"

    def test_empty_non_default_raises_oserror(self, tmp_path: Path):
        # Current behavior: ValueError for empty non-default is re-wrapped
        # as OSError by except Exception in load_config (Wave E may fix).
        path = tmp_path / "empty.yaml"
        path.write_text("", encoding="utf-8")
        with pytest.raises(OSError, match="YAML file is empty"):
            load_config(path)

    def test_default_create_failure_wraps_file_not_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.chdir(tmp_path)
        with patch(
            "scripts.config.save_config",
            side_effect=OSError("disk full"),
        ):
            with pytest.raises(FileNotFoundError, match="Attempt to create"):
                load_config(DEFAULT_CONFIG_PATH)


# ---------------------------------------------------------------------------
# load_config — invalid YAML & validation errors
# ---------------------------------------------------------------------------


class TestLoadConfigInvalidContent:
    def test_invalid_yaml_raises_value_error(self, tmp_path: Path):
        path = tmp_path / "bad.yaml"
        path.write_text("project_name: [unclosed\n", encoding="utf-8")
        with pytest.raises(ValueError, match="Invalid YAML"):
            load_config(path)

    def test_invalid_config_data_raises_value_error(self, tmp_path: Path):
        path = tmp_path / "typed.yaml"
        path.write_text(
            yaml.dump(
                {
                    "project_name": "Bad Types",
                    "banner_settings": {"width": "not-an-int"},
                }
            ),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="Invalid config data"):
            load_config(path)

    def test_nested_type_error_in_readme_sections(self, tmp_path: Path):
        path = tmp_path / "readme_bad.yaml"
        path.write_text(
            yaml.dump(
                {
                    "readme_sections_settings": {
                        "blog_post_limit": 99,
                    }
                }
            ),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="Invalid config data"):
            load_config(path)

    def test_unexpected_open_error_wraps_oserror(self, tmp_path: Path):
        path = tmp_path / "locked.yaml"
        path.write_text("project_name: X\n", encoding="utf-8")
        with patch("builtins.open", side_effect=PermissionError("denied")):
            with pytest.raises(OSError, match="Error loading config"):
                load_config(path)

    def test_yaml_error_from_safe_load(self, tmp_path: Path):
        path = tmp_path / "mock_yaml.yaml"
        path.write_text("project_name: X\n", encoding="utf-8")
        with patch(
            "scripts.config.yaml.safe_load",
            side_effect=yaml.YAMLError("boom"),
        ):
            with pytest.raises(ValueError, match="Invalid YAML"):
                load_config(path)


# ---------------------------------------------------------------------------
# save_config round-trip (supports load_config auto-create assertions)
# ---------------------------------------------------------------------------


class TestSaveConfig:
    def test_round_trip(self, tmp_path: Path):
        path = tmp_path / "out" / "config.yaml"
        original = ProjectConfig(
            project_name="Round Trip",
            version="9.9.9",
            banner_settings=BannerSettings(title="Saved"),
        )
        save_config(original, path)
        assert path.exists()
        loaded = load_config(path)
        assert loaded.project_name == "Round Trip"
        assert loaded.version == "9.9.9"
        assert loaded.banner_settings is not None
        assert loaded.banner_settings.title == "Saved"

    def test_save_failure_raises_oserror(self, tmp_path: Path):
        path = tmp_path / "fail.yaml"
        cfg = ProjectConfig()
        with patch("builtins.open", side_effect=OSError("write failed")):
            with pytest.raises(OSError, match="Failed to save config"):
                save_config(cfg, path)


# ---------------------------------------------------------------------------
# Determinism helpers — DEFAULT_CONFIG_PATH identity used by load_config
# ---------------------------------------------------------------------------


class TestDefaultConfigPathContract:
    def test_default_path_equals_relative_config_yaml(self):
        assert DEFAULT_CONFIG_PATH == Path("./config.yaml")
        assert DEFAULT_CONFIG_PATH == Path("config.yaml")

    def test_absolute_path_is_not_default(self, tmp_path: Path):
        absolute = tmp_path / "config.yaml"
        assert absolute != DEFAULT_CONFIG_PATH
        with pytest.raises(FileNotFoundError):
            load_config(absolute)


# ---------------------------------------------------------------------------
# SkillEntry.logo_path jail (repo-relative only)
# ---------------------------------------------------------------------------


class TestSkillEntryLogoPathJail:
    def test_accepts_repo_relative(self):
        entry = SkillEntry(
            name="Python",
            logo_path=".github/assets/skill-icons/python.svg",
            color="3776AB",
        )
        assert entry.logo_path == ".github/assets/skill-icons/python.svg"

    def test_rejects_absolute(self):
        with pytest.raises(ValidationError, match="repo-relative"):
            SkillEntry(name="X", logo_path="/etc/passwd", color="000")

    def test_rejects_traversal(self):
        with pytest.raises(ValidationError, match="must not contain"):
            SkillEntry(name="X", logo_path="../secrets.svg", color="000")

    def test_rejects_url_as_path(self):
        with pytest.raises(ValidationError, match="not a URL"):
            SkillEntry(
                name="X",
                logo_path="https://cdn.example.com/icon.svg",
                color="000",
            )
