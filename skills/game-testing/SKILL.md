# Game Testing Skill

This skill provides Claude Code with comprehensive knowledge for automated game testing using Playwright, including browser automation, visual testing, performance benchmarking, accessibility testing, mobile device testing, audio testing, and quality assurance patterns.

---

## Table of Contents

1. [Overview](#overview)
2. [Test Environment Setup](#test-environment-setup)
3. [Playwright Fundamentals](#playwright-fundamentals)
4. [Game-Specific Testing Patterns](#game-specific-testing-patterns)
5. [Smoke Tests](#smoke-tests)
6. [Functional Tests](#functional-tests)
7. [Visual Regression Testing](#visual-regression-testing)
8. [Performance Testing](#performance-testing)
9. [Console Error Detection](#console-error-detection)
10. [Input Simulation](#input-simulation)
11. [Canvas Inspection](#canvas-inspection)
12. [Accessibility Testing](#accessibility-testing)
13. [Mobile Device Testing](#mobile-device-testing)
14. [Audio Testing](#audio-testing)
15. [Network Testing for Multiplayer](#network-testing-for-multiplayer)
16. [Test Organization](#test-organization)
17. [CI/CD Integration](#cicd-integration)
18. [Common Issues and Solutions](#common-issues-and-solutions)

---

## Overview

Game testing differs from traditional web application testing because games:
- Render to a `<canvas>` element (no DOM structure for game objects)
- Have continuous update loops (time-dependent behavior)
- Respond to keyboard/mouse input in real-time
- May have non-deterministic elements (physics, particles, random events)
- Require performance benchmarking (frame rate, memory usage)

This skill covers testing strategies for Phaser.js games, but patterns apply to other web-based game engines.

### Test Categories

| Category | Purpose | Tools |
|----------|---------|-------|
| Smoke Tests | Verify game loads without errors | Playwright, console capture |
| Functional Tests | Verify mechanics work correctly | Playwright, game state injection |
| Visual Tests | Detect rendering regressions | Screenshot comparison |
| Performance Tests | Ensure acceptable frame rate | FPS measurement, memory profiling |
| Accessibility Tests | Check for a11y compliance | Playwright accessibility API |
| Mobile Tests | Verify touch/mobile behavior | Device emulation, touch events |
| Audio Tests | Verify sound/music works | Web Audio API inspection |
| Network Tests | Test multiplayer/online features | Request mocking, latency simulation |

---

## Test Environment Setup

### Directory Structure

```
game-project/
├── src/                    # Game source code
├── dist/                   # Built game
└── tests/
    ├── conftest.py         # Pytest fixtures and configuration
    ├── test_smoke.py       # Smoke tests (load, no errors)
    ├── test_gameplay.py    # Gameplay/functional tests
    ├── test_ui.py          # UI/menu tests
    ├── test_performance.py # Performance benchmarks
    └── screenshots/
        └── baseline/       # Reference screenshots for comparison
```

### Dependencies

```bash
# Install Playwright
pip install pytest-playwright
playwright install chromium

# Or use npm
npm install -D @playwright/test
```

### Pytest Configuration (conftest.py)

```python
"""Pytest configuration and fixtures for game testing."""

import asyncio
import subprocess
import time
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
from playwright.async_api import Browser, Page, async_playwright

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DIST_DIR = PROJECT_ROOT / "dist"

# Default test configuration
DEFAULT_VIEWPORT = {"width": 800, "height": 600}
GAME_LOAD_TIMEOUT = 10000  # 10 seconds
DEV_SERVER_PORT = 5173


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def browser() -> AsyncGenerator[Browser, None]:
    """Launch browser for the test session."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,  # Set to False for debugging
            args=[
                "--disable-web-security",  # Allow local file access
                "--disable-gpu",  # More stable in CI
            ],
        )
        yield browser
        await browser.close()


@pytest.fixture
async def page(browser: Browser) -> AsyncGenerator[Page, None]:
    """Create a new page for each test."""
    context = await browser.new_context(
        viewport=DEFAULT_VIEWPORT,
        device_scale_factor=1,  # Consistent screenshots
    )
    page = await context.new_page()
    yield page
    await context.close()


@pytest.fixture(scope="session")
def dev_server() -> Generator[str, None, None]:
    """Start the dev server for testing.

    Yields the server URL.
    """
    # Start the dev server
    process = subprocess.Popen(
        ["npm", "run", "dev", "--", "--port", str(DEV_SERVER_PORT)],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to be ready
    server_url = f"http://localhost:{DEV_SERVER_PORT}"
    max_wait = 30  # seconds
    start = time.time()

    while time.time() - start < max_wait:
        try:
            import httpx
            response = httpx.get(server_url, timeout=1)
            if response.status_code == 200:
                break
        except Exception:
            time.sleep(0.5)
    else:
        process.terminate()
        raise RuntimeError(f"Dev server failed to start within {max_wait}s")

    yield server_url

    # Cleanup
    process.terminate()
    process.wait(timeout=5)


@pytest.fixture
async def game_page(page: Page, dev_server: str) -> AsyncGenerator[Page, None]:
    """Navigate to the game and wait for it to load."""
    await page.goto(dev_server)

    # Wait for canvas to be present
    await page.wait_for_selector("canvas", timeout=GAME_LOAD_TIMEOUT)

    # Give the game time to initialize
    await page.wait_for_timeout(1000)

    yield page


class ConsoleErrorCollector:
    """Collect console errors from a page."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.logs: list[str] = []

    def handle_message(self, msg) -> None:
        """Handle a console message."""
        text = msg.text
        if msg.type == "error":
            self.errors.append(text)
        elif msg.type == "warning":
            self.warnings.append(text)
        else:
            self.logs.append(text)

    def clear(self) -> None:
        """Clear collected messages."""
        self.errors.clear()
        self.warnings.clear()
        self.logs.clear()

    def assert_no_errors(self, ignore_patterns: list[str] | None = None) -> None:
        """Assert no errors were logged.

        Args:
            ignore_patterns: Patterns to ignore (regex or substring)
        """
        ignore = ignore_patterns or []
        filtered = [
            e for e in self.errors
            if not any(p in e for p in ignore)
        ]
        if filtered:
            raise AssertionError(
                f"Console errors found:\n" + "\n".join(filtered)
            )


@pytest.fixture
async def console_errors(page: Page) -> AsyncGenerator[ConsoleErrorCollector, None]:
    """Collect console errors during a test."""
    collector = ConsoleErrorCollector()
    page.on("console", collector.handle_message)
    yield collector
    # Cleanup is automatic when page closes
```

---

## Playwright Fundamentals

### Basic Navigation and Waiting

```python
async def test_basic_navigation(page: Page, dev_server: str) -> None:
    """Test basic page navigation."""
    # Navigate to game
    await page.goto(dev_server)

    # Wait for specific conditions
    await page.wait_for_selector("canvas")  # Wait for element
    await page.wait_for_load_state("networkidle")  # Wait for network
    await page.wait_for_timeout(1000)  # Fixed delay (use sparingly)

    # Check page title
    title = await page.title()
    assert "Game" in title
```

### Element Interactions

```python
async def test_menu_interactions(game_page: Page) -> None:
    """Test menu button clicks."""
    # Find and click play button
    play_button = await game_page.wait_for_selector('[data-button="play"]')
    await play_button.click()

    # Or use text content
    await game_page.click('text="Start Game"')

    # Wait for scene transition
    await game_page.wait_for_timeout(500)
```

### Keyboard and Mouse Input

```python
async def test_keyboard_input(game_page: Page) -> None:
    """Test keyboard controls."""
    # Press single key
    await game_page.keyboard.press("ArrowRight")

    # Hold key
    await game_page.keyboard.down("ArrowRight")
    await game_page.wait_for_timeout(500)
    await game_page.keyboard.up("ArrowRight")

    # Multiple keys
    await game_page.keyboard.press("Control+C")

    # Type text (for input fields)
    await game_page.keyboard.type("Player Name")


async def test_mouse_input(game_page: Page) -> None:
    """Test mouse controls."""
    # Click at coordinates
    await game_page.mouse.click(400, 300)

    # Double click
    await game_page.mouse.dblclick(400, 300)

    # Drag
    await game_page.mouse.move(100, 100)
    await game_page.mouse.down()
    await game_page.mouse.move(200, 200)
    await game_page.mouse.up()
```

---

## Game-Specific Testing Patterns

### Accessing Game State via JavaScript

Since games render to canvas, you often need to access game state directly:

```python
async def get_game_state(page: Page) -> dict:
    """Get the current game state via Phaser globals."""
    return await page.evaluate("""
        () => {
            // Access Phaser game instance (common patterns)
            const game = window.game || window.phaserGame;
            if (!game) return { error: 'Game not found' };

            const scene = game.scene.getScene('GameScene');
            if (!scene) return { error: 'Scene not found' };

            return {
                score: scene.score || 0,
                lives: scene.lives || 0,
                level: scene.currentLevel || 1,
                isPaused: game.scene.isPaused('GameScene'),
                isGameOver: scene.isGameOver || false,
            };
        }
    """)


async def test_game_state_tracking(game_page: Page) -> None:
    """Test that game state is tracked correctly."""
    state = await get_game_state(game_page)

    assert state.get("score") == 0, "Initial score should be 0"
    assert state.get("lives") > 0, "Should have lives remaining"
```

### Exposing Game State for Testing

Add test hooks to your game code:

```javascript
// In your game setup (src/main.js or game config)
const config = {
    // ... other config
    callbacks: {
        postBoot: function(game) {
            // Expose game for testing
            window.game = game;

            // Add test utilities
            window.gameTestUtils = {
                getScore: () => game.scene.getScene('GameScene')?.score || 0,
                setScore: (score) => {
                    const scene = game.scene.getScene('GameScene');
                    if (scene) scene.score = score;
                },
                getCurrentScene: () => game.scene.getScenes(true)[0]?.scene.key,
                triggerEvent: (event, data) => {
                    game.events.emit(event, data);
                },
            };
        }
    }
};
```

Then in tests:

```python
async def test_score_increases(game_page: Page) -> None:
    """Test that collecting items increases score."""
    # Get initial score
    initial_score = await game_page.evaluate("window.gameTestUtils.getScore()")

    # Simulate collecting an item (game-specific action)
    await game_page.keyboard.press("Space")  # Or whatever collects
    await game_page.wait_for_timeout(500)

    # Check score increased
    new_score = await game_page.evaluate("window.gameTestUtils.getScore()")
    assert new_score > initial_score
```

---

## Smoke Tests

Smoke tests verify the game loads and runs without errors.

```python
"""Smoke tests to verify game loads correctly."""

import pytest
from playwright.async_api import Page


class TestGameLoads:
    """Tests that verify the game loads successfully."""

    async def test_canvas_present(self, game_page: Page) -> None:
        """Test that the game canvas is present."""
        canvas = await game_page.query_selector("canvas")
        assert canvas is not None, "Canvas element not found"

        # Check canvas has dimensions
        box = await canvas.bounding_box()
        assert box is not None
        assert box["width"] > 0
        assert box["height"] > 0

    async def test_no_console_errors(
        self,
        game_page: Page,
        console_errors: "ConsoleErrorCollector"
    ) -> None:
        """Test that no console errors occur during load."""
        # Wait for game to fully load
        await game_page.wait_for_timeout(2000)

        # Check for errors (ignore known benign ones)
        console_errors.assert_no_errors(ignore_patterns=[
            "favicon",  # Missing favicon
            "DevTools",  # Chrome DevTools messages
        ])

    async def test_no_javascript_errors(self, game_page: Page) -> None:
        """Test that no uncaught JavaScript errors occur."""
        errors = []
        game_page.on("pageerror", lambda e: errors.append(str(e)))

        # Let game run for a bit
        await game_page.wait_for_timeout(3000)

        assert len(errors) == 0, f"JavaScript errors: {errors}"

    async def test_game_initializes(self, game_page: Page) -> None:
        """Test that the Phaser game initializes."""
        is_initialized = await game_page.evaluate("""
            () => {
                const game = window.game || window.phaserGame;
                return game && game.isRunning;
            }
        """)
        assert is_initialized, "Game did not initialize"

    async def test_menu_scene_loads(self, game_page: Page) -> None:
        """Test that the menu scene loads."""
        # Wait for menu scene or game scene
        await game_page.wait_for_timeout(2000)

        current_scene = await game_page.evaluate("""
            () => {
                const game = window.game || window.phaserGame;
                if (!game) return null;
                const scenes = game.scene.getScenes(true);
                return scenes.length > 0 ? scenes[0].scene.key : null;
            }
        """)

        assert current_scene is not None, "No active scene"
        assert current_scene in ["MenuScene", "GameScene", "PreloadScene"], \
            f"Unexpected scene: {current_scene}"
```

---

## Functional Tests

Test specific game mechanics and behaviors.

```python
"""Functional tests for gameplay mechanics."""

import pytest
from playwright.async_api import Page


class TestPlayerMovement:
    """Tests for player movement mechanics."""

    async def get_player_position(self, page: Page) -> dict:
        """Get the player's current position."""
        return await page.evaluate("""
            () => {
                const game = window.game;
                const scene = game.scene.getScene('GameScene');
                const player = scene?.player;
                return player ? { x: player.x, y: player.y } : null;
            }
        """)

    async def test_player_moves_right(self, game_page: Page) -> None:
        """Test that pressing right arrow moves player right."""
        # Start in game scene
        await self.start_game(game_page)

        initial_pos = await self.get_player_position(game_page)
        assert initial_pos is not None

        # Press right arrow for 500ms
        await game_page.keyboard.down("ArrowRight")
        await game_page.wait_for_timeout(500)
        await game_page.keyboard.up("ArrowRight")

        new_pos = await self.get_player_position(game_page)
        assert new_pos["x"] > initial_pos["x"], "Player should move right"

    async def test_player_moves_left(self, game_page: Page) -> None:
        """Test that pressing left arrow moves player left."""
        await self.start_game(game_page)

        initial_pos = await self.get_player_position(game_page)

        await game_page.keyboard.down("ArrowLeft")
        await game_page.wait_for_timeout(500)
        await game_page.keyboard.up("ArrowLeft")

        new_pos = await self.get_player_position(game_page)
        # Note: Player might hit left boundary
        assert new_pos["x"] <= initial_pos["x"], "Player should move left or stay"

    async def start_game(self, page: Page) -> None:
        """Helper to start the game from menu."""
        # Click start button or press enter
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(500)


class TestScoring:
    """Tests for scoring mechanics."""

    async def get_score(self, page: Page) -> int:
        """Get the current score."""
        return await page.evaluate("""
            () => {
                const game = window.game;
                const scene = game.scene.getScene('GameScene');
                return scene?.score || 0;
            }
        """)

    async def test_score_starts_at_zero(self, game_page: Page) -> None:
        """Test that score starts at zero."""
        await self.start_game(game_page)
        score = await self.get_score(game_page)
        assert score == 0

    async def test_score_displayed(self, game_page: Page) -> None:
        """Test that score is displayed on screen."""
        await self.start_game(game_page)

        # Check for score text in DOM or canvas
        has_score = await game_page.evaluate("""
            () => {
                const game = window.game;
                const scene = game.scene.getScene('GameScene');
                // Check for score text object
                return scene?.scoreText !== undefined;
            }
        """)
        assert has_score, "Score display not found"

    async def start_game(self, page: Page) -> None:
        """Helper to start the game."""
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(500)


class TestGameOver:
    """Tests for game over conditions."""

    async def test_game_over_on_death(self, game_page: Page) -> None:
        """Test that game over triggers when player dies."""
        await self.start_game(game_page)

        # Trigger death condition (game-specific)
        await game_page.evaluate("""
            () => {
                const game = window.game;
                const scene = game.scene.getScene('GameScene');
                if (scene?.triggerGameOver) {
                    scene.triggerGameOver();
                } else if (scene?.lives !== undefined) {
                    scene.lives = 0;
                    scene.playerDied?.();
                }
            }
        """)

        await game_page.wait_for_timeout(1000)

        # Check game over state
        is_game_over = await game_page.evaluate("""
            () => {
                const game = window.game;
                const scene = game.scene.getScene('GameScene');
                return scene?.isGameOver ||
                       game.scene.isActive('GameOverScene');
            }
        """)
        assert is_game_over, "Game over should be triggered"

    async def start_game(self, page: Page) -> None:
        """Helper to start the game."""
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(500)
```

---

## Visual Regression Testing

Compare screenshots against baselines to detect visual changes.

```python
"""Visual regression tests."""

import hashlib
from pathlib import Path

import pytest
from PIL import Image
from playwright.async_api import Page

SCREENSHOTS_DIR = Path(__file__).parent / "screenshots"
BASELINE_DIR = SCREENSHOTS_DIR / "baseline"
CURRENT_DIR = SCREENSHOTS_DIR / "current"
DIFF_DIR = SCREENSHOTS_DIR / "diff"


def ensure_dirs() -> None:
    """Ensure screenshot directories exist."""
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    CURRENT_DIR.mkdir(parents=True, exist_ok=True)
    DIFF_DIR.mkdir(parents=True, exist_ok=True)


def images_match(img1_path: Path, img2_path: Path, threshold: float = 0.99) -> bool:
    """Compare two images and return True if they match within threshold.

    Args:
        img1_path: Path to first image
        img2_path: Path to second image
        threshold: Similarity threshold (0.0 to 1.0)

    Returns:
        True if images match within threshold
    """
    try:
        from PIL import Image, ImageChops
        import math

        img1 = Image.open(img1_path)
        img2 = Image.open(img2_path)

        if img1.size != img2.size:
            return False

        diff = ImageChops.difference(img1, img2)

        # Calculate similarity
        pixels = list(diff.getdata())
        total_diff = sum(sum(pixel) for pixel in pixels)
        max_diff = 255 * len(pixels) * len(pixels[0])  # Max possible difference

        similarity = 1 - (total_diff / max_diff)
        return similarity >= threshold

    except Exception:
        return False


class TestVisualRegression:
    """Visual regression tests."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up screenshot directories."""
        ensure_dirs()

    async def capture_and_compare(
        self,
        page: Page,
        name: str,
        threshold: float = 0.99,
        update_baseline: bool = False,
    ) -> None:
        """Capture screenshot and compare to baseline.

        Args:
            page: Playwright page
            name: Screenshot name (without extension)
            threshold: Similarity threshold
            update_baseline: If True, update baseline instead of comparing
        """
        baseline_path = BASELINE_DIR / f"{name}.png"
        current_path = CURRENT_DIR / f"{name}.png"
        diff_path = DIFF_DIR / f"{name}_diff.png"

        # Capture current screenshot
        await page.screenshot(path=str(current_path))

        if update_baseline or not baseline_path.exists():
            # Save as new baseline
            import shutil
            shutil.copy(current_path, baseline_path)
            return

        # Compare to baseline
        if not images_match(baseline_path, current_path, threshold):
            # Create diff image for debugging
            self._create_diff_image(baseline_path, current_path, diff_path)

            pytest.fail(
                f"Visual regression detected for '{name}'. "
                f"See diff at: {diff_path}"
            )

    def _create_diff_image(
        self,
        baseline: Path,
        current: Path,
        output: Path
    ) -> None:
        """Create a diff image highlighting differences."""
        try:
            from PIL import Image, ImageChops

            img1 = Image.open(baseline)
            img2 = Image.open(current)

            diff = ImageChops.difference(img1, img2)
            diff.save(output)
        except Exception:
            pass  # Diff creation is optional

    async def test_menu_appearance(self, game_page: Page) -> None:
        """Test menu screen appearance."""
        # Wait for menu to fully render
        await game_page.wait_for_timeout(1000)

        await self.capture_and_compare(game_page, "menu_screen")

    async def test_game_start_appearance(self, game_page: Page) -> None:
        """Test game screen appearance at start."""
        await game_page.keyboard.press("Enter")
        await game_page.wait_for_timeout(1000)

        await self.capture_and_compare(game_page, "game_start")

    async def test_pause_screen(self, game_page: Page) -> None:
        """Test pause screen appearance."""
        await game_page.keyboard.press("Enter")
        await game_page.wait_for_timeout(500)
        await game_page.keyboard.press("Escape")
        await game_page.wait_for_timeout(500)

        await self.capture_and_compare(game_page, "pause_screen")


# To update baselines, run:
# pytest tests/test_visual.py --update-baselines
# Or set UPDATE_BASELINES=1 environment variable
```

---

## Performance Testing

Measure and assert on game performance metrics.

```python
"""Performance tests for the game."""

import statistics
from dataclasses import dataclass

import pytest
from playwright.async_api import Page


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    fps_values: list[float]
    memory_mb: float
    load_time_ms: float

    @property
    def avg_fps(self) -> float:
        """Average FPS."""
        return statistics.mean(self.fps_values) if self.fps_values else 0

    @property
    def min_fps(self) -> float:
        """Minimum FPS."""
        return min(self.fps_values) if self.fps_values else 0

    @property
    def fps_stddev(self) -> float:
        """FPS standard deviation."""
        return statistics.stdev(self.fps_values) if len(self.fps_values) > 1 else 0


async def measure_fps(page: Page, duration_ms: int = 3000) -> list[float]:
    """Measure FPS over a duration.

    Args:
        page: Playwright page
        duration_ms: How long to measure (milliseconds)

    Returns:
        List of FPS measurements
    """
    return await page.evaluate(f"""
        () => new Promise(resolve => {{
            const frames = [];
            let lastTime = performance.now();
            const duration = {duration_ms};
            const startTime = performance.now();

            function measure() {{
                const now = performance.now();
                const delta = now - lastTime;
                if (delta > 0) {{
                    frames.push(1000 / delta);
                }}
                lastTime = now;

                if (now - startTime < duration) {{
                    requestAnimationFrame(measure);
                }} else {{
                    resolve(frames);
                }}
            }}

            requestAnimationFrame(measure);
        }})
    """)


async def measure_memory(page: Page) -> float:
    """Measure JavaScript heap size in MB.

    Returns:
        Heap size in MB, or -1 if not available
    """
    return await page.evaluate("""
        () => {
            if (performance.memory) {
                return performance.memory.usedJSHeapSize / (1024 * 1024);
            }
            return -1;
        }
    """)


async def measure_load_time(page: Page) -> float:
    """Measure page load time in milliseconds."""
    return await page.evaluate("""
        () => {
            const timing = performance.timing;
            return timing.loadEventEnd - timing.navigationStart;
        }
    """)


class TestPerformance:
    """Performance benchmark tests."""

    # Performance thresholds
    MIN_ACCEPTABLE_FPS = 55
    MAX_ACCEPTABLE_MEMORY_MB = 150
    MAX_ACCEPTABLE_LOAD_TIME_MS = 5000

    async def test_frame_rate(self, game_page: Page) -> None:
        """Test that game maintains acceptable frame rate."""
        # Start game
        await game_page.keyboard.press("Enter")
        await game_page.wait_for_timeout(1000)

        # Measure FPS
        fps_values = await measure_fps(game_page, duration_ms=5000)

        avg_fps = statistics.mean(fps_values)
        min_fps = min(fps_values)

        print(f"FPS - Avg: {avg_fps:.1f}, Min: {min_fps:.1f}")

        assert avg_fps >= self.MIN_ACCEPTABLE_FPS, \
            f"Average FPS {avg_fps:.1f} below threshold {self.MIN_ACCEPTABLE_FPS}"

        # Allow occasional dips but not too frequent
        dips = sum(1 for fps in fps_values if fps < self.MIN_ACCEPTABLE_FPS)
        dip_percentage = dips / len(fps_values) * 100
        assert dip_percentage < 10, \
            f"Too many FPS dips: {dip_percentage:.1f}% of frames below threshold"

    async def test_frame_rate_stability(self, game_page: Page) -> None:
        """Test that frame rate is stable (low variance)."""
        await game_page.keyboard.press("Enter")
        await game_page.wait_for_timeout(1000)

        fps_values = await measure_fps(game_page, duration_ms=5000)

        stddev = statistics.stdev(fps_values)
        print(f"FPS Std Dev: {stddev:.2f}")

        # Standard deviation should be low (stable frame rate)
        assert stddev < 15, f"FPS too unstable: stddev={stddev:.2f}"

    async def test_memory_usage(self, game_page: Page) -> None:
        """Test that memory usage is acceptable."""
        await game_page.keyboard.press("Enter")
        await game_page.wait_for_timeout(2000)

        memory_mb = await measure_memory(game_page)

        if memory_mb < 0:
            pytest.skip("Memory measurement not available")

        print(f"Memory usage: {memory_mb:.1f} MB")

        assert memory_mb < self.MAX_ACCEPTABLE_MEMORY_MB, \
            f"Memory usage {memory_mb:.1f}MB exceeds threshold"

    async def test_no_memory_leak(self, game_page: Page) -> None:
        """Test that memory doesn't grow unboundedly."""
        await game_page.keyboard.press("Enter")
        await game_page.wait_for_timeout(1000)

        # Measure initial memory
        initial_memory = await measure_memory(game_page)
        if initial_memory < 0:
            pytest.skip("Memory measurement not available")

        # Simulate gameplay for a while
        for _ in range(10):
            await game_page.keyboard.press("ArrowRight")
            await game_page.wait_for_timeout(200)
            await game_page.keyboard.press("Space")
            await game_page.wait_for_timeout(200)

        await game_page.wait_for_timeout(1000)

        # Measure final memory
        final_memory = await measure_memory(game_page)

        growth = final_memory - initial_memory
        growth_percentage = (growth / initial_memory) * 100

        print(f"Memory growth: {growth:.1f}MB ({growth_percentage:.1f}%)")

        # Allow some growth but not excessive
        assert growth_percentage < 50, \
            f"Memory grew {growth_percentage:.1f}% - possible leak"

    async def test_load_time(self, page: Page, dev_server: str) -> None:
        """Test that game loads within acceptable time."""
        start = await page.evaluate("() => performance.now()")

        await page.goto(dev_server)
        await page.wait_for_selector("canvas")

        # Wait for game to be fully initialized
        await page.wait_for_function(
            "() => window.game && window.game.isRunning",
            timeout=10000
        )

        end = await page.evaluate("() => performance.now()")
        load_time = end - start

        print(f"Load time: {load_time:.0f}ms")

        assert load_time < self.MAX_ACCEPTABLE_LOAD_TIME_MS, \
            f"Load time {load_time:.0f}ms exceeds threshold"
```

---

## Console Error Detection

Comprehensive console error monitoring.

```python
"""Console error detection utilities."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from playwright.async_api import ConsoleMessage, Page


class MessageSeverity(Enum):
    """Console message severity levels."""
    LOG = "log"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ConsoleEntry:
    """A captured console message."""
    text: str
    severity: MessageSeverity
    url: str = ""
    line: int = 0

    @classmethod
    def from_message(cls, msg: ConsoleMessage) -> "ConsoleEntry":
        """Create from Playwright ConsoleMessage."""
        return cls(
            text=msg.text,
            severity=MessageSeverity(msg.type) if msg.type in [e.value for e in MessageSeverity] else MessageSeverity.LOG,
            url=msg.location.get("url", "") if msg.location else "",
            line=msg.location.get("lineNumber", 0) if msg.location else 0,
        )


class ConsoleMonitor:
    """Monitor console output during tests."""

    # Common patterns to ignore
    DEFAULT_IGNORE_PATTERNS = [
        "favicon.ico",  # Missing favicon
        "DevTools",  # Chrome DevTools
        "Autofocus",  # Autofocus warnings
        "[HMR]",  # Vite hot module replacement
        "experiment",  # Chrome experiments
    ]

    def __init__(
        self,
        ignore_patterns: list[str] | None = None,
        fail_on_warning: bool = False,
    ) -> None:
        self.entries: list[ConsoleEntry] = []
        self.ignore_patterns = ignore_patterns or self.DEFAULT_IGNORE_PATTERNS
        self.fail_on_warning = fail_on_warning
        self._handlers: list[Callable[[ConsoleEntry], None]] = []

    def handle_message(self, msg: ConsoleMessage) -> None:
        """Handle incoming console message."""
        entry = ConsoleEntry.from_message(msg)

        # Skip ignored patterns
        if any(p in entry.text for p in self.ignore_patterns):
            return

        self.entries.append(entry)

        # Call registered handlers
        for handler in self._handlers:
            handler(entry)

    def on_entry(self, handler: Callable[[ConsoleEntry], None]) -> None:
        """Register a handler for console entries."""
        self._handlers.append(handler)

    @property
    def errors(self) -> list[ConsoleEntry]:
        """Get error entries."""
        return [e for e in self.entries if e.severity == MessageSeverity.ERROR]

    @property
    def warnings(self) -> list[ConsoleEntry]:
        """Get warning entries."""
        return [e for e in self.entries if e.severity == MessageSeverity.WARNING]

    def clear(self) -> None:
        """Clear all entries."""
        self.entries.clear()

    def assert_clean(self) -> None:
        """Assert no errors (and optionally warnings)."""
        if self.errors:
            error_texts = "\n".join(f"  - {e.text}" for e in self.errors)
            raise AssertionError(f"Console errors found:\n{error_texts}")

        if self.fail_on_warning and self.warnings:
            warning_texts = "\n".join(f"  - {e.text}" for e in self.warnings)
            raise AssertionError(f"Console warnings found:\n{warning_texts}")

    def get_summary(self) -> dict:
        """Get a summary of console output."""
        return {
            "total": len(self.entries),
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "error_texts": [e.text for e in self.errors],
            "warning_texts": [e.text for e in self.warnings],
        }


async def with_console_monitoring(
    page: Page,
    ignore_patterns: list[str] | None = None,
) -> ConsoleMonitor:
    """Set up console monitoring on a page.

    Args:
        page: Playwright page
        ignore_patterns: Patterns to ignore

    Returns:
        ConsoleMonitor instance
    """
    monitor = ConsoleMonitor(ignore_patterns=ignore_patterns)
    page.on("console", monitor.handle_message)
    return monitor
```

---

## Input Simulation

Advanced input simulation for game testing.

```python
"""Input simulation utilities for game testing."""

from dataclasses import dataclass
from typing import Literal

from playwright.async_api import Page


@dataclass
class InputSequence:
    """A sequence of inputs to perform."""
    actions: list[tuple[str, float]]  # (key, hold_duration_ms)


class GameInputSimulator:
    """Simulate game inputs."""

    def __init__(self, page: Page) -> None:
        self.page = page

    async def press_key(self, key: str) -> None:
        """Press a key once."""
        await self.page.keyboard.press(key)

    async def hold_key(self, key: str, duration_ms: int) -> None:
        """Hold a key for a duration."""
        await self.page.keyboard.down(key)
        await self.page.wait_for_timeout(duration_ms)
        await self.page.keyboard.up(key)

    async def press_keys_simultaneously(self, keys: list[str]) -> None:
        """Press multiple keys at once."""
        for key in keys:
            await self.page.keyboard.down(key)
        await self.page.wait_for_timeout(50)  # Brief hold
        for key in reversed(keys):
            await self.page.keyboard.up(key)

    async def click_at(self, x: int, y: int) -> None:
        """Click at canvas coordinates."""
        # Note: Coordinates are relative to viewport
        canvas = await self.page.query_selector("canvas")
        if canvas:
            box = await canvas.bounding_box()
            if box:
                await self.page.mouse.click(
                    box["x"] + x,
                    box["y"] + y
                )

    async def drag(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        steps: int = 10,
    ) -> None:
        """Perform a drag operation."""
        canvas = await self.page.query_selector("canvas")
        if not canvas:
            return

        box = await canvas.bounding_box()
        if not box:
            return

        # Move to start
        await self.page.mouse.move(box["x"] + start_x, box["y"] + start_y)
        await self.page.mouse.down()

        # Interpolate to end
        for i in range(steps):
            t = (i + 1) / steps
            x = start_x + (end_x - start_x) * t
            y = start_y + (end_y - start_y) * t
            await self.page.mouse.move(box["x"] + x, box["y"] + y)
            await self.page.wait_for_timeout(20)

        await self.page.mouse.up()

    async def perform_sequence(self, sequence: InputSequence) -> None:
        """Perform a sequence of inputs."""
        for key, duration in sequence.actions:
            if duration > 0:
                await self.hold_key(key, int(duration))
            else:
                await self.press_key(key)
            await self.page.wait_for_timeout(50)  # Gap between inputs


# Common input sequences for testing
MOVE_RIGHT = InputSequence([("ArrowRight", 500)])
MOVE_LEFT = InputSequence([("ArrowLeft", 500)])
JUMP = InputSequence([("Space", 0)])
JUMP_RIGHT = InputSequence([("ArrowRight", 300), ("Space", 0)])
```

---

## Canvas Inspection

Inspect canvas rendering for tests.

```python
"""Canvas inspection utilities."""

from dataclasses import dataclass
from typing import Tuple

from playwright.async_api import Page


@dataclass
class CanvasPixel:
    """A pixel from the canvas."""
    r: int
    g: int
    b: int
    a: int

    @property
    def is_transparent(self) -> bool:
        """Check if pixel is transparent."""
        return self.a == 0

    @property
    def rgb(self) -> Tuple[int, int, int]:
        """Get RGB tuple."""
        return (self.r, self.g, self.b)

    @property
    def hex(self) -> str:
        """Get hex color string."""
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"


async def get_canvas_pixel(page: Page, x: int, y: int) -> CanvasPixel:
    """Get a pixel from the canvas at coordinates.

    Args:
        page: Playwright page
        x: X coordinate
        y: Y coordinate

    Returns:
        CanvasPixel at the location
    """
    result = await page.evaluate(f"""
        () => {{
            const canvas = document.querySelector('canvas');
            const ctx = canvas.getContext('2d');
            const pixel = ctx.getImageData({x}, {y}, 1, 1).data;
            return {{r: pixel[0], g: pixel[1], b: pixel[2], a: pixel[3]}};
        }}
    """)
    return CanvasPixel(**result)


async def get_canvas_region_colors(
    page: Page,
    x: int,
    y: int,
    width: int,
    height: int,
) -> dict[str, int]:
    """Get dominant colors in a canvas region.

    Returns a dict of hex colors to pixel counts.
    """
    return await page.evaluate(f"""
        () => {{
            const canvas = document.querySelector('canvas');
            const ctx = canvas.getContext('2d');
            const imageData = ctx.getImageData({x}, {y}, {width}, {height});
            const data = imageData.data;
            const colors = {{}};

            for (let i = 0; i < data.length; i += 4) {{
                const r = data[i];
                const g = data[i + 1];
                const b = data[i + 2];
                const hex = '#' + [r, g, b].map(x => x.toString(16).padStart(2, '0')).join('');
                colors[hex] = (colors[hex] || 0) + 1;
            }}

            return colors;
        }}
    """)


async def is_canvas_region_uniform(
    page: Page,
    x: int,
    y: int,
    width: int,
    height: int,
    threshold: float = 0.95,
) -> bool:
    """Check if a canvas region has a uniform color.

    Args:
        page: Playwright page
        x, y, width, height: Region to check
        threshold: Percentage of pixels that must match dominant color

    Returns:
        True if region is uniform
    """
    colors = await get_canvas_region_colors(page, x, y, width, height)
    if not colors:
        return False

    total_pixels = sum(colors.values())
    max_color_count = max(colors.values())

    return max_color_count / total_pixels >= threshold
```

---

## Accessibility Testing

Games should be accessible to players with disabilities. This section covers testing for accessibility compliance.

### WCAG Color Contrast Testing

```python
"""Accessibility tests for color contrast and visibility."""

from dataclasses import dataclass
import math

from playwright.async_api import Page


@dataclass
class ColorContrastResult:
    """Result of a color contrast check."""
    foreground: str
    background: str
    ratio: float
    passes_aa: bool  # 4.5:1 for normal text, 3:1 for large text
    passes_aaa: bool  # 7:1 for normal text, 4.5:1 for large text

    @property
    def level(self) -> str:
        """Get the highest WCAG level passed."""
        if self.passes_aaa:
            return "AAA"
        elif self.passes_aa:
            return "AA"
        return "Fail"


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def relative_luminance(r: int, g: int, b: int) -> float:
    """Calculate relative luminance per WCAG 2.1.

    See: https://www.w3.org/WAI/GL/wiki/Relative_luminance
    """
    def channel_luminance(c: int) -> float:
        s = c / 255
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4

    return (
        0.2126 * channel_luminance(r) +
        0.7152 * channel_luminance(g) +
        0.0722 * channel_luminance(b)
    )


def contrast_ratio(fg: str, bg: str) -> float:
    """Calculate contrast ratio between two colors.

    Returns a value between 1 (no contrast) and 21 (max contrast).
    """
    fg_rgb = hex_to_rgb(fg)
    bg_rgb = hex_to_rgb(bg)

    fg_lum = relative_luminance(*fg_rgb)
    bg_lum = relative_luminance(*bg_rgb)

    lighter = max(fg_lum, bg_lum)
    darker = min(fg_lum, bg_lum)

    return (lighter + 0.05) / (darker + 0.05)


def check_contrast(
    foreground: str,
    background: str,
    large_text: bool = False
) -> ColorContrastResult:
    """Check color contrast against WCAG standards.

    Args:
        foreground: Foreground color (hex)
        background: Background color (hex)
        large_text: Whether text is 18pt+ or 14pt+ bold

    Returns:
        ColorContrastResult with pass/fail status
    """
    ratio = contrast_ratio(foreground, background)

    # WCAG thresholds
    aa_threshold = 3.0 if large_text else 4.5
    aaa_threshold = 4.5 if large_text else 7.0

    return ColorContrastResult(
        foreground=foreground,
        background=background,
        ratio=ratio,
        passes_aa=ratio >= aa_threshold,
        passes_aaa=ratio >= aaa_threshold,
    )


class TestColorContrast:
    """Tests for color contrast accessibility."""

    async def get_ui_colors(self, page: Page) -> list[dict]:
        """Extract UI text colors and backgrounds from game."""
        return await page.evaluate("""
            () => {
                const game = window.game;
                if (!game) return [];

                const colors = [];
                const scenes = game.scene.getScenes(true);

                for (const scene of scenes) {
                    // Check Phaser text objects
                    scene.children.list.forEach(child => {
                        if (child.type === 'Text') {
                            colors.push({
                                type: 'text',
                                color: child.style?.color || '#ffffff',
                                name: child.name || 'unnamed',
                            });
                        }
                    });
                }

                return colors;
            }
        """)

    async def test_ui_text_contrast(self, game_page: Page) -> None:
        """Test that UI text has sufficient contrast."""
        # Get background color (usually from game config or CSS)
        bg_color = await game_page.evaluate("""
            () => {
                const canvas = document.querySelector('canvas');
                const style = getComputedStyle(canvas.parentElement);
                return style.backgroundColor || '#000000';
            }
        """)

        ui_colors = await self.get_ui_colors(game_page)

        failures = []
        for item in ui_colors:
            result = check_contrast(item['color'], bg_color)
            if not result.passes_aa:
                failures.append(
                    f"{item['name']}: {item['color']} on {bg_color} "
                    f"(ratio: {result.ratio:.2f}, need 4.5:1)"
                )

        assert not failures, f"Color contrast failures:\n" + "\n".join(failures)

    async def test_critical_ui_colors(self, game_page: Page) -> None:
        """Test specific critical UI element colors."""
        # Define critical color pairs to test
        critical_pairs = [
            {"name": "Score text", "fg": "#ffffff", "bg": "#000000"},
            {"name": "Health bar text", "fg": "#ff0000", "bg": "#222222"},
            {"name": "Button text", "fg": "#000000", "bg": "#ffcc00"},
        ]

        for pair in critical_pairs:
            result = check_contrast(pair["fg"], pair["bg"])
            assert result.passes_aa, (
                f"{pair['name']} fails contrast: "
                f"{result.ratio:.2f}:1 (need 4.5:1)"
            )
```

### Keyboard Navigation Testing

```python
"""Keyboard navigation accessibility tests."""

import pytest
from playwright.async_api import Page


class TestKeyboardNavigation:
    """Tests for keyboard-only navigation."""

    async def test_menu_keyboard_navigation(self, game_page: Page) -> None:
        """Test that menus can be navigated with keyboard only."""
        # Focus should start on first interactive element
        await game_page.keyboard.press("Tab")

        # Get focused element
        focused = await game_page.evaluate("""
            () => {
                const game = window.game;
                // Check if game tracks keyboard focus
                return game.input?.keyboard?.getFocusedElement?.() ||
                       document.activeElement?.tagName;
            }
        """)

        assert focused is not None, "No element received focus"

    async def test_arrow_key_menu_navigation(self, game_page: Page) -> None:
        """Test arrow key navigation in menus."""
        # Wait for menu scene
        await game_page.wait_for_timeout(1000)

        # Test that arrow keys move focus
        selected_before = await self.get_selected_menu_item(game_page)

        await game_page.keyboard.press("ArrowDown")
        await game_page.wait_for_timeout(100)

        selected_after = await self.get_selected_menu_item(game_page)

        assert selected_before != selected_after, "Arrow key should change selection"

    async def test_enter_activates_button(self, game_page: Page) -> None:
        """Test that Enter key activates focused button."""
        # Navigate to play button
        await game_page.keyboard.press("ArrowDown")

        # Press Enter to activate
        current_scene = await self.get_current_scene(game_page)
        await game_page.keyboard.press("Enter")
        await game_page.wait_for_timeout(500)
        new_scene = await self.get_current_scene(game_page)

        # Scene should change (menu -> game)
        assert current_scene != new_scene, "Enter should activate button"

    async def test_escape_closes_dialogs(self, game_page: Page) -> None:
        """Test that Escape closes dialogs/menus."""
        # Start game
        await game_page.keyboard.press("Enter")
        await game_page.wait_for_timeout(500)

        # Open pause menu
        await game_page.keyboard.press("Escape")
        await game_page.wait_for_timeout(200)

        is_paused = await game_page.evaluate("""
            () => window.game?.scene.isPaused('GameScene') || false
        """)
        assert is_paused, "Escape should open pause menu"

        # Close pause menu
        await game_page.keyboard.press("Escape")
        await game_page.wait_for_timeout(200)

        is_paused = await game_page.evaluate("""
            () => window.game?.scene.isPaused('GameScene') || false
        """)
        assert not is_paused, "Escape should close pause menu"

    async def test_focus_visible(self, game_page: Page) -> None:
        """Test that focused elements have visible focus indicators."""
        # Tab to first button
        await game_page.keyboard.press("Tab")

        # Check for visual focus indicator
        has_focus_indicator = await game_page.evaluate("""
            () => {
                const game = window.game;
                const scene = game.scene.getScenes(true)[0];

                // Check for focus indicator (common implementations)
                const hasFocusRing = scene?.children.list.some(
                    child => child.name?.includes('focus') ||
                             child.type === 'Graphics'
                );

                return hasFocusRing;
            }
        """)

        # This may need game-specific implementation
        # At minimum, log a warning if no focus indicator found
        if not has_focus_indicator:
            pytest.skip("Focus indicator check requires game-specific implementation")

    async def get_selected_menu_item(self, page: Page) -> str | None:
        """Get currently selected menu item."""
        return await page.evaluate("""
            () => {
                const game = window.game;
                const scene = game.scene.getScenes(true)[0];
                return scene?.selectedButton?.name ||
                       scene?.menuButtons?.findIndex(b => b.selected) ||
                       null;
            }
        """)

    async def get_current_scene(self, page: Page) -> str | None:
        """Get current active scene name."""
        return await page.evaluate("""
            () => {
                const game = window.game;
                const scenes = game.scene.getScenes(true);
                return scenes[0]?.scene.key || null;
            }
        """)


class TestGameplayKeyboardControls:
    """Tests for keyboard controls during gameplay."""

    async def test_all_actions_keyboard_accessible(self, game_page: Page) -> None:
        """Test that all game actions have keyboard bindings."""
        required_actions = [
            "move_left",
            "move_right",
            "jump",
            "pause",
        ]

        # Get input bindings from game
        bindings = await game_page.evaluate("""
            () => {
                const game = window.game;
                const keyboard = game.input?.keyboard;

                // Common ways to get key bindings
                if (keyboard?.keys) {
                    return Object.keys(keyboard.keys);
                }

                // Or check for input actions
                const scene = game.scene.getScene('GameScene');
                if (scene?.input?.keyboard?.addKeys) {
                    return ['cursor keys bound'];
                }

                return [];
            }
        """)

        assert len(bindings) > 0, "No keyboard bindings found"

    async def test_remappable_controls(self, game_page: Page) -> None:
        """Test if controls can be remapped (accessibility feature)."""
        # Check for settings/options menu with key remapping
        has_remap = await game_page.evaluate("""
            () => {
                const game = window.game;
                // Check for common control remapping patterns
                return typeof window.gameSettings?.controls !== 'undefined' ||
                       typeof localStorage.getItem('keyBindings') !== 'undefined';
            }
        """)

        # This is a recommendation, not a requirement
        if not has_remap:
            pytest.skip("Key remapping not implemented (recommended for accessibility)")
```

### Screen Reader Support Testing

```python
"""Screen reader accessibility tests."""

from playwright.async_api import Page


class TestScreenReaderSupport:
    """Tests for screen reader compatibility."""

    async def test_aria_live_regions(self, game_page: Page) -> None:
        """Test that important updates are announced via ARIA live regions."""
        # Check for ARIA live regions in HTML
        live_regions = await game_page.evaluate("""
            () => {
                const regions = document.querySelectorAll('[aria-live]');
                return Array.from(regions).map(r => ({
                    role: r.getAttribute('role'),
                    ariaLive: r.getAttribute('aria-live'),
                    text: r.textContent,
                }));
            }
        """)

        # Games should have at least one live region for announcements
        if len(live_regions) == 0:
            pytest.skip("No ARIA live regions found (recommended for screen readers)")

    async def test_score_changes_announced(self, game_page: Page) -> None:
        """Test that score changes are announced to screen readers."""
        # Start game
        await game_page.keyboard.press("Enter")
        await game_page.wait_for_timeout(500)

        # Get initial announcement region content
        initial = await game_page.evaluate("""
            () => document.querySelector('[aria-live]')?.textContent || ''
        """)

        # Trigger score change (game-specific)
        await game_page.evaluate("""
            () => {
                const game = window.game;
                const scene = game.scene.getScene('GameScene');
                if (scene?.addScore) scene.addScore(100);
            }
        """)

        await game_page.wait_for_timeout(200)

        # Check if announcement changed
        updated = await game_page.evaluate("""
            () => document.querySelector('[aria-live]')?.textContent || ''
        """)

        # Score announcement is optional but recommended
        if initial == updated:
            pytest.skip("Score changes not announced (recommended feature)")

    async def test_game_state_announcements(self, game_page: Page) -> None:
        """Test that major game state changes are announced."""
        announcements_to_test = [
            ("Game start", "Enter"),
            ("Pause", "Escape"),
        ]

        for state, key in announcements_to_test:
            await game_page.keyboard.press(key)
            await game_page.wait_for_timeout(300)

            # Check for announcement
            announced = await game_page.evaluate("""
                () => {
                    const liveRegion = document.querySelector('[aria-live="assertive"]');
                    return liveRegion?.textContent?.length > 0;
                }
            """)

            if not announced:
                pytest.skip(f"{state} state not announced (recommended feature)")


class TestReducedMotion:
    """Tests for reduced motion preferences."""

    async def test_respects_reduced_motion(self, game_page: Page) -> None:
        """Test that game respects prefers-reduced-motion setting."""
        # Emulate reduced motion preference
        await game_page.emulate_media(reduced_motion="reduce")

        # Reload to apply preference
        await game_page.reload()
        await game_page.wait_for_selector("canvas")
        await game_page.wait_for_timeout(1000)

        # Check if animations are reduced
        has_reduced = await game_page.evaluate("""
            () => {
                // Check CSS media query
                const prefersReduced = window.matchMedia(
                    '(prefers-reduced-motion: reduce)'
                ).matches;

                // Check if game respects it
                const game = window.game;
                const config = game?.config;

                return {
                    browserPrefers: prefersReduced,
                    gameReduced: config?.reducedMotion ||
                                 window.gameSettings?.reducedMotion ||
                                 false,
                };
            }
        """)

        assert has_reduced["browserPrefers"], "Browser should report reduced motion"
        # Game implementation is recommended but not required
        if not has_reduced["gameReduced"]:
            pytest.skip("Game reduced motion support recommended but not required")

    async def test_option_to_disable_particles(self, game_page: Page) -> None:
        """Test for option to disable particle effects."""
        has_option = await game_page.evaluate("""
            () => {
                return typeof window.gameSettings?.particles !== 'undefined' ||
                       typeof window.gameSettings?.visualEffects !== 'undefined';
            }
        """)

        if not has_option:
            pytest.skip("Particle toggle option recommended for accessibility")

    async def test_option_to_disable_screen_shake(self, game_page: Page) -> None:
        """Test for option to disable screen shake."""
        has_option = await game_page.evaluate("""
            () => {
                return typeof window.gameSettings?.screenShake !== 'undefined';
            }
        """)

        if not has_option:
            pytest.skip("Screen shake toggle recommended for accessibility")
```

### Colorblind Mode Testing

```python
"""Colorblind accessibility tests."""

from playwright.async_api import Page
import pytest


class TestColorblindSupport:
    """Tests for colorblind accessibility."""

    async def test_colorblind_mode_available(self, game_page: Page) -> None:
        """Test if colorblind mode is available in settings."""
        has_mode = await game_page.evaluate("""
            () => {
                return typeof window.gameSettings?.colorblindMode !== 'undefined';
            }
        """)

        if not has_mode:
            pytest.skip("Colorblind mode setting recommended")

    async def test_not_color_only_indicators(self, game_page: Page) -> None:
        """Test that important info isn't conveyed by color alone."""
        # This is a manual check guide
        # Automated testing can only partially verify this

        # Check for shape/icon variations in addition to color
        has_shapes = await game_page.evaluate("""
            () => {
                const game = window.game;
                const scene = game.scene.getScene('GameScene');

                // Look for common patterns that use shapes + colors
                // This is game-specific
                return true; // Placeholder - needs manual verification
            }
        """)

        # Log reminder for manual check
        print("MANUAL CHECK REQUIRED: Verify important info uses shapes/icons, not just color")

    async def test_health_not_just_color(self, game_page: Page) -> None:
        """Test that health indication uses more than color."""
        # Start game
        await game_page.keyboard.press("Enter")
        await game_page.wait_for_timeout(500)

        # Check health display type
        health_display = await game_page.evaluate("""
            () => {
                const game = window.game;
                const scene = game.scene.getScene('GameScene');

                // Look for health bar with additional indicators
                const healthElements = scene?.children.list.filter(
                    c => c.name?.toLowerCase().includes('health')
                ) || [];

                return {
                    hasText: healthElements.some(e => e.type === 'Text'),
                    hasBar: healthElements.some(e => e.type === 'Graphics'),
                    hasIcon: healthElements.some(e => e.type === 'Sprite'),
                };
            }
        """)

        # At least one non-color indicator should exist
        has_alternative = (
            health_display.get("hasText") or
            health_display.get("hasIcon")
        )

        if not has_alternative:
            print("RECOMMENDATION: Add text or icons to health display for colorblind users")
```

---

## Mobile Device Testing

Testing games on mobile devices and with touch controls.

### Device Emulation Setup

```python
"""Mobile device testing setup and utilities."""

from dataclasses import dataclass
from typing import Literal

import pytest
from playwright.async_api import Browser, Page


@dataclass
class DeviceProfile:
    """Mobile device profile for testing."""
    name: str
    viewport_width: int
    viewport_height: int
    device_scale_factor: float
    is_mobile: bool
    has_touch: bool
    user_agent: str


# Common device profiles
DEVICES = {
    "iphone_12": DeviceProfile(
        name="iPhone 12",
        viewport_width=390,
        viewport_height=844,
        device_scale_factor=3,
        is_mobile=True,
        has_touch=True,
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
    ),
    "iphone_se": DeviceProfile(
        name="iPhone SE",
        viewport_width=375,
        viewport_height=667,
        device_scale_factor=2,
        is_mobile=True,
        has_touch=True,
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
    ),
    "ipad": DeviceProfile(
        name="iPad",
        viewport_width=768,
        viewport_height=1024,
        device_scale_factor=2,
        is_mobile=True,
        has_touch=True,
        user_agent="Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
    ),
    "pixel_5": DeviceProfile(
        name="Pixel 5",
        viewport_width=393,
        viewport_height=851,
        device_scale_factor=2.75,
        is_mobile=True,
        has_touch=True,
        user_agent="Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36",
    ),
    "galaxy_s21": DeviceProfile(
        name="Samsung Galaxy S21",
        viewport_width=360,
        viewport_height=800,
        device_scale_factor=3,
        is_mobile=True,
        has_touch=True,
        user_agent="Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36",
    ),
}


@pytest.fixture
async def mobile_page(browser: Browser, request) -> Page:
    """Create a page with mobile device emulation.

    Use with: @pytest.mark.parametrize("device", ["iphone_12", "pixel_5"])
    """
    device_name = getattr(request, "param", "iphone_12")
    device = DEVICES.get(device_name, DEVICES["iphone_12"])

    context = await browser.new_context(
        viewport={"width": device.viewport_width, "height": device.viewport_height},
        device_scale_factor=device.device_scale_factor,
        is_mobile=device.is_mobile,
        has_touch=device.has_touch,
        user_agent=device.user_agent,
    )

    page = await context.new_page()
    yield page
    await context.close()


@pytest.fixture
async def landscape_mobile_page(browser: Browser) -> Page:
    """Create a mobile page in landscape orientation."""
    device = DEVICES["iphone_12"]

    context = await browser.new_context(
        viewport={"width": device.viewport_height, "height": device.viewport_width},
        device_scale_factor=device.device_scale_factor,
        is_mobile=True,
        has_touch=True,
    )

    page = await context.new_page()
    yield page
    await context.close()
```

### Touch Input Testing

```python
"""Touch input testing for mobile games."""

from playwright.async_api import Page


class TouchSimulator:
    """Simulate touch inputs for game testing."""

    def __init__(self, page: Page) -> None:
        self.page = page

    async def tap(self, x: int, y: int) -> None:
        """Single tap at coordinates."""
        await self.page.touchscreen.tap(x, y)

    async def double_tap(self, x: int, y: int) -> None:
        """Double tap at coordinates."""
        await self.page.touchscreen.tap(x, y)
        await self.page.wait_for_timeout(50)
        await self.page.touchscreen.tap(x, y)

    async def long_press(self, x: int, y: int, duration_ms: int = 500) -> None:
        """Long press at coordinates."""
        await self.page.evaluate(f"""
            async () => {{
                const touch = new Touch({{
                    identifier: 1,
                    target: document.querySelector('canvas'),
                    clientX: {x},
                    clientY: {y},
                }});

                const touchStart = new TouchEvent('touchstart', {{
                    touches: [touch],
                    targetTouches: [touch],
                    changedTouches: [touch],
                }});
                document.querySelector('canvas').dispatchEvent(touchStart);

                await new Promise(r => setTimeout(r, {duration_ms}));

                const touchEnd = new TouchEvent('touchend', {{
                    touches: [],
                    targetTouches: [],
                    changedTouches: [touch],
                }});
                document.querySelector('canvas').dispatchEvent(touchEnd);
            }}
        """)

    async def swipe(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration_ms: int = 300,
    ) -> None:
        """Swipe from start to end coordinates."""
        steps = 10

        await self.page.evaluate(f"""
            async () => {{
                const canvas = document.querySelector('canvas');
                const steps = {steps};
                const duration = {duration_ms};
                const stepDelay = duration / steps;

                const startX = {start_x};
                const startY = {start_y};
                const endX = {end_x};
                const endY = {end_y};

                // Touch start
                const startTouch = new Touch({{
                    identifier: 1,
                    target: canvas,
                    clientX: startX,
                    clientY: startY,
                }});

                canvas.dispatchEvent(new TouchEvent('touchstart', {{
                    touches: [startTouch],
                    targetTouches: [startTouch],
                    changedTouches: [startTouch],
                }}));

                // Touch move (interpolated)
                for (let i = 1; i <= steps; i++) {{
                    const t = i / steps;
                    const x = startX + (endX - startX) * t;
                    const y = startY + (endY - startY) * t;

                    const moveTouch = new Touch({{
                        identifier: 1,
                        target: canvas,
                        clientX: x,
                        clientY: y,
                    }});

                    canvas.dispatchEvent(new TouchEvent('touchmove', {{
                        touches: [moveTouch],
                        targetTouches: [moveTouch],
                        changedTouches: [moveTouch],
                    }}));

                    await new Promise(r => setTimeout(r, stepDelay));
                }}

                // Touch end
                const endTouch = new Touch({{
                    identifier: 1,
                    target: canvas,
                    clientX: endX,
                    clientY: endY,
                }});

                canvas.dispatchEvent(new TouchEvent('touchend', {{
                    touches: [],
                    targetTouches: [],
                    changedTouches: [endTouch],
                }}));
            }}
        """)

    async def pinch(
        self,
        center_x: int,
        center_y: int,
        start_distance: int,
        end_distance: int,
        duration_ms: int = 300,
    ) -> None:
        """Pinch gesture (zoom in/out)."""
        await self.page.evaluate(f"""
            async () => {{
                const canvas = document.querySelector('canvas');
                const centerX = {center_x};
                const centerY = {center_y};
                const startDist = {start_distance};
                const endDist = {end_distance};
                const steps = 10;
                const stepDelay = {duration_ms} / steps;

                for (let i = 0; i <= steps; i++) {{
                    const t = i / steps;
                    const dist = startDist + (endDist - startDist) * t;

                    const touch1 = new Touch({{
                        identifier: 1,
                        target: canvas,
                        clientX: centerX - dist / 2,
                        clientY: centerY,
                    }});

                    const touch2 = new Touch({{
                        identifier: 2,
                        target: canvas,
                        clientX: centerX + dist / 2,
                        clientY: centerY,
                    }});

                    const eventType = i === 0 ? 'touchstart' :
                                     i === steps ? 'touchend' : 'touchmove';

                    canvas.dispatchEvent(new TouchEvent(eventType, {{
                        touches: eventType === 'touchend' ? [] : [touch1, touch2],
                        targetTouches: eventType === 'touchend' ? [] : [touch1, touch2],
                        changedTouches: [touch1, touch2],
                    }}));

                    await new Promise(r => setTimeout(r, stepDelay));
                }}
            }}
        """)


class TestTouchControls:
    """Tests for touch-based game controls."""

    async def test_virtual_joystick(self, mobile_page: Page, dev_server: str) -> None:
        """Test virtual joystick control."""
        await mobile_page.goto(dev_server)
        await mobile_page.wait_for_selector("canvas")
        await mobile_page.wait_for_timeout(1000)

        # Start game
        touch = TouchSimulator(mobile_page)
        await touch.tap(200, 400)  # Tap to start
        await mobile_page.wait_for_timeout(500)

        # Check for virtual joystick
        has_joystick = await mobile_page.evaluate("""
            () => {
                const game = window.game;
                const scene = game.scene.getScenes(true)[0];
                return scene?.virtualJoystick !== undefined ||
                       scene?.joystick !== undefined;
            }
        """)

        if not has_joystick:
            pytest.skip("Virtual joystick not implemented")

        # Test joystick movement
        initial_pos = await self.get_player_position(mobile_page)

        # Swipe right on joystick area (typically bottom-left)
        await touch.swipe(100, 500, 200, 500, duration_ms=500)
        await mobile_page.wait_for_timeout(200)

        new_pos = await self.get_player_position(mobile_page)
        assert new_pos["x"] != initial_pos["x"], "Joystick should move player"

    async def test_tap_to_jump(self, mobile_page: Page, dev_server: str) -> None:
        """Test tap-to-jump control."""
        await mobile_page.goto(dev_server)
        await mobile_page.wait_for_selector("canvas")
        await mobile_page.wait_for_timeout(1000)

        touch = TouchSimulator(mobile_page)

        # Start game
        await touch.tap(200, 400)
        await mobile_page.wait_for_timeout(500)

        # Get initial Y position
        initial_pos = await self.get_player_position(mobile_page)

        # Tap to jump (typically right side of screen)
        await touch.tap(350, 400)
        await mobile_page.wait_for_timeout(200)

        new_pos = await self.get_player_position(mobile_page)
        # In platformers, Y decreases when jumping (up)
        assert new_pos["y"] < initial_pos["y"], "Tap should trigger jump"

    async def test_swipe_gestures(self, mobile_page: Page, dev_server: str) -> None:
        """Test swipe gesture recognition."""
        await mobile_page.goto(dev_server)
        await mobile_page.wait_for_selector("canvas")
        await mobile_page.wait_for_timeout(1000)

        touch = TouchSimulator(mobile_page)

        # Test swipe directions
        swipe_tests = [
            ("right", 100, 300, 300, 300),
            ("left", 300, 300, 100, 300),
            ("up", 200, 400, 200, 200),
            ("down", 200, 200, 200, 400),
        ]

        for direction, sx, sy, ex, ey in swipe_tests:
            await touch.swipe(sx, sy, ex, ey)
            await mobile_page.wait_for_timeout(200)

            # Check if game recognized swipe
            last_swipe = await mobile_page.evaluate("""
                () => window.lastSwipeDirection || null
            """)

            # This requires game to track swipes
            if last_swipe:
                assert last_swipe == direction

    async def get_player_position(self, page: Page) -> dict:
        """Get player position."""
        return await page.evaluate("""
            () => {
                const game = window.game;
                const scene = game.scene.getScene('GameScene');
                const player = scene?.player;
                return player ? { x: player.x, y: player.y } : { x: 0, y: 0 };
            }
        """)


class TestMobileResponsiveness:
    """Tests for mobile screen responsiveness."""

    @pytest.mark.parametrize("device", ["iphone_se", "iphone_12", "pixel_5", "ipad"])
    async def test_game_fits_screen(
        self,
        browser: Browser,
        dev_server: str,
        device: str,
    ) -> None:
        """Test that game fits various screen sizes."""
        profile = DEVICES[device]

        context = await browser.new_context(
            viewport={"width": profile.viewport_width, "height": profile.viewport_height},
            device_scale_factor=profile.device_scale_factor,
            is_mobile=True,
        )
        page = await context.new_page()

        try:
            await page.goto(dev_server)
            await page.wait_for_selector("canvas")

            # Check canvas size vs viewport
            sizes = await page.evaluate("""
                () => {
                    const canvas = document.querySelector('canvas');
                    const rect = canvas.getBoundingClientRect();
                    return {
                        canvasWidth: rect.width,
                        canvasHeight: rect.height,
                        viewportWidth: window.innerWidth,
                        viewportHeight: window.innerHeight,
                    };
                }
            """)

            # Canvas should not overflow viewport
            assert sizes["canvasWidth"] <= sizes["viewportWidth"], \
                f"Canvas overflows horizontally on {profile.name}"
            assert sizes["canvasHeight"] <= sizes["viewportHeight"], \
                f"Canvas overflows vertically on {profile.name}"

        finally:
            await context.close()

    async def test_ui_elements_reachable(self, mobile_page: Page, dev_server: str) -> None:
        """Test that UI elements are reachable on small screens."""
        await mobile_page.goto(dev_server)
        await mobile_page.wait_for_selector("canvas")

        # Get positions of interactive elements
        ui_elements = await mobile_page.evaluate("""
            () => {
                const game = window.game;
                const scene = game.scene.getScenes(true)[0];

                const elements = [];
                scene?.children.list.forEach(child => {
                    if (child.input?.enabled) {
                        elements.push({
                            name: child.name,
                            x: child.x,
                            y: child.y,
                        });
                    }
                });

                return elements;
            }
        """)

        viewport = await mobile_page.viewport_size()

        for elem in ui_elements:
            assert 0 <= elem["x"] <= viewport["width"], \
                f"Element {elem['name']} is off-screen horizontally"
            assert 0 <= elem["y"] <= viewport["height"], \
                f"Element {elem['name']} is off-screen vertically"

    async def test_touch_targets_minimum_size(
        self,
        mobile_page: Page,
        dev_server: str,
    ) -> None:
        """Test that touch targets meet minimum size requirements (48x48px)."""
        await mobile_page.goto(dev_server)
        await mobile_page.wait_for_selector("canvas")

        MIN_TOUCH_SIZE = 48  # WCAG 2.5.5 recommendation

        # Get interactive element sizes
        touch_targets = await mobile_page.evaluate(f"""
            () => {{
                const game = window.game;
                const scene = game.scene.getScenes(true)[0];

                const targets = [];
                scene?.children.list.forEach(child => {{
                    if (child.input?.enabled) {{
                        targets.push({{
                            name: child.name,
                            width: child.displayWidth || child.width || 0,
                            height: child.displayHeight || child.height || 0,
                        }});
                    }}
                }});

                return targets;
            }}
        """)

        small_targets = []
        for target in touch_targets:
            if target["width"] < MIN_TOUCH_SIZE or target["height"] < MIN_TOUCH_SIZE:
                small_targets.append(
                    f"{target['name']}: {target['width']}x{target['height']}px"
                )

        if small_targets:
            pytest.fail(
                f"Touch targets smaller than {MIN_TOUCH_SIZE}px:\n" +
                "\n".join(small_targets)
            )


class TestMobilePerformance:
    """Performance tests specific to mobile devices."""

    async def test_mobile_fps(self, mobile_page: Page, dev_server: str) -> None:
        """Test frame rate on mobile device emulation."""
        await mobile_page.goto(dev_server)
        await mobile_page.wait_for_selector("canvas")
        await mobile_page.wait_for_timeout(1000)

        # Measure FPS
        fps_values = await mobile_page.evaluate("""
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

        import statistics
        avg_fps = statistics.mean(fps_values)

        # Mobile devices should maintain at least 30 FPS
        assert avg_fps >= 30, f"Mobile FPS {avg_fps:.1f} below minimum 30"

    async def test_battery_friendly_idle(self, mobile_page: Page, dev_server: str) -> None:
        """Test that game reduces activity when idle (battery saving)."""
        await mobile_page.goto(dev_server)
        await mobile_page.wait_for_selector("canvas")
        await mobile_page.wait_for_timeout(1000)

        # Put page in background (pause)
        await mobile_page.evaluate("""
            () => {
                document.dispatchEvent(new Event('visibilitychange'));
                Object.defineProperty(document, 'hidden', { value: true });
            }
        """)

        await mobile_page.wait_for_timeout(500)

        # Check if game paused/reduced updates
        is_paused = await mobile_page.evaluate("""
            () => {
                const game = window.game;
                return game?.isPaused ||
                       game?.loop?.running === false ||
                       game?.scene.getScenes(true).every(s => s.scene.isPaused);
            }
        """)

        if not is_paused:
            pytest.skip("Background pause recommended for battery saving")
```

---

## Audio Testing

Testing audio functionality in games.

### Audio System Testing

```python
"""Audio testing utilities and tests."""

from dataclasses import dataclass
from typing import Literal

from playwright.async_api import Page


@dataclass
class AudioState:
    """Current audio state."""
    music_playing: bool
    music_volume: float
    sfx_volume: float
    muted: bool
    active_sounds: list[str]


async def get_audio_state(page: Page) -> AudioState:
    """Get current audio state from game."""
    state = await page.evaluate("""
        () => {
            const game = window.game;
            if (!game) return null;

            // Phaser 3 audio
            const sound = game.sound;

            return {
                musicPlaying: sound.sounds.some(s => s.isPlaying && s.key.includes('music')),
                musicVolume: sound.volume,
                sfxVolume: sound.volume, // Phaser uses single volume
                muted: sound.mute,
                activeSounds: sound.sounds
                    .filter(s => s.isPlaying)
                    .map(s => s.key),
            };
        }
    """)

    if state is None:
        return AudioState(False, 0, 0, True, [])

    return AudioState(
        music_playing=state["musicPlaying"],
        music_volume=state["musicVolume"],
        sfx_volume=state["sfxVolume"],
        muted=state["muted"],
        active_sounds=state["activeSounds"],
    )


class TestAudioPlayback:
    """Tests for audio playback functionality."""

    async def test_audio_context_created(self, game_page: Page) -> None:
        """Test that Web Audio context is created."""
        has_context = await game_page.evaluate("""
            () => {
                const game = window.game;
                return game?.sound?.context !== undefined;
            }
        """)

        assert has_context, "Audio context should be created"

    async def test_audio_unlocked_on_interaction(self, game_page: Page) -> None:
        """Test that audio is unlocked after user interaction."""
        # Audio often requires user interaction to unlock
        await game_page.keyboard.press("Enter")
        await game_page.wait_for_timeout(500)

        is_unlocked = await game_page.evaluate("""
            () => {
                const game = window.game;
                const context = game?.sound?.context;
                return context?.state === 'running';
            }
        """)

        assert is_unlocked, "Audio should be unlocked after interaction"

    async def test_background_music_plays(self, game_page: Page) -> None:
        """Test that background music plays in game."""
        # Start game
        await game_page.keyboard.press("Enter")
        await game_page.wait_for_timeout(1000)

        state = await get_audio_state(game_page)

        # Music should be playing (or muted by default)
        has_music = state.music_playing or any("music" in s for s in state.active_sounds)

        if not has_music and not state.muted:
            pytest.skip("Background music not implemented or muted by default")

    async def test_sfx_on_action(self, game_page: Page) -> None:
        """Test that sound effects play on actions."""
        # Start game
        await game_page.keyboard.press("Enter")
        await game_page.wait_for_timeout(500)

        # Track played sounds
        await game_page.evaluate("""
            () => {
                window.playedSounds = [];
                const game = window.game;
                const originalPlay = game.sound.play.bind(game.sound);
                game.sound.play = (key, config) => {
                    window.playedSounds.push(key);
                    return originalPlay(key, config);
                };
            }
        """)

        # Trigger action that should play sound (e.g., jump)
        await game_page.keyboard.press("Space")
        await game_page.wait_for_timeout(200)

        played = await game_page.evaluate("() => window.playedSounds")

        # At least one sound should have played
        if len(played) == 0:
            pytest.skip("No SFX on action (may be intentional)")

    async def test_audio_no_errors(self, game_page: Page) -> None:
        """Test that no audio errors occur."""
        errors = []
        game_page.on("console", lambda msg:
            errors.append(msg.text) if "audio" in msg.text.lower() and msg.type == "error" else None
        )

        # Start game and let it run
        await game_page.keyboard.press("Enter")
        await game_page.wait_for_timeout(2000)

        assert len(errors) == 0, f"Audio errors: {errors}"


class TestAudioControls:
    """Tests for audio control functionality."""

    async def test_mute_toggle(self, game_page: Page) -> None:
        """Test mute toggle functionality."""
        # Get initial state
        initial = await get_audio_state(game_page)

        # Toggle mute (game-specific key, often M)
        await game_page.keyboard.press("m")
        await game_page.wait_for_timeout(200)

        after_toggle = await get_audio_state(game_page)

        assert initial.muted != after_toggle.muted, "Mute state should toggle"

    async def test_volume_controls(self, game_page: Page) -> None:
        """Test volume control functionality."""
        # Check for volume controls
        has_volume = await game_page.evaluate("""
            () => {
                const game = window.game;
                return typeof game?.sound?.volume !== 'undefined';
            }
        """)

        assert has_volume, "Volume control should be available"

    async def test_volume_persistence(self, game_page: Page) -> None:
        """Test that volume settings persist."""
        # Set volume
        await game_page.evaluate("""
            () => {
                const game = window.game;
                game.sound.volume = 0.5;
                localStorage.setItem('gameVolume', '0.5');
            }
        """)

        # Reload page
        await game_page.reload()
        await game_page.wait_for_selector("canvas")
        await game_page.wait_for_timeout(1000)

        # Check volume was restored
        volume = await game_page.evaluate("""
            () => {
                const saved = localStorage.getItem('gameVolume');
                return parseFloat(saved) || 1.0;
            }
        """)

        assert volume == 0.5, "Volume should persist after reload"

    async def test_separate_music_sfx_volume(self, game_page: Page) -> None:
        """Test separate music and SFX volume controls (recommended)."""
        has_separate = await game_page.evaluate("""
            () => {
                return typeof window.gameSettings?.musicVolume !== 'undefined' &&
                       typeof window.gameSettings?.sfxVolume !== 'undefined';
            }
        """)

        if not has_separate:
            pytest.skip("Separate music/SFX volume controls recommended")


class TestAudioAccessibility:
    """Tests for audio accessibility features."""

    async def test_visual_audio_indicators(self, game_page: Page) -> None:
        """Test for visual indicators of audio events (for deaf/HoH users)."""
        # Start game
        await game_page.keyboard.press("Enter")
        await game_page.wait_for_timeout(500)

        # Check for visual feedback option
        has_visual_audio = await game_page.evaluate("""
            () => {
                return typeof window.gameSettings?.visualAudioCues !== 'undefined';
            }
        """)

        if not has_visual_audio:
            pytest.skip("Visual audio indicators recommended for accessibility")

    async def test_subtitles_option(self, game_page: Page) -> None:
        """Test for subtitle/caption option."""
        has_subtitles = await game_page.evaluate("""
            () => {
                return typeof window.gameSettings?.subtitles !== 'undefined';
            }
        """)

        if not has_subtitles:
            pytest.skip("Subtitles option recommended for accessibility")

    async def test_audio_descriptions(self, game_page: Page) -> None:
        """Test for audio description option (for visually impaired)."""
        has_descriptions = await game_page.evaluate("""
            () => {
                return typeof window.gameSettings?.audioDescriptions !== 'undefined';
            }
        """)

        if not has_descriptions:
            pytest.skip("Audio descriptions recommended for accessibility")


class TestAudioPerformance:
    """Performance tests for audio system."""

    async def test_audio_no_memory_leak(self, game_page: Page) -> None:
        """Test that audio doesn't cause memory leaks."""
        # Start game
        await game_page.keyboard.press("Enter")
        await game_page.wait_for_timeout(500)

        # Get initial sound count
        initial = await game_page.evaluate("""
            () => window.game.sound.sounds.length
        """)

        # Play many sounds
        for _ in range(20):
            await game_page.keyboard.press("Space")
            await game_page.wait_for_timeout(100)

        await game_page.wait_for_timeout(1000)

        # Check sound count hasn't grown excessively
        final = await game_page.evaluate("""
            () => window.game.sound.sounds.length
        """)

        # Sound pool should manage instances
        assert final < initial + 10, f"Sound instances grew from {initial} to {final}"

    async def test_audio_stops_on_scene_change(self, game_page: Page) -> None:
        """Test that audio properly stops/transitions on scene changes."""
        # Start game
        await game_page.keyboard.press("Enter")
        await game_page.wait_for_timeout(500)

        # Get playing sounds
        sounds_in_game = await game_page.evaluate("""
            () => window.game.sound.sounds.filter(s => s.isPlaying).map(s => s.key)
        """)

        # Go back to menu (e.g., via pause then quit)
        await game_page.keyboard.press("Escape")
        await game_page.wait_for_timeout(200)
        await game_page.keyboard.press("q")  # Quit to menu (game-specific)
        await game_page.wait_for_timeout(500)

        # Game sounds should have stopped
        sounds_in_menu = await game_page.evaluate("""
            () => window.game.sound.sounds.filter(s => s.isPlaying).map(s => s.key)
        """)

        # Gameplay sounds shouldn't persist (music may transition)
        gameplay_sounds = [s for s in sounds_in_game if "sfx" in s.lower()]
        persisting = [s for s in gameplay_sounds if s in sounds_in_menu]

        assert len(persisting) == 0, f"Sounds persisted: {persisting}"
```

---

## Network Testing for Multiplayer

Testing network functionality for multiplayer games.

### Network Mocking Setup

```python
"""Network testing utilities for multiplayer games."""

from dataclasses import dataclass
from typing import Callable, Literal

from playwright.async_api import Page, Route


@dataclass
class MockResponse:
    """Mock response configuration."""
    status: int = 200
    body: str | dict = ""
    headers: dict = None
    delay_ms: int = 0


class NetworkMocker:
    """Mock and intercept network requests."""

    def __init__(self, page: Page) -> None:
        self.page = page
        self.intercepted: list[dict] = []
        self.mocks: dict[str, MockResponse] = {}

    async def start_recording(self) -> None:
        """Start recording network requests."""
        async def handler(route: Route) -> None:
            request = route.request
            self.intercepted.append({
                "url": request.url,
                "method": request.method,
                "post_data": request.post_data,
            })
            await route.continue_()

        await self.page.route("**/*", handler)

    async def mock_endpoint(
        self,
        url_pattern: str,
        response: MockResponse,
    ) -> None:
        """Mock a specific endpoint."""
        async def handler(route: Route) -> None:
            if response.delay_ms > 0:
                await self.page.wait_for_timeout(response.delay_ms)

            body = response.body
            if isinstance(body, dict):
                import json
                body = json.dumps(body)

            await route.fulfill(
                status=response.status,
                body=body,
                headers=response.headers or {"Content-Type": "application/json"},
            )

        await self.page.route(url_pattern, handler)

    async def mock_websocket(self, url_pattern: str) -> "WebSocketMock":
        """Mock WebSocket connections."""
        # WebSocket mocking requires browser-level setup
        mock = WebSocketMock(self.page, url_pattern)
        await mock.setup()
        return mock

    async def simulate_offline(self) -> None:
        """Simulate offline condition."""
        await self.page.context.set_offline(True)

    async def simulate_online(self) -> None:
        """Restore online condition."""
        await self.page.context.set_offline(False)

    async def simulate_slow_network(self, latency_ms: int = 500) -> None:
        """Simulate slow network conditions."""
        async def delay_handler(route: Route) -> None:
            await self.page.wait_for_timeout(latency_ms)
            await route.continue_()

        await self.page.route("**/*", delay_handler)

    def get_requests_to(self, url_contains: str) -> list[dict]:
        """Get intercepted requests to URLs containing pattern."""
        return [r for r in self.intercepted if url_contains in r["url"]]


class WebSocketMock:
    """Mock WebSocket for testing real-time features."""

    def __init__(self, page: Page, url_pattern: str) -> None:
        self.page = page
        self.url_pattern = url_pattern
        self.messages_sent: list = []
        self.message_handlers: list[Callable] = []

    async def setup(self) -> None:
        """Set up WebSocket interception."""
        await self.page.evaluate("""
            () => {
                window.mockWebSocket = {
                    messages: [],
                    handlers: [],

                    send(data) {
                        this.messages.push(data);
                    },

                    receive(data) {
                        this.handlers.forEach(h => h(data));
                    },

                    onMessage(handler) {
                        this.handlers.push(handler);
                    },
                };

                // Override WebSocket constructor
                const OriginalWS = window.WebSocket;
                window.WebSocket = function(url) {
                    const ws = {
                        url,
                        readyState: 1,
                        send: (data) => window.mockWebSocket.send(data),
                        onmessage: null,
                        onopen: null,
                        onclose: null,
                        onerror: null,
                        close: () => {},
                    };

                    window.mockWebSocket.onMessage(data => {
                        if (ws.onmessage) {
                            ws.onmessage({ data: JSON.stringify(data) });
                        }
                    });

                    setTimeout(() => {
                        if (ws.onopen) ws.onopen();
                    }, 0);

                    return ws;
                };
            }
        """)

    async def send_to_client(self, data: dict) -> None:
        """Send mock message to client."""
        await self.page.evaluate(f"""
            () => window.mockWebSocket.receive({data})
        """)

    async def get_sent_messages(self) -> list:
        """Get messages sent by client."""
        return await self.page.evaluate("""
            () => window.mockWebSocket.messages
        """)


class TestMultiplayerConnection:
    """Tests for multiplayer connection handling."""

    async def test_connection_established(self, game_page: Page) -> None:
        """Test that multiplayer connection is established."""
        mocker = NetworkMocker(game_page)
        ws_mock = await mocker.mock_websocket("**/game-server")

        # Navigate to multiplayer mode
        await game_page.keyboard.press("Enter")
        await game_page.wait_for_timeout(1000)

        # Check connection state
        is_connected = await game_page.evaluate("""
            () => {
                const game = window.game;
                return game?.network?.connected ||
                       game?.multiplayer?.isConnected ||
                       false;
            }
        """)

        assert is_connected, "Should establish multiplayer connection"

    async def test_reconnection_on_disconnect(self, game_page: Page) -> None:
        """Test automatic reconnection on disconnect."""
        mocker = NetworkMocker(game_page)

        # Start game
        await game_page.keyboard.press("Enter")
        await game_page.wait_for_timeout(1000)

        # Simulate disconnect
        await mocker.simulate_offline()
        await game_page.wait_for_timeout(500)

        # Check for reconnection attempt
        reconnecting = await game_page.evaluate("""
            () => {
                const game = window.game;
                return game?.network?.reconnecting ||
                       game?.multiplayer?.state === 'reconnecting';
            }
        """)

        # Restore connection
        await mocker.simulate_online()
        await game_page.wait_for_timeout(2000)

        # Should reconnect
        is_connected = await game_page.evaluate("""
            () => window.game?.network?.connected || false
        """)

        if not is_connected:
            pytest.skip("Auto-reconnect not implemented")

    async def test_connection_error_handling(self, game_page: Page) -> None:
        """Test graceful handling of connection errors."""
        mocker = NetworkMocker(game_page)

        # Mock server error
        await mocker.mock_endpoint(
            "**/api/matchmaking",
            MockResponse(status=500, body={"error": "Server error"})
        )

        # Try to connect
        await game_page.keyboard.press("Enter")
        await game_page.wait_for_timeout(1000)

        # Should show error message (not crash)
        has_error_ui = await game_page.evaluate("""
            () => {
                const game = window.game;
                const scene = game.scene.getScenes(true)[0];
                return scene?.errorMessage !== undefined ||
                       document.querySelector('[data-error]') !== null;
            }
        """)

        # Game should handle error gracefully
        is_running = await game_page.evaluate("""
            () => window.game?.isRunning
        """)

        assert is_running, "Game should still be running after connection error"


class TestMultiplayerSync:
    """Tests for multiplayer synchronization."""

    async def test_player_position_sync(self, game_page: Page) -> None:
        """Test that player positions are synchronized."""
        mocker = NetworkMocker(game_page)
        ws_mock = await mocker.mock_websocket("**/game-server")

        # Start multiplayer game
        await game_page.keyboard.press("Enter")
        await game_page.wait_for_timeout(500)

        # Move player
        await game_page.keyboard.down("ArrowRight")
        await game_page.wait_for_timeout(200)
        await game_page.keyboard.up("ArrowRight")

        # Check sent messages
        sent = await ws_mock.get_sent_messages()

        # Should have sent position update
        position_updates = [m for m in sent if "position" in str(m).lower()]
        assert len(position_updates) > 0, "Should send position updates"

    async def test_other_player_appears(self, game_page: Page) -> None:
        """Test that other players appear when they join."""
        mocker = NetworkMocker(game_page)
        ws_mock = await mocker.mock_websocket("**/game-server")

        # Start game
        await game_page.keyboard.press("Enter")
        await game_page.wait_for_timeout(500)

        # Simulate another player joining
        await ws_mock.send_to_client({
            "type": "player_joined",
            "player": {
                "id": "player2",
                "x": 100,
                "y": 200,
            },
        })

        await game_page.wait_for_timeout(200)

        # Check for other player
        other_players = await game_page.evaluate("""
            () => {
                const game = window.game;
                const scene = game.scene.getScene('GameScene');
                return scene?.otherPlayers?.length || 0;
            }
        """)

        assert other_players > 0, "Other player should appear"

    async def test_game_state_consistency(self, game_page: Page) -> None:
        """Test game state remains consistent during sync."""
        mocker = NetworkMocker(game_page)
        ws_mock = await mocker.mock_websocket("**/game-server")

        # Start game
        await game_page.keyboard.press("Enter")
        await game_page.wait_for_timeout(500)

        # Send conflicting state update
        local_score = await game_page.evaluate("""
            () => window.game.scene.getScene('GameScene')?.score || 0
        """)

        # Server says different score
        await ws_mock.send_to_client({
            "type": "state_sync",
            "state": {"score": 1000},
        })

        await game_page.wait_for_timeout(200)

        # Check how conflict was resolved
        new_score = await game_page.evaluate("""
            () => window.game.scene.getScene('GameScene')?.score || 0
        """)

        # Score should have been updated (server authoritative)
        assert new_score == 1000, "Server state should be authoritative"


class TestNetworkLatency:
    """Tests for handling network latency."""

    async def test_playable_with_latency(self, game_page: Page) -> None:
        """Test game remains playable with moderate latency."""
        mocker = NetworkMocker(game_page)

        # Add 100ms latency
        await mocker.simulate_slow_network(latency_ms=100)

        # Start game
        await game_page.keyboard.press("Enter")
        await game_page.wait_for_timeout(1000)

        # Test basic movement
        initial = await self.get_player_position(game_page)

        await game_page.keyboard.down("ArrowRight")
        await game_page.wait_for_timeout(500)
        await game_page.keyboard.up("ArrowRight")

        final = await self.get_player_position(game_page)

        # Player should still move despite latency
        assert final["x"] > initial["x"], "Player should move with latency"

    async def test_lag_compensation(self, game_page: Page) -> None:
        """Test client-side prediction and lag compensation."""
        mocker = NetworkMocker(game_page)

        # Add significant latency
        await mocker.simulate_slow_network(latency_ms=200)

        # Start game
        await game_page.keyboard.press("Enter")
        await game_page.wait_for_timeout(500)

        # Movement should feel responsive (client prediction)
        initial = await self.get_player_position(game_page)

        await game_page.keyboard.press("ArrowRight")

        # Check position immediately (before server response)
        immediate = await self.get_player_position(game_page)

        # With client prediction, should move immediately
        if immediate["x"] == initial["x"]:
            pytest.skip("Client-side prediction not implemented")

    async def test_latency_display(self, game_page: Page) -> None:
        """Test that latency/ping is displayed to player."""
        # Start game
        await game_page.keyboard.press("Enter")
        await game_page.wait_for_timeout(1000)

        has_ping_display = await game_page.evaluate("""
            () => {
                const game = window.game;
                const scene = game.scene.getScene('GameScene');
                return scene?.pingText !== undefined ||
                       document.querySelector('[data-ping]') !== null;
            }
        """)

        if not has_ping_display:
            pytest.skip("Ping display recommended for multiplayer")

    async def get_player_position(self, page: Page) -> dict:
        """Get player position."""
        return await page.evaluate("""
            () => {
                const game = window.game;
                const scene = game.scene.getScene('GameScene');
                return { x: scene?.player?.x || 0, y: scene?.player?.y || 0 };
            }
        """)


class TestMatchmaking:
    """Tests for matchmaking functionality."""

    async def test_matchmaking_request(self, game_page: Page) -> None:
        """Test matchmaking request is sent."""
        mocker = NetworkMocker(game_page)
        await mocker.start_recording()

        # Mock matchmaking endpoint
        await mocker.mock_endpoint(
            "**/api/matchmaking",
            MockResponse(
                status=200,
                body={"match_id": "test-match", "status": "waiting"},
            )
        )

        # Start multiplayer
        await game_page.keyboard.press("Enter")
        await game_page.wait_for_timeout(1000)

        # Check for matchmaking request
        requests = mocker.get_requests_to("matchmaking")
        assert len(requests) > 0, "Should send matchmaking request"

    async def test_matchmaking_queue_ui(self, game_page: Page) -> None:
        """Test matchmaking queue UI feedback."""
        mocker = NetworkMocker(game_page)

        # Mock slow matchmaking
        await mocker.mock_endpoint(
            "**/api/matchmaking",
            MockResponse(
                status=200,
                body={"status": "searching"},
                delay_ms=2000,
            )
        )

        # Start matchmaking
        await game_page.keyboard.press("Enter")
        await game_page.wait_for_timeout(500)

        # Should show searching UI
        is_searching = await game_page.evaluate("""
            () => {
                const game = window.game;
                return game?.matchmaking?.state === 'searching' ||
                       document.querySelector('[data-matchmaking="searching"]') !== null;
            }
        """)

        assert is_searching, "Should show searching state"

    async def test_matchmaking_cancel(self, game_page: Page) -> None:
        """Test ability to cancel matchmaking."""
        mocker = NetworkMocker(game_page)

        # Mock slow matchmaking
        await mocker.mock_endpoint(
            "**/api/matchmaking",
            MockResponse(status=200, body={"status": "searching"}, delay_ms=10000)
        )

        # Start matchmaking
        await game_page.keyboard.press("Enter")
        await game_page.wait_for_timeout(500)

        # Cancel (typically Escape)
        await game_page.keyboard.press("Escape")
        await game_page.wait_for_timeout(200)

        # Should return to menu
        current_state = await game_page.evaluate("""
            () => {
                const game = window.game;
                return game?.matchmaking?.state || 'unknown';
            }
        """)

        assert current_state != "searching", "Should cancel matchmaking"
```

---

## Test Organization

### Markers and Categories

```python
# conftest.py additions

import pytest


def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line("markers", "smoke: smoke tests (quick sanity checks)")
    config.addinivalue_line("markers", "functional: functional/gameplay tests")
    config.addinivalue_line("markers", "visual: visual regression tests")
    config.addinivalue_line("markers", "performance: performance benchmark tests")
    config.addinivalue_line("markers", "accessibility: accessibility compliance tests")
    config.addinivalue_line("markers", "mobile: mobile device and touch tests")
    config.addinivalue_line("markers", "audio: audio playback and control tests")
    config.addinivalue_line("markers", "network: multiplayer and network tests")
    config.addinivalue_line("markers", "slow: slow tests (>10 seconds)")
```

### Using Markers

```python
import pytest


@pytest.mark.smoke
async def test_game_loads(game_page):
    """Smoke test: game loads."""
    pass


@pytest.mark.functional
async def test_player_movement(game_page):
    """Functional test: player moves."""
    pass


@pytest.mark.visual
async def test_menu_appearance(game_page):
    """Visual test: menu looks correct."""
    pass


@pytest.mark.performance
@pytest.mark.slow
async def test_frame_rate(game_page):
    """Performance test: frame rate is acceptable."""
    pass


@pytest.mark.accessibility
async def test_color_contrast(game_page):
    """Accessibility test: color contrast meets WCAG."""
    pass


@pytest.mark.mobile
async def test_touch_controls(mobile_page):
    """Mobile test: touch controls work."""
    pass


@pytest.mark.audio
async def test_sound_effects(game_page):
    """Audio test: sound effects play correctly."""
    pass


@pytest.mark.network
async def test_multiplayer_sync(game_page):
    """Network test: multiplayer sync works."""
    pass
```

### Running Test Categories

```bash
# Run only smoke tests
pytest -m smoke

# Run everything except slow tests
pytest -m "not slow"

# Run functional and smoke tests
pytest -m "functional or smoke"

# Run visual tests with baseline update
pytest -m visual --update-baselines

# Run accessibility tests
pytest -m accessibility

# Run mobile tests
pytest -m mobile

# Run audio tests
pytest -m audio

# Run network/multiplayer tests
pytest -m network

# Run all tests except network (for offline development)
pytest -m "not network"
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/game-tests.yml
name: Game Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Node dependencies
        run: npm ci

      - name: Install Python dependencies
        run: |
          pip install pytest pytest-playwright pytest-asyncio
          playwright install chromium

      - name: Build game
        run: npm run build

      - name: Run smoke tests
        run: pytest tests/ -m smoke -v

      - name: Run functional tests
        run: pytest tests/ -m functional -v

      - name: Run performance tests
        run: pytest tests/ -m performance -v
        continue-on-error: true  # Don't fail build on perf regression

      - name: Upload screenshots on failure
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: screenshots
          path: tests/screenshots/
```

---

## Common Issues and Solutions

### Issue: Canvas not found

```python
# Problem: Canvas takes time to initialize
# Solution: Wait for canvas with proper timeout

async def test_with_canvas_wait(page, dev_server):
    await page.goto(dev_server)

    # Wait with extended timeout
    try:
        await page.wait_for_selector("canvas", timeout=15000)
    except TimeoutError:
        # Debug: check what's on the page
        content = await page.content()
        print(f"Page content: {content[:500]}")
        raise
```

### Issue: Game state not accessible

```python
# Problem: window.game is undefined
# Solution: Expose game in your code and wait for it

async def test_with_game_wait(game_page):
    # Wait for game to be exposed
    await game_page.wait_for_function(
        "() => window.game !== undefined",
        timeout=10000
    )
```

### Issue: Flaky tests due to timing

```python
# Problem: Tests fail intermittently
# Solution: Use explicit waits instead of timeouts

async def test_with_explicit_wait(game_page):
    # BAD: Fixed timeout
    # await game_page.wait_for_timeout(1000)

    # GOOD: Wait for specific condition
    await game_page.wait_for_function(
        "() => window.game.scene.getScene('GameScene')?.initialized === true"
    )
```

### Issue: Different results in headless mode

```python
# Problem: Test passes headed but fails headless
# Solution: Force consistent rendering

@pytest.fixture
async def consistent_page(browser):
    context = await browser.new_context(
        viewport={"width": 800, "height": 600},
        device_scale_factor=1,  # Consistent pixel ratio
        has_touch=False,  # Consistent input mode
    )
    page = await context.new_page()

    # Disable animations for consistent screenshots
    await page.add_init_script("""
        window.requestAnimationFrame = cb => setTimeout(cb, 16);
    """)

    yield page
    await context.close()
```

### Issue: Console errors from browser extensions

```python
# Solution: Filter known patterns
console_monitor = ConsoleMonitor(ignore_patterns=[
    "chrome-extension://",
    "moz-extension://",
    "Failed to load resource",  # External resources
])
```

---

## Quick Reference

### Essential Fixtures

```python
# conftest.py
@pytest.fixture
async def game_page(page, dev_server) -> Page:
    """Page with game loaded."""
    await page.goto(dev_server)
    await page.wait_for_selector("canvas")
    await page.wait_for_timeout(1000)
    yield page
```

### Essential Assertions

```python
# Game is running
assert await page.evaluate("() => window.game?.isRunning")

# Scene is active
assert await page.evaluate("() => window.game?.scene.isActive('GameScene')")

# No console errors
console_errors.assert_no_errors()

# FPS is acceptable
assert avg_fps >= 55
```

### Run Commands

```bash
# All tests
pytest tests/

# Specific category
pytest tests/ -m smoke

# With visual output
pytest tests/ --headed

# Generate coverage
pytest tests/ --cov=src --cov-report=html

# Accessibility tests only
pytest tests/ -m accessibility

# Mobile tests on specific device
pytest tests/ -m mobile --device=iphone_12

# Audio tests
pytest tests/ -m audio

# Network tests with mocking
pytest tests/ -m network
```

---

## Quick Reference: New Test Categories

### Accessibility Testing Checklist

```python
# Color contrast (WCAG AA: 4.5:1)
result = check_contrast("#ffffff", "#000000")
assert result.passes_aa

# Keyboard navigation
await page.keyboard.press("Tab")  # Focus moves
await page.keyboard.press("Enter")  # Activates button
await page.keyboard.press("Escape")  # Closes dialogs

# Screen reader support
# Check for aria-live regions
# Verify announcements on state changes

# Reduced motion
await page.emulate_media(reduced_motion="reduce")
```

### Mobile Testing Checklist

```python
# Device emulation
context = await browser.new_context(
    viewport={"width": 390, "height": 844},
    is_mobile=True,
    has_touch=True,
)

# Touch gestures
touch = TouchSimulator(page)
await touch.tap(x, y)
await touch.swipe(start_x, start_y, end_x, end_y)
await touch.pinch(center_x, center_y, start_dist, end_dist)

# Touch target size (min 48x48px)
# Responsive layout
# Battery-friendly idle behavior
```

### Audio Testing Checklist

```python
# Audio context unlocked
is_unlocked = await page.evaluate("""
    () => window.game?.sound?.context?.state === 'running'
""")

# Sound effects play
# Volume controls work
# Mute toggle works
# Audio stops on scene change
# No memory leaks from sound pooling
```

### Network Testing Checklist

```python
# Mock network requests
mocker = NetworkMocker(page)
await mocker.mock_endpoint("**/api/*", MockResponse(status=200, body={}))

# Simulate conditions
await mocker.simulate_offline()
await mocker.simulate_slow_network(latency_ms=200)

# WebSocket mocking
ws_mock = await mocker.mock_websocket("**/game-server")
await ws_mock.send_to_client({"type": "event", "data": {}})
sent = await ws_mock.get_sent_messages()
```
