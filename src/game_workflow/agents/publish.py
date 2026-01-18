"""Publish agent for itch.io release preparation.

This agent prepares game builds for publishing to itch.io,
including generating store pages, marketing copy, and handling uploads.
"""

from __future__ import annotations

import json
import logging
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from anthropic import Anthropic
from anthropic.types import Message, TextBlock
from pydantic import BaseModel, Field

from game_workflow.agents.base import DEFAULT_MODEL, BaseAgent
from game_workflow.agents.schemas import GameDesignDocument
from game_workflow.orchestrator.exceptions import AgentError
from game_workflow.utils.templates import render_itchio_page

if TYPE_CHECKING:
    from pathlib import Path

    from game_workflow.orchestrator.state import WorkflowState

logger = logging.getLogger(__name__)


# =============================================================================
# Schemas for Publish Output
# =============================================================================


class ReleaseType(str, Enum):
    """Types of releases."""

    INITIAL = "initial"
    UPDATE = "update"
    PATCH = "patch"
    BETA = "beta"
    DEMO = "demo"


class ItchioClassification(str, Enum):
    """itch.io game classifications."""

    GAME = "game"
    TOOL = "tool"
    GAME_ASSETS = "game_assets"
    COMIC = "comic"
    BOOK = "book"
    SOUNDTRACK = "soundtrack"
    PHYSICAL_GAME = "physical_game"
    OTHER = "other"


class ItchioVisibility(str, Enum):
    """itch.io project visibility options."""

    DRAFT = "draft"
    RESTRICTED = "restricted"
    PUBLIC = "public"


class ControlMapping(BaseModel):
    """A control/input mapping for the game."""

    input: str = Field(..., description="The input (e.g., 'Arrow Keys', 'WASD')")
    action: str = Field(..., description="What the input does")


class FeatureHighlight(BaseModel):
    """A highlighted feature of the game."""

    name: str = Field(..., description="Feature name")
    description: str = Field(..., description="Feature description")


class Screenshot(BaseModel):
    """A screenshot entry."""

    filename: str = Field(..., description="Screenshot filename")
    url: str = Field(default="", description="URL or path to screenshot")
    caption: str = Field(..., description="Screenshot caption/alt text")
    description: str | None = Field(default=None, description="Optional longer description")


class Credit(BaseModel):
    """A credit entry."""

    role: str = Field(..., description="Role (e.g., 'Developer', 'Art')")
    name: str = Field(..., description="Name of the person/entity")
    link: str | None = Field(default=None, description="Optional link")


class TechnicalDetails(BaseModel):
    """Technical details for the store page."""

    resolution: str = Field(default="800x600", description="Game resolution")
    browser_support: list[str] = Field(
        default_factory=lambda: ["Chrome", "Firefox", "Safari", "Edge"],
        description="Supported browsers",
    )
    input_methods: list[str] = Field(
        default_factory=lambda: ["Keyboard", "Mouse"],
        description="Supported input methods",
    )
    save_support: bool = Field(default=False, description="Whether game supports saves")
    audio: bool = Field(default=True, description="Whether game has audio")


class VersionInfo(BaseModel):
    """Version information for the release."""

    current: str = Field(default="1.0.0", description="Current version")
    changelog: list[dict[str, str]] = Field(default_factory=list, description="Changelog entries")


class SupportInfo(BaseModel):
    """Support information for the store page."""

    message: str = Field(default="", description="Support message")
    links: list[dict[str, str]] = Field(default_factory=list, description="Support links")


class StorePageContent(BaseModel):
    """Complete itch.io store page content.

    This is the structured output from marketing copy generation.
    """

    # Required fields
    title: str = Field(..., description="Game title")
    tagline: str = Field(..., description="Short tagline (1 sentence)")
    description: str = Field(..., description="Main description (2-3 paragraphs)")
    features: list[str] = Field(..., description="List of key features")
    controls: list[ControlMapping] = Field(..., description="Control mappings")

    # Optional content
    story: str | None = Field(default=None, description="Story/narrative description")
    tips: list[str] = Field(default_factory=list, description="Tips for players")
    highlights: list[FeatureHighlight] = Field(
        default_factory=list, description="Feature highlights"
    )
    screenshots: list[Screenshot] = Field(default_factory=list, description="Screenshots")
    technical_details: TechnicalDetails = Field(
        default_factory=TechnicalDetails, description="Technical details"
    )

    # Metadata
    tags: list[str] = Field(default_factory=list, description="itch.io tags")
    engine: str = Field(default="Phaser.js", description="Game engine used")

    # Credits
    credits: list[Credit] = Field(default_factory=list, description="Credits")
    acknowledgments: str | None = Field(default=None, description="Acknowledgments")

    # Version
    version: VersionInfo = Field(default_factory=VersionInfo, description="Version info")

    # Support
    support: SupportInfo | None = Field(default=None, description="Support info")


