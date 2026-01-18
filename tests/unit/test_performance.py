"""Unit tests for performance metrics and hook.

Tests the performance tracking infrastructure:
- TimingRecord creation and statistics
- PhaseMetrics tracking
- PerformanceMetrics aggregation
- Timer context manager
- PerformanceHook integration
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime
from typing import TYPE_CHECKING

import pytest

from game_workflow.hooks.performance import (
    PerformanceHook,
    PerformanceMetrics,
    PhaseMetrics,
    Timer,
    TimingRecord,
    timed_operation,
)

if TYPE_CHECKING:
    from pathlib import Path


class TestTimingRecord:
    """Tests for TimingRecord dataclass."""

    def test_create_from_timestamps(self) -> None:
        """Test creating a timing record from timestamps."""
        start = 1000.0
        end = 1500.0

        record = TimingRecord.from_timestamps(
            name="test_operation",
            start=start,
            end=end,
        )

        assert record.name == "test_operation"
        assert record.start_time == 1000.0
        assert record.end_time == 1500.0
        assert record.duration_ms == 500000.0  # (1500-1000) * 1000
        assert record.metadata == {}

    def test_create_with_metadata(self) -> None:
        """Test creating a timing record with metadata."""
        record = TimingRecord.from_timestamps(
            name="api_call",
            start=0.0,
            end=0.1,
            metadata={"tokens": 100, "model": "test"},
        )

        assert record.metadata["tokens"] == 100
        assert record.metadata["model"] == "test"

    def test_duration_calculation(self) -> None:
        """Test that duration is calculated in milliseconds."""
        # 0.5 seconds should be 500ms
        record = TimingRecord.from_timestamps(
            name="test",
            start=0.0,
            end=0.5,
        )

        assert record.duration_ms == 500.0


class TestPhaseMetrics:
    """Tests for PhaseMetrics dataclass."""

    def test_initialization(self) -> None:
        """Test PhaseMetrics default values."""
        metrics = PhaseMetrics(phase="design")

        assert metrics.phase == "design"
        assert metrics.start_time is None
        assert metrics.end_time is None
        assert metrics.duration_ms == 0.0
        assert metrics.api_calls == 0
        assert metrics.api_call_duration_ms == 0.0
        assert metrics.state_saves == 0
        assert metrics.errors == 0
        assert metrics.retries == 0
        assert metrics.timings == []

    def test_add_timing(self) -> None:
        """Test adding timing records to phase metrics."""
        metrics = PhaseMetrics(phase="build")

        record1 = TimingRecord.from_timestamps("op1", 0.0, 0.1)
        record2 = TimingRecord.from_timestamps("op2", 0.1, 0.3)

        metrics.add_timing(record1)
        metrics.add_timing(record2)

        assert len(metrics.timings) == 2
        assert metrics.timings[0].name == "op1"
        assert metrics.timings[1].name == "op2"

    def test_get_timing_stats_empty(self) -> None:
        """Test timing stats with no matching records."""
        metrics = PhaseMetrics(phase="qa")

        stats = metrics.get_timing_stats("nonexistent")

        assert stats["count"] == 0
        assert stats["total_ms"] == 0.0
        assert stats["min_ms"] == 0.0
        assert stats["max_ms"] == 0.0

    def test_get_timing_stats(self) -> None:
        """Test timing statistics calculation."""
        metrics = PhaseMetrics(phase="build")

        # Add multiple timings with same name
        for i in range(5):
            # Durations: 100ms, 200ms, 300ms, 400ms, 500ms
            record = TimingRecord.from_timestamps("api_call", 0.0, (i + 1) * 0.1)
            metrics.add_timing(record)

        stats = metrics.get_timing_stats("api_call")

        assert stats["count"] == 5
        assert stats["total_ms"] == pytest.approx(1500.0)  # 100+200+300+400+500
        assert stats["min_ms"] == pytest.approx(100.0)
        assert stats["max_ms"] == pytest.approx(500.0)
        assert stats["mean_ms"] == pytest.approx(300.0)
        assert stats["median_ms"] == pytest.approx(300.0)

    def test_get_timing_stats_filters_by_name(self) -> None:
        """Test that timing stats filter by operation name."""
        metrics = PhaseMetrics(phase="build")

        metrics.add_timing(TimingRecord.from_timestamps("api_call", 0.0, 0.1))
        metrics.add_timing(TimingRecord.from_timestamps("file_write", 0.0, 0.2))
        metrics.add_timing(TimingRecord.from_timestamps("api_call", 0.0, 0.3))

        api_stats = metrics.get_timing_stats("api_call")
        file_stats = metrics.get_timing_stats("file_write")

        assert api_stats["count"] == 2
        assert file_stats["count"] == 1


class TestPerformanceMetrics:
    """Tests for PerformanceMetrics dataclass."""

    def test_initialization(self) -> None:
        """Test PerformanceMetrics default values."""
        metrics = PerformanceMetrics(workflow_id="test_123")

        assert metrics.workflow_id == "test_123"
        assert metrics.started_at is not None
        assert metrics.completed_at is None
        assert metrics.total_duration_ms == 0.0
        assert metrics.phases == {}

    def test_get_or_create_phase_creates_new(self) -> None:
        """Test that get_or_create_phase creates new PhaseMetrics."""
        metrics = PerformanceMetrics(workflow_id="test")

        phase = metrics.get_or_create_phase("design")

        assert "design" in metrics.phases
        assert phase.phase == "design"

    def test_get_or_create_phase_returns_existing(self) -> None:
        """Test that get_or_create_phase returns existing PhaseMetrics."""
        metrics = PerformanceMetrics(workflow_id="test")

        phase1 = metrics.get_or_create_phase("design")
        phase1.api_calls = 5

        phase2 = metrics.get_or_create_phase("design")

        assert phase1 is phase2
        assert phase2.api_calls == 5

    def test_complete(self) -> None:
        """Test completing metrics and calculating duration."""
        metrics = PerformanceMetrics(workflow_id="test")
        original_start = metrics.started_at

        # Small delay to ensure measurable duration
        time.sleep(0.01)

        metrics.complete()

        assert metrics.completed_at is not None
        assert metrics.completed_at > original_start
        assert metrics.total_duration_ms > 0

    def test_get_summary(self) -> None:
        """Test summary generation."""
        metrics = PerformanceMetrics(workflow_id="test")

        # Add phase data
        design = metrics.get_or_create_phase("design")
        design.duration_ms = 1000.0
        design.api_calls = 3
        design.api_call_duration_ms = 600.0
        design.state_saves = 2
        design.state_save_duration_ms = 50.0
        design.errors = 1
        design.retries = 1

        build = metrics.get_or_create_phase("build")
        build.duration_ms = 2000.0
        build.api_calls = 5
        build.api_call_duration_ms = 1000.0

        metrics.total_duration_ms = 3000.0

        summary = metrics.get_summary()

        assert summary["total_duration_ms"] == 3000.0
        assert summary["total_duration_sec"] == 3.0
        assert summary["phase_count"] == 2
        assert summary["total_api_calls"] == 8
        assert summary["total_api_duration_ms"] == 1600.0
        assert summary["avg_api_call_ms"] == 200.0
        assert summary["total_state_saves"] == 2
        assert summary["total_errors"] == 1
        assert summary["total_retries"] == 1
        assert summary["slowest_phase"] == "build"
        assert summary["slowest_phase_duration_ms"] == 2000.0

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        metrics = PerformanceMetrics(workflow_id="test_workflow")

        phase = metrics.get_or_create_phase("design")
        phase.duration_ms = 500.0
        phase.api_calls = 2

        result = metrics.to_dict()

        assert result["workflow_id"] == "test_workflow"
        assert "started_at" in result
        assert "phases" in result
        assert "design" in result["phases"]
        assert result["phases"]["design"]["api_calls"] == 2
        assert "summary" in result

    def test_generate_report(self) -> None:
        """Test report generation."""
        metrics = PerformanceMetrics(workflow_id="test_report")

        design = metrics.get_or_create_phase("design")
        design.duration_ms = 1000.0
        design.api_calls = 2
        design.api_call_duration_ms = 400.0

        metrics.total_duration_ms = 1000.0
        metrics.complete()

        report = metrics.generate_report()

        assert "WORKFLOW PERFORMANCE REPORT" in report
        assert "test_report" in report
        assert "design" in report
        assert "API CALLS" in report
        assert "Total Calls: 2" in report

    def test_save(self, tmp_path: Path) -> None:
        """Test saving metrics to file."""
        metrics = PerformanceMetrics(workflow_id="save_test")

        phase = metrics.get_or_create_phase("init")
        phase.duration_ms = 100.0

        metrics.complete()

        output_path = tmp_path / "metrics.json"
        metrics.save(output_path)

        assert output_path.exists()

        import json

        with output_path.open() as f:
            data = json.load(f)

        assert data["workflow_id"] == "save_test"
        assert "init" in data["phases"]


class TestTimer:
    """Tests for Timer context manager."""

    def test_basic_timing(self) -> None:
        """Test basic timer functionality."""
        timer = Timer("test_op")

        with timer:
            time.sleep(0.01)

        assert timer.duration_ms >= 10  # At least 10ms
        assert timer.start_time > 0
        assert timer.end_time > timer.start_time

    def test_timer_name(self) -> None:
        """Test timer name is preserved."""
        timer = Timer("custom_name")

        with timer:
            pass

        assert timer.name == "custom_name"

    def test_add_metadata(self) -> None:
        """Test adding metadata to timer."""
        timer = Timer("api_call")

        with timer:
            timer.add_metadata("response_size", 1024)
            timer.add_metadata("status_code", 200)

        record = timer.to_record()

        assert record.metadata["response_size"] == 1024
        assert record.metadata["status_code"] == 200

    def test_to_record(self) -> None:
        """Test converting timer to TimingRecord."""
        timer = Timer("conversion_test")

        with timer:
            time.sleep(0.01)

        record = timer.to_record()

        assert isinstance(record, TimingRecord)
        assert record.name == "conversion_test"
        assert record.duration_ms >= 10


class TestTimedOperation:
    """Tests for timed_operation context manager."""

    def test_basic_usage(self) -> None:
        """Test basic timed_operation usage."""
        with timed_operation("test_op") as timer:
            time.sleep(0.01)

        assert timer.duration_ms >= 10

    def test_yields_timer(self) -> None:
        """Test that timed_operation yields a Timer."""
        with timed_operation("test") as timer:
            assert isinstance(timer, Timer)

    def test_metadata_in_context(self) -> None:
        """Test adding metadata within context."""
        with timed_operation("api_call") as timer:
            timer.add_metadata("tokens", 150)

        record = timer.to_record()
        assert record.metadata["tokens"] == 150


class TestPerformanceHook:
    """Tests for PerformanceHook class."""

    @pytest.fixture
    def hook(self) -> PerformanceHook:
        """Create a performance hook for testing."""
        return PerformanceHook(workflow_id="test_workflow")

    @pytest.mark.asyncio
    async def test_on_phase_start(self, hook: PerformanceHook) -> None:
        """Test phase start recording."""
        await hook.on_phase_start("design", {"prompt": "test"})

        assert hook._current_phase == "design"
        assert "design" in hook._phase_start_times
        assert "design" in hook.metrics.phases

        phase = hook.metrics.phases["design"]
        assert phase.start_time is not None

    @pytest.mark.asyncio
    async def test_on_phase_complete(self, hook: PerformanceHook) -> None:
        """Test phase completion recording."""
        await hook.on_phase_start("design")

        # Small delay to ensure measurable duration
        await asyncio.sleep(0.01)

        await hook.on_phase_complete("design", {"status": "success"})

        phase = hook.metrics.phases["design"]
        assert phase.end_time is not None
        assert phase.duration_ms > 0

    @pytest.mark.asyncio
    async def test_on_error(self, hook: PerformanceHook) -> None:
        """Test error recording."""
        await hook.on_phase_start("build")

        await hook.on_error(
            ValueError("Test error"),
            context={"phase": "build"},
        )

        phase = hook.metrics.phases["build"]
        assert phase.errors == 1

    @pytest.mark.asyncio
    async def test_on_error_uses_current_phase(self, hook: PerformanceHook) -> None:
        """Test that on_error uses current phase when not in context."""
        await hook.on_phase_start("qa")

        await hook.on_error(RuntimeError("Test"), context={})

        phase = hook.metrics.phases["qa"]
        assert phase.errors == 1

    def test_record_api_call(self, hook: PerformanceHook) -> None:
        """Test API call recording."""
        hook._current_phase = "design"
        hook.metrics.get_or_create_phase("design")

        hook.record_api_call(150.0)
        hook.record_api_call(200.0)

        phase = hook.metrics.phases["design"]
        assert phase.api_calls == 2
        assert phase.api_call_duration_ms == 350.0

    def test_record_api_call_with_explicit_phase(self, hook: PerformanceHook) -> None:
        """Test API call recording with explicit phase."""
        hook.metrics.get_or_create_phase("build")

        hook.record_api_call(100.0, phase="build")

        phase = hook.metrics.phases["build"]
        assert phase.api_calls == 1

    def test_record_state_save(self, hook: PerformanceHook) -> None:
        """Test state save recording."""
        hook._current_phase = "design"
        hook.metrics.get_or_create_phase("design")

        hook.record_state_save(25.0)
        hook.record_state_save(30.0)

        phase = hook.metrics.phases["design"]
        assert phase.state_saves == 2
        assert phase.state_save_duration_ms == 55.0

    def test_record_retry(self, hook: PerformanceHook) -> None:
        """Test retry recording."""
        hook._current_phase = "build"
        hook.metrics.get_or_create_phase("build")

        hook.record_retry()
        hook.record_retry()

        phase = hook.metrics.phases["build"]
        assert phase.retries == 2

    def test_add_timing(self, hook: PerformanceHook) -> None:
        """Test adding timing records."""
        hook._current_phase = "qa"
        hook.metrics.get_or_create_phase("qa")

        record = TimingRecord.from_timestamps("test_run", 0.0, 0.5)
        hook.add_timing(record)

        phase = hook.metrics.phases["qa"]
        assert len(phase.timings) == 1
        assert phase.timings[0].name == "test_run"

    def test_add_timing_to_global_when_no_phase(self, hook: PerformanceHook) -> None:
        """Test that timings go to global when no current phase."""
        record = TimingRecord.from_timestamps("global_op", 0.0, 0.1)
        hook.add_timing(record)

        assert len(hook.metrics.global_timings) == 1
        assert hook.metrics.global_timings[0].name == "global_op"

    def test_complete(self, hook: PerformanceHook) -> None:
        """Test completing metrics collection."""
        hook._current_phase = "design"
        hook.metrics.get_or_create_phase("design")

        metrics = hook.complete()

        assert metrics.completed_at is not None
        assert metrics.total_duration_ms > 0

    def test_get_metrics(self, hook: PerformanceHook) -> None:
        """Test getting metrics without completing."""
        hook._current_phase = "init"
        hook.metrics.get_or_create_phase("init")

        metrics = hook.get_metrics()

        assert metrics.completed_at is None
        assert metrics is hook.metrics

    @pytest.mark.asyncio
    async def test_full_workflow_simulation(self, hook: PerformanceHook) -> None:
        """Test simulating a full workflow with metrics."""
        # Simulate INIT phase
        await hook.on_phase_start("init")
        hook.record_state_save(10.0)
        await asyncio.sleep(0.005)
        await hook.on_phase_complete("init")

        # Simulate DESIGN phase
        await hook.on_phase_start("design")
        hook.record_api_call(500.0)
        hook.record_api_call(300.0)
        hook.record_state_save(15.0)
        await asyncio.sleep(0.01)
        await hook.on_phase_complete("design")

        # Simulate BUILD phase with error and retry
        await hook.on_phase_start("build")
        hook.record_api_call(1000.0)
        await hook.on_error(RuntimeError("Build failed"), {"phase": "build"})
        hook.record_retry()
        hook.record_api_call(800.0)
        await asyncio.sleep(0.01)
        await hook.on_phase_complete("build")

        # Complete metrics
        metrics = hook.complete()

        # Verify metrics
        assert len(metrics.phases) == 3

        summary = metrics.get_summary()
        assert summary["total_api_calls"] == 4
        assert summary["total_state_saves"] == 2
        assert summary["total_errors"] == 1
        assert summary["total_retries"] == 1

        # Generate report
        report = metrics.generate_report()
        assert "init" in report
        assert "design" in report
        assert "build" in report


class TestPerformanceIntegration:
    """Integration tests for performance metrics with workflow patterns."""

    @pytest.mark.asyncio
    async def test_multiple_phases_tracked(self) -> None:
        """Test that multiple phases are tracked correctly."""
        hook = PerformanceHook(workflow_id="multi_phase_test")

        phases = ["init", "design", "build", "qa", "publish"]

        for phase in phases:
            await hook.on_phase_start(phase)
            await asyncio.sleep(0.001)
            await hook.on_phase_complete(phase)

        metrics = hook.complete()

        assert len(metrics.phases) == 5
        for phase in phases:
            assert phase in metrics.phases
            assert metrics.phases[phase].duration_ms > 0

    @pytest.mark.asyncio
    async def test_api_call_distribution(self) -> None:
        """Test tracking API calls across phases."""
        hook = PerformanceHook(workflow_id="api_test")

        # Design phase - 2 API calls
        await hook.on_phase_start("design")
        hook.record_api_call(200.0)
        hook.record_api_call(300.0)
        await hook.on_phase_complete("design")

        # Build phase - 3 API calls
        await hook.on_phase_start("build")
        hook.record_api_call(500.0)
        hook.record_api_call(600.0)
        hook.record_api_call(400.0)
        await hook.on_phase_complete("build")

        metrics = hook.complete()

        assert metrics.phases["design"].api_calls == 2
        assert metrics.phases["design"].api_call_duration_ms == 500.0
        assert metrics.phases["build"].api_calls == 3
        assert metrics.phases["build"].api_call_duration_ms == 1500.0

        summary = metrics.get_summary()
        assert summary["total_api_calls"] == 5
        assert summary["avg_api_call_ms"] == 400.0

    def test_timing_record_accumulation(self) -> None:
        """Test that timing records accumulate correctly."""
        hook = PerformanceHook(workflow_id="timing_test")
        hook._current_phase = "build"
        hook.metrics.get_or_create_phase("build")

        # Add various timings
        for i in range(10):
            with timed_operation(f"step_{i % 3}") as timer:
                time.sleep(0.001)
            hook.add_timing(timer.to_record())

        phase = hook.metrics.phases["build"]
        assert len(phase.timings) == 10

        # Check stats for repeated operations
        step_0_stats = phase.get_timing_stats("step_0")
        assert step_0_stats["count"] == 4  # 0, 3, 6, 9 -> 4 occurrences

    def test_metrics_serialization_roundtrip(self, tmp_path: Path) -> None:
        """Test that metrics can be saved and contain expected data."""
        hook = PerformanceHook(workflow_id="serialize_test")
        hook._current_phase = "design"

        phase = hook.metrics.get_or_create_phase("design")
        phase.start_time = datetime.now()
        phase.duration_ms = 1500.0
        phase.api_calls = 3
        phase.api_call_duration_ms = 900.0

        hook.metrics.complete()

        # Save to file
        output_path = tmp_path / "test_metrics.json"
        hook.metrics.save(output_path)

        # Load and verify
        import json

        with output_path.open() as f:
            data = json.load(f)

        assert data["workflow_id"] == "serialize_test"
        assert data["phases"]["design"]["api_calls"] == 3
        assert data["summary"]["total_api_calls"] == 3
