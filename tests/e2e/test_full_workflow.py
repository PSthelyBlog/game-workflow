"""End-to-end tests for the full game workflow.

These tests verify the complete workflow from start to finish,
with mocked external services but real state management and
artifact generation.
"""

from __future__ import annotations

import json
import zipfile
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from game_workflow.orchestrator import Workflow, WorkflowPhase
from game_workflow.orchestrator.state import WorkflowState

if TYPE_CHECKING:
    from pathlib import Path


# =============================================================================
# Test Data Factories
# =============================================================================


def create_mock_concept_data() -> dict[str, Any]:
    """Create mock concept data matching the schema structure."""
    return {
        "title": "Block Match Puzzle",
        "genre": "Puzzle",
        "tagline": "Match colors, solve puzzles, have fun!",
        "elevator_pitch": "A colorful puzzle game where players match blocks to clear levels.",
        "core_hook": "Unique chain reaction mechanics",
        "key_features": [
            "Easy to learn, hard to master gameplay",
            "Colorful graphics",
            "Multiple game modes",
        ],
    }


def create_mock_gdd_data() -> dict[str, Any]:
    """Create mock GDD data matching the schema structure."""
    return {
        "title": "Block Match Puzzle",
        "genre": "Puzzle",
        "concept_summary": "A fun puzzle game about matching colored blocks.",
        "target_audience": "Casual gamers",
        "core_mechanics": [
            {
                "name": "Block Matching",
                "description": "Match 3 or more blocks of the same color",
                "controls": "Click/tap to select and swap blocks",
            }
        ],
        "player_actions": ["Select blocks", "Swap adjacent blocks", "Use power-ups"],
        "win_conditions": ["Clear all blocks", "Reach target score"],
        "lose_conditions": ["Run out of moves", "Time runs out"],
    }


def create_mock_tech_spec_data() -> dict[str, Any]:
    """Create mock tech spec data matching the schema structure."""
    return {
        "project_name": "block-match-puzzle",
        "engine": "phaser",
        "scene_list": ["BootScene", "PreloadScene", "MenuScene", "GameScene"],
        "implementation_order": [
            "Set up project scaffold",
            "Create game scene",
            "Implement block matching",
        ],
    }


# =============================================================================
# Mock Approval Hook
# =============================================================================


class E2EApprovalHook:
    """Approval hook for E2E testing with tracking."""

    def __init__(self, auto_approve: bool = True) -> None:
        """Initialize the approval hook."""
        self.auto_approve = auto_approve
        self.approval_requests: list[dict[str, Any]] = []
        self.notifications: list[dict[str, Any]] = []

    async def request_approval(
        self,
        message: str,
        context: dict[str, Any] | None = None,
        timeout_minutes: int | None = None,  # noqa: ARG002
    ) -> bool:
        """Record and handle approval request."""
        self.approval_requests.append(
            {
                "message": message,
                "context": context,
            }
        )
        return self.auto_approve

    async def send_notification(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
        level: str = "info",
    ) -> bool:
        """Record notification."""
        self.notifications.append(
            {
                "message": message,
                "context": context,
                "level": level,
            }
        )
        return True


# =============================================================================
# Mock Agent Factories
# =============================================================================


def create_mock_design_agent(tmp_path: Path) -> MagicMock:
    """Create a mock DesignAgent with realistic output."""
    concept = create_mock_concept_data()
    gdd = create_mock_gdd_data()
    tech_spec = create_mock_tech_spec_data()

    # Create artifact files
    design_dir = tmp_path / "design"
    design_dir.mkdir(parents=True, exist_ok=True)

    concept_path = design_dir / "concept.json"
    concept_path.write_text(json.dumps(concept, indent=2))

    gdd_json_path = design_dir / "gdd.json"
    gdd_json_path.write_text(json.dumps(gdd, indent=2))

    gdd_md_path = design_dir / "gdd.md"
    gdd_md_path.write_text(f"# {gdd['title']}\n\n{gdd['concept_summary']}")

    tech_spec_path = design_dir / "tech-spec.json"
    tech_spec_path.write_text(json.dumps(tech_spec, indent=2))

    agent = MagicMock()
    agent.name = "DesignAgent"
    agent.run = AsyncMock(
        return_value={
            "status": "success",
            "concepts": [concept],
            "selected_concept": concept,
            "gdd": gdd,
            "tech_spec": tech_spec,
            "artifacts": {
                "concept": str(concept_path),
                "gdd_json": str(gdd_json_path),
                "gdd": str(gdd_md_path),
                "tech_spec": str(tech_spec_path),
            },
        }
    )

    return agent


