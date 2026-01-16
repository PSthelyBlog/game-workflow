# Implementation Plan — Game Workflow Automation

> **Status**: 🟡 In Progress
> **Started**: 2026-01-16
> **Last Updated**: 2026-01-16
> **Current Phase**: Phase 1 — Core Infrastructure

---

## Progress Overview

| Phase | Description | Status | Issues | PRs |
|-------|-------------|--------|--------|-----|
| 0 | Repository Setup | ✅ Complete | #1 | #2 |
| 1 | Core Infrastructure | ⬜ Not Started | — | — |
| 2 | Design Agent | ⬜ Not Started | — | — |
| 3 | Build Agent | ⬜ Not Started | — | — |
| 4 | QA Agent | ⬜ Not Started | — | — |
| 5 | Publish Agent | ⬜ Not Started | — | — |
| 6 | MCP Servers | ⬜ Not Started | — | — |
| 7 | Skills | ⬜ Not Started | — | — |
| 8 | Integration & Testing | ⬜ Not Started | — | — |
| 9 | Documentation & Polish | ⬜ Not Started | — | — |

**Legend**: ⬜ Not Started | 🟡 In Progress | ✅ Complete | 🔴 Blocked

---

## Current Status

**Phase**: 1 — Core Infrastructure
**Working On**: Ready to begin Phase 1
**Blockers**: None
**Next Action**: Implement configuration management and workflow state machine

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

- [ ] **1.1** Implement configuration management (`src/game_workflow/config.py`)
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - Load from environment variables
    - Load from `~/.game-workflow/config.toml`
    - Pydantic models for validation
    - Sensible defaults

- [ ] **1.2** Implement state management (`src/game_workflow/orchestrator/state.py`)
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - JSON-based persistence
    - State transitions: `INIT → DESIGN → BUILD → QA → PUBLISH → COMPLETE`
    - Checkpoint/resume capability
    - State inspection CLI commands

- [ ] **1.3** Implement workflow orchestrator (`src/game_workflow/orchestrator/workflow.py`)
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - Main workflow state machine
    - Phase transitions
    - Error handling and recovery
    - Hook integration points

- [ ] **1.4** Implement custom exceptions (`src/game_workflow/orchestrator/exceptions.py`)
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - `WorkflowError` base class
    - `ApprovalTimeoutError`
    - `BuildFailedError`
    - `PublishFailedError`
    - `ConfigurationError`

- [ ] **1.5** Implement CLI entry point (`src/game_workflow/main.py`)
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - Use `typer` for CLI
    - Commands: `run`, `status`, `cancel`, `resume`, `state`
    - Rich output formatting

- [ ] **1.6** Implement base agent class (`src/game_workflow/agents/base.py`)
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - Abstract base for all agents
    - Common Agent SDK setup
    - Logging integration
    - Error handling patterns

- [ ] **1.7** Implement logging hook (`src/game_workflow/hooks/logging.py`)
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - Log all tool calls
    - Structured logging (JSON)
    - Console + file output

- [ ] **1.8** Implement checkpoint hook (`src/game_workflow/hooks/checkpoint.py`)
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - Save state after each tool call
    - Enable resume from any point
    - Prune old checkpoints

### Phase 1 Completion Criteria
- [ ] `python -m game_workflow status` works
- [ ] Configuration loads from env and file
- [ ] State persists across restarts
- [ ] Workflow can be started (stubs for agents)
- [ ] All tests pass: `pytest tests/unit/test_orchestrator.py`

---

## Phase 2: Design Agent

Implement the concept and GDD generation agent.

### Tasks

- [ ] **2.1** Create GDD template (`templates/gdd-template.md`)
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes: Comprehensive game design document structure

- [ ] **2.2** Create concept template (`templates/concept-template.md`)
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes: Brief concept summary format

- [ ] **2.3** Implement template loader (`src/game_workflow/utils/templates.py`)
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes: Load and render Jinja2 templates

- [ ] **2.4** Implement DesignAgent (`src/game_workflow/agents/design.py`)
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - Generate 3-5 concept variations
    - User selects or Claude picks best
    - Generate full GDD for selected concept
    - Output: `concept.json`, `gdd.md`, `tech-spec.md`
    - Use extended thinking for creative decisions

