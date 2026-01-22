"""Tests for the BuildAgent module."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest

from game_workflow.agents.build import SCAFFOLDS_DIR, BuildAgent
from game_workflow.agents.schemas import (
    ColorEntry,
    CoreMechanic,
    Dependency,
    FileStructure,
    GameDesignDocument,
    GameEngine,
    HUDElement,
    InspirationGame,
    Level,
    PlayerAction,
    SoundEffect,
    TechnicalSpecification,
)
from game_workflow.orchestrator.exceptions import AgentError, BuildFailedError
from game_workflow.utils.subprocess import ProcessResult

if TYPE_CHECKING:
    from pathlib import Path


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_gdd() -> GameDesignDocument:
    """Create a mock Game Design Document."""
    return GameDesignDocument(
        title="Test Game",
        concept_summary="A simple test game for unit testing.",
        genre="Puzzle",
        target_audience="Developers",
        unique_selling_points=["Easy to test", "Simple mechanics"],
        core_game_loop="Player solves puzzles to progress.",
        core_mechanics=[
            CoreMechanic(name="Click", description="Click on tiles to flip them"),
            CoreMechanic(name="Match", description="Match pairs to score points"),
        ],
        player_actions=[
            PlayerAction(name="Click", description="Click on a tile"),
            PlayerAction(name="Reset", description="Reset the game"),
        ],
        win_condition="Match all pairs",
        loss_condition="Run out of time",
        progression_system="Levels increase in difficulty",
        difficulty_curve="Linear increase in grid size",
        setting="Abstract puzzle world",
        narrative="No narrative",
        levels=[
            Level(name="Level 1", description="4x4 grid", objectives="Match 8 pairs"),
        ],
        visual_style="Minimalist",
        art_direction="Clean geometric shapes",
        color_palette=[
            ColorEntry(name="Primary", hex="#4A9FFF", usage="Main accent"),
            ColorEntry(name="Background", hex="#2D2D44", usage="Background"),
        ],
        audio_style="Simple",
        sound_effects=[
            SoundEffect(name="click", description="Tile click sound"),
        ],
        music_description="Calm background music",
        hud_elements=[
            HUDElement(name="Score", description="Current score"),
        ],
        menu_flow="Main Menu -> Game -> Game Over",
        ui_style_guide="Clean and minimal",
        mvp_features=["Basic gameplay", "Score tracking"],
        inspiration_games=[
            InspirationGame(name="Memory", relevance="Core mechanic"),
        ],
    )


@pytest.fixture
def mock_tech_spec() -> TechnicalSpecification:
    """Create a mock Technical Specification."""
    return TechnicalSpecification(
        project_name="test-game",
        engine=GameEngine.PHASER,
        file_structure=[
            FileStructure(path="src/main.js", purpose="Entry point"),
            FileStructure(path="src/scenes/GameScene.js", purpose="Main game"),
        ],
        dependencies=[
            Dependency(name="phaser", version="^3.80.0", purpose="Game engine"),
        ],
        scene_list=["BootScene", "PreloadScene", "MenuScene", "GameScene"],
        main_classes=["Player", "Tile"],
        implementation_order=["Set up project", "Implement core mechanics", "Add UI"],
    )


@pytest.fixture
def mock_process_result_success() -> ProcessResult:
    """Create a successful ProcessResult."""
    return ProcessResult(
        return_code=0,
        stdout="Build successful",
        stderr="",
        timed_out=False,
        duration_seconds=5.0,
    )


@pytest.fixture
def mock_process_result_failure() -> ProcessResult:
    """Create a failed ProcessResult."""
    return ProcessResult(
        return_code=1,
        stdout="",
        stderr="Build failed: error",
        timed_out=False,
        duration_seconds=2.0,
    )


@pytest.fixture
def scaffolds_dir(tmp_path: Path) -> Path:
    """Create a temporary scaffolds directory with test scaffold."""
    scaffold_dir = tmp_path / "scaffolds" / "phaser"
    scaffold_dir.mkdir(parents=True)

    # Create minimal scaffold files
    (scaffold_dir / "package.json").write_text(
        '{"name": "test", "scripts": {"build": "echo build"}}'
    )
    (scaffold_dir / "index.html").write_text("<html></html>")

    src_dir = scaffold_dir / "src"
    src_dir.mkdir()
    (src_dir / "main.js").write_text("// main")

    scenes_dir = src_dir / "scenes"
    scenes_dir.mkdir()
    (scenes_dir / "GameScene.js").write_text("// game scene")

    return tmp_path / "scaffolds"


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    """Create a temporary output directory."""
    out = tmp_path / "output"
    out.mkdir()
    return out


@pytest.fixture
def gdd_file(
    tmp_path: Path, mock_gdd: GameDesignDocument, mock_tech_spec: TechnicalSpecification
) -> Path:
    """Create a GDD JSON file."""
    gdd_path = tmp_path / "design_output.json"
    data = {
        "gdd": mock_gdd.model_dump(mode="json"),
        "tech_spec": mock_tech_spec.model_dump(mode="json"),
    }
    gdd_path.write_text(json.dumps(data))
    return gdd_path


# =============================================================================
# Basic Tests
# =============================================================================


class TestBuildAgentInit:
    """Tests for BuildAgent initialization."""

    def test_default_scaffolds_dir(self) -> None:
        """Test default scaffolds directory is set."""
        agent = BuildAgent()
        assert agent.scaffolds_dir == SCAFFOLDS_DIR

    def test_custom_scaffolds_dir(self, tmp_path: Path) -> None:
        """Test custom scaffolds directory."""
        agent = BuildAgent(scaffolds_dir=tmp_path)
        assert agent.scaffolds_dir == tmp_path

    def test_default_timeout(self) -> None:
        """Test default timeout is 30 minutes."""
        agent = BuildAgent()
        assert agent.timeout_seconds == 1800

    def test_custom_timeout(self) -> None:
        """Test custom timeout."""
        agent = BuildAgent(timeout_seconds=600)
        assert agent.timeout_seconds == 600

    def test_name(self) -> None:
        """Test agent name."""
        agent = BuildAgent()
        assert agent.name == "BuildAgent"


class TestGetScaffoldEngines:
    """Tests for get_scaffold_engines method."""

    def test_returns_engine_list(self, scaffolds_dir: Path) -> None:
        """Test returns list of available engines."""
        agent = BuildAgent(scaffolds_dir=scaffolds_dir)
        engines = agent.get_scaffold_engines()
        assert "phaser" in engines

    def test_empty_when_no_scaffolds(self, tmp_path: Path) -> None:
        """Test returns empty list when no scaffolds."""
        agent = BuildAgent(scaffolds_dir=tmp_path / "nonexistent")
        engines = agent.get_scaffold_engines()
        assert engines == []


# =============================================================================
# Scaffold Copy Tests
# =============================================================================


class TestCopyScaffold:
    """Tests for _copy_scaffold method."""

    @pytest.mark.asyncio
    async def test_copies_scaffold(self, scaffolds_dir: Path, output_dir: Path) -> None:
        """Test scaffold files are copied."""
        agent = BuildAgent(scaffolds_dir=scaffolds_dir)
        await agent._copy_scaffold("phaser", output_dir)

        assert (output_dir / "package.json").exists()
        assert (output_dir / "index.html").exists()
        assert (output_dir / "src" / "main.js").exists()
        assert (output_dir / "src" / "scenes" / "GameScene.js").exists()

    @pytest.mark.asyncio
    async def test_missing_scaffold_raises(self, tmp_path: Path, output_dir: Path) -> None:
        """Test error when scaffold doesn't exist."""
        agent = BuildAgent(scaffolds_dir=tmp_path)
        with pytest.raises(AgentError, match="Scaffold not found"):
            await agent._copy_scaffold("nonexistent", output_dir)

    @pytest.mark.asyncio
    async def test_creates_output_dir(self, scaffolds_dir: Path, tmp_path: Path) -> None:
        """Test output directory is created if missing."""
        agent = BuildAgent(scaffolds_dir=scaffolds_dir)
        new_output = tmp_path / "new" / "nested" / "dir"
        await agent._copy_scaffold("phaser", new_output)
        assert new_output.exists()


