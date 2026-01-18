# MCP Server Documentation

This document describes the MCP (Model Context Protocol) servers used by the Game Workflow system for external service integrations.

## Overview

The Game Workflow system uses MCP servers to integrate with external services:

| Server | Type | Purpose |
|--------|------|---------|
| GitHub | Official (@anthropic/github-mcp) | Repository management, releases |
| Slack | Official (@anthropic/slack-mcp) | Notifications, approval gates |
| itch.io | Custom (Python) | Game publishing |

MCP servers run as subprocesses and communicate via JSON-RPC 2.0.

## MCP Server Registry

The `MCPServerRegistry` class manages server configurations and lifecycle.

### Basic Usage

```python
from game_workflow.mcp_servers.registry import MCPServerRegistry

# Using async context manager (recommended)
async with MCPServerRegistry() as registry:
    # Start a server
    await registry.start_server("itchio", wait_healthy=True)

    # Check server status
    if registry.is_running("itchio"):
        print("itch.io server is running")

    # Get server statistics
    stats = registry.get_server_stats("itchio")
    print(f"PID: {stats['pid']}, Uptime: {stats['uptime_seconds']}s")

    # Stop server
    await registry.stop_server("itchio")
# All servers are stopped automatically when exiting context
```

### MCPServerConfig

Configuration for an MCP server.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `command` | `str` | — | Executable command (e.g., "python", "npx") |
| `args` | `list[str]` | `[]` | Command arguments |
| `env` | `dict[str, str]` | `{}` | Environment variables |
| `working_dir` | `str \| None` | `None` | Working directory |
| `startup_timeout` | `float` | `30.0` | Timeout for startup in seconds |
| `health_check_interval` | `float` | `10.0` | Health check interval in seconds |

### MCPServerProcess

Represents a running MCP server process.

| Property | Type | Description |
|----------|------|-------------|
| `name` | `str` | Server name |
| `config` | `MCPServerConfig` | Server configuration |
| `process` | `subprocess.Popen` | The subprocess object |
| `started_at` | `float \| None` | Start timestamp |
| `healthy` | `bool` | Health status |
| `is_running` | `bool` | Whether process is alive (property) |
| `pid` | `int \| None` | Process ID (property) |

### Registry Methods

**Server Management:**

| Method | Description |
|--------|-------------|
| `get(name)` | Get server configuration by name |
| `register(name, config)` | Register a new server |
| `unregister(name)` | Remove a server registration |
| `list_servers()` | List all registered server names |
| `list_running()` | List running server names |

**Lifecycle:**

| Method | Description |
|--------|-------------|
| `start_server(name, wait_healthy=True, timeout=None)` | Start a server |
| `stop_server(name, timeout=10.0)` | Stop a server gracefully |
| `restart_server(name, stop_timeout=10.0, wait_healthy=True, start_timeout=None)` | Restart a server |
| `stop_all(timeout=10.0)` | Stop all running servers |

**Status:**

| Method | Description |
|--------|-------------|
| `is_running(name)` | Check if server is running |
| `is_healthy(name)` | Check if server is healthy |
| `get_process(name)` | Get process info |
| `get_server_stats(name)` | Get server statistics |
| `get_all_stats()` | Get stats for all servers |

### Default Server Configurations

The registry comes pre-configured with three servers:

**GitHub:**
```python
MCPServerConfig(
    command="npx",
    args=["@anthropic/github-mcp"],
    env={"GITHUB_TOKEN": os.environ.get("GITHUB_TOKEN", "")}
)
```

**Slack:**
```python
MCPServerConfig(
    command="npx",
    args=["@anthropic/slack-mcp"],
    env={"SLACK_BOT_TOKEN": os.environ.get("SLACK_BOT_TOKEN", "")}
)
```

**itch.io:**
```python
MCPServerConfig(
    command="python",
    args=["-m", "game_workflow.mcp_servers.itchio.server"],
    env={"ITCHIO_API_KEY": os.environ.get("ITCHIO_API_KEY", "")}
)
```

### Registering Custom Servers

```python
from game_workflow.mcp_servers.registry import MCPServerRegistry, MCPServerConfig

registry = MCPServerRegistry()

# Register a custom MCP server
registry.register("custom", MCPServerConfig(
    command="node",
    args=["./my-mcp-server.js"],
    env={"MY_API_KEY": "secret"},
    startup_timeout=60.0,
    health_check_interval=30.0,
))

# Start the custom server
await registry.start_server("custom")
```

## itch.io MCP Server

The itch.io MCP server provides tools for publishing games to itch.io.

### Available Tools

#### upload_game

Upload a game build to itch.io using butler.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `directory` | `str` | Yes | — | Path to build directory |
| `target` | `str` | Yes | — | itch.io target (username/game-name) |
| `channel` | `str` | No | `"html5"` | Release channel |
| `version` | `str` | No | — | Version string |
| `dry_run` | `bool` | No | `false` | Validate without uploading |

