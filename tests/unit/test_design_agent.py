"""Tests for the DesignAgent module."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from game_workflow.agents import DesignAgent
from game_workflow.agents.schemas import (
    ComplexityLevel,
    GameConcept,
    GameDesignDocument,
    GameEngine,
    TechnicalSpecification,
)

# =============================================================================
# Sample Data Fixtures
# =============================================================================


@pytest.fixture
def sample_concept_data() -> dict:
    """Provide sample concept data for testing."""
    return {
        "title": "Time Twist",
        "elevator_pitch": "A mind-bending puzzle platformer where you control time itself. Rewind mistakes, slow enemies, and create temporal paradoxes to solve increasingly complex puzzles.",
        "core_hook": "Simultaneous control of multiple timeline versions of yourself to solve puzzles",
        "key_features": [
            "Time rewind mechanic",
            "Temporal clones that replay your actions",
            "Time-locked puzzle elements",
        ],
        "player_fantasy": "Being a master of time who can undo any mistake",
        "emotional_journey": "From confusion to mastery as you learn to think in multiple timelines",
        "session_length": "10-15 minutes",
        "primary_genre": "Puzzle Platformer",
        "sub_genres": ["Indie", "Brain Teaser"],
        "tone": "Mysterious and thought-provoking",
        "visual_style": "Minimalist pixel art with glowing time effects",
        "core_mechanics": [
            {
                "name": "Time Rewind",
                "brief_description": "Hold a button to rewind time up to 10 seconds",
            },
            {
                "name": "Temporal Clone",
                "brief_description": "Create a ghost that replays your recorded actions",
            },
        ],
        "similar_games": [
            {"name": "Braid", "what_we_take": "Time manipulation puzzles"},
            {"name": "Celeste", "what_we_take": "Tight platformer controls"},
        ],
        "unique_selling_points": [
            "Multiple simultaneous timelines",
            "Paradox-based puzzle mechanics",
            "Beautiful temporal visual effects",
        ],
        "recommended_engine": "phaser",
        "complexity_level": "moderate",
        "estimated_scope": "Medium - 3-4 week build",
        "risks": [
            "Time mechanics can be confusing for players",
            "Performance with multiple temporal clones",
        ],
        "rationale": "The prompt asked for time manipulation, and this concept explores the most interesting possibilities of that mechanic in a puzzle context.",
    }


@pytest.fixture
def sample_gdd_data(sample_concept_data: dict) -> dict:
    """Provide sample GDD data for testing."""
    return {
        "title": sample_concept_data["title"],
        "concept_summary": sample_concept_data["elevator_pitch"],
        "genre": sample_concept_data["primary_genre"],
        "platform": "Web (HTML5)",
        "target_audience": "Puzzle game enthusiasts aged 16-35",
        "unique_selling_points": sample_concept_data["unique_selling_points"],
        "core_game_loop": "Enter level -> Solve puzzle using time mechanics -> Complete level -> Unlock next",
        "core_mechanics": [
            {
                "name": "Time Rewind",
                "description": "Player can hold R to rewind time up to 10 seconds",
                "controls": "R key / Right trigger",
            },
            {
                "name": "Temporal Clone",
                "description": "Press C to create a clone that replays actions",
                "controls": "C key / X button",
            },
        ],
        "player_actions": [
            {"name": "Move", "description": "Arrow keys to move left/right"},
            {"name": "Jump", "description": "Space to jump"},
            {"name": "Rewind", "description": "R to rewind time"},
        ],
        "win_condition": "Complete all 20 levels",
        "loss_condition": "No death, puzzles reset on failure",
        "progression_system": "Linear progression through increasingly complex levels",
        "difficulty_curve": "Gentle learning curve with new mechanics introduced every 5 levels",
        "setting": "An ethereal void between moments in time",
        "narrative": "You are a temporal guardian who must fix broken timelines",
        "levels": [
            {
                "name": "Tutorial - First Steps",
                "description": "Introduction to basic movement",
                "objectives": "Reach the exit door",
            },
            {
                "name": "Time's First Lesson",
                "description": "Introduction to time rewind",
                "objectives": "Use rewind to undo a mistake",
            },
        ],
        "visual_style": "Minimalist pixel art with glowing neon time effects",
        "art_direction": "16x16 pixel sprites, limited color palette, particle effects for time",
        "color_palette": [
            {"name": "Background", "hex": "#0a0a0f", "usage": "Main background"},
            {"name": "Primary", "hex": "#4fc3f7", "usage": "Time effects"},
            {"name": "Accent", "hex": "#ff6b6b", "usage": "Danger zones"},
        ],
        "audio_style": "Ambient electronic with time-warping effects",
        "sound_effects": [
            {"name": "time_rewind", "description": "Whooshing reverse sound"},
            {"name": "clone_spawn", "description": "Ethereal chime"},
        ],
        "music_description": "Ambient electronic tracks that react to time manipulation",
        "hud_elements": [
            {"name": "Time Meter", "description": "Shows available rewind time"},
            {"name": "Clone Counter", "description": "Number of active clones"},
        ],
        "menu_flow": "Main Menu -> Level Select -> Play -> Pause -> Resume/Quit",
        "ui_style_guide": "Minimal UI with semi-transparent panels",
        "engine": "phaser",
        "resolution": "800x600",
        "target_fps": 60,
        "max_load_time": "< 3 seconds",
        "memory_budget": "< 100MB",
        "supported_platforms": ["Chrome", "Firefox", "Safari", "Edge"],
        "input_methods": ["Keyboard", "Gamepad"],
        "mvp_features": [
            "Basic movement and jumping",
            "Time rewind mechanic",
            "5 tutorial levels",
        ],
        "nice_to_have_features": ["Temporal clone mechanic", "15 additional levels"],
        "future_features": ["Level editor", "Speed run mode"],
        "out_of_scope": ["Multiplayer", "Mobile support"],
        "inspiration_games": [
            {"name": "Braid", "relevance": "Time manipulation puzzles"},
            {"name": "Celeste", "relevance": "Tight platformer feel"},
        ],
        "art_references": ["Hyper Light Drifter pixel art style"],
        "technical_references": ["Phaser 3 documentation"],
        "sprite_assets": [
            {"name": "player", "dimensions": "16x16", "description": "Player character"},
            {"name": "clone", "dimensions": "16x16", "description": "Temporal clone"},
        ],
        "audio_assets": [
            {"name": "bgm_main", "format": "mp3", "description": "Main background music"},
        ],
        "implementation_notes": "Focus on smooth time rewind first",
    }


@pytest.fixture
def sample_tech_spec_data() -> dict:
    """Provide sample tech spec data for testing."""
    return {
        "project_name": "time-twist",
        "engine": "phaser",
        "file_structure": [
            {"path": "src/main.js", "purpose": "Game entry point"},
            {"path": "src/scenes/GameScene.js", "purpose": "Main game scene"},
        ],
        "dependencies": [
            {"name": "phaser", "version": "^3.70.0", "purpose": "Game engine"},
        ],
        "scene_list": ["BootScene", "MenuScene", "GameScene", "PauseScene"],
        "main_classes": ["Player", "TemporalClone", "TimeManager", "Level"],
        "build_command": "npm run build",
        "dev_command": "npm run dev",
        "output_directory": "dist",
        "implementation_order": [
            "Project setup and basic scene structure",
            "Player movement and physics",
            "Time rewind mechanic",
            "Level loading and completion",
            "UI and menus",
        ],
        "technical_notes": "Use Phaser's built-in physics for platforming",
    }


@pytest.fixture
def mock_concept_response(sample_concept_data: dict) -> str:
    """Mock API response for concept generation."""
    return json.dumps([sample_concept_data])


@pytest.fixture
def mock_gdd_response(sample_gdd_data: dict) -> str:
    """Mock API response for GDD generation."""
    return json.dumps(sample_gdd_data)


@pytest.fixture
def mock_tech_spec_response(sample_tech_spec_data: dict) -> str:
    """Mock API response for tech spec generation."""
    return json.dumps(sample_tech_spec_data)


# =============================================================================
# Schema Tests
# =============================================================================


class TestGameConceptSchema:
    """Tests for the GameConcept Pydantic model."""

    def test_valid_concept(self, sample_concept_data: dict) -> None:
        """Test creating a valid GameConcept."""
        concept = GameConcept(**sample_concept_data)
        assert concept.title == "Time Twist"
        assert len(concept.key_features) == 3
        assert concept.recommended_engine == GameEngine.PHASER

    def test_concept_requires_title(self, sample_concept_data: dict) -> None:
        """Test that title is required."""
        from pydantic import ValidationError

        del sample_concept_data["title"]
        with pytest.raises(ValidationError):
            GameConcept(**sample_concept_data)

    def test_concept_validates_complexity(self, sample_concept_data: dict) -> None:
        """Test complexity level validation."""
        sample_concept_data["complexity_level"] = "moderate"
        concept = GameConcept(**sample_concept_data)
        assert concept.complexity_level == ComplexityLevel.MODERATE

    def test_concept_json_schema(self) -> None:
        """Test JSON schema generation."""
        schema = GameConcept.model_json_schema()
        assert "title" in schema["properties"]
        assert "elevator_pitch" in schema["properties"]


class TestGameDesignDocumentSchema:
    """Tests for the GameDesignDocument Pydantic model."""

    def test_valid_gdd(self, sample_gdd_data: dict) -> None:
        """Test creating a valid GDD."""
        gdd = GameDesignDocument(**sample_gdd_data)
        assert gdd.title == "Time Twist"
        assert len(gdd.core_mechanics) == 2
        assert gdd.engine == GameEngine.PHASER

    def test_gdd_defaults(self) -> None:
        """Test GDD default values."""
        minimal_data = {
            "title": "Test Game",
            "concept_summary": "A test game",
            "genre": "Action",
            "target_audience": "Everyone",
            "unique_selling_points": ["Unique"],
            "core_game_loop": "Play -> Win",
            "core_mechanics": [{"name": "Action", "description": "Do things"}],
            "player_actions": [{"name": "Move", "description": "Move around"}],
            "win_condition": "Reach the end",
            "loss_condition": "Die",
            "progression_system": "Levels",
            "difficulty_curve": "Linear",
            "setting": "Fantasy world",
            "narrative": "Save the world",
            "levels": [{"name": "Level 1", "description": "First", "objectives": "Win"}],
            "visual_style": "Pixel art",
            "art_direction": "Retro",
            "color_palette": [{"name": "Main", "hex": "#ffffff", "usage": "Background"}],
            "audio_style": "Chiptune",
            "sound_effects": [{"name": "jump", "description": "Jump sound"}],
            "music_description": "Retro music",
            "hud_elements": [{"name": "Score", "description": "Player score"}],
            "menu_flow": "Main -> Play",
            "ui_style_guide": "Minimal",
            "mvp_features": ["Core gameplay"],
            "inspiration_games": [{"name": "Classic", "relevance": "Inspiration"}],
        }
        gdd = GameDesignDocument(**minimal_data)
        assert gdd.platform == "Web (HTML5)"
        assert gdd.resolution == "800x600"
        assert gdd.target_fps == 60


class TestTechnicalSpecificationSchema:
    """Tests for the TechnicalSpecification Pydantic model."""

    def test_valid_tech_spec(self, sample_tech_spec_data: dict) -> None:
        """Test creating a valid tech spec."""
        spec = TechnicalSpecification(**sample_tech_spec_data)
        assert spec.project_name == "time-twist"
        assert spec.engine == GameEngine.PHASER
        assert len(spec.scene_list) == 4


# =============================================================================
# DesignAgent Tests
# =============================================================================


class TestDesignAgent:
    """Tests for the DesignAgent class."""

    def test_agent_name(self) -> None:
        """Test DesignAgent name property."""
        agent = DesignAgent()
        assert agent.name == "DesignAgent"

    def test_agent_default_model(self) -> None:
        """Test default model is set."""
        agent = DesignAgent()
        assert agent.model == "claude-sonnet-4-5-20250929"

    def test_agent_custom_model(self) -> None:
        """Test custom model can be set."""
        agent = DesignAgent(model="claude-3-opus-20240229")
        assert agent.model == "claude-3-opus-20240229"

    def test_agent_num_concepts_clamped(self) -> None:
        """Test num_concepts is clamped to 1-5."""
        agent1 = DesignAgent(num_concepts=0)
        assert agent1.num_concepts == 1

        agent2 = DesignAgent(num_concepts=10)
        assert agent2.num_concepts == 5

        agent3 = DesignAgent(num_concepts=3)
        assert agent3.num_concepts == 3

    def test_agent_warns_with_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that agent logs deprecation warning when API key is set."""
        import warnings

        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        agent = DesignAgent()

        # _validate_config should warn that API key is not required
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            agent._validate_config()
            assert len(w) == 1
            assert "not required" in str(w[0].message)
            assert issubclass(w[0].category, DeprecationWarning)

    def test_parse_json_response_clean(self) -> None:
        """Test parsing clean JSON response."""
        agent = DesignAgent()
        response = '{"key": "value"}'
        result = agent._parse_json_response(response)
        assert result == {"key": "value"}

    def test_parse_json_response_markdown(self) -> None:
        """Test parsing JSON wrapped in markdown code blocks."""
        agent = DesignAgent()
        response = '```json\n{"key": "value"}\n```'
        result = agent._parse_json_response(response)
        assert result == {"key": "value"}

    def test_parse_json_response_with_text(self) -> None:
        """Test parsing JSON with surrounding text."""
        agent = DesignAgent()
        response = 'Here is the JSON: {"key": "value"} Hope this helps!'
        result = agent._parse_json_response(response)
        assert result == {"key": "value"}

    def test_parse_concepts_response_array(self) -> None:
        """Test parsing array of concepts."""
        agent = DesignAgent()
        response = '[{"title": "Game 1"}, {"title": "Game 2"}]'
        result = agent._parse_concepts_response(response)
        assert len(result) == 2
        assert result[0]["title"] == "Game 1"

    def test_parse_concepts_response_wrapped(self) -> None:
        """Test parsing concepts wrapped in object."""
        agent = DesignAgent()
        response = '{"concepts": [{"title": "Game 1"}]}'
        result = agent._parse_concepts_response(response)
        assert len(result) == 1
        assert result[0]["title"] == "Game 1"

    @pytest.mark.asyncio
    async def test_run_with_mocked_api(
        self,
        tmp_path: Path,
        sample_prompt: str,
        mock_concept_response: str,
        mock_gdd_response: str,
        mock_tech_spec_response: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test full run with mocked Agent SDK responses."""
        # Track call count to return different responses
        call_count = [0]
        responses = [mock_concept_response, mock_gdd_response, mock_tech_spec_response]

        async def mock_generate(*_args: Any, **_kwargs: Any) -> str:
            response = responses[min(call_count[0], 2)]
            call_count[0] += 1
            return response

        # Patch the Agent SDK function
        monkeypatch.setattr(
            "game_workflow.agents.design.generate_structured_response",
            mock_generate,
        )

        agent = DesignAgent(num_concepts=1, output_dir=tmp_path)
        result = await agent.run(sample_prompt, engine="phaser")

        assert result["status"] == "success"
        assert "concepts" in result
        assert "selected_concept" in result
        assert "gdd" in result
        assert "tech_spec" in result
        assert "artifacts" in result

        # Check artifacts were saved
        assert (tmp_path / "concept.json").exists()
        assert (tmp_path / "gdd.json").exists()
        assert (tmp_path / "gdd.md").exists()
        assert (tmp_path / "tech-spec.json").exists()

    @pytest.mark.asyncio
    async def test_run_handles_invalid_engine(
        self,
        tmp_path: Path,
        sample_prompt: str,
        mock_concept_response: str,
        mock_gdd_response: str,
        mock_tech_spec_response: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that invalid engine falls back to phaser."""
        call_count = [0]
        responses = [mock_concept_response, mock_gdd_response, mock_tech_spec_response]

        async def mock_generate(*_args: Any, **_kwargs: Any) -> str:
            response = responses[min(call_count[0], 2)]
            call_count[0] += 1
            return response

        monkeypatch.setattr(
            "game_workflow.agents.design.generate_structured_response",
            mock_generate,
        )

        agent = DesignAgent(num_concepts=1, output_dir=tmp_path)
        result = await agent.run(sample_prompt, engine="invalid_engine")

        assert result["status"] == "success"


# =============================================================================
# Template Tests
# =============================================================================


class TestTemplates:
    """Tests for template loading and rendering."""

    def test_load_template(self) -> None:
        """Test loading a template."""
        from game_workflow.utils.templates import load_template

        content = load_template("gdd-template")
        assert "Game Design Document" in content
        assert "{{ title }}" in content

    def test_load_template_not_found(self) -> None:
        """Test loading non-existent template raises error."""
        from game_workflow.utils.templates import load_template

        with pytest.raises(FileNotFoundError):
            load_template("nonexistent-template")

    def test_render_template(self) -> None:
        """Test rendering a template with context."""
        from game_workflow.utils.templates import render_template

        context = {
            "title": "Test Game",
            "concept_summary": "A test game",
            "genre": "Action",
            "platform": "Web",
            "target_audience": "Everyone",
            "unique_selling_points": ["Fast", "Fun"],
            "core_game_loop": "Play",
            "core_mechanics": [{"name": "Jump", "description": "Jump up"}],
            "player_actions": [{"name": "Move", "description": "Move around"}],
            "win_condition": "Win",
            "loss_condition": "Lose",
            "progression_system": "Levels",
            "difficulty_curve": "Linear",
            "setting": "World",
            "narrative": "Story",
            "levels": [{"name": "L1", "description": "First", "objectives": "Go"}],
            "visual_style": "Pixel",
            "art_direction": "Retro",
            "color_palette": [{"name": "Main", "hex": "#fff", "usage": "bg"}],
            "audio_style": "Chip",
            "sound_effects": [{"name": "jump", "description": "boing"}],
            "music_description": "Music",
            "hud_elements": [{"name": "Score", "description": "Points"}],
            "menu_flow": "Main",
            "ui_style_guide": "Clean",
            "engine": "phaser",
            "resolution": "800x600",
            "target_fps": 60,
            "max_load_time": "3s",
            "memory_budget": "100MB",
            "supported_platforms": ["Web"],
            "input_methods": ["Keyboard"],
            "mvp_features": ["Core"],
            "nice_to_have_features": ["Extra"],
            "future_features": ["More"],
            "out_of_scope": ["Mobile"],
            "inspiration_games": [{"name": "Game", "relevance": "Inspired"}],
            "art_references": ["Art"],
            "technical_references": ["Docs"],
            "sprite_assets": [{"name": "player", "dimensions": "16x16", "description": "char"}],
            "audio_assets": [{"name": "bgm", "format": "mp3", "description": "music"}],
            "implementation_notes": "Notes here",
        }

        rendered = render_template("gdd-template.md", context)
        assert "Test Game" in rendered
        assert "Action" in rendered

    def test_render_gdd(self, sample_gdd_data: dict) -> None:
        """Test render_gdd convenience function."""
        from game_workflow.utils.templates import render_gdd

        rendered = render_gdd(sample_gdd_data)
        assert "Time Twist" in rendered
        assert "Puzzle Platformer" in rendered

    def test_render_concept(self, sample_concept_data: dict) -> None:
        """Test render_concept convenience function."""
        from game_workflow.utils.templates import render_concept

        rendered = render_concept(sample_concept_data)
        assert "Time Twist" in rendered
        assert "Elevator Pitch" in rendered

    def test_list_templates(self) -> None:
        """Test listing available templates."""
        from game_workflow.utils.templates import list_templates

        templates = list_templates()
        assert "gdd-template.md" in templates
        assert "concept-template.md" in templates
