"""Pytest configuration and fixtures."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def sample_prompt() -> str:
    """Provide a sample game prompt for testing."""
    return "Create a puzzle platformer about time manipulation"


@pytest.fixture
def sample_gdd_content() -> str:
    """Provide sample GDD content for testing."""
    return """# Game Design Document

## Overview
A puzzle platformer where the player can manipulate time.

## Mechanics
- Time rewind
- Time slow
- Time freeze zones
"""


@pytest.fixture
def mock_generate_structured_response(monkeypatch: pytest.MonkeyPatch):
    """Mock the Agent SDK generate_structured_response function.

    Returns a factory function that configures the mock with the desired response.
    """

    def _configure_mock(response_text: str) -> AsyncMock:
        """Configure the mock to return the specified text."""
        mock = AsyncMock(return_value=response_text)
        monkeypatch.setattr(
            "game_workflow.utils.agent_sdk.generate_structured_response",
            mock,
        )
        return mock

    return _configure_mock


@pytest.fixture
def mock_invoke_claude_code(monkeypatch: pytest.MonkeyPatch):
    """Mock the Agent SDK invoke_claude_code function.

    Returns a factory function that configures the mock with the desired result.
    """

    def _configure_mock(
        success: bool = True,
        output: str = "Build completed successfully",
        error: str | None = None,
    ) -> AsyncMock:
        """Configure the mock to return the specified result."""
        result: dict[str, Any] = {
            "success": success,
            "output": output,
            "error": error,
        }
        mock = AsyncMock(return_value=result)
        monkeypatch.setattr(
            "game_workflow.utils.agent_sdk.invoke_claude_code",
            mock,
        )
        return mock

    return _configure_mock


@pytest.fixture
def mock_agent_sdk_query(monkeypatch: pytest.MonkeyPatch):
    """Mock the Agent SDK query function for low-level testing.

    Returns a factory function that configures the mock with the desired messages.
    """

    def _configure_mock(response_text: str):
        """Configure the mock to yield messages with the specified text."""

        async def mock_query(*_args: Any, **_kwargs: Any):
            """Async generator that yields mock messages."""
            # Create a mock message with content
            message = MagicMock()
            text_block = MagicMock()
            text_block.text = response_text
            message.content = [text_block]
            yield message

        monkeypatch.setattr("claude_code_sdk.query", mock_query)

    return _configure_mock
