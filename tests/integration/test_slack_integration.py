"""Integration tests for Slack approval hook.

These tests require a valid SLACK_BOT_TOKEN environment variable
and access to a test Slack workspace.

Run with: pytest tests/integration/test_slack_integration.py -v
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

import pytest

# Import directly from the module to avoid circular import
from game_workflow.hooks.slack_approval import (
    ApprovalRequest,
    ApprovalStatus,
    SlackApprovalHook,
    SlackClient,
)


class TestSlackClient:
    """Unit tests for SlackClient (mocked)."""

    def test_init_default_token(self) -> None:
        """Test initialization with default token from env."""
        with patch.dict(os.environ, {"SLACK_BOT_TOKEN": "xoxb-test-token"}):
            client = SlackClient()
            assert client.token == "xoxb-test-token"

    def test_init_custom_token(self) -> None:
        """Test initialization with custom token."""
        client = SlackClient(token="custom-token")
        assert client.token == "custom-token"

    def test_init_custom_timeout(self) -> None:
        """Test initialization with custom timeout."""
        client = SlackClient(timeout=60.0)
        assert client.timeout == 60.0

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Test async context manager creates and closes client."""
        async with SlackClient(token="test-token") as client:
            assert client._client is not None
        assert client._client is None

    @pytest.mark.asyncio
    async def test_client_property(self) -> None:
        """Test client property creates client if needed."""
        client = SlackClient(token="test-token")
        assert client._client is None
        _ = client.client
        assert client._client is not None
        await client.close()


