"""itch.io MCP server for game publishing.

This module provides an MCP server for interacting with itch.io,
including game uploads via butler and API interactions.
"""

from game_workflow.mcp_servers.itchio.api import (
    APIResponse,
    GameClassification,
    GameType,
    ItchioAPI,
    ItchioAPIError,
    ItchioGame,
    ItchioUpload,
    ItchioUser,
    ReleaseStatus,
)
from game_workflow.mcp_servers.itchio.butler import (
    ButlerCLI,
    ButlerPushResult,
    ButlerStatusResult,
    ButlerVersion,
)

__all__ = [
    "APIResponse",
    "ButlerCLI",
    "ButlerPushResult",
    "ButlerStatusResult",
    "ButlerVersion",
    "GameClassification",
    "GameType",
    "ItchioAPI",
    "ItchioAPIError",
    "ItchioGame",
    "ItchioUpload",
    "ItchioUser",
    "ReleaseStatus",
]
