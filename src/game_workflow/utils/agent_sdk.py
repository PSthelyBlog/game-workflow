"""Claude Agent SDK utilities for structured JSON generation.

This module provides wrapper functions for using the Claude Agent SDK
in the game workflow. It handles text generation tasks that were previously
done with the Anthropic Python SDK.

The Agent SDK automatically inherits authentication from:
1. Claude Code CLI session (subscription-based auth for Pro/Max users)
2. ANTHROPIC_API_KEY environment variable (API key auth)

No explicit configuration is needed - the SDK handles auth priority automatically.
"""

from __future__ import annotations

import logging
from pathlib import Path  # noqa: TC003 - Used at runtime for file operations
from typing import Any

from claude_code_sdk import ClaudeCodeOptions, query

logger = logging.getLogger(__name__)

# Default model for text generation tasks
DEFAULT_MODEL = "claude-sonnet-4-5-20250929"


async def generate_structured_response(
    prompt: str,
    system_prompt: str,
    model: str = DEFAULT_MODEL,
) -> str:
    """Generate a text response using the Agent SDK.

    This function is used for tasks that need Claude to generate structured
    text output (like JSON) without needing file system access or tools.

    Args:
        prompt: The user prompt to send to the model.
        system_prompt: The system prompt that sets context and instructions.
        model: The Claude model to use.

    Returns:
        The concatenated text from all assistant messages.

    Raises:
        RuntimeError: If the Agent SDK returns an error.
    """
    # Combine system prompt and user prompt for the query
    # The Agent SDK doesn't have a separate system_prompt option,
    # so we include it in the prompt itself
    full_prompt = f"{system_prompt}\n\n---\n\n{prompt}"

    text_parts: list[str] = []

    async for message in query(
        prompt=full_prompt,
        options=ClaudeCodeOptions(
            model=model,
            max_turns=1,  # Single turn for generation tasks
        ),
    ):
        # Handle different message types
        if hasattr(message, "content"):
            for block in message.content:
                if hasattr(block, "text"):
                    text_parts.append(block.text)

    result = "".join(text_parts)
    if not result:
        raise RuntimeError("Agent SDK returned empty response")

    return result


async def invoke_claude_code(
    working_dir: Path,
    prompt: str,
    allowed_tools: list[str] | None = None,
    context_files: list[Path] | None = None,
    max_turns: int = 50,
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    """Invoke Claude Code using the Agent SDK for agentic tasks.

    This function is used for tasks that need Claude Code to work with
    files, run commands, and make changes - like implementing a game.

    Args:
        working_dir: The working directory for Claude Code.
        prompt: The task prompt for Claude Code.
        allowed_tools: Optional list of allowed tools (e.g., ["Read", "Write", "Bash"]).
        context_files: Optional files to include as context in the prompt.
        max_turns: Maximum number of agentic turns.
        model: The Claude model to use.

    Returns:
        Dict containing:
            - success: Whether the task completed successfully
            - output: The text output from Claude Code
            - error: Error message if failed

    Raises:
        RuntimeError: If Claude Code execution fails critically.
    """
    # Build the full prompt with context files embedded
    full_prompt = prompt

    if context_files:
        context_parts = []
        for context_file in context_files:
            if context_file.exists():
                try:
                    content = context_file.read_text(encoding="utf-8")
                    context_parts.append(
                        f"\n\n--- Context from {context_file.name} ---\n"
                        f"{content}\n"
                        f"--- End {context_file.name} ---"
                    )
                except Exception as e:
                    logger.warning(f"Could not read context file {context_file}: {e}")
        if context_parts:
            full_prompt = prompt + "".join(context_parts)

    output_parts: list[str] = []
    error_message: str | None = None
    success = True

    try:
        options = ClaudeCodeOptions(
            model=model,
            cwd=str(working_dir),
            max_turns=max_turns,
            allowed_tools=allowed_tools or ["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
        )

        async for message in query(prompt=full_prompt, options=options):
            # Collect text output from messages
            if hasattr(message, "content"):
                for block in message.content:
                    if hasattr(block, "text"):
                        output_parts.append(block.text)
                        logger.debug(f"claude-code: {block.text[:100]}...")

    except Exception as e:
        logger.error(f"Claude Code execution failed: {e}")
        error_message = str(e)
        success = False

    return {
        "success": success,
        "output": "\n".join(output_parts),
        "error": error_message,
    }
