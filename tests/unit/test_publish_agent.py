"""Tests for the PublishAgent module."""

from __future__ import annotations

import json
import zipfile
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock

import pytest

from game_workflow.agents.publish import (
    ControlMapping,
    Credit,
    FeatureHighlight,
    GitHubRelease,
    ItchioClassification,
    ItchioVisibility,
    PublishAgent,
    PublishConfig,
    PublishOutput,
    ReleaseArtifact,
    ReleaseType,
    Screenshot,
    StorePageContent,
    TechnicalDetails,
    VersionInfo,
    get_publish_output_schema,
    get_store_page_schema,
)
from game_workflow.orchestrator.exceptions import AgentError

if TYPE_CHECKING:
    from pathlib import Path


# =============================================================================
# Sample Data Fixtures
# =============================================================================


@pytest.fixture
def sample_gdd_data() -> dict[str, Any]:
    """Provide sample GDD data for testing."""
    return {
        "title": "Time Twist",
        "concept_summary": "A mind-bending puzzle platformer where you control time itself.",
        "genre": "Puzzle Platformer",
        "platform": "Web (HTML5)",
        "target_audience": "Puzzle game enthusiasts aged 16-35",
        "unique_selling_points": [
            "Multiple simultaneous timelines",
            "Paradox-based puzzle mechanics",
            "Beautiful temporal visual effects",
        ],
        "core_game_loop": "Enter level -> Solve puzzle using time mechanics -> Complete level -> Unlock next",
        "core_mechanics": [
            {
                "name": "Time Rewind",
                "description": "Player can hold R to rewind time up to 10 seconds",
                "controls": "R key",
            },
            {
                "name": "Temporal Clone",
                "description": "Press C to create a clone that replays actions",
                "controls": "C key",
            },
        ],
        "player_actions": [
            {"name": "Move", "description": "Arrow keys to move left/right"},
            {"name": "Jump", "description": "Space to jump"},
        ],
        "win_condition": "Complete all 20 levels",
        "loss_condition": "No death, puzzles reset on failure",
        "progression_system": "Linear progression through increasingly complex levels",
        "difficulty_curve": "Gentle learning curve",
        "setting": "An ethereal void between moments in time",
        "narrative": "You are a temporal guardian who must fix broken timelines",
        "levels": [
            {
                "name": "Tutorial",
                "description": "Introduction to basic movement",
                "objectives": "Reach the exit door",
            },
        ],
        "visual_style": "Minimalist pixel art with glowing neon time effects",
        "art_direction": "16x16 pixel sprites",
        "color_palette": [
            {"name": "Background", "hex": "#0a0a0f", "usage": "Main background"},
        ],
        "audio_style": "Ambient electronic",
        "sound_effects": [
            {"name": "time_rewind", "description": "Whooshing reverse sound"},
        ],
        "music_description": "Ambient electronic tracks",
        "hud_elements": [
            {"name": "Time Meter", "description": "Shows available rewind time"},
        ],
        "menu_flow": "Main Menu -> Level Select -> Play",
        "ui_style_guide": "Minimal UI",
        "engine": "phaser",
        "resolution": "800x600",
        "target_fps": 60,
        "max_load_time": "< 3 seconds",
        "memory_budget": "< 100MB",
        "supported_platforms": ["Chrome", "Firefox", "Safari", "Edge"],
        "input_methods": ["Keyboard", "Mouse"],
        "mvp_features": [
            "Basic movement and jumping",
            "Time rewind mechanic",
            "5 tutorial levels",
        ],
        "nice_to_have_features": ["Temporal clone mechanic"],
        "future_features": ["Level editor"],
        "out_of_scope": ["Multiplayer"],
        "inspiration_games": [
            {"name": "Braid", "relevance": "Time manipulation puzzles"},
        ],
        "art_references": ["Hyper Light Drifter"],
        "technical_references": ["Phaser 3 documentation"],
        "sprite_assets": [
            {"name": "player", "dimensions": "16x16", "description": "Player character"},
        ],
        "audio_assets": [
            {"name": "bgm_main", "format": "mp3", "description": "Main music"},
        ],
        "implementation_notes": "Focus on smooth time rewind first",
    }


