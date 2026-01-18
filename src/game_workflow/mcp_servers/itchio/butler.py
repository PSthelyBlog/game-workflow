"""Butler CLI wrapper for itch.io uploads.

This module provides a Python wrapper around the butler CLI
for uploading games to itch.io.
"""

from __future__ import annotations

import asyncio
import logging
import os
import platform
import re
import shutil
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import httpx

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


@dataclass
class ButlerVersion:
    """Butler version information."""

    version: str
    built_at: str | None = None
    commit: str | None = None

    @classmethod
    def from_output(cls, output: str) -> ButlerVersion:
        """Parse version from butler output.

        Args:
            output: Output from `butler version` command.

        Returns:
            Parsed version information.
        """
        version = "unknown"
        built_at = None
        commit = None

        for line in output.strip().split("\n"):
            line = line.strip()
            if "version" in line.lower():
                # Format: "butler version 15.21.0, built on ..."
                match = re.search(r"version\s+([\d.]+)", line, re.IGNORECASE)
                if match:
                    version = match.group(1)
            if "built" in line.lower():
                match = re.search(r"built\s+(?:on\s+)?(.+?)(?:,|$)", line, re.IGNORECASE)
                if match:
                    built_at = match.group(1).strip()
            if "commit" in line.lower():
                match = re.search(r"commit\s+(\w+)", line, re.IGNORECASE)
                if match:
                    commit = match.group(1)

        return cls(version=version, built_at=built_at, commit=commit)


@dataclass
class ButlerPushResult:
    """Result of a butler push operation."""

    success: bool
    target: str
    channel: str
    version: str | None = None
    build_id: int | None = None
    signature_path: str | None = None
    error: str | None = None
    output: str = ""


@dataclass
class ButlerStatusResult:
    """Result of a butler status operation."""

    success: bool
    target: str
    channels: dict[str, dict[str, object]] = None  # type: ignore[assignment]
    error: str | None = None
    output: str = ""

    def __post_init__(self) -> None:
        """Initialize default values."""
        if self.channels is None:
            self.channels = {}


