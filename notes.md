# Session Notes — Game Workflow Implementation

> Notes and observations from implementation sessions to help future work.

---

## Session 1: 2026-01-16 — Phase 0 Complete

### Environment Setup

**Python Version:**
- System Python was 3.9.6, but project requires Python 3.11+
- Installed Python 3.11.9 via official macOS installer from python.org
- Location: `/usr/local/bin/python3.11`
- Virtual environment created with: `/usr/local/bin/python3.11 -m venv .venv`

**GitHub CLI:**
- `gh` CLI was not installed
- Downloaded v2.85.0 for macOS ARM64 and installed to `~/bin/gh`
- Authenticated with PAT (requires `repo`, `read:org`, `workflow` scopes)

### Key Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Install project in dev mode
pip install -e ".[dev]"

# Run linting
ruff check .
ruff format .

# Run type checking
mypy src/game_workflow

# Run tests
pytest tests/unit -v

# Test CLI
game-workflow --help
```

### Issues Encountered & Solutions

1. **Ruff linting errors:**
   - `PTH123`: Use `Path.open()` instead of `open()` for pathlib objects
   - `F401`: Remove unused imports

2. **Mypy type errors:**
   - Base class `run()` method signature was too restrictive
   - Changed from `**kwargs: Any` to `*args: Any, **kwargs: Any` to allow subclass variations
   - Missing type parameters for `dict` — use `dict[str, Any]` not just `dict`

3. **Ruff formatter:**
   - CI runs `ruff format --check .` which fails if files need reformatting
   - Always run `ruff format .` before committing

### GitHub Workflow

Per CLAUDE.md, all work must go through Issues and PRs:

1. Create GitHub Issue for the work
2. Create feature branch: `git checkout -b feature/<issue-number>-<description>`
3. Implement and commit with messages referencing issue
4. Push and create PR with `gh pr create`
5. After CI passes, merge with `gh pr merge <number> --squash --delete-branch`
6. Update `implementation-plan.md` on main branch
7. Update `notes.md` on main branch

### Files Created in Phase 0

**Core Structure:**
- `pyproject.toml` — hatch build system, dependencies
- `src/game_workflow/` — main package with all submodules
- `tests/` — unit, integration, e2e test directories

**Config Files:**
- `ruff.toml` — linting rules
- `mypy.ini` — type checking config
- `.pre-commit-config.yaml` — pre-commit hooks
- `.github/workflows/ci.yml` — GitHub Actions

**Templates & Skills:**
- `templates/gdd-template.md`, `concept-template.md`, `itchio-page.md`
- `skills/phaser-game/SKILL.md`, `godot-game/SKILL.md`, `game-testing/SKILL.md`

### Dependencies Installed

From pyproject.toml:
- `anthropic>=0.40.0` — Claude API client
- `mcp>=1.0.0` — MCP protocol
- `httpx>=0.25.0` — Async HTTP client
- `pydantic>=2.0.0` — Data validation
- `pydantic-settings>=2.0.0` — Settings management
- `typer>=0.9.0` — CLI framework
- `rich>=13.0.0` — Terminal formatting

### Architecture Notes

**Agent Pattern:**
- All agents inherit from `BaseAgent`
- Each agent has a `name` property and `run()` method
- Default model: `claude-sonnet-4-5-20250929`

**State Management:**
- `WorkflowState` is a Pydantic model
- Saves to `~/.game-workflow/state/<id>.json`
- Supports save/load/get_latest operations

**MCP Server Registry:**
- Registers GitHub, Slack (official), and itch.io (custom) servers
- Each server has command, args, and env configuration

---

## Session 2: 2026-01-16 — Phase 1 Complete

### Summary

Implemented all 8 tasks for Phase 1 Core Infrastructure in a single PR (#4).

### Key Implementation Decisions

**Configuration (1.1):**
- Used `tomli` for TOML parsing (already in dependencies)
- TOML config loaded BEFORE env vars via Pydantic's `model_validator(mode="before")`
- Added `_deep_merge()` helper to merge nested config dicts
- Settings are cached with `@lru_cache` and can be refreshed with `reload_settings()`

**State Management (1.2):**
- Moved `WorkflowPhase` enum from workflow.py to state.py to avoid circular imports
- State transitions are validated with `can_transition_to()` method
- Added `CheckpointData` Pydantic model for checkpoint tracking
- QA phase can go back to BUILD (for fix-and-retry flows)

**Workflow Orchestrator (1.3):**
- Hooks are called via `_notify_phase_start()`, `_notify_phase_complete()`, `_notify_error()`
- Hook failures are logged but don't stop the workflow
- Stub implementations for agent phases return `{"status": "stub"}` for testing

**Exceptions (1.4):**
- All exceptions now have optional `context: dict[str, Any]` parameter
- `InvalidTransitionError` stores `from_phase` and `to_phase` attributes
- Used `TYPE_CHECKING` block for `WorkflowPhase` import to avoid circular imports

**CLI (1.5):**
- Used `typer.Typer()` subgroups for `state` commands
- Rich Console for all output with phase-specific colors
- Type narrowing pattern for mypy: declare `state: WorkflowState | None = None` before conditional branches

**Base Agent (1.6):**
- Added `execute()` wrapper that calls `run()` with error handling
- `_validate_config()` checks for API key before execution
- Logging methods delegate to a per-agent logger: `logging.getLogger(f"game_workflow.agents.{self.name}")`

**Hooks (1.7-1.8):**
- Logging hook sets up file rotation: 10MB max, 5 backups
- `setup_logging()` uses module-level `_logging_configured` flag to avoid duplicate setup
- Checkpoint hook auto-prunes when exceeding `max_checkpoints` (default 50)
- Used `# noqa: ARG002` for unused protocol arguments (required for interface compatibility)

