"""Design agent for game concept and GDD generation.

This agent generates game concepts and Game Design Documents (GDDs)
from user prompts using Claude's structured output capabilities.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from anthropic import Anthropic
from anthropic.types import Message, TextBlock

from game_workflow.agents.base import DEFAULT_MODEL, BaseAgent
from game_workflow.agents.schemas import (
    DesignOutput,
    GameConcept,
    GameDesignDocument,
    GameEngine,
    TechnicalSpecification,
    get_concept_schema,
    get_gdd_schema,
    get_tech_spec_schema,
)
from game_workflow.orchestrator.exceptions import AgentError
from game_workflow.utils.templates import render_concept, render_gdd

if TYPE_CHECKING:
    from game_workflow.orchestrator.state import WorkflowState

logger = logging.getLogger(__name__)


# System prompts for design generation
CONCEPT_GENERATION_PROMPT = """You are an expert game designer tasked with generating creative game concepts.

Given a user's prompt describing what kind of game they want, generate {num_concepts} distinct game concept variations.
Each concept should:
1. Be feasible to implement as a web game using {engine}
2. Have a unique core hook that differentiates it
3. Be scoped appropriately for a small indie game
4. Include specific, actionable details

Consider various interpretations of the prompt and explore different genres, art styles, and mechanics.
Be creative but practical - these games need to be implementable.

The user's prompt is: "{prompt}"

Generate {num_concepts} game concepts as a JSON array, following this schema for each:
{schema}

Important:
- Make each concept meaningfully different from the others
- Keep scope realistic for a solo developer / small team
- Consider both casual and more engaged players
- Include specific details, not vague descriptions
"""

GDD_GENERATION_PROMPT = """You are an expert game designer creating a complete Game Design Document.

Based on the following game concept, create a comprehensive GDD that a developer could use
to implement the game. Be specific and actionable.

Selected Concept:
{concept}

Target Engine: {engine}

Generate a complete Game Design Document following this schema:
{schema}

Important:
- Be specific about mechanics, not vague
- Include concrete examples where helpful
- Consider implementation feasibility for {engine}
- Define clear scope boundaries
- Include asset requirements
"""

TECH_SPEC_PROMPT = """You are a senior game developer creating a technical specification.

Based on the following Game Design Document, create a technical specification that will
guide the implementation. This should bridge the design and the code.

GDD Summary:
Title: {title}
Genre: {genre}
Engine: {engine}
Core Mechanics: {mechanics}

Generate a technical specification following this schema:
{schema}