class ReleaseArtifact(BaseModel):
    """A release artifact (build file)."""

    name: str = Field(..., description="Artifact name")
    path: str = Field(..., description="Path to artifact")
    size_bytes: int = Field(default=0, description="File size in bytes")
    checksum: str | None = Field(default=None, description="SHA256 checksum")


class GitHubRelease(BaseModel):
    """GitHub release information."""

    tag: str = Field(..., description="Git tag (e.g., 'v1.0.0')")
    name: str = Field(..., description="Release name")
    body: str = Field(..., description="Release notes markdown")
    prerelease: bool = Field(default=False, description="Is this a prerelease")
    draft: bool = Field(default=True, description="Is this a draft release")


class PublishOutput(BaseModel):
    """Complete output from the Publish Agent."""

    # Store page
    store_page: StorePageContent = Field(..., description="Store page content")
    store_page_markdown: str = Field(..., description="Rendered store page markdown")

    # Artifacts
    artifacts: list[ReleaseArtifact] = Field(..., description="Release artifacts")
    zip_path: str | None = Field(default=None, description="Path to the zip archive")

    # GitHub release (optional, may be created by MCP server)
    github_release: GitHubRelease | None = Field(default=None, description="GitHub release info")

    # itch.io settings
    itchio_project: str | None = Field(default=None, description="itch.io project slug")
    classification: ItchioClassification = Field(
        default=ItchioClassification.GAME, description="itch.io classification"
    )
    visibility: ItchioVisibility = Field(
        default=ItchioVisibility.DRAFT, description="Initial visibility"
    )

    # Metadata
    release_type: ReleaseType = Field(..., description="Type of release")
    version: str = Field(default="1.0.0", description="Version string")
    prepared_at: datetime = Field(default_factory=datetime.now, description="Preparation time")


# =============================================================================
# Dataclasses for internal use
# =============================================================================


@dataclass
class PublishConfig:
    """Configuration for the publish agent."""

    project_name: str
    version: str = "1.0.0"
    release_type: ReleaseType = ReleaseType.INITIAL
    visibility: ItchioVisibility = ItchioVisibility.DRAFT
    itchio_username: str | None = None
    github_repo: str | None = None
    create_github_release: bool = False
    screenshots_dir: Path | None = None
    additional_tags: list[str] = field(default_factory=list)


# =============================================================================
# System Prompts
# =============================================================================


MARKETING_COPY_PROMPT = """You are an expert game marketer and copywriter creating content for an itch.io store page.

Based on the following Game Design Document, create compelling marketing copy that will attract players.
Your copy should:
1. Be engaging and exciting without being hyperbolic
2. Clearly communicate what makes this game unique
3. Be honest about the game's scope (this is an indie/hobby game)
4. Include practical information players need

Game Design Document:
{gdd}

Generate store page content following this JSON schema:
{schema}

Important:
- The tagline should be punchy and memorable (under 80 characters)
- The description should hook players in the first paragraph
- Features should be specific and compelling
- Include 5-10 relevant itch.io tags (e.g., "puzzle", "platformer", "retro", "casual")
- Controls should be clear and complete
- If the game has a narrative, include a brief story tease
"""


# =============================================================================
# PublishAgent Implementation
# =============================================================================


