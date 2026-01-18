"""Integration tests for error scenarios.

These tests verify error handling in the workflow:
- Agent failures (DesignAgent, BuildAgent, QAAgent, PublishAgent)
- API errors (rate limits, auth failures, network errors)
- Timeout handling
- Error recovery and retry logic
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from game_workflow.orchestrator import Workflow, WorkflowPhase
from game_workflow.orchestrator.exceptions import (
    AgentError,
    BuildFailedError,
    QAFailedError,
)

if TYPE_CHECKING:
    from pathlib import Path


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_prompt() -> str:
    """Sample game prompt for testing."""
    return "Create a simple puzzle game where players match colored blocks."


def create_mock_agent(
    name: str,
    result: dict[str, Any] | None = None,
    error: Exception | None = None,
) -> MagicMock:
    """Create a mock agent with standard interface."""
    agent = MagicMock()
    agent.name = name
    if error:
        agent.run = AsyncMock(side_effect=error)
    else:
        agent.run = AsyncMock(return_value=result or {"status": "success"})
    return agent


class MockApprovalHook:
    """Mock approval hook that always approves."""

    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []
        self.notifications: list[dict[str, Any]] = []

    async def request_approval(
        self,
        message: str,
        context: dict[str, Any] | None = None,
        timeout_minutes: int | None = None,
    ) -> bool:
        self.requests.append({
            "message": message,
            "context": context,
            "timeout_minutes": timeout_minutes,
        })
        return True

    async def send_notification(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
        level: str = "info",
    ) -> bool:
        self.notifications.append({
            "message": message,
            "context": context,
            "level": level,
        })
        return True


@pytest.fixture
def mock_design_result(tmp_path: Path) -> dict[str, Any]:
    """Mock result from DesignAgent."""
    # Create a mock GDD file
    gdd_path = tmp_path / "design" / "gdd.json"
    gdd_path.parent.mkdir(parents=True, exist_ok=True)
    gdd_path.write_text('{"title": "Block Match Puzzle", "genre": "Puzzle"}')

    return {
        "status": "success",
        "selected_concept": {
            "title": "Block Match Puzzle",
            "genre": "Puzzle",
            "tagline": "Match colors, solve puzzles!",
        },
        "gdd": {"title": "Block Match Puzzle", "genre": "Puzzle"},
        "artifacts": {"gdd_json": str(gdd_path)},
    }


@pytest.fixture
def mock_build_result(tmp_path: Path) -> dict[str, Any]:
    """Mock result from BuildAgent."""
    return {
        "status": "success",
        "output_dir": str(tmp_path / "game"),
        "build_dir": str(tmp_path / "game" / "dist"),
    }


@pytest.fixture
def mock_qa_result() -> dict[str, Any]:
    """Mock result from QAAgent."""
    return {
        "status": "success",
        "report": {
            "summary": {
                "total_tests": 8,
                "passed": 8,
                "failed": 0,
                "success_rate": 100.0,
                "overall_status": "passed",
            }
        },
    }


@pytest.fixture
def mock_publish_result() -> dict[str, Any]:
    """Mock result from PublishAgent."""
    return {
        "status": "success",
        "store_page": {
            "title": "Block Match Puzzle",
            "tagline": "Match colors, solve puzzles!",
        },
        "publish_output": {"visibility": "draft"},
    }


# =============================================================================
# Agent Failure Tests
# =============================================================================


class TestDesignAgentFailure:
    """Tests for DesignAgent failure scenarios."""

    @pytest.mark.asyncio
    async def test_design_agent_error(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test workflow handles DesignAgent error."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            auto_approve=True,
            output_dir=tmp_path / "output",
            max_retries=0,  # No retries
        )

        workflow._design_agent = create_mock_agent(
            "DesignAgent",
            error=AgentError("DesignAgent", "Failed to generate concept"),
        )

        result = await workflow.run()

        assert result["status"] == "failed"
        assert len(result["errors"]) > 0
        assert workflow.phase == WorkflowPhase.FAILED

    @pytest.mark.asyncio
    async def test_design_agent_api_error(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test workflow handles API error in DesignAgent."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            auto_approve=True,
            output_dir=tmp_path / "output",
            max_retries=0,
        )

        # Simulate API rate limit error
        workflow._design_agent = create_mock_agent(
            "DesignAgent",
            error=AgentError("DesignAgent", "API rate limit exceeded"),
        )

        result = await workflow.run()

        assert result["status"] == "failed"
        assert any("rate limit" in e.lower() for e in result["errors"])


class TestBuildAgentFailure:
    """Tests for BuildAgent failure scenarios."""

    @pytest.mark.asyncio
    async def test_build_failed_error(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
    ) -> None:
        """Test workflow handles BuildFailedError."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            auto_approve=True,
            output_dir=tmp_path / "output",
            max_retries=0,
        )

        workflow._design_agent = create_mock_agent("DesignAgent", mock_design_result)
        workflow._build_agent = create_mock_agent(
            "BuildAgent",
            error=BuildFailedError("Build failed", build_output="npm ERR!"),
        )

        result = await workflow.run()

        assert result["status"] == "failed"
        assert workflow.phase == WorkflowPhase.FAILED

    @pytest.mark.asyncio
    async def test_build_npm_install_failure(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
    ) -> None:
        """Test workflow handles npm install failure."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            auto_approve=True,
            output_dir=tmp_path / "output",
            max_retries=0,
        )

        workflow._design_agent = create_mock_agent("DesignAgent", mock_design_result)
        workflow._build_agent = create_mock_agent(
            "BuildAgent",
            error=BuildFailedError(
                "npm install failed",
                build_output="npm ERR! network timeout",
            ),
        )

        result = await workflow.run()

        assert result["status"] == "failed"

    @pytest.mark.asyncio
    async def test_build_claude_code_failure(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
    ) -> None:
        """Test workflow handles Claude Code failure."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            auto_approve=True,
            output_dir=tmp_path / "output",
            max_retries=0,
        )

        workflow._design_agent = create_mock_agent("DesignAgent", mock_design_result)
        workflow._build_agent = create_mock_agent(
            "BuildAgent",
            error=BuildFailedError(
                "Claude Code failed",
                build_output="Error: Claude Code process exited with code 1",
            ),
        )

        result = await workflow.run()

        assert result["status"] == "failed"


