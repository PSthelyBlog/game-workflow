"""Unit tests for security validation functions.

Tests input validation to prevent command injection and path traversal attacks.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from game_workflow.utils.validation import (
    ALLOWED_CHANNELS,
    validate_channel,
    validate_directory_path,
    validate_itchio_target,
    validate_path_safety,
    validate_state_id,
    validate_version,
)

if TYPE_CHECKING:
    from pathlib import Path


class TestValidateStateId:
    """Tests for validate_state_id function."""

    def test_valid_timestamp_format(self) -> None:
        """Test valid timestamp-format state IDs."""
        assert validate_state_id("20260118_143052") == "20260118_143052"

    def test_valid_alphanumeric(self) -> None:
        """Test valid alphanumeric state IDs."""
        assert validate_state_id("test_state_001") == "test_state_001"
        assert validate_state_id("MyState123") == "MyState123"
        assert validate_state_id("state-with-hyphens") == "state-with-hyphens"

    def test_empty_state_id(self) -> None:
        """Test that empty state ID raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_state_id("")

    def test_path_traversal_attack(self) -> None:
        """Test that path traversal patterns are rejected."""
        with pytest.raises(ValueError, match="Invalid state ID"):
            validate_state_id("../../../etc/passwd")

        with pytest.raises(ValueError, match="Invalid state ID"):
            validate_state_id("..%2F..%2Fetc%2Fpasswd")

    def test_absolute_path_attack(self) -> None:
        """Test that absolute paths are rejected."""
        with pytest.raises(ValueError, match="Invalid state ID"):
            validate_state_id("/etc/passwd")

        with pytest.raises(ValueError, match="Invalid state ID"):
            validate_state_id("\\windows\\system32")

    def test_special_characters_rejected(self) -> None:
        """Test that special characters are rejected."""
        invalid_ids = [
            "state;id",
            "state|id",
            "state&id",
            "state$(cmd)",
            "state`cmd`",
            "state\nid",
            "state\x00id",
            "state/subdir",
        ]
        for invalid_id in invalid_ids:
            with pytest.raises(ValueError, match="Invalid state ID"):
                validate_state_id(invalid_id)


class TestValidateItchioTarget:
    """Tests for validate_itchio_target function."""

    def test_valid_targets(self) -> None:
        """Test valid itch.io targets."""
        assert validate_itchio_target("username/game-name") == "username/game-name"
        assert validate_itchio_target("my_user/my_game") == "my_user/my_game"
        assert validate_itchio_target("user123/game456") == "user123/game456"

    def test_empty_target(self) -> None:
        """Test that empty target raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_itchio_target("")

    def test_missing_slash(self) -> None:
        """Test that target without slash is rejected."""
        with pytest.raises(ValueError, match=r"Invalid itch\.io target"):
            validate_itchio_target("usergame")

    def test_multiple_slashes(self) -> None:
        """Test that multiple slashes are rejected."""
        with pytest.raises(ValueError, match=r"Invalid itch\.io target"):
            validate_itchio_target("user/game/extra")

    def test_command_injection_patterns(self) -> None:
        """Test that command injection patterns are rejected."""
        invalid_targets = [
            "user/game; rm -rf /",
            "user/game && echo hacked",
            "user/game | cat /etc/passwd",
            "user/game$(whoami)",
            "user/game`id`",
            "user\ngame/test",
        ]
        for invalid_target in invalid_targets:
            with pytest.raises(ValueError, match=r"Invalid itch\.io target"):
                validate_itchio_target(invalid_target)

    def test_special_characters_rejected(self) -> None:
        """Test that special characters in username or game are rejected."""
        invalid_targets = [
            "user@name/game",
            "user/game@name",
            "user name/game",
            "user/game name",
            "user/game.name",  # dots not allowed
        ]
        for invalid_target in invalid_targets:
            with pytest.raises(ValueError, match=r"Invalid itch\.io target"):
                validate_itchio_target(invalid_target)


class TestValidateChannel:
    """Tests for validate_channel function."""

    def test_valid_channels(self) -> None:
        """Test all valid channels."""
        for channel in ALLOWED_CHANNELS:
            assert validate_channel(channel) == channel

    def test_case_insensitive(self) -> None:
        """Test that validation is case-insensitive."""
        assert validate_channel("HTML5") == "html5"
        assert validate_channel("WINDOWS") == "windows"
        assert validate_channel("Linux") == "linux"

    def test_strips_whitespace(self) -> None:
        """Test that whitespace is stripped."""
        assert validate_channel("  html5  ") == "html5"

    def test_empty_channel(self) -> None:
        """Test that empty channel raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_channel("")

    def test_invalid_channels(self) -> None:
        """Test that invalid channels are rejected."""
        invalid_channels = [
            "invalid",
            "web",
            "desktop",
            "html6",
            "windows-arm",
            "../html5",
            "html5; rm -rf /",
        ]
        for invalid_channel in invalid_channels:
            with pytest.raises(ValueError, match="Invalid channel"):
                validate_channel(invalid_channel)


