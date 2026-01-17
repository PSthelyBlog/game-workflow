# Game Testing Skill

This skill provides Claude Code with comprehensive knowledge for automated game testing using Playwright, including browser automation, visual testing, performance benchmarking, and quality assurance patterns.

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
12. [Test Organization](#test-organization)
13. [CI/CD Integration](#cicd-integration)
14. [Common Issues and Solutions](#common-issues-and-solutions)

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
```
