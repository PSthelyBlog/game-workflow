"""Integration tests for approval flows.

These tests verify all approval paths in the workflow:
- Approval granted
- Approval rejected
- Approval timeout
- Selective approval gates
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from game_workflow.orchestrator import Workflow, WorkflowPhase

if TYPE_CHECKING:
    from pathlib import Path


# =============================================================================
# Approval Hook Implementations
# =============================================================================


class AlwaysApproveHook:
    """Hook that always approves requests."""

    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []
        self.notifications: list[dict[str, Any]] = []

    async def request_approval(
        self,
        message: str,
        context: dict[str, Any] | None = None,
        timeout_minutes: int | None = None,
    ) -> bool:
        self.requests.append(
            {
                "message": message,
                "context": context,
                "timeout_minutes": timeout_minutes,
            }
        )
        return True

    async def send_notification(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
        level: str = "info",
    ) -> bool:
        self.notifications.append(
            {
                "message": message,
                "context": context,
                "level": level,
            }
        )
        return True


class AlwaysRejectHook:
    """Hook that always rejects requests."""

    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []
        self.notifications: list[dict[str, Any]] = []

    async def request_approval(
        self,
        message: str,
        context: dict[str, Any] | None = None,
        timeout_minutes: int | None = None,
    ) -> bool:
        self.requests.append(
            {
                "message": message,
                "context": context,
                "timeout_minutes": timeout_minutes,
            }
        )
        return False

    async def send_notification(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
        level: str = "info",
    ) -> bool:
        self.notifications.append(
            {
                "message": message,
                "context": context,
                "level": level,
            }
        )
        return True


class SelectiveApprovalHook:
    """Hook that approves or rejects based on gate name."""

    def __init__(
        self,
        approve_gates: list[str] | None = None,
        reject_gates: list[str] | None = None,
    ) -> None:
        self.approve_gates = approve_gates or []
        self.reject_gates = reject_gates or []
        self.requests: list[dict[str, Any]] = []
        self.notifications: list[dict[str, Any]] = []

    async def request_approval(
        self,
        message: str,
        context: dict[str, Any] | None = None,
        timeout_minutes: int | None = None,
    ) -> bool:
        self.requests.append(
            {
                "message": message,
                "context": context,
                "timeout_minutes": timeout_minutes,
            }
        )

        # Check against reject gates first
        for gate in self.reject_gates:
            if gate.lower() in message.lower():
                return False

        # Check against approve gates
        for gate in self.approve_gates:
            if gate.lower() in message.lower():
                return True

        # Default to approve if not explicitly matched
        return True

    async def send_notification(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
        level: str = "info",
    ) -> bool:
        self.notifications.append(
            {
                "message": message,
                "context": context,
                "level": level,
            }
        )
        return True


class TimeoutApprovalHook:
    """Hook that simulates timeout by raising an error."""

    def __init__(self, timeout_after: int = 0) -> None:
        self.timeout_after = timeout_after
        self.request_count = 0
        self.requests: list[dict[str, Any]] = []
        self.notifications: list[dict[str, Any]] = []

    async def request_approval(
        self,
        message: str,
        context: dict[str, Any] | None = None,
        timeout_minutes: int | None = None,
    ) -> bool:
        self.requests.append(
            {
                "message": message,
                "context": context,
                "timeout_minutes": timeout_minutes,
            }
        )
        self.request_count += 1

        if self.request_count > self.timeout_after:
            # Simulate timeout by raising TimeoutError
            raise TimeoutError("Approval request timed out")

        return True

    async def send_notification(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
        level: str = "info",
    ) -> bool:
        self.notifications.append(
            {
                "message": message,
                "context": context,
                "level": level,
            }
        )
        return True


class DelayedApprovalHook:
    """Hook that delays approval responses."""

    def __init__(self, delay_seconds: float = 0.1) -> None:
        self.delay_seconds = delay_seconds
        self.requests: list[dict[str, Any]] = []
        self.notifications: list[dict[str, Any]] = []

    async def request_approval(
        self,
        message: str,
        context: dict[str, Any] | None = None,
        timeout_minutes: int | None = None,
    ) -> bool:
        self.requests.append(
            {
                "message": message,
                "context": context,
                "timeout_minutes": timeout_minutes,
            }
        )
        await asyncio.sleep(self.delay_seconds)
        return True

    async def send_notification(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
        level: str = "info",
    ) -> bool:
        self.notifications.append(
            {
                "message": message,
                "context": context,
                "level": level,
            }
        )
        return True


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_prompt() -> str:
    """Sample game prompt for testing."""
    return "Create a simple puzzle game where players match colored blocks."


def create_mock_agent(name: str, result: dict[str, Any]) -> MagicMock:
    """Create a mock agent with standard interface."""
    agent = MagicMock()
    agent.name = name
    agent.run = AsyncMock(return_value=result)
    return agent


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
# Approval Granted Tests
# =============================================================================


class TestApprovalGranted:
    """Tests for successful approval flows."""

    @pytest.mark.asyncio
    async def test_all_approvals_granted(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
        mock_build_result: dict[str, Any],
        mock_qa_result: dict[str, Any],
        mock_publish_result: dict[str, Any],
    ) -> None:
        """Test workflow completes when all approvals are granted."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        hook = AlwaysApproveHook()
        workflow = Workflow(
            prompt=sample_prompt,
            approval_hook=hook,
            output_dir=tmp_path / "output",
        )

        # Mock all agents
        workflow._design_agent = create_mock_agent("DesignAgent", mock_design_result)
        workflow._build_agent = create_mock_agent("BuildAgent", mock_build_result)
        workflow._qa_agent = create_mock_agent("QAAgent", mock_qa_result)
        workflow._publish_agent = create_mock_agent("PublishAgent", mock_publish_result)

        result = await workflow.run()

        # Should complete successfully
        assert result["status"] == "complete"
        assert workflow.phase == WorkflowPhase.COMPLETE

        # Should have 3 approval requests (concept, build, publish)
        assert len(hook.requests) == 3

    @pytest.mark.asyncio
    async def test_approval_context_is_passed(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
    ) -> None:
        """Test that approval requests include context."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        hook = AlwaysApproveHook()
        workflow = Workflow(
            prompt=sample_prompt,
            approval_hook=hook,
            output_dir=tmp_path / "output",
        )

        workflow._design_agent = create_mock_agent("DesignAgent", mock_design_result)

        # Run just through design phase
        workflow.state.transition_to(WorkflowPhase.DESIGN)
        await workflow._design_phase()

        # Check approval request had context
        assert len(hook.requests) == 1
        request = hook.requests[0]
        assert request["context"] is not None
        assert "title" in request["context"]
        assert request["context"]["title"] == "Block Match Puzzle"

    @pytest.mark.asyncio
    async def test_approvals_tracked_in_state(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
        mock_build_result: dict[str, Any],
        mock_qa_result: dict[str, Any],
        mock_publish_result: dict[str, Any],
    ) -> None:
        """Test that approvals are tracked in workflow state."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        hook = AlwaysApproveHook()
        workflow = Workflow(
            prompt=sample_prompt,
            approval_hook=hook,
            output_dir=tmp_path / "output",
        )

        workflow._design_agent = create_mock_agent("DesignAgent", mock_design_result)
        workflow._build_agent = create_mock_agent("BuildAgent", mock_build_result)
        workflow._qa_agent = create_mock_agent("QAAgent", mock_qa_result)
        workflow._publish_agent = create_mock_agent("PublishAgent", mock_publish_result)

        await workflow.run()

        # Check approvals are tracked
        assert "concept" in workflow.state.approvals
        assert workflow.state.approvals["concept"] is True
        assert "build" in workflow.state.approvals
        assert workflow.state.approvals["build"] is True
        assert "publish" in workflow.state.approvals
        assert workflow.state.approvals["publish"] is True


