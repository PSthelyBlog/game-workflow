"""itch.io API client.

This module provides a client for the itch.io API.
"""

from typing import Any

import httpx


class ItchioAPI:
    """Client for the itch.io API.

    Provides methods for interacting with itch.io's REST API
    for game management operations.
    """

    BASE_URL = "https://itch.io/api/1"

    def __init__(self, api_key: str) -> None:
        """Initialize the API client.

        Args:
            api_key: The itch.io API key.
        """
        self.api_key = api_key
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={"Authorization": f"Bearer {api_key}"},
        )

    async def get_my_games(self) -> list[dict[str, Any]]:
        """Get list of games owned by the authenticated user.

        Returns:
            List of game objects.
        """
        # TODO: Implement API call
        raise NotImplementedError("itch.io API not yet implemented")

    async def get_game(self, game_id: int) -> dict[str, Any]:
        """Get details for a specific game.

        Args:
            game_id: The game ID.

        Returns:
            Game object.
        """
        # TODO: Implement API call
        raise NotImplementedError("itch.io API not yet implemented")

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
