"""Base agent class for workflow agents.

This module provides the abstract base class that all workflow agents inherit from.
"""

from abc import ABC, abstractmethod
from typing import Any

# Default model for agents (Sonnet 4.5 for best balance)
DEFAULT_MODEL = "claude-sonnet-4-5-20250929"


class BaseAgent(ABC):
    """Abstract base class for workflow agents.

    All workflow agents (Design, Build, QA, Publish) inherit from this class
    and implement their specific logic.
    """

    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        """Initialize the agent.

        Args:
            model: The Claude model to use.
        """
        self.model = model

    @abstractmethod
    async def run(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Execute the agent's primary task.

        Args:
            *args: Agent-specific positional arguments.
            **kwargs: Agent-specific keyword arguments.

        Returns:
            Results from the agent's execution.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the agent's name."""
        raise NotImplementedError
