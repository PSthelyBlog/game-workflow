"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_prompt() -> str:
    """Provide a sample game prompt for testing."""
    return "Create a puzzle platformer about time manipulation"


@pytest.fixture
def sample_gdd_content() -> str:
    """Provide sample GDD content for testing."""
    return """# Game Design Document

## Overview
A puzzle platformer where the player can manipulate time.

## Mechanics
- Time rewind
- Time slow
- Time freeze zones
"""