**Returns:**
```json
{
  "success": true,
  "build_id": 12345,
  "target": "username/game-name",
  "channel": "html5",
  "version": "1.0.0"
}
```

#### get_game_status

Get the current status of a game on itch.io.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `target` | `str` | Yes | itch.io target (username/game-name) |

**Returns:**
```json
{
  "success": true,
  "target": "username/game-name",
  "channels": {
    "html5": {
      "version": "1.0.0",
      "build_id": "12345"
    }
  }
}
```

#### get_my_games

Get list of all games owned by the authenticated user.

**Parameters:** None

**Returns:**
```json
{
  "success": true,
  "games": [
    {
      "id": 123456,
      "title": "My Game",
      "url": "https://username.itch.io/my-game",
      "downloads_count": 100,
      "views_count": 500
    }
  ]
}
```

#### check_credentials

Verify itch.io API credentials and butler installation.

**Parameters:** None

**Returns:**
```json
{
  "success": true,
  "user": {
    "id": 12345,
    "username": "myusername"
  },
  "butler_installed": true,
  "butler_version": "15.21.0"
}
```

### Running the Server Manually

```bash
# Set the API key
export ITCHIO_API_KEY="your-api-key"

# Run the server
python -m game_workflow.mcp_servers.itchio.server
```

## Butler CLI Wrapper

The `ButlerCLI` class provides a Python wrapper around itch.io's butler command-line tool.

### Basic Usage

```python
from game_workflow.mcp_servers.itchio.butler import ButlerCLI
from pathlib import Path

butler = ButlerCLI()

# Check if butler is installed
if not butler.check_installed():
    # Download and install butler
    await butler.download_butler()

# Check version
version = butler.get_version()
print(f"Butler version: {version.version}")

# Push a game build
result = await butler.push(
    directory=Path("./build/html5"),
    target="myusername/mygame",
    channel="html5",
    version="1.0.0",
)

if result.success:
    print(f"Uploaded! Build ID: {result.build_id}")
else:
    print(f"Failed: {result.error}")
```

### ButlerCLI Methods

| Method | Description |
|--------|-------------|
| `check_installed()` | Check if butler is available |
| `get_version()` | Get butler version information |
| `is_logged_in()` | Check if authenticated with itch.io |
| `download_butler(install_dir, progress_callback)` | Download and install butler |
| `login(api_key)` | Authenticate with itch.io |
| `push(directory, target, channel, version, fix_permissions, dry_run, progress_callback)` | Upload a build |
| `status(target)` | Get game status |
| `fetch(target, output_dir, channel)` | Download a game build |
| `validate(directory)` | Validate a game directory |

### ButlerPushResult

Result of a push operation.

| Field | Type | Description |
|-------|------|-------------|
| `success` | `bool` | Whether upload succeeded |
| `target` | `str` | itch.io target |
| `channel` | `str` | Release channel |
| `version` | `str \| None` | Version string |
| `build_id` | `int \| None` | itch.io build ID |
| `signature_path` | `str \| None` | Path to signature file |
| `error` | `str \| None` | Error message if failed |
| `output` | `str` | Command output |

### ButlerStatusResult

Result of a status operation.

| Field | Type | Description |
|-------|------|-------------|
| `success` | `bool` | Whether status retrieval succeeded |
| `target` | `str` | itch.io target |
| `channels` | `dict[str, dict]` | Channel information |
| `error` | `str \| None` | Error message if failed |
| `output` | `str` | Command output |

### Automatic Butler Download

Butler is automatically downloaded if not found:

```python
butler = ButlerCLI()

if not butler.check_installed():
    # Downloads to ~/.game-workflow/bin/ by default
    path = await butler.download_butler()
    print(f"Butler installed to {path}")
```

Supported platforms:
- macOS (Intel and Apple Silicon)
- Linux (x64)
- Windows (x64)

## itch.io API Client

The `ItchioAPI` class provides direct access to the itch.io REST API.

### Basic Usage

```python
from game_workflow.mcp_servers.itchio.api import ItchioAPI

async with ItchioAPI(api_key="your-api-key") as api:
    # Get current user
    user = await api.get_me()
    print(f"Logged in as: {user.username}")

    # List games
    games = await api.get_my_games()
    for game in games:
        print(f"- {game.title}: {game.downloads_count} downloads")

    # Get specific game
    game = await api.get_game(game_id=123456)

    # Get game uploads
    uploads = await api.get_game_uploads(game_id=123456)
```

### API Methods

| Method | Description |
|--------|-------------|
| `get_me()` | Get authenticated user profile |
| `get_my_games()` | Get list of user's games |
| `get_game(game_id)` | Get specific game details |
| `get_game_uploads(game_id)` | Get uploads for a game |
| `find_game_by_url(game_url)` | Find game by URL |
| `find_game_by_slug(username, game_slug)` | Find game by username/slug |
| `get_credentials()` | Get API key scopes |
| `check_api_key()` | Verify API key is valid |

### Data Classes

