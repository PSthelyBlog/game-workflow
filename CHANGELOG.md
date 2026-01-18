# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-18

### Added

#### Core Infrastructure
- Configuration management with TOML file support and environment variables
- State management with JSON persistence and checkpoint/resume capability
- Workflow orchestrator with phase transitions (INIT → DESIGN → BUILD → QA → PUBLISH → COMPLETE)
- Custom exception hierarchy for workflow errors
- CLI entry point with commands: `run`, `status`, `cancel`, `resume`, `version`
- State subcommands: `show`, `list`, `reset`, `cleanup`
- Base agent class with logging, validation, and error handling
- Logging hook with JSON structured logging and rotating file output
- Checkpoint hook with auto-pruning of old checkpoints

#### Design Agent
- Game concept generation (1-5 variations)
- Game Design Document (GDD) generation from selected concept
- Technical specification generation
- Pydantic schemas: `GameConcept`, `GameDesignDocument`, `TechnicalSpecification`
- Jinja2 templates for GDD and concept rendering
- Template loader with custom filters and strict validation

#### Build Agent
- Phaser.js project scaffold with Vite build system
- Scaffold copying and npm dependency installation
- Claude Code invocation via subprocess
- Build prompt generation from GDD and tech spec
- Build output verification
- Subprocess management utilities with async output capture

#### QA Agent
- DevServerManager for hosting games during testing
- PlaywrightTester for browser-based tests
- 6 smoke tests: page loads, canvas present, no JS errors, game initializes, no console errors, input response
- 2 performance tests: FPS measurement, load time measurement
- QAReport with JSON and Markdown export
- Recommendations engine based on test results
- QAFailedError for critical failures

#### Publish Agent
- Marketing copy generation from GDD using Claude API
- Store page content preparation with Pydantic schemas
- Screenshot collection from build directory
- GitHub release metadata preparation
- Build artifact packaging (zip archives)
- itch.io page template with Jinja2

#### MCP Servers
- MCPServerRegistry for server lifecycle management
- itch.io MCP server with tools: `upload_game`, `get_game_status`, `get_my_games`, `check_credentials`
- Butler CLI wrapper with automatic download and installation
- itch.io API client with httpx and retry logic
- Slack approval hook with Block Kit formatting
- Approval detection via reactions and thread replies
- Notification support with severity levels

#### Skills
- Phaser.js game skill (~2700 lines)
  - State management (FSM, game state)
  - Save/load systems (localStorage, IndexedDB)
  - Audio handling (sound pools, crossfade)
  - Mobile/touch controls (virtual joystick, gestures)
  - Game patterns by genre (platformer, RPG, shooter, puzzle)
  - Performance optimization and web export

- Godot game skill (~2100 lines)
  - GDScript fundamentals and best practices
  - Scene system and node lifecycle
  - Signals and communication patterns
  - Physics, animation, and audio systems
  - UI/Control nodes and tilemaps
  - Web export for itch.io

- Game testing skill (~3700 lines)
  - Playwright setup and fixtures
  - Smoke, functional, and visual regression tests
  - Accessibility testing (WCAG, keyboard, screen reader)
  - Mobile device testing (emulation, touch gestures)
  - Audio and network testing for multiplayer

#### Scaffolds
- Phaser.js scaffold with Phaser 3.80 and Vite 5.4
  - Scene structure: Boot, Preload, Menu, Game
  - Loading progress bar
  - Basic player movement, score, pause, game over
  - Responsive scaling with FIT mode

- Godot scaffold for Godot 4.x
  - Complete UI system (main menu, HUD, pause menu, game over)
  - Player controller with platformer/top-down support
  - GameManager, AudioManager, EventBus autoloads
  - Web export preset for HTML5

#### Integration & Testing
- Full workflow integration with all agents wired together
- ApprovalHook and WorkflowHook protocols
- Retry logic with configurable max_retries
- Rollback to checkpoint for error recovery
- 495+ tests (unit, integration, E2E)
  - 18 workflow integration tests
  - 61 integration tests (external services, approval flows, error scenarios)
  - 23 E2E tests (full workflow, artifacts, state persistence, CLI)
  - 40 performance tests
  - 41 security tests

#### Performance Infrastructure
- PerformanceHook for collecting workflow metrics
- TimingRecord, PhaseMetrics, PerformanceMetrics dataclasses
- Timer context manager and timed_operation helper
- lru_cache on JSON schema generation functions

#### Security
- Input validation for command injection prevention
  - `validate_itchio_target()` for itch.io target format
  - `validate_channel()` for upload channels
  - `validate_version()` for version strings
- Path traversal prevention
  - `validate_state_id()` for state file names
  - `validate_path_safety()` for file paths
- All credentials stored in environment variables
- No secrets in logs or state files

#### Documentation
- Setup guide (`docs/setup.md`)
- Configuration reference (`docs/configuration.md`)
- MCP server documentation (`docs/mcp-servers.md`)
- Skills documentation (`docs/skills.md`)
- Setup scripts (`scripts/setup-butler.sh`, `scripts/setup-slack-app.sh`)
- Comprehensive README with badges, diagrams, and quick start

### Dependencies
- anthropic>=0.40.0
- mcp>=1.0.0
- httpx>=0.25.0
- pydantic>=2.0.0
- pydantic-settings>=2.0.0
- tomli>=2.0.0
- rich>=13.0.0
- typer>=0.9.0
- jinja2>=3.0.0

### Development Dependencies
- pytest>=7.0.0
- pytest-asyncio>=0.21.0
- pytest-cov>=4.0.0
- ruff>=0.1.0
- mypy>=1.0.0
- pre-commit>=3.0.0

### Optional Dependencies (QA)
- playwright>=1.40.0
- pytest-playwright>=0.4.0

[0.1.0]: https://github.com/PSthelyBlog/game-workflow/releases/tag/v0.1.0