class TestSlackApprovalHook:
    """Tests for SlackApprovalHook."""

    def test_init_defaults(self) -> None:
        """Test initialization with defaults."""
        hook = SlackApprovalHook()
        assert hook.channel == "#game-dev"
        assert hook.poll_interval == 5.0
        assert hook.require_thread_reply is False

    def test_init_custom_channel(self) -> None:
        """Test initialization with custom channel."""
        hook = SlackApprovalHook(channel="#custom-channel")
        assert hook.channel == "#custom-channel"

    def test_init_require_thread_reply(self) -> None:
        """Test initialization with thread reply requirement."""
        hook = SlackApprovalHook(require_thread_reply=True)
        assert hook.require_thread_reply is True

    def test_create_approval_blocks(self) -> None:
        """Test approval blocks creation."""
        hook = SlackApprovalHook()
        blocks = hook._create_approval_blocks("Test message")

        # Should have header, section, divider, context
        assert len(blocks) >= 4
        assert blocks[0]["type"] == "header"
        assert "Approval Required" in blocks[0]["text"]["text"]

    def test_create_approval_blocks_with_context(self) -> None:
        """Test approval blocks with context dict."""
        hook = SlackApprovalHook()
        blocks = hook._create_approval_blocks(
            "Test message",
            context={"Game": "My Game", "Version": "1.0.0"},
        )

        # Should include context section
        context_found = False
        for block in blocks:
            if block["type"] == "section":
                text = block.get("text", {}).get("text", "")
                if "Game" in text and "My Game" in text:
                    context_found = True
                    break
        assert context_found

    def test_create_approval_blocks_with_request_id(self) -> None:
        """Test approval blocks with request ID."""
        hook = SlackApprovalHook()
        blocks = hook._create_approval_blocks("Test message", request_id="abc123")

        # Should include request ID in context
        request_id_found = False
        for block in blocks:
            if block["type"] == "context":
                for element in block.get("elements", []):
                    if "abc123" in element.get("text", ""):
                        request_id_found = True
                        break
        assert request_id_found

    def test_create_approval_blocks_thread_reply_instruction(self) -> None:
        """Test approval blocks have thread reply instructions when required."""
        hook = SlackApprovalHook(require_thread_reply=True)
        blocks = hook._create_approval_blocks("Test message")

        # Should have thread reply instructions
        instruction_found = False
        for block in blocks:
            if block["type"] == "context":
                for element in block.get("elements", []):
                    if "Reply to this thread" in element.get("text", ""):
                        instruction_found = True
                        break
        assert instruction_found

    def test_create_response_blocks_approved(self) -> None:
        """Test response blocks for approved status."""
        hook = SlackApprovalHook()
        blocks = hook._create_response_blocks(
            "Original message",
            ApprovalStatus.APPROVED,
            responder="U12345",
        )

        assert len(blocks) >= 2
        assert "Approved" in blocks[0]["text"]["text"]
        assert "white_check_mark" in blocks[0]["text"]["text"]

    def test_create_response_blocks_rejected(self) -> None:
        """Test response blocks for rejected status."""
        hook = SlackApprovalHook()
        blocks = hook._create_response_blocks(
            "Original message",
            ApprovalStatus.REJECTED,
            responder="U12345",
            feedback="Not ready yet",
        )

        assert len(blocks) >= 3
        assert "Rejected" in blocks[0]["text"]["text"]
        # Should include feedback
        feedback_found = False
        for block in blocks:
            if "Feedback" in str(block):
                feedback_found = True
                break
        assert feedback_found

    def test_check_reactions_approve(self) -> None:
        """Test checking reactions for approval."""
        hook = SlackApprovalHook()
        reactions = [{"name": "white_check_mark", "users": ["U12345"]}]
        status, responder = hook._check_reactions(reactions)
        assert status == ApprovalStatus.APPROVED
        assert responder == "U12345"

    def test_check_reactions_reject(self) -> None:
        """Test checking reactions for rejection."""
        hook = SlackApprovalHook()
        reactions = [{"name": "x", "users": ["U12345"]}]
        status, responder = hook._check_reactions(reactions)
        assert status == ApprovalStatus.REJECTED
        assert responder == "U12345"

    def test_check_reactions_thumbsup(self) -> None:
        """Test checking thumbsup reaction."""
        hook = SlackApprovalHook()
        reactions = [{"name": "thumbsup", "users": ["U12345"]}]
        status, _responder = hook._check_reactions(reactions)
        assert status == ApprovalStatus.APPROVED

    def test_check_reactions_no_users(self) -> None:
        """Test checking reactions with no users."""
        hook = SlackApprovalHook()
        reactions = [{"name": "white_check_mark", "users": []}]
        status, responder = hook._check_reactions(reactions)
        assert status is None
        assert responder is None

    def test_check_reactions_unknown(self) -> None:
        """Test checking reactions with unknown emoji."""
        hook = SlackApprovalHook()
        reactions = [{"name": "smile", "users": ["U12345"]}]
        status, responder = hook._check_reactions(reactions)
        assert status is None
        assert responder is None

    def test_check_reactions_empty(self) -> None:
        """Test checking empty reactions."""
        hook = SlackApprovalHook()
        status, responder = hook._check_reactions([])
        assert status is None
        assert responder is None

    def test_check_replies_approve(self) -> None:
        """Test checking replies for approval."""
        hook = SlackApprovalHook()
        replies = [{"text": "approve", "user": "U12345"}]
        status, responder, feedback = hook._check_replies(replies)
        assert status == ApprovalStatus.APPROVED
        assert responder == "U12345"
        assert feedback is None

    def test_check_replies_approve_with_feedback(self) -> None:
        """Test checking replies for approval with feedback."""
        hook = SlackApprovalHook()
        replies = [{"text": "approve looks good!", "user": "U12345"}]
        status, responder, feedback = hook._check_replies(replies)
        assert status == ApprovalStatus.APPROVED
        assert responder == "U12345"
        assert feedback == "looks good!"

    def test_check_replies_reject(self) -> None:
        """Test checking replies for rejection."""
        hook = SlackApprovalHook()
        replies = [{"text": "reject", "user": "U12345"}]
        status, responder, _feedback = hook._check_replies(replies)
        assert status == ApprovalStatus.REJECTED
        assert responder == "U12345"

    def test_check_replies_reject_with_feedback(self) -> None:
        """Test checking replies for rejection with feedback."""
        hook = SlackApprovalHook()
        replies = [{"text": "reject needs more testing", "user": "U12345"}]
        status, _responder, feedback = hook._check_replies(replies)
        assert status == ApprovalStatus.REJECTED
        assert feedback == "needs more testing"

    def test_check_replies_yes(self) -> None:
        """Test checking replies with 'yes'."""
        hook = SlackApprovalHook()
        replies = [{"text": "yes", "user": "U12345"}]
        status, _responder, _feedback = hook._check_replies(replies)
        assert status == ApprovalStatus.APPROVED

    def test_check_replies_lgtm(self) -> None:
        """Test checking replies with 'lgtm'."""
        hook = SlackApprovalHook()
        replies = [{"text": "lgtm", "user": "U12345"}]
        status, _responder, _feedback = hook._check_replies(replies)
        assert status == ApprovalStatus.APPROVED

    def test_check_replies_no(self) -> None:
        """Test checking replies with 'no'."""
        hook = SlackApprovalHook()
        replies = [{"text": "no", "user": "U12345"}]
        status, _responder, _feedback = hook._check_replies(replies)
        assert status == ApprovalStatus.REJECTED

    def test_check_replies_stop(self) -> None:
        """Test checking replies with 'stop'."""
        hook = SlackApprovalHook()
        replies = [{"text": "stop", "user": "U12345"}]
        status, _responder, _feedback = hook._check_replies(replies)
        assert status == ApprovalStatus.REJECTED

    def test_check_replies_empty(self) -> None:
        """Test checking empty replies."""
        hook = SlackApprovalHook()
        status, responder, feedback = hook._check_replies([])
        assert status is None
        assert responder is None
        assert feedback is None

    def test_check_replies_unknown(self) -> None:
        """Test checking replies with unknown text."""
        hook = SlackApprovalHook()
        replies = [{"text": "maybe later", "user": "U12345"}]
        status, _responder, _feedback = hook._check_replies(replies)
        assert status is None

    def test_check_replies_no_user(self) -> None:
        """Test checking replies with no user."""
        hook = SlackApprovalHook()
        replies = [{"text": "approve", "user": ""}]
        status, _responder, _feedback = hook._check_replies(replies)
        assert status is None

    def test_check_replies_case_insensitive(self) -> None:
        """Test checking replies is case insensitive."""
        hook = SlackApprovalHook()
        replies = [{"text": "APPROVE", "user": "U12345"}]
        status, _responder, _feedback = hook._check_replies(replies)
        assert status == ApprovalStatus.APPROVED


