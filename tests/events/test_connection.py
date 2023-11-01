import asyncio
import uuid
from unittest.mock import Mock, create_autospec, patch

import pytest

from src.tuicubserver.events.connection import (
    Connection,
    ConnectionDelegate,
    TransportClosedError,
)


@pytest.fixture()
def sut() -> Connection:
    return Connection()


@pytest.fixture()
def delegate() -> ConnectionDelegate:
    return create_autospec(ConnectionDelegate)()


class TestConnectionMade:
    def test_when_protocol_connected__calls_connected_on_delegate(self, sut, delegate):
        sut.set_delegate(delegate)

        sut.protocol.connection_made(transport=create_autospec(asyncio.Transport))

        delegate.connection_connected.assert_called_once_with(sut)


class TestRead:
    def test_when_procotol_reads_data__calls_on_data_on_delegate_with_read_data(
        self, sut, delegate
    ):
        sut.set_delegate(delegate)
        expected = "foo"

        sut.protocol.data_received(data=b"foo")

        delegate.connection_on_data.assert_called_once_with(connection=sut, data=expected)


class TestConnectionLost:
    def test_when_protocol_disconnects__calls_disconnected_on_delegate(
        self, sut, delegate
    ):
        sut.set_delegate(delegate)

        sut.protocol.connection_lost(None)

        delegate.connection_disconnected.assert_called_once_with(sut)


class TestId:
    def test_returns_uuid_generated_during_init(self):
        expected = uuid.uuid4()

        with patch("uuid.uuid4", return_value=expected):
            sut = Connection()
            assert sut.id == expected


@pytest.mark.asyncio()
class TestWrite:
    async def test_when_protocol_connected__transport_not_closing__writes_data_to_transport(  # noqa: E501
        self, sut, delegate
    ):
        transport = create_autospec(asyncio.Transport)
        transport.is_closing = Mock(return_value=False)
        sut.set_delegate(delegate)
        expected = b"foo\n"

        sut.protocol.connection_made(transport=transport)
        await sut.write("foo")

        transport.write.assert_called_once_with(expected)

    async def test_when_protocol_connected__transport_closing__raises_transport_closed_error(  # noqa: E501
        self, sut, delegate
    ):
        transport = create_autospec(asyncio.Transport)
        transport.is_closing = Mock(return_value=True)
        sut.set_delegate(delegate)

        sut.protocol.connection_made(transport=transport)
        with pytest.raises(TransportClosedError):
            await sut.write("foo")
