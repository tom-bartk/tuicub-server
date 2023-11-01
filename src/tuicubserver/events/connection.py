from __future__ import annotations

import asyncio
import uuid
from collections.abc import Callable
from typing import Protocol
from weakref import ReferenceType, WeakMethod, ref

from attrs import frozen


@frozen
class TuicubProtocol(asyncio.Protocol):
    """The stream protocol for users connections.

    Attributes:
        on_connection_made (WeakMethod[Callable[[asyncio.Transport], None]]): A weak
            reference to a method called when a connection has been estabilished.
        on_data (WeakMethod[Callable[[str], None]]): A weak reference to a method called
            when new data is sent over the connection.
        on_connection_lost (WeakMethod[Callable[[], None]]): A weak reference to a method
            called when a connection has been lost.
    """

    on_connection_made: WeakMethod[Callable[[asyncio.Transport], None]]
    on_data: WeakMethod[Callable[[str], None]]
    on_connection_lost: WeakMethod[Callable[[], None]]

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        """Called when a connection is made."""
        if isinstance(transport, asyncio.Transport) and (
            on_connection_made := self.on_connection_made()
        ):
            on_connection_made(transport)

    def data_received(self, data: bytes) -> None:
        """Called when some data is received."""
        if on_data := self.on_data():
            for message in data.decode().splitlines():
                if message:
                    on_data(message)

    def connection_lost(self, exc: Exception | None) -> None:
        """Called when the connection is lost or closed."""
        if on_connection_lost := self.on_connection_lost():
            on_connection_lost()


class Connection:
    """A connection between a user and the events server."""

    __slots__ = ("_id", "_delegate", "_protocol", "_transport", "__weakref__")

    @property
    def id(self) -> uuid.UUID:
        """The id of the connection."""
        return self._id

    @property
    def protocol(self) -> TuicubProtocol:
        """The stream protocol of this connection."""
        return self._protocol

    def __init__(self) -> None:
        """Initialize new connection with a `TuicubProtocol`."""
        self._id: uuid.UUID = uuid.uuid4()
        self._delegate: ReferenceType[ConnectionDelegate] | None = None
        self._protocol = TuicubProtocol(
            on_connection_made=WeakMethod(self._connection_made),
            on_data=WeakMethod(self._read),
            on_connection_lost=WeakMethod(self._connection_lost),
        )
        self._transport: asyncio.Transport | None = None

    async def write(self, data: str) -> None:
        """Write data over the connection.

        The data is sent with an appended newline character.

        Args:
            data (str): The data to send.

        Raises:
            TransportClosedError: Raised when the underlying transport is None,
            or has been closed.
        """
        if self._transport and not self._transport.is_closing():
            self._transport.write(f"{data}\n".encode())
        else:
            raise TransportClosedError()

    def set_delegate(self, delegate: ConnectionDelegate) -> None:
        """Sets a weak reference to the delegate."""
        self._delegate = ref(delegate)

    def _read(self, data: str) -> None:
        if self._delegate and (delegate := self._delegate()):
            delegate.connection_on_data(connection=self, data=data)

    def _connection_made(self, transport: asyncio.Transport) -> None:
        self._transport = transport
        if self._delegate and (delegate := self._delegate()):
            delegate.connection_connected(connection=self)

    def _connection_lost(self) -> None:
        if self._delegate and (delegate := self._delegate()):
            delegate.connection_disconnected(connection=self)

    def __hash__(self) -> int:
        return hash((self.id,))


class ConnectionDelegate(Protocol):
    """The delegate of the connection."""

    def connection_on_data(self, connection: Connection, data: str) -> None:
        """Called whenever the connection receives new data."""

    def connection_connected(self, connection: Connection) -> None:
        """Called when the connection has been estabilished."""

    def connection_disconnected(self, connection: Connection) -> None:
        """Called when the connection has been lost."""


class TransportClosedError(Exception):
    def __init__(self) -> None:
        super().__init__("Transport is None or closed.")
