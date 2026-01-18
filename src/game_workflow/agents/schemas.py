"""Pydantic schemas for design artifacts.

This module defines structured output schemas for game concepts and GDDs,
enabling validation and JSON Schema generation for API integration.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from functools import lru_cache
from typing import Any

from pydantic import BaseModel, Field


class ComplexityLevel(str, Enum):
    """Game complexity levels."""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class GameEngine(str, Enum):
    """Supported game engines."""

    PHASER = "phaser"
    GODOT = "godot"


# =============================================================================
# Game Concept Schemas
# =============================================================================


class CoreMechanicPreview(BaseModel):
    """Brief preview of a core mechanic for concept documents."""

    name: str = Field(..., description="Name of the mechanic")
    brief_description: str = Field(..., description="One-sentence description")


class SimilarGame(BaseModel):
    """Reference to a similar game."""

    name: str = Field(..., description="Name of the similar game")
    what_we_take: str = Field(..., description="What element we're inspired by")


class GameConcept(BaseModel):
    """A game concept proposal.

    This represents one of several concept variations generated
    from a user's prompt before the full GDD is created.
    """

    # Identification
    title: str = Field(..., description="Working title for the game")
    concept_number: int = Field(default=1, description="Which concept this is (1-5)")
    total_concepts: int = Field(default=1, description="Total concepts generated")
    generated_at: datetime = Field(default_factory=datetime.now)

    # Core pitch
    elevator_pitch: str = Field(
        ...,
        description="2-3 sentence summary that sells the game",
        min_length=50,
        max_length=500,
    )
    core_hook: str = Field(
        ...,
        description="The single unique mechanic or idea that makes this game special",
        min_length=20,
        max_length=300,
    )

    # Features
    key_features: list[str] = Field(
        ...,
        description="3-5 key features of the game",
        min_length=3,
        max_length=5,
    )

    # Experience
    player_fantasy: str = Field(..., description="What fantasy does the player live out?")
    emotional_journey: str = Field(..., description="What emotions should the player feel?")
    session_length: str = Field(
        ..., description="Typical play session length (e.g., '5-10 minutes')"
    )

    # Genre & style
    primary_genre: str = Field(..., description="Main genre (e.g., 'Puzzle Platformer')")
    sub_genres: list[str] = Field(default_factory=list, description="Secondary genres")
    tone: str = Field(..., description="Game tone (e.g., 'Lighthearted', 'Dark')")
    visual_style: str = Field(..., description="Art style (e.g., 'Pixel art', 'Minimalist')")

    # Mechanics preview
    core_mechanics: list[CoreMechanicPreview] = Field(
        ...,
        description="Preview of 2-4 core mechanics",
        min_length=2,
        max_length=4,
    )

    # References
    similar_games: list[SimilarGame] = Field(
        ...,
        description="2-3 similar games for reference",
        min_length=1,
        max_length=5,
    )
    unique_selling_points: list[str] = Field(
        ...,
        description="3 unique selling points",
        min_length=1,
        max_length=5,
    )

    # Technical assessment
    recommended_engine: GameEngine = Field(
        default=GameEngine.PHASER, description="Recommended game engine"
    )
    complexity_level: ComplexityLevel = Field(
        ..., description="Estimated implementation complexity"
    )
    estimated_scope: str = Field(..., description="Scope estimate (e.g., 'Small - 1-2 week build')")

    # Risks
    risks: list[str] = Field(default_factory=list, description="Potential risks or challenges")

    # Rationale
    rationale: str = Field(..., description="Why this concept fits the user's prompt")


# =============================================================================
# Game Design Document Schemas
# =============================================================================


class CoreMechanic(BaseModel):
    """Detailed core mechanic description for GDD."""

    name: str = Field(..., description="Name of the mechanic")
    description: str = Field(..., description="Detailed description of how it works")
    controls: str | None = Field(default=None, description="Input controls for this mechanic")


class PlayerAction(BaseModel):
    """A player action in the game."""

    name: str = Field(..., description="Action name (e.g., 'Jump')")
    description: str = Field(..., description="What the action does")


class Level(BaseModel):
    """A game level or environment."""

    name: str = Field(..., description="Level name")
    description: str = Field(..., description="Level description")
    objectives: str = Field(..., description="Level objectives")
    unique_features: str | None = Field(default=None, description="Unique features of this level")


class ColorEntry(BaseModel):
    """A color in the palette."""

    name: str = Field(..., description="Color name (e.g., 'Primary')")
    hex: str = Field(..., description="Hex color code", pattern=r"^#[0-9A-Fa-f]{6}$")
    usage: str = Field(..., description="How this color is used")


class SoundEffect(BaseModel):
    """A sound effect entry."""

    name: str = Field(..., description="Sound effect name")
    description: str = Field(..., description="When/how it plays")


class HUDElement(BaseModel):
    """A HUD element."""

    name: str = Field(..., description="Element name (e.g., 'Score')")
    description: str = Field(..., description="What it displays")


class InspirationGame(BaseModel):
    """A game that inspired this design."""

    name: str = Field(..., description="Game name")
    relevance: str = Field(..., description="Why it's relevant")


class SpriteAsset(BaseModel):
    """A sprite or graphic asset."""

    name: str = Field(..., description="Asset name")
    dimensions: str = Field(..., description="Size (e.g., '32x32')")
    description: str = Field(..., description="What it represents")


class AudioAsset(BaseModel):
    """An audio asset."""

    name: str = Field(..., description="Asset name")
    format: str = Field(default="mp3", description="Audio format")
    description: str = Field(..., description="What it's for")


class GameDesignDocument(BaseModel):
    """Complete Game Design Document.

    This is the full specification for implementing the game,
    generated from a selected GameConcept.
    """

    # Metadata
    title: str = Field(..., description="Game title")
    version: str = Field(default="1.0", description="Document version")
    updated_at: datetime = Field(default_factory=datetime.now)

    # Section 1: Overview
    concept_summary: str = Field(..., description="Expanded concept summary")
    genre: str = Field(..., description="Game genre")
    platform: str = Field(default="Web (HTML5)", description="Target platform")
    target_audience: str = Field(..., description="Target audience description")
    unique_selling_points: list[str] = Field(..., description="Unique selling points")

    # Section 2: Gameplay
    core_game_loop: str = Field(..., description="Description of the core game loop")
    core_mechanics: list[CoreMechanic] = Field(..., description="Core mechanics")
    player_actions: list[PlayerAction] = Field(..., description="Player actions")
    win_condition: str = Field(..., description="How to win")
    loss_condition: str = Field(..., description="How to lose")
    progression_system: str = Field(..., description="How player progresses")
    difficulty_curve: str = Field(..., description="How difficulty increases")

    # Section 3: Game World
    setting: str = Field(..., description="Game setting/world")
    narrative: str = Field(..., description="Story/narrative summary")
    levels: list[Level] = Field(..., description="Level descriptions")

    # Section 4: Art & Audio
    visual_style: str = Field(..., description="Visual style description")
    art_direction: str = Field(..., description="Art direction guidelines")
    color_palette: list[ColorEntry] = Field(..., description="Color palette")
    audio_style: str = Field(..., description="Audio style description")
    sound_effects: list[SoundEffect] = Field(..., description="Sound effects list")
    music_description: str = Field(..., description="Music requirements")

    # Section 5: User Interface
    hud_elements: list[HUDElement] = Field(..., description="HUD elements")
    menu_flow: str = Field(..., description="Menu navigation description")
    ui_style_guide: str = Field(..., description="UI style guidelines")

    # Section 6: Technical Specifications
    engine: GameEngine = Field(default=GameEngine.PHASER, description="Game engine")
    resolution: str = Field(default="800x600", description="Target resolution")
    target_fps: int = Field(default=60, description="Target frame rate")
    max_load_time: str = Field(default="< 3 seconds", description="Max load time")
    memory_budget: str = Field(default="< 100MB", description="Memory budget")
    supported_platforms: list[str] = Field(
        default_factory=lambda: ["Chrome", "Firefox", "Safari", "Edge"],
        description="Supported browsers/platforms",
    )
    input_methods: list[str] = Field(
        default_factory=lambda: ["Keyboard", "Mouse"],
        description="Supported input methods",
    )

    # Section 7: Scope
    mvp_features: list[str] = Field(..., description="Must-have features for MVP")
    nice_to_have_features: list[str] = Field(
        default_factory=list, description="Nice-to-have features"
    )
    future_features: list[str] = Field(default_factory=list, description="Post-launch features")
    out_of_scope: list[str] = Field(default_factory=list, description="Explicitly excluded")

    # Section 8: References
    inspiration_games: list[InspirationGame] = Field(..., description="Inspiration games")
    art_references: list[str] = Field(default_factory=list, description="Art references")
    technical_references: list[str] = Field(
        default_factory=list, description="Technical references"
    )

    # Appendix A: Asset List
    sprite_assets: list[SpriteAsset] = Field(default_factory=list, description="Sprite assets")
    audio_assets: list[AudioAsset] = Field(default_factory=list, description="Audio assets")

    # Appendix B: Implementation Notes
    implementation_notes: str = Field(default="", description="Additional implementation notes")


# =============================================================================
# Technical Specification Schema
# =============================================================================


class FileStructure(BaseModel):
    """A file in the project structure."""

    path: str = Field(..., description="Relative file path")
    purpose: str = Field(..., description="What this file is for")


class Dependency(BaseModel):
    """A project dependency."""

    name: str = Field(..., description="Package name")
    version: str = Field(..., description="Version constraint")
    purpose: str = Field(..., description="Why it's needed")


class TechnicalSpecification(BaseModel):
    """Technical specification for game implementation.

    This bridges the GDD and the actual implementation,
    providing specific technical guidance for Claude Code.
    """

    # Project structure
    project_name: str = Field(..., description="Project directory name")
    engine: GameEngine = Field(..., description="Game engine")
    file_structure: list[FileStructure] = Field(..., description="Project file structure")

    # Dependencies
    dependencies: list[Dependency] = Field(..., description="Project dependencies")

    # Architecture
    scene_list: list[str] = Field(..., description="List of game scenes")
    main_classes: list[str] = Field(..., description="Main classes to implement")

    # Build configuration
    build_command: str = Field(default="npm run build", description="Build command")
    dev_command: str = Field(default="npm run dev", description="Dev server command")
    output_directory: str = Field(default="dist", description="Build output directory")

    # Implementation priorities
    implementation_order: list[str] = Field(..., description="Suggested order of implementation")

    # Notes
    technical_notes: str = Field(default="", description="Additional technical notes")


# =============================================================================
# Design Output Schema (combines all outputs)
# =============================================================================


class DesignOutput(BaseModel):
    """Complete output from the Design Agent.

    This is the full package of design artifacts produced
    by the DesignAgent.
    """

    # The selected concept (from the generated options)
    selected_concept: GameConcept = Field(..., description="The selected game concept")

    # All generated concepts (for reference)
    all_concepts: list[GameConcept] = Field(..., description="All generated concept variations")

    # Full GDD
    gdd: GameDesignDocument = Field(..., description="Complete Game Design Document")

    # Technical spec
    tech_spec: TechnicalSpecification = Field(..., description="Technical specification")

    # Metadata
    original_prompt: str = Field(..., description="The original user prompt")
    engine: GameEngine = Field(..., description="Selected game engine")


# =============================================================================
# JSON Schema Export
# =============================================================================


@lru_cache(maxsize=1)
def get_concept_schema() -> dict[str, Any]:
    """Get JSON Schema for GameConcept (cached).

    Returns:
        JSON Schema dictionary.
    """
    return GameConcept.model_json_schema()


@lru_cache(maxsize=1)
def get_gdd_schema() -> dict[str, Any]:
    """Get JSON Schema for GameDesignDocument (cached).

    Returns:
        JSON Schema dictionary.
    """
    return GameDesignDocument.model_json_schema()


@lru_cache(maxsize=1)
def get_tech_spec_schema() -> dict[str, Any]:
    """Get JSON Schema for TechnicalSpecification (cached).

    Returns:
        JSON Schema dictionary.
    """
    return TechnicalSpecification.model_json_schema()


@lru_cache(maxsize=1)
def get_design_output_schema() -> dict[str, Any]:
    """Get JSON Schema for DesignOutput (cached).

    Returns:
        JSON Schema dictionary.
    """
    return DesignOutput.model_json_schema()
