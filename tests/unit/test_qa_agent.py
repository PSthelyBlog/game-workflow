"""Tests for the QAAgent module."""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from game_workflow.agents.qa import (
    ConsoleMessage,
    DevServerManager,
    PlaywrightTester,
    QAAgent,
    QAReport,
    TestResult,
    TestSeverity,
    TestStatus,
)
from game_workflow.orchestrator.exceptions import AgentError, QAFailedError

if TYPE_CHECKING:
    from pathlib import Path


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def game_dir(tmp_path: Path) -> Path:
    """Create a temporary game directory with package.json."""
    game_path = tmp_path / "game"
    game_path.mkdir()
    (game_path / "package.json").write_text('{"name": "test-game", "scripts": {"dev": "vite"}}')
    (game_path / "index.html").write_text("<html><body></body></html>")
    return game_path


@pytest.fixture
def qa_report() -> QAReport:
    """Create a sample QA report."""
    return QAReport(
        game_title="Test Game",
        test_date=datetime.now().isoformat(),
    )


@pytest.fixture
def passed_test_result() -> TestResult:
    """Create a passed test result."""
    return TestResult(
        name="test_passed",
        status=TestStatus.PASSED,
        duration_ms=100.0,
        message="Test passed",
        severity=TestSeverity.MEDIUM,
    )


@pytest.fixture
def failed_test_result() -> TestResult:
    """Create a failed test result."""
    return TestResult(
        name="test_failed",
        status=TestStatus.FAILED,
        duration_ms=50.0,
        message="Test failed",
        details={"error": "Something went wrong"},
        severity=TestSeverity.HIGH,
    )


@pytest.fixture
def critical_failed_test() -> TestResult:
    """Create a critical failed test result."""
    return TestResult(
        name="test_critical_failure",
        status=TestStatus.FAILED,
        duration_ms=10.0,
        message="Critical failure",
        severity=TestSeverity.CRITICAL,
    )


# =============================================================================
# TestResult Tests
# =============================================================================


class TestTestResult:
    """Tests for TestResult dataclass."""

    def test_to_dict(self, passed_test_result: TestResult) -> None:
        """Test converting TestResult to dictionary."""
        result = passed_test_result.to_dict()

        assert result["name"] == "test_passed"
        assert result["status"] == "passed"
        assert result["duration_ms"] == 100.0
        assert result["message"] == "Test passed"
        assert result["severity"] == "medium"

    def test_to_dict_with_details(self, failed_test_result: TestResult) -> None:
        """Test converting TestResult with details to dictionary."""
        result = failed_test_result.to_dict()

        assert result["details"] == {"error": "Something went wrong"}
        assert result["severity"] == "high"

    def test_default_values(self) -> None:
        """Test TestResult with default values."""
        result = TestResult(name="test", status=TestStatus.PASSED)

        assert result.duration_ms == 0.0
        assert result.message == ""
        assert result.details == {}
        assert result.severity == TestSeverity.MEDIUM


# =============================================================================
# ConsoleMessage Tests
# =============================================================================


class TestConsoleMessage:
    """Tests for ConsoleMessage dataclass."""

    def test_to_dict(self) -> None:
        """Test converting ConsoleMessage to dictionary."""
        msg = ConsoleMessage(
            level="error",
            text="An error occurred",
            url="http://localhost:5173/main.js",
            line=42,
        )
        result = msg.to_dict()

        assert result["level"] == "error"
        assert result["text"] == "An error occurred"
        assert result["url"] == "http://localhost:5173/main.js"
        assert result["line"] == 42

    def test_default_values(self) -> None:
        """Test ConsoleMessage with default values."""
        msg = ConsoleMessage(level="log", text="Info message")

        assert msg.url == ""
        assert msg.line == 0


# =============================================================================
# QAReport Tests
# =============================================================================


