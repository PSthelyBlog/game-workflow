# Game Workflow

Fully automated game creation pipeline using Anthropic's Agent SDK, Claude Code, and MCP integrations.

## Overview

Game Workflow automates the entire game creation process from concept to publication:

1. **Design** - Generate game concepts and Game Design Documents from prompts
2. **Build** - Implement games using Claude Code as a subagent
3. **QA** - Automatically test and validate builds
4. **Publish** - Release to itch.io with human approval gates

## Installation

```bash
# Clone the repository
git clone https://github.com/PSthelyBlog/game-workflow.git
cd game-workflow

# Install in development mode
pip install -e ".[dev]"
```

## Quick Start

```bash
# Start a new workflow
game-workflow run "Create a puzzle platformer about time manipulation"

# Check workflow status
game-workflow status

# Resume from a checkpoint
game-workflow resume --checkpoint <checkpoint-id>
```

## Requirements

- Python 3.11+
- Anthropic API key
- Slack workspace (for approvals)
- itch.io account (for publishing)
- butler CLI (for itch.io uploads)

## Configuration

Set the required environment variables:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export SLACK_BOT_TOKEN=xoxb-...
export SLACK_CHANNEL=#game-dev
export GITHUB_TOKEN=ghp_...
export ITCHIO_API_KEY=...
```

Or create a config file at `~/.game-workflow/config.toml`:

```toml
[workflow]
default_engine = "phaser"
auto_publish = false

[slack]
channel = "#game-dev"
```

## Supported Game Engines

- **Phaser.js** (default) - Web-native HTML5 games
- **Godot** - Cross-platform game engine

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run linting
ruff check .

# Run type checking
mypy src/game_workflow

# Run tests
pytest tests/unit -v

# Run all tests with coverage
pytest --cov=game_workflow --cov-report=html
```

## License

MIT License - see [LICENSE](LICENSE) for details.
