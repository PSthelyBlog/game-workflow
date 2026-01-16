"""Butler CLI wrapper for itch.io uploads.

This module provides a Python wrapper around the butler CLI
for uploading games to itch.io.
"""

import subprocess
from pathlib import Path


class ButlerCLI:
    """Wrapper for the butler CLI tool.

    Butler is itch.io's command-line tool for uploading games
    and managing releases.
    """

    def __init__(self, butler_path: str = "butler") -> None:
        """Initialize the butler wrapper.

        Args:
            butler_path: Path to the butler executable.
        """
        self.butler_path = butler_path

    def check_installed(self) -> bool:
        """Check if butler is installed and accessible.

        Returns:
            True if butler is available.
        """
        try:
            result = subprocess.run(
                [self.butler_path, "version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def push(
        self,
        directory: Path,
        target: str,
        channel: str = "html5",
    ) -> dict[str, str]:
        """Push a game build to itch.io.

        Args:
            directory: Directory containing the game build.
            target: The itch.io target (username/game-name).
            channel: The release channel.

        Returns:
            Dict with upload results.

        Raises:
            RuntimeError: If the upload fails.
        """
        # TODO: Implement butler push
        raise NotImplementedError("Butler push not yet implemented")

    def status(self, target: str) -> dict[str, str]:
        """Get the status of an itch.io game.

        Args:
            target: The itch.io target (username/game-name).

        Returns:
            Dict with game status.
        """
        # TODO: Implement butler status
        raise NotImplementedError("Butler status not yet implemented")
