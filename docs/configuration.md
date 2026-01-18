# Configuration Reference

This document describes all configuration options available in the Game Workflow system.

## Configuration Loading Order

Configuration is loaded from multiple sources, with later sources taking precedence:

1. **Default values** — Built-in defaults in the code
2. **TOML config file** — `~/.game-workflow/config.toml`
3. **Environment variables** — Highest priority, overrides everything

This means you can set defaults in a config file and override specific values with environment variables.

## Environment Variables

### Core Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | **Yes** | — | Your Anthropic API key for Claude access |

### Workflow Settings

All workflow settings use the `GAME_WORKFLOW_` prefix.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GAME_WORKFLOW_STATE_DIR` | No | `~/.game-workflow/state` | Directory for workflow state persistence |
| `GAME_WORKFLOW_LOG_DIR` | No | `~/.game-workflow/logs` | Directory for log files |
| `GAME_WORKFLOW_LOG_LEVEL` | No | `INFO` | Logging level: DEBUG, INFO, WARNING, ERROR |
| `GAME_WORKFLOW_DEFAULT_ENGINE` | No | `phaser` | Default game engine: `phaser` or `godot` |
| `GAME_WORKFLOW_AUTO_PUBLISH` | No | `false` | Skip publish approval gate |
| `GAME_WORKFLOW_REQUIRE_ALL_APPROVALS` | No | `true` | Require all approval gates to pass |

### Slack Settings

All Slack settings use the `SLACK_` prefix.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SLACK_BOT_TOKEN` | No | — | Slack bot OAuth token (starts with `xoxb-`) |
| `SLACK_CHANNEL` | No | `#game-dev` | Default channel for notifications and approvals |
| `SLACK_NOTIFY_ON_ERROR` | No | `true` | Send Slack notifications when errors occur |

### GitHub Settings

All GitHub settings use the `GITHUB_` prefix.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITHUB_TOKEN` | No | — | GitHub personal access token |
| `GITHUB_DEFAULT_ORG` | No | — | Default GitHub organization for repositories |
| `GITHUB_TEMPLATE_REPO` | No | — | Template repository for new game projects |

### itch.io Settings

All itch.io settings use the `ITCHIO_` prefix.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ITCHIO_API_KEY` | No | — | itch.io API key for publishing |
| `ITCHIO_USERNAME` | No | — | Your itch.io username |
| `ITCHIO_DEFAULT_VISIBILITY` | No | `draft` | Default visibility: `draft`, `public`, or `restricted` |

## Configuration File Format

The configuration file uses TOML format and should be located at `~/.game-workflow/config.toml`.

### Complete Example

```toml
# Workflow Configuration
# ~/.game-workflow/config.toml

[workflow]
# Directory for state persistence
state_dir = "~/.game-workflow/state"

# Directory for log files
log_dir = "~/.game-workflow/logs"

# Logging level: DEBUG, INFO, WARNING, ERROR
log_level = "INFO"

# Default game engine: phaser or godot
default_engine = "phaser"

# Skip the publish approval gate
auto_publish = false

# Require all approval gates (concept, build, publish)
require_all_approvals = true

[slack]
# Slack bot token (overridden by SLACK_BOT_TOKEN env var)
# bot_token = "xoxb-..."

# Default notification channel
channel = "#game-dev"

# Send notifications when errors occur
notify_on_error = true

[github]
# GitHub token (overridden by GITHUB_TOKEN env var)
# token = "ghp_..."

# Default organization for new repositories
default_org = "my-game-studio"

# Template repository for scaffolding
template_repo = "game-template"

[itchio]
# itch.io API key (overridden by ITCHIO_API_KEY env var)
# api_key = "..."

# Your itch.io username
username = "mygamestudio"

# Default game visibility: draft, public, restricted
default_visibility = "draft"
```

### Minimal Example

For basic usage with just environment variables for secrets:

```toml
[workflow]
default_engine = "phaser"
log_level = "INFO"

[slack]
channel = "#game-dev"
```

## Configuration Classes

The configuration system is implemented using Pydantic for validation.

### Settings

Main container class that holds all configuration.

```python
from game_workflow.config import get_settings, reload_settings

# Get cached settings
settings = get_settings()

# Access nested settings
print(settings.anthropic_api_key)
print(settings.workflow.default_engine)
print(settings.slack.channel)

# Reload settings (clears cache)
fresh = reload_settings()
```

### WorkflowSettings

Workflow-specific configuration.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `state_dir` | `Path` | `~/.game-workflow/state` | State persistence directory |
| `log_dir` | `Path` | `~/.game-workflow/logs` | Log file directory |
| `log_level` | `str` | `"INFO"` | Logging level |
| `default_engine` | `"phaser"` \| `"godot"` | `"phaser"` | Default game engine |
| `auto_publish` | `bool` | `False` | Skip publish approval |
| `require_all_approvals` | `bool` | `True` | Require all gates |

### SlackSettings

Slack integration configuration.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `bot_token` | `str \| None` | `None` | Slack bot OAuth token |
| `channel` | `str` | `"#game-dev"` | Default notification channel |
| `notify_on_error` | `bool` | `True` | Send error notifications |

