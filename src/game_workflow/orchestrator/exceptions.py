"""Custom exceptions for workflow errors.

This module defines the exception hierarchy for workflow-related errors.
All exceptions inherit from WorkflowError for easy catching of workflow issues.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from game_workflow.orchestrator.state import WorkflowPhase


class WorkflowError(Exception):
    """Base exception for workflow errors.

    All workflow-related exceptions inherit from this class.
    """

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Initialize the exception.

        Args:
            message: The error message.
            context: Optional additional context about the error.
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}


class ConfigurationError(WorkflowError):
    """Configuration is invalid or missing required values."""

    pass


class InvalidTransitionError(WorkflowError):
    """Attempted an invalid state transition.

    Raised when trying to move to a phase that isn't a valid
    successor of the current phase.
    """

    def __init__(
        self,
        from_phase: "WorkflowPhase",
        to_phase: "WorkflowPhase",
        message: str | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            from_phase: The current phase.
            to_phase: The attempted target phase.
            message: Optional custom message.
        """
        self.from_phase = from_phase
        self.to_phase = to_phase
        msg = message or f"Cannot transition from {from_phase} to {to_phase}"
        super().__init__(msg, {"from_phase": str(from_phase), "to_phase": str(to_phase)})


class ApprovalTimeoutError(WorkflowError):
    """Human didn't respond to approval request in time."""

    def __init__(self, gate: str, timeout_minutes: int | None = None) -> None:
        """Initialize the exception.

        Args:
            gate: The approval gate that timed out.
            timeout_minutes: The timeout duration if applicable.
        """
        self.gate = gate
        self.timeout_minutes = timeout_minutes
        msg = f"Approval timeout for gate: {gate}"
        if timeout_minutes:
            msg += f" after {timeout_minutes} minutes"
        super().__init__(msg, {"gate": gate, "timeout_minutes": timeout_minutes})


class ApprovalRejectedError(WorkflowError):
    """Human rejected the approval request."""

    def __init__(self, gate: str, reason: str | None = None) -> None:
        """Initialize the exception.

        Args:
            gate: The approval gate that was rejected.
            reason: Optional rejection reason provided by user.
        """
        self.gate = gate
        self.reason = reason
        msg = f"Approval rejected for gate: {gate}"
        if reason:
            msg += f" - Reason: {reason}"
        super().__init__(msg, {"gate": gate, "reason": reason})


class BuildFailedError(WorkflowError):
    """Game build failed."""

    def __init__(self, message: str, build_output: str | None = None) -> None:
        """Initialize the exception.

        Args:
            message: The error message.
            build_output: Optional build output/logs.
        """
        super().__init__(message, {"build_output": build_output})
        self.build_output = build_output


class DesignFailedError(WorkflowError):
    """Design phase failed."""

    pass


class QAFailedError(WorkflowError):
    """QA phase failed.

    Raised when tests fail or quality checks don't pass.
    """

    def __init__(self, message: str, test_results: dict[str, Any] | None = None) -> None:
        """Initialize the exception.

        Args:
            message: The error message.
            test_results: Optional test results summary.
        """
        super().__init__(message, {"test_results": test_results})
        self.test_results = test_results


class PublishFailedError(WorkflowError):
    """Publish phase failed."""

    def __init__(self, message: str, platform: str | None = None) -> None:
        """Initialize the exception.

        Args:
            message: The error message.
            platform: The platform that failed (e.g., "itch.io").
        """
        super().__init__(message, {"platform": platform})
        self.platform = platform


class StateError(WorkflowError):
    """State persistence error.

    Raised when saving or loading state fails.
    """

    pass


class StateNotFoundError(StateError):
    """Requested state was not found."""

    def __init__(self, state_id: str) -> None:
        """Initialize the exception.

        Args:
            state_id: The ID of the state that wasn't found.
        """
        self.state_id = state_id
        super().__init__(f"State not found: {state_id}", {"state_id": state_id})


class AgentError(WorkflowError):
    """Error during agent execution."""

    def __init__(self, agent_name: str, message: str, cause: Exception | None = None) -> None:
        """Initialize the exception.

        Args:
            agent_name: The name of the agent that failed.
            message: The error message.
            cause: The underlying exception if any.
        """
        self.agent_name = agent_name
        self.cause = cause
        super().__init__(
            f"Agent '{agent_name}' failed: {message}",
            {"agent_name": agent_name, "cause": str(cause) if cause else None},
        )
