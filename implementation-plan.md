# Implementation Plan — Game Workflow Automation

> **Status**: 🟡 In Progress
> **Started**: 2026-01-16
> **Last Updated**: 2026-01-18
> **Current Phase**: Phase 6 — MCP Servers

---

## Progress Overview

| Phase | Description | Status | Issues | PRs |
|-------|-------------|--------|--------|-----|
| 0 | Repository Setup | ✅ Complete | #1 | #2 |
| 1 | Core Infrastructure | ✅ Complete | #3 | #4 |
| 2 | Design Agent | ✅ Complete | #5 | #6 |
| 3 | Build Agent | ✅ Complete | #7 | #8 |
| 4 | QA Agent | ✅ Complete | #9 | #10 |
| 5 | Publish Agent | ✅ Complete | #11 | #12 |
| 6 | MCP Servers | ⬜ Not Started | — | — |
| 7 | Skills | ⬜ Not Started | — | — |
| 8 | Integration & Testing | ⬜ Not Started | — | — |
| 9 | Documentation & Polish | ⬜ Not Started | — | — |

**Legend**: ⬜ Not Started | 🟡 In Progress | ✅ Complete | 🔴 Blocked

---

## Current Status

**Phase**: 6 — MCP Servers
**Working On**: Ready to begin Phase 6
**Blockers**: None
**Next Action**: Implement MCP server registry and itch.io MCP server

---

## Phase 0: Repository Setup

Initialize the repository with basic structure and tooling.

### Tasks

- [x] **0.1** Create GitHub repository `game-workflow`
  - Issue: —
  - PR: —
  - Merged: 2026-01-16
  - Notes: Public repo, MIT license, Python .gitignore

- [x] **0.2** Initialize Python project with pyproject.toml
  - Issue: #1
  - PR: #2
  - Merged: 2026-01-16
  - Notes: Used hatch for build system with all required dependencies

- [x] **0.3** Set up directory structure (empty files with docstrings)
  - Issue: #1
  - PR: #2
  - Merged: 2026-01-16
  - Notes: Created all directories and `__init__.py` files per CLAUDE.md, plus stub modules

- [x] **0.4** Configure development tooling
  - Issue: #1
  - PR: #2
  - Merged: 2026-01-16
  - Notes: Added ruff.toml, mypy.ini, .github/workflows/ci.yml, .pre-commit-config.yaml

- [x] **0.5** Create README.md with project overview
  - Issue: #1
  - PR: #2
  - Merged: 2026-01-16
  - Notes: User-facing documentation, installation, quick start

### Phase 0 Completion Criteria
- [x] Repository exists on GitHub
- [x] `pip install -e .` works
- [x] `ruff check .` passes
- [x] `mypy .` passes (with empty files)
- [x] CI workflow runs successfully

---

## Phase 1: Core Infrastructure

Build the orchestration foundation.

### Tasks

- [x] **1.1** Implement configuration management (`src/game_workflow/config.py`)
  - Issue: #3
  - PR: #4
  - Merged: 2026-01-16
  - Notes:
    - Load from environment variables
    - Load from `~/.game-workflow/config.toml`
    - Pydantic models for validation
    - Sensible defaults
    - Settings caching with reload_settings()

- [x] **1.2** Implement state management (`src/game_workflow/orchestrator/state.py`)
  - Issue: #3
  - PR: #4
  - Merged: 2026-01-16
  - Notes:
    - JSON-based persistence
    - State transitions with validation: `INIT → DESIGN → BUILD → QA → PUBLISH → COMPLETE`
    - Checkpoint/resume capability with CheckpointData model
    - list_all(), delete(), cleanup_old() methods

- [x] **1.3** Implement workflow orchestrator (`src/game_workflow/orchestrator/workflow.py`)
  - Issue: #3
  - PR: #4
  - Merged: 2026-01-16
  - Notes:
    - Main workflow state machine with phase transitions
    - Hook integration points for all phases
    - Error handling with automatic FAILED state
    - resume() and resume_latest() class methods

