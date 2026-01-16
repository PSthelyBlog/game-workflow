"""Checkpoint hook for state persistence.

This hook saves workflow state at key points to enable
resumption after interruptions.
"""

from game_workflow.orchestrator.state import WorkflowState


class CheckpointHook:
    """Hook for creating workflow checkpoints.

    Automatically saves state at configured intervals and
    after significant workflow events.
    """

    def __init__(self, state: WorkflowState) -> None:
        """Initialize the hook.

        Args:
            state: The workflow state to checkpoint.
        """
        self.state = state

    async def on_phase_complete(self, phase: str) -> None:
        """Create a checkpoint after a phase completes.

        Args:
            phase: The completed phase name.
        """
        self.state.phase = phase
        self.state.save()

    async def on_artifact_created(self, name: str, path: str) -> None:
        """Record an artifact and checkpoint.

        Args:
            name: Artifact name.
            path: Path to the artifact.
        """
        from pathlib import Path

        self.state.artifacts[name] = Path(path)
        self.state.save()

    async def on_approval_received(self, gate: str, approved: bool) -> None:
        """Record an approval decision and checkpoint.

        Args:
            gate: The approval gate name.
            approved: Whether approval was granted.
        """
        self.state.approvals[gate] = approved
        self.state.save()