class TestQAAgentFailure:
    """Tests for QAAgent failure scenarios."""

    @pytest.mark.asyncio
    async def test_qa_failed_error(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
        mock_build_result: dict[str, Any],
    ) -> None:
        """Test workflow handles QAFailedError."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            auto_approve=True,
            output_dir=tmp_path / "output",
            max_retries=0,
        )

        workflow._design_agent = create_mock_agent("DesignAgent", mock_design_result)
        workflow._build_agent = create_mock_agent("BuildAgent", mock_build_result)
        workflow._qa_agent = create_mock_agent(
            "QAAgent",
            error=QAFailedError(
                "Critical test failures",
                test_results={"failed": ["page_loads"]},
            ),
        )

        result = await workflow.run()

        assert result["status"] == "failed"

    @pytest.mark.asyncio
    async def test_qa_playwright_not_installed(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
        mock_build_result: dict[str, Any],
    ) -> None:
        """Test workflow handles missing Playwright."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            auto_approve=True,
            output_dir=tmp_path / "output",
            max_retries=0,
        )

        workflow._design_agent = create_mock_agent("DesignAgent", mock_design_result)
        workflow._build_agent = create_mock_agent("BuildAgent", mock_build_result)
        workflow._qa_agent = create_mock_agent(
            "QAAgent",
            error=AgentError("QAAgent", "Playwright not installed"),
        )

        result = await workflow.run()

        assert result["status"] == "failed"