Important:
- Use standard {engine} project structure
- List specific files needed
- Define clear implementation order
- Consider performance requirements
"""


class DesignAgent(BaseAgent):
    """Agent for generating game designs.

    This agent takes a game concept prompt and produces:
    - Multiple concept variations (3-5)
    - A complete Game Design Document (GDD) for the selected concept
    - A technical specification for implementation
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        state: WorkflowState | None = None,
        num_concepts: int = 3,
        output_dir: Path | None = None,
    ) -> None:
        """Initialize the design agent.

        Args:
            model: The Claude model to use.
            state: The workflow state for context.
            num_concepts: Number of concept variations to generate (1-5).
            output_dir: Directory to save design artifacts.
        """
        super().__init__(model=model, state=state)
        self.num_concepts = max(1, min(5, num_concepts))  # Clamp to 1-5
        self.output_dir = output_dir
        self._client: Anthropic | None = None

    @property
    def name(self) -> str:
        """Get the agent's name."""
        return "DesignAgent"

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
        prompt: str,
        engine: str = "phaser",
        selected_concept_index: int | None = None,
        **kwargs: Any,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Generate a game design from a prompt.

        Args:
            prompt: The game concept prompt from the user.
            engine: The target game engine ("phaser" or "godot").
            selected_concept_index: If provided, skip concept generation and
                use this index from previously generated concepts.
            **kwargs: Additional arguments.

        Returns:
            Dict containing:
                - status: "success" or "failed"
                - concepts: List of generated concepts
                - selected_concept: The chosen concept
                - gdd: The full Game Design Document
                - tech_spec: Technical specification
                - artifacts: Paths to saved files

        Raises:
            AgentError: If design generation fails.
        """
        self.log_info(f"Starting design generation for: {prompt[:50]}...")

        try:
            game_engine = GameEngine(engine.lower())
        except ValueError:
            game_engine = GameEngine.PHASER
            self.log_info(f"Unknown engine '{engine}', defaulting to Phaser")

        # Step 1: Generate concepts
        self.log_info(f"Generating {self.num_concepts} concept variations...")
        concepts = await self._generate_concepts(prompt, game_engine)

        if not concepts:
            raise AgentError(self.name, "Failed to generate any game concepts")

        self.log_info(f"Generated {len(concepts)} concepts")

        # Step 2: Select concept (for now, use first or specified index)
        if selected_concept_index is not None:
            idx = max(0, min(len(concepts) - 1, selected_concept_index))
        else:
            # Default to first concept (in production, this would go through approval)
            idx = 0

        selected = concepts[idx]
        self.log_info(f"Selected concept: {selected.title}")

        # Step 3: Generate full GDD
        self.log_info("Generating Game Design Document...")
        gdd = await self._generate_gdd(selected, game_engine)

        # Step 4: Generate technical specification
        self.log_info("Generating technical specification...")
        tech_spec = await self._generate_tech_spec(gdd, game_engine)

        # Step 5: Create complete output
        output = DesignOutput(
            selected_concept=selected,
            all_concepts=concepts,
            gdd=gdd,
            tech_spec=tech_spec,
            original_prompt=prompt,
            engine=game_engine,
        )

        # Step 6: Save artifacts
        artifacts = await self._save_artifacts(output)

        self.log_info("Design generation complete")

        return {
            "status": "success",
            "concepts": [c.model_dump() for c in concepts],
            "selected_concept": selected.model_dump(),
            "gdd": gdd.model_dump(),
            "tech_spec": tech_spec.model_dump(),
            "artifacts": artifacts,
        }

    async def _generate_concepts(self, prompt: str, engine: GameEngine) -> list[GameConcept]:
        """Generate multiple game concepts from a prompt.

        Args:
            prompt: The user's game concept prompt.
            engine: Target game engine.

        Returns:
            List of generated concepts.
        """
        schema = get_concept_schema()

        system_prompt = CONCEPT_GENERATION_PROMPT.format(
            num_concepts=self.num_concepts,
            engine=engine.value,
            prompt=prompt,
            schema=json.dumps(schema, indent=2),
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            messages=[
                {
                    "role": "user",
                    "content": f"Generate {self.num_concepts} distinct game concepts based on: '{prompt}'. Return as a JSON array.",
                }
            ],
            system=system_prompt,
        )

        # Extract text from response
        text = self._extract_text(response)

        # Parse JSON from response
        concepts = self._parse_concepts_response(text)

        # Validate and add metadata
        validated = []
        for i, concept_data in enumerate(concepts):
            concept_data["concept_number"] = i + 1
            concept_data["total_concepts"] = len(concepts)
            concept_data["generated_at"] = datetime.now().isoformat()

            try:
                concept = GameConcept.model_validate(concept_data)
                validated.append(concept)
            except Exception as e:
                self.log_error(f"Failed to validate concept {i + 1}: {e}")

        return validated

    async def _generate_gdd(self, concept: GameConcept, engine: GameEngine) -> GameDesignDocument:
        """Generate a full GDD from a concept.

        Args:
            concept: The selected game concept.
            engine: Target game engine.

        Returns:
            Complete Game Design Document.
        """
        schema = get_gdd_schema()

        system_prompt = GDD_GENERATION_PROMPT.format(
            concept=concept.model_dump_json(indent=2),
            engine=engine.value,
            schema=json.dumps(schema, indent=2),
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=16384,
            messages=[
                {
                    "role": "user",
                    "content": f"Create a complete Game Design Document for '{concept.title}'. Return as JSON.",
                }
            ],
            system=system_prompt,
        )

        text = self._extract_text(response)

        # Parse JSON
        gdd_data = self._parse_json_response(text)

        # Set defaults and validate
        gdd_data["title"] = concept.title
        gdd_data["engine"] = engine.value
        gdd_data["updated_at"] = datetime.now().isoformat()

        return GameDesignDocument.model_validate(gdd_data)

    async def _generate_tech_spec(
        self, gdd: GameDesignDocument, engine: GameEngine
    ) -> TechnicalSpecification:
        """Generate technical specification from GDD.

        Args:
            gdd: The Game Design Document.
            engine: Target game engine.

        Returns:
            Technical specification.
        """
        schema = get_tech_spec_schema()

        # Summarize mechanics for the prompt
        mechanics_summary = ", ".join(m.name for m in gdd.core_mechanics[:5])

        system_prompt = TECH_SPEC_PROMPT.format(
            title=gdd.title,
            genre=gdd.genre,
            engine=engine.value,
            mechanics=mechanics_summary,
            schema=json.dumps(schema, indent=2),
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            messages=[
                {
                    "role": "user",
                    "content": f"Create a technical specification for '{gdd.title}'. Return as JSON.",
                }
            ],
            system=system_prompt,
        )

        text = self._extract_text(response)

        # Parse JSON
        spec_data = self._parse_json_response(text)

        # Set required fields
        spec_data["project_name"] = gdd.title.lower().replace(" ", "-")
        spec_data["engine"] = engine.value

        return TechnicalSpecification.model_validate(spec_data)

    async def _save_artifacts(self, output: DesignOutput) -> dict[str, str]:
        """Save design artifacts to files.

        Args:
            output: The complete design output.

        Returns:
            Dictionary mapping artifact names to file paths.
        """
        if self.output_dir is None:
            if self.state:
                # Use state directory
                from game_workflow.config import get_settings

                settings = get_settings()
                self.output_dir = settings.workflow.state_dir / self.state.id / "design"
            else:
                # Use current directory
                self.output_dir = Path.cwd() / "design_output"

        self.output_dir.mkdir(parents=True, exist_ok=True)

        artifacts: dict[str, str] = {}

        # Save concept.json
        concept_path = self.output_dir / "concept.json"
        with concept_path.open("w") as f:
            json.dump(output.selected_concept.model_dump(mode="json"), f, indent=2, default=str)
        artifacts["concept"] = str(concept_path)
        self.log_debug(f"Saved concept to {concept_path}")

        # Save all_concepts.json
        all_concepts_path = self.output_dir / "all_concepts.json"
        with all_concepts_path.open("w") as f:
            json.dump(
                [c.model_dump(mode="json") for c in output.all_concepts],
                f,
                indent=2,
                default=str,
            )
        artifacts["all_concepts"] = str(all_concepts_path)

        # Save gdd.json
        gdd_json_path = self.output_dir / "gdd.json"
        with gdd_json_path.open("w") as f:
            json.dump(output.gdd.model_dump(mode="json"), f, indent=2, default=str)
        artifacts["gdd_json"] = str(gdd_json_path)

        # Save gdd.md (rendered)
        gdd_md_path = self.output_dir / "gdd.md"
        gdd_md = render_gdd(output.gdd.model_dump())
        gdd_md_path.write_text(gdd_md)
        artifacts["gdd"] = str(gdd_md_path)
        self.log_debug(f"Saved GDD to {gdd_md_path}")

        # Save concept.md (rendered) for the selected concept
        concept_md_path = self.output_dir / "concept.md"
        concept_md = render_concept(output.selected_concept.model_dump())
        concept_md_path.write_text(concept_md)
        artifacts["concept_md"] = str(concept_md_path)

        # Save tech-spec.json
        tech_spec_path = self.output_dir / "tech-spec.json"
        with tech_spec_path.open("w") as f:
            json.dump(output.tech_spec.model_dump(mode="json"), f, indent=2, default=str)
        artifacts["tech_spec"] = str(tech_spec_path)
        self.log_debug(f"Saved tech spec to {tech_spec_path}")

        # Add artifacts to state if available
        if self.state:
            for name, path in artifacts.items():
                self.add_artifact(name, path)

        return artifacts

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
            # Find the first newline and last ```
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

    def _parse_concepts_response(self, text: str) -> list[dict[str, Any]]:
        """Parse concepts array from a model response.

        Args:
            text: The response text.

        Returns:
            List of concept dictionaries.

        Raises:
            AgentError: If parsing fails.
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
            data = json.loads(text)
            if isinstance(data, list):
                result: list[dict[str, Any]] = data
                return result
            if isinstance(data, dict) and "concepts" in data:
                concepts: list[dict[str, Any]] = data["concepts"]
                return concepts
            return [data]
        except json.JSONDecodeError as e:
            # Try to find JSON array in the response
            start = text.find("[")
            end = text.rfind("]") + 1
            if start != -1 and end > start:
                try:
                    result = json.loads(text[start:end])
                    return result
                except json.JSONDecodeError:
                    pass

            raise AgentError(
                self.name,
                f"Failed to parse concepts response: {e}",
                cause=e,
            ) from e