class PublishAgent(BaseAgent):
    """Agent for publishing games to itch.io.

    This agent prepares releases including:
    - Generating store page content from GDD
    - Creating marketing copy
    - Packaging build artifacts
    - Preparing GitHub releases
    - Setting up itch.io project configuration
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        state: WorkflowState | None = None,
        output_dir: Path | None = None,
    ) -> None:
        """Initialize the publish agent.

        Args:
            model: The Claude model to use.
            state: The workflow state for context.
            output_dir: Directory to save publish artifacts.
        """
        super().__init__(model=model, state=state)
        self.output_dir = output_dir
        self._client: Anthropic | None = None

    @property
    def name(self) -> str:
        """Get the agent's name."""
        return "PublishAgent"

    @property
    def client(self) -> Anthropic:
        """Get or create the Anthropic client.

        Returns:
            Configured Anthropic client.

        Raises:
            AgentError: If API key is not configured.
        """
        if self._client is None:
            if not self.api_key:
                raise AgentError(
                    self.name,
                    "Anthropic API key not configured. Set ANTHROPIC_API_KEY.",
                )
            self._client = Anthropic(api_key=self.api_key)
        return self._client

    async def run(
        self,
        game_dir: Path,
        gdd_path: Path | None = None,
        gdd_data: dict[str, Any] | None = None,
        config: PublishConfig | None = None,
        **kwargs: Any,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Prepare a game for publishing to itch.io.

        Args:
            game_dir: Directory containing the built game (dist folder).
            gdd_path: Path to the GDD JSON file.
            gdd_data: GDD data as dictionary (alternative to gdd_path).
            config: Publishing configuration.
            **kwargs: Additional arguments.

        Returns:
            Dict containing:
                - status: "success" or "failed"
                - store_page: Store page content
                - artifacts: List of release artifacts
                - publish_output: Full PublishOutput object

        Raises:
            AgentError: If publishing preparation fails.
        """
        self.log_info("Starting publish preparation...")

        # Validate inputs
        if not game_dir.exists():
            raise AgentError(self.name, f"Game directory not found: {game_dir}")

        # Load GDD
        gdd = await self._load_gdd(gdd_path, gdd_data)

        # Create default config if not provided
        if config is None:
            project_slug = gdd.title.lower().replace(" ", "-").replace("'", "")
            config = PublishConfig(project_name=project_slug)

        # Setup output directory
        if self.output_dir is None:
            self.output_dir = game_dir.parent / "publish"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Generate marketing copy
        self.log_info("Generating marketing copy...")
        store_page = await self._generate_marketing_copy(gdd, config)

        # Step 2: Collect screenshots (if available)
        if config.screenshots_dir and config.screenshots_dir.exists():
            store_page = self._add_screenshots(store_page, config.screenshots_dir)

        # Step 3: Render store page markdown
        self.log_info("Rendering store page...")
        store_page_md = self._render_store_page(store_page)

        # Step 4: Package build artifacts
        self.log_info("Packaging build artifacts...")
        artifacts, zip_path = await self._package_artifacts(game_dir, config)

        # Step 5: Prepare GitHub release (metadata only)
        github_release = None
        if config.create_github_release:
            github_release = self._prepare_github_release(gdd, config, store_page)

        # Step 6: Create complete output
        output = PublishOutput(
            store_page=store_page,
            store_page_markdown=store_page_md,
            artifacts=artifacts,
            zip_path=str(zip_path) if zip_path else None,
            github_release=github_release,
            itchio_project=config.project_name,
            visibility=config.visibility,
            release_type=config.release_type,
            version=config.version,
        )

        # Step 7: Save artifacts
        artifacts_dict = await self._save_artifacts(output)

        self.log_info("Publish preparation complete")

        return {
            "status": "success",
            "store_page": store_page.model_dump(),
            "store_page_markdown": store_page_md,
            "artifacts": [a.model_dump() for a in artifacts],
            "zip_path": str(zip_path) if zip_path else None,
            "github_release": github_release.model_dump() if github_release else None,
            "saved_files": artifacts_dict,
            "publish_output": output.model_dump(mode="json"),
        }

    async def _load_gdd(
        self, gdd_path: Path | None, gdd_data: dict[str, Any] | None
    ) -> GameDesignDocument:
        """Load GDD from path or data.

        Args:
            gdd_path: Path to GDD JSON file.
            gdd_data: GDD data as dictionary.

        Returns:
            Validated GameDesignDocument.

        Raises:
            AgentError: If GDD cannot be loaded.
        """
        if gdd_data is not None:
            return GameDesignDocument.model_validate(gdd_data)

        if gdd_path is None:
            raise AgentError(self.name, "Either gdd_path or gdd_data must be provided")

        if not gdd_path.exists():
            raise AgentError(self.name, f"GDD file not found: {gdd_path}")

        try:
            with gdd_path.open() as f:
                data: dict[str, Any] = json.load(f)
            return GameDesignDocument.model_validate(data)
        except json.JSONDecodeError as e:
            raise AgentError(self.name, f"Failed to parse GDD JSON: {e}", cause=e) from e
        except Exception as e:
            raise AgentError(self.name, f"Failed to load GDD: {e}", cause=e) from e

    async def _generate_marketing_copy(
        self, gdd: GameDesignDocument, config: PublishConfig
    ) -> StorePageContent:
        """Generate marketing copy from GDD.

        Args:
            gdd: The Game Design Document.
            config: Publishing configuration.

        Returns:
            Store page content.
        """
        schema = StorePageContent.model_json_schema()

        # Create a summary of the GDD for the prompt
        gdd_summary = self._summarize_gdd(gdd)

        system_prompt = MARKETING_COPY_PROMPT.format(
            gdd=gdd_summary,
            schema=json.dumps(schema, indent=2),
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            messages=[
                {
                    "role": "user",
                    "content": f"Create itch.io store page content for '{gdd.title}'. Return as JSON.",
                }
            ],
            system=system_prompt,
        )

        text = self._extract_text(response)
        page_data = self._parse_json_response(text)

        # Set defaults and merge with config
        page_data["title"] = gdd.title
        page_data["engine"] = gdd.engine.value.capitalize()

        # Add additional tags from config
        if config.additional_tags:
            existing_tags = page_data.get("tags", [])
            page_data["tags"] = list(set(existing_tags + config.additional_tags))

        # Set version
        page_data["version"] = {"current": config.version, "changelog": []}

        # Extract technical details from GDD
        page_data["technical_details"] = {
            "resolution": gdd.resolution,
            "browser_support": gdd.supported_platforms,
            "input_methods": gdd.input_methods,
            "save_support": False,  # Default
            "audio": bool(gdd.sound_effects or gdd.music_description),
        }

        return StorePageContent.model_validate(page_data)

    def _summarize_gdd(self, gdd: GameDesignDocument) -> str:
        """Create a summary of the GDD for the marketing prompt.

        Args:
            gdd: The Game Design Document.

        Returns:
            Summary string.
        """
        mechanics = ", ".join(m.name for m in gdd.core_mechanics[:5])
        features = "\n".join(f"- {f}" for f in gdd.mvp_features[:10])
        usps = "\n".join(f"- {u}" for u in gdd.unique_selling_points[:5])

        return f"""Title: {gdd.title}
Genre: {gdd.genre}
Visual Style: {gdd.visual_style}
Target Audience: {gdd.target_audience}

Concept Summary:
{gdd.concept_summary}

Core Mechanics: {mechanics}

Core Game Loop:
{gdd.core_game_loop}

Win Condition: {gdd.win_condition}
Loss Condition: {gdd.loss_condition}

Setting: {gdd.setting}
Narrative: {gdd.narrative}

Unique Selling Points:
{usps}

Key Features:
{features}
"""

    def _add_screenshots(
        self, store_page: StorePageContent, screenshots_dir: Path
    ) -> StorePageContent:
        """Add screenshots to store page content.

        Args:
            store_page: Existing store page content.
            screenshots_dir: Directory containing screenshots.

        Returns:
            Updated store page content with screenshots.
        """
        screenshots: list[Screenshot] = []

        # Look for common screenshot formats
        for pattern in ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.webp"]:
            for img_path in screenshots_dir.glob(pattern):
                screenshot = Screenshot(
                    filename=img_path.name,
                    url=str(img_path),
                    caption=img_path.stem.replace("-", " ").replace("_", " ").title(),
                )
                screenshots.append(screenshot)

        # Sort by filename for consistent ordering
        screenshots.sort(key=lambda s: s.filename)

        # Update store page
        store_page.screenshots = screenshots[:10]  # Limit to 10 screenshots

        return store_page

    def _render_store_page(self, store_page: StorePageContent) -> str:
        """Render the store page to markdown.

        Args:
            store_page: Store page content.

        Returns:
            Rendered markdown string.
        """
        # Convert to dict for template rendering
        page_data = store_page.model_dump()

        # Convert controls to list of dicts for template
        if page_data.get("controls"):
            page_data["controls"] = [
                {"input": c["input"], "action": c["action"]} for c in page_data["controls"]
            ]

        return render_itchio_page(page_data)

    async def _package_artifacts(
        self, game_dir: Path, config: PublishConfig
    ) -> tuple[list[ReleaseArtifact], Path | None]:
        """Package build artifacts for release.

        Args:
            game_dir: Directory containing the built game.
            config: Publishing configuration.

        Returns:
            Tuple of (list of artifacts, path to zip file).
        """
        artifacts: list[ReleaseArtifact] = []

        # Find all files in the game directory
        for file_path in game_dir.rglob("*"):
            if file_path.is_file():
                artifact = ReleaseArtifact(
                    name=file_path.name,
                    path=str(file_path),
                    size_bytes=file_path.stat().st_size,
                )
                artifacts.append(artifact)

        # Create a zip archive
        zip_name = f"{config.project_name}-v{config.version}.zip"
        zip_path = self.output_dir / zip_name if self.output_dir else game_dir.parent / zip_name

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in game_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(game_dir)
                    zf.write(file_path, arcname)

        # Add the zip as an artifact
        zip_artifact = ReleaseArtifact(
            name=zip_name,
            path=str(zip_path),
            size_bytes=zip_path.stat().st_size,
        )
        artifacts.append(zip_artifact)

        self.log_info(f"Created zip archive: {zip_path} ({zip_artifact.size_bytes} bytes)")

        return artifacts, zip_path

    def _prepare_github_release(
        self,
        gdd: GameDesignDocument,
        config: PublishConfig,
        store_page: StorePageContent,
    ) -> GitHubRelease:
        """Prepare GitHub release metadata.

        Args:
            gdd: The Game Design Document.
            config: Publishing configuration.
            store_page: Store page content for release notes.

        Returns:
            GitHub release information.
        """
        tag = f"v{config.version}"

        # Create release notes
        features_list = "\n".join(f"- {f}" for f in store_page.features[:10])

        body = f"""# {gdd.title} {tag}

{store_page.tagline}

## What's New

This is the {"initial release" if config.release_type == ReleaseType.INITIAL else config.release_type.value} of {gdd.title}.

## Features

{features_list}

## Play Now

[Play on itch.io](https://itch.io)

---

Built with {gdd.engine.value.capitalize()} | Generated by Game Workflow Automation
"""

        return GitHubRelease(
            tag=tag,
            name=f"{gdd.title} {tag}",
            body=body,
            prerelease=config.release_type in (ReleaseType.BETA, ReleaseType.DEMO),
            draft=True,  # Always create as draft for review
        )

    async def _save_artifacts(self, output: PublishOutput) -> dict[str, str]:
        """Save publish artifacts to files.

        Args:
            output: The complete publish output.

        Returns:
            Dictionary mapping artifact names to file paths.
        """
        if self.output_dir is None:
            raise AgentError(self.name, "Output directory not set")

        saved: dict[str, str] = {}

        # Save store page markdown
        store_page_path = self.output_dir / "store-page.md"
        store_page_path.write_text(output.store_page_markdown)
        saved["store_page_md"] = str(store_page_path)

        # Save store page JSON
        store_page_json_path = self.output_dir / "store-page.json"
        with store_page_json_path.open("w") as f:
            json.dump(output.store_page.model_dump(mode="json"), f, indent=2, default=str)
        saved["store_page_json"] = str(store_page_json_path)

        # Save complete publish output
        output_path = self.output_dir / "publish-output.json"
        with output_path.open("w") as f:
            json.dump(output.model_dump(mode="json"), f, indent=2, default=str)
        saved["publish_output"] = str(output_path)

        # Save GitHub release notes if present
        if output.github_release:
            release_notes_path = self.output_dir / "release-notes.md"
            release_notes_path.write_text(output.github_release.body)
            saved["release_notes"] = str(release_notes_path)

        # Add artifacts to state if available
        if self.state:
            for name, path in saved.items():
                self.add_artifact(name, path)

        self.log_debug(f"Saved {len(saved)} publish artifacts to {self.output_dir}")

        return saved

    def _extract_text(self, response: Message) -> str:
        """Extract text content from an API response.

        Args:
            response: The API response message.

        Returns:
            The text content, or empty string if no text block found.
        """
        if not response.content:
            return ""
        for block in response.content:
            if isinstance(block, TextBlock):
                return block.text
        return ""

    def _parse_json_response(self, text: str) -> dict[str, Any]:
        """Parse JSON from a model response.

        Handles cases where the JSON might be wrapped in markdown code blocks.

        Args:
            text: The response text.

        Returns:
            Parsed JSON as dictionary.

        Raises:
            AgentError: If JSON parsing fails.
        """
        # Strip markdown code blocks if present
        text = text.strip()
        if text.startswith("```"):
            first_newline = text.find("\n")
            if first_newline != -1:
                text = text[first_newline + 1 :]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

        try:
            result: dict[str, Any] = json.loads(text)
            return result
        except json.JSONDecodeError as e:
            # Try to find JSON in the response
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    result = json.loads(text[start:end])
                    return result
                except json.JSONDecodeError:
                    pass

            raise AgentError(
                self.name,
                f"Failed to parse JSON response: {e}",
                cause=e,
            ) from e


# =============================================================================
# Helper Functions
# =============================================================================


def get_store_page_schema() -> dict[str, Any]:
    """Get JSON Schema for StorePageContent.

    Returns:
        JSON Schema dictionary.
    """
    return StorePageContent.model_json_schema()


def get_publish_output_schema() -> dict[str, Any]:
    """Get JSON Schema for PublishOutput.

    Returns:
        JSON Schema dictionary.
    """
    return PublishOutput.model_json_schema()
