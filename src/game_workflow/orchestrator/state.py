"""State persistence for workflows.

This module handles saving and loading workflow state to enable
resumption after interruptions.
"""

from __future__ import annotations

import contextlib
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from pathlib import Path

from game_workflow.config import get_settings
from game_workflow.orchestrator.exceptions import InvalidTransitionError, StateNotFoundError


class WorkflowPhase(str, Enum):
    """Phases of the game creation workflow.

    The workflow progresses through these phases in order:
    INIT -> DESIGN -> BUILD -> QA -> PUBLISH -> COMPLETE

    FAILED can be reached from any phase if an error occurs.
    """

    INIT = "init"
    DESIGN = "design"
    BUILD = "build"
    QA = "qa"
    PUBLISH = "publish"
    COMPLETE = "complete"
    FAILED = "failed"

    @classmethod
    def get_valid_transitions(cls) -> dict[WorkflowPhase, set[WorkflowPhase]]:
        """Get the valid state transitions.

        Returns:
            Dictionary mapping each phase to its valid successor phases.
        """
        return {
            cls.INIT: {cls.DESIGN, cls.FAILED},
            cls.DESIGN: {cls.BUILD, cls.FAILED},
            cls.BUILD: {cls.QA, cls.FAILED},
            cls.QA: {cls.BUILD, cls.PUBLISH, cls.FAILED},  # Can go back to BUILD if QA fails
            cls.PUBLISH: {cls.COMPLETE, cls.FAILED},
            cls.COMPLETE: set(),  # Terminal state
            cls.FAILED: {cls.INIT},  # Can restart from INIT
        }

    def can_transition_to(self, target: WorkflowPhase) -> bool:
        """Check if transition to target phase is valid.

        Args:
            target: The target phase.

        Returns:
            True if the transition is valid.
        """
        valid_targets = self.get_valid_transitions().get(self, set())
        return target in valid_targets

    def get_next_phase(self) -> WorkflowPhase | None:
        """Get the next phase in the normal workflow progression.

        Returns:
            The next phase, or None if this is a terminal state.
        """
        progression = {
            WorkflowPhase.INIT: WorkflowPhase.DESIGN,
            WorkflowPhase.DESIGN: WorkflowPhase.BUILD,
            WorkflowPhase.BUILD: WorkflowPhase.QA,
            WorkflowPhase.QA: WorkflowPhase.PUBLISH,
            WorkflowPhase.PUBLISH: WorkflowPhase.COMPLETE,
        }
        return progression.get(self)

    @property
    def is_terminal(self) -> bool:
        """Check if this is a terminal phase (COMPLETE or FAILED)."""
        return self in (WorkflowPhase.COMPLETE, WorkflowPhase.FAILED)


class CheckpointData(BaseModel):
    """Data for a workflow checkpoint."""

    checkpoint_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: datetime = Field(default_factory=datetime.now)
    phase: WorkflowPhase
    description: str = ""


