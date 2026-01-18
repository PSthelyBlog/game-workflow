"""Main workflow state machine.

This module implements the orchestrator that manages the game
creation workflow through its various phases.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Protocol

from game_workflow.config import get_settings
from game_workflow.orchestrator.exceptions import WorkflowError
from game_workflow.orchestrator.state import WorkflowPhase, WorkflowState

if TYPE_CHECKING:
    from game_workflow.agents.base import BaseAgent

logger = logging.getLogger("game_workflow.orchestrator")


class WorkflowHook(Protocol):
    """Protocol for workflow hooks."""

    async def on_phase_start(self, phase: str, context: dict[str, Any] | None = None) -> None:
        """Called when a phase starts."""
        ...

    async def on_phase_complete(self, phase: str, result: dict[str, Any] | None = None) -> None:
        """Called when a phase completes."""
        ...

    async def on_error(self, error: Exception, context: dict[str, Any] | None = None) -> None:
        """Called when an error occurs."""
        ...


class Workflow:
    """Main workflow orchestrator.

    Manages the game creation workflow through design, build,
    QA, and publish phases with human approval gates.

    The workflow follows these phases:
    1. INIT - Initial state, workflow is being set up
    2. DESIGN - Generate game concept and design document
    3. BUILD - Implement the game using Claude Code
    4. QA - Test and validate the game
    5. PUBLISH - Prepare and publish to itch.io
    6. COMPLETE - Workflow finished successfully
    7. FAILED - Workflow failed (can restart)
    """

    def __init__(
        self,
        prompt: str,
        engine: str | None = None,
        state: WorkflowState | None = None,
    ) -> None:
        """Initialize a new workflow.

        Args:
            prompt: The game concept prompt.
            engine: The game engine to use. Defaults to config setting.
            state: Existing state to resume from. If None, creates new state.
        """
        settings = get_settings()

        self.prompt = prompt
        self.engine = engine or settings.workflow.default_engine

        # Initialize or resume state
        if state is not None:
            self.state = state
        else:
            self.state = WorkflowState(
                prompt=prompt,
                engine=self.engine,
            )

        # Initialize hooks
        self._hooks: list[WorkflowHook] = []
        self._setup_default_hooks()

        # Agent instances (lazy loaded)
        self._design_agent: BaseAgent | None = None
        self._build_agent: BaseAgent | None = None
        self._qa_agent: BaseAgent | None = None
        self._publish_agent: BaseAgent | None = None

    def _setup_default_hooks(self) -> None:
        """Set up the default workflow hooks."""
        # Import here to avoid circular imports
        from game_workflow.hooks.checkpoint import CheckpointHook
        from game_workflow.hooks.logging import LoggingHook

        settings = get_settings()

        # Add logging hook
        logging_hook = LoggingHook(log_level=settings.workflow.log_level)
        self.add_hook(logging_hook)

        # Add checkpoint hook
        checkpoint_hook = CheckpointHook(self.state)
        self.add_hook(checkpoint_hook)

    def add_hook(self, hook: WorkflowHook) -> None:
        """Add a hook to the workflow.

        Args:
            hook: The hook to add.
        """
        self._hooks.append(hook)

    @property
    def phase(self) -> WorkflowPhase:
        """Get the current workflow phase."""
        return self.state.phase

    @classmethod
    def resume(cls, state_id: str) -> Workflow:
        """Resume a workflow from a saved state.

        Args:
            state_id: The ID of the state to resume.

        Returns:
            A new Workflow instance with the loaded state.
        """
        state = WorkflowState.load(state_id)
        return cls(prompt=state.prompt, engine=state.engine, state=state)

    @classmethod
    def resume_latest(cls) -> Workflow | None:
        """Resume the most recent workflow.

        Returns:
            A new Workflow instance with the latest state, or None if no state exists.
        """
        state = WorkflowState.get_latest()
        if state is None:
            return None
        return cls(prompt=state.prompt, engine=state.engine, state=state)

    async def _notify_phase_start(self, phase: WorkflowPhase) -> None:
        """Notify all hooks that a phase is starting.

        Args:
            phase: The phase that is starting.
        """
        context = {"prompt": self.prompt, "engine": self.engine, "state_id": self.state.id}
        for hook in self._hooks:
            try:
                await hook.on_phase_start(phase.value, context)
            except Exception as e:
                logger.warning(f"Hook {hook} failed on phase start: {e}")

    async def _notify_phase_complete(self, phase: WorkflowPhase, result: dict[str, Any]) -> None:
        """Notify all hooks that a phase completed.

        Args:
            phase: The phase that completed.
            result: The phase results.
        """
        for hook in self._hooks:
            try:
                await hook.on_phase_complete(phase.value, result)
            except Exception as e:
                logger.warning(f"Hook {hook} failed on phase complete: {e}")

    async def _notify_error(self, error: Exception) -> None:
        """Notify all hooks of an error.

        Args:
            error: The error that occurred.
        """
        context = {"phase": self.state.phase.value, "state_id": self.state.id}
        for hook in self._hooks:
            try:
                await hook.on_error(error, context)
            except Exception as e:
                logger.warning(f"Hook {hook} failed on error: {e}")

    async def run(self) -> dict[str, Any]:
        """Execute the full workflow.

        Runs through all phases from the current state until completion or failure.

        Returns:
            Workflow results including:
                - status: "complete" or "failed"
                - state_id: The workflow state ID
                - artifacts: Dictionary of generated artifacts
                - errors: List of any errors encountered
        """
        logger.info(f"Starting workflow from phase: {self.state.phase}")
        self.state.save()

        try:
            while not self.state.phase.is_terminal:
                await self._execute_current_phase()

            return {
                "status": "complete" if self.state.phase == WorkflowPhase.COMPLETE else "failed",
                "state_id": self.state.id,
                "artifacts": self.state.artifacts,
                "errors": self.state.errors,
            }

        except Exception as e:
            await self._handle_failure(e)
            return {
                "status": "failed",
                "state_id": self.state.id,
                "artifacts": self.state.artifacts,
                "errors": self.state.errors,
            }

    async def _execute_current_phase(self) -> None:
        """Execute the current phase and transition to the next."""
        phase = self.state.phase
        await self._notify_phase_start(phase)

        try:
            result = await self._run_phase(phase)
            await self._notify_phase_complete(phase, result)

            # Transition to next phase
            next_phase = phase.get_next_phase()
            if next_phase is not None:
                self.state.transition_to(next_phase)
                self.state.save()

        except WorkflowError as e:
            await self._handle_failure(e)
            raise

    async def _run_phase(self, phase: WorkflowPhase) -> dict[str, Any]:
        """Run a specific phase.

        Args:
            phase: The phase to run.

        Returns:
            Phase results.
        """
        phase_methods = {
            WorkflowPhase.INIT: self._init_phase,
            WorkflowPhase.DESIGN: self._design_phase,
            WorkflowPhase.BUILD: self._build_phase,
            WorkflowPhase.QA: self._qa_phase,
            WorkflowPhase.PUBLISH: self._publish_phase,
        }

        method = phase_methods.get(phase)
        if method is None:
            return {}

        return await method()

    async def _init_phase(self) -> dict[str, Any]:
        """Initialize the workflow.

        Sets up initial state and validates configuration.

        Returns:
            Initialization result.
        """
        logger.info(f"Initializing workflow for: {self.prompt[:50]}...")

        # Create initial checkpoint
        self.state.create_checkpoint("Workflow initialized")

        return {"initialized": True, "prompt": self.prompt, "engine": self.engine}

    async def _design_phase(self) -> dict[str, Any]:
        """Execute the design phase.

        Generates game concept and design document using the DesignAgent.

        Returns:
            Design phase results including generated artifacts.
        """
        logger.info("Starting design phase...")

        # TODO: Implement DesignAgent invocation in Phase 2
        # For now, create a placeholder checkpoint
        self.state.create_checkpoint("Design phase started (stub)")

        return {"status": "stub", "message": "Design agent not yet implemented"}

    async def _build_phase(self) -> dict[str, Any]:
        """Execute the build phase.

        Builds the game using Claude Code via the BuildAgent.

        Returns:
            Build phase results.
        """
        logger.info("Starting build phase...")

        # TODO: Implement BuildAgent invocation in Phase 3
        self.state.create_checkpoint("Build phase started (stub)")

        return {"status": "stub", "message": "Build agent not yet implemented"}

    async def _qa_phase(self) -> dict[str, Any]:
        """Execute the QA phase.

        Tests and validates the game using the QAAgent.

        Returns:
            QA phase results including test results.
        """
        logger.info("Starting QA phase...")

        # TODO: Implement QAAgent invocation in Phase 4
        self.state.create_checkpoint("QA phase started (stub)")

        return {"status": "stub", "message": "QA agent not yet implemented"}

    async def _publish_phase(self) -> dict[str, Any]:
        """Execute the publish phase.

        Prepares and publishes the game using the PublishAgent.

        Returns:
            Publish phase results.
        """
        logger.info("Starting publish phase...")

        # TODO: Implement PublishAgent invocation in Phase 5
        self.state.create_checkpoint("Publish phase started (stub)")

        return {"status": "stub", "message": "Publish agent not yet implemented"}

    async def _handle_failure(self, error: Exception) -> None:
        """Handle a workflow failure.

        Args:
            error: The error that caused the failure.
        """
        error_msg = str(error)
        logger.error(f"Workflow failed: {error_msg}")

        self.state.add_error(error_msg)
        await self._notify_error(error)

        # Transition to FAILED state if possible
        if self.state.phase.can_transition_to(WorkflowPhase.FAILED):
            self.state.transition_to(WorkflowPhase.FAILED)
            self.state.save()

    async def cancel(self) -> None:
        """Cancel the current workflow.

        Marks the workflow as failed and saves the state.
        """
        logger.info(f"Cancelling workflow: {self.state.id}")
        self.state.add_error("Workflow cancelled by user")

        if self.state.phase.can_transition_to(WorkflowPhase.FAILED):
            self.state.transition_to(WorkflowPhase.FAILED)
            self.state.save()
