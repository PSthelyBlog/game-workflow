# Game Workflow Automation

> Fully automated game creation pipeline using Anthropic's Agent SDK, Claude Code, and MCP integrations.

## Project Overview

This repository implements an **automated game creation workflow** that:
1. Generates game concepts and design documents from prompts
2. Implements games using Claude Code as a subagent
3. Tests and QA's the builds automatically
4. Publishes to itch.io with human approval gates
5. Notifies via Slack throughout the process

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR (Agent SDK)                        │
│  Primary control loop • State management • Human-in-loop triggers  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  DESIGN PHASE │     │  BUILD PHASE    │     │ PUBLISH PHASE   │
│  Subagent     │     │  Claude Code    │     │  Subagent       │
└───────────────┘     └─────────────────┘     └─────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────────┐
│                    MCP SERVERS (GitHub, Slack, itch.io)            │
└─────────────────────────────────────────────────────────────────────┘
```

## Tech Stack

- **Python 3.11+** — Primary language
- **Claude Agent SDK** — Orchestration framework
- **Claude Code** — Game implementation (invoked as subprocess)
- **MCP Protocol** — External service integrations
- **Phaser.js** — Default game engine (web-native)
- **pytest + playwright** — Testing
- **butler CLI** — itch.io uploads

## Directory Structure

```
game-workflow/
├── CLAUDE.md                   # This file
├── implementation-plan.md      # Progress tracking (UPDATE AFTER EACH PR MERGE)
├── notes.md                    # Notes and observations (UPDATE AFTER EACH PR MERGE)
├── pyproject.toml              # Project configuration
├── README.md                   # User-facing documentation
│
├── src/
│   └── game_workflow/
│       ├── __init__.py
│       ├── main.py             # CLI entry point
│       ├── config.py           # Configuration management
│       │
│       ├── orchestrator/
│       │   ├── __init__.py
│       │   ├── workflow.py     # Main workflow state machine
│       │   ├── state.py        # State persistence
│       │   └── exceptions.py   # Custom exceptions
│       │
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── base.py         # Base agent class
│       │   ├── design.py       # DesignAgent - concept/GDD generation
│       │   ├── build.py        # BuildAgent - Claude Code invocation
│       │   ├── qa.py           # QAAgent - testing and validation
│       │   └── publish.py      # PublishAgent - release preparation
│       │
│       ├── hooks/
│       │   ├── __init__.py
│       │   ├── slack_approval.py   # Human approval gates
│       │   ├── checkpoint.py       # State checkpointing
│       │   └── logging.py          # Action logging
│       │
│       ├── mcp_servers/
│       │   ├── __init__.py
│       │   ├── itchio/
│       │   │   ├── __init__.py
│       │   │   ├── server.py       # MCP server implementation
│       │   │   ├── butler.py       # butler CLI wrapper
│       │   │   └── api.py          # itch.io API client
│       │   └── registry.py         # MCP server registry
│       │
│       └── utils/
│           ├── __init__.py
│           ├── templates.py        # Template loading
│           └── validation.py       # Input validation
│
├── skills/
│   ├── phaser-game/
│   │   └── SKILL.md            # Phaser.js game implementation skill
│   ├── godot-game/
│   │   └── SKILL.md            # Godot game implementation skill
│   └── game-testing/
│       └── SKILL.md            # Automated game testing skill
│
├── templates/
│   ├── gdd-template.md         # Game Design Document template
│   ├── concept-template.md     # Game concept template
│   ├── itchio-page.md          # itch.io store page template
│   └── scaffolds/
│       ├── phaser/             # Phaser.js project scaffold
│       └── godot/              # Godot project scaffold
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # pytest fixtures
│   ├── unit/
│   │   ├── test_orchestrator.py
│   │   ├── test_agents.py
│   │   └── test_mcp_servers.py
│   ├── integration/
│   │   ├── test_workflow.py
│   │   └── test_slack_integration.py
│   └── e2e/
│       └── test_full_workflow.py
│
├── docs/
│   ├── setup.md                # Setup instructions
│   ├── configuration.md        # Configuration reference
│   ├── mcp-servers.md          # MCP server documentation
│   └── skills.md               # Skills documentation
│
└── scripts/
    ├── setup-butler.sh         # Install butler CLI
    └── setup-slack-app.sh      # Slack app configuration helper
