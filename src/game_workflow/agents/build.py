"""Build agent for game implementation.

This agent invokes Claude Code as a subprocess to implement games
based on the Game Design Document.
"""

from pathlib import Path
from typing import Any

from game_workflow.agents.base import BaseAgent


class BuildAgent(BaseAgent):
    """Agent for building games using Claude Code.

    This agent takes a GDD and invokes Claude Code to implement
    the game according to the specification.
    """

    @property
    def name(self) -> str:
        """Get the agent's name."""
        return "BuildAgent"

    async def run(
        self,
        gdd_path: Path,
        output_dir: Path,
        engine: str = "phaser",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Build a game from a GDD.

        Args:
            gdd_path: Path to the Game Design Document.
            output_dir: Directory for the built game.
            engine: The game engine to use.
            **kwargs: Additional arguments.

        Returns:
            Dict containing build results and artifact paths.
        """
        # TODO: Implement Claude Code invocation
        raise NotImplementedError("Game building not yet implemented")
