# Game Testing Skill

This skill provides Claude Code with knowledge for automated game testing.

## Overview

This skill covers:
- Playwright-based browser testing
- Screenshot comparison
- Performance benchmarks
- Accessibility testing

## Test Structure

```
tests/
├── conftest.py         # Fixtures
├── test_gameplay.py    # Gameplay tests
├── test_ui.py          # UI tests
├── test_performance.py # Performance tests
└── screenshots/
    └── baseline/       # Reference screenshots
```

## Playwright Setup

```python
import pytest
from playwright.async_api import async_playwright

@pytest.fixture
async def game_page():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("http://localhost:5173")
        yield page
        await browser.close()
```

## Common Test Patterns

### Game Load Test
```python
async def test_game_loads(game_page):
    # Wait for game canvas
    canvas = await game_page.wait_for_selector("canvas")
    assert canvas is not None

    # Check for no console errors
    errors = []
    game_page.on("console", lambda msg: errors.append(msg) if msg.type == "error" else None)
    await game_page.wait_for_timeout(2000)
    assert len(errors) == 0
```

### Input Test
```python
async def test_player_movement(game_page):
    await game_page.keyboard.press("ArrowRight")
    await game_page.wait_for_timeout(500)
    # Verify player moved via screenshot or game state
```

### Screenshot Comparison
```python
async def test_main_menu_appearance(game_page):
    await game_page.wait_for_selector("[data-scene='menu']")
    screenshot = await game_page.screenshot()
    # Compare with baseline
    assert_screenshots_match(screenshot, "baseline/menu.png")
```

## Performance Testing

```python
async def test_frame_rate(game_page):
    # Inject FPS counter
    fps_values = await game_page.evaluate("""
        () => new Promise(resolve => {
            const frames = [];
            let lastTime = performance.now();
            const measure = () => {
                const now = performance.now();
                frames.push(1000 / (now - lastTime));
                lastTime = now;
                if (frames.length < 60) requestAnimationFrame(measure);
                else resolve(frames);
            };
            requestAnimationFrame(measure);
        })
    """)
    avg_fps = sum(fps_values) / len(fps_values)
    assert avg_fps >= 55, f"FPS too low: {avg_fps}"
```

## Best Practices

1. Use stable selectors (data attributes)
2. Add appropriate waits for animations
3. Test on multiple viewport sizes
4. Run tests in headless mode for CI
5. Store baseline screenshots in version control