class TestPublishAgentFailure:
    """Tests for PublishAgent failure scenarios."""

    @pytest.mark.asyncio
    async def test_publish_agent_error(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
        mock_build_result: dict[str, Any],
        mock_qa_result: dict[str, Any],
    ) -> None:
        """Test workflow handles PublishAgent error."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            auto_approve=True,
            output_dir=tmp_path / "output",
            max_retries=0,
        )

        workflow._design_agent = create_mock_agent("DesignAgent", mock_design_result)
        workflow._build_agent = create_mock_agent("BuildAgent", mock_build_result)
        workflow._qa_agent = create_mock_agent("QAAgent", mock_qa_result)
        workflow._publish_agent = create_mock_agent(
            "PublishAgent",
            error=AgentError("PublishAgent", "Failed to generate marketing copy"),
        )

        result = await workflow.run()

        assert result["status"] == "failed"

    @pytest.mark.asyncio
    async def test_publish_itchio_upload_failure(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
        mock_build_result: dict[str, Any],
        mock_qa_result: dict[str, Any],
    ) -> None:
        """Test workflow handles itch.io upload failure."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            auto_approve=True,
            output_dir=tmp_path / "output",
            max_retries=0,
        )

        workflow._design_agent = create_mock_agent("DesignAgent", mock_design_result)
        workflow._build_agent = create_mock_agent("BuildAgent", mock_build_result)
        workflow._qa_agent = create_mock_agent("QAAgent", mock_qa_result)
        workflow._publish_agent = create_mock_agent(
            "PublishAgent",
            error=AgentError("PublishAgent", "itch.io upload failed: Invalid API key"),
        )

        result = await workflow.run()

        assert result["status"] == "failed"


# =============================================================================
# Retry Logic Tests
# =============================================================================


class TestRetryLogic:
    """Tests for error retry logic."""

    @pytest.mark.asyncio
    async def test_retry_succeeds_after_failure(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
        mock_build_result: dict[str, Any],
        mock_qa_result: dict[str, Any],
        mock_publish_result: dict[str, Any],
    ) -> None:
        """Test that retry succeeds after initial failure."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            auto_approve=True,
            output_dir=tmp_path / "output",
            max_retries=2,
        )

        workflow._design_agent = create_mock_agent("DesignAgent", mock_design_result)

        # Build fails twice then succeeds
        call_count = 0

        async def failing_build(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise BuildFailedError("Transient failure", build_output="Error")
            return mock_build_result

        workflow._build_agent = MagicMock()
        workflow._build_agent.name = "BuildAgent"
        workflow._build_agent.run = AsyncMock(side_effect=failing_build)

        workflow._qa_agent = create_mock_agent("QAAgent", mock_qa_result)
        workflow._publish_agent = create_mock_agent("PublishAgent", mock_publish_result)

        result = await workflow.run()

        # Should succeed after retries
        assert result["status"] == "complete"
        assert call_count == 3  # 2 failures + 1 success

    @pytest.mark.asyncio
    async def test_retry_exhausted_fails(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
    ) -> None:
        """Test that workflow fails after retries exhausted."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            auto_approve=True,
            output_dir=tmp_path / "output",
            max_retries=1,
        )

        workflow._design_agent = create_mock_agent("DesignAgent", mock_design_result)
        workflow._build_agent = create_mock_agent(
            "BuildAgent",
            error=BuildFailedError("Persistent failure", build_output="Error"),
        )

        result = await workflow.run()

        # Should fail after retries exhausted
        assert result["status"] == "failed"
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_retry_sends_notifications(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
        mock_build_result: dict[str, Any],
        mock_qa_result: dict[str, Any],
        mock_publish_result: dict[str, Any],
    ) -> None:
        """Test that retry sends warning notifications."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        hook = MockApprovalHook()
        workflow = Workflow(
            prompt=sample_prompt,
            approval_hook=hook,
            output_dir=tmp_path / "output",
            max_retries=2,
        )

        workflow._design_agent = create_mock_agent("DesignAgent", mock_design_result)

        # Build fails once then succeeds
        call_count = 0

        async def failing_build(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise BuildFailedError("Transient failure", build_output="Error")
            return mock_build_result

        workflow._build_agent = MagicMock()
        workflow._build_agent.name = "BuildAgent"
        workflow._build_agent.run = AsyncMock(side_effect=failing_build)

        workflow._qa_agent = create_mock_agent("QAAgent", mock_qa_result)
        workflow._publish_agent = create_mock_agent("PublishAgent", mock_publish_result)

        await workflow.run()

        # Should have retry notification
        warning_notifications = [n for n in hook.notifications if n["level"] == "warning"]
        assert len(warning_notifications) >= 1


# =============================================================================
# API Error Tests
# =============================================================================


class TestAPIErrors:
    """Tests for API error handling."""

    @pytest.mark.asyncio
    async def test_rate_limit_error(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test workflow handles rate limit errors."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            auto_approve=True,
            output_dir=tmp_path / "output",
            max_retries=0,
        )

        workflow._design_agent = create_mock_agent(
            "DesignAgent",
            error=AgentError("DesignAgent", "Rate limit exceeded: Try again in 60 seconds"),
        )

        result = await workflow.run()

        assert result["status"] == "failed"
        assert any("rate limit" in e.lower() for e in result["errors"])

    @pytest.mark.asyncio
    async def test_authentication_error(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test workflow handles authentication errors."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            auto_approve=True,
            output_dir=tmp_path / "output",
            max_retries=0,
        )

        workflow._design_agent = create_mock_agent(
            "DesignAgent",
            error=AgentError("DesignAgent", "Invalid API key"),
        )

        result = await workflow.run()

        assert result["status"] == "failed"
        assert any("api key" in e.lower() for e in result["errors"])

    @pytest.mark.asyncio
    async def test_network_error(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test workflow handles network errors."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            auto_approve=True,
            output_dir=tmp_path / "output",
            max_retries=0,
        )

        workflow._design_agent = create_mock_agent(
            "DesignAgent",
            error=AgentError("DesignAgent", "Connection refused"),
        )

        result = await workflow.run()

        assert result["status"] == "failed"


# =============================================================================
# Timeout Handling Tests
# =============================================================================


class TestTimeoutHandling:
    """Tests for timeout handling."""

    @pytest.mark.asyncio
    async def test_agent_timeout(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test workflow handles agent timeout."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            auto_approve=True,
            output_dir=tmp_path / "output",
            max_retries=0,
        )

        workflow._design_agent = create_mock_agent(
            "DesignAgent",
            error=TimeoutError("Agent execution timed out"),
        )

        result = await workflow.run()

        assert result["status"] == "failed"

    @pytest.mark.asyncio
    async def test_subprocess_timeout(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
    ) -> None:
        """Test workflow handles subprocess timeout."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            auto_approve=True,
            output_dir=tmp_path / "output",
            max_retries=0,
        )

        workflow._design_agent = create_mock_agent("DesignAgent", mock_design_result)
        workflow._build_agent = create_mock_agent(
            "BuildAgent",
            error=BuildFailedError(
                "Build timed out",
                build_output="Process killed after timeout",
            ),
        )

        result = await workflow.run()

        assert result["status"] == "failed"


