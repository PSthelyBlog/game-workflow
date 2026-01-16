"""Template loading utilities.

This module provides functions for loading and rendering templates
for GDDs, concepts, and store pages.
"""

from pathlib import Path

# Package root directory
PACKAGE_ROOT = Path(__file__).parent.parent.parent.parent
TEMPLATES_DIR = PACKAGE_ROOT / "templates"


def load_template(name: str) -> str:
    """Load a template by name.

    Args:
        name: Template name (without extension).

    Returns:
        Template content as string.

    Raises:
        FileNotFoundError: If template doesn't exist.
    """
    template_path = TEMPLATES_DIR / f"{name}.md"

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {name}")

    return template_path.read_text()


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
