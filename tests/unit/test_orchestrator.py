"""Tests for the orchestrator module."""

from pathlib import Path

import pytest

from game_workflow.orchestrator import (
    InvalidTransitionError,
    StateNotFoundError,
    WorkflowPhase,
    WorkflowState,
)
from game_workflow.orchestrator.workflow import Workflow


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

    def test_valid_transitions(self) -> None:
        """Test valid state transitions."""
        # INIT can transition to DESIGN or FAILED
        assert WorkflowPhase.INIT.can_transition_to(WorkflowPhase.DESIGN)
        assert WorkflowPhase.INIT.can_transition_to(WorkflowPhase.FAILED)
        assert not WorkflowPhase.INIT.can_transition_to(WorkflowPhase.BUILD)

        # DESIGN can transition to BUILD or FAILED
        assert WorkflowPhase.DESIGN.can_transition_to(WorkflowPhase.BUILD)
        assert WorkflowPhase.DESIGN.can_transition_to(WorkflowPhase.FAILED)
        assert not WorkflowPhase.DESIGN.can_transition_to(WorkflowPhase.PUBLISH)

        # QA can go back to BUILD or forward to PUBLISH
        assert WorkflowPhase.QA.can_transition_to(WorkflowPhase.BUILD)
        assert WorkflowPhase.QA.can_transition_to(WorkflowPhase.PUBLISH)
        assert WorkflowPhase.QA.can_transition_to(WorkflowPhase.FAILED)

        # COMPLETE is terminal
        assert not WorkflowPhase.COMPLETE.can_transition_to(WorkflowPhase.INIT)
        assert not WorkflowPhase.COMPLETE.can_transition_to(WorkflowPhase.FAILED)

        # FAILED can restart
        assert WorkflowPhase.FAILED.can_transition_to(WorkflowPhase.INIT)

    def test_get_next_phase(self) -> None:
        """Test getting the next phase in progression."""
        assert WorkflowPhase.INIT.get_next_phase() == WorkflowPhase.DESIGN
        assert WorkflowPhase.DESIGN.get_next_phase() == WorkflowPhase.BUILD
        assert WorkflowPhase.BUILD.get_next_phase() == WorkflowPhase.QA
        assert WorkflowPhase.QA.get_next_phase() == WorkflowPhase.PUBLISH
        assert WorkflowPhase.PUBLISH.get_next_phase() == WorkflowPhase.COMPLETE
        assert WorkflowPhase.COMPLETE.get_next_phase() is None
        assert WorkflowPhase.FAILED.get_next_phase() is None

    def test_is_terminal(self) -> None:
        """Test terminal phase detection."""
        assert WorkflowPhase.COMPLETE.is_terminal
        assert WorkflowPhase.FAILED.is_terminal
        assert not WorkflowPhase.INIT.is_terminal
        assert not WorkflowPhase.BUILD.is_terminal