- [x] **1.4** Implement custom exceptions (`src/game_workflow/orchestrator/exceptions.py`)
  - Issue: #3
  - PR: #4
  - Merged: 2026-01-16
  - Notes:
    - `WorkflowError` base class with context dict
    - `ApprovalTimeoutError`, `ApprovalRejectedError`
    - `InvalidTransitionError`, `StateNotFoundError`
    - `ConfigurationError`, `AgentError`

- [x] **1.5** Implement CLI entry point (`src/game_workflow/main.py`)
  - Issue: #3
  - PR: #4
  - Merged: 2026-01-16
  - Notes:
    - Commands: `run`, `status`, `cancel`, `resume`, `version`
    - `state` subcommand: `show`, `list`, `reset`, `cleanup`
    - Rich output formatting with colored phases

- [x] **1.6** Implement base agent class (`src/game_workflow/agents/base.py`)
  - Issue: #3
  - PR: #4
  - Merged: 2026-01-16
  - Notes:
    - Logging integration with log_info/debug/error
    - _validate_config() for API key checking
    - execute() wrapper with error handling
    - add_artifact() helper method

- [x] **1.7** Implement logging hook (`src/game_workflow/hooks/logging.py`)
  - Issue: #3
  - PR: #4
  - Merged: 2026-01-16
  - Notes:
    - Structured JSON logging with JSONFormatter
    - Console + rotating file output (10MB, 5 backups)
    - on_tool_call, on_approval_requested/received methods

- [x] **1.8** Implement checkpoint hook (`src/game_workflow/hooks/checkpoint.py`)
  - Issue: #3
  - PR: #4
  - Merged: 2026-01-16
  - Notes:
    - Auto-pruning of old checkpoints (max 50)
    - Checkpoint on phase start/complete/error
    - Selective tool call checkpointing

### Phase 1 Completion Criteria
- [x] `python -m game_workflow status` works
- [x] Configuration loads from env and file
- [x] State persists across restarts
- [x] Workflow can be started (stubs for agents)
- [x] All tests pass: `pytest tests/unit/test_orchestrator.py`

---

## Phase 2: Design Agent

Implement the concept and GDD generation agent.

### Tasks

- [x] **2.1** Create GDD template (`templates/gdd-template.md`)
  - Issue: #5
  - PR: #6
  - Merged: 2026-01-16
  - Notes: Comprehensive GDD with 8 sections, Jinja2 syntax, optional fields support

- [x] **2.2** Create concept template (`templates/concept-template.md`)
  - Issue: #5
  - PR: #6
  - Merged: 2026-01-16
  - Notes: Brief format for concept variations with elevator pitch, features, and technical fit

- [x] **2.3** Implement template loader (`src/game_workflow/utils/templates.py`)
  - Issue: #5
  - PR: #6
  - Merged: 2026-01-16
  - Notes: Jinja2 environment with StrictUndefined, custom filters, render helpers

- [x] **2.4** Implement DesignAgent (`src/game_workflow/agents/design.py`)
  - Issue: #5
  - PR: #6
  - Merged: 2026-01-16
  - Notes:
    - Generates 1-5 concept variations (configurable)
    - Generates full GDD from selected concept
    - Generates technical specification
    - Saves artifacts as JSON and rendered markdown
    - Proper error handling and logging

- [x] **2.5** Implement structured output schemas for design artifacts
  - Issue: #5
  - PR: #6
  - Merged: 2026-01-16
  - Notes:
    - GameConcept, GameDesignDocument, TechnicalSpecification models
    - DesignOutput combined output model
    - JSON Schema generation functions
    - Full validation with Pydantic v2

- [x] **2.6** Write unit tests for DesignAgent
  - Issue: #5
  - PR: #6
  - Merged: 2026-01-16
  - Notes: 80 tests total, mocked API calls, template rendering tests

### Phase 2 Completion Criteria
- [x] DesignAgent generates valid concept.json
- [x] DesignAgent generates valid gdd.md
- [x] Templates render correctly
- [x] All tests pass: `pytest tests/unit/test_agents.py::TestDesignAgent`

---

## Phase 3: Build Agent

Implement the Claude Code invocation agent.

### Tasks