class TestApprovalRequest:
    """Tests for ApprovalRequest dataclass."""

    def test_default_values(self) -> None:
        """Test ApprovalRequest has correct defaults."""
        request = ApprovalRequest(
            id="abc123",
            channel="C12345",
            message="Test message",
        )
        assert request.status == ApprovalStatus.PENDING
        assert request.responded_at is None
        assert request.responder is None
        assert request.feedback is None


class TestApprovalStatus:
    """Tests for ApprovalStatus enum."""

    def test_status_values(self) -> None:
        """Test status enum values."""
        assert ApprovalStatus.PENDING == "pending"
        assert ApprovalStatus.APPROVED == "approved"
        assert ApprovalStatus.REJECTED == "rejected"
        assert ApprovalStatus.EXPIRED == "expired"


class TestSlackApprovalHookIntegration:
    """Integration tests that mock the Slack API."""

    @pytest.mark.asyncio
    async def test_send_notification_success(self) -> None:
        """Test sending notification successfully."""
        hook = SlackApprovalHook(channel="#test-channel", token="test-token")

        with patch.object(SlackClient, "post_message", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = {"ok": True, "ts": "123.456"}

            result = await hook.send_notification(
                "Test notification",
                context={"key": "value"},
                level="info",
            )

            assert result is True
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_notification_failure(self) -> None:
        """Test sending notification when it fails."""
        hook = SlackApprovalHook(channel="#test-channel", token="test-token")

        with patch.object(SlackClient, "post_message", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = RuntimeError("API Error")

            result = await hook.send_notification("Test notification")

            assert result is False

    @pytest.mark.asyncio
    async def test_send_notification_different_levels(self) -> None:
        """Test sending notifications with different levels."""
        hook = SlackApprovalHook(channel="#test-channel", token="test-token")

        levels = ["info", "warning", "error", "success"]

        for level in levels:
            with patch.object(SlackClient, "post_message", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = {"ok": True, "ts": "123.456"}

                result = await hook.send_notification(
                    f"Test {level}",
                    level=level,
                )

                assert result is True


@pytest.mark.skipif(
    not os.environ.get("SLACK_BOT_TOKEN"),
    reason="SLACK_BOT_TOKEN not set - skipping real Slack integration tests",
)
class TestSlackRealIntegration:
    """Real integration tests with Slack.

    These tests only run when SLACK_BOT_TOKEN is set.
    They test actual API connectivity.
    """

    @pytest.mark.asyncio
    async def test_auth_test(self) -> None:
        """Test Slack authentication."""
        async with SlackClient() as client:
            result = await client.test_auth()
            assert result is not None
            assert result.get("ok") is True

    @pytest.mark.asyncio
    async def test_post_and_get_reactions(self) -> None:
        """Test posting a message and getting reactions."""
        channel = os.environ.get("SLACK_CHANNEL", "#game-dev-test")

        async with SlackClient() as client:
            # Post a test message
            result = await client.post_message(
                channel=channel,
                text="Integration test message (will be deleted)",
            )

            assert result.get("ok") is True
            ts = result.get("ts")
            assert ts is not None

            # Get reactions (should be empty initially)
            reactions = await client.get_reactions(result.get("channel"), ts)
            assert isinstance(reactions, list)
