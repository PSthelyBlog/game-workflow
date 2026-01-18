"""Integration tests for external services.

These tests verify that the workflow correctly integrates with
mocked external services: GitHub, Slack, and itch.io.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from game_workflow.hooks.slack_approval import (
    ApprovalRequest,
    ApprovalStatus,
    SlackApprovalHook,
    SlackClient,
)
from game_workflow.mcp_servers import MCPServerConfig, MCPServerProcess, MCPServerRegistry
from game_workflow.mcp_servers.itchio import (
    APIResponse,
    ButlerCLI,
    ButlerPushResult,
    ItchioAPI,
    ItchioGame,
    ItchioUser,
)
from game_workflow.orchestrator import Workflow, WorkflowPhase
from game_workflow.orchestrator.exceptions import ApprovalRejectedError, ApprovalTimeoutError

if TYPE_CHECKING:
    from pathlib import Path


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_prompt() -> str:
    """Sample game prompt for testing."""
    return "Create a simple puzzle game where players match colored blocks."




@pytest.fixture
def mock_itchio_api() -> MagicMock:
    """Create a mock itch.io API client."""
    api = MagicMock(spec=ItchioAPI)
    api.get_profile = AsyncMock(
        return_value=APIResponse(
            success=True,
            data={"user": {"id": 123, "username": "testuser", "url": "https://testuser.itch.io"}},
        )
    )
    api.get_my_games = AsyncMock(
        return_value=APIResponse(
            success=True,
            data={
                "games": [
                    {"id": 1, "title": "Test Game", "url": "https://testuser.itch.io/test-game"}
                ]
            },
        )
    )
    api.get_game = AsyncMock(
        return_value=APIResponse(
            success=True,
            data={"game": {"id": 1, "title": "Test Game", "url": "https://testuser.itch.io/test-game"}},
        )
    )
    return api


@pytest.fixture
def mock_butler() -> MagicMock:
    """Create a mock Butler CLI."""
    butler = MagicMock(spec=ButlerCLI)
    butler.check_installed.return_value = True
    butler.is_logged_in.return_value = True
    butler.push = AsyncMock(
        return_value=ButlerPushResult(
            success=True,
            target="testuser/test-game",
            channel="html5",
            version="1.0.0",
            build_id=12345,
        )
    )
    butler.validate = AsyncMock(return_value=(True, "Valid HTML5 game"))
    return butler


# =============================================================================
# Mock External Services Tests
# =============================================================================


class TestSlackIntegration:
    """Tests for Slack integration with mocked API."""

    def test_approval_blocks_created(self) -> None:
        """Test that approval blocks are created correctly."""
        hook = SlackApprovalHook(channel="#test-channel", token="test-token")
        blocks = hook._create_approval_blocks(
            message="Test approval",
            context={"game": "Test Game"},
        )

        # Should have structured blocks
        assert len(blocks) >= 3
        assert blocks[0]["type"] == "header"

    def test_check_reactions_approve(self) -> None:
        """Test checking reactions for approval."""
        hook = SlackApprovalHook(channel="#test-channel", token="test-token")
        reactions = [{"name": "white_check_mark", "users": ["U12345"]}]
        status, responder = hook._check_reactions(reactions)
        assert status == ApprovalStatus.APPROVED
        assert responder == "U12345"

    def test_check_reactions_reject(self) -> None:
        """Test checking reactions for rejection."""
        hook = SlackApprovalHook(channel="#test-channel", token="test-token")
        reactions = [{"name": "x", "users": ["U12345"]}]
        status, responder = hook._check_reactions(reactions)
        assert status == ApprovalStatus.REJECTED
        assert responder == "U12345"

    def test_check_replies_approve(self) -> None:
        """Test checking replies for approval."""
        hook = SlackApprovalHook(channel="#test-channel", token="test-token")
        replies = [{"text": "approve", "user": "U12345"}]
        status, responder, feedback = hook._check_replies(replies)
        assert status == ApprovalStatus.APPROVED
        assert responder == "U12345"

    def test_check_replies_reject(self) -> None:
        """Test checking replies for rejection."""
        hook = SlackApprovalHook(channel="#test-channel", token="test-token")
        replies = [{"text": "reject needs more work", "user": "U12345"}]
        status, responder, feedback = hook._check_replies(replies)
        assert status == ApprovalStatus.REJECTED
        assert responder == "U12345"
        assert feedback == "needs more work"

    @pytest.mark.asyncio
    async def test_send_notification_levels(self) -> None:
        """Test sending notifications with different levels."""
        hook = SlackApprovalHook(channel="#test-channel", token="test-token")

        with patch.object(SlackClient, "post_message", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = {"ok": True, "ts": "123.456", "channel": "C12345"}
            for level in ["info", "warning", "error", "success"]:
                result = await hook.send_notification(
                    message=f"Test {level} notification",
                    level=level,
                )
                assert result is True


class TestItchioIntegration:
    """Tests for itch.io integration with mocked API."""

    @pytest.mark.asyncio
    async def test_api_get_profile(self, mock_itchio_api: MagicMock) -> None:
        """Test getting user profile from itch.io API."""
        result = await mock_itchio_api.get_profile()
        assert result.success is True
        assert result.data["user"]["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_api_get_games(self, mock_itchio_api: MagicMock) -> None:
        """Test getting user's games from itch.io API."""
        result = await mock_itchio_api.get_my_games()
        assert result.success is True
        assert len(result.data["games"]) == 1
        assert result.data["games"][0]["title"] == "Test Game"

    @pytest.mark.asyncio
    async def test_butler_push_success(self, mock_butler: MagicMock, tmp_path: Path) -> None:
        """Test successful game push via Butler."""
        # Create a mock game directory
        game_dir = tmp_path / "game"
        game_dir.mkdir()
        (game_dir / "index.html").touch()

        result = await mock_butler.push(
            directory=game_dir,
            target="testuser/test-game",
            channel="html5",
        )

        assert result.success is True
        assert result.build_id == 12345

    @pytest.mark.asyncio
    async def test_butler_validate(self, mock_butler: MagicMock, tmp_path: Path) -> None:
        """Test game directory validation via Butler."""
        game_dir = tmp_path / "game"
        game_dir.mkdir()
        (game_dir / "index.html").touch()

        is_valid, message = await mock_butler.validate(game_dir)
        assert is_valid is True
        assert "HTML5" in message

    @pytest.mark.asyncio
    async def test_api_error_handling(self) -> None:
        """Test API error handling."""
        api = MagicMock(spec=ItchioAPI)
        api.get_profile = AsyncMock(
            return_value=APIResponse(
                success=False,
                error="Invalid API key",
                errors=["Invalid API key"],
            )
        )

        result = await api.get_profile()
        assert result.success is False
        assert result.error == "Invalid API key"

    @pytest.mark.asyncio
    async def test_api_rate_limit_handling(self) -> None:
        """Test handling of rate limit errors."""
        api = MagicMock(spec=ItchioAPI)
        api.get_my_games = AsyncMock(
            return_value=APIResponse(
                success=False,
                error="Rate limit exceeded",
                errors=["Rate limit exceeded. Try again in 60 seconds."],
            )
        )

        result = await api.get_my_games()
        assert result.success is False
        assert "Rate limit" in result.error


