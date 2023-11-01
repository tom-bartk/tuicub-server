from uuid import UUID

import requests


class EventsApiClient:
    """The client for notifying the api server about user disconnects."""

    def __init__(self, api_url: str, token: str):
        """Initialize new client.

        Args:
            api_url (str): The base url of the api server.
            token (str): The authentication token to include in every request.
        """
        self._api_url: str = api_url
        self._token: str = token

    def notify_user_disconnected(self, user_id: UUID) -> None:
        """Notify the api server about a disconnecting user.

        Sends a POST request to the `/gamerooms/disconnect` endpoint
        with the disconnected user id in the body.

        Args:
            user_id (UUID): The id of the disconnected user.
        """
        requests.post(
            f"{self._api_url}/gamerooms/disconnect",
            json={"user_id": str(user_id)},
            headers={"Authorization": f"Bearer {self._token}"},
        )
