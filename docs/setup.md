# Setup Guide

This guide walks you through setting up the Game Workflow automation system from scratch.

## Prerequisites

Before installing game-workflow, ensure you have the following:

### Required

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.11+ | Core runtime |
| pip | Latest | Package installation |
| Git | Any | Version control |
| Anthropic API Key | — | Claude AI access |
| Claude Code | Latest | Game implementation (build phase) |

### Optional (for game development)

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Node.js | 18+ | Phaser.js game builds |
| npm | 9+ | JavaScript dependency management |
| Godot | 4.x | Godot game development |

### Optional (for publishing)

| Requirement | Version | Purpose |
|-------------|---------|---------|
| butler CLI | Latest | itch.io uploads (can be auto-installed) |
| Slack Workspace | — | Approval gates and notifications |
| GitHub Token | — | Repository integration |
| itch.io Account | — | Game publishing |

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/PSthelyBlog/game-workflow.git
cd game-workflow
```

### 2. Create a Virtual Environment

We recommend using a virtual environment to isolate dependencies:

```bash
# Create virtual environment
python3.11 -m venv .venv

# Activate (macOS/Linux)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate
```

### 3. Install the Package

**Basic installation:**

```bash
pip install -e .
```

**With development tools (recommended for contributors):**

```bash
pip install -e ".[dev]"
```

**With QA testing tools (Playwright):**

```bash
pip install -e ".[qa]"
```

**Full installation:**

```bash
pip install -e ".[dev,qa]"
```

### 4. Verify Installation

```bash
# Check the CLI is available
game-workflow --version

# Check configuration status
game-workflow status
```

## Initial Configuration

### Environment Variables

Create a `.env` file in your project root or export these variables:

**Required:**

```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
```

**Recommended:**

```bash
# Slack integration (for approval gates)
export SLACK_BOT_TOKEN="xoxb-..."
export SLACK_CHANNEL="#game-dev"

# GitHub integration (for repository management)
export GITHUB_TOKEN="ghp_..."
```

**Optional:**

```bash
# Workflow settings
export GAME_WORKFLOW_STATE_DIR="~/.game-workflow/state"
export GAME_WORKFLOW_LOG_DIR="~/.game-workflow/logs"
export GAME_WORKFLOW_LOG_LEVEL="INFO"
export GAME_WORKFLOW_DEFAULT_ENGINE="phaser"

# itch.io publishing
export ITCHIO_API_KEY="your-api-key"
export ITCHIO_USERNAME="your-username"
```

### Configuration File (Optional)

For persistent configuration, create `~/.game-workflow/config.toml`:

```toml
[workflow]
default_engine = "phaser"
auto_publish = false
require_all_approvals = true
log_level = "INFO"

[slack]
channel = "#game-dev"
notify_on_error = true

[github]
default_org = "your-org"

[itchio]
default_visibility = "draft"
```

See [Configuration Reference](configuration.md) for all available options.

### Create Required Directories

The system auto-creates directories on first use, but you can create them manually:

```bash
mkdir -p ~/.game-workflow/state
mkdir -p ~/.game-workflow/logs
```

## Optional Setup

### butler CLI (itch.io Publishing)

butler is itch.io's command-line tool for uploading game builds. It can be auto-downloaded by the workflow, or you can install it manually:

**Auto-download (recommended):**

The system will automatically download butler when needed. No action required.

**Manual installation:**

```bash
# macOS
curl -L -o butler.zip https://broth.itch.zone/butler/darwin-amd64/LATEST/archive/default
unzip butler.zip -d ~/bin
chmod +x ~/bin/butler

# Linux
curl -L -o butler.zip https://broth.itch.zone/butler/linux-amd64/LATEST/archive/default
unzip butler.zip -d ~/bin
chmod +x ~/bin/butler

