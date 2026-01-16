"""State persistence for workflows.

This module handles saving and loading workflow state to enable
resumption after interruptions.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from game_workflow.config import get_settings


class WorkflowState(BaseModel):
    """Persistent state for a workflow."""

    id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    phase: str = "init"
    prompt: str = ""
    engine: str = "phaser"
    artifacts: dict[str, Path] = Field(default_factory=dict)
    approvals: dict[str, bool] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

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
    def load(cls, state_id: str) -> "WorkflowState":
        """Load state from disk.

        Args:
            state_id: The ID of the state to load.

        Returns:
            The loaded workflow state.

        Raises:
            FileNotFoundError: If the state file doesn't exist.
        """
        settings = get_settings()
        state_file = settings.workflow.state_dir / f"{state_id}.json"

        with state_file.open() as f:
            data = json.load(f)

        return cls.model_validate(data)

    @classmethod
    def get_latest(cls) -> "WorkflowState | None":
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