class WorkflowState(BaseModel):
    """Persistent state for a workflow.

    This model represents the complete state of a workflow run,
    including the current phase, generated artifacts, approvals,
    and checkpoint history.
    """

    # Identification
    id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Workflow configuration
    prompt: str = ""
    engine: str = "phaser"

    # Current state
    phase: WorkflowPhase = WorkflowPhase.INIT

    # Artifacts and results
    artifacts: dict[str, str] = Field(default_factory=dict)  # name -> path as string
    approvals: dict[str, bool] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Checkpoint history
    checkpoints: list[CheckpointData] = Field(default_factory=list)

    def transition_to(self, target: WorkflowPhase) -> None:
        """Transition to a new phase.

        Args:
            target: The target phase.

        Raises:
            InvalidTransitionError: If the transition is not valid.
        """
        if not self.phase.can_transition_to(target):
            raise InvalidTransitionError(self.phase, target)

        self.phase = target
        self.updated_at = datetime.now()

    def create_checkpoint(self, description: str = "") -> CheckpointData:
        """Create a checkpoint at the current state.

        Args:
            description: Optional description of the checkpoint.

        Returns:
            The created checkpoint data.
        """
        checkpoint = CheckpointData(
            phase=self.phase,
            description=description,
        )
        self.checkpoints.append(checkpoint)
        self.save()
        return checkpoint

    def add_artifact(self, name: str, path: Path | str) -> None:
        """Add an artifact to the state.

        Args:
            name: The artifact name (e.g., "gdd", "concept").
            path: The path to the artifact.
        """
        self.artifacts[name] = str(path)
        self.updated_at = datetime.now()

    def add_error(self, error: str | Exception) -> None:
        """Record an error.

        Args:
            error: The error message or exception.
        """
        error_msg = str(error)
        self.errors.append(error_msg)
        self.updated_at = datetime.now()

    def set_approval(self, gate: str, approved: bool) -> None:
        """Record an approval decision.

        Args:
            gate: The approval gate name.
            approved: Whether approval was granted.
        """
        self.approvals[gate] = approved
        self.updated_at = datetime.now()

    def save(self) -> Path:
        """Save state to disk.

        Returns:
            Path to the saved state file.
        """
        settings = get_settings()
        state_dir = settings.workflow.state_dir
        state_dir.mkdir(parents=True, exist_ok=True)

        self.updated_at = datetime.now()
        state_file = state_dir / f"{self.id}.json"

        with state_file.open("w") as f:
            json.dump(self.model_dump(mode="json"), f, indent=2, default=str)

        return state_file

    @classmethod
    def load(cls, state_id: str) -> WorkflowState:
        """Load state from disk.

        Args:
            state_id: The ID of the state to load.

        Returns:
            The loaded workflow state.

        Raises:
            StateNotFoundError: If the state file doesn't exist.
        """
        settings = get_settings()
        state_file = settings.workflow.state_dir / f"{state_id}.json"

        if not state_file.exists():
            raise StateNotFoundError(state_id)

        with state_file.open() as f:
            data = json.load(f)

        return cls.model_validate(data)

    @classmethod
    def get_latest(cls) -> WorkflowState | None:
        """Get the most recent workflow state.

        Returns:
            The latest workflow state, or None if none exists.
        """
        settings = get_settings()
        state_dir = settings.workflow.state_dir

        if not state_dir.exists():
            return None

        state_files = sorted(state_dir.glob("*.json"), reverse=True)
        if not state_files:
            return None

        return cls.load(state_files[0].stem)

    @classmethod
    def list_all(cls) -> list[WorkflowState]:
        """List all saved workflow states.

        Returns:
            List of all workflow states, sorted by creation time (newest first).
        """
        settings = get_settings()
        state_dir = settings.workflow.state_dir

        if not state_dir.exists():
            return []

        states = []
        for state_file in sorted(state_dir.glob("*.json"), reverse=True):
            with contextlib.suppress(Exception):
                states.append(cls.load(state_file.stem))

        return states

    @classmethod
    def delete(cls, state_id: str) -> bool:
        """Delete a workflow state.

        Args:
            state_id: The ID of the state to delete.

        Returns:
            True if deleted, False if not found.
        """
        settings = get_settings()
        state_file = settings.workflow.state_dir / f"{state_id}.json"

        if state_file.exists():
            state_file.unlink()
            return True
        return False

    @classmethod
    def cleanup_old(cls, keep_count: int = 10) -> int:
        """Remove old workflow states, keeping the most recent ones.

        Args:
            keep_count: Number of recent states to keep.

        Returns:
            Number of states deleted.
        """
        settings = get_settings()
        state_dir = settings.workflow.state_dir

        if not state_dir.exists():
            return 0

        state_files = sorted(state_dir.glob("*.json"), reverse=True)

        deleted = 0
        for state_file in state_files[keep_count:]:
            state_file.unlink()
            deleted += 1

        return deleted
