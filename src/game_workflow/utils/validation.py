"""Input validation utilities.

This module provides validation functions for user inputs.
"""

SUPPORTED_ENGINES = {"phaser", "godot"}
MIN_PROMPT_LENGTH = 10
MAX_PROMPT_LENGTH = 5000


def validate_prompt(prompt: str) -> str:
    """Validate a game concept prompt.

    Args:
        prompt: The prompt to validate.

    Returns:
        The validated prompt (stripped).

    Raises:
        ValueError: If prompt is invalid.
    """
    prompt = prompt.strip()

    if len(prompt) < MIN_PROMPT_LENGTH:
        raise ValueError(f"Prompt too short (minimum {MIN_PROMPT_LENGTH} characters)")

    if len(prompt) > MAX_PROMPT_LENGTH:
        raise ValueError(f"Prompt too long (maximum {MAX_PROMPT_LENGTH} characters)")

    return prompt


def validate_engine(engine: str) -> str:
    """Validate a game engine selection.

    Args:
        engine: The engine name to validate.

    Returns:
        The validated engine name (lowercase).

    Raises:
        ValueError: If engine is not supported.
    """
    engine = engine.lower().strip()

    if engine not in SUPPORTED_ENGINES:
        raise ValueError(
            f"Unsupported engine: {engine}. Supported: {', '.join(sorted(SUPPORTED_ENGINES))}"
        )

    return engine