### GitHubSettings

GitHub integration configuration.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `token` | `str \| None` | `None` | Personal access token |
| `default_org` | `str \| None` | `None` | Default organization |
| `template_repo` | `str \| None` | `None` | Template repository name |

### ItchioSettings

itch.io integration configuration.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `api_key` | `str \| None` | `None` | itch.io API key |
| `username` | `str \| None` | `None` | itch.io username |
| `default_visibility` | `"draft"` \| `"public"` \| `"restricted"` | `"draft"` | Game visibility |

## Validation Rules

The system validates inputs to prevent security issues and ensure correctness.

### Prompts

- Minimum length: 10 characters
- Maximum length: 5000 characters

### Game Engine

Must be one of:
- `phaser` — Phaser.js (web-based)
- `godot` — Godot Engine

### State IDs

- Alphanumeric characters only
- Plus underscore (`_`) and hyphen (`-`)
- No path separators or traversal patterns

### itch.io Targets

Format: `username/game-name`

- Username and game name must be alphanumeric
- Plus underscore (`_`) and hyphen (`-`)
- Separated by single forward slash

Examples:
- `mygamestudio/awesome-platformer` — Valid
- `my-studio/puzzle_game` — Valid
- `../hack/attempt` — Invalid (path traversal)
- `user` — Invalid (missing game name)

### Release Channels

Must be one of:
- `html5` — Web/HTML5 builds
- `windows`, `windows-32`, `windows-64` — Windows builds
- `linux`, `linux-32`, `linux-64` — Linux builds
- `mac`, `osx` — macOS builds
- `android` — Android builds
- `ios` — iOS builds

### Version Strings

- Alphanumeric characters
- Plus dots (`.`), underscores (`_`), and hyphens (`-`)
- Maximum 100 characters

Examples:
- `1.0.0` — Valid
- `v2.1.3-beta` — Valid
- `2024.01.18_hotfix` — Valid

## Programmatic Configuration

### Loading Configuration

```python
from game_workflow.config import get_settings, reload_settings, load_toml_config
from pathlib import Path

# Get cached settings (recommended for most uses)
settings = get_settings()

# Force reload from files and environment
settings = reload_settings()

# Load a specific TOML file
config = load_toml_config(Path("./custom-config.toml"))
```

### Checking Required Configuration

```python
from game_workflow.config import get_settings

settings = get_settings()

# Check if API key is configured
if not settings.anthropic_api_key:
    raise ValueError("ANTHROPIC_API_KEY is required")

# Check if Slack is configured
if settings.slack.bot_token:
    print("Slack integration enabled")
else:
    print("Slack not configured - approvals will auto-pass")

# Check if itch.io publishing is available
if settings.itchio.api_key:
    print(f"itch.io publishing enabled for {settings.itchio.username}")
```

### Testing with Custom Configuration

```python
import os
from game_workflow.config import reload_settings

# Set test configuration
os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["GAME_WORKFLOW_DEFAULT_ENGINE"] = "godot"

# Reload to pick up changes
settings = reload_settings()
assert settings.workflow.default_engine == "godot"
```

## Environment-Specific Configurations

### Development

```bash
export ANTHROPIC_API_KEY="sk-ant-dev-..."
export GAME_WORKFLOW_LOG_LEVEL="DEBUG"
export GAME_WORKFLOW_AUTO_PUBLISH="true"
export GAME_WORKFLOW_REQUIRE_ALL_APPROVALS="false"
```

### Production

```bash
export ANTHROPIC_API_KEY="sk-ant-prod-..."
export GAME_WORKFLOW_LOG_LEVEL="INFO"
export SLACK_BOT_TOKEN="xoxb-..."
export SLACK_CHANNEL="#game-releases"
export ITCHIO_API_KEY="..."
```

### CI/CD

```bash
export ANTHROPIC_API_KEY="${SECRETS_ANTHROPIC_KEY}"
export GAME_WORKFLOW_LOG_LEVEL="WARNING"
export GAME_WORKFLOW_AUTO_PUBLISH="true"
export GAME_WORKFLOW_REQUIRE_ALL_APPROVALS="false"
```

## Secrets Management

**Best Practices:**

1. Never commit secrets to version control
2. Use environment variables for all API keys and tokens
3. Add `.env` to `.gitignore`
4. Use secret management tools in CI/CD (GitHub Secrets, etc.)

**Example `.env` file (never commit this):**

```bash
# .env - DO NOT COMMIT
ANTHROPIC_API_KEY=sk-ant-api03-...
SLACK_BOT_TOKEN=xoxb-...
GITHUB_TOKEN=ghp_...
ITCHIO_API_KEY=...
```

**Loading `.env` files:**

The project doesn't auto-load `.env` files. Use a tool like `direnv` or source it manually:

```bash
# Using direnv (recommended)
echo 'dotenv' > .envrc
direnv allow

# Or source manually
source .env
```

## Related Documentation

- [Setup Guide](setup.md) — Initial setup instructions
- [MCP Servers](mcp-servers.md) — External service integration
- [Skills](skills.md) — Game development skills