- [ ] **2.5** Implement structured output schemas for design artifacts
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - Pydantic models for concept, GDD
    - Validation before saving
    - JSON Schema generation for API

- [ ] **2.6** Write unit tests for DesignAgent
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes: Mock Claude API, test all outputs

### Phase 2 Completion Criteria
- [ ] DesignAgent generates valid concept.json
- [ ] DesignAgent generates valid gdd.md
- [ ] Templates render correctly
- [ ] All tests pass: `pytest tests/unit/test_agents.py::TestDesignAgent`

---

## Phase 3: Build Agent

Implement the Claude Code invocation agent.

### Tasks

- [ ] **3.1** Create Phaser.js scaffold (`templates/scaffolds/phaser/`)
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - `package.json` with Phaser dependency
    - Basic `index.html`
    - `src/main.js` entry point
    - `src/scenes/` directory structure
    - Vite config for dev/build

- [ ] **3.2** Create Phaser game skill (`skills/phaser-game/SKILL.md`)
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - Project structure guidelines
    - Common patterns (scenes, sprites, physics)
    - Asset handling best practices
    - Build and export instructions

- [ ] **3.3** Implement BuildAgent (`src/game_workflow/agents/build.py`)
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - Create game repo from scaffold
    - Invoke Claude Code via subprocess
    - Pass GDD as context
    - Monitor progress via stdout
    - Handle errors and retries
    - Commit incrementally to GitHub

- [ ] **3.4** Implement GitHub integration in BuildAgent
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - Create repo from template
    - Create feature branches
    - Commit changes
    - Create PRs for review (optional)

- [ ] **3.5** Write unit tests for BuildAgent
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes: Mock subprocess, test GitHub operations

### Phase 3 Completion Criteria
- [ ] BuildAgent creates repo from scaffold
- [ ] Claude Code is invoked successfully
- [ ] Game code is committed to GitHub
- [ ] All tests pass: `pytest tests/unit/test_agents.py::TestBuildAgent`

---

## Phase 4: QA Agent

Implement the testing and validation agent.

### Tasks

- [ ] **4.1** Create game testing skill (`skills/game-testing/SKILL.md`)
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - Playwright setup for browser testing
    - Common game test patterns
    - Screenshot comparison
    - Performance benchmarks

- [ ] **4.2** Implement QAAgent (`src/game_workflow/agents/qa.py`)
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - Run automated test suite
    - Perform smoke tests (game loads, no console errors)
    - Check for common issues (memory leaks, infinite loops)
    - Generate QA report
    - Suggest fixes for found issues

- [ ] **4.3** Implement automated smoke tests
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - Playwright-based browser tests
    - Check game loads
    - Check no JavaScript errors
    - Check basic interactions work

- [ ] **4.4** Write unit tests for QAAgent
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes: Mock test runners, test report generation

### Phase 4 Completion Criteria
- [ ] QAAgent runs smoke tests
- [ ] QA report is generated
- [ ] Issues are identified and reported
- [ ] All tests pass: `pytest tests/unit/test_agents.py::TestQAAgent`

---

## Phase 5: Publish Agent

Implement the release preparation agent.

### Tasks

- [ ] **5.1** Create itch.io page template (`templates/itchio-page.md`)
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - Store page description structure
    - Screenshot requirements
    - Tag recommendations

- [ ] **5.2** Implement PublishAgent (`src/game_workflow/agents/publish.py`)
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes:
    - Generate marketing copy from GDD
    - Prepare store page content
    - Generate/collect screenshots
    - Create release tag on GitHub
    - Prepare build artifacts

- [ ] **5.3** Write unit tests for PublishAgent
  - Issue: #_pending_
  - PR: #_pending_
  - Merged: _pending_
  - Notes: Mock external services, test artifact generation

### Phase 5 Completion Criteria
- [ ] PublishAgent generates marketing copy
- [ ] Store page content is prepared
- [ ] Release artifacts are created
- [ ] All tests pass: `pytest tests/unit/test_agents.py::TestPublishAgent`

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