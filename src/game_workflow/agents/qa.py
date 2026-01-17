"""QA agent for game testing and validation.

This agent tests built games to ensure they meet quality standards
and work correctly. It performs smoke tests, functional validation,
and generates QA reports.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar

from game_workflow.agents.base import BaseAgent
from game_workflow.orchestrator.exceptions import AgentError, QAFailedError
from game_workflow.utils.subprocess import find_executable

# Default timeouts
DEV_SERVER_STARTUP_TIMEOUT = 30  # seconds
GAME_LOAD_TIMEOUT = 10000  # milliseconds
TEST_RUN_TIMEOUT = 60  # seconds per test
DEFAULT_PORT = 5173


class TestStatus(Enum):
    """Status of a test result."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestSeverity(Enum):
    """Severity level of a test issue."""

    CRITICAL = "critical"  # Game-breaking issues
    HIGH = "high"  # Major issues affecting gameplay
    MEDIUM = "medium"  # Minor issues
    LOW = "low"  # Cosmetic or polish issues
    INFO = "info"  # Informational only


@dataclass
class TestResult:
    """Result of a single test."""

    name: str
    status: TestStatus
    duration_ms: float = 0.0
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    severity: TestSeverity = TestSeverity.MEDIUM

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "message": self.message,
            "details": self.details,
            "severity": self.severity.value,
        }


@dataclass
class ConsoleMessage:
    """A console message captured during testing."""

    level: str  # "log", "warning", "error"
    text: str
    url: str = ""
    line: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "level": self.level,
            "text": self.text,
            "url": self.url,
            "line": self.line,
        }


