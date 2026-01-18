"""Tests for the MCP servers module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from game_workflow.mcp_servers import MCPServerConfig, MCPServerProcess, MCPServerRegistry
from game_workflow.mcp_servers.itchio import (
    APIResponse,
    ButlerCLI,
    ButlerPushResult,
    ButlerStatusResult,
    ButlerVersion,
    GameClassification,
    GameType,
    ItchioAPI,
    ItchioGame,
    ItchioUpload,
    ItchioUser,
)


class TestMCPServerConfig:
    """Tests for MCPServerConfig dataclass."""

    def test_config_defaults(self) -> None:
        """Test config has sensible defaults."""
        config = MCPServerConfig(command="python")
        assert config.command == "python"
        assert config.args == []
        assert config.env == {}
        assert config.working_dir is None
        assert config.startup_timeout == 30.0
        assert config.health_check_interval == 10.0

    def test_config_with_all_fields(self) -> None:
        """Test config with all fields set."""
        config = MCPServerConfig(
            command="node",
            args=["server.js"],
            env={"PORT": "3000"},
            working_dir="/app",
            startup_timeout=60.0,
            health_check_interval=5.0,
        )
        assert config.command == "node"
        assert config.args == ["server.js"]
        assert config.env == {"PORT": "3000"}
        assert config.working_dir == "/app"
        assert config.startup_timeout == 60.0
        assert config.health_check_interval == 5.0


class TestMCPServerProcess:
    """Tests for MCPServerProcess dataclass."""

    def test_is_running_no_process(self) -> None:
        """Test is_running returns False when no process."""
        config = MCPServerConfig(command="python")
        proc = MCPServerProcess(name="test", config=config)
        assert proc.is_running is False

    def test_is_running_with_active_process(self) -> None:
        """Test is_running returns True when process is active."""
        config = MCPServerConfig(command="python")
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # None means still running
        proc = MCPServerProcess(name="test", config=config, process=mock_process)
        assert proc.is_running is True

    def test_is_running_with_terminated_process(self) -> None:
        """Test is_running returns False when process has exited."""
        config = MCPServerConfig(command="python")
        mock_process = MagicMock()
        mock_process.poll.return_value = 0  # Exit code means not running
        proc = MCPServerProcess(name="test", config=config, process=mock_process)
        assert proc.is_running is False

    def test_pid_no_process(self) -> None:
        """Test pid returns None when no process."""
        config = MCPServerConfig(command="python")
        proc = MCPServerProcess(name="test", config=config)
        assert proc.pid is None

    def test_pid_with_running_process(self) -> None:
        """Test pid returns process ID when running."""
        config = MCPServerConfig(command="python")
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.pid = 12345
        proc = MCPServerProcess(name="test", config=config, process=mock_process)
        assert proc.pid == 12345


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

    def test_register_custom_server(self) -> None:
        """Test registering a custom server."""
        registry = MCPServerRegistry()
        config = MCPServerConfig(command="python", args=["custom_server.py"])
        registry.register("custom", config)
        assert "custom" in registry.list_servers()
        assert registry.get("custom") == config

    def test_unregister_server(self) -> None:
        """Test unregistering a server."""
        registry = MCPServerRegistry()
        config = MCPServerConfig(command="python")
        registry.register("custom", config)
        assert "custom" in registry.list_servers()
        result = registry.unregister("custom")
        assert result is True
        assert "custom" not in registry.list_servers()

    def test_unregister_nonexistent(self) -> None:
        """Test unregistering a nonexistent server returns False."""
        registry = MCPServerRegistry()
        result = registry.unregister("nonexistent")
        assert result is False

    def test_list_running_empty(self) -> None:
        """Test list_running returns empty list when nothing running."""
        registry = MCPServerRegistry()
        assert registry.list_running() == []

    def test_is_running_false_when_not_started(self) -> None:
        """Test is_running returns False for unstarted server."""
        registry = MCPServerRegistry()
        assert registry.is_running("github") is False

    def test_is_healthy_false_when_not_started(self) -> None:
        """Test is_healthy returns False for unstarted server."""
        registry = MCPServerRegistry()
        assert registry.is_healthy("github") is False

    def test_get_process_none_when_not_started(self) -> None:
        """Test get_process returns None for unstarted server."""
        registry = MCPServerRegistry()
        assert registry.get_process("github") is None

    def test_get_server_stats_none_when_not_started(self) -> None:
        """Test get_server_stats returns None for unstarted server."""
        registry = MCPServerRegistry()
        assert registry.get_server_stats("github") is None

    def test_get_all_stats(self) -> None:
        """Test get_all_stats returns dict for all servers."""
        registry = MCPServerRegistry()
        stats = registry.get_all_stats()
        assert "github" in stats
        assert "slack" in stats
        assert "itchio" in stats


class TestButlerVersion:
    """Tests for ButlerVersion dataclass."""

    def test_from_output_simple(self) -> None:
        """Test parsing simple version output."""
        output = "butler version 15.21.0"
        version = ButlerVersion.from_output(output)
        assert version.version == "15.21.0"

    def test_from_output_with_built_at(self) -> None:
        """Test parsing version with build date."""
        output = "butler version 15.21.0, built on 2024-01-15"
        version = ButlerVersion.from_output(output)
        assert version.version == "15.21.0"
        assert version.built_at == "2024-01-15"

    def test_from_output_with_commit(self) -> None:
        """Test parsing version with commit hash."""
        output = "butler version 15.21.0\ncommit abc123"
        version = ButlerVersion.from_output(output)
        assert version.version == "15.21.0"
        assert version.commit == "abc123"

    def test_from_output_empty(self) -> None:
        """Test parsing empty output."""
        version = ButlerVersion.from_output("")
        assert version.version == "unknown"


class TestButlerPushResult:
    """Tests for ButlerPushResult dataclass."""

    def test_success_result(self) -> None:
        """Test successful push result."""
        result = ButlerPushResult(
            success=True,
            target="user/game",
            channel="html5",
            version="1.0.0",
            build_id=12345,
        )
        assert result.success is True
        assert result.target == "user/game"
        assert result.channel == "html5"
        assert result.version == "1.0.0"
        assert result.build_id == 12345
        assert result.error is None

    def test_failure_result(self) -> None:
        """Test failed push result."""
        result = ButlerPushResult(
            success=False,
            target="user/game",
            channel="html5",
            error="Upload failed",
        )
        assert result.success is False
        assert result.error == "Upload failed"


class TestButlerStatusResult:
    """Tests for ButlerStatusResult dataclass."""

    def test_success_result(self) -> None:
        """Test successful status result."""
        result = ButlerStatusResult(
            success=True,
            target="user/game",
            channels={"html5": {"version": "1.0.0"}},
        )
        assert result.success is True
        assert result.channels == {"html5": {"version": "1.0.0"}}

    def test_default_channels(self) -> None:
        """Test default channels is empty dict."""
        result = ButlerStatusResult(success=True, target="user/game")
        assert result.channels == {}


class TestButlerCLI:
    """Tests for the Butler CLI wrapper."""

    def test_init_default_path(self) -> None:
        """Test Butler initialization with default path."""
        butler = ButlerCLI()
        # Path should be Path type
        assert butler.butler_path.name == "butler"

    def test_init_custom_path(self) -> None:
        """Test Butler initialization with custom path."""
        butler = ButlerCLI("/usr/local/bin/butler")
        assert butler.butler_path == Path("/usr/local/bin/butler")

    def test_init_custom_timeout(self) -> None:
        """Test Butler initialization with custom timeout."""
        butler = ButlerCLI(timeout=600.0)
        assert butler.timeout == 600.0

    def test_check_installed_not_found(self) -> None:
        """Test check_installed returns False when not installed."""
        butler = ButlerCLI("/nonexistent/butler")
        assert butler.check_installed() is False

    def test_get_version_not_found(self) -> None:
        """Test get_version returns None when not installed."""
        butler = ButlerCLI("/nonexistent/butler")
        assert butler.get_version() is None

    def test_is_logged_in_not_found(self) -> None:
        """Test is_logged_in returns False when not installed."""
        butler = ButlerCLI("/nonexistent/butler")
        assert butler.is_logged_in() is False

    @patch("platform.system")
    @patch("platform.machine")
    def test_get_platform_key_darwin_arm64(
        self, mock_machine: MagicMock, mock_system: MagicMock
    ) -> None:
        """Test platform key for M1 Mac."""
        mock_system.return_value = "Darwin"
        mock_machine.return_value = "arm64"
        key = ButlerCLI._get_platform_key()
        assert key == "darwin_arm64"

    @patch("platform.system")
    @patch("platform.machine")
    def test_get_platform_key_darwin_x64(
        self, mock_machine: MagicMock, mock_system: MagicMock
    ) -> None:
        """Test platform key for Intel Mac."""
        mock_system.return_value = "Darwin"
        mock_machine.return_value = "x86_64"
        key = ButlerCLI._get_platform_key()
        assert key == "darwin_x64"

    @patch("platform.system")
    @patch("platform.machine")
    def test_get_platform_key_linux(
        self, mock_machine: MagicMock, mock_system: MagicMock
    ) -> None:
        """Test platform key for Linux."""
        mock_system.return_value = "Linux"
        mock_machine.return_value = "x86_64"
        key = ButlerCLI._get_platform_key()
        assert key == "linux_x64"

    @patch("platform.system")
    @patch("platform.machine")
    def test_get_platform_key_windows(
        self, mock_machine: MagicMock, mock_system: MagicMock
    ) -> None:
        """Test platform key for Windows."""
        mock_system.return_value = "Windows"
        mock_machine.return_value = "AMD64"
        key = ButlerCLI._get_platform_key()
        assert key == "windows_x64"

    @pytest.mark.asyncio
    async def test_push_directory_not_exists(self, tmp_path: Path) -> None:
        """Test push fails when directory doesn't exist."""
        butler = ButlerCLI()
        result = await butler.push(
            directory=tmp_path / "nonexistent",
            target="user/game",
            channel="html5",
        )
        assert result.success is False
        assert "does not exist" in result.error

    @pytest.mark.asyncio
    async def test_push_not_directory(self, tmp_path: Path) -> None:
        """Test push fails when path is not a directory."""
        file_path = tmp_path / "file.txt"
        file_path.touch()
        butler = ButlerCLI()
        result = await butler.push(
            directory=file_path,
            target="user/game",
            channel="html5",
        )
        assert result.success is False
        assert "not a directory" in result.error

    @pytest.mark.asyncio
    async def test_validate_empty_directory(self, tmp_path: Path) -> None:
        """Test validate fails for empty directory."""
        butler = ButlerCLI()
        is_valid, message = await butler.validate(tmp_path)
        assert is_valid is False
        assert "empty" in message.lower()

    @pytest.mark.asyncio
    async def test_validate_with_index_html(self, tmp_path: Path) -> None:
        """Test validate succeeds for HTML5 game."""
        (tmp_path / "index.html").touch()
        butler = ButlerCLI()
        is_valid, message = await butler.validate(tmp_path)
        assert is_valid is True
        assert "HTML5" in message

    @pytest.mark.asyncio
    async def test_validate_with_other_files(self, tmp_path: Path) -> None:
        """Test validate succeeds for directory with files."""
        (tmp_path / "game.exe").touch()
        butler = ButlerCLI()
        is_valid, message = await butler.validate(tmp_path)
        assert is_valid is True
        assert "contains files" in message