```

---

## Development Workflow

### CRITICAL: GitHub-First Development

**All work MUST go through GitHub Issues and Pull Requests.**

1. **Before starting work**: Create or find the relevant GitHub Issue
2. **Create a feature branch**: `git checkout -b feature/<issue-number>-<short-description>`
3. **Implement the feature**: Make commits with clear messages referencing the issue
4. **Create a Pull Request**: Reference the issue with "Closes #<issue-number>"
5. **Before merge**: make sure CI passes
6. **After CI passes**: Merge with `gh pr merge <number> --squash --delete-branch`
7. **After merge**: Update `implementation-plan.md` to reflect progress and `notes.md` with notes and observations from implementation session

### Branch Naming Convention

```
feature/<issue-number>-<short-description>   # New features
fix/<issue-number>-<short-description>       # Bug fixes
docs/<issue-number>-<short-description>      # Documentation
refactor/<issue-number>-<short-description>  # Refactoring
```

### Commit Message Format

```
<type>(<scope>): <description>

[optional body]

Refs #<issue-number>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

### Before Each PR Merge

**ALWAYS make sure** CI passes.

### After Each PR Merge

**ALWAYS update `implementation-plan.md`**:
1. Mark the completed task with `[x]`
2. Add the PR number and merge date
3. Update the "Current Status" section
4. Note any blockers or changes to the plan

**ALWAYS update `notes.md`**: notes and observations from implementation sessions to help future work

---

## Implementation Guidelines

### Agent SDK Usage

```python
from claude_agent_sdk import Agent, ClaudeAgentOptions
from claude_agent_sdk.tools import Bash, Read, Write
from claude_agent_sdk.hooks import Hook

# Always use Sonnet 4.5 for agents (best balance)
DEFAULT_MODEL = "claude-sonnet-4-5-20250929"

# Enable extended thinking for complex decisions
THINKING_OPTIONS = ClaudeAgentOptions(
    model=DEFAULT_MODEL,
    extended_thinking=True
)
```

### MCP Server Pattern

```python
from mcp import Server, Tool

server = Server("server-name")

@server.tool()
async def tool_name(param: str) -> dict:
    """Tool description for Claude to understand usage."""
    # Implementation
    return {"status": "success", "data": result}
```

### Human Approval Gates

All approval gates go through Slack. Required gates:
1. **Concept approval** — After GDD generation
2. **Build approval** — After implementation complete
3. **Publish approval** — Before itch.io upload

```python
# Use SlackApprovalHook for gating
approval = await slack.request_approval(
    channel="#game-dev",
    message="Approve action?",
    timeout_minutes=None  # Wait indefinitely for human input
)
```

### State Management

```python
# All workflow state persists to JSON
STATE_DIR = Path("~/.game-workflow/state")

# State includes:
# - Current phase
# - Generated artifacts (paths)
# - Approval statuses
# - Error history
```

### Error Handling

```python
# All agents should handle errors gracefully
class WorkflowError(Exception):
    """Base exception for workflow errors."""
    
class ApprovalTimeoutError(WorkflowError):
    """Human didn't respond in time."""
    
class BuildFailedError(WorkflowError):
    """Game build failed."""
```

---

## Testing Requirements

### Unit Tests
- All agents must have unit tests
- Mock external services (GitHub, Slack, itch.io)
- Test state transitions

### Integration Tests
- Test MCP server connections
- Test Slack message formatting
- Test GitHub API interactions

### E2E Tests
- Full workflow with mock approvals
- Use test itch.io project
- Verify all artifacts generated

### Running Tests

```bash
# Unit tests
pytest tests/unit -v

# Integration tests (requires credentials)
pytest tests/integration -v

# E2E tests (requires all services)
pytest tests/e2e -v

# All tests with coverage
pytest --cov=game_workflow --cov-report=html
```

