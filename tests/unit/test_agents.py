"""Tests for the agents module."""

from pathlib import Path
from unittest.mock import patch

import pytest

from game_workflow.agents import (
    BuildAgent,
    DesignAgent,
    PublishAgent,
    QAAgent,
)
from game_workflow.orchestrator.exceptions import AgentError


class TestAgentNames:
    """Tests for agent name properties."""

    def test_design_agent_name(self) -> None:
        """Test DesignAgent name."""
        agent = DesignAgent()
        assert agent.name == "DesignAgent"

    def test_build_agent_name(self) -> None:
        """Test BuildAgent name."""
        agent = BuildAgent()
        assert agent.name == "BuildAgent"

    def test_qa_agent_name(self) -> None:
        """Test QAAgent name."""
        agent = QAAgent()
        assert agent.name == "QAAgent"

    def test_publish_agent_name(self) -> None:
        """Test PublishAgent name."""
        agent = PublishAgent()
        assert agent.name == "PublishAgent"


class TestAgentModel:
    """Tests for agent model configuration."""

    def test_default_model(self) -> None:
        """Test agents use default model."""
        agent = DesignAgent()
        assert agent.model == "claude-sonnet-4-5-20250929"

    def test_custom_model(self) -> None:
        """Test agents accept custom model."""
        agent = DesignAgent(model="claude-3-opus-20240229")
        assert agent.model == "claude-3-opus-20240229"


class TestDesignAgentBasics:
    """Basic tests for DesignAgent."""

    def test_num_concepts_clamped_low(self) -> None:
        """Test num_concepts is clamped to minimum 1."""
        agent = DesignAgent(num_concepts=0)
        assert agent.num_concepts == 1

    def test_num_concepts_clamped_high(self) -> None:
        """Test num_concepts is clamped to maximum 5."""
        agent = DesignAgent(num_concepts=10)
        assert agent.num_concepts == 5

    def test_num_concepts_valid(self) -> None:
        """Test valid num_concepts values are accepted."""
        agent = DesignAgent(num_concepts=3)
        assert agent.num_concepts == 3

    def test_output_dir_custom(self, tmp_path: Path) -> None:
        """Test custom output directory is set."""
        agent = DesignAgent(output_dir=tmp_path)
        assert agent.output_dir == tmp_path

    def test_output_dir_default(self) -> None:
        """Test default output directory is None."""
        agent = DesignAgent()
        assert agent.output_dir is None


class TestDesignAgentAPIKey:
    """Tests for API key handling."""

    def test_client_requires_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that client property raises without API key."""
        # Clear API key
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        from game_workflow.config import reload_settings

        reload_settings()

        agent = DesignAgent()
        with pytest.raises(AgentError, match="API key"):
            _ = agent.client

    def test_client_creates_with_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that client is created with API key."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from game_workflow.config import reload_settings

        reload_settings()

        with patch("game_workflow.agents.design.Anthropic") as mock_anthropic:
            agent = DesignAgent()
            _ = agent.client
            mock_anthropic.assert_called_once_with(api_key="test-key")


class TestDesignAgentParsing:
    """Tests for JSON parsing utilities."""

    def test_parse_json_clean(self) -> None:
        """Test parsing clean JSON."""
        agent = DesignAgent()
        result = agent._parse_json_response('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_json_markdown_block(self) -> None:
        """Test parsing JSON in markdown code block."""
        agent = DesignAgent()
        result = agent._parse_json_response('```json\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_parse_json_with_surrounding_text(self) -> None:
        """Test parsing JSON with text around it."""
        agent = DesignAgent()
        result = agent._parse_json_response('Here: {"key": "value"} Done.')
        assert result == {"key": "value"}

    def test_parse_json_invalid(self) -> None:
        """Test parsing invalid JSON raises error."""
        agent = DesignAgent()
        with pytest.raises(AgentError, match="Failed to parse"):
            agent._parse_json_response("not json at all")

    def test_parse_concepts_array(self) -> None:
        """Test parsing array of concepts."""
        agent = DesignAgent()
        result = agent._parse_concepts_response('[{"title": "A"}, {"title": "B"}]')
        assert len(result) == 2
        assert result[0]["title"] == "A"

    def test_parse_concepts_wrapped(self) -> None:
        """Test parsing concepts wrapped in object."""
        agent = DesignAgent()
        result = agent._parse_concepts_response('{"concepts": [{"title": "A"}]}')
        assert len(result) == 1
        assert result[0]["title"] == "A"

    def test_parse_concepts_single(self) -> None:
        """Test parsing single concept returns list."""
        agent = DesignAgent()
        result = agent._parse_concepts_response('{"title": "Single"}')
        assert len(result) == 1
        assert result[0]["title"] == "Single"
