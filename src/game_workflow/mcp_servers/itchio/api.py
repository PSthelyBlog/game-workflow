"""itch.io API client.

This module provides an async client for the itch.io API.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class GameType(str, Enum):
    """Type of game on itch.io."""

    DEFAULT = "default"
    FLASH = "flash"
    UNITY = "unity"
    JAVA = "java"
    HTML = "html"


class GameClassification(str, Enum):
    """Classification of game on itch.io."""

    GAME = "game"
    TOOL = "tool"
    ASSETS = "assets"
    GAME_MOD = "game_mod"
    PHYSICAL_GAME = "physical_game"
    SOUNDTRACK = "soundtrack"
    OTHER = "other"
    COMIC = "comic"
    BOOK = "book"


class ReleaseStatus(str, Enum):
    """Release status of a game."""

    RELEASED = "released"
    IN_DEVELOPMENT = "in-development"
    PROTOTYPE = "prototype"
    ON_HOLD = "on-hold"
    CANCELLED = "cancelled"


@dataclass
class ItchioGame:
    """Representation of an itch.io game."""

    id: int
    url: str
    title: str
    short_text: str | None = None
    type: GameType = GameType.DEFAULT
    classification: GameClassification = GameClassification.GAME
    created_at: str | None = None
    published_at: str | None = None
    cover_url: str | None = None
    min_price: int = 0  # In cents
    can_be_bought: bool = False
    has_demo: bool = False
    in_press_system: bool = False
    p_windows: bool = False
    p_linux: bool = False
    p_osx: bool = False
    p_android: bool = False
    downloads_count: int = 0
    views_count: int = 0
    purchases_count: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ItchioGame:
        """Create a game from API response data.

        Args:
            data: Dictionary from API response.

        Returns:
            ItchioGame instance.
        """
        game_type = data.get("type", "default")
        if game_type and isinstance(game_type, str):
            try:
                game_type = GameType(game_type)
            except ValueError:
                game_type = GameType.DEFAULT
        else:
            game_type = GameType.DEFAULT

        classification = data.get("classification", "game")
        if classification and isinstance(classification, str):
            try:
                classification = GameClassification(classification)
            except ValueError:
                classification = GameClassification.GAME
        else:
            classification = GameClassification.GAME

        return cls(
            id=data.get("id", 0),
            url=data.get("url", ""),
            title=data.get("title", ""),
            short_text=data.get("short_text"),
            type=game_type,
            classification=classification,
            created_at=data.get("created_at"),
            published_at=data.get("published_at"),
            cover_url=data.get("cover_url"),
            min_price=data.get("min_price", 0),
            can_be_bought=data.get("can_be_bought", False),
            has_demo=data.get("has_demo", False),
            in_press_system=data.get("in_press_system", False),
            p_windows=data.get("p_windows", False),
            p_linux=data.get("p_linux", False),
            p_osx=data.get("p_osx", False),
            p_android=data.get("p_android", False),
            downloads_count=data.get("downloads_count", 0),
            views_count=data.get("views_count", 0),
            purchases_count=data.get("purchases_count", 0),
        )


@dataclass
class ItchioUpload:
    """Representation of an itch.io upload (game file)."""

    id: int
    game_id: int
    filename: str
    display_name: str | None = None
    size: int = 0
    channel_name: str | None = None
    build_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None
    storage: str | None = None
    md5_hash: str | None = None
    p_windows: bool = False
    p_linux: bool = False
    p_osx: bool = False
    p_android: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ItchioUpload:
        """Create an upload from API response data.

        Args:
            data: Dictionary from API response.

        Returns:
            ItchioUpload instance.
        """
        return cls(
            id=data.get("id", 0),
            game_id=data.get("game_id", 0),
            filename=data.get("filename", ""),
            display_name=data.get("display_name"),
            size=data.get("size", 0),
            channel_name=data.get("channel_name"),
            build_id=data.get("build_id"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            storage=data.get("storage"),
            md5_hash=data.get("md5_hash"),
            p_windows=data.get("p_windows", False),
            p_linux=data.get("p_linux", False),
            p_osx=data.get("p_osx", False),
            p_android=data.get("p_android", False),
        )


@dataclass
class ItchioUser:
    """Representation of an itch.io user."""

    id: int
    username: str
    url: str
    display_name: str | None = None
    cover_url: str | None = None
    gamer: bool = False
    developer: bool = False
    press_user: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ItchioUser:
        """Create a user from API response data.

        Args:
            data: Dictionary from API response.

        Returns:
            ItchioUser instance.
        """
        return cls(
            id=data.get("id", 0),
            username=data.get("username", ""),
            url=data.get("url", ""),
            display_name=data.get("display_name"),
            cover_url=data.get("cover_url"),
            gamer=data.get("gamer", False),
            developer=data.get("developer", False),
            press_user=data.get("press_user", False),
        )


@dataclass
class APIResponse:
    """Generic API response wrapper."""

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    errors: list[str] = field(default_factory=list)

    @classmethod
    def from_response(cls, response: httpx.Response) -> APIResponse:
        """Create from httpx response.

        Args:
            response: The HTTP response.

        Returns:
            APIResponse instance.
        """
        try:
            data = response.json()
            errors = data.get("errors", [])
            if isinstance(errors, str):
                errors = [errors]
            return cls(
                success=response.is_success and not errors,
                data=data,
                error=errors[0] if errors else None,
                errors=errors,
            )
        except Exception as e:
            return cls(
                success=False,
                error=f"Failed to parse response: {e}",
            )


class ItchioAPIError(Exception):
    """Exception raised for itch.io API errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        errors: list[str] | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message.
            status_code: HTTP status code if applicable.
            errors: List of error messages from API.
        """
        super().__init__(message)
        self.status_code = status_code
        self.errors = errors or []


class ItchioAPI:
    """Client for the itch.io API.

    Provides methods for interacting with itch.io's REST API
    for game management operations.

    Example:
        async with ItchioAPI(api_key="...") as api:
            games = await api.get_my_games()
            for game in games:
                print(game.title)
    """

    BASE_URL = "https://itch.io/api/1"

    def __init__(
        self,
        api_key: str | None = None,
        *,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        """Initialize the API client.

        Args:
            api_key: The itch.io API key. If None, uses ITCHIO_API_KEY env var.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries for failed requests.
            retry_delay: Delay between retries in seconds.
        """
        self.api_key = api_key or os.environ.get("ITCHIO_API_KEY", "")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> ItchioAPI:
        """Enter async context."""
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
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
                timeout=self.timeout,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _get_key_param(self) -> dict[str, str]:
        """Get the API key parameter for requests."""
        return {"api_key": self.api_key} if self.api_key else {}

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> APIResponse:
        """Make an API request with retry logic.

        Args:
            method: HTTP method.
            endpoint: API endpoint (without base URL).
            **kwargs: Additional arguments for httpx.

        Returns:
            API response.
        """
        import asyncio

        # Add API key to params
        params = kwargs.pop("params", {})
        params.update(self._get_key_param())

        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = await self.client.request(
                    method,
                    endpoint,
                    params=params,
                    **kwargs,
                )

                api_response = APIResponse.from_response(response)

                # Check for rate limiting
                if response.status_code == 429:
                    if attempt < self.max_retries - 1:
                        retry_after = int(
                            response.headers.get("Retry-After", self.retry_delay * (attempt + 1))
                        )
                        logger.warning("Rate limited, retrying in %d seconds", retry_after)
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        return APIResponse(
                            success=False,
                            error="Rate limit exceeded",
                        )

                # Check for server errors (5xx)
                if response.status_code >= 500:
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delay * (attempt + 1)
                        logger.warning(
                            "Server error %d, retrying in %f seconds", response.status_code, delay
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        return APIResponse(
                            success=False,
                            error=f"Server error: {response.status_code}",
                        )

                return api_response

            except httpx.TimeoutException as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (attempt + 1)
                    logger.warning("Request timeout, retrying in %f seconds", delay)
                    await asyncio.sleep(delay)
                else:
                    return APIResponse(
                        success=False,
                        error="Request timeout",
                    )

            except httpx.RequestError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (attempt + 1)
                    logger.warning("Request error: %s, retrying in %f seconds", e, delay)
                    await asyncio.sleep(delay)
                else:
                    return APIResponse(
                        success=False,
                        error=f"Request error: {e}",
                    )

        return APIResponse(
            success=False,
            error=str(last_error) if last_error else "Unknown error",
        )

    async def get_me(self) -> ItchioUser | None:
        """Get the authenticated user's profile.

        Returns:
            The current user, or None if not authenticated.
        """
        response = await self._request("GET", "/me")
        if not response.success or not response.data:
            logger.error("Failed to get user profile: %s", response.error)
            return None

        user_data = response.data.get("user")
        if not user_data:
            return None

        return ItchioUser.from_dict(user_data)

    async def get_my_games(self) -> list[ItchioGame]:
        """Get list of games owned by the authenticated user.

        Returns:
            List of game objects.
        """
        response = await self._request("GET", "/my-games")
        if not response.success or not response.data:
            logger.error("Failed to get games: %s", response.error)
            return []

        games_data = response.data.get("games", [])
        return [ItchioGame.from_dict(g) for g in games_data]

    async def get_game(self, game_id: int) -> ItchioGame | None:
        """Get details for a specific game.

        Args:
            game_id: The game ID.

        Returns:
            Game object, or None if not found.
        """
        response = await self._request("GET", f"/game/{game_id}")
        if not response.success or not response.data:
            logger.error("Failed to get game %d: %s", game_id, response.error)
            return None

        game_data = response.data.get("game")
        if not game_data:
            return None

        return ItchioGame.from_dict(game_data)

    async def get_game_uploads(self, game_id: int) -> list[ItchioUpload]:
        """Get uploads for a specific game.

        Args:
            game_id: The game ID.

        Returns:
            List of upload objects.
        """
        response = await self._request("GET", f"/game/{game_id}/uploads")
        if not response.success or not response.data:
            logger.error("Failed to get uploads for game %d: %s", game_id, response.error)
            return []

        uploads_data = response.data.get("uploads", [])
        return [ItchioUpload.from_dict(u) for u in uploads_data]

    async def find_game_by_url(self, game_url: str) -> ItchioGame | None:
        """Find a game by its URL.

        Args:
            game_url: The full itch.io game URL.

        Returns:
            Game object, or None if not found.
        """
        # First get all games
        games = await self.get_my_games()
        for game in games:
            if game.url == game_url or game.url in game_url:
                return game
        return None

    async def find_game_by_slug(self, username: str, game_slug: str) -> ItchioGame | None:
        """Find a game by username and slug.

        Args:
            username: The itch.io username.
            game_slug: The game slug (URL name).

        Returns:
            Game object, or None if not found.
        """
        expected_url_part = f"{username}.itch.io/{game_slug}"
        games = await self.get_my_games()
        for game in games:
            if expected_url_part in game.url:
                return game
        return None

    async def get_credentials(self) -> dict[str, Any] | None:
        """Get credentials/scopes for the current API key.

        Returns:
            Credentials information, or None if failed.
        """
        response = await self._request("GET", "/credentials/info")
        if not response.success or not response.data:
            return None
        return response.data

    async def check_api_key(self) -> bool:
        """Check if the API key is valid.

        Returns:
            True if the API key is valid.
        """
        user = await self.get_me()
        return user is not None