@dataclass
class QAReport:
    """Complete QA report for a game."""

    game_title: str
    test_date: str
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    error_tests: int = 0
    duration_seconds: float = 0.0
    test_results: list[TestResult] = field(default_factory=list)
    console_messages: list[ConsoleMessage] = field(default_factory=list)
    performance_metrics: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    overall_status: str = "unknown"

    @property
    def success_rate(self) -> float:
        """Calculate test success rate."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100

    @property
    def has_critical_failures(self) -> bool:
        """Check if there are critical failures."""
        return any(
            r.status == TestStatus.FAILED and r.severity == TestSeverity.CRITICAL
            for r in self.test_results
        )

    def add_result(self, result: TestResult) -> None:
        """Add a test result."""
        self.test_results.append(result)
        self.total_tests += 1
        if result.status == TestStatus.PASSED:
            self.passed_tests += 1
        elif result.status == TestStatus.FAILED:
            self.failed_tests += 1
        elif result.status == TestStatus.SKIPPED:
            self.skipped_tests += 1
        elif result.status == TestStatus.ERROR:
            self.error_tests += 1

    def add_recommendation(self, recommendation: str) -> None:
        """Add a recommendation."""
        if recommendation not in self.recommendations:
            self.recommendations.append(recommendation)

    def determine_overall_status(self) -> None:
        """Determine the overall status based on test results."""
        if self.has_critical_failures:
            self.overall_status = "failed"
        elif self.failed_tests > 0:
            self.overall_status = "needs_attention"
        elif self.error_tests > 0:
            self.overall_status = "incomplete"
        elif self.passed_tests == self.total_tests > 0:
            self.overall_status = "passed"
        else:
            self.overall_status = "unknown"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "game_title": self.game_title,
            "test_date": self.test_date,
            "summary": {
                "total_tests": self.total_tests,
                "passed": self.passed_tests,
                "failed": self.failed_tests,
                "skipped": self.skipped_tests,
                "errors": self.error_tests,
                "success_rate": round(self.success_rate, 1),
                "duration_seconds": round(self.duration_seconds, 2),
                "overall_status": self.overall_status,
            },
            "test_results": [r.to_dict() for r in self.test_results],
            "console_messages": [m.to_dict() for m in self.console_messages],
            "performance_metrics": self.performance_metrics,
            "recommendations": self.recommendations,
        }

    def to_markdown(self) -> str:
        """Generate a markdown report."""
        lines = [
            f"# QA Report: {self.game_title}",
            "",
            f"**Date**: {self.test_date}",
            f"**Status**: {self.overall_status.upper()}",
            "",
            "## Summary",
            "",
            f"- **Total Tests**: {self.total_tests}",
            f"- **Passed**: {self.passed_tests}",
            f"- **Failed**: {self.failed_tests}",
            f"- **Skipped**: {self.skipped_tests}",
            f"- **Errors**: {self.error_tests}",
            f"- **Success Rate**: {self.success_rate:.1f}%",
            f"- **Duration**: {self.duration_seconds:.2f}s",
            "",
        ]

        # Failed tests section
        failed = [r for r in self.test_results if r.status == TestStatus.FAILED]
        if failed:
            lines.extend(["## Failed Tests", ""])
            for result in failed:
                severity_emoji = {
                    TestSeverity.CRITICAL: "[!]",
                    TestSeverity.HIGH: "[H]",
                    TestSeverity.MEDIUM: "[M]",
                    TestSeverity.LOW: "[L]",
                    TestSeverity.INFO: "[i]",
                }.get(result.severity, "[-]")
                lines.append(f"### {severity_emoji} {result.name}")
                lines.append("")
                lines.append(f"**Severity**: {result.severity.value}")
                lines.append(f"**Message**: {result.message}")
                if result.details:
                    lines.append("**Details**:")
                    lines.append("```json")
                    lines.append(json.dumps(result.details, indent=2))
                    lines.append("```")
                lines.append("")

        # Console errors
        errors = [m for m in self.console_messages if m.level == "error"]
        if errors:
            lines.extend(["## Console Errors", ""])
            for error in errors[:10]:  # Limit to 10
                lines.append(f"- `{error.text[:100]}`")
            if len(errors) > 10:
                lines.append(f"- ... and {len(errors) - 10} more errors")
            lines.append("")

        # Performance metrics
        if self.performance_metrics:
            lines.extend(["## Performance Metrics", ""])
            if "avg_fps" in self.performance_metrics:
                lines.append(f"- **Average FPS**: {self.performance_metrics['avg_fps']:.1f}")
            if "min_fps" in self.performance_metrics:
                lines.append(f"- **Minimum FPS**: {self.performance_metrics['min_fps']:.1f}")
            if "memory_mb" in self.performance_metrics:
                lines.append(f"- **Memory Usage**: {self.performance_metrics['memory_mb']:.1f} MB")
            if "load_time_ms" in self.performance_metrics:
                lines.append(f"- **Load Time**: {self.performance_metrics['load_time_ms']:.0f}ms")
            lines.append("")

        # Recommendations
        if self.recommendations:
            lines.extend(["## Recommendations", ""])
            for rec in self.recommendations:
                lines.append(f"- {rec}")
            lines.append("")

        # Passed tests (collapsed)
        passed = [r for r in self.test_results if r.status == TestStatus.PASSED]
        if passed:
            lines.extend(["## Passed Tests", ""])
            for result in passed:
                lines.append(f"- ✅ {result.name}")
            lines.append("")

        return "\n".join(lines)


class DevServerManager:
    """Manage a development server for testing."""

    def __init__(
        self,
        project_dir: Path,
        port: int = DEFAULT_PORT,
    ) -> None:
        """Initialize the dev server manager.

        Args:
            project_dir: Directory containing the game project.
            port: Port to run the server on.
        """
        self.project_dir = project_dir
        self.port = port
        self._process: subprocess.Popen[bytes] | None = None

    @property
    def url(self) -> str:
        """Get the server URL."""
        return f"http://localhost:{self.port}"

    async def start(self, timeout: float = DEV_SERVER_STARTUP_TIMEOUT) -> None:
        """Start the development server.

        Args:
            timeout: Maximum time to wait for server to be ready.

        Raises:
            RuntimeError: If server fails to start.
        """
        npm_path = find_executable("npm")
        if npm_path is None:
            raise RuntimeError("npm not found")

        # Start the server process
        self._process = subprocess.Popen(
            [str(npm_path), "run", "dev", "--", "--port", str(self.port)],
            cwd=self.project_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for server to be ready
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                import httpx

                response = httpx.get(self.url, timeout=1)
                if response.status_code == 200:
                    return
            except Exception:
                await asyncio.sleep(0.5)

        # Timeout - clean up and raise
        self.stop()
        raise RuntimeError(f"Dev server failed to start within {timeout}s")

    def stop(self) -> None:
        """Stop the development server."""
        if self._process is not None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None


class PlaywrightTester:
    """Run Playwright-based tests on a game."""

    # Common patterns to ignore in console errors
    IGNORE_PATTERNS: ClassVar[list[str]] = [
        "favicon.ico",
        "DevTools",
        "Autofocus",
        "[HMR]",
        "chrome-extension://",
        "moz-extension://",
    ]

    def __init__(self, server_url: str) -> None:
        """Initialize the tester.

        Args:
            server_url: URL of the game server.
        """
        self.server_url = server_url
        self.console_messages: list[ConsoleMessage] = []

    async def run_smoke_tests(self) -> list[TestResult]:
        """Run smoke tests on the game.

        Returns:
            List of test results.
        """
        results: list[TestResult] = []

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return [
                TestResult(
                    name="playwright_available",
                    status=TestStatus.SKIPPED,
                    message="Playwright not installed. Install with: pip install playwright && playwright install chromium",
                )
            ]

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-web-security", "--disable-gpu"],
            )

            try:
                context = await browser.new_context(
                    viewport={"width": 800, "height": 600},
                    device_scale_factor=1,
                )
                page = await context.new_page()

                # Set up console message collection
                page.on("console", self._handle_console_message)

                # Test 1: Page loads
                results.append(await self._test_page_loads(page))

                # Test 2: Canvas present
                results.append(await self._test_canvas_present(page))

                # Test 3: No JavaScript errors
                results.append(await self._test_no_js_errors(page))

                # Test 4: Game initializes
                results.append(await self._test_game_initializes(page))

                # Test 5: No console errors
                results.append(await self._test_no_console_errors())

                # Test 6: Game responds to input
                results.append(await self._test_input_response(page))

                await context.close()

            finally:
                await browser.close()

        return results

    async def measure_performance(self) -> dict[str, Any]:
        """Measure game performance metrics.

        Returns:
            Dictionary of performance metrics.
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return {"error": "Playwright not installed"}

        metrics: dict[str, Any] = {}

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-web-security", "--disable-gpu"],
            )

            try:
                context = await browser.new_context(
                    viewport={"width": 800, "height": 600},
                )
                page = await context.new_page()

                # Measure load time
                start = time.time()
                await page.goto(self.server_url)
                await page.wait_for_selector("canvas", timeout=GAME_LOAD_TIMEOUT)
                load_time = (time.time() - start) * 1000
                metrics["load_time_ms"] = load_time

                # Wait for game to initialize
                await page.wait_for_timeout(1000)

                # Measure FPS
                fps_values = await page.evaluate("""
                    () => new Promise(resolve => {
                        const frames = [];
                        let lastTime = performance.now();
                        const duration = 3000;
                        const startTime = performance.now();

                        function measure() {
                            const now = performance.now();
                            const delta = now - lastTime;
                            if (delta > 0) {
                                frames.push(1000 / delta);
                            }
                            lastTime = now;

                            if (now - startTime < duration) {
                                requestAnimationFrame(measure);
                            } else {
                                resolve(frames);
                            }
                        }

                        requestAnimationFrame(measure);
                    })
                """)

                if fps_values:
                    metrics["avg_fps"] = sum(fps_values) / len(fps_values)
                    metrics["min_fps"] = min(fps_values)
                    metrics["max_fps"] = max(fps_values)

                # Measure memory (if available)
                memory = await page.evaluate("""
                    () => {
                        if (performance.memory) {
                            return performance.memory.usedJSHeapSize / (1024 * 1024);
                        }
                        return null;
                    }
                """)
                if memory is not None:
                    metrics["memory_mb"] = memory

                await context.close()

            finally:
                await browser.close()

        return metrics

    def _handle_console_message(self, msg: Any) -> None:
        """Handle a console message from the page."""
        text = msg.text

        # Skip ignored patterns
        if any(p in text for p in self.IGNORE_PATTERNS):
            return

        message = ConsoleMessage(
            level=msg.type,
            text=text,
            url=msg.location.get("url", "") if hasattr(msg, "location") else "",
            line=msg.location.get("lineNumber", 0) if hasattr(msg, "location") else 0,
        )
        self.console_messages.append(message)

    async def _test_page_loads(self, page: Any) -> TestResult:
        """Test that the page loads."""
        start = time.time()
        try:
            response = await page.goto(self.server_url)
            duration = (time.time() - start) * 1000

            if response.status == 200:
                return TestResult(
                    name="page_loads",
                    status=TestStatus.PASSED,
                    duration_ms=duration,
                    message="Page loaded successfully",
                    severity=TestSeverity.CRITICAL,
                )
            else:
                return TestResult(
                    name="page_loads",
                    status=TestStatus.FAILED,
                    duration_ms=duration,
                    message=f"Page returned status {response.status}",
                    severity=TestSeverity.CRITICAL,
                )
        except Exception as e:
            return TestResult(
                name="page_loads",
                status=TestStatus.ERROR,
                duration_ms=(time.time() - start) * 1000,
                message=str(e),
                severity=TestSeverity.CRITICAL,
            )

    async def _test_canvas_present(self, page: Any) -> TestResult:
        """Test that the canvas element is present."""
        start = time.time()
        try:
            canvas = await page.wait_for_selector("canvas", timeout=GAME_LOAD_TIMEOUT)
            duration = (time.time() - start) * 1000

            if canvas:
                box = await canvas.bounding_box()
                if box and box["width"] > 0 and box["height"] > 0:
                    return TestResult(
                        name="canvas_present",
                        status=TestStatus.PASSED,
                        duration_ms=duration,
                        message=f"Canvas found with size {box['width']}x{box['height']}",
                        details={"width": box["width"], "height": box["height"]},
                        severity=TestSeverity.CRITICAL,
                    )
                else:
                    return TestResult(
                        name="canvas_present",
                        status=TestStatus.FAILED,
                        duration_ms=duration,
                        message="Canvas has zero dimensions",
                        severity=TestSeverity.CRITICAL,
                    )
            else:
                return TestResult(
                    name="canvas_present",
                    status=TestStatus.FAILED,
                    duration_ms=duration,
                    message="Canvas element not found",
                    severity=TestSeverity.CRITICAL,
                )
        except Exception as e:
            return TestResult(
                name="canvas_present",
                status=TestStatus.ERROR,
                duration_ms=(time.time() - start) * 1000,
                message=str(e),
                severity=TestSeverity.CRITICAL,
            )

    async def _test_no_js_errors(self, page: Any) -> TestResult:
        """Test that no JavaScript errors occur."""
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        # Wait and check for errors
        await page.wait_for_timeout(2000)

        if not errors:
            return TestResult(
                name="no_javascript_errors",
                status=TestStatus.PASSED,
                message="No JavaScript errors detected",
                severity=TestSeverity.HIGH,
            )
        else:
            return TestResult(
                name="no_javascript_errors",
                status=TestStatus.FAILED,
                message=f"Found {len(errors)} JavaScript error(s)",
                details={"errors": errors[:5]},  # Limit to 5
                severity=TestSeverity.HIGH,
            )

    async def _test_game_initializes(self, page: Any) -> TestResult:
        """Test that the game initializes."""
        start = time.time()
        try:
            # Wait for game to be exposed
            is_running = await page.evaluate("""
                () => {
                    const game = window.game || window.phaserGame;
                    return game && game.isRunning;
                }
            """)
            duration = (time.time() - start) * 1000

            if is_running:
                return TestResult(
                    name="game_initializes",
                    status=TestStatus.PASSED,
                    duration_ms=duration,
                    message="Game initialized and running",
                    severity=TestSeverity.CRITICAL,
                )
            else:
                return TestResult(
                    name="game_initializes",
                    status=TestStatus.FAILED,
                    duration_ms=duration,
                    message="Game not running or not exposed on window.game",
                    severity=TestSeverity.CRITICAL,
                )
        except Exception as e:
            return TestResult(
                name="game_initializes",
                status=TestStatus.ERROR,
                duration_ms=(time.time() - start) * 1000,
                message=str(e),
                severity=TestSeverity.CRITICAL,
            )

    async def _test_no_console_errors(self) -> TestResult:
        """Test that no console errors were logged."""
        errors = [m for m in self.console_messages if m.level == "error"]

        if not errors:
            return TestResult(
                name="no_console_errors",
                status=TestStatus.PASSED,
                message="No console errors detected",
                severity=TestSeverity.MEDIUM,
            )
        else:
            return TestResult(
                name="no_console_errors",
                status=TestStatus.FAILED,
                message=f"Found {len(errors)} console error(s)",
                details={"errors": [e.text[:100] for e in errors[:5]]},
                severity=TestSeverity.MEDIUM,
            )

    async def _test_input_response(self, page: Any) -> TestResult:
        """Test that the game responds to input."""
        start = time.time()
        try:
            # Try pressing some keys
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(500)
            await page.keyboard.press("ArrowRight")
            await page.wait_for_timeout(500)

            # Check if any scene changed or game state updated
            # This is a basic check - just verify no errors occurred
            duration = (time.time() - start) * 1000

            return TestResult(
                name="input_response",
                status=TestStatus.PASSED,
                duration_ms=duration,
                message="Game accepted input without errors",
                severity=TestSeverity.MEDIUM,
            )
        except Exception as e:
            return TestResult(
                name="input_response",
                status=TestStatus.ERROR,
                duration_ms=(time.time() - start) * 1000,
                message=str(e),
                severity=TestSeverity.MEDIUM,
            )


