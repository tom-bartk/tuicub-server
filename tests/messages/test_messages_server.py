import asyncio
from unittest.mock import Mock, call, create_autospec, patch
from uuid import UUID
from weakref import ref

import pytest

from src.tuicubserver.common.errors import UnauthorizedError
from src.tuicubserver.messages.server import MessagesDelegate, MessagesServer
from tests.utils import AsyncIter, not_raises


@pytest.fixture()
def sut(auth_service, logger) -> MessagesServer:
    return MessagesServer(auth_service=auth_service, logger=logger)


@pytest.mark.asyncio()
class TestListen:
    async def test_creates_server_on_host_and_port(self, sut):
        with patch("asyncio.start_server") as mocked_start_server:
            await sut.listen(host="localhost", port=12421)

            mocked_start_server.assert_awaited_once_with(
                sut.client_connected, host="localhost", port=12421
            )

    async def test_starts_serving_forever(self, sut, loop):
        server = create_autospec(asyncio.AbstractServer)
        with patch("asyncio.start_server", return_value=server):
            await sut.listen(host="localhost", port=12421)

            server.serve_forever.assert_awaited_once()


class TestSetDelegate:
    def test_stores_weak_reference_to_delegate(self, sut):
        delegate = create_autospec(MessagesDelegate)

        sut.set_delegate(delegate)

        assert sut.delegate == ref(delegate)


@pytest.mark.asyncio()
class TestClientConnected:
    async def test_when_delegate_set__reader_lines_are_valid_messages__calls_delegate_on_event_for_each_message(  # noqa: E501
        self, sut
    ):
        delegate = create_autospec(MessagesDelegate)

        user_id_1 = UUID("d052cc24-dc55-4f19-b71f-f38f0deef258")
        user_id_2 = UUID("5d4c8ca4-a7d7-4da4-bb66-8717c92d350e")
        message_1 = (
            b'{"token": "foo", "message": {"recipents": '
            b'["d052cc24-dc55-4f19-b71f-f38f0deef258", '
            b'"5d4c8ca4-a7d7-4da4-bb66-8717c92d350e"], "event": {"bar": 13}}}'
        )
        message_2 = (
            b'{"token": "foo", "message": {"recipents": '
            b'["d052cc24-dc55-4f19-b71f-f38f0deef258", '
            b'"5d4c8ca4-a7d7-4da4-bb66-8717c92d350e"], "event": {"bar": 42}}}'
        )
        expected_calls = [
            call(event={"bar": 13}, recipents=[user_id_1, user_id_2]),
            call(event={"bar": 42}, recipents=[user_id_1, user_id_2]),
        ]

        sut.set_delegate(delegate)
        await sut.client_connected(AsyncIter([message_1, message_2]), writer=Mock())

        delegate.on_event.assert_has_calls(expected_calls)

    async def test_when_message_is_invalid__does_not_raise(self, sut):
        with not_raises(Exception):
            await sut.client_connected(AsyncIter([b"foo"]), writer=Mock())

    async def test_when_read_message_has_invalid_token__does_not_call_delegate(
        self, sut, auth_service
    ):
        auth_service.authorize_message = Mock(side_effect=UnauthorizedError)
        delegate = create_autospec(MessagesDelegate)

        message = (
            b'{"token": "foo", "message": {"recipents": '
            b'["d052cc24-dc55-4f19-b71f-f38f0deef258", '
            b'"5d4c8ca4-a7d7-4da4-bb66-8717c92d350e"], "event": {"bar": 13}}}'
        )

        sut.set_delegate(delegate)
        await sut.client_connected(AsyncIter([message]), writer=Mock())

        delegate.on_event.assert_not_called()
        auth_service.authorize_message.assert_called_once_with(secret="foo")
