"""Build agent for game implementation.

This agent invokes Claude Code as a subprocess to implement games
based on the Game Design Document.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any

from game_workflow.agents.base import BaseAgent
from game_workflow.orchestrator.exceptions import AgentError, BuildFailedError
from game_workflow.utils.subprocess import (
    ClaudeCodeRunner,
    ProcessResult,
    find_claude_executable,
    find_executable,
    run_npm_command,
)

if TYPE_CHECKING:
    from game_workflow.agents.schemas import (
        DesignOutput,
        GameDesignDocument,
        TechnicalSpecification,
    )


# Default scaffold directory (relative to package)
SCAFFOLDS_DIR = Path(__file__).parent.parent.parent.parent / "templates" / "scaffolds"

# Default timeout for Claude Code (30 minutes)
DEFAULT_TIMEOUT_SECONDS = 1800

# Default timeout for npm operations (10 minutes)
NPM_TIMEOUT_SECONDS = 600


class BuildAgent(BaseAgent):
    """Agent for building games using Claude Code.

    This agent takes a GDD and invokes Claude Code to implement
    the game according to the specification. The workflow is:

    1. Copy the scaffold to the output directory
    2. Install dependencies (npm install)
    3. Create a build prompt from the GDD and tech spec
    4. Invoke Claude Code to implement the game
    5. Build the game (npm run build)
    6. Verify the build output

    Attributes:
        scaffolds_dir: Directory containing scaffold templates.
        timeout_seconds: Timeout for Claude Code execution.
    """

    def __init__(
        self,
        scaffolds_dir: Path | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        **kwargs: Any,
    ) -> None:
        """Initialize the BuildAgent.

        Args:
            scaffolds_dir: Directory containing scaffold templates.
            timeout_seconds: Timeout for Claude Code execution.
            **kwargs: Arguments passed to BaseAgent.
        """
        super().__init__(**kwargs)
        self.scaffolds_dir = scaffolds_dir or SCAFFOLDS_DIR
        self.timeout_seconds = timeout_seconds
        self._npm_logs: list[str] = []

    @property
    def name(self) -> str:
        """Get the agent's name."""
        return "BuildAgent"

    async def run(
        self,
        gdd_path: Path | None = None,
        output_dir: Path | None = None,
        engine: str = "phaser",
        design_output: DesignOutput | None = None,
        tech_spec: TechnicalSpecification | None = None,
        gdd: GameDesignDocument | None = None,
        skip_npm_install: bool = False,
        skip_build: bool = False,
        **kwargs: Any,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Build a game from a GDD.

        You can provide input in one of two ways:
        1. Pass a gdd_path pointing to a JSON file containing DesignOutput
        2. Pass design_output, gdd, or tech_spec objects directly

        Args:
            gdd_path: Path to the Game Design Document JSON file.
            output_dir: Directory for the built game.
            engine: The game engine to use ("phaser" or "godot").
            design_output: DesignOutput object from DesignAgent.
            tech_spec: TechnicalSpecification object (if not using design_output).
            gdd: GameDesignDocument object (if not using design_output).
            skip_npm_install: Skip npm install step (for testing).
            skip_build: Skip final build step (for testing).
            **kwargs: Additional arguments.

        Returns:
            Dict containing build results and artifact paths:
                - status: "success" or "failed"
                - output_dir: Path to the built game directory
                - build_dir: Path to the build output (dist/)
                - claude_code_output: Output from Claude Code
                - npm_build_output: Output from npm build

        Raises:
            AgentError: If required inputs are missing.
            BuildFailedError: If the build fails.
        """
        # Validate inputs
        if output_dir is None:
            raise AgentError(self.name, "output_dir is required")

        output_dir = Path(output_dir)

        # Load design data from file or use provided objects
        gdd_data, tech_spec_data = await self._load_design_data(
            gdd_path=gdd_path,
            design_output=design_output,
            tech_spec=tech_spec,
            gdd=gdd,
        )

        # Ensure engine matches
        if tech_spec_data:
            engine = tech_spec_data.get("engine", engine)
            if isinstance(engine, str) and engine.startswith("GameEngine."):
                engine = engine.split(".")[-1].lower()

        self.log_info(f"Building game with engine: {engine}")

        # Step 1: Copy scaffold
        self.log_info("Copying scaffold to output directory")
        await self._copy_scaffold(engine, output_dir)

        # Step 2: Install dependencies
        if not skip_npm_install:
            self.log_info("Installing dependencies")
            await self._install_dependencies(output_dir)
        else:
            self.log_debug("Skipping npm install")

        # Step 3: Generate build prompt
        self.log_info("Generating build prompt")
        build_prompt = self._generate_build_prompt(gdd_data, tech_spec_data)

        # Step 4: Invoke Claude Code
        self.log_info("Invoking Claude Code")
        claude_result = await self._invoke_claude_code(
            output_dir,
            build_prompt,
            gdd_path,
        )

        if not claude_result.success:
            raise BuildFailedError(
                "Claude Code execution failed",
                build_output=claude_result.stdout + "\n" + claude_result.stderr,
            )

        # Step 5: Build the game
        build_output = ""
        if not skip_build:
            self.log_info("Building game")
            build_result = await self._build_game(output_dir)
            build_output = build_result.stdout
            if not build_result.success:
                raise BuildFailedError(
                    "npm build failed",
                    build_output=build_result.stdout + "\n" + build_result.stderr,
                )
        else:
            self.log_debug("Skipping npm build")

        # Step 6: Verify build output
        build_dir = output_dir / "dist"
        if not skip_build and not build_dir.exists():
            raise BuildFailedError(
                "Build directory not created",
                build_output=build_output,
            )

        # Add artifacts to state
        self.add_artifact("game_source", str(output_dir))
        if build_dir.exists():
            self.add_artifact("game_build", str(build_dir))

        self.log_info("Build completed successfully")

        return {
            "status": "success",
            "output_dir": str(output_dir),
            "build_dir": str(build_dir) if build_dir.exists() else None,
            "claude_code_output": claude_result.stdout,
            "npm_build_output": build_output,
        }

    async def _load_design_data(
        self,
        gdd_path: Path | None,
        design_output: DesignOutput | None,
        tech_spec: TechnicalSpecification | None,
        gdd: GameDesignDocument | None,
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        """Load design data from file or objects.

        Args:
            gdd_path: Path to JSON file.
            design_output: DesignOutput object.
            tech_spec: TechnicalSpecification object.
            gdd: GameDesignDocument object.

        Returns:
            Tuple of (gdd_dict, tech_spec_dict or None).

        Raises:
            AgentError: If no valid input is provided.
        """
        gdd_data: dict[str, Any] = {}
        tech_spec_data: dict[str, Any] | None = None

        # Try to load from DesignOutput object
        if design_output is not None:
            gdd_data = design_output.gdd.model_dump()
            tech_spec_data = design_output.tech_spec.model_dump()
            return gdd_data, tech_spec_data

        # Try to load from individual objects
        if gdd is not None:
            gdd_data = gdd.model_dump()
        if tech_spec is not None:
            tech_spec_data = tech_spec.model_dump()

        # Try to load from file
        if gdd_path is not None and gdd_path.exists():
            try:
                with gdd_path.open() as f:
                    data = json.load(f)

                # Check if it's a DesignOutput structure
                if "gdd" in data and "tech_spec" in data:
                    gdd_data = data["gdd"]
                    tech_spec_data = data["tech_spec"]
                elif "title" in data and "core_mechanics" in data:
                    # It's a raw GDD
                    gdd_data = data
                else:
                    raise AgentError(self.name, f"Unknown JSON structure in {gdd_path}")

            except json.JSONDecodeError as e:
                raise AgentError(self.name, f"Invalid JSON in {gdd_path}: {e}") from e

        # Validate we have at least GDD data
        if not gdd_data:
            raise AgentError(
                self.name,
                "No GDD data provided. Pass gdd_path, design_output, or gdd parameter.",
            )

        return gdd_data, tech_spec_data

    async def _copy_scaffold(self, engine: str, output_dir: Path) -> None:
        """Copy the scaffold template to the output directory.

        Args:
            engine: The game engine ("phaser" or "godot").
            output_dir: The destination directory.

        Raises:
            AgentError: If the scaffold doesn't exist.
        """
        scaffold_dir = self.scaffolds_dir / engine

        if not scaffold_dir.exists():
            raise AgentError(
                self.name,
                f"Scaffold not found for engine '{engine}' at {scaffold_dir}",
            )

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Copy scaffold contents (excluding .gitkeep files)
        for item in scaffold_dir.iterdir():
            if item.name == ".gitkeep":
                continue

            dest = output_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)

        self.log_debug(f"Copied scaffold from {scaffold_dir} to {output_dir}")

    async def _install_dependencies(self, project_dir: Path) -> ProcessResult:
        """Install npm dependencies.

        Args:
            project_dir: The project directory.

        Returns:
            ProcessResult from npm install.

        Raises:
            BuildFailedError: If npm install fails.
        """
        # Check npm is available
        if find_executable("npm") is None:
            raise BuildFailedError(
                "npm not found. Please install Node.js.",
                build_output=None,
            )

        self._npm_logs = []

        def log_output(line: str, is_error: bool) -> None:
            self._npm_logs.append(line)
            if is_error:
                self.log_debug(f"npm stderr: {line}")
            else:
                self.log_debug(f"npm: {line}")

        result = await run_npm_command(
            ["install"],
            cwd=project_dir,
            timeout_seconds=NPM_TIMEOUT_SECONDS,
            output_callback=log_output,
        )

        if not result.success:
            raise BuildFailedError(
                "npm install failed",
                build_output=result.stdout + "\n" + result.stderr,
            )

        return result

    def _generate_build_prompt(
        self,
        gdd_data: dict[str, Any],
        tech_spec_data: dict[str, Any] | None,
    ) -> str:
        """Generate a prompt for Claude Code.

        Args:
            gdd_data: The Game Design Document data.
            tech_spec_data: The Technical Specification data (optional).

        Returns:
            A prompt string for Claude Code.
        """
        # Extract key information
        title = gdd_data.get("title", "Game")
        genre = gdd_data.get("genre", "")
        concept = gdd_data.get("concept_summary", "")
        core_mechanics = gdd_data.get("core_mechanics", [])
        player_actions = gdd_data.get("player_actions", [])
        levels = gdd_data.get("levels", [])
        visual_style = gdd_data.get("visual_style", "")
        win_condition = gdd_data.get("win_condition", "")
        loss_condition = gdd_data.get("loss_condition", "")

        # Build mechanics description
        mechanics_desc = ""
        for mech in core_mechanics:
            name = mech.get("name", "")
            desc = mech.get("description", "")
            controls = mech.get("controls", "")
            mechanics_desc += f"- **{name}**: {desc}"
            if controls:
                mechanics_desc += f" (Controls: {controls})"
            mechanics_desc += "\n"

        # Build actions description
        actions_desc = ""
        for action in player_actions:
            name = action.get("name", "")
            desc = action.get("description", "")
            actions_desc += f"- **{name}**: {desc}\n"

        # Build levels description
        levels_desc = ""
        for level in levels:
            name = level.get("name", "")
            desc = level.get("description", "")
            objectives = level.get("objectives", "")
            levels_desc += f"- **{name}**: {desc} (Objectives: {objectives})\n"

        # Implementation order from tech spec
        impl_order = ""
        if tech_spec_data:
            order = tech_spec_data.get("implementation_order", [])
            if order:
                impl_order = "\n\n## Implementation Order\n"
                for i, step in enumerate(order, 1):
                    impl_order += f"{i}. {step}\n"

        prompt = f"""# Game Implementation Task

Implement the game "{title}" based on the following Game Design Document.

## Overview
- **Genre**: {genre}
- **Concept**: {concept}
- **Visual Style**: {visual_style}

## Core Mechanics
{mechanics_desc}

## Player Actions
{actions_desc}

## Win/Loss Conditions
- **Win**: {win_condition}
- **Lose**: {loss_condition}

## Levels/Environments
{levels_desc}
{impl_order}

## Instructions

1. This is a Phaser.js project. The scaffold is already set up with scenes in `src/scenes/`.
2. Implement the game logic in `src/scenes/GameScene.js`.
3. Add any additional scenes or game objects as needed in `src/scenes/` and `src/objects/`.
4. Use simple geometric shapes (rectangles, circles) for visual placeholders.
5. Do NOT require any external assets - the game should work with programmatic graphics.
6. Ensure the game is playable with keyboard controls.
7. Test your implementation by running `npm run dev` and verifying the game works.
8. Commit your changes with clear commit messages.

## Quality Checklist

Before finishing, verify:
- [ ] Game loads without errors
- [ ] Core mechanics are implemented
- [ ] Win and loss conditions work
- [ ] Controls are responsive
- [ ] No console errors

Start implementing the game now. Focus on getting the core gameplay loop working first."""

        return prompt

    async def _invoke_claude_code(
        self,
        project_dir: Path,
        prompt: str,
        gdd_path: Path | None = None,
    ) -> ProcessResult:
        """Invoke Claude Code to implement the game.

        Args:
            project_dir: The project directory.
            prompt: The build prompt.
            gdd_path: Optional path to GDD file for context.

        Returns:
            ProcessResult from Claude Code.

        Raises:
            BuildFailedError: If Claude Code is not available.
        """
        # Check claude is available
        if find_claude_executable() is None:
            raise BuildFailedError(
                "Claude Code not found. Please install it from https://claude.ai/code",
                build_output=None,
            )

        runner = ClaudeCodeRunner(
            working_dir=project_dir,
            timeout_seconds=self.timeout_seconds,
        )

        # Add GDD file as context if available
        context_files = []
        if gdd_path and gdd_path.exists():
            context_files.append(gdd_path)

        # Also add the skill file as context
        skill_file = self.scaffolds_dir.parent.parent / "skills" / "phaser-game" / "SKILL.md"
        if skill_file.exists():
            context_files.append(skill_file)

        result = await runner.run(
            prompt=prompt,
            context_files=context_files if context_files else None,
            allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
        )

        return result

    async def _build_game(self, project_dir: Path) -> ProcessResult:
        """Run npm build to create the distributable.

        Args:
            project_dir: The project directory.

        Returns:
            ProcessResult from npm build.
        """
        self._npm_logs = []

        def log_output(line: str, is_error: bool) -> None:
            self._npm_logs.append(line)
            if is_error:
                self.log_debug(f"npm build stderr: {line}")
            else:
                self.log_debug(f"npm build: {line}")

        result = await run_npm_command(
            ["run", "build"],
            cwd=project_dir,
            timeout_seconds=NPM_TIMEOUT_SECONDS,
            output_callback=log_output,
        )

        return result

    def get_scaffold_engines(self) -> list[str]:
        """Get list of available scaffold engines.

        Returns:
            List of engine names with available scaffolds.
        """
        if not self.scaffolds_dir.exists():
            return []

        return [
            d.name
            for d in self.scaffolds_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]
