"""Slack approval hook for human-in-the-loop gates.

This hook sends approval requests to Slack and waits for
human confirmation before proceeding.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, ClassVar

import httpx

from game_workflow.orchestrator.exceptions import (
    ApprovalRejectedError,
    ApprovalTimeoutError,
)

logger = logging.getLogger(__name__)


class ApprovalStatus(str, Enum):
    """Status of an approval request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class ApprovalRequest:
    """Represents an approval request."""

    id: str
    channel: str
    message: str
    context: dict[str, Any] | None = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: float = field(default_factory=time.time)
    responded_at: float | None = None
    responder: str | None = None
    feedback: str | None = None
    thread_ts: str | None = None
    message_ts: str | None = None


@dataclass
class SlackMessage:
    """Represents a Slack message."""

    channel: str
    ts: str
    text: str | None = None
    user: str | None = None
    thread_ts: str | None = None
    reactions: list[dict[str, Any]] = field(default_factory=list)


class SlackClient:
    """Async client for Slack API.

    Uses Slack Web API for sending messages and checking reactions.
    """

    BASE_URL = "https://slack.com/api"

    def __init__(
        self,
        token: str | None = None,
        *,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the Slack client.

        Args:
            token: Slack bot token. If None, uses SLACK_BOT_TOKEN env var.
            timeout: Request timeout in seconds.
        """
        self.token = token or os.environ.get("SLACK_BOT_TOKEN", "")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> SlackClient:
        """Enter async context."""
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=self.timeout,
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit async context."""
        await self.close()

    @property
    def client(self) -> httpx.AsyncClient:
        """Get the HTTP client, creating if necessary."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=self.timeout,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make a Slack API request.

        Args:
            method: HTTP method.
            endpoint: API endpoint.
            **kwargs: Additional arguments for httpx.

        Returns:
            API response data.

        Raises:
            RuntimeError: If the request fails.
        """
        try:
            response = await self.client.request(method, endpoint, **kwargs)
            data = response.json()

            if not data.get("ok"):
                error = data.get("error", "Unknown error")
                raise RuntimeError(f"Slack API error: {error}")

            return data

        except httpx.HTTPError as e:
            raise RuntimeError(f"Slack request failed: {e}") from e

    async def post_message(
        self,
        channel: str,
        text: str,
        *,
        blocks: list[dict[str, Any]] | None = None,
        thread_ts: str | None = None,
        unfurl_links: bool = False,
    ) -> dict[str, Any]:
        """Post a message to a Slack channel.

        Args:
            channel: Channel ID or name.
            text: Message text (fallback for notifications).
            blocks: Block Kit blocks for rich formatting.
            thread_ts: Thread timestamp for replies.
            unfurl_links: Whether to unfurl links.

        Returns:
            API response with message details.
        """
        payload: dict[str, Any] = {
            "channel": channel,
            "text": text,
            "unfurl_links": unfurl_links,
        }

        if blocks:
            payload["blocks"] = blocks

        if thread_ts:
            payload["thread_ts"] = thread_ts

        return await self._request("POST", "/chat.postMessage", json=payload)

    async def update_message(
        self,
        channel: str,
        ts: str,
        text: str,
        *,
        blocks: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Update an existing message.

        Args:
            channel: Channel ID.
            ts: Message timestamp.
            text: New message text.
            blocks: New Block Kit blocks.

        Returns:
            API response.
        """
        payload: dict[str, Any] = {
            "channel": channel,
            "ts": ts,
            "text": text,
        }

        if blocks:
            payload["blocks"] = blocks

        return await self._request("POST", "/chat.update", json=payload)

    async def get_reactions(
        self,
        channel: str,
        ts: str,
    ) -> list[dict[str, Any]]:
        """Get reactions on a message.

        Args:
            channel: Channel ID.
            ts: Message timestamp.

        Returns:
            List of reactions.
        """
        try:
            data = await self._request(
                "GET",
                "/reactions.get",
                params={"channel": channel, "timestamp": ts},
            )
            message = data.get("message", {})
            return message.get("reactions", [])
        except RuntimeError:
            return []

    async def get_replies(
        self,
        channel: str,
        ts: str,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get replies in a thread.

        Args:
            channel: Channel ID.
            ts: Thread parent timestamp.
            limit: Maximum number of replies.

        Returns:
            List of reply messages.
        """
        try:
            data = await self._request(
                "GET",
                "/conversations.replies",
                params={"channel": channel, "ts": ts, "limit": limit},
            )
            messages = data.get("messages", [])
            # First message is the parent, rest are replies
            return messages[1:] if len(messages) > 1 else []
        except RuntimeError:
            return []

    async def test_auth(self) -> dict[str, Any] | None:
        """Test authentication and get bot info.

        Returns:
            Bot info if authenticated, None otherwise.
        """
        try:
            return await self._request("POST", "/auth.test")
        except RuntimeError:
            return None


class SlackApprovalHook:
    """Hook for requesting human approval via Slack.

    Sends interactive messages to Slack and waits for
    approval/rejection responses via reactions or replies.

    Example:
        hook = SlackApprovalHook(channel="#game-dev")
        approved = await hook.request_approval(
            message="Ready to publish game?",
            context={"game": "My Game", "version": "1.0.0"},
        )
        if approved:
            print("Proceeding with publish")
    """

    # Default reaction emojis for approval/rejection
    APPROVE_REACTIONS: ClassVar[set[str]] = {"white_check_mark", "heavy_check_mark", "+1", "thumbsup"}
    REJECT_REACTIONS: ClassVar[set[str]] = {"x", "no_entry", "-1", "thumbsdown"}

    def __init__(
        self,
        channel: str = "#game-dev",
        *,
        token: str | None = None,
        poll_interval: float = 5.0,
        require_thread_reply: bool = False,
    ) -> None:
        """Initialize the hook.

        Args:
            channel: Slack channel for approval requests.
            token: Slack bot token. If None, uses SLACK_BOT_TOKEN env var.
            poll_interval: Interval between checks in seconds.
            require_thread_reply: If True, require reply instead of reaction.
        """
        self.channel = channel
        self.token = token
        self.poll_interval = poll_interval
        self.require_thread_reply = require_thread_reply
        self._pending_requests: dict[str, ApprovalRequest] = {}

    def _create_approval_blocks(
        self,
        message: str,
        context: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Create Block Kit blocks for approval message.

        Args:
            message: Main approval message.
            context: Additional context to display.
            request_id: Unique request ID.

        Returns:
            List of Block Kit blocks.
        """
        blocks: list[dict[str, Any]] = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Approval Required",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message,
                },
            },
        ]

        # Add context if provided
        if context:
            context_text = "\n".join(
                f"*{k}:* {v}" for k, v in context.items()
            )
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": context_text,
                },
            })

        blocks.append({"type": "divider"})

        # Add instructions
        if self.require_thread_reply:
            instruction = (
                "Reply to this thread with `approve` or `reject` to respond.\n"
                "You can include feedback in your reply."
            )
        else:
            instruction = (
                "React with :white_check_mark: to approve or :x: to reject.\n"
                "Alternatively, reply in thread with `approve` or `reject`."
            )

        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": instruction,
                },
            ],
        })

        if request_id:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"_Request ID: {request_id}_",
                    },
                ],
            })

        return blocks

    def _create_response_blocks(
        self,
        original_message: str,
        status: ApprovalStatus,
        responder: str | None = None,
        feedback: str | None = None,
    ) -> list[dict[str, Any]]:
        """Create Block Kit blocks for response update.

        Args:
            original_message: Original approval message.
            status: Final status.
            responder: Who responded.
            feedback: Any feedback provided.

        Returns:
            List of Block Kit blocks.
        """
        status_emoji = ":white_check_mark:" if status == ApprovalStatus.APPROVED else ":x:"
        status_text = "Approved" if status == ApprovalStatus.APPROVED else "Rejected"

        blocks: list[dict[str, Any]] = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{status_emoji} {status_text}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"~{original_message}~",
                },
            },
        ]

        if responder:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Responded by <@{responder}>",
                    },
                ],
            })

        if feedback:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Feedback:* {feedback}",
                },
            })

        return blocks

    async def request_approval(
        self,
        message: str,
        context: dict[str, Any] | None = None,
        timeout_minutes: int | None = None,
    ) -> bool:
        """Request approval from a human.

        Args:
            message: The approval request message.
            context: Additional context to display.
            timeout_minutes: Timeout in minutes (None for indefinite).

        Returns:
            True if approved, False if rejected.

        Raises:
            ApprovalTimeoutError: If timeout is reached.
            ApprovalRejectedError: If explicitly rejected with feedback.
        """
        import uuid

        request_id = str(uuid.uuid4())[:8]
        timeout_seconds = timeout_minutes * 60 if timeout_minutes else None

        logger.info(
            "Requesting approval in %s (timeout: %s minutes)",
            self.channel,
            timeout_minutes,
        )

        async with SlackClient(token=self.token) as client:
            # Check authentication
            auth = await client.test_auth()
            if not auth:
                raise RuntimeError("Failed to authenticate with Slack")

            # Create and send approval message
            blocks = self._create_approval_blocks(message, context, request_id)
            fallback_text = f"Approval Required: {message}"

            response = await client.post_message(
                channel=self.channel,
                text=fallback_text,
                blocks=blocks,
            )

            channel_id = response.get("channel", self.channel)
            message_ts = response.get("ts", "")

            # Create request record
            request = ApprovalRequest(
                id=request_id,
                channel=channel_id,
                message=message,
                context=context,
                message_ts=message_ts,
                thread_ts=message_ts,
            )
            self._pending_requests[request_id] = request

            try:
                # Poll for response
                start_time = time.time()

                while True:
                    # Check timeout
                    if timeout_seconds:
                        elapsed = time.time() - start_time
                        if elapsed >= timeout_seconds:
                            request.status = ApprovalStatus.EXPIRED
                            raise ApprovalTimeoutError(
                                f"Approval request timed out after {timeout_minutes} minutes"
                            )

                    # Check reactions
                    if not self.require_thread_reply:
                        reactions = await client.get_reactions(channel_id, message_ts)
                        status, responder = self._check_reactions(reactions)
                        if status:
                            request.status = status
                            request.responder = responder
                            request.responded_at = time.time()
                            break

                    # Check thread replies
                    replies = await client.get_replies(channel_id, message_ts)
                    status, responder, feedback = self._check_replies(replies)
                    if status:
                        request.status = status
                        request.responder = responder
                        request.feedback = feedback
                        request.responded_at = time.time()
                        break

                    await asyncio.sleep(self.poll_interval)

                # Update the original message
                response_blocks = self._create_response_blocks(
                    message, request.status, request.responder, request.feedback
                )
                await client.update_message(
                    channel=channel_id,
                    ts=message_ts,
                    text=f"{request.status.value}: {message}",
                    blocks=response_blocks,
                )

                if request.status == ApprovalStatus.APPROVED:
                    logger.info("Approval granted by %s", request.responder)
                    return True
                else:
                    logger.info("Approval rejected by %s", request.responder)
                    if request.feedback:
                        raise ApprovalRejectedError(
                            f"Rejected by {request.responder}: {request.feedback}"
                        )
                    return False

            finally:
                # Clean up
                self._pending_requests.pop(request_id, None)

    def _check_reactions(
        self,
        reactions: list[dict[str, Any]],
    ) -> tuple[ApprovalStatus | None, str | None]:
        """Check reactions for approval/rejection.

        Args:
            reactions: List of reaction objects.

        Returns:
            Tuple of (status, responder_user_id).
        """
        for reaction in reactions:
            name = reaction.get("name", "")
            users = reaction.get("users", [])

            if not users:
                continue

            if name in self.APPROVE_REACTIONS:
                return ApprovalStatus.APPROVED, users[0]
            elif name in self.REJECT_REACTIONS:
                return ApprovalStatus.REJECTED, users[0]

        return None, None

    def _check_replies(
        self,
        replies: list[dict[str, Any]],
    ) -> tuple[ApprovalStatus | None, str | None, str | None]:
        """Check thread replies for approval/rejection.

        Args:
            replies: List of reply message objects.

        Returns:
            Tuple of (status, responder_user_id, feedback).
        """
        for reply in replies:
            text = reply.get("text", "").lower().strip()
            user = reply.get("user")

            if not text or not user:
                continue

            # Check for approval
            if text.startswith("approve"):
                feedback = text[7:].strip() if len(text) > 7 else None
                return ApprovalStatus.APPROVED, user, feedback

            # Check for rejection
            if text.startswith("reject"):
                feedback = text[6:].strip() if len(text) > 6 else None
                return ApprovalStatus.REJECTED, user, feedback

            # Check for simple yes/no
            if text in ("yes", "ok", "lgtm", "go", "ship it"):
                return ApprovalStatus.APPROVED, user, None
            if text in ("no", "stop", "wait", "hold"):
                return ApprovalStatus.REJECTED, user, None

        return None, None, None

    async def send_notification(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
        level: str = "info",
    ) -> bool:
        """Send a notification to Slack (no approval required).

        Args:
            message: Notification message.
            context: Additional context.
            level: Notification level (info, warning, error, success).

        Returns:
            True if sent successfully.
        """
        level_emoji = {
            "info": ":information_source:",
            "warning": ":warning:",
            "error": ":x:",
            "success": ":white_check_mark:",
        }.get(level, ":speech_balloon:")

        blocks: list[dict[str, Any]] = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{level_emoji} {message}",
                },
            },
        ]

        if context:
            context_text = "\n".join(f"*{k}:* {v}" for k, v in context.items())
            blocks.append({
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": context_text}],
            })

        try:
            async with SlackClient(token=self.token) as client:
                await client.post_message(
                    channel=self.channel,
                    text=f"{level.upper()}: {message}",
                    blocks=blocks,
                )
            return True
        except Exception as e:
            logger.error("Failed to send Slack notification: %s", e)
            return False
