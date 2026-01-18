"""Performance metrics tracking for workflow execution.

This module provides performance monitoring and optimization support:
- PerformanceMetrics: Data model for timing and resource metrics
- PerformanceHook: Collects metrics during workflow execution
- Timer: Context manager for timing operations
"""

from __future__ import annotations

import logging
import statistics
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

logger = logging.getLogger("game_workflow.hooks.performance")


@dataclass
class TimingRecord:
    """Record of a single timed operation."""

    name: str
    start_time: float
    end_time: float
    duration_ms: float
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_timestamps(
        cls,
        name: str,
        start: float,
        end: float,
        metadata: dict[str, Any] | None = None,
    ) -> TimingRecord:
        """Create a timing record from timestamps.

        Args:
            name: Name of the operation.
            start: Start timestamp (from time.perf_counter()).
            end: End timestamp (from time.perf_counter()).
            metadata: Optional additional metadata.

        Returns:
            A TimingRecord instance.
        """
        duration_ms = (end - start) * 1000
        return cls(
            name=name,
            start_time=start,
            end_time=end,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )


@dataclass
class PhaseMetrics:
    """Metrics for a single workflow phase."""

    phase: str
    start_time: datetime | None = None
    end_time: datetime | None = None
    duration_ms: float = 0.0
    api_calls: int = 0
    api_call_duration_ms: float = 0.0
    state_saves: int = 0
    state_save_duration_ms: float = 0.0
    errors: int = 0
    retries: int = 0
    timings: list[TimingRecord] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_timing(self, record: TimingRecord) -> None:
        """Add a timing record to this phase.

        Args:
            record: The timing record to add.
        """
        self.timings.append(record)

    def get_timing_stats(self, name: str) -> dict[str, float]:
        """Get statistics for timings with a specific name.

        Args:
            name: The timing name to filter by.

        Returns:
            Dictionary with count, total, min, max, mean, median.
        """
        durations = [t.duration_ms for t in self.timings if t.name == name]

        if not durations:
            return {
                "count": 0,
                "total_ms": 0.0,
                "min_ms": 0.0,
                "max_ms": 0.0,
                "mean_ms": 0.0,
                "median_ms": 0.0,
            }

        return {
            "count": len(durations),
            "total_ms": sum(durations),
            "min_ms": min(durations),
            "max_ms": max(durations),
            "mean_ms": statistics.mean(durations),
            "median_ms": statistics.median(durations),
        }