- [x] **3.1** Create Phaser.js scaffold (`templates/scaffolds/phaser/`)
  - Issue: #7
  - PR: #8
  - Merged: 2026-01-16
  - Notes:
    - `package.json` with Phaser 3.80 and Vite 5.4
    - `index.html` with responsive viewport
    - `src/main.js` entry point with game config
    - `src/scenes/` with Boot, Preload, Menu, Game scenes
    - `vite.config.js` with optimized build settings

- [x] **3.2** Create Phaser game skill (`skills/phaser-game/SKILL.md`)
  - Issue: #7
  - PR: #8
  - Merged: 2026-01-16
  - Notes:
    - Comprehensive guide (~800 lines)
    - Scenes, sprites, animations, physics
    - Input handling, audio, cameras, tilemaps
    - Common patterns by genre (platformer, top-down, shooter)

- [x] **3.3** Implement BuildAgent (`src/game_workflow/agents/build.py`)
  - Issue: #7
  - PR: #8
  - Merged: 2026-01-16
  - Notes:
    - Copy scaffold to output directory
    - Install dependencies (npm install)
    - Generate build prompt from GDD/tech spec
    - Invoke Claude Code via subprocess
    - Build game (npm run build)
    - Verify build output

- [x] **3.4** Add subprocess management utilities (`src/game_workflow/utils/subprocess.py`)
  - Issue: #7
  - PR: #8
  - Merged: 2026-01-16
  - Notes:
    - ProcessResult dataclass with success property
    - SubprocessConfig for timeout, cwd, env, streaming
    - run_subprocess with async output capture
    - ClaudeCodeRunner for Claude Code invocation

- [x] **3.5** Write unit tests for BuildAgent
  - Issue: #7
  - PR: #8
  - Merged: 2026-01-16
  - Notes: 29 tests, mocked subprocess, scaffold copying, prompt generation

### Phase 3 Completion Criteria
- [x] BuildAgent creates project from scaffold
- [x] Claude Code is invoked successfully
- [x] Build output is captured and logged
- [x] All tests pass: `pytest tests/unit/test_build_agent.py` (29 tests)

---

## Phase 4: QA Agent

Implement the testing and validation agent.

### Tasks

- [x] **4.1** Create game testing skill (`skills/game-testing/SKILL.md`)
  - Issue: #9
  - PR: #10
  - Merged: 2026-01-17
  - Notes:
    - Comprehensive Playwright setup (~1600 lines)
    - Smoke tests, functional tests, visual regression
    - Performance benchmarking (FPS, memory, load time)
    - Console error detection and filtering
    - Input simulation utilities
    - Canvas inspection techniques
    - CI/CD integration examples

- [x] **4.2** Implement QAAgent (`src/game_workflow/agents/qa.py`)
  - Issue: #9
  - PR: #10
  - Merged: 2026-01-17
  - Notes:
    - DevServerManager for hosting game during tests
    - PlaywrightTester for browser-based tests
    - Smoke tests: page loads, canvas, JS errors, game init, console, input
    - Performance measurement with thresholds
    - QAReport with JSON and Markdown output
    - Recommendations engine based on results
    - Raises QAFailedError for critical failures

- [x] **4.3** Implement automated smoke tests
  - Issue: #9
  - PR: #10
  - Merged: 2026-01-17
  - Notes:
    - 6 smoke tests: page_loads, canvas_present, no_javascript_errors,
      game_initializes, no_console_errors, input_response
    - Performance tests: performance_fps, performance_load_time
    - Console error filtering with ignore patterns

- [x] **4.4** Write unit tests for QAAgent
  - Issue: #9
  - PR: #10
  - Merged: 2026-01-17
  - Notes:
    - 49 tests covering all components
    - TestResult, ConsoleMessage, QAReport dataclasses
    - DevServerManager and PlaywrightTester classes
    - QAAgent evaluation and recommendation logic

### Phase 4 Completion Criteria
- [x] QAAgent runs smoke tests
- [x] QA report is generated
- [x] Issues are identified and reported
- [x] All tests pass: `pytest tests/unit/test_qa_agent.py` (49 tests)

---

## Phase 5: Publish Agent

Implement the release preparation agent.

### Tasks