class TestWorkflowState:
    """Tests for the WorkflowState class."""

    def test_default_state(self) -> None:
        """Test default state values."""
        state = WorkflowState()
        assert state.phase == WorkflowPhase.INIT
        assert state.engine == "phaser"
        assert state.artifacts == {}
        assert state.approvals == {}
        assert state.errors == []
        assert state.checkpoints == []

    def test_transition_to_valid(self) -> None:
        """Test valid state transition."""
        state = WorkflowState()
        state.transition_to(WorkflowPhase.DESIGN)
        assert state.phase == WorkflowPhase.DESIGN

    def test_transition_to_invalid(self) -> None:
        """Test invalid state transition raises error."""
        state = WorkflowState()
        with pytest.raises(InvalidTransitionError):
            state.transition_to(WorkflowPhase.BUILD)  # Can't skip DESIGN

    def test_add_artifact(self) -> None:
        """Test adding an artifact."""
        state = WorkflowState()
        state.add_artifact("gdd", "/path/to/gdd.md")
        assert "gdd" in state.artifacts
        assert state.artifacts["gdd"] == "/path/to/gdd.md"

    def test_add_error(self) -> None:
        """Test adding an error."""
        state = WorkflowState()
        state.add_error("Something went wrong")
        assert len(state.errors) == 1
        assert "Something went wrong" in state.errors[0]

    def test_set_approval(self) -> None:
        """Test setting an approval."""
        state = WorkflowState()
        state.set_approval("concept", True)
        assert state.approvals["concept"] is True

    def test_create_checkpoint(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test creating a checkpoint."""
        # Use temp directory for state
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))

        # Clear the settings cache
        from game_workflow.config import reload_settings

        reload_settings()

        state = WorkflowState()
        state.save()  # Save first to create the file

        checkpoint = state.create_checkpoint("Test checkpoint")
        assert checkpoint.phase == WorkflowPhase.INIT
        assert checkpoint.description == "Test checkpoint"
        assert len(state.checkpoints) == 1

    def test_save_and_load(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test saving and loading state."""
        # Use temp directory for state
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))

        # Clear the settings cache
        from game_workflow.config import reload_settings

        reload_settings()

        # Create and save state
        state = WorkflowState(prompt="Test prompt", engine="godot")
        state.add_artifact("test", "/test/path")
        state_file = state.save()
        assert state_file.exists()

        # Load state
        loaded = WorkflowState.load(state.id)
        assert loaded.id == state.id
        assert loaded.prompt == "Test prompt"
        assert loaded.engine == "godot"
        assert loaded.artifacts["test"] == "/test/path"

    def test_load_not_found(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test loading non-existent state raises error."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))

        from game_workflow.config import reload_settings

        reload_settings()

        with pytest.raises(StateNotFoundError):
            WorkflowState.load("nonexistent")

    def test_get_latest(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test getting the latest state."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))

        from game_workflow.config import reload_settings

        reload_settings()

        # No states yet
        assert WorkflowState.get_latest() is None

        # Create a state
        state = WorkflowState(prompt="Test")
        state.save()

        latest = WorkflowState.get_latest()
        assert latest is not None
        assert latest.id == state.id

    def test_list_all(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test listing all states."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))

        from game_workflow.config import reload_settings

        reload_settings()

        # Create multiple states with unique IDs
        state1 = WorkflowState(id="state_001", prompt="Test 1")
        state1.save()

        state2 = WorkflowState(id="state_002", prompt="Test 2")
        state2.save()

        states = WorkflowState.list_all()
        assert len(states) == 2

    def test_delete(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test deleting a state."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))

        from game_workflow.config import reload_settings

        reload_settings()

        state = WorkflowState(prompt="Test")
        state.save()

        assert WorkflowState.delete(state.id)
        assert not WorkflowState.delete(state.id)  # Already deleted

    def test_cleanup_old(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test cleaning up old states."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))

        from game_workflow.config import reload_settings

        reload_settings()

        # Create multiple states with unique IDs
        for i in range(5):
            state = WorkflowState(id=f"state_{i:03d}", prompt=f"Test {i}")
            state.save()

        # Keep only 2
        deleted = WorkflowState.cleanup_old(keep_count=2)
        assert deleted == 3
        assert len(WorkflowState.list_all()) == 2


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

    def test_init_with_existing_state(self, sample_prompt: str) -> None:
        """Test workflow initialization with existing state."""
        state = WorkflowState(prompt=sample_prompt, engine="godot")
        state.transition_to(WorkflowPhase.DESIGN)

        workflow = Workflow(prompt=sample_prompt, state=state)
        assert workflow.phase == WorkflowPhase.DESIGN

    def test_resume(
        self, sample_prompt: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test resuming a workflow."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))

        from game_workflow.config import reload_settings

        reload_settings()

        # Create and save a workflow
        workflow1 = Workflow(sample_prompt)
        workflow1.state.save()

        # Resume it
        workflow2 = Workflow.resume(workflow1.state.id)
        assert workflow2.state.id == workflow1.state.id
        assert workflow2.prompt == sample_prompt

    def test_resume_latest(
        self, sample_prompt: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test resuming the latest workflow."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))

        from game_workflow.config import reload_settings

        reload_settings()

        # No workflows yet
        assert Workflow.resume_latest() is None

        # Create a workflow
        workflow = Workflow(sample_prompt)
        workflow.state.save()

        # Resume latest
        resumed = Workflow.resume_latest()
        assert resumed is not None
        assert resumed.state.id == workflow.state.id

    def test_add_hook(self, sample_prompt: str) -> None:
        """Test adding a hook to the workflow."""
        workflow = Workflow(sample_prompt)

        # Default hooks are already added
        initial_hook_count = len(workflow._hooks)

        # Add a custom hook
        class DummyHook:
            async def on_phase_start(self, phase: str, context: dict | None = None) -> None:
                pass

            async def on_phase_complete(self, phase: str, result: dict | None = None) -> None:
                pass

            async def on_error(self, error: Exception, context: dict | None = None) -> None:
                pass

        workflow.add_hook(DummyHook())
        assert len(workflow._hooks) == initial_hook_count + 1
