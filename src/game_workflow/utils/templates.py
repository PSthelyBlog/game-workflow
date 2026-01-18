"""Template loading and rendering utilities.

This module provides functions for loading and rendering Jinja2 templates
for GDDs, concepts, and store pages.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateNotFound

# Package root directory
PACKAGE_ROOT = Path(__file__).parent.parent.parent.parent
TEMPLATES_DIR = PACKAGE_ROOT / "templates"

# Jinja2 environment with strict mode for catching missing variables
_env: Environment | None = None


def _get_env() -> Environment:
    """Get or create the Jinja2 environment.

    Returns:
        Configured Jinja2 environment.
    """
    global _env
    if _env is None:
        _env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=False,  # We're generating markdown, not HTML
        )
        # Add custom filters
        _env.filters["datetime"] = _format_datetime
    return _env


def _format_datetime(value: datetime | str | None, fmt: str = "%Y-%m-%d %H:%M") -> str:
    """Format a datetime value.

    Args:
        value: Datetime or string to format.
        fmt: Format string.

    Returns:
        Formatted datetime string.
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return value.strftime(fmt)


def load_template(name: str) -> str:
    """Load a raw template by name.

    Args:
        name: Template name (without extension).

    Returns:
        Template content as raw string.

    Raises:
        FileNotFoundError: If template doesn't exist.
    """
    template_path = TEMPLATES_DIR / f"{name}.md"

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {name}")

    return template_path.read_text()


def render_template(name: str, context: dict[str, Any]) -> str:
    """Render a template with the given context.

    Args:
        name: Template name (with extension, e.g., "gdd-template.md").
        context: Dictionary of variables to pass to the template.

    Returns:
        Rendered template as string.

    Raises:
        FileNotFoundError: If template doesn't exist.
        jinja2.UndefinedError: If a required variable is missing.
    """
    env = _get_env()

    try:
        template = env.get_template(name)
    except TemplateNotFound as e:
        raise FileNotFoundError(f"Template not found: {name}") from e

    # Add default context values
    full_context = {
        "updated_at": datetime.now().strftime("%Y-%m-%d"),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        **context,
    }

    return template.render(full_context)


def render_gdd(gdd_data: dict[str, Any]) -> str:
    """Render a Game Design Document from structured data.

    Args:
        gdd_data: Dictionary containing GDD fields.

    Returns:
        Rendered GDD as markdown string.
    """
    return render_template("gdd-template.md", gdd_data)


def render_concept(concept_data: dict[str, Any]) -> str:
    """Render a game concept from structured data.

    Args:
        concept_data: Dictionary containing concept fields.

    Returns:
        Rendered concept as markdown string.
    """
    return render_template("concept-template.md", concept_data)


def render_itchio_page(page_data: dict[str, Any]) -> str:
    """Render an itch.io store page from structured data.

    Args:
        page_data: Dictionary containing itch.io page fields.

    Returns:
        Rendered itch.io page as markdown string.
    """
    return render_template("itchio-page.md", page_data)


def get_scaffold_path(engine: str) -> Path:
    """Get the path to a project scaffold.

    Args:
        engine: The game engine name.

    Returns:
        Path to the scaffold directory.

    Raises:
        ValueError: If engine is not supported.
    """
    scaffold_path = TEMPLATES_DIR / "scaffolds" / engine

    if not scaffold_path.exists():
        raise ValueError(f"Unsupported engine: {engine}")

    return scaffold_path


def list_templates() -> list[str]:
    """List all available templates.

    Returns:
        List of template names (without directory path).
    """
    return [f.name for f in TEMPLATES_DIR.glob("*.md")]


def validate_template_context(name: str, context: dict[str, Any]) -> list[str]:
    """Validate that a context has all required variables for a template.

    Note: This does a basic validation by attempting to render the template.
    For production use, you might want to parse the template AST.

    Args:
        name: Template name.
        context: Context to validate.

    Returns:
        List of missing variable names (empty if valid).
    """
    from jinja2 import UndefinedError

    env = _get_env()
    missing = []

    try:
        template = env.get_template(name)
        template.render(context)
    except TemplateNotFound as e:
        raise FileNotFoundError(f"Template not found: {name}") from e
    except UndefinedError as e:
        # Extract variable name from error message
        # e.g., "'variable_name' is undefined"
        error_msg = str(e)
        if "'" in error_msg:
            var_name = error_msg.split("'")[1]
            missing.append(var_name)

    return missing