class TestItchioGame:
    """Tests for ItchioGame dataclass."""

    def test_from_dict_minimal(self) -> None:
        """Test creating game from minimal dict."""
        game = ItchioGame.from_dict({
            "id": 12345,
            "url": "https://user.itch.io/game",
            "title": "My Game",
        })
        assert game.id == 12345
        assert game.url == "https://user.itch.io/game"
        assert game.title == "My Game"
        assert game.type == GameType.DEFAULT
        assert game.classification == GameClassification.GAME

    def test_from_dict_full(self) -> None:
        """Test creating game from full dict."""
        game = ItchioGame.from_dict({
            "id": 12345,
            "url": "https://user.itch.io/game",
            "title": "My Game",
            "short_text": "A great game",
            "type": "html",
            "classification": "tool",
            "downloads_count": 100,
            "views_count": 1000,
            "p_windows": True,
        })
        assert game.short_text == "A great game"
        assert game.type == GameType.HTML
        assert game.classification == GameClassification.TOOL
        assert game.downloads_count == 100
        assert game.views_count == 1000
        assert game.p_windows is True

    def test_from_dict_unknown_type(self) -> None:
        """Test creating game with unknown type falls back to default."""
        game = ItchioGame.from_dict({
            "id": 12345,
            "url": "https://user.itch.io/game",
            "title": "My Game",
            "type": "unknown_type",
        })
        assert game.type == GameType.DEFAULT