# =============================================================================
# Approval Rejected Tests
# =============================================================================


class TestApprovalRejected:
    """Tests for rejected approval flows."""

    @pytest.mark.asyncio
    async def test_concept_rejection_stops_workflow(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
    ) -> None:
        """Test workflow stops when concept is rejected."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        hook = AlwaysRejectHook()
        workflow = Workflow(
            prompt=sample_prompt,
            approval_hook=hook,
            output_dir=tmp_path / "output",
        )

        workflow._design_agent = create_mock_agent("DesignAgent", mock_design_result)

        result = await workflow.run()

        # Should fail
        assert result["status"] == "failed"
        assert workflow.phase == WorkflowPhase.FAILED

        # Only one approval request (concept)
        assert len(hook.requests) == 1

    @pytest.mark.asyncio
    async def test_build_rejection_stops_workflow(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
        mock_build_result: dict[str, Any],
        mock_qa_result: dict[str, Any],
    ) -> None:
        """Test workflow stops when build is rejected."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        # Approve concept, reject build
        hook = SelectiveApprovalHook(
            approve_gates=["concept"],
            reject_gates=["build"],
        )
        workflow = Workflow(
            prompt=sample_prompt,
            approval_hook=hook,
            output_dir=tmp_path / "output",
        )

        workflow._design_agent = create_mock_agent("DesignAgent", mock_design_result)
        workflow._build_agent = create_mock_agent("BuildAgent", mock_build_result)
        workflow._qa_agent = create_mock_agent("QAAgent", mock_qa_result)

        result = await workflow.run()

        # Should fail
        assert result["status"] == "failed"

        # Two approval requests (concept approved, build rejected)
        assert len(hook.requests) == 2

    @pytest.mark.asyncio
    async def test_publish_rejection_stops_workflow(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
        mock_build_result: dict[str, Any],
        mock_qa_result: dict[str, Any],
        mock_publish_result: dict[str, Any],
    ) -> None:
        """Test workflow stops when publish is rejected."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        # Approve concept and build, reject publish
        hook = SelectiveApprovalHook(
            approve_gates=["concept", "build"],
            reject_gates=["publish"],
        )
        workflow = Workflow(
            prompt=sample_prompt,
            approval_hook=hook,
            output_dir=tmp_path / "output",
        )

        workflow._design_agent = create_mock_agent("DesignAgent", mock_design_result)
        workflow._build_agent = create_mock_agent("BuildAgent", mock_build_result)
        workflow._qa_agent = create_mock_agent("QAAgent", mock_qa_result)
        workflow._publish_agent = create_mock_agent("PublishAgent", mock_publish_result)

        result = await workflow.run()

        # Should fail
        assert result["status"] == "failed"

        # All three approval requests made
        assert len(hook.requests) == 3

    @pytest.mark.asyncio
    async def test_rejection_tracked_in_state(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
    ) -> None:
        """Test that rejections are tracked in workflow state."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        hook = AlwaysRejectHook()
        workflow = Workflow(
            prompt=sample_prompt,
            approval_hook=hook,
            output_dir=tmp_path / "output",
        )

        workflow._design_agent = create_mock_agent("DesignAgent", mock_design_result)

        await workflow.run()

        # Rejection should be tracked
        assert "concept" in workflow.state.approvals
        assert workflow.state.approvals["concept"] is False