class TestQAReport:
    """Tests for QAReport dataclass."""

    def test_add_result_passed(self, qa_report: QAReport, passed_test_result: TestResult) -> None:
        """Test adding a passed test result."""
        qa_report.add_result(passed_test_result)

        assert qa_report.total_tests == 1
        assert qa_report.passed_tests == 1
        assert qa_report.failed_tests == 0

    def test_add_result_failed(self, qa_report: QAReport, failed_test_result: TestResult) -> None:
        """Test adding a failed test result."""
        qa_report.add_result(failed_test_result)

        assert qa_report.total_tests == 1
        assert qa_report.passed_tests == 0
        assert qa_report.failed_tests == 1

    def test_add_result_skipped(self, qa_report: QAReport) -> None:
        """Test adding a skipped test result."""
        result = TestResult(name="skipped", status=TestStatus.SKIPPED)
        qa_report.add_result(result)

        assert qa_report.skipped_tests == 1

    def test_add_result_error(self, qa_report: QAReport) -> None:
        """Test adding an error test result."""
        result = TestResult(name="error", status=TestStatus.ERROR)
        qa_report.add_result(result)

        assert qa_report.error_tests == 1

    def test_success_rate(self, qa_report: QAReport, passed_test_result: TestResult) -> None:
        """Test calculating success rate."""
        qa_report.add_result(passed_test_result)
        qa_report.add_result(TestResult(name="failed", status=TestStatus.FAILED))

        assert qa_report.success_rate == 50.0

    def test_success_rate_zero_tests(self, qa_report: QAReport) -> None:
        """Test success rate with zero tests."""
        assert qa_report.success_rate == 0.0

    def test_has_critical_failures_true(
        self, qa_report: QAReport, critical_failed_test: TestResult
    ) -> None:
        """Test detecting critical failures."""
        qa_report.add_result(critical_failed_test)

        assert qa_report.has_critical_failures is True

    def test_has_critical_failures_false(
        self, qa_report: QAReport, passed_test_result: TestResult
    ) -> None:
        """Test no critical failures."""
        qa_report.add_result(passed_test_result)

        assert qa_report.has_critical_failures is False

    def test_add_recommendation(self, qa_report: QAReport) -> None:
        """Test adding recommendations."""
        qa_report.add_recommendation("Fix this issue")
        qa_report.add_recommendation("Fix another issue")
        qa_report.add_recommendation("Fix this issue")  # Duplicate

        assert len(qa_report.recommendations) == 2

    def test_determine_overall_status_passed(
        self, qa_report: QAReport, passed_test_result: TestResult
    ) -> None:
        """Test determining overall status as passed."""
        qa_report.add_result(passed_test_result)
        qa_report.determine_overall_status()

        assert qa_report.overall_status == "passed"

    def test_determine_overall_status_failed(
        self, qa_report: QAReport, critical_failed_test: TestResult
    ) -> None:
        """Test determining overall status as failed."""
        qa_report.add_result(critical_failed_test)
        qa_report.determine_overall_status()

        assert qa_report.overall_status == "failed"

    def test_determine_overall_status_needs_attention(
        self, qa_report: QAReport, failed_test_result: TestResult
    ) -> None:
        """Test determining overall status as needs_attention."""
        qa_report.add_result(failed_test_result)
        qa_report.determine_overall_status()

        assert qa_report.overall_status == "needs_attention"

    def test_determine_overall_status_incomplete(self, qa_report: QAReport) -> None:
        """Test determining overall status as incomplete."""
        qa_report.add_result(TestResult(name="error", status=TestStatus.ERROR))
        qa_report.determine_overall_status()

        assert qa_report.overall_status == "incomplete"

    def test_to_dict(self, qa_report: QAReport, passed_test_result: TestResult) -> None:
        """Test converting QAReport to dictionary."""
        qa_report.add_result(passed_test_result)
        qa_report.console_messages.append(ConsoleMessage(level="log", text="Test"))
        qa_report.performance_metrics = {"avg_fps": 60.0}
        qa_report.add_recommendation("Test recommendation")
        qa_report.determine_overall_status()

        result = qa_report.to_dict()

        assert result["game_title"] == "Test Game"
        assert result["summary"]["total_tests"] == 1
        assert result["summary"]["passed"] == 1
        assert result["summary"]["success_rate"] == 100.0
        assert len(result["test_results"]) == 1
        assert len(result["console_messages"]) == 1
        assert result["performance_metrics"]["avg_fps"] == 60.0
        assert len(result["recommendations"]) == 1

    def test_to_markdown(self, qa_report: QAReport) -> None:
        """Test generating markdown report."""
        qa_report.add_result(
            TestResult(name="passed_test", status=TestStatus.PASSED, message="All good")
        )
        qa_report.add_result(
            TestResult(
                name="failed_test",
                status=TestStatus.FAILED,
                message="Problem",
                severity=TestSeverity.HIGH,
            )
        )
        qa_report.performance_metrics = {"avg_fps": 60.0, "memory_mb": 50.0}
        qa_report.add_recommendation("Fix the issue")
        qa_report.determine_overall_status()

        markdown = qa_report.to_markdown()

        assert "# QA Report: Test Game" in markdown
        assert "## Summary" in markdown
        assert "## Failed Tests" in markdown
        assert "failed_test" in markdown
        assert "## Performance Metrics" in markdown
        assert "Average FPS" in markdown
        assert "## Recommendations" in markdown
        assert "Fix the issue" in markdown
        assert "## Passed Tests" in markdown
        assert "passed_test" in markdown


