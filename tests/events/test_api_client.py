from unittest.mock import patch
from uuid import uuid4

import pytest

from src.tuicubserver.events.api_client import EventsApiClient


@pytest.fixture()
def api_url() -> str:
    return "http://localhost:5000"


@pytest.fixture()
def token() -> str:
    return "token"


@pytest.fixture()
def sut(api_url, token) -> EventsApiClient:
    return EventsApiClient(api_url=api_url, token=token)


class TestNotifyUserDisconnected:
    def test_sends_correct_request(self, sut, api_url, token) -> None:
        with patch("requests.post") as mocked_post:
            user_id = uuid4()
            sut.notify_user_disconnected(user_id)

            mocked_post.assert_called_with(
                f"{api_url}/gamerooms/disconnect",
                json={"user_id": str(user_id)},
                headers={"Authorization": f"Bearer {token}"},
            )
