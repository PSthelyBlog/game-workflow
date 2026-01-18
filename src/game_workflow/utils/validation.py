"""Input validation utilities.

This module provides validation functions for user inputs,
including security-critical validation for paths, identifiers, and external inputs.
"""

from __future__ import annotations

import re
from pathlib import Path

SUPPORTED_ENGINES = {"phaser", "godot"}

# Allowed channels for itch.io uploads
ALLOWED_CHANNELS = {
    "html5",
    "windows",
    "windows-32",
    "windows-64",
    "linux",
    "linux-32",
    "linux-64",
    "mac",
    "osx",
    "android",
    "ios",
}
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


# Regular expressions for validation
# State ID: timestamp format YYYYMMDD_HHMMSS or custom alphanumeric with underscores
STATE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

# itch.io target: username/game-name format
ITCHIO_TARGET_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$")

# Version string: semantic version or simple version numbers
VERSION_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+$")


def validate_state_id(state_id: str) -> str:
    """Validate a workflow state ID.

    State IDs should be alphanumeric with underscores/hyphens only.
    This prevents path traversal attacks when loading state files.

    Args:
        state_id: The state ID to validate.

    Returns:
        The validated state ID.

    Raises:
        ValueError: If state_id contains invalid characters.
    """
    if not state_id:
        raise ValueError("State ID cannot be empty")

    if not STATE_ID_PATTERN.match(state_id):
        raise ValueError(
            f"Invalid state ID: {state_id!r}. "
            "State IDs must contain only alphanumeric characters, underscores, and hyphens."
        )

    # Additional check for path traversal patterns
    if ".." in state_id or state_id.startswith("/") or state_id.startswith("\\"):
        raise ValueError(f"Invalid state ID: {state_id!r}. Path traversal patterns not allowed.")

    return state_id


def validate_itchio_target(target: str) -> str:
    """Validate an itch.io target (username/game-name).

    Args:
        target: The itch.io target to validate.

    Returns:
        The validated target.

    Raises:
        ValueError: If target format is invalid.
    """
    if not target:
        raise ValueError("itch.io target cannot be empty")

    if not ITCHIO_TARGET_PATTERN.match(target):
        raise ValueError(
            f"Invalid itch.io target: {target!r}. "
            "Target must be in format 'username/game-name' with alphanumeric characters, "
            "underscores, and hyphens only."
        )

    return target


def validate_channel(channel: str) -> str:
    """Validate an itch.io release channel.

    Args:
        channel: The channel name to validate.

    Returns:
        The validated channel (lowercase).

    Raises:
        ValueError: If channel is not in the allowed list.
    """
    if not channel:
        raise ValueError("Channel cannot be empty")

    channel = channel.lower().strip()

    if channel not in ALLOWED_CHANNELS:
        raise ValueError(
            f"Invalid channel: {channel!r}. Allowed channels: {', '.join(sorted(ALLOWED_CHANNELS))}"
        )

    return channel


def validate_version(version: str) -> str:
    """Validate a version string.

    Args:
        version: The version string to validate.

    Returns:
        The validated version string.

    Raises:
        ValueError: If version contains invalid characters.
    """
    if not version:
        raise ValueError("Version cannot be empty")

    version = version.strip()

    if not VERSION_PATTERN.match(version):
        raise ValueError(
            f"Invalid version: {version!r}. "
            "Version must contain only alphanumeric characters, dots, underscores, and hyphens."
        )

    # Max length check to prevent buffer overflow attacks
    if len(version) > 100:
        raise ValueError("Version string too long (maximum 100 characters)")

    return version


def validate_path_safety(
    path: str | Path,
    allowed_parent: Path | None = None,
    must_exist: bool = False,
) -> Path:
    """Validate a path for safety against path traversal attacks.

    This function:
    1. Resolves the path to an absolute path
    2. Checks for path traversal patterns
    3. Optionally verifies the path is within an allowed parent directory
    4. Optionally checks if the path exists

    Args:
        path: The path to validate.
        allowed_parent: If set, the path must be within this directory.
        must_exist: If True, raise an error if the path doesn't exist.

    Returns:
        The resolved, validated Path object.

    Raises:
        ValueError: If the path is invalid or outside allowed boundaries.
        FileNotFoundError: If must_exist is True and path doesn't exist.
    """
    if not path:
        raise ValueError("Path cannot be empty")

    # Check for null bytes (common attack vector) before Path operations
    path_str = str(path)
    if "\x00" in path_str:
        raise ValueError("Path contains null bytes")

    # Convert to Path and resolve to absolute
    try:
        path_obj = Path(path).resolve()
    except ValueError as e:
        # Re-raise with consistent message for null bytes
        if "null" in str(e).lower():
            raise ValueError("Path contains null bytes") from e
        raise

    # Check for suspicious patterns in the original input
    original_str = str(path)
    if ".." in original_str:
        raise ValueError(f"Path traversal pattern detected in: {original_str!r}")

    # If allowed_parent is specified, verify the path is within it
    if allowed_parent is not None:
        allowed_parent = allowed_parent.resolve()
        try:
            path_obj.relative_to(allowed_parent)
        except ValueError as e:
            raise ValueError(
                f"Path {path_obj} is outside allowed directory {allowed_parent}"
            ) from e

    # Check existence if required
    if must_exist and not path_obj.exists():
        raise FileNotFoundError(f"Path does not exist: {path_obj}")

    return path_obj


def validate_directory_path(
    path: str | Path,
    allowed_parent: Path | None = None,
    must_exist: bool = True,
) -> Path:
    """Validate a directory path.

    Args:
        path: The directory path to validate.
        allowed_parent: If set, the path must be within this directory.
        must_exist: If True, raise an error if the directory doesn't exist.

    Returns:
        The resolved, validated Path object.

    Raises:
        ValueError: If the path is invalid, not a directory, or outside allowed boundaries.
        FileNotFoundError: If must_exist is True and path doesn't exist.
    """
    path_obj = validate_path_safety(path, allowed_parent, must_exist=must_exist)

    if must_exist and not path_obj.is_dir():
        raise ValueError(f"Path is not a directory: {path_obj}")

    return path_obj
