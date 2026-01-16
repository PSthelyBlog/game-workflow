"""MCP server registry for managing server configurations.

This module provides a registry for MCP servers used by the workflow.
"""

import os
from dataclasses import dataclass, field


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""

    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)


class MCPServerRegistry:
    """Registry for MCP server configurations.

    Manages the configuration and lifecycle of MCP servers
    used by the workflow agents.
    """

    def __init__(self) -> None:
        """Initialize the registry with default servers."""
        self._servers: dict[str, MCPServerConfig] = {}
        self._register_default_servers()

    def _register_default_servers(self) -> None:
        """Register the default MCP servers."""
        # GitHub MCP server
        github_token = os.environ.get("GITHUB_TOKEN", "")
        self._servers["github"] = MCPServerConfig(
            command="npx",
            args=["@anthropic/github-mcp"],
            env={"GITHUB_TOKEN": github_token},
        )

        # Slack MCP server
        slack_token = os.environ.get("SLACK_BOT_TOKEN", "")
        self._servers["slack"] = MCPServerConfig(
            command="npx",
            args=["@anthropic/slack-mcp"],
            env={"SLACK_BOT_TOKEN": slack_token},
        )

        # itch.io MCP server (custom)
        itchio_key = os.environ.get("ITCHIO_API_KEY", "")
        self._servers["itchio"] = MCPServerConfig(
            command="python",
            args=["-m", "game_workflow.mcp_servers.itchio.server"],
            env={"ITCHIO_API_KEY": itchio_key},
        )

    def get(self, name: str) -> MCPServerConfig | None:
        """Get a server configuration by name.

        Args:
            name: The server name.

        Returns:
            The server configuration, or None if not found.
        """
        return self._servers.get(name)

    def register(self, name: str, config: MCPServerConfig) -> None:
        """Register a new server configuration.

        Args:
            name: The server name.
            config: The server configuration.
        """
        self._servers[name] = config

    def list_servers(self) -> list[str]:
        """List all registered server names.

        Returns:
            List of server names.
        """
        return list(self._servers.keys())