def create_mock_build_agent(tmp_path: Path) -> MagicMock:
    """Create a mock BuildAgent with realistic output."""
    # Create game directory structure
    game_dir = tmp_path / "game"
    game_dir.mkdir(parents=True, exist_ok=True)

    src_dir = game_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)

    # Create source files
    (src_dir / "main.js").write_text("// Game entry point\nconsole.log('Game loaded');")
    (src_dir / "scenes").mkdir(exist_ok=True)
    (src_dir / "scenes" / "GameScene.js").write_text("// Game scene")

    # Create dist directory
    dist_dir = game_dir / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    (dist_dir / "index.html").write_text("<html><body>Game</body></html>")
    (dist_dir / "game.js").write_text("// Bundled game code")

    # Create package.json
    package_json = {
        "name": "block-match-puzzle",
        "version": "1.0.0",
        "scripts": {
            "dev": "vite",
            "build": "vite build",
        },
    }
    (game_dir / "package.json").write_text(json.dumps(package_json, indent=2))

    agent = MagicMock()
    agent.name = "BuildAgent"
    agent.run = AsyncMock(
        return_value={
            "status": "success",
            "output_dir": str(game_dir),
            "build_dir": str(dist_dir),
            "claude_code_output": "Game implemented successfully.",
            "npm_build_output": "Build complete.",
        }
    )

    return agent


def create_mock_qa_agent(tmp_path: Path) -> MagicMock:
    """Create a mock QAAgent with realistic output."""
    # Create QA report
    qa_dir = tmp_path / "qa"
    qa_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "game_title": "Block Match Puzzle",
        "summary": {
            "total_tests": 8,
            "passed": 8,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "success_rate": 100.0,
            "overall_status": "passed",
        },
        "test_results": [
            {"name": "page_loads", "status": "passed", "duration": 0.5},
            {"name": "canvas_present", "status": "passed", "duration": 0.1},
            {"name": "no_javascript_errors", "status": "passed", "duration": 0.2},
            {"name": "game_initializes", "status": "passed", "duration": 1.0},
            {"name": "no_console_errors", "status": "passed", "duration": 0.3},
            {"name": "input_response", "status": "passed", "duration": 0.5},
            {"name": "performance_fps", "status": "passed", "duration": 2.0},
            {"name": "performance_load_time", "status": "passed", "duration": 0.8},
        ],
        "recommendations": [],
    }

    report_path = qa_dir / "qa-report.json"
    report_path.write_text(json.dumps(report, indent=2))

    agent = MagicMock()
    agent.name = "QAAgent"
    agent.run = AsyncMock(
        return_value={
            "status": "success",
            "report": report,
            "report_path": str(report_path),
            "recommendations": [],
        }
    )

    return agent


def create_mock_publish_agent(tmp_path: Path) -> MagicMock:
    """Create a mock PublishAgent with realistic output."""
    # Create publish artifacts
    publish_dir = tmp_path / "publish"
    publish_dir.mkdir(parents=True, exist_ok=True)

    store_page = {
        "title": "Block Match Puzzle",
        "tagline": "Match colors, solve puzzles, have fun!",
        "description": "A colorful puzzle game where players match blocks.",
        "controls": [{"key": "Mouse", "action": "Select and swap blocks"}],
        "features": ["Easy to learn", "Multiple levels"],
    }

    store_page_path = publish_dir / "store-page.json"
    store_page_path.write_text(json.dumps(store_page, indent=2))

    store_page_md = publish_dir / "store-page.md"
    store_page_md.write_text(
        f"# {store_page['title']}\n\n{store_page['tagline']}\n\n{store_page['description']}"
    )

    # Create game zip
    zip_path = publish_dir / "game.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("index.html", "<html><body>Game</body></html>")
        zf.writestr("game.js", "// Game code")

    publish_output = {
        "store_page": store_page,
        "store_page_markdown": store_page_md.read_text(),
        "artifacts": [
            {"name": "game.zip", "path": str(zip_path)},
        ],
        "zip_path": str(zip_path),
        "github_release": {
            "tag": "v1.0.0",
            "title": "Block Match Puzzle v1.0.0",
            "body": "Initial release",
        },
        "visibility": "draft",
    }

    publish_output_path = publish_dir / "publish-output.json"
    publish_output_path.write_text(json.dumps(publish_output, indent=2))

    agent = MagicMock()
    agent.name = "PublishAgent"
    agent.run = AsyncMock(
        return_value={
            "status": "success",
            "store_page": store_page,
            "store_page_markdown": store_page_md.read_text(),
            "artifacts": [{"name": "game.zip", "path": str(zip_path)}],
            "zip_path": str(zip_path),
            "publish_output": {"visibility": "draft"},
        }
    )

    return agent