class TestItchioUpload:
    """Tests for ItchioUpload dataclass."""

    def test_from_dict(self) -> None:
        """Test creating upload from dict."""
        upload = ItchioUpload.from_dict({
            "id": 1,
            "game_id": 12345,
            "filename": "game.zip",
            "size": 1024000,
            "channel_name": "html5",
        })
        assert upload.id == 1
        assert upload.game_id == 12345
        assert upload.filename == "game.zip"
        assert upload.size == 1024000
        assert upload.channel_name == "html5"


class TestItchioUser:
    """Tests for ItchioUser dataclass."""

    def test_from_dict(self) -> None:
        """Test creating user from dict."""
        user = ItchioUser.from_dict({
            "id": 123,
            "username": "testuser",
            "url": "https://testuser.itch.io",
            "display_name": "Test User",
            "developer": True,
        })
        assert user.id == 123
        assert user.username == "testuser"
        assert user.url == "https://testuser.itch.io"
        assert user.display_name == "Test User"
        assert user.developer is True


class TestAPIResponse:
    """Tests for APIResponse dataclass."""

    def test_from_response_success(self) -> None:
        """Test creating response from successful HTTP response."""
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {"user": {"id": 123}}

        response = APIResponse.from_response(mock_response)
        assert response.success is True
        assert response.data == {"user": {"id": 123}}
        assert response.error is None

    def test_from_response_with_errors(self) -> None:
        """Test creating response with API errors."""
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = {"errors": ["Invalid API key"]}

        response = APIResponse.from_response(mock_response)
        assert response.success is False
        assert response.error == "Invalid API key"
        assert response.errors == ["Invalid API key"]

    def test_from_response_parse_error(self) -> None:
        """Test creating response when JSON parsing fails."""
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")

        response = APIResponse.from_response(mock_response)
        assert response.success is False
        assert "Failed to parse" in response.error