# =============================================================================
# Design Data Loading Tests
# =============================================================================


class TestLoadDesignData:
    """Tests for _load_design_data method."""

    @pytest.mark.asyncio
    async def test_load_from_file(self, gdd_file: Path) -> None:
        """Test loading from JSON file."""
        agent = BuildAgent()
        gdd_data, tech_spec_data = await agent._load_design_data(
            gdd_path=gdd_file,
            design_output=None,
            tech_spec=None,
            gdd=None,
        )

        assert gdd_data["title"] == "Test Game"
        assert tech_spec_data is not None
        assert tech_spec_data["project_name"] == "test-game"

    @pytest.mark.asyncio
    async def test_load_from_objects(
        self, mock_gdd: GameDesignDocument, mock_tech_spec: TechnicalSpecification
    ) -> None:
        """Test loading from Pydantic objects."""
        agent = BuildAgent()
        gdd_data, tech_spec_data = await agent._load_design_data(
            gdd_path=None,
            design_output=None,
            tech_spec=mock_tech_spec,
            gdd=mock_gdd,
        )

        assert gdd_data["title"] == "Test Game"
        assert tech_spec_data is not None

    @pytest.mark.asyncio
    async def test_no_data_raises(self) -> None:
        """Test error when no data provided."""
        agent = BuildAgent()
        with pytest.raises(AgentError, match="No GDD data"):
            await agent._load_design_data(
                gdd_path=None,
                design_output=None,
                tech_spec=None,
                gdd=None,
            )

    @pytest.mark.asyncio
    async def test_invalid_json_raises(self, tmp_path: Path) -> None:
        """Test error with invalid JSON file."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not valid json")

        agent = BuildAgent()
        with pytest.raises(AgentError, match="Invalid JSON"):
            await agent._load_design_data(
                gdd_path=bad_file,
                design_output=None,
                tech_spec=None,
                gdd=None,
            )


# =============================================================================
# Build Prompt Generation Tests
# =============================================================================


class TestGenerateBuildPrompt:
    """Tests for _generate_build_prompt method."""

    def test_includes_title(self, mock_gdd: GameDesignDocument) -> None:
        """Test prompt includes game title."""
        agent = BuildAgent()
        prompt = agent._generate_build_prompt(mock_gdd.model_dump(), None)
        assert "Test Game" in prompt

    def test_includes_mechanics(self, mock_gdd: GameDesignDocument) -> None:
        """Test prompt includes core mechanics."""
        agent = BuildAgent()
        prompt = agent._generate_build_prompt(mock_gdd.model_dump(), None)
        assert "Click" in prompt
        assert "Match" in prompt

    def test_includes_win_loss(self, mock_gdd: GameDesignDocument) -> None:
        """Test prompt includes win/loss conditions."""
        agent = BuildAgent()
        prompt = agent._generate_build_prompt(mock_gdd.model_dump(), None)
        assert "Match all pairs" in prompt
        assert "Run out of time" in prompt

    def test_includes_implementation_order(
        self, mock_gdd: GameDesignDocument, mock_tech_spec: TechnicalSpecification
    ) -> None:
        """Test prompt includes implementation order from tech spec."""
        agent = BuildAgent()
        prompt = agent._generate_build_prompt(mock_gdd.model_dump(), mock_tech_spec.model_dump())
        assert "Implementation Order" in prompt
        assert "Set up project" in prompt


# =============================================================================
# Integration Tests (with mocks)
# =============================================================================


class TestBuildAgentRun:
    """Integration tests for the run method."""

    @pytest.mark.asyncio
    async def test_missing_output_dir_raises(self, mock_gdd: GameDesignDocument) -> None:
        """Test error when output_dir not provided."""
        agent = BuildAgent()
        with pytest.raises(AgentError, match="output_dir is required"):
            await agent.run(gdd=mock_gdd, output_dir=None)

    @pytest.mark.asyncio
    async def test_copies_scaffold_on_run(
        self,
        scaffolds_dir: Path,
        output_dir: Path,
        mock_gdd: GameDesignDocument,
    ) -> None:
        """Test scaffold is copied during run."""
        agent = BuildAgent(scaffolds_dir=scaffolds_dir)

        # Mock the subprocess calls
        with (
            patch.object(agent, "_install_dependencies", new_callable=AsyncMock) as mock_install,
            patch.object(agent, "_invoke_claude_code", new_callable=AsyncMock) as mock_claude,
            patch.object(agent, "_build_game", new_callable=AsyncMock) as mock_build,
        ):
            mock_install.return_value = ProcessResult(0, "", "", False, 1.0)
            mock_claude.return_value = ProcessResult(0, "done", "", False, 10.0)
            mock_build.return_value = ProcessResult(0, "built", "", False, 5.0)

            # Create dist dir (simulating build)
            (output_dir / "dist").mkdir()

            result = await agent.run(
                gdd=mock_gdd,
                output_dir=output_dir,
                engine="phaser",
            )

            assert result["status"] == "success"
            assert (output_dir / "package.json").exists()

    @pytest.mark.asyncio
    async def test_skip_npm_install(
        self,
        scaffolds_dir: Path,
        output_dir: Path,
        mock_gdd: GameDesignDocument,
    ) -> None:
        """Test skip_npm_install flag."""
        agent = BuildAgent(scaffolds_dir=scaffolds_dir)

        with (
            patch.object(agent, "_install_dependencies", new_callable=AsyncMock) as mock_install,
            patch.object(agent, "_invoke_claude_code", new_callable=AsyncMock) as mock_claude,
            patch.object(agent, "_build_game", new_callable=AsyncMock) as mock_build,
        ):
            mock_claude.return_value = ProcessResult(0, "done", "", False, 10.0)
            mock_build.return_value = ProcessResult(0, "built", "", False, 5.0)
            (output_dir / "dist").mkdir()

            await agent.run(
                gdd=mock_gdd,
                output_dir=output_dir,
                skip_npm_install=True,
            )

            mock_install.assert_not_called()

    @pytest.mark.asyncio
    async def test_skip_build(
        self,
        scaffolds_dir: Path,
        output_dir: Path,
        mock_gdd: GameDesignDocument,
    ) -> None:
        """Test skip_build flag."""
        agent = BuildAgent(scaffolds_dir=scaffolds_dir)

        with (
            patch.object(agent, "_install_dependencies", new_callable=AsyncMock) as mock_install,
            patch.object(agent, "_invoke_claude_code", new_callable=AsyncMock) as mock_claude,
            patch.object(agent, "_build_game", new_callable=AsyncMock) as mock_build,
        ):
            mock_install.return_value = ProcessResult(0, "", "", False, 1.0)
            mock_claude.return_value = ProcessResult(0, "done", "", False, 10.0)

            result = await agent.run(
                gdd=mock_gdd,
                output_dir=output_dir,
                skip_build=True,
            )

            mock_build.assert_not_called()
            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_claude_code_failure_raises(
        self,
        scaffolds_dir: Path,
        output_dir: Path,
        mock_gdd: GameDesignDocument,
    ) -> None:
        """Test BuildFailedError when Claude Code fails."""
        agent = BuildAgent(scaffolds_dir=scaffolds_dir)

        with (
            patch.object(agent, "_install_dependencies", new_callable=AsyncMock) as mock_install,
            patch.object(agent, "_invoke_claude_code", new_callable=AsyncMock) as mock_claude,
        ):
            mock_install.return_value = ProcessResult(0, "", "", False, 1.0)
            mock_claude.return_value = ProcessResult(1, "", "error", False, 5.0)

            with pytest.raises(BuildFailedError, match="Claude Code execution failed"):
                await agent.run(
                    gdd=mock_gdd,
                    output_dir=output_dir,
                    skip_build=True,
                )

    @pytest.mark.asyncio
    async def test_build_failure_raises(
        self,
        scaffolds_dir: Path,
        output_dir: Path,
        mock_gdd: GameDesignDocument,
    ) -> None:
        """Test BuildFailedError when npm build fails."""
        agent = BuildAgent(scaffolds_dir=scaffolds_dir)

        with (
            patch.object(agent, "_install_dependencies", new_callable=AsyncMock) as mock_install,
            patch.object(agent, "_invoke_claude_code", new_callable=AsyncMock) as mock_claude,
            patch.object(agent, "_build_game", new_callable=AsyncMock) as mock_build,
        ):
            mock_install.return_value = ProcessResult(0, "", "", False, 1.0)
            mock_claude.return_value = ProcessResult(0, "done", "", False, 10.0)
            mock_build.return_value = ProcessResult(1, "", "build error", False, 5.0)

            with pytest.raises(BuildFailedError, match="npm build failed"):
                await agent.run(
                    gdd=mock_gdd,
                    output_dir=output_dir,
                )


# =============================================================================
# Subprocess Utility Tests
# =============================================================================


class TestSubprocessUtilities:
    """Tests for subprocess utilities used by BuildAgent."""

    @pytest.mark.asyncio
    async def test_install_dependencies_no_npm(self, output_dir: Path) -> None:
        """Test error when npm not found."""
        agent = BuildAgent()

        with (
            patch("game_workflow.agents.build.find_executable", return_value=None),
            pytest.raises(BuildFailedError, match="npm not found"),
        ):
            await agent._install_dependencies(output_dir)

    @pytest.mark.asyncio
    async def test_invoke_claude_code_uses_agent_sdk(
        self, output_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that _invoke_claude_code uses the Agent SDK."""
        agent = BuildAgent()

        # Mock the Agent SDK function
        mock_invoke = AsyncMock(
            return_value={"success": True, "output": "Build completed", "error": None}
        )
        monkeypatch.setattr("game_workflow.agents.build.invoke_claude_code", mock_invoke)

        result = await agent._invoke_claude_code(output_dir, "test prompt")

        mock_invoke.assert_called_once()
        assert result.success is True
        assert result.stdout == "Build completed"


# =============================================================================
# ProcessResult Tests
# =============================================================================


class TestProcessResult:
    """Tests for ProcessResult dataclass."""

    def test_success_property_true(self) -> None:
        """Test success is True for return_code 0."""
        result = ProcessResult(return_code=0, stdout="ok")
        assert result.success is True

    def test_success_property_false_nonzero(self) -> None:
        """Test success is False for non-zero return_code."""
        result = ProcessResult(return_code=1, stdout="error")
        assert result.success is False

    def test_success_property_false_timeout(self) -> None:
        """Test success is False when timed out."""
        result = ProcessResult(return_code=0, stdout="ok", timed_out=True)
        assert result.success is False
