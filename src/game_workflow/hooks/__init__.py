"""Hooks for workflow events.

This module contains hooks that respond to workflow events:
- SlackApprovalHook: Human approval gates via Slack
- CheckpointHook: State checkpointing
- LoggingHook: Action logging
- PerformanceHook: Performance metrics collection

Hooks follow a common protocol and can be composed to add
multiple behaviors to the workflow orchestrator.
"""

from game_workflow.hooks.checkpoint import CheckpointHook
from game_workflow.hooks.logging import JSONFormatter, LoggingHook, setup_logging
from game_workflow.hooks.performance import (
    PerformanceHook,
    PerformanceMetrics,
    PhaseMetrics,
    Timer,
    TimingRecord,
    timed_operation,
)
from game_workflow.hooks.slack_approval import (
    ApprovalRequest,
    ApprovalStatus,
    SlackApprovalHook,
    SlackClient,
    SlackMessage,
)

__all__ = [
    "ApprovalRequest",
    "ApprovalStatus",
    "CheckpointHook",
    "JSONFormatter",
    "LoggingHook",
    "PerformanceHook",
    "PerformanceMetrics",
    "PhaseMetrics",
    "SlackApprovalHook",
    "SlackClient",
    "SlackMessage",
    "Timer",
    "TimingRecord",
    "setup_logging",
    "timed_operation",
]