### Issues Encountered & Solutions

1. **Circular imports:**
   - `WorkflowPhase` was in workflow.py but exceptions.py needed it
   - Solution: Moved `WorkflowPhase` to state.py, use `TYPE_CHECKING` block in exceptions.py

2. **Mypy type narrowing:**
   - `if state_id: state = load() else: state = get_latest()` didn't narrow type
   - Solution: Declare `state: WorkflowState | None = None` at start, check `if state is None` after

3. **Path import for TYPE_CHECKING:**
   - Ruff TC003 wants `Path` in TYPE_CHECKING block when only used for type hints
   - Solution: `from typing import TYPE_CHECKING` + `if TYPE_CHECKING: from pathlib import Path`

4. **Test timing issues:**
   - `WorkflowState` uses timestamp for ID, fast tests created duplicates
   - Solution: Use explicit unique IDs in tests: `WorkflowState(id="state_001", ...)`

5. **Settings persistence across tests:**
   - `get_settings()` is cached, tests need to reset between runs
   - Solution: Call `reload_settings()` after changing env vars with monkeypatch

6. **Exception chaining for typer.Exit:**
   - Ruff B904 requires `raise ... from err` or `raise ... from None`
   - Solution: `raise typer.Exit(1) from None` when we don't want to chain

### Files Modified in Phase 1

```
src/game_workflow/
├── agents/base.py          (+120 lines) - logging, validation, execute()
├── config.py               (+80 lines)  - TOML loading, deep merge, caching
├── hooks/
│   ├── __init__.py         (+5 lines)   - export setup_logging, JSONFormatter
│   ├── checkpoint.py       (+130 lines) - auto-prune, tool checkpoints
│   └── logging.py          (+180 lines) - JSON formatter, file rotation
├── main.py                 (+330 lines) - state commands, Rich output
└── orchestrator/
    ├── __init__.py         (+15 lines)  - export all new exceptions
    ├── exceptions.py       (+130 lines) - context dicts, new exception types
    ├── state.py            (+200 lines) - WorkflowPhase, transitions, utilities
    └── workflow.py         (+320 lines) - state machine, hooks, resume

tests/unit/
├── test_config.py          (new, 97 lines)
└── test_orchestrator.py    (+270 lines)
```

### Test Coverage

- 41 unit tests total (6 agents, 7 config, 5 mcp_servers, 23 orchestrator)
- All tests pass on Python 3.11 and 3.12
- CI checks: lint, format, type check, tests

---

## Session 3: 2026-01-16 — Phase 2 Complete

### Summary

