"""Checkpoint hook for state persistence.

This hook saves workflow state at key points to enable
resumption after interruptions.
"""

from __future__ import annotations

import logging
from typing import Any

from game_workflow.orchestrator.state import WorkflowState

logger = logging.getLogger("game_workflow.hooks.checkpoint")


class CheckpointHook:
    """Hook for creating workflow checkpoints.

    Automatically saves state at configured intervals and
    after significant workflow events. Supports checkpoint
    pruning to manage disk usage.

    Checkpoints are created:
    - After each phase completes
    - When artifacts are created
    - When approvals are received
    - On explicit checkpoint requests
    """

    def __init__(
        self,
        state: WorkflowState,
        max_checkpoints: int = 50,
        auto_prune: bool = True,
    ) -> None:
        """Initialize the hook.

        Args:
            state: The workflow state to checkpoint.
            max_checkpoints: Maximum number of checkpoints to keep per workflow.
            auto_prune: Automatically prune old checkpoints.
        """
        self.state = state
        self.max_checkpoints = max_checkpoints
        self.auto_prune = auto_prune
        self._checkpoint_count = 0

    def _maybe_prune_checkpoints(self) -> None:
        """Prune old checkpoints if over the limit."""
        if not self.auto_prune:
            return

        if len(self.state.checkpoints) > self.max_checkpoints:
            # Keep only the most recent checkpoints
            pruned_count = len(self.state.checkpoints) - self.max_checkpoints
            self.state.checkpoints = self.state.checkpoints[-self.max_checkpoints :]
            logger.debug(f"Pruned {pruned_count} old checkpoints")

    async def on_phase_start(
        self,
        phase: str,
        context: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> None:
        """Create a checkpoint when a phase starts.

        Args:
            phase: The phase name.
            context: Additional context (kept for protocol compatibility).
        """
        self.state.create_checkpoint(f"Phase started: {phase}")
        self._checkpoint_count += 1
        self._maybe_prune_checkpoints()
        logger.debug(f"Checkpoint created: phase start - {phase}")

    async def on_phase_complete(self, phase: str, result: dict[str, Any] | None = None) -> None:
        """Create a checkpoint after a phase completes.

        Args:
            phase: The completed phase name.
            result: Phase results.
        """
        description = f"Phase completed: {phase}"
        if result and result.get("status"):
            description += f" ({result['status']})"

        self.state.create_checkpoint(description)
        self._checkpoint_count += 1
        self._maybe_prune_checkpoints()
        logger.debug(f"Checkpoint created: phase complete - {phase}")

    async def on_error(self, error: Exception, context: dict[str, Any] | None = None) -> None:
        """Create a checkpoint when an error occurs.

        Args:
            error: The exception.
            context: Additional context.
        """
        phase = context.get("phase", "unknown") if context else "unknown"
        self.state.add_error(str(error))
        self.state.create_checkpoint(f"Error in {phase}: {str(error)[:50]}")
        self._checkpoint_count += 1
        logger.debug(f"Checkpoint created: error in {phase}")

    async def on_artifact_created(self, name: str, path: str) -> None:
        """Record an artifact and checkpoint.

        Args:
            name: Artifact name.
            path: Path to the artifact.
        """
        self.state.add_artifact(name, path)
        self.state.create_checkpoint(f"Artifact created: {name}")
        self._checkpoint_count += 1
        self._maybe_prune_checkpoints()
        logger.debug(f"Checkpoint created: artifact - {name}")

    async def on_approval_requested(
        self,
        gate: str,
        message: str,  # noqa: ARG002
    ) -> None:
        """Create a checkpoint when approval is requested.

        Args:
            gate: The approval gate name.
            message: The approval message (kept for protocol compatibility).
        """
        self.state.create_checkpoint(f"Approval requested: {gate}")
        self._checkpoint_count += 1
        logger.debug(f"Checkpoint created: approval requested - {gate}")

    async def on_approval_received(
        self, gate: str, approved: bool, reason: str | None = None
    ) -> None:
        """Record an approval decision and checkpoint.

        Args:
            gate: The approval gate name.
            approved: Whether approval was granted.
            reason: Optional reason provided.
        """
        self.state.set_approval(gate, approved)

        status = "approved" if approved else "rejected"
        description = f"Approval {status}: {gate}"
        if reason:
            description += f" - {reason[:30]}"

        self.state.create_checkpoint(description)
        self._checkpoint_count += 1
        self._maybe_prune_checkpoints()
        logger.debug(f"Checkpoint created: approval {status} - {gate}")

    async def on_tool_call(
        self,
        tool_name: str,
        tool_input: dict[str, Any],  # noqa: ARG002
        tool_result: Any = None,  # noqa: ARG002
    ) -> None:
        """Optionally checkpoint after tool calls.

        This is called frequently so we only checkpoint on significant tools.

        Args:
            tool_name: The name of the tool called.
            tool_input: The input parameters (kept for protocol compatibility).
            tool_result: The result if available (kept for protocol compatibility).
        """
        # Only checkpoint for significant tool operations
        significant_tools = {"write_file", "create_file", "execute", "commit", "push"}

        if tool_name.lower() in significant_tools:
            self.state.create_checkpoint(f"Tool: {tool_name}")
            self._checkpoint_count += 1
            self._maybe_prune_checkpoints()

    def get_checkpoint_count(self) -> int:
        """Get the number of checkpoints created in this session.

        Returns:
            Number of checkpoints created.
        """
        return self._checkpoint_count

    @staticmethod
    def cleanup_old_workflows(keep_count: int = 10) -> int:
        """Clean up old workflow states.

        This is a convenience method to manage disk space by
        removing old workflow states.

        Args:
            keep_count: Number of recent workflows to keep.

        Returns:
            Number of workflows deleted.
        """
        return WorkflowState.cleanup_old(keep_count=keep_count)
