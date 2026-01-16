"""Tests for the orchestrator module."""

from game_workflow.orchestrator import WorkflowState
from game_workflow.orchestrator.workflow import Workflow, WorkflowPhase


class TestWorkflowPhase:
    """Tests for WorkflowPhase enum."""

    def test_phases_exist(self) -> None:
        """Verify all expected phases are defined."""
        assert WorkflowPhase.INIT == "init"
        assert WorkflowPhase.DESIGN == "design"
        assert WorkflowPhase.BUILD == "build"
        assert WorkflowPhase.QA == "qa"
        assert WorkflowPhase.PUBLISH == "publish"
        assert WorkflowPhase.COMPLETE == "complete"
        assert WorkflowPhase.FAILED == "failed"


class TestWorkflow:
    """Tests for the Workflow class."""

    def test_init(self, sample_prompt: str) -> None:
        """Test workflow initialization."""
        workflow = Workflow(sample_prompt)
        assert workflow.prompt == sample_prompt
        assert workflow.engine == "phaser"
        assert workflow.phase == WorkflowPhase.INIT

    def test_init_with_engine(self, sample_prompt: str) -> None:
        """Test workflow initialization with custom engine."""
        workflow = Workflow(sample_prompt, engine="godot")
        assert workflow.engine == "godot"


class TestWorkflowState:
    """Tests for the WorkflowState class."""

    def test_default_state(self) -> None:
        """Test default state values."""
        state = WorkflowState()
        assert state.phase == "init"
        assert state.engine == "phaser"
        assert state.artifacts == {}
        assert state.approvals == {}
        assert state.errors == []
