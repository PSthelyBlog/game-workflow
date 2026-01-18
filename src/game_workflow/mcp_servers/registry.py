"""MCP server registry for managing server configurations and lifecycle.

This module provides a registry for MCP servers used by the workflow,
including lifecycle management (start, stop, health checks).
"""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""

    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    working_dir: str | None = None
    startup_timeout: float = 30.0
    health_check_interval: float = 10.0


@dataclass
class MCPServerProcess:
    """Represents a running MCP server process."""

    name: str
    config: MCPServerConfig
    process: subprocess.Popen[bytes] | None = None
    started_at: float | None = None
    healthy: bool = False

    @property
    def is_running(self) -> bool:
        """Check if the process is running."""
        if self.process is None:
            return False
        return self.process.poll() is None

    @property
    def pid(self) -> int | None:
        """Get the process ID if running."""
        if self.process is not None and self.is_running:
            return self.process.pid
        return None


class MCPServerRegistry:
    """Registry for MCP server configurations and lifecycle.

    Manages the configuration and lifecycle of MCP servers
    used by the workflow agents.

    Example:
        async with MCPServerRegistry() as registry:
            await registry.start_server("github")
            # Use the server...
            await registry.stop_server("github")
    """

    def __init__(self) -> None:
        """Initialize the registry with default servers."""
        self._servers: dict[str, MCPServerConfig] = {}
        self._processes: dict[str, MCPServerProcess] = {}
        self._health_check_tasks: dict[str, asyncio.Task[None]] = {}
        self._lock = asyncio.Lock()
        self._register_default_servers()

    def _register_default_servers(self) -> None:
        """Register the default MCP servers."""
        # GitHub MCP server
        github_token = os.environ.get("GITHUB_TOKEN", "")
        self._servers["github"] = MCPServerConfig(
            command="npx",
            args=["@anthropic/github-mcp"],
            env={"GITHUB_TOKEN": github_token},
        )

        # Slack MCP server
        slack_token = os.environ.get("SLACK_BOT_TOKEN", "")
        self._servers["slack"] = MCPServerConfig(
            command="npx",
            args=["@anthropic/slack-mcp"],
            env={"SLACK_BOT_TOKEN": slack_token},
        )

        # itch.io MCP server (custom)
        itchio_key = os.environ.get("ITCHIO_API_KEY", "")
        self._servers["itchio"] = MCPServerConfig(
            command="python",
            args=["-m", "game_workflow.mcp_servers.itchio.server"],
            env={"ITCHIO_API_KEY": itchio_key},
        )

    async def __aenter__(self) -> MCPServerRegistry:
        """Enter async context."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit async context, stopping all servers."""
        await self.stop_all()

    def get(self, name: str) -> MCPServerConfig | None:
        """Get a server configuration by name.

        Args:
            name: The server name.

        Returns:
            The server configuration, or None if not found.
        """
        return self._servers.get(name)

    def register(self, name: str, config: MCPServerConfig) -> None:
        """Register a new server configuration.

        Args:
            name: The server name.
            config: The server configuration.
        """
        self._servers[name] = config

    def unregister(self, name: str) -> bool:
        """Unregister a server configuration.

        Args:
            name: The server name.

        Returns:
            True if the server was unregistered, False if not found.
        """
        if name in self._servers:
            # Stop if running
            if name in self._processes:
                # Store the task reference to prevent garbage collection
                task = asyncio.create_task(self.stop_server(name))
                task.add_done_callback(lambda t: None)  # noqa: ARG005
            del self._servers[name]
            return True
        return False

    def list_servers(self) -> list[str]:
        """List all registered server names.

        Returns:
            List of server names.
        """
        return list(self._servers.keys())

    def list_running(self) -> list[str]:
        """List all running server names.

        Returns:
            List of running server names.
        """
        return [
            name for name, proc in self._processes.items()
            if proc.is_running
        ]

    def is_running(self, name: str) -> bool:
        """Check if a server is running.

        Args:
            name: The server name.

        Returns:
            True if the server is running.
        """
        proc = self._processes.get(name)
        return proc is not None and proc.is_running

    def is_healthy(self, name: str) -> bool:
        """Check if a server is healthy.

        Args:
            name: The server name.

        Returns:
            True if the server is running and healthy.
        """
        proc = self._processes.get(name)
        return proc is not None and proc.is_running and proc.healthy

    def get_process(self, name: str) -> MCPServerProcess | None:
        """Get the process info for a server.

        Args:
            name: The server name.

        Returns:
            The server process info, or None if not running.
        """
        return self._processes.get(name)

    async def start_server(
        self,
        name: str,
        *,
        wait_healthy: bool = True,
        timeout: float | None = None,
    ) -> MCPServerProcess:
        """Start an MCP server.

        Args:
            name: The server name.
            wait_healthy: Whether to wait for health check.
            timeout: Timeout for startup (uses config default if None).

        Returns:
            The server process info.

        Raises:
            ValueError: If the server is not registered.
            RuntimeError: If the server fails to start.
        """
        config = self._servers.get(name)
        if config is None:
            raise ValueError(f"Server '{name}' is not registered")

        async with self._lock:
            # Check if already running
            if name in self._processes and self._processes[name].is_running:
                logger.info("Server '%s' is already running", name)
                return self._processes[name]

            # Build environment
            env = os.environ.copy()
            env.update(config.env)

            # Build command
            cmd = [config.command, *config.args]

            logger.info("Starting MCP server '%s': %s", name, " ".join(cmd))

            try:
                import time

                process = subprocess.Popen(
                    cmd,
                    env=env,
                    cwd=config.working_dir,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

                proc_info = MCPServerProcess(
                    name=name,
                    config=config,
                    process=process,
                    started_at=time.time(),
                    healthy=False,
                )

                self._processes[name] = proc_info

                # Wait for process to stabilize
                await asyncio.sleep(0.1)

                if not proc_info.is_running:
                    # Process exited immediately
                    stderr = ""
                    if process.stderr:
                        stderr = process.stderr.read().decode("utf-8", errors="replace")
                    raise RuntimeError(
                        f"Server '{name}' exited immediately: {stderr}"
                    )

                if wait_healthy:
                    startup_timeout = timeout or config.startup_timeout
                    await self._wait_healthy(name, timeout=startup_timeout)

                # Start health check task
                self._start_health_check(name)

                logger.info("Server '%s' started successfully (PID: %s)", name, proc_info.pid)
                return proc_info

            except Exception as e:
                # Clean up on failure
                if name in self._processes:
                    del self._processes[name]
                raise RuntimeError(f"Failed to start server '{name}': {e}") from e

    async def stop_server(self, name: str, *, timeout: float = 10.0) -> bool:
        """Stop an MCP server.

        Args:
            name: The server name.
            timeout: Timeout for graceful shutdown.

        Returns:
            True if the server was stopped, False if not running.
        """
        async with self._lock:
            proc_info = self._processes.get(name)
            if proc_info is None or not proc_info.is_running:
                logger.debug("Server '%s' is not running", name)
                if name in self._processes:
                    del self._processes[name]
                return False

            # Cancel health check
            self._stop_health_check(name)

            process = proc_info.process
            if process is None:
                return False

            logger.info("Stopping MCP server '%s' (PID: %s)", name, process.pid)

            try:
                # Try graceful shutdown first
                process.terminate()

                # Wait for graceful shutdown
                try:
                    await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None, process.wait
                        ),
                        timeout=timeout,
                    )
                except TimeoutError:
                    # Force kill
                    logger.warning("Server '%s' did not stop gracefully, killing", name)
                    process.kill()
                    process.wait()

                logger.info("Server '%s' stopped", name)
                del self._processes[name]
                return True

            except Exception as e:
                logger.error("Error stopping server '%s': %s", name, e)
                if name in self._processes:
                    del self._processes[name]
                return False

    async def restart_server(
        self,
        name: str,
        *,
        stop_timeout: float = 10.0,
        wait_healthy: bool = True,
        start_timeout: float | None = None,
    ) -> MCPServerProcess:
        """Restart an MCP server.

        Args:
            name: The server name.
            stop_timeout: Timeout for stopping.
            wait_healthy: Whether to wait for health check.
            start_timeout: Timeout for startup.

        Returns:
            The new server process info.
        """
        await self.stop_server(name, timeout=stop_timeout)
        return await self.start_server(
            name, wait_healthy=wait_healthy, timeout=start_timeout
        )

    async def stop_all(self, *, timeout: float = 10.0) -> None:
        """Stop all running servers.

        Args:
            timeout: Timeout for each server shutdown.
        """
        running = self.list_running()
        if not running:
            return

        logger.info("Stopping %d MCP servers", len(running))

        # Stop all servers concurrently
        await asyncio.gather(
            *[self.stop_server(name, timeout=timeout) for name in running],
            return_exceptions=True,
        )

    async def _wait_healthy(
        self,
        name: str,
        timeout: float = 30.0,  # noqa: ARG002
    ) -> None:
        """Wait for a server to become healthy.

        Args:
            name: The server name.
            timeout: Maximum time to wait (reserved for future health check logic).

        Raises:
            RuntimeError: If the server fails to become healthy.
        """
        proc_info = self._processes.get(name)
        if proc_info is None:
            raise RuntimeError(f"Server '{name}' is not running")

        # Check if process is still running
        if not proc_info.is_running:
            raise RuntimeError(f"Server '{name}' exited unexpectedly")

        # Simple health check: process is running
        # In a real implementation, you'd do an actual health check RPC
        proc_info.healthy = True

        # Future: implement actual health check loop with timeout
        # start_time = asyncio.get_event_loop().time()
        # while True:
        #     elapsed = asyncio.get_event_loop().time() - start_time
        #     if elapsed >= timeout:
            #     raise RuntimeError(f"Server '{name}' did not become healthy")
            # await asyncio.sleep(0.5)

    def _start_health_check(self, name: str) -> None:
        """Start periodic health check for a server.

        Args:
            name: The server name.
        """
        # Cancel existing task if any
        self._stop_health_check(name)

        config = self._servers.get(name)
        if config is None:
            return

        async def health_check_loop() -> None:
            while True:
                await asyncio.sleep(config.health_check_interval)
                proc_info = self._processes.get(name)
                if proc_info is None or not proc_info.is_running:
                    break
                # Simple health check: process is running
                proc_info.healthy = proc_info.is_running

        self._health_check_tasks[name] = asyncio.create_task(health_check_loop())

    def _stop_health_check(self, name: str) -> None:
        """Stop health check for a server.

        Args:
            name: The server name.
        """
        task = self._health_check_tasks.pop(name, None)
        if task is not None:
            task.cancel()

    def get_server_stats(self, name: str) -> dict[str, object] | None:
        """Get statistics for a server.

        Args:
            name: The server name.

        Returns:
            Dictionary with server stats, or None if not running.
        """
        import time

        proc_info = self._processes.get(name)
        if proc_info is None:
            return None

        uptime = None
        if proc_info.started_at is not None:
            uptime = time.time() - proc_info.started_at

        return {
            "name": name,
            "running": proc_info.is_running,
            "healthy": proc_info.healthy,
            "pid": proc_info.pid,
            "uptime_seconds": uptime,
            "config": {
                "command": proc_info.config.command,
                "args": proc_info.config.args,
            },
        }

    def get_all_stats(self) -> dict[str, dict[str, object] | None]:
        """Get statistics for all servers.

        Returns:
            Dictionary mapping server names to stats.
        """
        return {
            name: self.get_server_stats(name)
            for name in self._servers
        }