@pytest.fixture
def sample_store_page_data() -> dict[str, Any]:
    """Provide sample store page data for testing."""
    return {
        "title": "Time Twist",
        "tagline": "Bend time, solve puzzles, master the paradox.",
        "description": "A mind-bending puzzle platformer where you control time itself. Rewind mistakes, create temporal clones, and solve increasingly complex puzzles across 20 hand-crafted levels.",
        "features": [
            "Time rewind mechanic - undo your mistakes",
            "Temporal clones that replay your actions",
            "20 challenging puzzle levels",
            "Beautiful minimalist pixel art",
        ],
        "controls": [
            {"input": "Arrow Keys", "action": "Move left/right"},
            {"input": "Space", "action": "Jump"},
            {"input": "R", "action": "Rewind time"},
        ],
        "story": "You are a temporal guardian tasked with fixing broken timelines.",
        "tips": [
            "Use rewind liberally - there's no penalty",
            "Watch your clone carefully to time jumps",
        ],
        "tags": ["puzzle", "platformer", "time-manipulation", "pixel-art", "indie"],
        "engine": "Phaser",
    }


@pytest.fixture
def sample_api_response_text() -> str:
    """Create a sample API response text with store page content."""
    return json.dumps(
        {
            "title": "Time Twist",
            "tagline": "Bend time, solve puzzles, master the paradox.",
            "description": "A mind-bending puzzle platformer where you control time itself.",
            "features": [
                "Time rewind mechanic",
                "Temporal clones",
                "20 puzzle levels",
            ],
            "controls": [
                {"input": "Arrow Keys", "action": "Move"},
                {"input": "Space", "action": "Jump"},
            ],
            "tags": ["puzzle", "platformer", "indie"],
        }
    )