# =============================================================================
# Error Recovery Tests
# =============================================================================


class TestErrorRecovery:
    """Tests for error recovery mechanisms."""

    @pytest.mark.asyncio
    async def test_cancel_recovers_gracefully(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test workflow cancellation recovers gracefully."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))

        from game_workflow.config import reload_settings

        reload_settings()

        hook = MockApprovalHook()
        workflow = Workflow(
            prompt=sample_prompt,
            approval_hook=hook,
            output_dir=tmp_path / "output",
        )

        await workflow.cancel()

        assert workflow.phase == WorkflowPhase.FAILED
        assert any("cancelled" in e.lower() for e in workflow.state.errors)

        # Should have cancellation notification
        cancel_notifications = [
            n for n in hook.notifications if "cancelled" in n["message"].lower()
        ]
        assert len(cancel_notifications) == 1

    @pytest.mark.asyncio
    async def test_rollback_to_checkpoint(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test rollback to checkpoint works."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            auto_approve=True,
            output_dir=tmp_path / "output",
        )

        # Create checkpoint at INIT
        checkpoint = workflow.state.create_checkpoint("Test checkpoint")

        # Move to DESIGN
        workflow.state.transition_to(WorkflowPhase.DESIGN)
        assert workflow.phase == WorkflowPhase.DESIGN

        # Rollback
        await workflow.rollback_to_checkpoint(checkpoint.checkpoint_id)

        # Should be back at INIT
        assert workflow.phase == WorkflowPhase.INIT

    @pytest.mark.asyncio
    async def test_retry_phase_resets_retry_count(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
    ) -> None:
        """Test that retry_phase resets the retry count."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            auto_approve=True,
            output_dir=tmp_path / "output",
        )

        workflow._design_agent = create_mock_agent("DesignAgent", mock_design_result)

        # Move to DESIGN
        workflow.state.transition_to(WorkflowPhase.DESIGN)

        # Set retry count manually
        workflow._retry_counts["design"] = 5

        # Retry phase
        await workflow.retry_phase(WorkflowPhase.DESIGN)

        # Retry count should be reset
        assert workflow._retry_counts.get("design", 0) == 0


# =============================================================================
# State Persistence After Error Tests
# =============================================================================


class TestStatePersistenceAfterError:
    """Tests for state persistence after errors."""

    @pytest.mark.asyncio
    async def test_state_saved_on_failure(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that state is saved when workflow fails."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import get_settings, reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            auto_approve=True,
            output_dir=tmp_path / "output",
            max_retries=0,
        )

        workflow._design_agent = create_mock_agent(
            "DesignAgent",
            error=AgentError("DesignAgent", "Test error"),
        )

        await workflow.run()

        # State should be saved
        settings = get_settings()
        state_file = settings.workflow.state_dir / f"{workflow.state.id}.json"
        assert state_file.exists()

    @pytest.mark.asyncio
    async def test_errors_recorded_in_state(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that errors are recorded in state."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            auto_approve=True,
            output_dir=tmp_path / "output",
            max_retries=0,
        )

        workflow._design_agent = create_mock_agent(
            "DesignAgent",
            error=AgentError("DesignAgent", "Specific error message"),
        )

        await workflow.run()

        # Error should be in state
        assert len(workflow.state.errors) > 0
        assert any("Specific error message" in e for e in workflow.state.errors)


# =============================================================================
# Hook Error Handling Tests
# =============================================================================


class TestHookErrors:
    """Tests for hook error handling."""

    @pytest.mark.asyncio
    async def test_hook_error_does_not_stop_workflow(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
        mock_build_result: dict[str, Any],
        mock_qa_result: dict[str, Any],
        mock_publish_result: dict[str, Any],
    ) -> None:
        """Test that hook errors don't stop workflow."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        class FailingHook:
            """Hook that always fails."""

            async def on_phase_start(
                self, _phase: str, _context: dict[str, Any] | None = None
            ) -> None:
                raise RuntimeError("Hook failed!")

            async def on_phase_complete(
                self, _phase: str, _result: dict[str, Any] | None = None
            ) -> None:
                raise RuntimeError("Hook failed!")

            async def on_error(
                self, _error: Exception, _context: dict[str, Any] | None = None
            ) -> None:
                raise RuntimeError("Hook failed!")

        workflow = Workflow(
            prompt=sample_prompt,
            auto_approve=True,
            output_dir=tmp_path / "output",
        )

        # Add failing hook
        workflow.add_hook(FailingHook())

        workflow._design_agent = create_mock_agent("DesignAgent", mock_design_result)
        workflow._build_agent = create_mock_agent("BuildAgent", mock_build_result)
        workflow._qa_agent = create_mock_agent("QAAgent", mock_qa_result)
        workflow._publish_agent = create_mock_agent("PublishAgent", mock_publish_result)

        # Workflow should still complete despite hook failures
        result = await workflow.run()

        assert result["status"] == "complete"

    @pytest.mark.asyncio
    async def test_notification_failure_does_not_stop_workflow(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
        mock_build_result: dict[str, Any],
        mock_qa_result: dict[str, Any],
        mock_publish_result: dict[str, Any],
    ) -> None:
        """Test that notification failures don't stop workflow."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        class FailingNotificationHook:
            """Approval hook with failing notifications."""

            async def request_approval(
                self,
                message: str,  # noqa: ARG002
                context: dict[str, Any] | None = None,  # noqa: ARG002
                timeout_minutes: int | None = None,  # noqa: ARG002
            ) -> bool:
                return True

            async def send_notification(
                self,
                message: str,  # noqa: ARG002
                *,
                context: dict[str, Any] | None = None,  # noqa: ARG002
                level: str = "info",  # noqa: ARG002
            ) -> bool:
                raise RuntimeError("Notification failed!")

        workflow = Workflow(
            prompt=sample_prompt,
            approval_hook=FailingNotificationHook(),
            output_dir=tmp_path / "output",
        )

        workflow._design_agent = create_mock_agent("DesignAgent", mock_design_result)
        workflow._build_agent = create_mock_agent("BuildAgent", mock_build_result)
        workflow._qa_agent = create_mock_agent("QAAgent", mock_qa_result)
        workflow._publish_agent = create_mock_agent("PublishAgent", mock_publish_result)

        # Workflow should still complete despite notification failures
        result = await workflow.run()

        assert result["status"] == "complete"
