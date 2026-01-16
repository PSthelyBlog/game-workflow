"""Hooks for workflow events.

This module contains hooks that respond to workflow events:
- SlackApprovalHook: Human approval gates via Slack
- CheckpointHook: State checkpointing
- LoggingHook: Action logging

Hooks follow a common protocol and can be composed to add
multiple behaviors to the workflow orchestrator.
"""

from game_workflow.hooks.checkpoint import CheckpointHook
from game_workflow.hooks.logging import JSONFormatter, LoggingHook, setup_logging
from game_workflow.hooks.slack_approval import SlackApprovalHook

__all__ = [
    "CheckpointHook",
    "JSONFormatter",
    "LoggingHook",
    "SlackApprovalHook",
    "setup_logging",
]
