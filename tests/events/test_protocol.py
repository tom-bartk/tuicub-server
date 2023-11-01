import asyncio
from unittest.mock import Mock, call
from weakref import WeakMethod

import pytest

from src.tuicubserver.events.connection import TuicubProtocol


class MockConnection:
    def __init__(self):
        self.on_data_mock = Mock()
        self.on_connection_made_mock = Mock()
        self.on_connection_lost_mock = Mock()

    def on_data(self, data: str) -> None:
        self.on_data_mock(data)

    def on_connection_made(self, transport: asyncio.Transport) -> None:
        self.on_connection_made_mock(transport)

    def on_connection_lost(self) -> None:
        self.on_connection_lost_mock()


@pytest.fixture()
def connection() -> MockConnection:
    return MockConnection()


@pytest.fixture()
def sut(connection) -> TuicubProtocol:
    return TuicubProtocol(
        on_connection_made=WeakMethod(connection.on_connection_made),
        on_data=WeakMethod(connection.on_data),
        on_connection_lost=WeakMethod(connection.on_connection_lost),
    )


class TestConnectionMade:
    def test_calls_connection_made_callback_with_transport(self, sut, connection):
        expected = asyncio.Transport()

        sut.connection_made(transport=expected)

        connection.on_connection_made_mock.assert_called_once_with(expected)


class TestDataReceived:
    def test_when_data_has_one_line__calls_on_data_callback_once_with_decoded_message(
        self, sut, connection
    ):
        expected = "foo"

        sut.data_received(data=b"foo")

        connection.on_data_mock.assert_called_once_with(expected)

    def test_when_data_has_two_lines__calls_on_data_callback_twice_with_decoded_messages(
        self, sut, connection
    ):
        expected = [call("foo"), call("bar")]

        sut.data_received(data=b"foo\nbar")

        connection.on_data_mock.assert_has_calls(expected, any_order=False)

    def test_when_data_has_empty_lines__does_not_call_on_data_callback_for_empty_lines(
        self, sut, connection
    ):
        expected = [call("foo"), call("bar")]

        sut.data_received(data=b"\n\nfoo\nbar\n")

        connection.on_data_mock.assert_has_calls(expected, any_order=False)


class TestConnectionLost:
    def test_calls_on_connection_loast_callback(self, sut, connection):
        sut.connection_lost(None)

        connection.on_connection_lost_mock.assert_called_once()