Implemented all 6 tasks for Phase 2 Design Agent in a single PR (#6).

### Key Implementation Decisions

**Templates (2.1, 2.2):**
- GDD template has 8 major sections covering all aspects of game design
- Used Jinja2 `is defined` tests for optional fields: `{% if mechanic.controls is defined and mechanic.controls %}`
- Concept template is lightweight, focused on selling the concept and assessing scope
- Both templates work with both Pydantic models and plain dicts

**Template Loader (2.3):**
- Created Jinja2 environment with `StrictUndefined` for early error detection
- Added `trim_blocks` and `lstrip_blocks` for cleaner output
- Custom `datetime` filter for consistent date formatting
- `render_gdd()` and `render_concept()` convenience functions
- `validate_template_context()` for pre-flight checking

**DesignAgent (2.4):**
- Uses Anthropic SDK directly (not Agent SDK) for API calls
- Three-step process: concepts → GDD → tech spec
- Configurable `num_concepts` (1-5, clamped)
- `_extract_text()` helper for type-safe text extraction from API response
- JSON parsing handles markdown code blocks and surrounding text

**Schemas (2.5):**
- All schemas in separate `schemas.py` module for cleaner imports
- `GameConcept`: 15+ fields covering all aspects of a concept pitch
- `GameDesignDocument`: Matches GDD template structure exactly
- `TechnicalSpecification`: Bridges design to implementation
- `DesignOutput`: Combines all outputs for serialization
- JSON Schema export functions for API documentation

**Testing (2.6):**
- 80 total unit tests (39 new for Design Agent)
- Mocked API using `anthropic.types.TextBlock` for type-safe mocks
- Comprehensive template rendering tests
- Schema validation tests

### Issues Encountered & Solutions

1. **Jinja2 attribute access on dicts:**
   - `mechanic.controls` fails if `controls` key doesn't exist in dict
   - Solution: Use `is defined` test: `{% if mechanic.controls is defined %}`

2. **Anthropic response type handling:**
   - `response.content[0].text` doesn't work with mypy due to union types
   - Solution: Created `_extract_text()` helper that uses `isinstance(block, TextBlock)`

3. **Mocking API for tests:**
   - `MagicMock(text="...")` doesn't satisfy `isinstance(block, TextBlock)`
   - Solution: Use actual `TextBlock` instances in mocks

4. **Property patching in tests:**
   - `patch.object(agent, "api_key", None)` fails because `api_key` is a property
   - Solution: Use `monkeypatch.delenv("ANTHROPIC_API_KEY")` instead

5. **JSON parsing type safety:**
   - `json.loads()` returns `Any`, mypy wants explicit types
   - Solution: Explicit type annotations: `result: dict[str, Any] = json.loads(text)`

### Files Modified in Phase 2

```
templates/
├── gdd-template.md          (rewritten) - 8 sections, Jinja2 syntax
└── concept-template.md      (rewritten) - lightweight pitch format

src/game_workflow/
├── agents/
│   ├── __init__.py          (+15 lines) - export schemas
│   ├── design.py            (+550 lines) - full DesignAgent implementation
│   └── schemas.py           (new, 412 lines) - Pydantic models
└── utils/
    └── templates.py         (+150 lines) - Jinja2 loader

tests/unit/
├── test_agents.py           (+70 lines) - DesignAgent basic tests
└── test_design_agent.py     (new, 591 lines) - comprehensive tests

pyproject.toml               (+1 line) - jinja2 dependency
```

### Test Coverage

- 80 unit tests total (39 new for Design Agent)
- All tests pass on Python 3.11 and 3.12
- CI checks: lint, format, type check, tests

---

## Session 4: 2026-01-16 — Phase 3 Complete

### Summary

Implemented all 5 tasks for Phase 3 Build Agent in a single PR (#8).

### Key Implementation Decisions

**Phaser.js Scaffold (3.1):**
- Used Phaser 3.80 (latest stable) and Vite 5.4 for fast builds
- Scene structure: BootScene, PreloadScene, MenuScene, GameScene
- PreloadScene includes loading progress bar
- GameScene includes basic player movement, score, pause, game over flow
- Responsive scaling with FIT mode, auto-center

**Phaser Game Skill (3.2):**
- Comprehensive ~800 line guide for Claude Code
- Covers entire Phaser ecosystem: scenes, sprites, animations, physics
- Input handling: keyboard, mouse, touch
- Audio management with autoplay policy handling
- Cameras, tilemaps, UI patterns
- Common game patterns by genre (platformer, top-down, shooter)
- Object pooling for performance
- Save/load game state
- Build and export instructions for itch.io

**BuildAgent (3.3):**
- Async workflow: copy scaffold → npm install → generate prompt → invoke Claude Code → npm build → verify
- Supports multiple input formats: gdd_path, design_output object, or separate gdd/tech_spec
- Generates comprehensive build prompt from GDD with mechanics, actions, levels, win/loss conditions
- skip_npm_install and skip_build flags for testing
- Proper error handling with BuildFailedError

**Subprocess Utilities (3.4):**
- `ProcessResult` dataclass with `success` property (return_code == 0 and not timed_out)
- `SubprocessConfig` for timeout, cwd, env, capture_output, stream_output
- `run_subprocess` with async output capture and timeout handling
- `run_npm_command` helper with output streaming
- `ClaudeCodeRunner` class for invoking Claude Code with context files and allowed tools
- `find_executable` helper for locating commands in PATH

**Tests (3.5):**
- 29 unit tests for BuildAgent
- Scaffold copying, design data loading, prompt generation
- Integration tests with mocked subprocess calls
- ProcessResult success property tests

### Issues Encountered & Solutions

1. **RUF022 `__all__` is not sorted:**
   - Ruff requires alphabetically sorted `__all__` lists
   - Solution: Removed comments and sorted entries alphabetically

2. **TYPE_CHECKING for Path in tests:**
   - Ruff TC003 requires Path in TYPE_CHECKING when only used for type hints
   - Solution: Moved `from pathlib import Path` into TYPE_CHECKING block

3. **Nested with statements:**
   - Ruff SIM117 prefers single with statement with multiple contexts
   - Solution: Combined `with patch(...), pytest.raises(...):` syntax

### Files Modified in Phase 3

```
templates/scaffolds/phaser/
├── package.json             (new) - Phaser 3.80, Vite 5.4
├── index.html               (new) - responsive viewport
├── vite.config.js           (new) - optimized build config
├── README.md                (new) - scaffold usage guide
├── src/
│   ├── main.js              (new) - game config, visibility handling
│   ├── scenes/
│   │   ├── BootScene.js     (new) - initial setup
│   │   ├── PreloadScene.js  (new) - loading with progress bar
│   │   ├── MenuScene.js     (new) - menu with hover effects
│   │   └── GameScene.js     (new) - game template with score, pause, game over
│   ├── objects/.gitkeep     (new)
│   └── utils/.gitkeep       (new)
└── assets/
    ├── images/.gitkeep      (new)
    ├── audio/.gitkeep       (new)
    └── fonts/.gitkeep       (new)

skills/phaser-game/SKILL.md  (rewritten) - ~800 lines comprehensive guide

src/game_workflow/
├── agents/build.py          (+500 lines) - full BuildAgent implementation
└── utils/
    ├── __init__.py          (+15 lines) - export subprocess utilities
    └── subprocess.py        (new, 347 lines) - async subprocess management

tests/unit/
└── test_build_agent.py      (new, 569 lines) - 29 tests
```

### Test Coverage

- 109 unit tests total (29 new for Build Agent)
- All tests pass on Python 3.11 and 3.12
- CI checks: lint, format, type check, tests

---

## Next Session: Phase 4 Tasks

Phase 4 focuses on the QA Agent. Key tasks:

1. **4.1** Create game testing skill (`skills/game-testing/SKILL.md`)
   - Playwright setup for browser testing
   - Common game test patterns
   - Screenshot comparison

2. **4.2** Implement QAAgent (`src/game_workflow/agents/qa.py`)
   - Run automated test suite
   - Perform smoke tests (game loads, no console errors)
   - Generate QA report
   - Suggest fixes for found issues

3. **4.3** Implement automated smoke tests
   - Playwright-based browser tests
   - Check game loads, no JS errors, basic interactions

4. **4.4** Write unit tests for QAAgent

### Key Considerations for Phase 4

- Playwright will be used for browser automation
- Need to start a dev server to test the game
- Console error detection via Playwright
- May want screenshot capture for visual testing
- QA report should be structured (JSON) for later processing

---

## Useful References

- **CLAUDE.md**: Project specification and guidelines
- **implementation-plan.md**: Detailed task tracking
- **Agent SDK Docs**: https://platform.claude.com/docs/en/agent-sdk/overview
- **MCP Specification**: https://modelcontextprotocol.io