class ButlerCLI:
    """Wrapper for the butler CLI tool.

    Butler is itch.io's command-line tool for uploading games
    and managing releases.

    Example:
        butler = ButlerCLI()
        if not butler.check_installed():
            await butler.download_butler()
        result = await butler.push(Path("./build"), "username/game", "html5")
    """

    # Butler download URLs by platform
    DOWNLOAD_URLS: ClassVar[dict[str, str]] = {
        "darwin_x64": "https://broth.itch.ovh/butler/darwin-amd64/LATEST/archive/default",
        "darwin_arm64": "https://broth.itch.ovh/butler/darwin-arm64/LATEST/archive/default",
        "linux_x64": "https://broth.itch.ovh/butler/linux-amd64/LATEST/archive/default",
        "windows_x64": "https://broth.itch.ovh/butler/windows-amd64/LATEST/archive/default",
    }

    def __init__(
        self,
        butler_path: str | Path | None = None,
        timeout: float = 300.0,
    ) -> None:
        """Initialize the butler wrapper.

        Args:
            butler_path: Path to the butler executable.
                        If None, uses 'butler' from PATH or downloads it.
            timeout: Default timeout for butler operations in seconds.
        """
        if butler_path is None:
            # Try to find butler in PATH
            found = shutil.which("butler")
            self.butler_path = Path(found) if found else Path("butler")
        else:
            self.butler_path = Path(butler_path)
        self.timeout = timeout

    def check_installed(self) -> bool:
        """Check if butler is installed and accessible.

        Returns:
            True if butler is available.
        """
        try:
            result = subprocess.run(
                [str(self.butler_path), "version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            return False

    def get_version(self) -> ButlerVersion | None:
        """Get butler version information.

        Returns:
            Version information, or None if butler is not installed.
        """
        try:
            result = subprocess.run(
                [str(self.butler_path), "version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                return None
            return ButlerVersion.from_output(result.stdout)
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            return None

    def is_logged_in(self) -> bool:
        """Check if butler is logged in to itch.io.

        Returns:
            True if logged in.
        """
        try:
            result = subprocess.run(
                [str(self.butler_path), "login", "--check"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            return False

    @staticmethod
    def _get_platform_key() -> str:
        """Get the platform key for downloading butler.

        Returns:
            Platform key string.

        Raises:
            RuntimeError: If platform is not supported.
        """
        system = platform.system().lower()
        machine = platform.machine().lower()

        if system == "darwin":
            if machine in ("arm64", "aarch64"):
                return "darwin_arm64"
            return "darwin_x64"
        elif system == "linux":
            return "linux_x64"
        elif system == "windows":
            return "windows_x64"
        else:
            raise RuntimeError(f"Unsupported platform: {system} {machine}")

    async def download_butler(
        self,
        install_dir: Path | None = None,
        *,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> Path:
        """Download and install butler.

        Args:
            install_dir: Directory to install butler to.
                        Defaults to ~/.game-workflow/bin/
            progress_callback: Callback for download progress (bytes_downloaded, total_bytes).

        Returns:
            Path to the installed butler executable.

        Raises:
            RuntimeError: If download or installation fails.
        """
        if install_dir is None:
            install_dir = Path.home() / ".game-workflow" / "bin"

        install_dir.mkdir(parents=True, exist_ok=True)

        platform_key = self._get_platform_key()
        url = self.DOWNLOAD_URLS.get(platform_key)
        if url is None:
            raise RuntimeError(f"No butler download URL for platform: {platform_key}")

        logger.info("Downloading butler for %s from %s", platform_key, url)

        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                # Get the download URL (may redirect)
                response = await client.get(url)
                response.raise_for_status()

                # The response is a zip file
                content = response.content
                total_bytes = len(content)

                if progress_callback:
                    progress_callback(total_bytes, total_bytes)

            # Extract the zip file
            import zipfile
            from io import BytesIO

            with zipfile.ZipFile(BytesIO(content)) as zf:
                # Find the butler executable
                butler_name = "butler.exe" if platform.system() == "Windows" else "butler"
                for name in zf.namelist():
                    if name.endswith(butler_name) or name == butler_name:
                        # Extract to install directory
                        zf.extract(name, install_dir)
                        butler_path = install_dir / name
                        break
                else:
                    # Butler is directly in the zip without subdirectory
                    zf.extractall(install_dir)
                    butler_path = install_dir / butler_name

            # Make executable on Unix
            if platform.system() != "Windows":
                butler_path.chmod(
                    butler_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
                )

            # Update our path
            self.butler_path = butler_path

            logger.info("Butler installed to %s", butler_path)
            return butler_path

        except Exception as e:
            raise RuntimeError(f"Failed to download butler: {e}") from e

    async def login(self, api_key: str | None = None) -> bool:
        """Log in to itch.io.

        Args:
            api_key: API key for authentication.
                    If None, uses ITCHIO_API_KEY environment variable.

        Returns:
            True if login successful.

        Note:
            If no API key is provided, butler will open a browser
            for interactive login.
        """
        if api_key is None:
            api_key = os.environ.get("ITCHIO_API_KEY")

        if api_key:
            # Use API key login
            env = os.environ.copy()
            env["BUTLER_API_KEY"] = api_key

            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    [str(self.butler_path), "login"],
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=30,
                ),
            )
            return result.returncode == 0
        else:
            # Interactive login - this won't work in automated environments
            logger.warning("No API key provided, butler login requires interactive session")
            return False

    async def push(
        self,
        directory: Path,
        target: str,
        channel: str = "html5",
        *,
        version: str | None = None,
        fix_permissions: bool = True,
        dry_run: bool = False,
        progress_callback: Callable[[str], None] | None = None,
    ) -> ButlerPushResult:
        """Push a game build to itch.io.

        Args:
            directory: Directory containing the game build.
            target: The itch.io target (username/game-name).
            channel: The release channel (e.g., "html5", "windows", "linux").
            version: Version string for this upload.
            fix_permissions: Whether to fix file permissions.
            dry_run: If True, validate but don't actually upload.
            progress_callback: Callback for progress updates.

        Returns:
            Result of the push operation.
        """
        if not directory.exists():
            return ButlerPushResult(
                success=False,
                target=target,
                channel=channel,
                error=f"Directory does not exist: {directory}",
            )

        if not directory.is_dir():
            return ButlerPushResult(
                success=False,
                target=target,
                channel=channel,
                error=f"Path is not a directory: {directory}",
            )

        # Build command
        cmd = [str(self.butler_path), "push"]

        if fix_permissions:
            cmd.append("--fix-permissions")

        if dry_run:
            cmd.append("--dry-run")

        if version:
            cmd.extend(["--userversion", version])

        # Add directory and target:channel
        cmd.append(str(directory))
        cmd.append(f"{target}:{channel}")

        logger.info("Running butler push: %s", " ".join(cmd))

        try:
            # Run with streaming output
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            output_lines: list[str] = []
            build_id = None

            if process.stdout:
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    line_str = line.decode("utf-8", errors="replace").strip()
                    output_lines.append(line_str)
                    logger.debug("butler: %s", line_str)

                    if progress_callback:
                        progress_callback(line_str)

                    # Try to extract build ID from output
                    if "Build ID" in line_str:
                        match = re.search(r"Build ID:\s*(\d+)", line_str)
                        if match:
                            build_id = int(match.group(1))

            await process.wait()
            output = "\n".join(output_lines)

            if process.returncode == 0:
                return ButlerPushResult(
                    success=True,
                    target=target,
                    channel=channel,
                    version=version,
                    build_id=build_id,
                    output=output,
                )
            else:
                return ButlerPushResult(
                    success=False,
                    target=target,
                    channel=channel,
                    version=version,
                    error=f"butler push failed with exit code {process.returncode}",
                    output=output,
                )

        except TimeoutError:
            return ButlerPushResult(
                success=False,
                target=target,
                channel=channel,
                version=version,
                error="butler push timed out",
            )
        except Exception as e:
            return ButlerPushResult(
                success=False,
                target=target,
                channel=channel,
                version=version,
                error=str(e),
            )

    async def status(self, target: str) -> ButlerStatusResult:
        """Get the status of an itch.io game.

        Args:
            target: The itch.io target (username/game-name).

        Returns:
            Status information for the game.
        """
        cmd = [str(self.butler_path), "status", target]

        logger.info("Running butler status: %s", " ".join(cmd))

        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                ),
            )

            if result.returncode != 0:
                return ButlerStatusResult(
                    success=False,
                    target=target,
                    error=result.stderr
                    or f"butler status failed with exit code {result.returncode}",
                    output=result.stdout,
                )

            # Parse the output to extract channel information
            channels: dict[str, dict[str, object]] = {}
            current_channel = None

            for line in result.stdout.split("\n"):
                line = line.strip()
                if not line:
                    continue

                # Channel header: "Channel: html5"
                if line.startswith("Channel:"):
                    current_channel = line.split(":", 1)[1].strip()
                    channels[current_channel] = {}
                elif current_channel and ":" in line:
                    key, value = line.split(":", 1)
                    channels[current_channel][key.strip().lower().replace(" ", "_")] = value.strip()

            return ButlerStatusResult(
                success=True,
                target=target,
                channels=channels,
                output=result.stdout,
            )

        except TimeoutError:
            return ButlerStatusResult(
                success=False,
                target=target,
                error="butler status timed out",
            )
        except Exception as e:
            return ButlerStatusResult(
                success=False,
                target=target,
                error=str(e),
            )

    async def fetch(
        self,
        target: str,
        output_dir: Path,
        *,
        channel: str | None = None,
    ) -> bool:
        """Fetch a game build from itch.io.

        Args:
            target: The itch.io target (username/game-name).
            output_dir: Directory to download to.
            channel: Specific channel to fetch (optional).

        Returns:
            True if fetch was successful.
        """
        cmd = [str(self.butler_path), "fetch"]

        fetch_target = target
        if channel:
            fetch_target = f"{target}:{channel}"

        cmd.extend([fetch_target, str(output_dir)])

        logger.info("Running butler fetch: %s", " ".join(cmd))

        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                ),
            )
            return result.returncode == 0

        except (TimeoutError, subprocess.SubprocessError):
            return False

    async def validate(self, directory: Path) -> tuple[bool, str]:
        """Validate a game directory.

        Args:
            directory: Directory to validate.

        Returns:
            Tuple of (is_valid, message).
        """
        if not directory.exists():
            return False, f"Directory does not exist: {directory}"

        if not directory.is_dir():
            return False, f"Path is not a directory: {directory}"

        # Check for common game files
        has_index = (directory / "index.html").exists()
        has_any_files = any(directory.iterdir())

        if not has_any_files:
            return False, "Directory is empty"

        # For HTML5 games, check for index.html
        if has_index:
            return True, "Valid HTML5 game (index.html found)"

        # Check for other common patterns
        return True, "Directory contains files"
