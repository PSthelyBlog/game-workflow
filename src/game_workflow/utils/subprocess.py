"""Subprocess management utilities.

This module provides async subprocess execution with proper output handling,
timeout management, and streaming capabilities.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("game_workflow.utils.subprocess")


@dataclass
class ProcessResult:
    """Result of a subprocess execution.

    Attributes:
        return_code: The process exit code.
        stdout: Standard output (if captured).
        stderr: Standard error (if captured).
        timed_out: Whether the process was killed due to timeout.
        duration_seconds: How long the process ran.
    """

    return_code: int
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    duration_seconds: float = 0.0

    @property
    def success(self) -> bool:
        """Check if the process completed successfully."""
        return self.return_code == 0 and not self.timed_out


@dataclass
class SubprocessConfig:
    """Configuration for subprocess execution.

    Attributes:
        timeout_seconds: Maximum time to wait (None for no timeout).
        cwd: Working directory for the process.
        env: Environment variables (merged with current env).
        capture_output: Whether to capture stdout/stderr.
        stream_output: Whether to stream output to a callback.
        output_callback: Function to call with each line of output.
    """

    timeout_seconds: float | None = None
    cwd: Path | None = None
    env: dict[str, str] = field(default_factory=dict)
    capture_output: bool = True
    stream_output: bool = False
    output_callback: Any | None = None


async def run_subprocess(
    command: list[str],
    config: SubprocessConfig | None = None,
) -> ProcessResult:
    """Run a subprocess asynchronously.

    Args:
        command: The command and arguments to run.
        config: Configuration for the subprocess.

    Returns:
        ProcessResult with output and status.

    Raises:
        FileNotFoundError: If the command is not found.
        OSError: If there's an OS-level error running the process.
    """
    if config is None:
        config = SubprocessConfig()

    import os
    import time

    # Merge environment
    env = os.environ.copy()
    env.update(config.env)

    start_time = time.monotonic()

    # Create the process
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE if config.capture_output else None,
        stderr=asyncio.subprocess.PIPE if config.capture_output else None,
        cwd=config.cwd,
        env=env,
    )

    stdout_data = ""
    stderr_data = ""
    timed_out = False

    try:
        if config.stream_output and config.capture_output:
            # Stream output while capturing
            stdout_task = asyncio.create_task(_read_stream(process.stdout, config.output_callback))
            stderr_task = asyncio.create_task(
                _read_stream(process.stderr, config.output_callback, is_error=True)
            )

            try:
                stdout_data, stderr_data = await asyncio.wait_for(
                    asyncio.gather(stdout_task, stderr_task),
                    timeout=config.timeout_seconds,
                )
                await process.wait()
            except TimeoutError:
                timed_out = True
                process.kill()
                await process.wait()
        else:
            # Standard capture
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=config.timeout_seconds,
                )
                stdout_data = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
                stderr_data = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""
            except TimeoutError:
                timed_out = True
                process.kill()
                await process.wait()

    except Exception as e:
        logger.error(f"Subprocess error: {e}")
        process.kill()
        await process.wait()
        raise

    duration = time.monotonic() - start_time

    return ProcessResult(
        return_code=process.returncode if process.returncode is not None else -1,
        stdout=stdout_data,
        stderr=stderr_data,
        timed_out=timed_out,
        duration_seconds=duration,
    )


async def _read_stream(
    stream: asyncio.StreamReader | None,
    callback: Any | None = None,
    is_error: bool = False,
) -> str:
    """Read a stream and optionally call a callback for each line.

    Args:
        stream: The async stream to read.
        callback: Optional callback(line, is_error) for each line.
        is_error: Whether this is stderr (passed to callback).

    Returns:
        The complete output as a string.
    """
    if stream is None:
        return ""

    lines: list[str] = []
    while True:
        line_bytes = await stream.readline()
        if not line_bytes:
            break
        line = line_bytes.decode("utf-8", errors="replace").rstrip("\n\r")
        lines.append(line)
        if callback is not None:
            try:
                callback(line, is_error)
            except Exception as e:
                logger.warning(f"Output callback error: {e}")

    return "\n".join(lines)


def find_executable(name: str) -> Path | None:
    """Find an executable in PATH.

    Args:
        name: The executable name.

    Returns:
        Path to the executable, or None if not found.
    """
    path = shutil.which(name)
    return Path(path) if path else None


async def run_npm_command(
    args: list[str],
    cwd: Path,
    timeout_seconds: float | None = 300,
    output_callback: Any | None = None,
) -> ProcessResult:
    """Run an npm command.

    Args:
        args: Arguments to pass to npm (e.g., ["install"]).
        cwd: Working directory (should contain package.json).
        timeout_seconds: Maximum time to wait.
        output_callback: Optional callback for streaming output.

    Returns:
        ProcessResult with output and status.

    Raises:
        FileNotFoundError: If npm is not found.
    """
    npm_path = find_executable("npm")
    if npm_path is None:
        raise FileNotFoundError("npm not found in PATH")

    command = [str(npm_path), *args]

    config = SubprocessConfig(
        timeout_seconds=timeout_seconds,
        cwd=cwd,
        capture_output=True,
        stream_output=output_callback is not None,
        output_callback=output_callback,
    )

    return await run_subprocess(command, config)


class ClaudeCodeRunner:
    """Runner for invoking Claude Code as a subprocess.

    This class manages the invocation of Claude Code for game implementation.
    """

    def __init__(
        self,
        working_dir: Path,
        timeout_seconds: float = 1800,  # 30 minutes default
    ) -> None:
        """Initialize the runner.

        Args:
            working_dir: The working directory for Claude Code.
            timeout_seconds: Maximum time to wait for completion.
        """
        self.working_dir = working_dir
        self.timeout_seconds = timeout_seconds
        self._output_lines: list[str] = []
        self._error_lines: list[str] = []
        self._logger = logging.getLogger("game_workflow.claude_code")

    def _output_callback(self, line: str, is_error: bool) -> None:
        """Handle output from Claude Code.

        Args:
            line: The output line.
            is_error: Whether this is from stderr.
        """
        if is_error:
            self._error_lines.append(line)
            self._logger.debug(f"stderr: {line}")
        else:
            self._output_lines.append(line)
            self._logger.info(f"claude-code: {line}")

    async def run(
        self,
        prompt: str,
        context_files: list[Path] | None = None,
        allowed_tools: list[str] | None = None,
    ) -> ProcessResult:
        """Run Claude Code with a prompt.

        Args:
            prompt: The prompt/task for Claude Code.
            context_files: Optional files to include as context (contents will be
                embedded in the prompt since Claude Code CLI doesn't support --add-file).
            allowed_tools: Optional list of allowed tools (e.g., ["Read", "Write", "Bash"]).

        Returns:
            ProcessResult with Claude Code output.

        Raises:
            FileNotFoundError: If claude executable is not found.
        """
        # Find claude executable
        claude_path = find_executable("claude")
        if claude_path is None:
            raise FileNotFoundError(
                "claude command not found. Please install Claude Code: https://claude.ai/code"
            )

        # Build the full prompt with context files embedded
        full_prompt = prompt

        # Embed context file contents in the prompt (Claude Code CLI doesn't have --add-file)
        if context_files:
            context_parts = []
            for context_file in context_files:
                if context_file.exists():
                    try:
                        content = context_file.read_text(encoding="utf-8")
                        context_parts.append(
                            f"\n\n--- Context from {context_file.name} ---\n{content}\n--- End {context_file.name} ---"
                        )
                    except Exception as e:
                        self._logger.warning(f"Could not read context file {context_file}: {e}")
            if context_parts:
                full_prompt = prompt + "\n".join(context_parts)

        # Build command
        command = [str(claude_path), "-p", full_prompt]

        # Add allowed tools if specified
        if allowed_tools:
            command.extend(["--allowedTools", ",".join(allowed_tools)])

        # Clear output buffers
        self._output_lines = []
        self._error_lines = []

        config = SubprocessConfig(
            timeout_seconds=self.timeout_seconds,
            cwd=self.working_dir,
            capture_output=True,
            stream_output=True,
            output_callback=self._output_callback,
        )

        self._logger.info(f"Running Claude Code in {self.working_dir}")
        self._logger.debug(f"Command: {' '.join(command)}")

        result = await run_subprocess(command, config)

        self._logger.info(
            f"Claude Code finished: return_code={result.return_code}, "
            f"timed_out={result.timed_out}, duration={result.duration_seconds:.1f}s"
        )

        return result

    @property
    def output(self) -> str:
        """Get the combined output from the last run."""
        return "\n".join(self._output_lines)

    @property
    def errors(self) -> str:
        """Get the error output from the last run."""
        return "\n".join(self._error_lines)