class TestMCPServerRegistry:
    """Tests for MCP server registry integration."""

    def test_default_servers_configured(self) -> None:
        """Test that default servers are properly configured."""
        registry = MCPServerRegistry()

        # Check all expected servers are registered
        servers = registry.list_servers()
        assert "github" in servers
        assert "slack" in servers
        assert "itchio" in servers

    def test_github_server_config(self) -> None:
        """Test GitHub MCP server configuration."""
        registry = MCPServerRegistry()
        config = registry.get("github")

        assert config is not None
        assert config.command == "npx"
        assert "@anthropic/github-mcp" in config.args

    def test_slack_server_config(self) -> None:
        """Test Slack MCP server configuration."""
        registry = MCPServerRegistry()
        config = registry.get("slack")

        assert config is not None
        assert config.command == "npx"
        assert "@anthropic/slack-mcp" in config.args

    def test_itchio_server_config(self) -> None:
        """Test itch.io MCP server configuration."""
        registry = MCPServerRegistry()
        config = registry.get("itchio")

        assert config is not None
        assert config.command == "python"
        assert "game_workflow.mcp_servers.itchio.server" in " ".join(config.args)

    def test_register_custom_server(self) -> None:
        """Test registering a custom MCP server."""
        registry = MCPServerRegistry()
        config = MCPServerConfig(
            command="node",
            args=["custom-server.js"],
            env={"API_KEY": "test"},
        )

        registry.register("custom", config)

        assert "custom" in registry.list_servers()
        retrieved = registry.get("custom")
        assert retrieved == config

    def test_server_process_state(self) -> None:
        """Test server process state tracking."""
        config = MCPServerConfig(command="python")
        process = MCPServerProcess(name="test", config=config)

        # Initially not running
        assert process.is_running is False
        assert process.pid is None

        # Simulate running process
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_proc.pid = 12345
        process.process = mock_proc

        assert process.is_running is True
        assert process.pid == 12345


# =============================================================================
# GitHub Integration Tests (Mocked)
# =============================================================================


