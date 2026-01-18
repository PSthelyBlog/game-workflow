"""Main workflow state machine.

This module implements the orchestrator that manages the game
creation workflow through its various phases.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from game_workflow.config import get_settings
from game_workflow.orchestrator.exceptions import (
    AgentError,
    ApprovalRejectedError,
    BuildFailedError,
    QAFailedError,
    WorkflowError,
)
from game_workflow.orchestrator.state import WorkflowPhase, WorkflowState

if TYPE_CHECKING:
    from game_workflow.agents.build import BuildAgent
    from game_workflow.agents.design import DesignAgent
    from game_workflow.agents.publish import PublishAgent
    from game_workflow.agents.qa import QAAgent

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


class ApprovalHook(Protocol):
    """Protocol for approval hooks."""

    async def request_approval(
        self,
        message: str,
        context: dict[str, Any] | None = None,
        timeout_minutes: int | None = None,
    ) -> bool:
        """Request approval from a human."""
        ...

    async def send_notification(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
        level: str = "info",
    ) -> bool:
        """Send a notification."""
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

    Approval gates are inserted between major phases:
    - After DESIGN: Approve concept before building
    - After QA: Approve build before publishing
    - After PUBLISH: Approve before final release

    Attributes:
        prompt: The game concept prompt.
        engine: The game engine to use.
        state: The current workflow state.
        output_dir: Directory for all workflow outputs.
        approval_hook: Hook for human-in-the-loop approvals.
    """

    def __init__(
        self,
        prompt: str,
        engine: str | None = None,
        state: WorkflowState | None = None,
        output_dir: Path | None = None,
        approval_hook: ApprovalHook | None = None,
        auto_approve: bool = False,
        max_retries: int = 2,
    ) -> None:
        """Initialize a new workflow.

        Args:
            prompt: The game concept prompt.
            engine: The game engine to use. Defaults to config setting.
            state: Existing state to resume from. If None, creates new state.
            output_dir: Directory for workflow outputs. Defaults to state dir.
            approval_hook: Hook for requesting human approvals.
            auto_approve: If True, skip approval gates (for testing).
            max_retries: Maximum retry attempts for failed phases.
        """
        settings = get_settings()

        self.prompt = prompt
        self.engine = engine or settings.workflow.default_engine
        self.auto_approve = auto_approve
        self.max_retries = max_retries

        # Initialize or resume state
        if state is not None:
            self.state = state
        else:
            self.state = WorkflowState(
                prompt=prompt,
                engine=self.engine,
            )

        # Set up output directory
        if output_dir is not None:
            self.output_dir = output_dir
        else:
            self.output_dir = settings.workflow.state_dir / self.state.id

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize hooks
        self._hooks: list[WorkflowHook] = []
        self._approval_hook = approval_hook
        self._setup_default_hooks()

        # Agent instances (lazy loaded)
        self._design_agent: DesignAgent | None = None
        self._build_agent: BuildAgent | None = None
        self._qa_agent: QAAgent | None = None
        self._publish_agent: PublishAgent | None = None

        # Phase results for passing data between phases
        self._design_result: dict[str, Any] | None = None
        self._build_result: dict[str, Any] | None = None
        self._qa_result: dict[str, Any] | None = None

        # Retry tracking
        self._retry_counts: dict[str, int] = {}

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

    def set_approval_hook(self, hook: ApprovalHook) -> None:
        """Set the approval hook.

        Args:
            hook: The approval hook instance.
        """
        self._approval_hook = hook

    @property
    def phase(self) -> WorkflowPhase:
        """Get the current workflow phase."""
        return self.state.phase

    @property
    def design_agent(self) -> DesignAgent:
        """Get or create the DesignAgent."""
        if self._design_agent is None:
            from game_workflow.agents.design import DesignAgent

            self._design_agent = DesignAgent(
                state=self.state,
                output_dir=self.output_dir / "design",
            )
        return self._design_agent

    @property
    def build_agent(self) -> BuildAgent:
        """Get or create the BuildAgent."""
        if self._build_agent is None:
            from game_workflow.agents.build import BuildAgent

            self._build_agent = BuildAgent(
                state=self.state,
            )
        return self._build_agent

    @property
    def qa_agent(self) -> QAAgent:
        """Get or create the QAAgent."""
        if self._qa_agent is None:
            from game_workflow.agents.qa import QAAgent

            self._qa_agent = QAAgent(
                state=self.state,
            )
        return self._qa_agent

    @property
    def publish_agent(self) -> PublishAgent:
        """Get or create the PublishAgent."""
        if self._publish_agent is None:
            from game_workflow.agents.publish import PublishAgent

            self._publish_agent = PublishAgent(
                state=self.state,
                output_dir=self.output_dir / "publish",
            )
        return self._publish_agent

    @classmethod
    def resume(cls, state_id: str, **kwargs: Any) -> Workflow:
        """Resume a workflow from a saved state.

        Args:
            state_id: The ID of the state to resume.
            **kwargs: Additional arguments passed to constructor.

        Returns:
            A new Workflow instance with the loaded state.
        """
        state = WorkflowState.load(state_id)
        return cls(prompt=state.prompt, engine=state.engine, state=state, **kwargs)

    @classmethod
    def resume_latest(cls, **kwargs: Any) -> Workflow | None:
        """Resume the most recent workflow.

        Args:
            **kwargs: Additional arguments passed to constructor.

        Returns:
            A new Workflow instance with the latest state, or None if no state exists.
        """
        state = WorkflowState.get_latest()
        if state is None:
            return None
        return cls(prompt=state.prompt, engine=state.engine, state=state, **kwargs)

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

    async def _request_approval(
        self,
        gate: str,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """Request approval at a gate.

        Args:
            gate: The approval gate name (for tracking).
            message: The approval message.
            context: Additional context to display.

        Returns:
            True if approved.

        Raises:
            ApprovalRejectedError: If rejected.
        """
        # Skip if auto-approve is enabled
        if self.auto_approve:
            logger.info(f"Auto-approving gate: {gate}")
            self.state.set_approval(gate, approved=True)
            self.state.save()
            return True

        # Skip if no approval hook configured
        if self._approval_hook is None:
            logger.warning(f"No approval hook configured, auto-approving: {gate}")
            self.state.set_approval(gate, approved=True)
            self.state.save()
            return True

        # Request approval
        try:
            approved = await self._approval_hook.request_approval(
                message=message,
                context=context,
                timeout_minutes=None,  # Wait indefinitely
            )
            self.state.set_approval(gate, approved=approved)
            self.state.save()
            return approved
        except ApprovalRejectedError:
            self.state.set_approval(gate, approved=False)
            self.state.save()
            raise

    async def _send_notification(
        self,
        message: str,
        context: dict[str, Any] | None = None,
        level: str = "info",
    ) -> None:
        """Send a notification via the approval hook.

        Args:
            message: The notification message.
            context: Additional context.
            level: Notification level (info, warning, error, success).
        """
        if self._approval_hook is not None:
            try:
                await self._approval_hook.send_notification(
                    message=message,
                    context=context,
                    level=level,
                )
            except Exception as e:
                logger.warning(f"Failed to send notification: {e}")

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

        await self._send_notification(
            f"Starting game workflow: {self.prompt[:50]}...",
            context={"engine": self.engine, "state_id": self.state.id},
            level="info",
        )

        try:
            while not self.state.phase.is_terminal:
                await self._execute_current_phase()

            # Send completion notification
            if self.state.phase == WorkflowPhase.COMPLETE:
                await self._send_notification(
                    "Workflow completed successfully!",
                    context={
                        "state_id": self.state.id,
                        "artifacts": len(self.state.artifacts),
                    },
                    level="success",
                )

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
            result = await self._run_phase_with_retry(phase)
            await self._notify_phase_complete(phase, result)

            # Transition to next phase
            next_phase = phase.get_next_phase()
            if next_phase is not None:
                self.state.transition_to(next_phase)
                self.state.save()

        except WorkflowError as e:
            await self._handle_failure(e)
            raise

    async def _run_phase_with_retry(self, phase: WorkflowPhase) -> dict[str, Any]:
        """Run a phase with retry logic.

        Args:
            phase: The phase to run.

        Returns:
            Phase results.
        """
        phase_key = phase.value
        retry_count = self._retry_counts.get(phase_key, 0)

        while True:
            try:
                return await self._run_phase(phase)
            except (AgentError, BuildFailedError, QAFailedError) as e:
                retry_count += 1
                self._retry_counts[phase_key] = retry_count

                if retry_count > self.max_retries:
                    logger.error(f"Phase {phase.value} failed after {retry_count} attempts")
                    raise

                logger.warning(
                    f"Phase {phase.value} failed (attempt {retry_count}/{self.max_retries + 1}), retrying..."
                )
                self.state.add_error(f"Retry {retry_count}: {e}")

                # Notify about retry
                await self._send_notification(
                    f"Phase {phase.value} failed, retrying...",
                    context={"attempt": retry_count, "error": str(e)[:100]},
                    level="warning",
                )

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

        # Store prompt in metadata for later phases
        self.state.metadata["prompt"] = self.prompt
        self.state.metadata["engine"] = self.engine
        self.state.metadata["output_dir"] = str(self.output_dir)
        self.state.save()

        return {"initialized": True, "prompt": self.prompt, "engine": self.engine}

    async def _design_phase(self) -> dict[str, Any]:
        """Execute the design phase.

        Generates game concept and design document using the DesignAgent.

        Returns:
            Design phase results including generated artifacts.
        """
        logger.info("Starting design phase...")

        # Run design agent
        result = await self.design_agent.run(
            prompt=self.prompt,
            engine=self.engine,
        )

        # Store result for later phases
        self._design_result = result

        # Create checkpoint after design
        self.state.create_checkpoint("Design phase completed")

        # Request approval for the concept
        concept = result.get("selected_concept", {})
        approval_context = {
            "title": concept.get("title", "Unknown"),
            "genre": concept.get("genre", "Unknown"),
            "tagline": concept.get("tagline", "")[:100],
            "artifacts": list(result.get("artifacts", {}).keys()),
        }

        approved = await self._request_approval(
            gate="concept",
            message=f"Approve game concept: *{concept.get('title', 'Unknown')}*\n\n{concept.get('tagline', '')}",
            context=approval_context,
        )

        if not approved:
            raise ApprovalRejectedError("Concept approval rejected")

        return result

    async def _build_phase(self) -> dict[str, Any]:
        """Execute the build phase.

        Builds the game using Claude Code via the BuildAgent.

        Returns:
            Build phase results.
        """
        logger.info("Starting build phase...")

        # Get design artifacts
        if self._design_result is None:
            # Try to load from state artifacts
            gdd_path_str = self.state.artifacts.get("gdd_json")
            if gdd_path_str is None:
                raise AgentError("BuildAgent", "No GDD available - design phase must run first")
            gdd_path = Path(gdd_path_str)
        else:
            gdd_path_str = self._design_result.get("artifacts", {}).get("gdd_json")
            if gdd_path_str is None:
                raise AgentError("BuildAgent", "No GDD path in design result")
            gdd_path = Path(gdd_path_str)

        # Run build agent
        build_output_dir = self.output_dir / "game"
        result = await self.build_agent.run(
            gdd_path=gdd_path,
            output_dir=build_output_dir,
            engine=self.engine,
        )

        # Store result for later phases
        self._build_result = result

        # Create checkpoint
        self.state.create_checkpoint("Build phase completed")

        return result

    async def _qa_phase(self) -> dict[str, Any]:
        """Execute the QA phase.

        Tests and validates the game using the QAAgent.

        Returns:
            QA phase results including test results.
        """
        logger.info("Starting QA phase...")

        # Get build directory
        if self._build_result is None:
            # Try to load from state artifacts
            game_source = self.state.artifacts.get("game_source")
            if game_source is None:
                raise AgentError("QAAgent", "No game build available - build phase must run first")
            game_dir = Path(game_source)
        else:
            game_dir_str = self._build_result.get("output_dir")
            if game_dir_str is None:
                raise AgentError("QAAgent", "No output_dir in build result")
            game_dir = Path(game_dir_str)

        # Get game title from design
        game_title = "Game"
        if self._design_result:
            concept = self._design_result.get("selected_concept", {})
            game_title = concept.get("title", "Game")

        # Run QA agent
        result = await self.qa_agent.run(
            game_dir=game_dir,
            game_title=game_title,
        )

        # Store result for later phases
        self._qa_result = result

        # Create checkpoint
        self.state.create_checkpoint("QA phase completed")

        # Request approval for the build
        report = result.get("report", {})
        summary = report.get("summary", {})

        approval_context = {
            "title": game_title,
            "total_tests": summary.get("total_tests", 0),
            "passed": summary.get("passed", 0),
            "failed": summary.get("failed", 0),
            "success_rate": f"{summary.get('success_rate', 0):.1f}%",
            "status": summary.get("overall_status", "unknown"),
        }

        approved = await self._request_approval(
            gate="build",
            message=f"Approve build for *{game_title}*\n\nQA Status: {summary.get('overall_status', 'unknown').upper()}\nTests: {summary.get('passed', 0)}/{summary.get('total_tests', 0)} passed",
            context=approval_context,
        )

        if not approved:
            raise ApprovalRejectedError("Build approval rejected")

        return result

    async def _publish_phase(self) -> dict[str, Any]:
        """Execute the publish phase.

        Prepares and publishes the game using the PublishAgent.

        Returns:
            Publish phase results.
        """
        logger.info("Starting publish phase...")

        # Get build directory
        if self._build_result is None:
            game_build = self.state.artifacts.get("game_build")
            if game_build is None:
                raise AgentError("PublishAgent", "No game build available")
            game_dir = Path(game_build)
        else:
            build_dir_str = self._build_result.get("build_dir")
            if build_dir_str is None:
                # Fall back to output_dir
                build_dir_str = self._build_result.get("output_dir")
            if build_dir_str is None:
                raise AgentError("PublishAgent", "No build directory in build result")
            game_dir = Path(build_dir_str)

        # Get GDD for marketing copy
        gdd_path: Path | None = None
        gdd_data = None
        if self._design_result:
            gdd_data = self._design_result.get("gdd")
        else:
            gdd_path_str = self.state.artifacts.get("gdd_json")
            if gdd_path_str:
                gdd_path = Path(gdd_path_str)

        # Run publish agent
        result = await self.publish_agent.run(
            game_dir=game_dir,
            gdd_path=gdd_path,
            gdd_data=gdd_data,
        )

        # Create checkpoint
        self.state.create_checkpoint("Publish phase completed")

        # Request approval for publishing
        store_page = result.get("store_page", {})
        approval_context = {
            "title": store_page.get("title", "Unknown"),
            "tagline": store_page.get("tagline", "")[:100],
            "visibility": result.get("publish_output", {}).get("visibility", "draft"),
        }

        approved = await self._request_approval(
            gate="publish",
            message=f"Approve publishing *{store_page.get('title', 'Unknown')}* to itch.io\n\n_{store_page.get('tagline', '')}_",
            context=approval_context,
        )

        if not approved:
            raise ApprovalRejectedError("Publish approval rejected")

        return result

    async def _handle_failure(self, error: Exception) -> None:
        """Handle a workflow failure.

        Args:
            error: The error that caused the failure.
        """
        error_msg = str(error)
        logger.error(f"Workflow failed: {error_msg}")

        self.state.add_error(error_msg)
        await self._notify_error(error)

        # Send failure notification
        await self._send_notification(
            f"Workflow failed: {error_msg[:100]}",
            context={"phase": self.state.phase.value, "state_id": self.state.id},
            level="error",
        )

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

        await self._send_notification(
            "Workflow cancelled by user",
            context={"state_id": self.state.id, "phase": self.state.phase.value},
            level="warning",
        )

        if self.state.phase.can_transition_to(WorkflowPhase.FAILED):
            self.state.transition_to(WorkflowPhase.FAILED)
            self.state.save()

    async def retry_phase(self, phase: WorkflowPhase | None = None) -> dict[str, Any]:
        """Retry a failed phase.

        Args:
            phase: The phase to retry. If None, retries the current phase
                   or the phase before FAILED.

        Returns:
            Phase results.

        Raises:
            WorkflowError: If workflow is not in a retryable state.
        """
        if phase is None:
            if self.state.phase == WorkflowPhase.FAILED:
                # Find the last non-failed phase from errors/checkpoints
                # For now, transition back to INIT to restart
                self.state.transition_to(WorkflowPhase.INIT)
                self.state.save()
                return await self.run()
            else:
                phase = self.state.phase

        # Reset retry count for this phase
        self._retry_counts[phase.value] = 0

        # Run the phase
        return await self._run_phase(phase)

    async def rollback_to_checkpoint(self, checkpoint_id: str) -> None:
        """Rollback to a specific checkpoint.

        Args:
            checkpoint_id: The checkpoint ID to rollback to.

        Raises:
            WorkflowError: If checkpoint not found.
        """
        for checkpoint in self.state.checkpoints:
            if checkpoint.checkpoint_id == checkpoint_id:
                # Transition to that phase
                if self.state.phase.can_transition_to(checkpoint.phase):
                    self.state.transition_to(checkpoint.phase)
                else:
                    # Force transition via FAILED -> INIT -> target
                    self.state.transition_to(WorkflowPhase.FAILED)
                    self.state.transition_to(WorkflowPhase.INIT)
                    # Then transition through phases
                    current = WorkflowPhase.INIT
                    while current != checkpoint.phase:
                        next_phase = current.get_next_phase()
                        if next_phase is None:
                            break
                        self.state.transition_to(next_phase)
                        current = next_phase

                self.state.save()
                logger.info(
                    f"Rolled back to checkpoint {checkpoint_id} (phase: {checkpoint.phase})"
                )
                return

        raise WorkflowError(f"Checkpoint not found: {checkpoint_id}")
