"""Tests for the config module."""

from pathlib import Path

import pytest

from game_workflow.config import Settings, WorkflowSettings, load_toml_config, reload_settings


class TestWorkflowSettings:
    """Tests for WorkflowSettings."""

    def test_default_values(self) -> None:
        """Test default settings values."""
        settings = WorkflowSettings()
        assert settings.log_level == "INFO"
        assert settings.default_engine == "phaser"
        assert settings.auto_publish is False
        assert settings.require_all_approvals is True

    def test_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test environment variable override."""
        monkeypatch.setenv("GAME_WORKFLOW_LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("GAME_WORKFLOW_DEFAULT_ENGINE", "godot")

        settings = WorkflowSettings()
        assert settings.log_level == "DEBUG"
        assert settings.default_engine == "godot"


class TestSettings:
    """Tests for main Settings."""

    def test_default_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test default settings."""
        # Clear the API key env var if set
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        settings = Settings()
        # API key will be None or empty string depending on env
        assert not settings.anthropic_api_key  # Falsy check (None or empty)
        assert settings.workflow.default_engine == "phaser"
        assert settings.slack.channel == "#game-dev"

    def test_api_key_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test loading API key from environment."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-123")

        settings = Settings()
        assert settings.anthropic_api_key == "test-key-123"


class TestLoadTomlConfig:
    """Tests for TOML config loading."""

    def test_load_valid_toml(self, tmp_path: Path) -> None:
        """Test loading valid TOML config."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[workflow]
default_engine = "godot"
log_level = "DEBUG"

[slack]
channel = "#test-channel"
""")

        config = load_toml_config(config_file)
        assert config["workflow"]["default_engine"] == "godot"
        assert config["workflow"]["log_level"] == "DEBUG"
        assert config["slack"]["channel"] == "#test-channel"

    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        """Test loading non-existent file raises error."""
        config_file = tmp_path / "nonexistent.toml"

        with pytest.raises(FileNotFoundError):
            load_toml_config(config_file)


class TestReloadSettings:
    """Tests for settings reload."""

    def test_reload_clears_cache(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that reload clears the cache."""
        # First load - ensure the cache is populated
        reload_settings()

        # Change environment
        monkeypatch.setenv("ANTHROPIC_API_KEY", "new-key")

        # Reload
        settings = reload_settings()

        # Should get new value
        assert settings.anthropic_api_key == "new-key"
