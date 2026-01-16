"""Custom exceptions for workflow errors.

This module defines the exception hierarchy for workflow-related errors.
"""


class WorkflowError(Exception):
    """Base exception for workflow errors."""

    pass


class ApprovalTimeoutError(WorkflowError):
    """Human didn't respond to approval request in time."""

    pass


class BuildFailedError(WorkflowError):
    """Game build failed."""

    pass


class DesignFailedError(WorkflowError):
    """Design phase failed."""

    pass


class QAFailedError(WorkflowError):
    """QA phase failed."""

    pass


class PublishFailedError(WorkflowError):
    """Publish phase failed."""

    pass


class StateError(WorkflowError):
    """State persistence error."""

    pass
