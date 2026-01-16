"""Configuration management for game-workflow.

This module handles loading and validating configuration from
environment variables and config files.
"""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkflowSettings(BaseSettings):
    """Workflow configuration settings."""

    model_config = SettingsConfigDict(env_prefix="GAME_WORKFLOW_")

    state_dir: Path = Field(
        default=Path.home() / ".game-workflow" / "state",
        description="Directory for workflow state persistence",
    )
    log_level: str = Field(default="INFO", description="Logging level")
    default_engine: Literal["phaser", "godot"] = Field(
        default="phaser", description="Default game engine"
    )


class SlackSettings(BaseSettings):
    """Slack integration settings."""

    model_config = SettingsConfigDict(env_prefix="SLACK_")

    bot_token: str | None = Field(default=None, description="Slack bot token")
    channel: str = Field(default="#game-dev", description="Default Slack channel")


class GitHubSettings(BaseSettings):
    """GitHub integration settings."""

    model_config = SettingsConfigDict(env_prefix="GITHUB_")

    token: str | None = Field(default=None, description="GitHub personal access token")


class ItchioSettings(BaseSettings):
    """itch.io integration settings."""

    model_config = SettingsConfigDict(env_prefix="ITCHIO_")

    api_key: str | None = Field(default=None, description="itch.io API key")
    username: str | None = Field(default=None, description="itch.io username")


class Settings(BaseSettings):
    """Main settings container."""

    model_config = SettingsConfigDict(env_prefix="")

    anthropic_api_key: str | None = Field(
        default=None, alias="ANTHROPIC_API_KEY", description="Anthropic API key"
    )

    workflow: WorkflowSettings = Field(default_factory=WorkflowSettings)
    slack: SlackSettings = Field(default_factory=SlackSettings)
    github: GitHubSettings = Field(default_factory=GitHubSettings)
    itchio: ItchioSettings = Field(default_factory=ItchioSettings)


def get_settings() -> Settings:
    """Get the application settings."""
    return Settings()