---

## Configuration

### Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL=#game-dev
GITHUB_TOKEN=ghp_...
ITCHIO_API_KEY=...

# Optional
GAME_WORKFLOW_STATE_DIR=~/.game-workflow/state
GAME_WORKFLOW_LOG_LEVEL=INFO
DEFAULT_GAME_ENGINE=phaser  # or "godot"
```

### Config File (`~/.game-workflow/config.toml`)

```toml
[workflow]
default_engine = "phaser"
auto_publish = false
require_all_approvals = true

[slack]
channel = "#game-dev"
notify_on_error = true

[github]
default_org = "your-org"
template_repo = "game-template"

[itchio]
username = "your-username"
default_visibility = "draft"
```

---

## MCP Servers

### Official Servers (install via npm)
- `@anthropic/github-mcp` — GitHub integration
- `@anthropic/slack-mcp` — Slack integration

### Custom Servers (in this repo)
- `game_workflow.mcp_servers.itchio` — itch.io publishing

### Server Configuration

```python
# In src/game_workflow/mcp_servers/registry.py
MCP_SERVERS = {
    "github": {
        "command": "npx",
        "args": ["@anthropic/github-mcp"],
        "env": {"GITHUB_TOKEN": os.environ["GITHUB_TOKEN"]}
    },
    "slack": {
        "command": "npx", 
        "args": ["@anthropic/slack-mcp"],
        "env": {"SLACK_BOT_TOKEN": os.environ["SLACK_BOT_TOKEN"]}
    },
    "itchio": {
        "command": "python",
        "args": ["-m", "game_workflow.mcp_servers.itchio.server"],
        "env": {"ITCHIO_API_KEY": os.environ["ITCHIO_API_KEY"]}
    }
}
```

---

## Skills

Skills are loaded by Claude Code during the build phase.

### Phaser Game Skill (`skills/phaser-game/SKILL.md`)
- Project scaffolding
- Common game patterns
- Asset handling
- Build configuration

### Godot Game Skill (`skills/godot-game/SKILL.md`)
- GDScript patterns
- Scene structure
- Export configuration

### Game Testing Skill (`skills/game-testing/SKILL.md`)
- Playwright-based testing
- Screenshot comparison
- Performance benchmarks

---

## Debugging

### Logging

```python
import logging

logger = logging.getLogger("game_workflow")

# Logs go to:
# - Console (INFO+)
# - ~/.game-workflow/logs/workflow.log (DEBUG+)
# - Slack #game-dev-errors (ERROR+)
```

### State Inspection

```bash
# View current workflow state
python -m game_workflow state show

# Reset stuck workflow
python -m game_workflow state reset

# Resume from checkpoint
python -m game_workflow resume --checkpoint <id>
```

### Common Issues

1. **Slack approval not received**: Check bot permissions, channel membership
2. **Claude Code fails**: Check ANTHROPIC_API_KEY, model availability
3. **itch.io upload fails**: Verify butler installation, API key
4. **GitHub PR fails**: Check token permissions (repo, workflow)

---

## Security Notes

- Never commit API keys or tokens
- Use environment variables for all secrets
- The itch.io MCP server should validate all inputs
- Slack approval tokens expire — handle refresh
- Game builds run in sandboxed environment

---

## Quick Reference

### Start a new workflow
```bash
python -m game_workflow run "Create a puzzle platformer about time manipulation"
```

### Check workflow status
```bash
python -m game_workflow status
```

### Cancel current workflow
```bash
python -m game_workflow cancel
```

### Run with specific engine
```bash
python -m game_workflow run --engine godot "Create a top-down shooter"
```

---

## Related Documentation

- [Agent SDK Docs](https://platform.claude.com/docs/en/agent-sdk/overview)
- [MCP Specification](https://modelcontextprotocol.io)
- [Phaser.js Docs](https://phaser.io/docs)
- [itch.io API](https://itch.io/docs/api/overview)
- [butler CLI](https://itch.io/docs/butler/)