class TestValidateVersion:
    """Tests for validate_version function."""

    def test_valid_versions(self) -> None:
        """Test valid version strings."""
        valid_versions = [
            "1.0.0",
            "1.0",
            "1",
            "v1.0.0",
            "1.0.0-beta",
            "1.0.0_rc1",
            "2026.01.18",
            "build-123",
        ]
        for version in valid_versions:
            assert validate_version(version) == version

    def test_empty_version(self) -> None:
        """Test that empty version raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_version("")

    def test_strips_whitespace(self) -> None:
        """Test that whitespace is stripped."""
        assert validate_version("  1.0.0  ") == "1.0.0"

    def test_command_injection_patterns(self) -> None:
        """Test that command injection patterns are rejected."""
        invalid_versions = [
            "1.0; rm -rf /",
            "1.0 && echo hacked",
            "1.0 | cat /etc/passwd",
            "1.0$(whoami)",
            "1.0`id`",
            "1.0\n2.0",
        ]
        for invalid_version in invalid_versions:
            with pytest.raises(ValueError, match="Invalid version"):
                validate_version(invalid_version)

    def test_too_long_version(self) -> None:
        """Test that overly long versions are rejected."""
        with pytest.raises(ValueError, match="too long"):
            validate_version("a" * 101)


class TestValidatePathSafety:
    """Tests for validate_path_safety function."""

    def test_valid_absolute_path(self, tmp_path: Path) -> None:
        """Test valid absolute path."""
        test_file = tmp_path / "test.txt"
        test_file.touch()
        result = validate_path_safety(test_file, must_exist=True)
        assert result == test_file.resolve()

    def test_valid_relative_path(self, tmp_path: Path) -> None:
        """Test valid relative path is resolved."""
        import os

        os.chdir(tmp_path)
        test_file = tmp_path / "test.txt"
        test_file.touch()
        result = validate_path_safety("test.txt", must_exist=True)
        assert result == test_file.resolve()

    def test_empty_path(self) -> None:
        """Test that empty path raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_path_safety("")

    def test_path_traversal_detected(self, tmp_path: Path) -> None:
        """Test that path traversal patterns are detected."""
        with pytest.raises(ValueError, match="Path traversal pattern"):
            validate_path_safety(str(tmp_path / ".." / ".." / "etc" / "passwd"))

    def test_null_byte_attack(self) -> None:
        """Test that null bytes are rejected."""
        with pytest.raises(ValueError, match="null bytes"):
            validate_path_safety("/path/to/file\x00.txt")

    def test_allowed_parent_validation(self, tmp_path: Path) -> None:
        """Test that path must be within allowed parent."""
        test_file = tmp_path / "subdir" / "test.txt"
        test_file.parent.mkdir()
        test_file.touch()

        # Valid: within allowed parent
        result = validate_path_safety(test_file, allowed_parent=tmp_path, must_exist=True)
        assert result == test_file.resolve()

    def test_path_outside_allowed_parent(self, tmp_path: Path) -> None:
        """Test that paths outside allowed parent are rejected."""
        with pytest.raises(ValueError, match="outside allowed directory"):
            validate_path_safety("/etc/passwd", allowed_parent=tmp_path)

    def test_must_exist_file_not_found(self, tmp_path: Path) -> None:
        """Test that non-existent path raises FileNotFoundError when must_exist=True."""
        with pytest.raises(FileNotFoundError):
            validate_path_safety(tmp_path / "nonexistent.txt", must_exist=True)

    def test_must_exist_false(self, tmp_path: Path) -> None:
        """Test that non-existent path is allowed when must_exist=False."""
        path = tmp_path / "nonexistent.txt"
        result = validate_path_safety(path, must_exist=False)
        assert result == path.resolve()