# =============================================================================
# Test Classes
# =============================================================================


class TestFullWorkflowE2E:
    """End-to-end tests for the complete workflow."""

    @pytest.mark.asyncio
    async def test_full_workflow_with_auto_approve(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test complete workflow execution with auto-approve."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path / "state"))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt="Create a simple puzzle game about matching colored blocks",
            auto_approve=True,
            output_dir=tmp_path / "output",
        )

        # Set up mock agents
        workflow._design_agent = create_mock_design_agent(tmp_path)
        workflow._build_agent = create_mock_build_agent(tmp_path)
        workflow._qa_agent = create_mock_qa_agent(tmp_path)
        workflow._publish_agent = create_mock_publish_agent(tmp_path)

        # Run the workflow
        result = await workflow.run()

        # Verify completion
        assert result["status"] == "complete"
        assert workflow.phase == WorkflowPhase.COMPLETE

        # Verify all agents were called
        workflow._design_agent.run.assert_called_once()
        workflow._build_agent.run.assert_called_once()
        workflow._qa_agent.run.assert_called_once()
        workflow._publish_agent.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_full_workflow_with_approval_hook(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test workflow with approval hook tracking."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path / "state"))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        approval_hook = E2EApprovalHook(auto_approve=True)

        workflow = Workflow(
            prompt="Create a puzzle platformer",
            approval_hook=approval_hook,
            output_dir=tmp_path / "output",
        )

        # Set up mock agents
        workflow._design_agent = create_mock_design_agent(tmp_path)
        workflow._build_agent = create_mock_build_agent(tmp_path)
        workflow._qa_agent = create_mock_qa_agent(tmp_path)
        workflow._publish_agent = create_mock_publish_agent(tmp_path)

        result = await workflow.run()

        # Verify completion
        assert result["status"] == "complete"

        # Verify approval gates were hit
        assert len(approval_hook.approval_requests) == 3
        gate_messages = [req["message"] for req in approval_hook.approval_requests]
        assert any("concept" in msg.lower() for msg in gate_messages)
        assert any("build" in msg.lower() for msg in gate_messages)
        assert any("publish" in msg.lower() for msg in gate_messages)

        # Verify notifications were sent
        assert len(approval_hook.notifications) >= 2
        levels = [n["level"] for n in approval_hook.notifications]
        assert "info" in levels  # Start notification
        assert "success" in levels  # Completion notification

    @pytest.mark.asyncio
    async def test_workflow_state_persistence(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that workflow state is persisted and can be loaded."""
        state_dir = tmp_path / "state"
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(state_dir))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        # Create workflow and run through design phase
        workflow = Workflow(
            prompt="Create a space shooter game",
            auto_approve=True,
            output_dir=tmp_path / "output",
        )

        # Store state ID for later
        state_id = workflow.state.id

        # Set up mock agents
        workflow._design_agent = create_mock_design_agent(tmp_path)
        workflow._build_agent = create_mock_build_agent(tmp_path)
        workflow._qa_agent = create_mock_qa_agent(tmp_path)
        workflow._publish_agent = create_mock_publish_agent(tmp_path)

        # Run workflow
        await workflow.run()

        # Verify state was saved
        state_file = state_dir / f"{state_id}.json"
        assert state_file.exists()

        # Load state and verify
        loaded_state = WorkflowState.load(state_id)
        assert loaded_state.id == state_id
        assert loaded_state.prompt == "Create a space shooter game"
        assert loaded_state.phase == WorkflowPhase.COMPLETE

    @pytest.mark.asyncio
    async def test_workflow_checkpoint_creation(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that checkpoints are created at each phase."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path / "state"))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt="Create a racing game",
            auto_approve=True,
            output_dir=tmp_path / "output",
        )

        # Set up mock agents
        workflow._design_agent = create_mock_design_agent(tmp_path)
        workflow._build_agent = create_mock_build_agent(tmp_path)
        workflow._qa_agent = create_mock_qa_agent(tmp_path)
        workflow._publish_agent = create_mock_publish_agent(tmp_path)

        await workflow.run()

        # Verify checkpoints were created
        checkpoints = workflow.state.checkpoints
        assert len(checkpoints) >= 4  # Init, Design, Build, QA, Publish

        # Verify checkpoint phases
        checkpoint_phases = [cp.phase for cp in checkpoints]
        assert WorkflowPhase.INIT in checkpoint_phases


class TestArtifactVerification:
    """Tests to verify generated artifacts."""

    @pytest.mark.asyncio
    async def test_design_artifacts_created(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that design artifacts are created correctly."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path / "state"))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt="Create a puzzle game",
            auto_approve=True,
            output_dir=tmp_path / "output",
        )

        # Create design agent with real artifacts
        workflow._design_agent = create_mock_design_agent(tmp_path)
        workflow._build_agent = create_mock_build_agent(tmp_path)
        workflow._qa_agent = create_mock_qa_agent(tmp_path)
        workflow._publish_agent = create_mock_publish_agent(tmp_path)

        await workflow.run()

        # Verify design artifacts
        design_dir = tmp_path / "design"
        assert (design_dir / "concept.json").exists()
        assert (design_dir / "gdd.json").exists()
        assert (design_dir / "gdd.md").exists()
        assert (design_dir / "tech-spec.json").exists()

        # Verify concept content
        concept_data = json.loads((design_dir / "concept.json").read_text())
        assert "title" in concept_data
        assert "genre" in concept_data
        assert "tagline" in concept_data

        # Verify GDD content
        gdd_data = json.loads((design_dir / "gdd.json").read_text())
        assert "title" in gdd_data
        assert "core_mechanics" in gdd_data
        assert "win_conditions" in gdd_data

    @pytest.mark.asyncio
    async def test_build_artifacts_created(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that build artifacts are created correctly."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path / "state"))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt="Create a puzzle game",
            auto_approve=True,
            output_dir=tmp_path / "output",
        )

        workflow._design_agent = create_mock_design_agent(tmp_path)
        workflow._build_agent = create_mock_build_agent(tmp_path)
        workflow._qa_agent = create_mock_qa_agent(tmp_path)
        workflow._publish_agent = create_mock_publish_agent(tmp_path)

        await workflow.run()

        # Verify build artifacts
        game_dir = tmp_path / "game"
        assert (game_dir / "package.json").exists()
        assert (game_dir / "src" / "main.js").exists()
        assert (game_dir / "dist" / "index.html").exists()

    @pytest.mark.asyncio
    async def test_qa_report_created(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that QA report is created correctly."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path / "state"))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt="Create a puzzle game",
            auto_approve=True,
            output_dir=tmp_path / "output",
        )

        workflow._design_agent = create_mock_design_agent(tmp_path)
        workflow._build_agent = create_mock_build_agent(tmp_path)
        workflow._qa_agent = create_mock_qa_agent(tmp_path)
        workflow._publish_agent = create_mock_publish_agent(tmp_path)

        await workflow.run()

        # Verify QA report
        qa_dir = tmp_path / "qa"
        assert (qa_dir / "qa-report.json").exists()

        report = json.loads((qa_dir / "qa-report.json").read_text())
        assert "summary" in report
        assert "test_results" in report
        assert report["summary"]["total_tests"] > 0

    @pytest.mark.asyncio
    async def test_publish_artifacts_created(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that publish artifacts are created correctly."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path / "state"))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt="Create a puzzle game",
            auto_approve=True,
            output_dir=tmp_path / "output",
        )

        workflow._design_agent = create_mock_design_agent(tmp_path)
        workflow._build_agent = create_mock_build_agent(tmp_path)
        workflow._qa_agent = create_mock_qa_agent(tmp_path)
        workflow._publish_agent = create_mock_publish_agent(tmp_path)

        await workflow.run()

        # Verify publish artifacts
        publish_dir = tmp_path / "publish"
        assert (publish_dir / "store-page.json").exists()
        assert (publish_dir / "store-page.md").exists()
        assert (publish_dir / "game.zip").exists()

        # Verify zip contents
        with zipfile.ZipFile(publish_dir / "game.zip", "r") as zf:
            names = zf.namelist()
            assert "index.html" in names


class TestWorkflowErrorHandling:
    """E2E tests for error handling scenarios."""

    @pytest.mark.asyncio
    async def test_workflow_handles_design_failure(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test workflow handles design agent failure."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path / "state"))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings
        from game_workflow.orchestrator.exceptions import AgentError

        reload_settings()

        workflow = Workflow(
            prompt="Create a puzzle game",
            auto_approve=True,
            output_dir=tmp_path / "output",
            max_retries=0,  # No retries
        )

        # Create failing design agent
        failing_agent = MagicMock()
        failing_agent.name = "DesignAgent"
        failing_agent.run = AsyncMock(side_effect=AgentError("DesignAgent", "API error"))
        workflow._design_agent = failing_agent

        result = await workflow.run()

        assert result["status"] == "failed"
        assert workflow.phase == WorkflowPhase.FAILED
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_workflow_approval_rejection_stops_workflow(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that rejection at approval gate stops workflow."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path / "state"))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        # Reject all approvals
        approval_hook = E2EApprovalHook(auto_approve=False)

        workflow = Workflow(
            prompt="Create a puzzle game",
            approval_hook=approval_hook,
            output_dir=tmp_path / "output",
        )

        workflow._design_agent = create_mock_design_agent(tmp_path)

        result = await workflow.run()

        assert result["status"] == "failed"
        assert workflow.phase == WorkflowPhase.FAILED

        # Only concept approval was requested before rejection
        assert len(approval_hook.approval_requests) == 1


class TestWorkflowResume:
    """E2E tests for workflow resume functionality."""

    @pytest.mark.asyncio
    async def test_resume_from_saved_state(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test resuming workflow from saved state."""
        state_dir = tmp_path / "state"
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(state_dir))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        # Create initial state at DESIGN phase
        initial_state = WorkflowState(
            prompt="Create a platformer game",
            engine="phaser",
        )
        initial_state.transition_to(WorkflowPhase.DESIGN)
        initial_state.save()
        state_id = initial_state.id

        # Resume the workflow
        resumed_workflow = Workflow.resume(
            state_id=state_id,
            auto_approve=True,
            output_dir=tmp_path / "output",
        )

        # Verify resume was successful
        assert resumed_workflow.state.id == state_id
        assert resumed_workflow.phase == WorkflowPhase.DESIGN
        assert resumed_workflow.prompt == "Create a platformer game"

    @pytest.mark.asyncio
    async def test_resume_latest_workflow(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test resuming the latest workflow."""
        state_dir = tmp_path / "state"
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(state_dir))

        from game_workflow.config import reload_settings

        reload_settings()

        # Create a state
        state = WorkflowState(
            prompt="Create a shooter game",
            engine="phaser",
        )
        state.save()

        # Resume latest
        resumed = Workflow.resume_latest(
            auto_approve=True,
            output_dir=tmp_path / "output",
        )

        assert resumed is not None
        assert resumed.prompt == "Create a shooter game"


class TestWorkflowWithDifferentEngines:
    """E2E tests for different game engines."""

    @pytest.mark.asyncio
    async def test_workflow_with_phaser_engine(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test workflow with Phaser engine."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path / "state"))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt="Create a puzzle game",
            engine="phaser",
            auto_approve=True,
            output_dir=tmp_path / "output",
        )

        assert workflow.engine == "phaser"

        workflow._design_agent = create_mock_design_agent(tmp_path)
        workflow._build_agent = create_mock_build_agent(tmp_path)
        workflow._qa_agent = create_mock_qa_agent(tmp_path)
        workflow._publish_agent = create_mock_publish_agent(tmp_path)

        result = await workflow.run()
        assert result["status"] == "complete"

    @pytest.mark.asyncio
    async def test_workflow_with_godot_engine(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test workflow with Godot engine."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path / "state"))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt="Create a puzzle game",
            engine="godot",
            auto_approve=True,
            output_dir=tmp_path / "output",
        )

        assert workflow.engine == "godot"

        workflow._design_agent = create_mock_design_agent(tmp_path)
        workflow._build_agent = create_mock_build_agent(tmp_path)
        workflow._qa_agent = create_mock_qa_agent(tmp_path)
        workflow._publish_agent = create_mock_publish_agent(tmp_path)

        result = await workflow.run()
        assert result["status"] == "complete"


class TestCLIIntegration:
    """E2E tests for CLI commands."""

    def test_cli_version_command(self) -> None:
        """Test the version command works."""
        from typer.testing import CliRunner

        from game_workflow.main import app

        runner = CliRunner()
        result = runner.invoke(app, ["version"])

        assert result.exit_code == 0
        assert "game-workflow" in result.stdout.lower() or "version" in result.stdout.lower()

    def test_cli_status_no_workflow(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test status command with no active workflow."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path / "state"))

        from game_workflow.config import reload_settings

        reload_settings()

        from typer.testing import CliRunner

        from game_workflow.main import app

        runner = CliRunner()
        result = runner.invoke(app, ["status"])

        # Should indicate no workflow or show empty status
        assert result.exit_code in [0, 1]

    def test_cli_state_list_empty(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test state list command with no states."""
        state_dir = tmp_path / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(state_dir))

        from game_workflow.config import reload_settings

        reload_settings()

        from typer.testing import CliRunner

        from game_workflow.main import app

        runner = CliRunner()
        result = runner.invoke(app, ["state", "list"])

        assert result.exit_code == 0

    def test_cli_state_list_with_states(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test state list command with existing states."""
        state_dir = tmp_path / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(state_dir))

        from game_workflow.config import reload_settings

        reload_settings()

        # Create a state
        state = WorkflowState(
            prompt="Test prompt",
            engine="phaser",
        )
        state.save()

        from typer.testing import CliRunner

        from game_workflow.main import app

        runner = CliRunner()
        result = runner.invoke(app, ["state", "list"])

        assert result.exit_code == 0
        # Should show at least one state
        assert state.id in result.stdout or "workflow" in result.stdout.lower()


class TestMultipleWorkflows:
    """E2E tests for handling multiple workflows."""

    @pytest.mark.asyncio
    async def test_multiple_sequential_workflows(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test running multiple workflows sequentially."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path / "state"))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        prompts = [
            "Create a puzzle game",
            "Create a platformer game",
            "Create a shooter game",
        ]

        results = []
        workflows = []
        for i, prompt in enumerate(prompts):
            workflow = Workflow(
                prompt=prompt,
                auto_approve=True,
                output_dir=tmp_path / f"output_{i}",
            )

            workflow._design_agent = create_mock_design_agent(tmp_path / f"design_{i}")
            workflow._build_agent = create_mock_build_agent(tmp_path / f"build_{i}")
            workflow._qa_agent = create_mock_qa_agent(tmp_path / f"qa_{i}")
            workflow._publish_agent = create_mock_publish_agent(tmp_path / f"publish_{i}")

            result = await workflow.run()
            results.append(result)
            workflows.append(workflow)

        # All workflows should complete
        assert all(r["status"] == "complete" for r in results)

        # Each workflow should have captured its prompt correctly
        assert workflows[0].prompt == "Create a puzzle game"
        assert workflows[1].prompt == "Create a platformer game"
        assert workflows[2].prompt == "Create a shooter game"

        # All workflows completed successfully
        assert all(w.phase == WorkflowPhase.COMPLETE for w in workflows)


class TestApprovalGates:
    """E2E tests for approval gate behavior."""

    @pytest.mark.asyncio
    async def test_approval_context_includes_relevant_data(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that approval requests include relevant context."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path / "state"))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        approval_hook = E2EApprovalHook(auto_approve=True)

        workflow = Workflow(
            prompt="Create a puzzle game",
            approval_hook=approval_hook,
            output_dir=tmp_path / "output",
        )

        workflow._design_agent = create_mock_design_agent(tmp_path)
        workflow._build_agent = create_mock_build_agent(tmp_path)
        workflow._qa_agent = create_mock_qa_agent(tmp_path)
        workflow._publish_agent = create_mock_publish_agent(tmp_path)

        await workflow.run()

        # Verify concept approval has title
        concept_approval = approval_hook.approval_requests[0]
        assert concept_approval["context"] is not None
        assert "title" in concept_approval["context"]

        # Verify build approval has QA data
        build_approval = approval_hook.approval_requests[1]
        assert build_approval["context"] is not None
        assert "total_tests" in build_approval["context"]

        # Verify publish approval has store page data
        publish_approval = approval_hook.approval_requests[2]
        assert publish_approval["context"] is not None
        assert "visibility" in publish_approval["context"]

    @pytest.mark.asyncio
    async def test_selective_approval_gate_rejection(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test rejecting only the publish gate."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path / "state"))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        class SelectiveApprovalHook:
            """Approve concept and build, reject publish."""

            def __init__(self) -> None:
                self.approval_requests: list[dict[str, Any]] = []
                self.notifications: list[dict[str, Any]] = []

            async def request_approval(
                self,
                message: str,
                context: dict[str, Any] | None = None,
                timeout_minutes: int | None = None,  # noqa: ARG002
            ) -> bool:
                self.approval_requests.append({"message": message, "context": context})
                # Reject publish gate
                return "publish" not in message.lower()

            async def send_notification(
                self,
                message: str,
                *,
                context: dict[str, Any] | None = None,  # noqa: ARG002
                level: str = "info",
            ) -> bool:
                self.notifications.append({"message": message, "level": level})
                return True

        approval_hook = SelectiveApprovalHook()

        workflow = Workflow(
            prompt="Create a puzzle game",
            approval_hook=approval_hook,
            output_dir=tmp_path / "output",
        )

        workflow._design_agent = create_mock_design_agent(tmp_path)
        workflow._build_agent = create_mock_build_agent(tmp_path)
        workflow._qa_agent = create_mock_qa_agent(tmp_path)
        workflow._publish_agent = create_mock_publish_agent(tmp_path)

        result = await workflow.run()

        # Should fail at publish gate
        assert result["status"] == "failed"

        # Should have hit all 3 approval gates
        assert len(approval_hook.approval_requests) == 3


class TestStateMetadata:
    """E2E tests for state metadata handling."""

    @pytest.mark.asyncio
    async def test_state_metadata_preserved(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that state metadata is preserved through workflow."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path / "state"))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt="Create a puzzle game",
            engine="phaser",
            auto_approve=True,
            output_dir=tmp_path / "output",
        )

        workflow._design_agent = create_mock_design_agent(tmp_path)
        workflow._build_agent = create_mock_build_agent(tmp_path)
        workflow._qa_agent = create_mock_qa_agent(tmp_path)
        workflow._publish_agent = create_mock_publish_agent(tmp_path)

        await workflow.run()

        # Verify metadata is populated
        assert workflow.state.metadata.get("prompt") == "Create a puzzle game"
        assert workflow.state.metadata.get("engine") == "phaser"
        assert workflow.state.metadata.get("output_dir") is not None

    @pytest.mark.asyncio
    async def test_approvals_tracked_in_state(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that approvals are tracked in state."""
        monkeypatch.setenv("GAME_WORKFLOW_STATE_DIR", str(tmp_path / "state"))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        workflow = Workflow(
            prompt="Create a puzzle game",
            auto_approve=True,
            output_dir=tmp_path / "output",
        )

        workflow._design_agent = create_mock_design_agent(tmp_path)
        workflow._build_agent = create_mock_build_agent(tmp_path)
        workflow._qa_agent = create_mock_qa_agent(tmp_path)
        workflow._publish_agent = create_mock_publish_agent(tmp_path)

        await workflow.run()

        # Verify approvals are tracked
        assert "concept" in workflow.state.approvals
        assert "build" in workflow.state.approvals
        assert "publish" in workflow.state.approvals
        assert all(v is True for v in workflow.state.approvals.values())
