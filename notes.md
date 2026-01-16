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

## Next Session: Phase 1 Tasks

Phase 1 focuses on Core Infrastructure. Key tasks:

1. **1.1** Enhance configuration management
   - Already have basic config.py, needs TOML file loading

2. **1.2** Enhance state management
   - Already have basic state.py, needs state transitions

3. **1.3** Implement workflow orchestrator
   - Main state machine with phase transitions

4. **1.4** Enhance exceptions
   - Already have basic exceptions, may need more

5. **1.5** Enhance CLI
   - Already have basic CLI, needs state commands

6. **1.6** Enhance base agent
   - Already have basic agent, needs Agent SDK integration

7. **1.7-1.8** Implement hooks
   - Already have stub hooks, need full implementation

### Completion Criteria for Phase 1
- `python -m game_workflow status` works
- Configuration loads from env and file
- State persists across restarts
- Workflow can be started (stubs for agents)
- All tests pass

---

## Useful References

- **CLAUDE.md**: Project specification and guidelines
- **implementation-plan.md**: Detailed task tracking
- **Agent SDK Docs**: https://platform.claude.com/docs/en/agent-sdk/overview
- **MCP Specification**: https://modelcontextprotocol.io