class TestItchioAPI:
    """Tests for ItchioAPI class."""

    def test_init_with_api_key(self) -> None:
        """Test initialization with API key."""
        api = ItchioAPI(api_key="test_key")
        assert api.api_key == "test_key"
        assert api.timeout == 30.0
        assert api.max_retries == 3

    def test_init_with_custom_settings(self) -> None:
        """Test initialization with custom settings."""
        api = ItchioAPI(
            api_key="test_key",
            timeout=60.0,
            max_retries=5,
            retry_delay=2.0,
        )
        assert api.timeout == 60.0
        assert api.max_retries == 5
        assert api.retry_delay == 2.0

    def test_get_key_param(self) -> None:
        """Test _get_key_param returns correct dict."""
        api = ItchioAPI(api_key="test_key")
        assert api._get_key_param() == {"api_key": "test_key"}

    def test_get_key_param_empty(self) -> None:
        """Test _get_key_param returns empty dict when no key."""
        api = ItchioAPI(api_key="")
        assert api._get_key_param() == {}

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Test async context manager creates and closes client."""
        async with ItchioAPI(api_key="test_key") as api:
            assert api._client is not None
        assert api._client is None

    @pytest.mark.asyncio
    async def test_client_property_creates_client(self) -> None:
        """Test client property creates client if needed."""
        api = ItchioAPI(api_key="test_key")
        assert api._client is None
        _ = api.client  # Access property
        assert api._client is not None
        await api.close()