@pytest.fixture
def game_dir(tmp_path: Path) -> Path:
    """Create a temporary game directory with sample files."""
    game_path = tmp_path / "dist"
    game_path.mkdir()

    # Create sample game files
    (game_path / "index.html").write_text("<html><body>Game</body></html>")
    (game_path / "main.js").write_text("console.log('game');")

    assets_dir = game_path / "assets"
    assets_dir.mkdir()
    (assets_dir / "player.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

    return game_path


@pytest.fixture
def gdd_file(tmp_path: Path, sample_gdd_data: dict) -> Path:
    """Create a temporary GDD JSON file."""
    gdd_path = tmp_path / "gdd.json"
    with gdd_path.open("w") as f:
        json.dump(sample_gdd_data, f)
    return gdd_path


@pytest.fixture
def screenshots_dir(tmp_path: Path) -> Path:
    """Create a temporary screenshots directory."""
    screenshots = tmp_path / "screenshots"
    screenshots.mkdir()
    (screenshots / "screenshot-01.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)
    (screenshots / "screenshot-02.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)
    return screenshots


# =============================================================================
# Schema Tests
# =============================================================================


class TestPublishSchemas:
    """Tests for Pydantic schemas."""

    def test_control_mapping_creation(self) -> None:
        """Test ControlMapping schema."""
        control = ControlMapping(input="Space", action="Jump")
        assert control.input == "Space"
        assert control.action == "Jump"

    def test_feature_highlight_creation(self) -> None:
        """Test FeatureHighlight schema."""
        highlight = FeatureHighlight(name="Time Rewind", description="Undo your mistakes")
        assert highlight.name == "Time Rewind"
        assert highlight.description == "Undo your mistakes"

    def test_screenshot_creation(self) -> None:
        """Test Screenshot schema."""
        screenshot = Screenshot(
            filename="screen1.png",
            url="/path/to/screen1.png",
            caption="Gameplay screenshot",
            description="Player navigating a puzzle",
        )
        assert screenshot.filename == "screen1.png"
        assert screenshot.caption == "Gameplay screenshot"

    def test_screenshot_optional_fields(self) -> None:
        """Test Screenshot with minimal fields."""
        screenshot = Screenshot(filename="screen.png", caption="Test")
        assert screenshot.url == ""
        assert screenshot.description is None

    def test_credit_creation(self) -> None:
        """Test Credit schema."""
        credit = Credit(role="Developer", name="Test User", link="https://example.com")
        assert credit.role == "Developer"
        assert credit.link == "https://example.com"

    def test_technical_details_defaults(self) -> None:
        """Test TechnicalDetails default values."""
        details = TechnicalDetails()
        assert details.resolution == "800x600"
        assert "Chrome" in details.browser_support
        assert details.save_support is False
        assert details.audio is True

    def test_version_info_defaults(self) -> None:
        """Test VersionInfo default values."""
        version = VersionInfo()
        assert version.current == "1.0.0"
        assert version.changelog == []

    def test_store_page_content_creation(self, sample_store_page_data: dict) -> None:
        """Test StorePageContent creation."""
        page = StorePageContent(**sample_store_page_data)
        assert page.title == "Time Twist"
        assert page.tagline == "Bend time, solve puzzles, master the paradox."
        assert len(page.features) == 4
        assert len(page.controls) == 3

    def test_release_artifact_creation(self) -> None:
        """Test ReleaseArtifact schema."""
        artifact = ReleaseArtifact(
            name="game.zip",
            path="/path/to/game.zip",
            size_bytes=1024,
        )
        assert artifact.name == "game.zip"
        assert artifact.size_bytes == 1024
        assert artifact.checksum is None

    def test_github_release_creation(self) -> None:
        """Test GitHubRelease schema."""
        release = GitHubRelease(
            tag="v1.0.0",
            name="Time Twist v1.0.0",
            body="Initial release",
        )
        assert release.tag == "v1.0.0"
        assert release.prerelease is False
        assert release.draft is True

    def test_publish_output_creation(self, sample_store_page_data: dict) -> None:
        """Test PublishOutput schema."""
        store_page = StorePageContent(**sample_store_page_data)
        output = PublishOutput(
            store_page=store_page,
            store_page_markdown="# Game",
            artifacts=[],
            release_type=ReleaseType.INITIAL,
        )
        assert output.version == "1.0.0"
        assert output.classification == ItchioClassification.GAME
        assert output.visibility == ItchioVisibility.DRAFT


class TestPublishEnums:
    """Tests for enum types."""

    def test_release_type_values(self) -> None:
        """Test ReleaseType enum values."""
        assert ReleaseType.INITIAL == "initial"
        assert ReleaseType.UPDATE == "update"
        assert ReleaseType.PATCH == "patch"
        assert ReleaseType.BETA == "beta"
        assert ReleaseType.DEMO == "demo"

    def test_itchio_classification_values(self) -> None:
        """Test ItchioClassification enum values."""
        assert ItchioClassification.GAME == "game"
        assert ItchioClassification.TOOL == "tool"
        assert ItchioClassification.OTHER == "other"

    def test_itchio_visibility_values(self) -> None:
        """Test ItchioVisibility enum values."""
        assert ItchioVisibility.DRAFT == "draft"
        assert ItchioVisibility.RESTRICTED == "restricted"
        assert ItchioVisibility.PUBLIC == "public"


class TestPublishConfig:
    """Tests for PublishConfig dataclass."""

    def test_publish_config_defaults(self) -> None:
        """Test PublishConfig default values."""
        config = PublishConfig(project_name="test-game")
        assert config.project_name == "test-game"
        assert config.version == "1.0.0"
        assert config.release_type == ReleaseType.INITIAL
        assert config.visibility == ItchioVisibility.DRAFT
        assert config.create_github_release is False

    def test_publish_config_custom_values(self, tmp_path: Path) -> None:
        """Test PublishConfig with custom values."""
        config = PublishConfig(
            project_name="my-game",
            version="2.0.0",
            release_type=ReleaseType.UPDATE,
            visibility=ItchioVisibility.PUBLIC,
            itchio_username="testuser",
            github_repo="user/repo",
            create_github_release=True,
            screenshots_dir=tmp_path,
            additional_tags=["puzzle", "indie"],
        )
        assert config.version == "2.0.0"
        assert config.release_type == ReleaseType.UPDATE
        assert config.additional_tags == ["puzzle", "indie"]


# =============================================================================
# PublishAgent Tests
# =============================================================================


class TestPublishAgentBasic:
    """Basic tests for PublishAgent."""

    def test_agent_name(self) -> None:
        """Test agent name property."""
        agent = PublishAgent()
        assert agent.name == "PublishAgent"

    def test_agent_initialization(self, tmp_path: Path) -> None:
        """Test agent initialization with options."""
        agent = PublishAgent(
            model="claude-sonnet-4-5-20250929",
            output_dir=tmp_path,
        )
        assert agent.model == "claude-sonnet-4-5-20250929"
        assert agent.output_dir == tmp_path

    def test_config_validates_without_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that validation passes without API key (SDK handles auth)."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        from game_workflow.config import reload_settings

        reload_settings()

        agent = PublishAgent()

        # Should not raise - API key is optional with Agent SDK
        agent._validate_config()  # No error expected


class TestPublishAgentGDDLoading:
    """Tests for GDD loading functionality."""

    @pytest.mark.asyncio
    async def test_load_gdd_from_data(self, sample_gdd_data: dict) -> None:
        """Test loading GDD from dictionary."""
        agent = PublishAgent()
        gdd = await agent._load_gdd(None, sample_gdd_data)
        assert gdd.title == "Time Twist"
        assert gdd.genre == "Puzzle Platformer"

    @pytest.mark.asyncio
    async def test_load_gdd_from_file(self, gdd_file: Path) -> None:
        """Test loading GDD from JSON file."""
        agent = PublishAgent()
        gdd = await agent._load_gdd(gdd_file, None)
        assert gdd.title == "Time Twist"

    @pytest.mark.asyncio
    async def test_load_gdd_no_input(self) -> None:
        """Test that loading without any input raises error."""
        agent = PublishAgent()
        with pytest.raises(AgentError) as exc_info:
            await agent._load_gdd(None, None)
        assert "gdd_path or gdd_data must be provided" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_load_gdd_file_not_found(self, tmp_path: Path) -> None:
        """Test error when GDD file doesn't exist."""
        agent = PublishAgent()
        with pytest.raises(AgentError) as exc_info:
            await agent._load_gdd(tmp_path / "nonexistent.json", None)
        assert "GDD file not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_load_gdd_invalid_json(self, tmp_path: Path) -> None:
        """Test error when GDD file contains invalid JSON."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not valid json")

        agent = PublishAgent()
        with pytest.raises(AgentError) as exc_info:
            await agent._load_gdd(bad_file, None)
        assert "Failed to parse GDD JSON" in str(exc_info.value)


class TestPublishAgentScreenshots:
    """Tests for screenshot handling."""

    def test_add_screenshots(self, screenshots_dir: Path, sample_store_page_data: dict) -> None:
        """Test adding screenshots to store page."""
        agent = PublishAgent()
        store_page = StorePageContent(**sample_store_page_data)

        updated = agent._add_screenshots(store_page, screenshots_dir)

        assert len(updated.screenshots) == 2
        assert updated.screenshots[0].filename == "screenshot-01.png"
        assert updated.screenshots[1].filename == "screenshot-02.png"

    def test_add_screenshots_empty_dir(self, tmp_path: Path, sample_store_page_data: dict) -> None:
        """Test with empty screenshots directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        agent = PublishAgent()
        store_page = StorePageContent(**sample_store_page_data)

        updated = agent._add_screenshots(store_page, empty_dir)
        assert len(updated.screenshots) == 0

    def test_add_screenshots_limit(self, tmp_path: Path, sample_store_page_data: dict) -> None:
        """Test that screenshots are limited to 10."""
        many_screenshots = tmp_path / "many"
        many_screenshots.mkdir()
        for i in range(15):
            (many_screenshots / f"screen-{i:02d}.png").write_bytes(
                b"\x89PNG\r\n\x1a\n" + b"\x00" * 10
            )

        agent = PublishAgent()
        store_page = StorePageContent(**sample_store_page_data)

        updated = agent._add_screenshots(store_page, many_screenshots)
        assert len(updated.screenshots) == 10


class TestPublishAgentArtifacts:
    """Tests for artifact packaging."""

    @pytest.mark.asyncio
    async def test_package_artifacts(self, game_dir: Path, tmp_path: Path) -> None:
        """Test packaging game artifacts."""
        agent = PublishAgent(output_dir=tmp_path)
        config = PublishConfig(project_name="test-game", version="1.0.0")

        artifacts, zip_path = await agent._package_artifacts(game_dir, config)

        # Check artifacts list
        assert len(artifacts) >= 3  # index.html, main.js, player.png + zip

        # Check zip was created
        assert zip_path is not None
        assert zip_path.exists()
        assert zip_path.name == "test-game-v1.0.0.zip"

        # Verify zip contents
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            assert "index.html" in names
            assert "main.js" in names

    @pytest.mark.asyncio
    async def test_package_artifacts_custom_version(self, game_dir: Path, tmp_path: Path) -> None:
        """Test artifact packaging with custom version."""
        agent = PublishAgent(output_dir=tmp_path)
        config = PublishConfig(project_name="my-game", version="2.5.0")

        _, zip_path = await agent._package_artifacts(game_dir, config)

        assert zip_path is not None
        assert zip_path.name == "my-game-v2.5.0.zip"


class TestPublishAgentGitHubRelease:
    """Tests for GitHub release preparation."""

    def test_prepare_github_release_initial(self, sample_gdd_data: dict) -> None:
        """Test preparing initial GitHub release."""
        from game_workflow.agents.schemas import GameDesignDocument

        agent = PublishAgent()
        gdd = GameDesignDocument.model_validate(sample_gdd_data)
        config = PublishConfig(
            project_name="time-twist",
            version="1.0.0",
            release_type=ReleaseType.INITIAL,
        )
        store_page = StorePageContent(
            title="Time Twist",
            tagline="Bend time!",
            description="A puzzle game.",
            features=["Feature 1", "Feature 2"],
            controls=[ControlMapping(input="Space", action="Jump")],
        )

        release = agent._prepare_github_release(gdd, config, store_page)

        assert release.tag == "v1.0.0"
        assert release.name == "Time Twist v1.0.0"
        assert "initial release" in release.body
        assert release.draft is True
        assert release.prerelease is False

    def test_prepare_github_release_beta(self, sample_gdd_data: dict) -> None:
        """Test preparing beta GitHub release."""
        from game_workflow.agents.schemas import GameDesignDocument

        agent = PublishAgent()
        gdd = GameDesignDocument.model_validate(sample_gdd_data)
        config = PublishConfig(
            project_name="time-twist",
            version="0.9.0",
            release_type=ReleaseType.BETA,
        )
        store_page = StorePageContent(
            title="Time Twist",
            tagline="Bend time!",
            description="A puzzle game.",
            features=["Feature 1"],
            controls=[ControlMapping(input="Space", action="Jump")],
        )

        release = agent._prepare_github_release(gdd, config, store_page)

        assert release.tag == "v0.9.0"
        assert release.prerelease is True


class TestPublishAgentStorePageRendering:
    """Tests for store page rendering."""

    def test_render_store_page(self, sample_store_page_data: dict) -> None:
        """Test rendering store page to markdown."""
        agent = PublishAgent()
        store_page = StorePageContent(**sample_store_page_data)

        markdown = agent._render_store_page(store_page)

        assert "# Time Twist" in markdown
        assert "Bend time, solve puzzles, master the paradox." in markdown
        assert "Arrow Keys" in markdown
        assert "Made with Phaser" in markdown

    def test_render_store_page_with_screenshots(self, sample_store_page_data: dict) -> None:
        """Test rendering store page with screenshots."""
        sample_store_page_data["screenshots"] = [
            {"filename": "screen1.png", "url": "/img/screen1.png", "caption": "Gameplay"},
        ]
        agent = PublishAgent()
        store_page = StorePageContent(**sample_store_page_data)

        markdown = agent._render_store_page(store_page)

        assert "## Screenshots" in markdown
        assert "Gameplay" in markdown


class TestPublishAgentJSONParsing:
    """Tests for JSON response parsing."""

    def test_parse_json_response_clean(self) -> None:
        """Test parsing clean JSON response."""
        agent = PublishAgent()
        text = '{"title": "Test", "version": "1.0"}'

        result = agent._parse_json_response(text)

        assert result["title"] == "Test"
        assert result["version"] == "1.0"

    def test_parse_json_response_with_code_block(self) -> None:
        """Test parsing JSON wrapped in markdown code block."""
        agent = PublishAgent()
        text = '```json\n{"title": "Test"}\n```'

        result = agent._parse_json_response(text)

        assert result["title"] == "Test"

    def test_parse_json_response_with_surrounding_text(self) -> None:
        """Test parsing JSON with surrounding text."""
        agent = PublishAgent()
        text = 'Here is the response:\n{"title": "Test"}\nThank you!'

        result = agent._parse_json_response(text)

        assert result["title"] == "Test"

    def test_parse_json_response_invalid(self) -> None:
        """Test parsing invalid JSON raises error."""
        agent = PublishAgent()
        text = "This is not valid JSON at all"

        with pytest.raises(AgentError) as exc_info:
            agent._parse_json_response(text)

        assert "Failed to parse JSON" in str(exc_info.value)


class TestPublishAgentSaveArtifacts:
    """Tests for artifact saving."""

    @pytest.mark.asyncio
    async def test_save_artifacts(self, tmp_path: Path, sample_store_page_data: dict) -> None:
        """Test saving publish artifacts."""
        agent = PublishAgent(output_dir=tmp_path)
        store_page = StorePageContent(**sample_store_page_data)
        output = PublishOutput(
            store_page=store_page,
            store_page_markdown="# Test Game\n\nDescription",
            artifacts=[],
            release_type=ReleaseType.INITIAL,
        )

        saved = await agent._save_artifacts(output)

        assert "store_page_md" in saved
        assert "store_page_json" in saved
        assert "publish_output" in saved

        # Verify files exist
        assert (tmp_path / "store-page.md").exists()
        assert (tmp_path / "store-page.json").exists()
        assert (tmp_path / "publish-output.json").exists()

    @pytest.mark.asyncio
    async def test_save_artifacts_with_github_release(
        self, tmp_path: Path, sample_store_page_data: dict
    ) -> None:
        """Test saving artifacts including GitHub release notes."""
        agent = PublishAgent(output_dir=tmp_path)
        store_page = StorePageContent(**sample_store_page_data)
        github_release = GitHubRelease(
            tag="v1.0.0",
            name="Test v1.0.0",
            body="# Release Notes\n\nInitial release!",
        )
        output = PublishOutput(
            store_page=store_page,
            store_page_markdown="# Test",
            artifacts=[],
            release_type=ReleaseType.INITIAL,
            github_release=github_release,
        )

        saved = await agent._save_artifacts(output)

        assert "release_notes" in saved
        assert (tmp_path / "release-notes.md").exists()

    @pytest.mark.asyncio
    async def test_save_artifacts_no_output_dir(self, sample_store_page_data: dict) -> None:
        """Test error when output directory not set."""
        agent = PublishAgent()  # No output_dir
        store_page = StorePageContent(**sample_store_page_data)
        output = PublishOutput(
            store_page=store_page,
            store_page_markdown="# Test",
            artifacts=[],
            release_type=ReleaseType.INITIAL,
        )

        with pytest.raises(AgentError) as exc_info:
            await agent._save_artifacts(output)

        assert "Output directory not set" in str(exc_info.value)


class TestPublishAgentRun:
    """Tests for the main run method."""

    @pytest.mark.asyncio
    async def test_run_game_dir_not_found(self, tmp_path: Path, sample_gdd_data: dict) -> None:
        """Test error when game directory doesn't exist."""
        agent = PublishAgent()

        with pytest.raises(AgentError) as exc_info:
            await agent.run(
                game_dir=tmp_path / "nonexistent",
                gdd_data=sample_gdd_data,
            )

        assert "Game directory not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_run_full_workflow(
        self,
        game_dir: Path,
        sample_gdd_data: dict,
        sample_api_response_text: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test full publish workflow with mocked Agent SDK."""
        agent = PublishAgent(output_dir=tmp_path / "publish")

        # Mock the Agent SDK function
        mock_generate = AsyncMock(return_value=sample_api_response_text)
        monkeypatch.setattr(
            "game_workflow.agents.publish.generate_structured_response",
            mock_generate,
        )

        result = await agent.run(
            game_dir=game_dir,
            gdd_data=sample_gdd_data,
        )

        assert result["status"] == "success"
        assert "store_page" in result
        assert "artifacts" in result
        assert "zip_path" in result

    @pytest.mark.asyncio
    async def test_run_with_github_release(
        self,
        game_dir: Path,
        sample_gdd_data: dict,
        sample_api_response_text: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test workflow with GitHub release enabled."""
        agent = PublishAgent(output_dir=tmp_path / "publish")
        config = PublishConfig(
            project_name="test-game",
            create_github_release=True,
        )

        # Mock the Agent SDK function
        mock_generate = AsyncMock(return_value=sample_api_response_text)
        monkeypatch.setattr(
            "game_workflow.agents.publish.generate_structured_response",
            mock_generate,
        )

        result = await agent.run(
            game_dir=game_dir,
            gdd_data=sample_gdd_data,
            config=config,
        )

        assert result["github_release"] is not None
        assert result["github_release"]["tag"] == "v1.0.0"


class TestPublishAgentAgentSDK:
    """Tests for Agent SDK integration."""

    @pytest.mark.asyncio
    async def test_generate_marketing_copy_uses_agent_sdk(
        self,
        sample_gdd_data: dict,
        sample_api_response_text: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that _generate_marketing_copy uses the Agent SDK."""
        from game_workflow.agents.schemas import GameDesignDocument

        agent = PublishAgent()
        gdd = GameDesignDocument.model_validate(sample_gdd_data)
        config = PublishConfig(project_name="test-game")

        # Mock the Agent SDK function
        mock_generate = AsyncMock(return_value=sample_api_response_text)
        monkeypatch.setattr(
            "game_workflow.agents.publish.generate_structured_response",
            mock_generate,
        )

        result = await agent._generate_marketing_copy(gdd, config)

        # Verify the mock was called
        mock_generate.assert_called_once()
        assert result.title == "Time Twist"


class TestPublishAgentGDDSummary:
    """Tests for GDD summary generation."""

    def test_summarize_gdd(self, sample_gdd_data: dict) -> None:
        """Test GDD summarization for marketing prompt."""
        from game_workflow.agents.schemas import GameDesignDocument

        agent = PublishAgent()
        gdd = GameDesignDocument.model_validate(sample_gdd_data)

        summary = agent._summarize_gdd(gdd)

        assert "Time Twist" in summary
        assert "Puzzle Platformer" in summary
        assert "Time Rewind" in summary
        assert "Multiple simultaneous timelines" in summary


# =============================================================================
# Schema Export Tests
# =============================================================================


class TestSchemaExport:
    """Tests for JSON Schema export functions."""

    def test_get_store_page_schema(self) -> None:
        """Test StorePageContent schema export."""
        schema = get_store_page_schema()

        assert "properties" in schema
        assert "title" in schema["properties"]
        assert "tagline" in schema["properties"]
        assert "features" in schema["properties"]

    def test_get_publish_output_schema(self) -> None:
        """Test PublishOutput schema export."""
        schema = get_publish_output_schema()

        assert "properties" in schema
        assert "store_page" in schema["properties"]
        assert "artifacts" in schema["properties"]
        assert "release_type" in schema["properties"]