# =============================================================================
# DevServerManager Tests
# =============================================================================


class TestDevServerManager:
    """Tests for DevServerManager class."""

    def test_url_property(self, game_dir: Path) -> None:
        """Test the URL property."""
        manager = DevServerManager(game_dir, port=5173)
        assert manager.url == "http://localhost:5173"

    def test_url_custom_port(self, game_dir: Path) -> None:
        """Test the URL property with custom port."""
        manager = DevServerManager(game_dir, port=8080)
        assert manager.url == "http://localhost:8080"

    @patch("game_workflow.agents.qa.find_executable")
    async def test_start_npm_not_found(self, mock_find: MagicMock, game_dir: Path) -> None:
        """Test start fails when npm is not found."""
        mock_find.return_value = None
        manager = DevServerManager(game_dir)

        with pytest.raises(RuntimeError, match="npm not found"):
            await manager.start(timeout=1)

    def test_stop_no_process(self, game_dir: Path) -> None:
        """Test stop when no process is running."""
        manager = DevServerManager(game_dir)
        # Should not raise
        manager.stop()


# =============================================================================
# PlaywrightTester Tests
# =============================================================================


class TestPlaywrightTester:
    """Tests for PlaywrightTester class."""

    def test_init(self) -> None:
        """Test PlaywrightTester initialization."""
        tester = PlaywrightTester("http://localhost:5173")
        assert tester.server_url == "http://localhost:5173"
        assert tester.console_messages == []

    def test_handle_console_message(self) -> None:
        """Test handling console messages."""
        tester = PlaywrightTester("http://localhost:5173")

        # Create mock message
        mock_msg = MagicMock()
        mock_msg.text = "Test error message"
        mock_msg.type = "error"

        tester._handle_console_message(mock_msg)

        assert len(tester.console_messages) == 1
        assert tester.console_messages[0].text == "Test error message"
        assert tester.console_messages[0].level == "error"

    def test_handle_console_message_ignored(self) -> None:
        """Test that certain patterns are ignored."""
        tester = PlaywrightTester("http://localhost:5173")

        # Create mock message with ignored pattern
        mock_msg = MagicMock()
        mock_msg.text = "Failed to load favicon.ico"
        mock_msg.type = "error"

        tester._handle_console_message(mock_msg)

        assert len(tester.console_messages) == 0

    async def test_run_smoke_tests_no_playwright(self) -> None:
        """Test smoke tests when Playwright is not installed."""
        tester = PlaywrightTester("http://localhost:5173")

        with patch.dict("sys.modules", {"playwright.async_api": None}):
            # Force ImportError
            original_import = __builtins__["__import__"]

            def mock_import(name, *args, **kwargs):
                if "playwright" in name:
                    raise ImportError("No module named 'playwright'")
                return original_import(name, *args, **kwargs)

            with patch("builtins.__import__", mock_import):
                results = await tester.run_smoke_tests()

        assert len(results) == 1
        assert results[0].status == TestStatus.SKIPPED
        assert "Playwright not installed" in results[0].message