@dataclass
class PerformanceMetrics:
    """Complete performance metrics for a workflow run."""

    workflow_id: str
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    total_duration_ms: float = 0.0
    phases: dict[str, PhaseMetrics] = field(default_factory=dict)
    global_timings: list[TimingRecord] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_or_create_phase(self, phase: str) -> PhaseMetrics:
        """Get or create metrics for a phase.

        Args:
            phase: The phase name.

        Returns:
            PhaseMetrics for the phase.
        """
        if phase not in self.phases:
            self.phases[phase] = PhaseMetrics(phase=phase)
        return self.phases[phase]

    def complete(self) -> None:
        """Mark the workflow as complete and calculate total duration."""
        self.completed_at = datetime.now()
        if self.started_at:
            delta = self.completed_at - self.started_at
            self.total_duration_ms = delta.total_seconds() * 1000

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to a dictionary for serialization.

        Returns:
            Dictionary representation of all metrics.
        """
        return {
            "workflow_id": self.workflow_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_duration_ms": self.total_duration_ms,
            "phases": {
                name: {
                    "phase": metrics.phase,
                    "start_time": metrics.start_time.isoformat() if metrics.start_time else None,
                    "end_time": metrics.end_time.isoformat() if metrics.end_time else None,
                    "duration_ms": metrics.duration_ms,
                    "api_calls": metrics.api_calls,
                    "api_call_duration_ms": metrics.api_call_duration_ms,
                    "state_saves": metrics.state_saves,
                    "state_save_duration_ms": metrics.state_save_duration_ms,
                    "errors": metrics.errors,
                    "retries": metrics.retries,
                    "timing_stats": {
                        timing_name: metrics.get_timing_stats(timing_name)
                        for timing_name in {t.name for t in metrics.timings}
                    },
                    "metadata": metrics.metadata,
                }
                for name, metrics in self.phases.items()
            },
            "summary": self.get_summary(),
            "metadata": self.metadata,
        }

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of performance metrics.

        Returns:
            Summary dictionary with key performance indicators.
        """
        total_api_calls = sum(p.api_calls for p in self.phases.values())
        total_api_duration = sum(p.api_call_duration_ms for p in self.phases.values())
        total_state_saves = sum(p.state_saves for p in self.phases.values())
        total_state_duration = sum(p.state_save_duration_ms for p in self.phases.values())
        total_errors = sum(p.errors for p in self.phases.values())
        total_retries = sum(p.retries for p in self.phases.values())

        phase_durations = {
            name: metrics.duration_ms
            for name, metrics in self.phases.items()
            if metrics.duration_ms > 0
        }

        slowest_phase = (
            max(phase_durations.items(), key=lambda x: x[1]) if phase_durations else None
        )

        return {
            "total_duration_ms": self.total_duration_ms,
            "total_duration_sec": self.total_duration_ms / 1000,
            "phase_count": len(self.phases),
            "total_api_calls": total_api_calls,
            "total_api_duration_ms": total_api_duration,
            "avg_api_call_ms": total_api_duration / total_api_calls if total_api_calls > 0 else 0,
            "total_state_saves": total_state_saves,
            "total_state_duration_ms": total_state_duration,
            "avg_state_save_ms": total_state_duration / total_state_saves
            if total_state_saves > 0
            else 0,
            "total_errors": total_errors,
            "total_retries": total_retries,
            "slowest_phase": slowest_phase[0] if slowest_phase else None,
            "slowest_phase_duration_ms": slowest_phase[1] if slowest_phase else 0,
            "phase_durations_ms": phase_durations,
        }

    def generate_report(self) -> str:
        """Generate a human-readable performance report.

        Returns:
            Formatted report string.
        """
        summary = self.get_summary()
        lines = [
            "=" * 60,
            "WORKFLOW PERFORMANCE REPORT",
            "=" * 60,
            f"Workflow ID: {self.workflow_id}",
            f"Started: {self.started_at.isoformat() if self.started_at else 'N/A'}",
            f"Completed: {self.completed_at.isoformat() if self.completed_at else 'N/A'}",
            "",
            "TIMING SUMMARY",
            "-" * 40,
            f"Total Duration: {summary['total_duration_sec']:.2f}s ({summary['total_duration_ms']:.0f}ms)",
            "",
            "PHASE BREAKDOWN",
            "-" * 40,
        ]

        for name, duration in sorted(
            summary["phase_durations_ms"].items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            pct = (
                (duration / summary["total_duration_ms"] * 100)
                if summary["total_duration_ms"] > 0
                else 0
            )
            lines.append(f"  {name}: {duration:.0f}ms ({pct:.1f}%)")

        lines.extend(
            [
                "",
                "API CALLS",
                "-" * 40,
                f"Total Calls: {summary['total_api_calls']}",
                f"Total Duration: {summary['total_api_duration_ms']:.0f}ms",
                f"Average per Call: {summary['avg_api_call_ms']:.0f}ms",
                "",
                "STATE PERSISTENCE",
                "-" * 40,
                f"Total Saves: {summary['total_state_saves']}",
                f"Total Duration: {summary['total_state_duration_ms']:.0f}ms",
                f"Average per Save: {summary['avg_state_save_ms']:.0f}ms",
                "",
                "ERRORS & RETRIES",
                "-" * 40,
                f"Errors: {summary['total_errors']}",
                f"Retries: {summary['total_retries']}",
                "",
                "=" * 60,
            ]
        )

        return "\n".join(lines)

    def save(self, path: Path) -> None:
        """Save metrics to a JSON file.

        Args:
            path: Path to save the metrics file.
        """
        import json

        with path.open("w") as f:
            json.dump(self.to_dict(), f, indent=2)


class Timer:
    """Context manager for timing operations."""

    def __init__(self, name: str = "operation") -> None:
        """Initialize the timer.

        Args:
            name: Name of the operation being timed.
        """
        self.name = name
        self.start_time: float = 0
        self.end_time: float = 0
        self.duration_ms: float = 0
        self._metadata: dict[str, Any] = {}

    def __enter__(self) -> Timer:
        """Start timing."""
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args: object) -> None:
        """Stop timing and calculate duration."""
        self.end_time = time.perf_counter()
        self.duration_ms = (self.end_time - self.start_time) * 1000

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the timing.

        Args:
            key: Metadata key.
            value: Metadata value.
        """
        self._metadata[key] = value

    def to_record(self) -> TimingRecord:
        """Convert to a TimingRecord.

        Returns:
            TimingRecord with this timer's data.
        """
        return TimingRecord.from_timestamps(
            name=self.name,
            start=self.start_time,
            end=self.end_time,
            metadata=self._metadata,
        )


@contextmanager
def timed_operation(name: str) -> Iterator[Timer]:
    """Context manager for timing an operation.

    Args:
        name: Name of the operation.

    Yields:
        Timer instance.

    Example:
        with timed_operation("api_call") as timer:
            result = make_api_call()
            timer.add_metadata("tokens", result.tokens)
    """
    timer = Timer(name)
    with timer:
        yield timer


class PerformanceHook:
    """Hook for collecting performance metrics during workflow execution.

    This hook implements the WorkflowHook protocol and collects
    timing and resource metrics during workflow execution.
    """

    def __init__(self, workflow_id: str) -> None:
        """Initialize the performance hook.

        Args:
            workflow_id: ID of the workflow being monitored.
        """
        self.metrics = PerformanceMetrics(workflow_id=workflow_id)
        self._phase_start_times: dict[str, float] = {}
        self._current_phase: str | None = None

    async def on_phase_start(
        self,
        phase: str,
        context: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> None:
        """Record phase start time.

        Args:
            phase: The phase that is starting.
            context: Additional context (unused).
        """
        self._current_phase = phase
        self._phase_start_times[phase] = time.perf_counter()

        phase_metrics = self.metrics.get_or_create_phase(phase)
        phase_metrics.start_time = datetime.now()

        logger.debug(f"Phase started: {phase}")

    async def on_phase_complete(
        self,
        phase: str,
        result: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> None:
        """Record phase completion and calculate duration.

        Args:
            phase: The phase that completed.
            result: Phase results (unused).
        """
        end_time = time.perf_counter()
        start_time = self._phase_start_times.get(phase, end_time)
        duration_ms = (end_time - start_time) * 1000

        phase_metrics = self.metrics.get_or_create_phase(phase)
        phase_metrics.end_time = datetime.now()
        phase_metrics.duration_ms = duration_ms

        logger.debug(f"Phase completed: {phase} ({duration_ms:.0f}ms)")

    async def on_error(
        self,
        error: Exception,  # noqa: ARG002
        context: dict[str, Any] | None = None,
    ) -> None:
        """Record error occurrence.

        Args:
            error: The error that occurred (unused, logged elsewhere).
            context: Error context with phase information.
        """
        phase = context.get("phase") if context else self._current_phase
        if phase:
            phase_metrics = self.metrics.get_or_create_phase(phase)
            phase_metrics.errors += 1

        logger.debug(f"Error recorded in phase: {phase}")

    def record_api_call(self, duration_ms: float, phase: str | None = None) -> None:
        """Record an API call.

        Args:
            duration_ms: Duration of the API call in milliseconds.
            phase: The phase this call belongs to (defaults to current).
        """
        target_phase = phase or self._current_phase
        if target_phase:
            phase_metrics = self.metrics.get_or_create_phase(target_phase)
            phase_metrics.api_calls += 1
            phase_metrics.api_call_duration_ms += duration_ms

    def record_state_save(self, duration_ms: float, phase: str | None = None) -> None:
        """Record a state save operation.

        Args:
            duration_ms: Duration of the save in milliseconds.
            phase: The phase this save belongs to (defaults to current).
        """
        target_phase = phase or self._current_phase
        if target_phase:
            phase_metrics = self.metrics.get_or_create_phase(target_phase)
            phase_metrics.state_saves += 1
            phase_metrics.state_save_duration_ms += duration_ms

    def record_retry(self, phase: str | None = None) -> None:
        """Record a retry attempt.

        Args:
            phase: The phase being retried (defaults to current).
        """
        target_phase = phase or self._current_phase
        if target_phase:
            phase_metrics = self.metrics.get_or_create_phase(target_phase)
            phase_metrics.retries += 1

    def add_timing(self, record: TimingRecord, phase: str | None = None) -> None:
        """Add a timing record.

        Args:
            record: The timing record to add.
            phase: The phase this timing belongs to (defaults to current).
        """
        target_phase = phase or self._current_phase
        if target_phase:
            phase_metrics = self.metrics.get_or_create_phase(target_phase)
            phase_metrics.add_timing(record)
        else:
            self.metrics.global_timings.append(record)

    def complete(self) -> PerformanceMetrics:
        """Complete metrics collection and return results.

        Returns:
            The complete performance metrics.
        """
        self.metrics.complete()
        return self.metrics

    def get_metrics(self) -> PerformanceMetrics:
        """Get the current metrics (without completing).

        Returns:
            Current performance metrics.
        """
        return self.metrics
