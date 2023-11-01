from socket import socket
from unittest.mock import call, create_autospec, patch
from uuid import UUID

import pytest

from src.tuicubserver.messages.client import MessagesClient
from src.tuicubserver.messages.message import (
    Message,
    MessageEnvelopeSchema,
)


@pytest.fixture()
def sock() -> socket:
    return create_autospec(socket)


@pytest.fixture()
def sut(sock) -> MessagesClient:
    return MessagesClient(
        host="localhost", port=8888, token="token", schema=MessageEnvelopeSchema()
    )


class TestSend:
    def test_sends_serialized_message_with_newline_over_socket(self, sut, sock):
        with patch("socket.create_connection", return_value=sock):
            user_id_1 = UUID("d052cc24-dc55-4f19-b71f-f38f0deef258")
            user_id_2 = UUID("5d4c8ca4-a7d7-4da4-bb66-8717c92d350e")
            message = Message(recipents=[user_id_1, user_id_2], event={"foo": 42})
            expected = (
                b'{"token": "token", "message": {"recipents": '
                b'["d052cc24-dc55-4f19-b71f-f38f0deef258", '
                b'"5d4c8ca4-a7d7-4da4-bb66-8717c92d350e"], "event": {"foo": 42}}}\n'
            )

            sut.connect()
            sut.send(message)

            sock.sendall.assert_called_once_with(expected)

    def test_sends_all_passed_messages(self, sut, sock):
        with patch("socket.create_connection", return_value=sock):
            user_id_1 = UUID("d052cc24-dc55-4f19-b71f-f38f0deef258")
            user_id_2 = UUID("5d4c8ca4-a7d7-4da4-bb66-8717c92d350e")
            message_1 = Message(recipents=[user_id_1, user_id_2], event={"foo": 42})
            message_2 = Message(recipents=[user_id_1, user_id_2], event={"bar": 13})
            call_1 = call(
                b'{"token": "token", "message": {"recipents": '
                b'["d052cc24-dc55-4f19-b71f-f38f0deef258", '
                b'"5d4c8ca4-a7d7-4da4-bb66-8717c92d350e"], "event": {"foo": 42}}}\n'
            )
            call_2 = call(
                b'{"token": "token", "message": {"recipents": '
                b'["d052cc24-dc55-4f19-b71f-f38f0deef258", '
                b'"5d4c8ca4-a7d7-4da4-bb66-8717c92d350e"], "event": {"bar": 13}}}\n'
            )
            expected_calls = [call_1, call_2]

            sut.connect()
            sut.send(message_1, message_2)

            sock.sendall.assert_has_calls(expected_calls)
