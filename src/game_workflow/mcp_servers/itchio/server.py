"""MCP server implementation for itch.io.

This module implements the MCP server protocol for itch.io operations,
providing tools for uploading games, managing store pages, and publishing.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    TextContent,
    Tool,
)
from pydantic import BaseModel, Field

from game_workflow.mcp_servers.itchio.api import ItchioAPI
from game_workflow.mcp_servers.itchio.butler import ButlerCLI

logger = logging.getLogger(__name__)

# Type alias for content that can be used in CallToolResult
ContentList = list[TextContent]


# Tool parameter schemas
class UploadGameParams(BaseModel):
    """Parameters for upload_game tool."""

    directory: str = Field(description="Path to the directory containing the game build")
    target: str = Field(description="itch.io target in format 'username/game-name'")
    channel: str = Field(
        default="html5", description="Release channel (e.g., html5, windows, linux)"
    )
    version: str | None = Field(default=None, description="Version string for this upload")
    dry_run: bool = Field(default=False, description="If true, validate but don't actually upload")


class UpdateGamePageParams(BaseModel):
    """Parameters for update_game_page tool."""

    target: str = Field(description="itch.io target in format 'username/game-name'")
    title: str | None = Field(default=None, description="New game title")
    short_description: str | None = Field(default=None, description="Short description (tagline)")
    description: str | None = Field(
        default=None, description="Full game description (HTML or Markdown)"
    )


class PublishGameParams(BaseModel):
    """Parameters for publish_game tool."""

    target: str = Field(description="itch.io target in format 'username/game-name'")
    channel: str = Field(default="html5", description="Channel to publish")


class GetGameStatusParams(BaseModel):
    """Parameters for get_game_status tool."""

    target: str = Field(description="itch.io target in format 'username/game-name'")


class GetMyGamesParams(BaseModel):
    """Parameters for get_my_games tool."""

    pass


class CheckCredentialsParams(BaseModel):
    """Parameters for check_credentials tool."""

    pass


# Create the MCP server
server = Server("itchio")


def _create_error_response(message: str, code: int = -32603) -> ContentList:
    """Create an error response.

    Args:
        message: Error message.
        code: Error code (default: -32603 for internal error).

    Returns:
        List containing error text content.
    """
    return [TextContent(type="text", text=json.dumps({"error": message, "code": code}))]


def _create_success_response(data: dict[str, Any]) -> ContentList:
    """Create a success response.

    Args:
        data: Response data.

    Returns:
        List containing success text content.
    """
    return [TextContent(type="text", text=json.dumps({"success": True, **data}))]


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available itch.io tools."""
    return [
        Tool(
            name="upload_game",
            description="Upload a game build to itch.io using butler. "
            "Requires a built game directory and an itch.io target (username/game-name).",
            inputSchema=UploadGameParams.model_json_schema(),
        ),
        Tool(
            name="get_game_status",
            description="Get the current status of a game on itch.io, including all channels and uploads.",
            inputSchema=GetGameStatusParams.model_json_schema(),
        ),
        Tool(
            name="get_my_games",
            description="Get a list of all games owned by the authenticated user.",
            inputSchema=GetMyGamesParams.model_json_schema(),
        ),
        Tool(
            name="check_credentials",
            description="Check if the itch.io API credentials are valid and return user information.",
            inputSchema=CheckCredentialsParams.model_json_schema(),
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
    """Handle tool calls.

    Args:
        name: Tool name.
        arguments: Tool arguments.

    Returns:
        Tool result.
    """
    try:
        if name == "upload_game":
            return await _upload_game(arguments)
        elif name == "get_game_status":
            return await _get_game_status(arguments)
        elif name == "get_my_games":
            return await _get_my_games(arguments)
        elif name == "check_credentials":
            return await _check_credentials(arguments)
        else:
            return CallToolResult(
                content=_create_error_response(f"Unknown tool: {name}", -32602),
                isError=True,
            )
    except Exception as e:
        logger.exception("Error in tool %s", name)
        return CallToolResult(
            content=_create_error_response(str(e)),
            isError=True,
        )


async def _upload_game(arguments: dict[str, Any]) -> CallToolResult:
    """Handle upload_game tool.

    Args:
        arguments: Tool arguments.

    Returns:
        Tool result.
    """
    try:
        params = UploadGameParams(**arguments)
    except Exception as e:
        return CallToolResult(
            content=_create_error_response(f"Invalid parameters: {e}", -32602),
            isError=True,
        )

    directory = Path(params.directory)

    # Validate directory
    if not directory.exists():
        return CallToolResult(
            content=_create_error_response(f"Directory does not exist: {directory}"),
            isError=True,
        )

    if not directory.is_dir():
        return CallToolResult(
            content=_create_error_response(f"Path is not a directory: {directory}"),
            isError=True,
        )

    # Initialize butler
    butler = ButlerCLI()

    # Check if butler is installed
    if not butler.check_installed():
        return CallToolResult(
            content=_create_error_response(
                "Butler CLI is not installed. Please install butler first: "
                "https://itch.io/docs/butler/installing.html"
            ),
            isError=True,
        )

    # Validate directory contents
    is_valid, validation_message = await butler.validate(directory)
    if not is_valid:
        return CallToolResult(
            content=_create_error_response(f"Invalid game directory: {validation_message}"),
            isError=True,
        )

    # Push the game
    result = await butler.push(
        directory=directory,
        target=params.target,
        channel=params.channel,
        version=params.version,
        dry_run=params.dry_run,
    )

    if result.success:
        return CallToolResult(
            content=_create_success_response(
                {
                    "target": result.target,
                    "channel": result.channel,
                    "version": result.version,
                    "build_id": result.build_id,
                    "dry_run": params.dry_run,
                    "message": f"Successfully uploaded to {result.target}:{result.channel}",
                }
            ),
        )
    else:
        return CallToolResult(
            content=_create_error_response(result.error or "Upload failed"),
            isError=True,
        )


async def _get_game_status(arguments: dict[str, Any]) -> CallToolResult:
    """Handle get_game_status tool.

    Args:
        arguments: Tool arguments.

    Returns:
        Tool result.
    """
    try:
        params = GetGameStatusParams(**arguments)
    except Exception as e:
        return CallToolResult(
            content=_create_error_response(f"Invalid parameters: {e}", -32602),
            isError=True,
        )

    # Initialize butler
    butler = ButlerCLI()

    if not butler.check_installed():
        return CallToolResult(
            content=_create_error_response(
                "Butler CLI is not installed. Please install butler first: "
                "https://itch.io/docs/butler/installing.html"
            ),
            isError=True,
        )

    # Get status
    result = await butler.status(params.target)

    if result.success:
        return CallToolResult(
            content=_create_success_response(
                {
                    "target": result.target,
                    "channels": result.channels,
                }
            ),
        )
    else:
        return CallToolResult(
            content=_create_error_response(result.error or "Failed to get status"),
            isError=True,
        )


async def _get_my_games(
    arguments: dict[str, Any],  # noqa: ARG001
) -> CallToolResult:
    """Handle get_my_games tool.

    Args:
        arguments: Tool arguments (unused, no parameters needed).

    Returns:
        Tool result.
    """
    api_key = os.environ.get("ITCHIO_API_KEY")
    if not api_key:
        return CallToolResult(
            content=_create_error_response("ITCHIO_API_KEY environment variable is not set"),
            isError=True,
        )

    async with ItchioAPI(api_key=api_key) as api:
        games = await api.get_my_games()

        games_data = []
        for game in games:
            games_data.append(
                {
                    "id": game.id,
                    "title": game.title,
                    "url": game.url,
                    "short_text": game.short_text,
                    "classification": game.classification.value,
                    "downloads_count": game.downloads_count,
                    "views_count": game.views_count,
                }
            )

        return CallToolResult(
            content=_create_success_response(
                {
                    "games": games_data,
                    "count": len(games_data),
                }
            ),
        )


async def _check_credentials(
    arguments: dict[str, Any],  # noqa: ARG001
) -> CallToolResult:
    """Handle check_credentials tool.

    Args:
        arguments: Tool arguments (unused, no parameters needed).

    Returns:
        Tool result.
    """
    api_key = os.environ.get("ITCHIO_API_KEY")
    if not api_key:
        return CallToolResult(
            content=_create_error_response("ITCHIO_API_KEY environment variable is not set"),
            isError=True,
        )

    # Check butler
    butler = ButlerCLI()
    butler_installed = butler.check_installed()
    butler_version = None
    butler_logged_in = False

    if butler_installed:
        version_info = butler.get_version()
        if version_info:
            butler_version = version_info.version
        butler_logged_in = butler.is_logged_in()

    # Check API
    async with ItchioAPI(api_key=api_key) as api:
        user = await api.get_me()

        if user:
            return CallToolResult(
                content=_create_success_response(
                    {
                        "api_valid": True,
                        "user": {
                            "id": user.id,
                            "username": user.username,
                            "display_name": user.display_name,
                            "url": user.url,
                            "developer": user.developer,
                        },
                        "butler": {
                            "installed": butler_installed,
                            "version": butler_version,
                            "logged_in": butler_logged_in,
                        },
                    }
                ),
            )
        else:
            return CallToolResult(
                content=_create_error_response("Invalid API key or failed to authenticate"),
                isError=True,
            )


async def run_server() -> None:
    """Run the MCP server."""
    logger.info("Starting itch.io MCP server")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main() -> None:
    """Run the itch.io MCP server."""
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
