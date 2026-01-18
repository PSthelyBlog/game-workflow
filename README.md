# Game Workflow

[![CI](https://github.com/PSthelyBlog/game-workflow/actions/workflows/ci.yml/badge.svg)](https://github.com/PSthelyBlog/game-workflow/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

**Fully automated game creation pipeline** using Anthropic's Claude API, Claude Code, and MCP integrations.

---

## Overview

Game Workflow automates the entire game creation process from concept to publication:

```
Prompt --> [Design] --> [Build] --> [QA] --> [Publish] --> itch.io
              |           |          |          |
              v           v          v          v
          Concepts    Game Code   Test      Store Page
            GDD       + Assets   Reports    + Release
```

1. **Design** - Generate game concepts and Game Design Documents from natural language prompts
2. **Build** - Implement games using Claude Code as a subagent with Phaser.js or Godot
3. **QA** - Automatically test and validate builds with Playwright
4. **Publish** - Release to itch.io with human approval gates via Slack

---

## Features

- **Multi-engine support**: Phaser.js (default) and Godot
- **Human-in-the-loop**: Slack approval gates at key checkpoints
- **Comprehensive testing**: Smoke tests, performance benchmarks, visual regression
- **State persistence**: Resume workflows from any checkpoint
- **Extensible skills**: Add custom knowledge for Claude Code

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/PSthelyBlog/game-workflow.git
cd game-workflow

# Create virtual environment (Python 3.11+ required)
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
pip install -e .
```

### Configuration

Set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

For Slack approvals and itch.io publishing, see the [Setup Guide](docs/setup.md).

### Create Your First Game

```bash
# Generate a puzzle platformer
game-workflow run "Create a puzzle platformer about time manipulation"
```

The workflow will:
1. Generate 3 game concepts for you to choose from
2. Create a detailed Game Design Document
3. Implement the game with Phaser.js
4. Run automated tests
5. Prepare assets for itch.io publishing

---

## Commands

```bash
# Start a new workflow
game-workflow run "Your game idea here"

# Use a specific engine
game-workflow run --engine godot "A top-down adventure game"

# Check current workflow status
game-workflow status

# Resume an interrupted workflow
game-workflow resume

# Resume from a specific checkpoint
game-workflow resume --checkpoint <checkpoint-id>

# Cancel the current workflow
game-workflow cancel

# View workflow state
game-workflow state show
game-workflow state list
game-workflow state cleanup --days 30
```

---

## Architecture

```
+---------------------------------------------------------+
|                ORCHESTRATOR (Python)                     |
|  State machine | Hook system | Human approval gates      |
+---------------------------------------------------------+
          |              |              |              |
          v              v              v              v
    +-----------+  +-----------+  +---------+  +-----------+
    |  Design   |  |   Build   |  |   QA    |  |  Publish  |
    |   Agent   |  |   Agent   |  |  Agent  |  |   Agent   |
    +-----------+  +-----------+  +---------+  +-----------+
          |              |              |              |
          v              v              v              v
      Claude API    Claude Code    Playwright    itch.io API
                    + Phaser/       + Tests       + butler
                    Godot Skills
```

### Agents

| Agent | Purpose | Tools |
|-------|---------|-------|
| **DesignAgent** | Generate concepts, GDDs, tech specs | Claude API |
| **BuildAgent** | Implement games from specs | Claude Code |
| **QAAgent** | Test and validate builds | Playwright |
| **PublishAgent** | Prepare release assets | Claude API, butler |

### Skills

Skills are knowledge files that guide Claude Code during implementation:

| Skill | Engine | Coverage |
|-------|--------|----------|
| `phaser-game` | Phaser.js | 2,700 lines of patterns and examples |
| `godot-game` | Godot 4.x | 2,100 lines of GDScript guidance |
| `game-testing` | Playwright | 3,700 lines of test patterns |

See [Skills Documentation](docs/skills.md) for details.

---

## Requirements

### Required

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.11+ | Core runtime |
| Anthropic API Key | - | Claude AI access |

### Optional (for game development)

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Node.js | 18+ | Phaser.js builds |
| Godot | 4.x | Godot game development |

### Optional (for publishing)

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Slack | - | Approval gates |
| itch.io account | - | Game publishing |
| butler CLI | Latest | itch.io uploads |

---

## Configuration

### Environment Variables

```bash
# Required
export ANTHROPIC_API_KEY=sk-ant-...

# Optional - Slack approvals
export SLACK_BOT_TOKEN=xoxb-...
export SLACK_CHANNEL=#game-dev

# Optional - GitHub integration
export GITHUB_TOKEN=ghp_...

# Optional - itch.io publishing
export ITCHIO_API_KEY=...
```

### Config File

Create `~/.game-workflow/config.toml`:

```toml
[workflow]
default_engine = "phaser"  # or "godot"
auto_publish = false
require_all_approvals = true

[slack]
channel = "#game-dev"
notify_on_error = true

[itchio]
username = "your-username"
default_visibility = "draft"
```

See [Configuration Reference](docs/configuration.md) for all options.

---

## Development

### Setup

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit -v
pytest tests/integration -v
pytest tests/e2e -v

# With coverage
pytest --cov=game_workflow --cov-report=html
```

### Linting

```bash
# Check code style
ruff check .
ruff format --check .

# Auto-fix issues
ruff check --fix .
ruff format .

# Type checking
mypy src/game_workflow
```

### Project Structure

```
game-workflow/
├── src/game_workflow/
│   ├── agents/          # Design, Build, QA, Publish agents
│   ├── orchestrator/    # Workflow state machine
│   ├── hooks/           # Logging, checkpoints, Slack
│   ├── mcp_servers/     # itch.io MCP server
│   └── utils/           # Templates, subprocess, validation
├── skills/              # Claude Code knowledge files
├── templates/           # GDD, scaffolds, store pages
├── tests/               # Unit, integration, e2e tests
├── docs/                # Documentation
└── scripts/             # Setup helpers
```

---

## Documentation

- [Setup Guide](docs/setup.md) - Installation and configuration
- [Configuration Reference](docs/configuration.md) - All config options
- [MCP Servers](docs/mcp-servers.md) - External integrations
- [Skills Documentation](docs/skills.md) - Creating custom skills

---

## Supported Game Engines

### Phaser.js (default)

Web-native HTML5 games with:
- Arcade and Matter.js physics
- Sprite animations and tilemaps
- Touch and gamepad input
- Audio with autoplay handling
- Vite-based builds

### Godot 4.x

Cross-platform games with:
- GDScript patterns
- Scene system and signals
- 2D physics and tilemaps
- HTML5 web export

---

## Troubleshooting

### Common Issues

**Workflow stuck on approval**

Check that your Slack bot is invited to the channel:
```
/invite @Game Workflow
```

**Build fails with npm errors**

Ensure Node.js 18+ is installed:
```bash
node --version
```

**Claude Code not found**

Install Claude Code or ensure it's in your PATH:
```bash
claude --version
```

**itch.io upload fails**

Run the butler setup script:
```bash
./scripts/setup-butler.sh
```

### Getting Help

- Check the [Setup Guide](docs/setup.md) for detailed instructions
- Open an [issue](https://github.com/PSthelyBlog/game-workflow/issues) for bugs
- See [notes.md](notes.md) for implementation details

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes with tests
4. Run linting: `ruff check . && mypy src/game_workflow`
5. Run tests: `pytest`
6. Submit a pull request

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- [Anthropic](https://www.anthropic.com/) for Claude AI
- [Phaser](https://phaser.io/) for the game framework
- [Godot](https://godotengine.org/) for the game engine
- [itch.io](https://itch.io/) for game publishing
