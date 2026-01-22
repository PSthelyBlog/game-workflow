"""Base agent class for workflow agents.

This module provides the abstract base class that all workflow agents inherit from.
It includes common functionality for logging, error handling, and Agent SDK integration.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from game_workflow.config import get_settings
from game_workflow.orchestrator.exceptions import AgentError

if TYPE_CHECKING:
    from game_workflow.orchestrator.state import WorkflowState

# Default model for agents (Sonnet 4.5 for best balance)
DEFAULT_MODEL = "claude-sonnet-4-5-20250929"


class BaseAgent(ABC):
    """Abstract base class for workflow agents.

    All workflow agents (Design, Build, QA, Publish) inherit from this class
    and implement their specific logic.

    Provides:
    - Common configuration and model setup
    - Logging integration
    - Error handling patterns
    - State context management
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        state: WorkflowState | None = None,
    ) -> None:
        """Initialize the agent.

        Args:
            model: The Claude model to use.
            state: The workflow state for context.
        """
        self.model = model
        self.state = state
        self._settings = get_settings()
        self._logger = logging.getLogger(f"game_workflow.agents.{self.name}")

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the agent's name.

        Returns:
            The unique name for this agent type.
        """
        raise NotImplementedError

    @property
    def api_key(self) -> str | None:
        """Get the Anthropic API key.

        Returns:
            The API key from settings.
        """
        return self._settings.anthropic_api_key

    def log_info(self, message: str, **kwargs: Any) -> None:
        """Log an info message.

        Args:
            message: The message to log.
            **kwargs: Additional context to include.
        """
        self._logger.info(message, extra=kwargs)

    def log_debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message.

        Args:
            message: The message to log.
            **kwargs: Additional context to include.
        """
        self._logger.debug(message, extra=kwargs)

    def log_error(self, message: str, exc: Exception | None = None, **kwargs: Any) -> None:
        """Log an error message.

        Args:
            message: The message to log.
            exc: Optional exception to include.
            **kwargs: Additional context to include.
        """
        self._logger.error(message, exc_info=exc, extra=kwargs)

    def _validate_config(self) -> None:
        """Validate configuration (API key no longer required).

        The Claude Agent SDK inherits authentication from the Claude Code CLI,
        so API key is optional. If set, a deprecation warning is logged.
        """
        import warnings

        if self.api_key:
            warnings.warn(
                "ANTHROPIC_API_KEY is set but not required. "
                "Claude Agent SDK inherits authentication from Claude Code CLI.",
                DeprecationWarning,
                stacklevel=3,
            )

    @abstractmethod
    async def run(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Execute the agent's primary task.

        Subclasses must implement this method to define the agent's
        specific behavior.

        Args:
            *args: Agent-specific positional arguments.
            **kwargs: Agent-specific keyword arguments.

        Returns:
            Results from the agent's execution. Should include at minimum:
                - status: "success" or "failed"
                - Any artifacts or outputs produced

        Raises:
            AgentError: If the agent execution fails.
        """
        raise NotImplementedError

    async def execute(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Execute the agent with error handling.

        This is a wrapper around run() that provides common error handling
        and logging. Agents should implement run() and callers should use
        this method.

        Args:
            *args: Arguments to pass to run().
            **kwargs: Keyword arguments to pass to run().

        Returns:
            Results from the agent's execution.

        Raises:
            AgentError: If the agent execution fails.
        """
        self.log_info(f"Starting {self.name} agent")

        try:
            self._validate_config()
            result = await self.run(*args, **kwargs)
            self.log_info(f"Completed {self.name} agent", status=result.get("status"))
            return result

        except AgentError:
            # Re-raise AgentError as-is
            raise

        except Exception as e:
            self.log_error("Agent failed with unexpected error", exc=e)
            raise AgentError(self.name, str(e), cause=e) from e

    def add_artifact(self, name: str, path: str) -> None:
        """Add an artifact to the workflow state.

        Args:
            name: The artifact name.
            path: The path to the artifact.
        """
        if self.state is not None:
            self.state.add_artifact(name, path)
            self.state.save()
            self.log_debug(f"Added artifact: {name} -> {path}")
