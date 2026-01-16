"""Logging hook for workflow actions.

This hook logs workflow events for debugging and monitoring.
Supports console output, file logging, and structured JSON logging.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import TYPE_CHECKING, Any

from game_workflow.config import get_settings

if TYPE_CHECKING:
    from pathlib import Path

# Main logger for game_workflow
logger = logging.getLogger("game_workflow")

# Flag to track if logging has been configured
_logging_configured = False


class JSONFormatter(logging.Formatter):
    """Formatter that outputs JSON-structured log records."""

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as JSON.

        Args:
            record: The log record to format.

        Returns:
            JSON-formatted log string.
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        for key in ["phase", "state_id", "context", "result"]:
            if hasattr(record, key):
                log_data[key] = getattr(record, key)

        return json.dumps(log_data)


def setup_logging(
    log_level: str = "INFO",
    log_dir: Path | None = None,
    json_format: bool = False,
) -> None:
    """Set up logging configuration.

    Configures both console and file logging handlers.

    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR).
        log_dir: Directory for log files. Defaults to settings.
        json_format: Use JSON format for file logs.
    """
    global _logging_configured

    if _logging_configured:
        return

    settings = get_settings()
    level = getattr(logging, log_level.upper(), logging.INFO)
    log_directory = log_dir or settings.workflow.log_dir

    # Configure root logger
    logger.setLevel(level)

    # Clear any existing handlers
    logger.handlers.clear()

    # Console handler with simple formatting
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler with rotating logs
    log_directory.mkdir(parents=True, exist_ok=True)
    log_file = log_directory / "workflow.log"

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
    )
    file_handler.setLevel(logging.DEBUG)  # Always log DEBUG to file

    if json_format:
        file_handler.setFormatter(JSONFormatter())
    else:
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)

    logger.addHandler(file_handler)

    _logging_configured = True
    logger.debug(
        "Logging configured", extra={"log_level": log_level, "log_dir": str(log_directory)}
    )


class LoggingHook:
    """Hook for logging workflow events.

    Logs actions and events to console and file for
    debugging and audit purposes.

    This hook integrates with the workflow orchestrator to log:
    - Phase transitions
    - Phase completions with results
    - Errors with context
    - Tool calls (when integrated with Agent SDK)
    """

    def __init__(
        self,
        log_level: str = "INFO",
        json_format: bool = False,
    ) -> None:
        """Initialize the hook.

        Args:
            log_level: The logging level.
            json_format: Use JSON format for file logs.
        """
        self.log_level = log_level
        self.json_format = json_format
        setup_logging(log_level=log_level, json_format=json_format)

    async def on_phase_start(self, phase: str, context: dict[str, Any] | None = None) -> None:
        """Log phase start.

        Args:
            phase: The phase name.
            context: Additional context.
        """
        extra: dict[str, Any] = {"phase": phase}
        if context:
            extra["context"] = context

        logger.info(f"▶ Starting phase: {phase}", extra=extra)

        if context:
            state_id = context.get("state_id", "unknown")
            logger.debug(f"  State ID: {state_id}", extra=extra)

    async def on_phase_complete(self, phase: str, result: dict[str, Any] | None = None) -> None:
        """Log phase completion.

        Args:
            phase: The phase name.
            result: Phase results.
        """
        extra: dict[str, Any] = {"phase": phase}
        if result:
            extra["result"] = result

        logger.info(f"✓ Completed phase: {phase}", extra=extra)

        if result:
            logger.debug(f"  Result: {result}", extra=extra)

    async def on_error(self, error: Exception, context: dict[str, Any] | None = None) -> None:
        """Log an error.

        Args:
            error: The exception.
            context: Additional context.
        """
        extra: dict[str, Any] = {}
        if context:
            extra["context"] = context

        logger.error(f"✗ Error: {error}", exc_info=True, extra=extra)

        if context:
            phase = context.get("phase", "unknown")
            state_id = context.get("state_id", "unknown")
            logger.error(f"  Phase: {phase}, State: {state_id}", extra=extra)

    async def on_tool_call(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_result: Any = None,
    ) -> None:
        """Log a tool call (for Agent SDK integration).

        Args:
            tool_name: The name of the tool called.
            tool_input: The input parameters.
            tool_result: The result if available.
        """
        logger.debug(f"Tool call: {tool_name}", extra={"tool_input": tool_input})

        if tool_result is not None:
            logger.debug(f"Tool result: {tool_name}", extra={"tool_result": str(tool_result)[:500]})

    async def on_approval_requested(self, gate: str, message: str) -> None:
        """Log an approval request.

        Args:
            gate: The approval gate name.
            message: The approval message.
        """
        logger.info(f"⏳ Approval requested: {gate}", extra={"gate": gate, "message": message})

    async def on_approval_received(
        self, gate: str, approved: bool, reason: str | None = None
    ) -> None:
        """Log an approval response.

        Args:
            gate: The approval gate name.
            approved: Whether it was approved.
            reason: Optional reason provided.
        """
        status = "approved" if approved else "rejected"
        icon = "✓" if approved else "✗"
        logger.info(
            f"{icon} Approval {status}: {gate}",
            extra={"gate": gate, "approved": approved, "reason": reason},
        )
