"""Tests for the agents module."""

from game_workflow.agents import (
    BuildAgent,
    DesignAgent,
    PublishAgent,
    QAAgent,
)


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