# =============================================================================
# Approval Timeout Tests
# =============================================================================


class TestApprovalTimeout:
    """Tests for approval timeout handling."""

    @pytest.mark.asyncio
    async def test_timeout_after_first_approval(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
        mock_build_result: dict[str, Any],
        mock_qa_result: dict[str, Any],
    ) -> None:
        """Test workflow handles timeout after first approval."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        # Timeout after first request
        hook = TimeoutApprovalHook(timeout_after=1)
        workflow = Workflow(
            prompt=sample_prompt,
            approval_hook=hook,
            output_dir=tmp_path / "output",
        )

        workflow._design_agent = create_mock_agent("DesignAgent", mock_design_result)
        workflow._build_agent = create_mock_agent("BuildAgent", mock_build_result)
        workflow._qa_agent = create_mock_agent("QAAgent", mock_qa_result)

        result = await workflow.run()

        # Should fail due to timeout
        assert result["status"] == "failed"

        # First request approved, second timed out
        assert len(hook.requests) == 2

    @pytest.mark.asyncio
    async def test_delayed_approval_succeeds(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
        mock_build_result: dict[str, Any],
        mock_qa_result: dict[str, Any],
        mock_publish_result: dict[str, Any],
    ) -> None:
        """Test that delayed approvals still succeed."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        # Small delay
        hook = DelayedApprovalHook(delay_seconds=0.01)
        workflow = Workflow(
            prompt=sample_prompt,
            approval_hook=hook,
            output_dir=tmp_path / "output",
        )

        workflow._design_agent = create_mock_agent("DesignAgent", mock_design_result)
        workflow._build_agent = create_mock_agent("BuildAgent", mock_build_result)
        workflow._qa_agent = create_mock_agent("QAAgent", mock_qa_result)
        workflow._publish_agent = create_mock_agent("PublishAgent", mock_publish_result)

        result = await workflow.run()

        # Should complete despite delays
        assert result["status"] == "complete"
        assert len(hook.requests) == 3