class TestValidateDirectoryPath:
    """Tests for validate_directory_path function."""

    def test_valid_directory(self, tmp_path: Path) -> None:
        """Test valid directory path."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        result = validate_directory_path(subdir)
        assert result == subdir.resolve()

    def test_file_not_directory(self, tmp_path: Path) -> None:
        """Test that file (not directory) raises ValueError."""
        test_file = tmp_path / "test.txt"
        test_file.touch()
        with pytest.raises(ValueError, match="not a directory"):
            validate_directory_path(test_file)

    def test_nonexistent_directory(self, tmp_path: Path) -> None:
        """Test that non-existent directory raises error."""
        with pytest.raises(FileNotFoundError):
            validate_directory_path(tmp_path / "nonexistent")


class TestStateIdPathTraversal:
    """Integration tests for state ID path traversal prevention."""

    def test_state_load_with_path_traversal(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that WorkflowState.load rejects path traversal."""
        from game_workflow.orchestrator.state import WorkflowState

        # Set up settings to use tmp_path
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))

        with pytest.raises(ValueError, match="Invalid state ID"):
            WorkflowState.load("../../../etc/passwd")

    def test_state_delete_with_path_traversal(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that WorkflowState.delete rejects path traversal."""
        from game_workflow.orchestrator.state import WorkflowState

        # Set up settings to use tmp_path
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path))

        with pytest.raises(ValueError, match="Invalid state ID"):
            WorkflowState.delete("../../../etc/passwd")


class TestButlerInputValidation:
    """Tests for butler CLI input validation."""

    @pytest.mark.asyncio
    async def test_push_with_invalid_target(self, tmp_path: Path) -> None:
        """Test that push rejects invalid targets."""
        from game_workflow.mcp_servers.itchio.butler import ButlerCLI

        butler = ButlerCLI()
        (tmp_path / "index.html").touch()

        result = await butler.push(
            directory=tmp_path,
            target="user/game; rm -rf /",
            channel="html5",
        )

        assert not result.success
        assert "Invalid itch.io target" in (result.error or "")

    @pytest.mark.asyncio
    async def test_push_with_invalid_channel(self, tmp_path: Path) -> None:
        """Test that push rejects invalid channels."""
        from game_workflow.mcp_servers.itchio.butler import ButlerCLI

        butler = ButlerCLI()
        (tmp_path / "index.html").touch()

        result = await butler.push(
            directory=tmp_path,
            target="user/game",
            channel="invalid-channel",
        )

        assert not result.success
        assert "Invalid channel" in (result.error or "")

    @pytest.mark.asyncio
    async def test_push_with_invalid_version(self, tmp_path: Path) -> None:
        """Test that push rejects invalid versions."""
        from game_workflow.mcp_servers.itchio.butler import ButlerCLI

        butler = ButlerCLI()
        (tmp_path / "index.html").touch()

        result = await butler.push(
            directory=tmp_path,
            target="user/game",
            channel="html5",
            version="1.0; rm -rf /",
        )

        assert not result.success
        assert "Invalid version" in (result.error or "")

    @pytest.mark.asyncio
    async def test_status_with_invalid_target(self) -> None:
        """Test that status rejects invalid targets."""
        from game_workflow.mcp_servers.itchio.butler import ButlerCLI

        butler = ButlerCLI()

        result = await butler.status("user/game && echo hacked")

        assert not result.success
        assert "Invalid itch.io target" in (result.error or "")

    @pytest.mark.asyncio
    async def test_fetch_with_invalid_target(self, tmp_path: Path) -> None:
        """Test that fetch rejects invalid targets."""
        from game_workflow.mcp_servers.itchio.butler import ButlerCLI

        butler = ButlerCLI()

        result = await butler.fetch("user|game", tmp_path)

        assert result is False