# Verify
butler version
```

**Authenticate with itch.io:**

```bash
butler login
# Enter your itch.io API key when prompted
```

Alternatively, set the API key via environment variable:

```bash
export ITCHIO_API_KEY="your-api-key"
```

### Slack App Setup

To enable approval gates and notifications, create a Slack app:

1. Go to [Slack API Apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Name it "Game Workflow" and select your workspace
4. Navigate to "OAuth & Permissions"
5. Add these Bot Token Scopes:
   - `chat:write` — Send messages
   - `reactions:read` — Read approval reactions
   - `channels:history` — Read channel messages
   - `groups:history` — Read private channel messages
6. Install the app to your workspace
7. Copy the "Bot User OAuth Token" (starts with `xoxb-`)
8. Set the environment variable:

```bash
export SLACK_BOT_TOKEN="xoxb-your-token"
export SLACK_CHANNEL="#game-dev"  # or your preferred channel
```

9. Invite the bot to your channel:

```
/invite @Game Workflow
```

### GitHub Token Setup

For GitHub integration (release management, repository creation):

1. Go to [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select scopes:
   - `repo` — Full repository access
   - `read:org` — Read organization membership
   - `workflow` — GitHub Actions access (optional)
4. Copy the token and set it:

```bash
export GITHUB_TOKEN="ghp_your-token"
```

### Claude Code Setup

Claude Code is required for the build phase. It's the AI agent that implements the game based on the Game Design Document.

**Installation:**

Visit [claude.ai/download](https://claude.ai/download) and follow the installation instructions for your platform.

**Verify installation:**

```bash
claude --version
```

**Authentication:**

Claude Code uses your Anthropic API key. Ensure it's set:

```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
```

### Node.js Setup (for Phaser.js games)

Phaser.js games require Node.js for building:

**macOS (using Homebrew):**

```bash
brew install node@18
```

**Linux (using nvm):**

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18
```

**Windows:**

Download from [nodejs.org](https://nodejs.org/) and install.

**Verify:**

```bash
node --version  # Should be v18.x.x or higher
npm --version   # Should be v9.x.x or higher
```

### Godot Setup (for Godot games)

For Godot game development:

1. Download Godot 4.x from [godotengine.org](https://godotengine.org/download)
2. Install and verify:

```bash
godot --version  # Should be 4.x.x
```

3. For headless CI builds, use the headless export templates:

```bash
godot --headless --export-release "Web" ./build/html5
```

## Verifying Your Setup

Run these commands to verify everything is working:

```bash
# Check CLI
game-workflow --version

# Check configuration
game-workflow status

# List any existing workflow states
game-workflow state list

# Run unit tests (if dev dependencies installed)
pytest tests/unit -v
```

## Quick Start

Once setup is complete, create your first game:

```bash
# Start a new workflow
game-workflow run "Create a simple platformer game where a cat collects fish"

# Check the status
game-workflow status

# Resume a workflow (if needed)
game-workflow resume
```

## Troubleshooting

### Common Issues

**"ANTHROPIC_API_KEY not set"**

Make sure your API key is exported:

```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
```

**"No module named 'game_workflow'"**

Ensure you installed in development mode:

```bash
pip install -e .
```

**"Permission denied" when running butler**

Make butler executable:

```bash
chmod +x ~/bin/butler
```

**Slack messages not appearing**

1. Verify the bot token is correct
2. Ensure the bot is invited to the channel
3. Check the channel name includes the `#`

**Tests failing with import errors**

Ensure all dependencies are installed:

```bash
pip install -e ".[dev,qa]"
```

### Getting Help

- Check the [Configuration Reference](configuration.md) for all options
- Review the [MCP Servers](mcp-servers.md) documentation
- Open an issue on [GitHub](https://github.com/PSthelyBlog/game-workflow/issues)

## Next Steps

- [Configuration Reference](configuration.md) — All configuration options
- [MCP Servers](mcp-servers.md) — External service integrations
- [Skills](skills.md) — Game development skills documentation