- [x] **5.1** Create itch.io page template (`templates/itchio-page.md`)
  - Issue: #11
  - PR: #12
  - Merged: 2026-01-18
  - Notes:
    - Store page description structure with title, tagline, description
    - Controls, features, screenshots, technical details sections
    - Credits, version history, support information
    - Tag recommendations using Jinja2 syntax

- [x] **5.2** Implement PublishAgent (`src/game_workflow/agents/publish.py`)
  - Issue: #11
  - PR: #12
  - Merged: 2026-01-18
  - Notes:
    - Generate marketing copy from GDD using Claude API
    - Prepare store page content with StorePageContent Pydantic schema
    - Collect screenshots from directory with limit of 10
    - Prepare GitHub release metadata (GitHubRelease schema)
    - Package build artifacts into zip archives
    - Save all publish artifacts (store-page.md, store-page.json, publish-output.json)

- [x] **5.3** Write unit tests for PublishAgent
  - Issue: #11
  - PR: #12
  - Merged: 2026-01-18
  - Notes:
    - 48 tests covering schemas, enums, config, and agent functionality
    - GDD loading tests (file and data)
    - Screenshot handling tests with limit verification
    - Artifact packaging tests with zip creation
    - GitHub release preparation tests
    - Store page rendering tests
    - JSON parsing tests with code block handling

### Phase 5 Completion Criteria
- [x] PublishAgent generates marketing copy
- [x] Store page content is prepared
- [x] Release artifacts are created
- [x] All tests pass: `pytest tests/unit/test_publish_agent.py` (48 tests)

---

## Phase 6: MCP Servers

Implement MCP server integrations.

### Tasks

- [ ] **6.1** Implement MCP server registry (`src/game_workflow/mcp_servers/registry.py`)
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - Register official servers (GitHub, Slack)
    - Register custom servers
    - Handle server lifecycle

- [ ] **6.2** Implement butler CLI wrapper (`src/game_workflow/mcp_servers/itchio/butler.py`)
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - Download/install butler
    - Login handling
    - Push command wrapper
    - Status command wrapper

- [ ] **6.3** Implement itch.io API client (`src/game_workflow/mcp_servers/itchio/api.py`)
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - httpx-based async client
    - Game metadata endpoints
    - Upload status endpoints

- [ ] **6.4** Implement itch.io MCP server (`src/game_workflow/mcp_servers/itchio/server.py`)
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - Tools: `upload_game`, `update_game_page`, `publish_game`, `get_game_status`
    - Proper error handling
    - Input validation

- [ ] **6.5** Implement Slack approval hook (`src/game_workflow/hooks/slack_approval.py`)
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - Send approval request messages
    - Wait for reaction or reply
    - Handle timeouts gracefully
    - Support feedback collection

- [ ] **6.6** Write unit tests for MCP servers
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes: Mock butler CLI, mock APIs

- [ ] **6.7** Write integration tests for Slack
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes: Test with real Slack workspace (dev)

### Phase 6 Completion Criteria
- [ ] itch.io MCP server works with butler
- [ ] Slack approvals work end-to-end
- [ ] All MCP servers register correctly
- [ ] All tests pass: `pytest tests/unit/test_mcp_servers.py`

---

## Phase 7: Skills

Create comprehensive skills for Claude Code.

### Tasks

- [ ] **7.1** Enhance Phaser game skill with advanced patterns
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - State management patterns
    - Save/load game state
    - Audio handling
    - Mobile touch controls
    - Common game mechanics (platformer, puzzle, etc.)

- [ ] **7.2** Create Godot game skill (`skills/godot-game/SKILL.md`)
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - GDScript best practices
    - Scene structure
    - Signal patterns
    - Export for web

- [ ] **7.3** Create Godot scaffold (`templates/scaffolds/godot/`)
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - project.godot
    - Basic scene structure
    - Export presets for HTML5

- [ ] **7.4** Enhance game testing skill
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - Visual regression testing
    - Performance profiling
    - Accessibility checks

### Phase 7 Completion Criteria
- [ ] Phaser skill covers common game types
- [ ] Godot skill is complete
- [ ] Testing skill covers visual regression
- [ ] Skills are validated with sample games

