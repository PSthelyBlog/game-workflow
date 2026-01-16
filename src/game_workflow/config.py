"""Configuration management for game-workflow.

This module handles loading and validating configuration from
environment variables and TOML config files.

Configuration is loaded in the following order (later sources override earlier):
1. Default values
2. TOML config file (~/.game-workflow/config.toml)
3. Environment variables
"""

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import tomli
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Default config file location
DEFAULT_CONFIG_PATH = Path.home() / ".game-workflow" / "config.toml"


class WorkflowSettings(BaseSettings):
    """Workflow configuration settings."""

    model_config = SettingsConfigDict(env_prefix="GAME_WORKFLOW_")

    state_dir: Path = Field(
        default=Path.home() / ".game-workflow" / "state",
        description="Directory for workflow state persistence",
    )
    log_dir: Path = Field(
        default=Path.home() / ".game-workflow" / "logs",
        description="Directory for log files",
    )
    log_level: str = Field(default="INFO", description="Logging level")
    default_engine: Literal["phaser", "godot"] = Field(
        default="phaser", description="Default game engine"
    )
    auto_publish: bool = Field(default=False, description="Automatically publish without approval")
    require_all_approvals: bool = Field(default=True, description="Require all approval gates")


class SlackSettings(BaseSettings):
    """Slack integration settings."""

    model_config = SettingsConfigDict(env_prefix="SLACK_")

    bot_token: str | None = Field(default=None, description="Slack bot token")
    channel: str = Field(default="#game-dev", description="Default Slack channel")
    notify_on_error: bool = Field(default=True, description="Send Slack notifications on errors")


class GitHubSettings(BaseSettings):
    """GitHub integration settings."""

    model_config = SettingsConfigDict(env_prefix="GITHUB_")

    token: str | None = Field(default=None, description="GitHub personal access token")
    default_org: str | None = Field(default=None, description="Default GitHub organization")
    template_repo: str | None = Field(default=None, description="Template repository name")


class ItchioSettings(BaseSettings):
    """itch.io integration settings."""

    model_config = SettingsConfigDict(env_prefix="ITCHIO_")

    api_key: str | None = Field(default=None, description="itch.io API key")
    username: str | None = Field(default=None, description="itch.io username")
    default_visibility: Literal["draft", "public", "restricted"] = Field(
        default="draft", description="Default game visibility on itch.io"
    )


class Settings(BaseSettings):
    """Main settings container.

    Loads configuration from:
    1. Default values
    2. TOML config file (if exists)
    3. Environment variables (highest priority)
    """

    model_config = SettingsConfigDict(env_prefix="")

    anthropic_api_key: str | None = Field(
        default=None, alias="ANTHROPIC_API_KEY", description="Anthropic API key"
    )

    workflow: WorkflowSettings = Field(default_factory=WorkflowSettings)
    slack: SlackSettings = Field(default_factory=SlackSettings)
    github: GitHubSettings = Field(default_factory=GitHubSettings)
    itchio: ItchioSettings = Field(default_factory=ItchioSettings)

    @model_validator(mode="before")
    @classmethod
    def load_config_file(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Load configuration from TOML file before environment variables.

        Args:
            data: The initial data dictionary.

        Returns:
            Updated data dictionary with TOML config merged in.
        """
        config_path = Path(data.get("config_path", DEFAULT_CONFIG_PATH))

        if config_path.exists():
            file_config = load_toml_config(config_path)
            # Merge file config with provided data (data takes precedence)
            merged = _deep_merge(file_config, data)
            return merged

        return data


def load_toml_config(config_path: Path) -> dict[str, Any]:
    """Load configuration from a TOML file.

    Args:
        config_path: Path to the TOML configuration file.

    Returns:
        Dictionary containing the configuration.

    Raises:
        FileNotFoundError: If the config file doesn't exist.
        tomli.TOMLDecodeError: If the TOML is invalid.
    """
    with config_path.open("rb") as f:
        return tomli.load(f)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two dictionaries.

    Args:
        base: The base dictionary.
        override: The dictionary to merge in (values take precedence).

    Returns:
        Merged dictionary.
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


@lru_cache
def get_settings() -> Settings:
    """Get the application settings (cached).

    Returns:
        The application settings instance.
    """
    return Settings()


def reload_settings() -> Settings:
    """Reload settings, clearing the cache.

    Returns:
        Fresh settings instance.
    """
    get_settings.cache_clear()
    return get_settings()