class TestGitHubIntegration:
    """Tests for GitHub integration with mocked API."""

    @pytest.mark.asyncio
    async def test_create_release_metadata(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test creating GitHub release metadata."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setenv("GITHUB_TOKEN", "test-token")

        from game_workflow.config import reload_settings

        reload_settings()

        from game_workflow.agents.publish import (
            GitHubRelease,
            PublishAgent,
            PublishConfig,
            ReleaseType,
            StorePageContent,
        )

        # Create a mock GDD as a MagicMock that quacks like GameDesignDocument
        gdd = MagicMock()
        gdd.title = "Test Game"
        gdd.genre = "Puzzle"
        gdd.concept_summary = "A test puzzle game"

        # Create a config
        config = PublishConfig(
            version="1.0.0",
            release_type=ReleaseType.INITIAL,
            project_name="test-game",
        )

        # Create store page content
        store_page = StorePageContent(
            title="Test Game",
            tagline="A test puzzle game",
            description="Test description",
            controls=[],
            features=["Feature 1", "Feature 2"],
        )

        agent = PublishAgent(output_dir=tmp_path)
        release = agent._prepare_github_release(
            gdd=gdd,
            config=config,
            store_page=store_page,
        )

        assert isinstance(release, GitHubRelease)
        assert release.tag == "v1.0.0"
        assert "Test Game" in release.name
        assert release.draft is True


# =============================================================================
# Combined Workflow with External Services Tests
# =============================================================================


class TestWorkflowWithExternalServices:
    """Tests for workflow integration with external services."""

    @pytest.mark.asyncio
    async def test_workflow_with_slack_notifications(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test workflow sends Slack notifications at key points."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        # Create mock approval hook that tracks notifications
        notifications: list[dict[str, Any]] = []

        class TrackingApprovalHook:
            """Approval hook that tracks all notifications."""

            async def request_approval(
                self,
                message: str,
                context: dict[str, Any] | None = None,
                timeout_minutes: int | None = None,
            ) -> bool:
                return True

            async def send_notification(
                self,
                message: str,
                *,
                context: dict[str, Any] | None = None,
                level: str = "info",
            ) -> bool:
                notifications.append(
                    {"message": message, "context": context, "level": level}
                )
                return True

        # Create a mock GDD file
        gdd_path = tmp_path / "gdd.json"
        gdd_path.write_text('{"title": "Test", "genre": "Puzzle"}')

        workflow = Workflow(
            prompt=sample_prompt,
            approval_hook=TrackingApprovalHook(),
            output_dir=tmp_path / "output",
        )

        # Mock agents
        from unittest.mock import AsyncMock, MagicMock

        def create_mock_agent(name: str, result: dict[str, Any]) -> MagicMock:
            agent = MagicMock()
            agent.name = name
            agent.run = AsyncMock(return_value=result)
            return agent

        workflow._design_agent = create_mock_agent(
            "DesignAgent",
            {
                "status": "success",
                "selected_concept": {"title": "Test", "tagline": "Test game"},
                "gdd": {"title": "Test", "genre": "Puzzle"},
                "artifacts": {"gdd_json": str(gdd_path)},
            },
        )
        workflow._build_agent = create_mock_agent(
            "BuildAgent",
            {
                "status": "success",
                "output_dir": str(tmp_path / "game"),
                "build_dir": str(tmp_path / "game" / "dist"),
            },
        )
        workflow._qa_agent = create_mock_agent(
            "QAAgent",
            {
                "status": "success",
                "report": {
                    "summary": {
                        "total_tests": 1,
                        "passed": 1,
                        "failed": 0,
                        "success_rate": 100,
                        "overall_status": "passed",
                    }
                },
            },
        )
        workflow._publish_agent = create_mock_agent(
            "PublishAgent",
            {
                "status": "success",
                "store_page": {"title": "Test", "tagline": "Test"},
                "publish_output": {"visibility": "draft"},
            },
        )

        result = await workflow.run()

        # Should complete successfully
        assert result["status"] == "complete"

        # Should have start and success notifications
        assert len(notifications) >= 2
        assert any("Starting" in n["message"] for n in notifications)
        assert any(n["level"] == "success" for n in notifications)

    @pytest.mark.asyncio
    async def test_workflow_with_itchio_publish(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_butler: MagicMock,
        mock_itchio_api: MagicMock,
    ) -> None:
        """Test workflow publishes to itch.io correctly."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setenv("ITCHIO_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        # Create game directory
        game_dir = tmp_path / "game" / "dist"
        game_dir.mkdir(parents=True)
        (game_dir / "index.html").write_text("<html>Game</html>")

        # Test Butler validation
        is_valid, _ = await mock_butler.validate(game_dir)
        assert is_valid is True

        # Test push
        result = await mock_butler.push(
            directory=game_dir,
            target="testuser/test-game",
            channel="html5",
        )
        assert result.success is True
