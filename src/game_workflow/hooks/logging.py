"""Logging hook for workflow actions.

This hook logs workflow events for debugging and monitoring.
"""

import logging
from typing import Any

logger = logging.getLogger("game_workflow")


class LoggingHook:
    """Hook for logging workflow events.

    Logs actions and events to console and file for
    debugging and audit purposes.
    """

    def __init__(self, log_level: str = "INFO") -> None:
        """Initialize the hook.

        Args:
            log_level: The logging level.
        """
        self.log_level = getattr(logging, log_level.upper())
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging handlers."""
        logger.setLevel(self.log_level)

        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(self.log_level)
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)

    async def on_phase_start(self, phase: str, context: dict[str, Any] | None = None) -> None:
        """Log phase start.

        Args:
            phase: The phase name.
            context: Additional context.
        """
        logger.info(f"Starting phase: {phase}")
        if context:
            logger.debug(f"Phase context: {context}")

    async def on_phase_complete(self, phase: str, result: dict[str, Any] | None = None) -> None:
        """Log phase completion.

        Args:
            phase: The phase name.
            result: Phase results.
        """
        logger.info(f"Completed phase: {phase}")
        if result:
            logger.debug(f"Phase result: {result}")

    async def on_error(self, error: Exception, context: dict[str, Any] | None = None) -> None:
        """Log an error.

        Args:
            error: The exception.
            context: Additional context.
        """
        logger.error(f"Error: {error}", exc_info=True)
        if context:
            logger.error(f"Error context: {context}")