# =============================================================================
# Selective Approval Tests
# =============================================================================


class TestSelectiveApproval:
    """Tests for selective approval gate behavior."""

    @pytest.mark.asyncio
    async def test_approve_specific_gates(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
        mock_build_result: dict[str, Any],
        mock_qa_result: dict[str, Any],
        mock_publish_result: dict[str, Any],
    ) -> None:
        """Test approving specific gates only."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        # Only explicitly approve these gates
        hook = SelectiveApprovalHook(
            approve_gates=["concept", "build", "publish"],
        )
        workflow = Workflow(
            prompt=sample_prompt,
            approval_hook=hook,
            output_dir=tmp_path / "output",
        )

        workflow._design_agent = create_mock_agent("DesignAgent", mock_design_result)
        workflow._build_agent = create_mock_agent("BuildAgent", mock_build_result)
        workflow._qa_agent = create_mock_agent("QAAgent", mock_qa_result)
        workflow._publish_agent = create_mock_agent("PublishAgent", mock_publish_result)

        result = await workflow.run()

        assert result["status"] == "complete"

    @pytest.mark.asyncio
    async def test_reject_specific_gates(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
    ) -> None:
        """Test rejecting specific gates only."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        # Reject concept specifically
        hook = SelectiveApprovalHook(
            reject_gates=["concept"],
        )
        workflow = Workflow(
            prompt=sample_prompt,
            approval_hook=hook,
            output_dir=tmp_path / "output",
        )

        workflow._design_agent = create_mock_agent("DesignAgent", mock_design_result)

        result = await workflow.run()

        assert result["status"] == "failed"
        assert len(hook.requests) == 1


# =============================================================================
# Auto-Approval Tests
# =============================================================================