---

## Phase 8: Integration & Testing

End-to-end integration and comprehensive testing.

### Tasks

- [ ] **8.1** Implement full workflow integration
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - Wire all agents together
    - Test phase transitions
    - Test error recovery

- [ ] **8.2** Write integration tests
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - Test with mocked external services
    - Test all approval paths
    - Test error scenarios

- [ ] **8.3** Write E2E tests
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - Full workflow with test itch.io project
    - Automated approvals for CI
    - Verify all artifacts

- [ ] **8.4** Performance testing and optimization
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - Measure workflow duration
    - Identify bottlenecks
    - Optimize API calls

- [ ] **8.5** Security audit
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - Review credential handling
    - Check for injection vulnerabilities
    - Validate input sanitization

### Phase 8 Completion Criteria
- [ ] Full workflow runs successfully
- [ ] All tests pass with >80% coverage
- [ ] Performance is acceptable (<30 min for simple game)
- [ ] Security audit passes

---

## Phase 9: Documentation & Polish

Final documentation and release preparation.

### Tasks

- [ ] **9.1** Write setup documentation (`docs/setup.md`)
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes: Step-by-step setup guide

- [ ] **9.2** Write configuration reference (`docs/configuration.md`)
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes: All config options documented

- [ ] **9.3** Write MCP server documentation (`docs/mcp-servers.md`)
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes: How to use and extend MCP servers

- [ ] **9.4** Write skills documentation (`docs/skills.md`)
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes: How to create custom skills

- [ ] **9.5** Create setup scripts
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - `scripts/setup-butler.sh`
    - `scripts/setup-slack-app.sh`

- [ ] **9.6** Final README polish
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes: Badges, GIFs, examples

- [ ] **9.7** Create release v0.1.0
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes: Tag, changelog, GitHub release

### Phase 9 Completion Criteria
- [ ] All documentation complete
- [ ] Setup scripts work
- [ ] v0.1.0 released on GitHub
- [ ] PyPI package published (optional)

---

## Changelog

_Record significant changes to this plan here._

| Date | Change | Reason |
|------|--------|--------|
| 2026-01-18 | Phase 5 completed | PR #12 merged with Publish Agent implementation |
| 2026-01-17 | Phase 4 completed | PR #10 merged with QA Agent implementation |
| 2026-01-16 | Phase 3 completed | PR #8 merged with Build Agent implementation |
| 2026-01-16 | Phase 2 completed | PR #6 merged with Design Agent |
| 2026-01-16 | Phase 1 completed | PR #4 merged with core infrastructure |
| 2026-01-16 | Phase 0 completed | PR #2 merged with full project structure |
| 2026-01-16 | Initial plan created | Project kickoff |

---

## Notes & Decisions

_Record important decisions and their rationale here._

### Decision Log

| Date | Decision | Rationale | Alternatives Considered |
|------|----------|-----------|------------------------|
| _TBD_ | Use Phaser.js as default engine | Web-native, easy itch.io deployment | Godot (added as option), Unity (too heavy) |
| _TBD_ | Use Agent SDK for orchestration | Production-grade, hooks, subagents | Raw API (less control), Claude Code only (no programmatic control) |
| _TBD_ | Slack for approvals | Best MCP support, threading | Discord (less business-friendly), email (slow) |

### Open Questions

- [ ] Should we support multiple games in parallel?
- [ ] How to handle asset generation (images, sounds)?
- [ ] Should we integrate with game analytics platforms?

### Blockers

_None currently._

---

## How to Update This Document

**After each PR merge:**

1. Find the corresponding task in the relevant phase
2. Update the checkbox: `- [ ]` → `- [x]`
3. Fill in the Issue and PR numbers
4. Add the merge date
5. Update the "Progress Overview" table
6. Update the "Current Status" section
7. Add any notes or decisions to the appropriate sections
8. Commit with message: `docs: update implementation-plan.md after #<PR>`

**Example update:**

```markdown
- [x] **0.1** Create GitHub repository `game-workflow`
  - Issue: #1
  - PR: #2
  - Merged: 2026-01-16
  - Notes: Public repo, MIT license, Python .gitignore
```