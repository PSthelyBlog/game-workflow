"""Tests for the MCP servers module."""

from game_workflow.mcp_servers import MCPServerRegistry
from game_workflow.mcp_servers.itchio import ButlerCLI


class TestMCPServerRegistry:
    """Tests for the MCP server registry."""

    def test_default_servers_registered(self) -> None:
        """Test that default servers are registered."""
        registry = MCPServerRegistry()
        servers = registry.list_servers()
        assert "github" in servers
        assert "slack" in servers
        assert "itchio" in servers

    def test_get_server_config(self) -> None:
        """Test getting a server configuration."""
        registry = MCPServerRegistry()
        github = registry.get("github")
        assert github is not None
        assert github.command == "npx"
        assert "@anthropic/github-mcp" in github.args

    def test_get_nonexistent_server(self) -> None:
        """Test getting a non-existent server returns None."""
        registry = MCPServerRegistry()
        result = registry.get("nonexistent")
        assert result is None


class TestButlerCLI:
    """Tests for the Butler CLI wrapper."""

    def test_init_default_path(self) -> None:
        """Test Butler initialization with default path."""
        butler = ButlerCLI()
        assert butler.butler_path == "butler"

    def test_init_custom_path(self) -> None:
        """Test Butler initialization with custom path."""
        butler = ButlerCLI("/usr/local/bin/butler")
        assert butler.butler_path == "/usr/local/bin/butler"