**ItchioGame:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | `int` | Game ID |
| `url` | `str` | Full game URL |
| `title` | `str` | Game title |
| `short_text` | `str \| None` | Short description |
| `type` | `GameType` | Game type (default, flash, unity, java, html) |
| `classification` | `GameClassification` | Classification (game, tool, assets, etc.) |
| `created_at` | `str \| None` | Creation timestamp |
| `published_at` | `str \| None` | Publication timestamp |
| `cover_url` | `str \| None` | Cover image URL |
| `min_price` | `int` | Minimum price in cents |
| `downloads_count` | `int` | Download count |
| `views_count` | `int` | View count |
| `purchases_count` | `int` | Purchase count |

**ItchioUpload:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | `int` | Upload ID |
| `game_id` | `int` | Parent game ID |
| `filename` | `str` | Original filename |
| `display_name` | `str \| None` | Display name |
| `size` | `int` | File size in bytes |
| `channel_name` | `str \| None` | Release channel |
| `build_id` | `int \| None` | Build ID |
| `p_windows` | `bool` | Windows platform flag |
| `p_linux` | `bool` | Linux platform flag |
| `p_osx` | `bool` | macOS platform flag |
| `p_android` | `bool` | Android platform flag |

**ItchioUser:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | `int` | User ID |
| `username` | `str` | Username |
| `url` | `str` | Profile URL |
| `display_name` | `str \| None` | Display name |
| `developer` | `bool` | Is developer flag |
| `gamer` | `bool` | Is gamer flag |

### Retry Logic

The API client includes automatic retry logic:

- **Max retries:** 3 (configurable)
- **Retry delay:** 1.0 seconds (configurable, with exponential backoff)
- **Retried errors:** Timeouts, rate limiting (429), server errors (5xx)

```python
api = ItchioAPI(
    api_key="...",
    timeout=30.0,
    max_retries=5,
    retry_delay=2.0,
)
```

## Release Channels

When publishing to itch.io, use the appropriate channel for your build:

| Channel | Platform | Description |
|---------|----------|-------------|
| `html5` | Web | HTML5/WebGL games |
| `windows` | Windows | Windows 64-bit (default) |
| `windows-32` | Windows | Windows 32-bit |
| `windows-64` | Windows | Windows 64-bit (explicit) |
| `linux` | Linux | Linux 64-bit (default) |
| `linux-32` | Linux | Linux 32-bit |
| `linux-64` | Linux | Linux 64-bit (explicit) |
| `mac` | macOS | macOS build |
| `osx` | macOS | macOS build (alias) |
| `android` | Android | Android APK |
| `ios` | iOS | iOS build |

## Security Considerations

### Input Validation

All external inputs are validated to prevent security issues:

**itch.io Targets:**
- Must match format `username/game-name`
- Only alphanumeric characters, underscores, and hyphens allowed
- No path traversal patterns (`..`, `/`, `\`)

**Channels:**
- Validated against whitelist of allowed channels
- Prevents command injection

**Versions:**
- Alphanumeric, dots, underscores, hyphens only
- Maximum 100 characters

### Credential Storage

- API keys are loaded from environment variables
- Never logged or exposed in state files
- Passed to subprocesses via environment, not command line

### Example Validation

```python
from game_workflow.utils.validation import (
    validate_itchio_target,
    validate_channel,
    validate_version,
)

# Valid inputs
target = validate_itchio_target("myuser/my-game")  # OK
channel = validate_channel("html5")  # OK
version = validate_version("1.0.0-beta.1")  # OK

# Invalid inputs raise ValueError
validate_itchio_target("../hack")  # ValueError: path traversal
validate_channel("custom-channel")  # ValueError: not in whitelist
validate_version("version; rm -rf /")  # ValueError: invalid characters
```

## Troubleshooting

### Common Issues

**"Server failed to start"**

1. Check the server command and arguments
2. Verify required environment variables are set
3. Check the working directory exists

```python
# Debug server startup
registry = MCPServerRegistry()
config = registry.get("itchio")
print(f"Command: {config.command} {' '.join(config.args)}")
print(f"Env: {config.env}")
```

**"Butler not found"**

```python
butler = ButlerCLI()
if not butler.check_installed():
    print("Butler not installed, downloading...")
    await butler.download_butler()
```

**"API key invalid"**

```python
api = ItchioAPI()
if not await api.check_api_key():
    print("Invalid or expired API key")
```

**"Rate limit exceeded"**

The API client automatically handles rate limiting with retries. If you still hit limits:

```python
# Increase retry settings
api = ItchioAPI(
    max_retries=5,
    retry_delay=5.0,
)
```

### Logging

Enable debug logging to see server communication:

```python
import logging
logging.getLogger("game_workflow.mcp_servers").setLevel(logging.DEBUG)
```

## Related Documentation

- [Setup Guide](setup.md) — Initial setup instructions
- [Configuration Reference](configuration.md) — All configuration options
- [Skills](skills.md) — Game development skills