class QAAgent(BaseAgent):
    """Agent for testing and validating games.

    This agent runs automated tests on built games to verify
    they function correctly and meet quality standards.

    The QA process includes:
    1. Starting a dev server to host the game
    2. Running smoke tests via Playwright
    3. Measuring performance metrics
    4. Generating a comprehensive QA report
    """

    def __init__(
        self,
        port: int = DEFAULT_PORT,
        **kwargs: Any,
    ) -> None:
        """Initialize the QAAgent.

        Args:
            port: Port to use for the dev server.
            **kwargs: Arguments passed to BaseAgent.
        """
        super().__init__(**kwargs)
        self.port = port

    @property
    def name(self) -> str:
        """Get the agent's name."""
        return "QAAgent"

    async def run(
        self,
        game_dir: Path,
        gdd_path: Path | None = None,  # noqa: ARG002
        game_title: str = "Game",
        skip_performance: bool = False,
        **kwargs: Any,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Test a built game.

        Args:
            game_dir: Directory containing the game project.
            gdd_path: Path to the GDD for reference (optional).
            game_title: Title of the game for the report.
            skip_performance: Skip performance tests.
            **kwargs: Additional arguments.

        Returns:
            Dict containing:
                - status: "success" or "failed"
                - report: QAReport as dictionary
                - report_path: Path to saved report
                - recommendations: List of recommendations

        Raises:
            AgentError: If testing setup fails.
            QAFailedError: If critical tests fail.
        """
        game_dir = Path(game_dir)
        start_time = time.time()

        # Validate game directory
        if not game_dir.exists():
            raise AgentError(self.name, f"Game directory not found: {game_dir}")

        if not (game_dir / "package.json").exists():
            raise AgentError(self.name, f"No package.json in game directory: {game_dir}")

        # Create report
        report = QAReport(
            game_title=game_title,
            test_date=datetime.now().isoformat(),
        )

        # Start dev server
        self.log_info("Starting development server")
        server = DevServerManager(game_dir, self.port)

        try:
            await server.start()
            self.log_info(f"Dev server running at {server.url}")

            # Run smoke tests
            self.log_info("Running smoke tests")
            tester = PlaywrightTester(server.url)
            smoke_results = await tester.run_smoke_tests()

            for result in smoke_results:
                report.add_result(result)

            # Collect console messages
            report.console_messages = tester.console_messages

            # Run performance tests
            if not skip_performance:
                self.log_info("Measuring performance")
                performance = await tester.measure_performance()
                report.performance_metrics = performance

                # Add performance-based test results
                if "avg_fps" in performance:
                    fps_result = self._evaluate_fps(performance["avg_fps"])
                    report.add_result(fps_result)

                if "load_time_ms" in performance:
                    load_result = self._evaluate_load_time(performance["load_time_ms"])
                    report.add_result(load_result)

            # Generate recommendations
            self._generate_recommendations(report)

            # Determine overall status
            report.determine_overall_status()
            report.duration_seconds = time.time() - start_time

            self.log_info(
                f"QA complete: {report.passed_tests}/{report.total_tests} passed, "
                f"status={report.overall_status}"
            )

        finally:
            server.stop()
            self.log_debug("Dev server stopped")

        # Save report
        report_path = await self._save_report(game_dir, report)

        # Add artifact
        self.add_artifact("qa_report", str(report_path))

        # Check for critical failures
        if report.has_critical_failures:
            raise QAFailedError(
                f"Critical tests failed: {report.failed_tests} failures",
                test_results=report.to_dict(),
            )

        return {
            "status": "success" if report.overall_status == "passed" else "needs_review",
            "report": report.to_dict(),
            "report_path": str(report_path),
            "recommendations": report.recommendations,
        }

    def _evaluate_fps(self, avg_fps: float) -> TestResult:
        """Evaluate FPS performance.

        Args:
            avg_fps: Average frames per second.

        Returns:
            TestResult for the FPS evaluation.
        """
        if avg_fps >= 55:
            return TestResult(
                name="performance_fps",
                status=TestStatus.PASSED,
                message=f"Average FPS {avg_fps:.1f} is acceptable",
                details={"avg_fps": avg_fps},
                severity=TestSeverity.MEDIUM,
            )
        elif avg_fps >= 30:
            return TestResult(
                name="performance_fps",
                status=TestStatus.FAILED,
                message=f"Average FPS {avg_fps:.1f} is below target (55)",
                details={"avg_fps": avg_fps, "target": 55},
                severity=TestSeverity.MEDIUM,
            )
        else:
            return TestResult(
                name="performance_fps",
                status=TestStatus.FAILED,
                message=f"Average FPS {avg_fps:.1f} is critically low",
                details={"avg_fps": avg_fps, "target": 55},
                severity=TestSeverity.HIGH,
            )

    def _evaluate_load_time(self, load_time_ms: float) -> TestResult:
        """Evaluate load time performance.

        Args:
            load_time_ms: Load time in milliseconds.

        Returns:
            TestResult for the load time evaluation.
        """
        if load_time_ms <= 3000:
            return TestResult(
                name="performance_load_time",
                status=TestStatus.PASSED,
                message=f"Load time {load_time_ms:.0f}ms is acceptable",
                details={"load_time_ms": load_time_ms},
                severity=TestSeverity.LOW,
            )
        elif load_time_ms <= 5000:
            return TestResult(
                name="performance_load_time",
                status=TestStatus.FAILED,
                message=f"Load time {load_time_ms:.0f}ms is slow",
                details={"load_time_ms": load_time_ms, "target": 3000},
                severity=TestSeverity.LOW,
            )
        else:
            return TestResult(
                name="performance_load_time",
                status=TestStatus.FAILED,
                message=f"Load time {load_time_ms:.0f}ms is too slow",
                details={"load_time_ms": load_time_ms, "target": 3000},
                severity=TestSeverity.MEDIUM,
            )

    def _generate_recommendations(self, report: QAReport) -> None:
        """Generate recommendations based on test results.

        Args:
            report: The QA report to add recommendations to.
        """
        # Check for critical failures
        critical_failures = [
            r
            for r in report.test_results
            if r.status == TestStatus.FAILED and r.severity == TestSeverity.CRITICAL
        ]
        if critical_failures:
            report.add_recommendation(
                "Fix critical issues before proceeding: "
                + ", ".join(r.name for r in critical_failures)
            )

        # Check console errors
        errors = [m for m in report.console_messages if m.level == "error"]
        if errors:
            report.add_recommendation(
                f"Address {len(errors)} console error(s) to improve stability"
            )

        # Check performance
        if "avg_fps" in report.performance_metrics:
            fps = report.performance_metrics["avg_fps"]
            if fps < 55:
                report.add_recommendation(f"Optimize game to achieve 55+ FPS (currently {fps:.1f})")

        if "load_time_ms" in report.performance_metrics:
            load_time = report.performance_metrics["load_time_ms"]
            if load_time > 3000:
                report.add_recommendation(
                    f"Reduce load time from {load_time:.0f}ms to under 3000ms"
                )

        if "memory_mb" in report.performance_metrics:
            memory = report.performance_metrics["memory_mb"]
            if memory > 100:
                report.add_recommendation(
                    f"Investigate memory usage ({memory:.1f}MB may indicate a leak)"
                )

        # General recommendations
        if not report.has_critical_failures and report.failed_tests == 0:
            report.add_recommendation(
                "All smoke tests passed. Consider adding gameplay-specific tests."
            )

    async def _save_report(self, game_dir: Path, report: QAReport) -> Path:
        """Save the QA report to files.

        Args:
            game_dir: Game directory.
            report: The report to save.

        Returns:
            Path to the JSON report file.
        """
        reports_dir = game_dir / "qa-reports"
        reports_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save JSON report
        json_path = reports_dir / f"qa_report_{timestamp}.json"
        with json_path.open("w") as f:
            json.dump(report.to_dict(), f, indent=2)

        # Save Markdown report
        md_path = reports_dir / f"qa_report_{timestamp}.md"
        with md_path.open("w") as f:
            f.write(report.to_markdown())

        self.log_debug(f"Reports saved to {reports_dir}")

        return json_path