# =============================================================================
# QAAgent Tests
# =============================================================================


class TestQAAgent:
    """Tests for QAAgent class."""

    def test_name(self) -> None:
        """Test agent name property."""
        agent = QAAgent()
        assert agent.name == "QAAgent"

    def test_init_custom_port(self) -> None:
        """Test initialization with custom port."""
        agent = QAAgent(port=8080)
        assert agent.port == 8080

    async def test_run_missing_game_dir(self, tmp_path: Path) -> None:
        """Test run with missing game directory."""
        agent = QAAgent()
        missing_dir = tmp_path / "nonexistent"

        with pytest.raises(AgentError, match="Game directory not found"):
            await agent.run(game_dir=missing_dir)

    async def test_run_missing_package_json(self, tmp_path: Path) -> None:
        """Test run with missing package.json."""
        agent = QAAgent()
        game_dir = tmp_path / "game"
        game_dir.mkdir()

        with pytest.raises(AgentError, match=r"No package\.json"):
            await agent.run(game_dir=game_dir)

    def test_evaluate_fps_passed(self) -> None:
        """Test FPS evaluation with good FPS."""
        agent = QAAgent()
        result = agent._evaluate_fps(60.0)

        assert result.status == TestStatus.PASSED
        assert "acceptable" in result.message

    def test_evaluate_fps_low(self) -> None:
        """Test FPS evaluation with low FPS."""
        agent = QAAgent()
        result = agent._evaluate_fps(45.0)

        assert result.status == TestStatus.FAILED
        assert "below target" in result.message

    def test_evaluate_fps_critical(self) -> None:
        """Test FPS evaluation with critically low FPS."""
        agent = QAAgent()
        result = agent._evaluate_fps(20.0)

        assert result.status == TestStatus.FAILED
        assert result.severity == TestSeverity.HIGH
        assert "critically low" in result.message

    def test_evaluate_load_time_passed(self) -> None:
        """Test load time evaluation with good time."""
        agent = QAAgent()
        result = agent._evaluate_load_time(2000.0)

        assert result.status == TestStatus.PASSED
        assert "acceptable" in result.message

    def test_evaluate_load_time_slow(self) -> None:
        """Test load time evaluation with slow time."""
        agent = QAAgent()
        result = agent._evaluate_load_time(4000.0)

        assert result.status == TestStatus.FAILED
        assert "slow" in result.message

    def test_evaluate_load_time_too_slow(self) -> None:
        """Test load time evaluation with too slow time."""
        agent = QAAgent()
        result = agent._evaluate_load_time(6000.0)

        assert result.status == TestStatus.FAILED
        assert "too slow" in result.message

    def test_generate_recommendations_critical_failures(self) -> None:
        """Test generating recommendations for critical failures."""
        agent = QAAgent()
        report = QAReport(game_title="Test", test_date="2024-01-01")
        report.add_result(
            TestResult(
                name="critical_test",
                status=TestStatus.FAILED,
                severity=TestSeverity.CRITICAL,
            )
        )

        agent._generate_recommendations(report)

        assert any("Fix critical issues" in r for r in report.recommendations)

    def test_generate_recommendations_console_errors(self) -> None:
        """Test generating recommendations for console errors."""
        agent = QAAgent()
        report = QAReport(game_title="Test", test_date="2024-01-01")
        report.console_messages.append(ConsoleMessage(level="error", text="Error"))

        agent._generate_recommendations(report)

        assert any("console error" in r for r in report.recommendations)

    def test_generate_recommendations_low_fps(self) -> None:
        """Test generating recommendations for low FPS."""
        agent = QAAgent()
        report = QAReport(game_title="Test", test_date="2024-01-01")
        report.performance_metrics = {"avg_fps": 40.0}

        agent._generate_recommendations(report)

        assert any("55+ FPS" in r for r in report.recommendations)

    def test_generate_recommendations_slow_load(self) -> None:
        """Test generating recommendations for slow load time."""
        agent = QAAgent()
        report = QAReport(game_title="Test", test_date="2024-01-01")
        report.performance_metrics = {"load_time_ms": 5000.0}

        agent._generate_recommendations(report)

        assert any("load time" in r for r in report.recommendations)

    def test_generate_recommendations_high_memory(self) -> None:
        """Test generating recommendations for high memory usage."""
        agent = QAAgent()
        report = QAReport(game_title="Test", test_date="2024-01-01")
        report.performance_metrics = {"memory_mb": 150.0}

        agent._generate_recommendations(report)

        assert any("memory usage" in r for r in report.recommendations)

    def test_generate_recommendations_all_passed(self) -> None:
        """Test generating recommendations when all tests pass."""
        agent = QAAgent()
        report = QAReport(game_title="Test", test_date="2024-01-01")
        report.add_result(TestResult(name="test", status=TestStatus.PASSED))

        agent._generate_recommendations(report)

        assert any("All smoke tests passed" in r for r in report.recommendations)

    @patch("game_workflow.agents.qa.DevServerManager")
    @patch("game_workflow.agents.qa.PlaywrightTester")
    async def test_run_success(
        self,
        mock_tester_class: MagicMock,
        mock_server_class: MagicMock,
        game_dir: Path,
    ) -> None:
        """Test successful QA run."""
        # Set up mocks
        mock_server = AsyncMock()
        mock_server.url = "http://localhost:5173"
        mock_server_class.return_value = mock_server

        mock_tester = MagicMock()
        mock_tester.console_messages = []
        mock_tester.run_smoke_tests = AsyncMock(
            return_value=[
                TestResult(name="page_loads", status=TestStatus.PASSED),
                TestResult(name="canvas_present", status=TestStatus.PASSED),
            ]
        )
        mock_tester.measure_performance = AsyncMock(
            return_value={"avg_fps": 60.0, "load_time_ms": 2000.0}
        )
        mock_tester_class.return_value = mock_tester

        agent = QAAgent()
        result = await agent.run(game_dir=game_dir, game_title="Test Game")

        assert result["status"] == "success"
        assert "report" in result
        assert "report_path" in result
        assert result["report"]["game_title"] == "Test Game"

        # Check report was saved
        reports_dir = game_dir / "qa-reports"
        assert reports_dir.exists()

    @patch("game_workflow.agents.qa.DevServerManager")
    @patch("game_workflow.agents.qa.PlaywrightTester")
    async def test_run_critical_failure(
        self,
        mock_tester_class: MagicMock,
        mock_server_class: MagicMock,
        game_dir: Path,
    ) -> None:
        """Test QA run with critical failure."""
        # Set up mocks
        mock_server = AsyncMock()
        mock_server.url = "http://localhost:5173"
        mock_server_class.return_value = mock_server

        mock_tester = MagicMock()
        mock_tester.console_messages = []
        mock_tester.run_smoke_tests = AsyncMock(
            return_value=[
                TestResult(
                    name="page_loads",
                    status=TestStatus.FAILED,
                    severity=TestSeverity.CRITICAL,
                ),
            ]
        )
        mock_tester.measure_performance = AsyncMock(return_value={})
        mock_tester_class.return_value = mock_tester

        agent = QAAgent()

        with pytest.raises(QAFailedError, match="Critical tests failed"):
            await agent.run(game_dir=game_dir, skip_performance=True)

    @patch("game_workflow.agents.qa.DevServerManager")
    @patch("game_workflow.agents.qa.PlaywrightTester")
    async def test_run_skip_performance(
        self,
        mock_tester_class: MagicMock,
        mock_server_class: MagicMock,
        game_dir: Path,
    ) -> None:
        """Test QA run with performance tests skipped."""
        # Set up mocks
        mock_server = AsyncMock()
        mock_server.url = "http://localhost:5173"
        mock_server_class.return_value = mock_server

        mock_tester = MagicMock()
        mock_tester.console_messages = []
        mock_tester.run_smoke_tests = AsyncMock(
            return_value=[
                TestResult(name="page_loads", status=TestStatus.PASSED),
            ]
        )
        mock_tester_class.return_value = mock_tester

        agent = QAAgent()
        result = await agent.run(game_dir=game_dir, skip_performance=True)

        # Performance should not have been measured
        mock_tester.measure_performance.assert_not_called()
        assert result["report"]["performance_metrics"] == {}

    @patch("game_workflow.agents.qa.DevServerManager")
    @patch("game_workflow.agents.qa.PlaywrightTester")
    async def test_run_saves_reports(
        self,
        mock_tester_class: MagicMock,
        mock_server_class: MagicMock,
        game_dir: Path,
    ) -> None:
        """Test that QA run saves JSON and Markdown reports."""
        # Set up mocks
        mock_server = AsyncMock()
        mock_server.url = "http://localhost:5173"
        mock_server_class.return_value = mock_server

        mock_tester = MagicMock()
        mock_tester.console_messages = []
        mock_tester.run_smoke_tests = AsyncMock(
            return_value=[
                TestResult(name="test", status=TestStatus.PASSED),
            ]
        )
        mock_tester.measure_performance = AsyncMock(return_value={})
        mock_tester_class.return_value = mock_tester

        agent = QAAgent()
        await agent.run(game_dir=game_dir)

        # Check reports directory was created
        reports_dir = game_dir / "qa-reports"
        assert reports_dir.exists()

        # Check JSON report exists
        json_files = list(reports_dir.glob("*.json"))
        assert len(json_files) == 1

        # Verify JSON is valid
        with json_files[0].open() as f:
            report_data = json.load(f)
        assert "game_title" in report_data

        # Check Markdown report exists
        md_files = list(reports_dir.glob("*.md"))
        assert len(md_files) == 1


