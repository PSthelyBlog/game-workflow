"""Integration tests for the full workflow.

These tests verify that all agents work together correctly
through the workflow orchestrator.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from game_workflow.orchestrator import (
    Workflow,
    WorkflowPhase,
)
from game_workflow.orchestrator.exceptions import BuildFailedError

if TYPE_CHECKING:
    from pathlib import Path


# =============================================================================
# Mock Approval Hook
# =============================================================================


class MockApprovalHook:
    """Mock approval hook for testing."""

    def __init__(
        self,
        approve_all: bool = True,
        reject_gates: list[str] | None = None,
        raise_timeout: bool = False,
    ) -> None:
        """Initialize mock approval hook.

        Args:
            approve_all: If True, approve all gates.
            reject_gates: List of gate names to reject.
            raise_timeout: If True, raise timeout error.
        """
        self.approve_all = approve_all
        self.reject_gates = reject_gates or []
        self.raise_timeout = raise_timeout
        self.approval_requests: list[dict[str, Any]] = []
        self.notifications: list[dict[str, Any]] = []

    async def request_approval(
        self,
        message: str,
        context: dict[str, Any] | None = None,
        timeout_minutes: int | None = None,
    ) -> bool:
        """Mock approval request."""
        self.approval_requests.append(
            {
                "message": message,
                "context": context,
                "timeout_minutes": timeout_minutes,
            }
        )

        # Check if this gate should be rejected
        for gate in self.reject_gates:
            if gate in message.lower():
                return False

        return self.approve_all

    async def send_notification(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
        level: str = "info",
    ) -> bool:
        """Mock notification."""
        self.notifications.append(
            {
                "message": message,
                "context": context,
                "level": level,
            }
        )
        return True


# =============================================================================
# Mock Agent
# =============================================================================


def create_mock_agent(name: str) -> MagicMock:
    """Create a mock agent with standard interface."""
    agent = MagicMock()
    agent.name = name
    agent.run = AsyncMock()
    agent.add_artifact = MagicMock()
    return agent


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_prompt() -> str:
    """Sample game prompt for testing."""
    return "Create a simple puzzle game where players match colored blocks."


@pytest.fixture
def mock_design_result() -> dict[str, Any]:
    """Mock result from DesignAgent."""
    return {
        "status": "success",
        "concepts": [
            {
                "title": "Block Match Puzzle",
                "genre": "Puzzle",
                "tagline": "Match colors, solve puzzles!",
            }
        ],
        "selected_concept": {
            "title": "Block Match Puzzle",
            "genre": "Puzzle",
            "tagline": "Match colors, solve puzzles!",
        },
        "gdd": {
            "title": "Block Match Puzzle",
            "genre": "Puzzle",
            "concept_summary": "A colorful puzzle game.",
            "core_mechanics": [{"name": "Matching", "description": "Match blocks"}],
        },
        "tech_spec": {
            "project_name": "block-match-puzzle",
            "engine": "phaser",
        },
        "artifacts": {
            "concept": "/path/to/concept.json",
            "gdd_json": "/path/to/gdd.json",
            "gdd": "/path/to/gdd.md",
            "tech_spec": "/path/to/tech-spec.json",
        },
    }


@pytest.fixture
def mock_build_result() -> dict[str, Any]:
    """Mock result from BuildAgent."""
    return {
        "status": "success",
        "output_dir": "/path/to/game",
        "build_dir": "/path/to/game/dist",
        "claude_code_output": "Game implemented successfully.",
        "npm_build_output": "Build complete.",
    }


@pytest.fixture
def mock_qa_result() -> dict[str, Any]:
    """Mock result from QAAgent."""
    return {
        "status": "success",
        "report": {
            "game_title": "Block Match Puzzle",
            "summary": {
                "total_tests": 8,
                "passed": 7,
                "failed": 1,
                "skipped": 0,
                "errors": 0,
                "success_rate": 87.5,
                "overall_status": "needs_attention",
            },
            "test_results": [],
            "recommendations": ["Fix the failing test."],
        },
        "report_path": "/path/to/qa-report.json",
        "recommendations": ["Fix the failing test."],
    }


@pytest.fixture
def mock_publish_result() -> dict[str, Any]:
    """Mock result from PublishAgent."""
    return {
        "status": "success",
        "store_page": {
            "title": "Block Match Puzzle",
            "tagline": "Match colors, solve puzzles!",
            "description": "A fun puzzle game.",
        },
        "store_page_markdown": "# Block Match Puzzle\n\nMatch colors!",
        "artifacts": [],
        "zip_path": "/path/to/game.zip",
        "publish_output": {
            "visibility": "draft",
        },
    }


# =============================================================================
# Test Classes
# =============================================================================


class TestWorkflowIntegration:
    """Integration tests for workflow with mocked agents."""

    @pytest.mark.asyncio
    async def test_workflow_init_phase(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test workflow initialization phase."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            auto_approve=True,
            output_dir=tmp_path / "output",
        )

        assert workflow.phase == WorkflowPhase.INIT
        assert workflow.prompt == sample_prompt

        # Run just the init phase
        result = await workflow._init_phase()
        assert result["initialized"] is True
        assert result["prompt"] == sample_prompt

    @pytest.mark.asyncio
    async def test_workflow_with_auto_approve(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
        mock_build_result: dict[str, Any],
        mock_qa_result: dict[str, Any],
        mock_publish_result: dict[str, Any],
    ) -> None:
        """Test full workflow with auto-approve enabled."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            auto_approve=True,
            output_dir=tmp_path / "output",
        )

        # Create mock agents and assign to private attributes
        mock_design = create_mock_agent("DesignAgent")
        mock_design.run.return_value = mock_design_result
        workflow._design_agent = mock_design

        mock_build = create_mock_agent("BuildAgent")
        mock_build.run.return_value = mock_build_result
        workflow._build_agent = mock_build

        mock_qa = create_mock_agent("QAAgent")
        mock_qa.run.return_value = mock_qa_result
        workflow._qa_agent = mock_qa

        mock_publish = create_mock_agent("PublishAgent")
        mock_publish.run.return_value = mock_publish_result
        workflow._publish_agent = mock_publish

        # Run the full workflow
        result = await workflow.run()

        # Verify workflow completed
        assert result["status"] == "complete"
        assert workflow.phase == WorkflowPhase.COMPLETE

        # Verify all agents were called
        mock_design.run.assert_called_once()
        mock_build.run.assert_called_once()
        mock_qa.run.assert_called_once()
        mock_publish.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_workflow_with_approval_hook(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
        mock_build_result: dict[str, Any],
        mock_qa_result: dict[str, Any],
        mock_publish_result: dict[str, Any],
    ) -> None:
        """Test workflow with approval hook."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        approval_hook = MockApprovalHook(approve_all=True)

        workflow = Workflow(
            prompt=sample_prompt,
            approval_hook=approval_hook,
            output_dir=tmp_path / "output",
        )

        # Create mock agents
        mock_design = create_mock_agent("DesignAgent")
        mock_design.run.return_value = mock_design_result
        workflow._design_agent = mock_design

        mock_build = create_mock_agent("BuildAgent")
        mock_build.run.return_value = mock_build_result
        workflow._build_agent = mock_build

        mock_qa = create_mock_agent("QAAgent")
        mock_qa.run.return_value = mock_qa_result
        workflow._qa_agent = mock_qa

        mock_publish = create_mock_agent("PublishAgent")
        mock_publish.run.return_value = mock_publish_result
        workflow._publish_agent = mock_publish

        result = await workflow.run()

        # Verify approvals were requested
        assert len(approval_hook.approval_requests) == 3  # concept, build, publish
        assert result["status"] == "complete"

    @pytest.mark.asyncio
    async def test_workflow_approval_rejection(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
    ) -> None:
        """Test workflow with rejected approval."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        # Reject the concept approval
        approval_hook = MockApprovalHook(approve_all=False)

        workflow = Workflow(
            prompt=sample_prompt,
            approval_hook=approval_hook,
            output_dir=tmp_path / "output",
        )

        # Create mock design agent
        mock_design = create_mock_agent("DesignAgent")
        mock_design.run.return_value = mock_design_result
        workflow._design_agent = mock_design

        result = await workflow.run()

        # Workflow should fail due to rejected approval
        assert result["status"] == "failed"
        assert workflow.phase == WorkflowPhase.FAILED

    @pytest.mark.asyncio
    async def test_workflow_retry_on_failure(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
        mock_build_result: dict[str, Any],
    ) -> None:
        """Test workflow retries on agent failure."""
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

        # Create mock design agent
        mock_design = create_mock_agent("DesignAgent")
        mock_design.run.return_value = mock_design_result
        workflow._design_agent = mock_design

        # Track call count for build agent
        build_call_count = 0

        async def failing_build(
            *_args: Any,
            **_kwargs: Any,
        ) -> dict[str, Any]:
            nonlocal build_call_count
            build_call_count += 1
            if build_call_count < 3:
                raise BuildFailedError("Build failed", build_output="Error")
            return mock_build_result

        mock_build = create_mock_agent("BuildAgent")
        mock_build.run = AsyncMock(side_effect=failing_build)
        workflow._build_agent = mock_build

        # Create mock QA and publish agents
        mock_qa = create_mock_agent("QAAgent")
        mock_qa.run.return_value = {
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
        }
        workflow._qa_agent = mock_qa

        mock_publish = create_mock_agent("PublishAgent")
        mock_publish.run.return_value = {
            "status": "success",
            "store_page": {"title": "Test", "tagline": "Test"},
            "publish_output": {"visibility": "draft"},
        }
        workflow._publish_agent = mock_publish

        result = await workflow.run()

        # Should succeed after retries
        assert build_call_count == 3  # Initial + 2 retries
        assert result["status"] == "complete"

    @pytest.mark.asyncio
    async def test_workflow_fails_after_max_retries(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
    ) -> None:
        """Test workflow fails after exceeding max retries."""
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

        # Create mock design agent
        mock_design = create_mock_agent("DesignAgent")
        mock_design.run.return_value = mock_design_result
        workflow._design_agent = mock_design

        # Create mock build agent that always fails
        mock_build = create_mock_agent("BuildAgent")
        mock_build.run.side_effect = BuildFailedError("Build failed", build_output="Error")
        workflow._build_agent = mock_build

        result = await workflow.run()

        # Should fail after max retries exceeded
        assert result["status"] == "failed"
        assert workflow.phase == WorkflowPhase.FAILED
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_workflow_notifications(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
        mock_build_result: dict[str, Any],
        mock_qa_result: dict[str, Any],
        mock_publish_result: dict[str, Any],
    ) -> None:
        """Test workflow sends notifications."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        approval_hook = MockApprovalHook(approve_all=True)

        workflow = Workflow(
            prompt=sample_prompt,
            approval_hook=approval_hook,
            output_dir=tmp_path / "output",
        )

        # Create mock agents
        mock_design = create_mock_agent("DesignAgent")
        mock_design.run.return_value = mock_design_result
        workflow._design_agent = mock_design

        mock_build = create_mock_agent("BuildAgent")
        mock_build.run.return_value = mock_build_result
        workflow._build_agent = mock_build

        mock_qa = create_mock_agent("QAAgent")
        mock_qa.run.return_value = mock_qa_result
        workflow._qa_agent = mock_qa

        mock_publish = create_mock_agent("PublishAgent")
        mock_publish.run.return_value = mock_publish_result
        workflow._publish_agent = mock_publish

        await workflow.run()

        # Verify notifications were sent
        assert len(approval_hook.notifications) >= 2  # Start + success notifications

        # Check for start notification
        start_notifications = [n for n in approval_hook.notifications if "Starting" in n["message"]]
        assert len(start_notifications) == 1

        # Check for success notification
        success_notifications = [n for n in approval_hook.notifications if n["level"] == "success"]
        assert len(success_notifications) == 1


class TestWorkflowPhaseTransitions:
    """Tests for phase transition handling."""

    @pytest.mark.asyncio
    async def test_phase_transitions_on_success(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test phases transition correctly on success."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            auto_approve=True,
            output_dir=tmp_path / "output",
        )

        # Track phase transitions via hook
        phases_visited: list[WorkflowPhase] = []

        class PhaseTrackingHook:
            """Hook to track phase transitions."""

            async def on_phase_start(
                self,
                phase: str,
                context: dict[str, Any] | None = None,  # noqa: ARG002
            ) -> None:
                phases_visited.append(WorkflowPhase(phase))

            async def on_phase_complete(
                self, phase: str, result: dict[str, Any] | None = None
            ) -> None:
                _ = phase, result  # Unused but required by protocol

            async def on_error(
                self, error: Exception, context: dict[str, Any] | None = None
            ) -> None:
                _ = error, context  # Unused but required by protocol

        workflow.add_hook(PhaseTrackingHook())

        # Create mock agents
        mock_design = create_mock_agent("DesignAgent")
        mock_design.run.return_value = {
            "status": "success",
            "selected_concept": {"title": "Test"},
            "artifacts": {"gdd_json": str(tmp_path / "gdd.json")},
        }
        workflow._design_agent = mock_design

        mock_build = create_mock_agent("BuildAgent")
        mock_build.run.return_value = {
            "status": "success",
            "output_dir": str(tmp_path / "game"),
        }
        workflow._build_agent = mock_build

        mock_qa = create_mock_agent("QAAgent")
        mock_qa.run.return_value = {
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
        }
        workflow._qa_agent = mock_qa

        mock_publish = create_mock_agent("PublishAgent")
        mock_publish.run.return_value = {
            "status": "success",
            "store_page": {"title": "Test", "tagline": "Test"},
            "publish_output": {"visibility": "draft"},
        }
        workflow._publish_agent = mock_publish

        await workflow.run()

        # Verify all phases were visited in order
        expected_phases = [
            WorkflowPhase.INIT,
            WorkflowPhase.DESIGN,
            WorkflowPhase.BUILD,
            WorkflowPhase.QA,
            WorkflowPhase.PUBLISH,
        ]
        assert phases_visited == expected_phases
        assert workflow.phase == WorkflowPhase.COMPLETE


class TestWorkflowErrorRecovery:
    """Tests for error recovery mechanisms."""

    @pytest.mark.asyncio
    async def test_cancel_workflow(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test cancelling a workflow."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))

        from game_workflow.config import reload_settings

        reload_settings()

        approval_hook = MockApprovalHook(approve_all=True)

        workflow = Workflow(
            prompt=sample_prompt,
            approval_hook=approval_hook,
            output_dir=tmp_path / "output",
        )

        # Cancel the workflow
        await workflow.cancel()

        assert workflow.phase == WorkflowPhase.FAILED
        assert "cancelled" in workflow.state.errors[0].lower()

        # Check notification was sent
        cancel_notifications = [
            n for n in approval_hook.notifications if "cancelled" in n["message"].lower()
        ]
        assert len(cancel_notifications) == 1

    @pytest.mark.asyncio
    async def test_retry_phase(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test retrying a specific phase."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            auto_approve=True,
            output_dir=tmp_path / "output",
        )

        # Move to design phase
        workflow.state.transition_to(WorkflowPhase.DESIGN)

        # Create mock design agent
        mock_design = create_mock_agent("DesignAgent")
        mock_design.run.return_value = {
            "status": "success",
            "selected_concept": {"title": "Test", "tagline": "Test"},
            "artifacts": {},
        }
        workflow._design_agent = mock_design

        result = await workflow.retry_phase(WorkflowPhase.DESIGN)

        assert result["status"] == "success"
        mock_design.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_rollback_to_checkpoint(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test rolling back to a checkpoint."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            auto_approve=True,
            output_dir=tmp_path / "output",
        )

        # Create checkpoints at different phases
        workflow.state.create_checkpoint("Init checkpoint")

        workflow.state.transition_to(WorkflowPhase.DESIGN)
        checkpoint = workflow.state.create_checkpoint("Design checkpoint")

        workflow.state.transition_to(WorkflowPhase.BUILD)
        workflow.state.create_checkpoint("Build checkpoint")

        # Rollback to design checkpoint
        await workflow.rollback_to_checkpoint(checkpoint.checkpoint_id)

        assert workflow.phase == WorkflowPhase.DESIGN


class TestWorkflowStateManagement:
    """Tests for workflow state management."""

    @pytest.mark.asyncio
    async def test_artifacts_are_stored(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
    ) -> None:
        """Test that artifacts are stored in state."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            auto_approve=True,
            output_dir=tmp_path / "output",
        )

        # Create mock design agent
        mock_design = create_mock_agent("DesignAgent")
        mock_design.run.return_value = mock_design_result
        workflow._design_agent = mock_design

        # Run init phase
        await workflow._init_phase()

        # Transition to design and run
        workflow.state.transition_to(WorkflowPhase.DESIGN)
        await workflow._design_phase()

        # Design result is stored
        assert workflow._design_result is not None
        assert workflow._design_result["status"] == "success"

    @pytest.mark.asyncio
    async def test_approvals_are_tracked(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mock_design_result: dict[str, Any],
    ) -> None:
        """Test that approvals are tracked in state."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        approval_hook = MockApprovalHook(approve_all=True)

        workflow = Workflow(
            prompt=sample_prompt,
            approval_hook=approval_hook,
            output_dir=tmp_path / "output",
        )

        # Create mock design agent
        mock_design = create_mock_agent("DesignAgent")
        mock_design.run.return_value = mock_design_result
        workflow._design_agent = mock_design

        # Run design phase (includes approval)
        workflow.state.transition_to(WorkflowPhase.DESIGN)
        await workflow._design_phase()

        # Approval should be tracked
        assert "concept" in workflow.state.approvals
        assert workflow.state.approvals["concept"] is True


class TestAgentProperties:
    """Tests for lazy-loaded agent properties."""

    def test_design_agent_property(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test design agent is lazily loaded."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            output_dir=tmp_path / "output",
        )

        # Agent is not created yet
        assert workflow._design_agent is None

        # Access property creates the agent
        agent = workflow.design_agent
        assert agent is not None
        assert workflow._design_agent is not None

        # Second access returns same instance
        assert workflow.design_agent is agent

    def test_build_agent_property(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test build agent is lazily loaded."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            output_dir=tmp_path / "output",
        )

        agent = workflow.build_agent
        assert agent is not None
        assert agent.name == "BuildAgent"

    def test_qa_agent_property(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test QA agent is lazily loaded."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            output_dir=tmp_path / "output",
        )

        agent = workflow.qa_agent
        assert agent is not None
        assert agent.name == "QAAgent"

    def test_publish_agent_property(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test publish agent is lazily loaded."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            output_dir=tmp_path / "output",
        )

        agent = workflow.publish_agent
        assert agent is not None
        assert agent.name == "PublishAgent"


class TestSetApprovalHook:
    """Tests for setting approval hook."""

    def test_set_approval_hook(
        self,
        sample_prompt: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test setting approval hook after creation."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt=sample_prompt,
            output_dir=tmp_path / "output",
        )

        # No hook initially
        assert workflow._approval_hook is None

        # Set hook
        hook = MockApprovalHook()
        workflow.set_approval_hook(hook)

        assert workflow._approval_hook is hook