class TestAutoApproval:
    """Tests for auto-approval mode."""

    @pytest.mark.asyncio
    async def test_auto_approve_skips_hook(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
        mock_build_result: dict[str, Any],
        mock_qa_result: dict[str, Any],
        mock_publish_result: dict[str, Any],
    ) -> None:
        """Test auto-approve mode skips approval hook."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        # Hook that would reject, but shouldn't be called
        hook = AlwaysRejectHook()
        workflow = Workflow(
            prompt=sample_prompt,
            approval_hook=hook,
            auto_approve=True,
            output_dir=tmp_path / "output",
        )

        workflow._design_agent = create_mock_agent("DesignAgent", mock_design_result)
        workflow._build_agent = create_mock_agent("BuildAgent", mock_build_result)
        workflow._qa_agent = create_mock_agent("QAAgent", mock_qa_result)
        workflow._publish_agent = create_mock_agent("PublishAgent", mock_publish_result)

        result = await workflow.run()

        # Should complete because auto-approve bypasses hook
        assert result["status"] == "complete"

        # Hook should not have been called for approvals
        assert len(hook.requests) == 0

    @pytest.mark.asyncio
    async def test_auto_approve_tracks_in_state(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
        mock_build_result: dict[str, Any],
        mock_qa_result: dict[str, Any],
        mock_publish_result: dict[str, Any],
    ) -> None:
        """Test auto-approved gates are tracked in state."""
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
        workflow._build_agent = create_mock_agent("BuildAgent", mock_build_result)
        workflow._qa_agent = create_mock_agent("QAAgent", mock_qa_result)
        workflow._publish_agent = create_mock_agent("PublishAgent", mock_publish_result)

        await workflow.run()

        # All gates should be tracked as approved
        assert workflow.state.approvals.get("concept") is True
        assert workflow.state.approvals.get("build") is True
        assert workflow.state.approvals.get("publish") is True


# =============================================================================
# No Hook Configured Tests
# =============================================================================


class TestNoApprovalHook:
    """Tests for behavior when no approval hook is configured."""

    @pytest.mark.asyncio
    async def test_no_hook_auto_approves(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
        mock_build_result: dict[str, Any],
        mock_qa_result: dict[str, Any],
        mock_publish_result: dict[str, Any],
    ) -> None:
        """Test workflow auto-approves when no hook is configured."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            approval_hook=None,  # No hook
            auto_approve=False,  # Not auto-approve mode
            output_dir=tmp_path / "output",
        )

        workflow._design_agent = create_mock_agent("DesignAgent", mock_design_result)
        workflow._build_agent = create_mock_agent("BuildAgent", mock_build_result)
        workflow._qa_agent = create_mock_agent("QAAgent", mock_qa_result)
        workflow._publish_agent = create_mock_agent("PublishAgent", mock_publish_result)

        result = await workflow.run()

        # Should complete (auto-approves when no hook)
        assert result["status"] == "complete"


# =============================================================================
# Notification Tests
# =============================================================================


class TestApprovalNotifications:
    """Tests for notifications during approval flow."""

    @pytest.mark.asyncio
    async def test_notifications_sent_on_approval(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
        mock_build_result: dict[str, Any],
        mock_qa_result: dict[str, Any],
        mock_publish_result: dict[str, Any],
    ) -> None:
        """Test notifications are sent throughout workflow."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        hook = AlwaysApproveHook()
        workflow = Workflow(
            prompt=sample_prompt,
            approval_hook=hook,
            output_dir=tmp_path / "output",
        )

        workflow._design_agent = create_mock_agent("DesignAgent", mock_design_result)
        workflow._build_agent = create_mock_agent("BuildAgent", mock_build_result)
        workflow._qa_agent = create_mock_agent("QAAgent", mock_qa_result)
        workflow._publish_agent = create_mock_agent("PublishAgent", mock_publish_result)

        await workflow.run()

        # Should have notifications
        assert len(hook.notifications) >= 2

        # Check for start and success notifications
        levels = [n["level"] for n in hook.notifications]
        assert "info" in levels
        assert "success" in levels

    @pytest.mark.asyncio
    async def test_error_notification_on_rejection(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
    ) -> None:
        """Test error notification is sent on rejection."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        hook = AlwaysRejectHook()
        workflow = Workflow(
            prompt=sample_prompt,
            approval_hook=hook,
            output_dir=tmp_path / "output",
        )

        workflow._design_agent = create_mock_agent("DesignAgent", mock_design_result)

        await workflow.run()

        # Should have error notification
        error_notifications = [n for n in hook.notifications if n["level"] == "error"]
        assert len(error_notifications) >= 1