# =============================================================================
# Integration-style Tests
# =============================================================================


class TestQAReportFlow:
    """Integration tests for the QA report flow."""

    def test_complete_report_flow(self) -> None:
        """Test a complete report generation flow."""
        report = QAReport(
            game_title="My Game",
            test_date="2024-01-15T10:30:00",
        )

        # Add various test results
        report.add_result(
            TestResult(
                name="page_loads",
                status=TestStatus.PASSED,
                duration_ms=150.0,
                message="Page loaded in 150ms",
                severity=TestSeverity.CRITICAL,
            )
        )
        report.add_result(
            TestResult(
                name="canvas_present",
                status=TestStatus.PASSED,
                duration_ms=50.0,
                message="Canvas found",
                severity=TestSeverity.CRITICAL,
            )
        )
        report.add_result(
            TestResult(
                name="console_errors",
                status=TestStatus.FAILED,
                message="Found 2 console errors",
                details={"errors": ["Error 1", "Error 2"]},
                severity=TestSeverity.MEDIUM,
            )
        )

        # Add console messages
        report.console_messages.append(
            ConsoleMessage(level="error", text="Error 1", url="main.js", line=10)
        )
        report.console_messages.append(
            ConsoleMessage(level="error", text="Error 2", url="main.js", line=20)
        )
        report.console_messages.append(ConsoleMessage(level="log", text="Game started"))

        # Add performance metrics
        report.performance_metrics = {
            "avg_fps": 58.5,
            "min_fps": 45.0,
            "max_fps": 60.0,
            "memory_mb": 75.0,
            "load_time_ms": 2500.0,
        }

        # Determine status
        report.determine_overall_status()
        report.duration_seconds = 15.5

        # Verify the report
        assert report.total_tests == 3
        assert report.passed_tests == 2
        assert report.failed_tests == 1
        assert report.success_rate == pytest.approx(66.67, rel=0.1)
        assert report.overall_status == "needs_attention"

        # Test serialization
        report_dict = report.to_dict()
        assert report_dict["summary"]["total_tests"] == 3
        assert len(report_dict["console_messages"]) == 3
        assert report_dict["performance_metrics"]["avg_fps"] == 58.5

        # Test markdown generation
        markdown = report.to_markdown()
        assert "My Game" in markdown
        assert "console_errors" in markdown
        assert "58.5" in markdown  # FPS in performance section
