import asyncio
from typing import Protocol
from uuid import UUID
from weakref import ReferenceType, ref

from ..common.logger import Logger
from ..services.auth import AuthService
from .message import MessageEnvelopeSchema


class MessagesDelegate(Protocol):
    """The delegate of the messages server."""

    async def on_event(self, event: dict, recipents: list[UUID]) -> None:
        """Callback called whenever a valid message arrives.

        Args:
            event (dict): The event from the message.
            recipents (list[UUID]): The recipents of the event.
        """


class MessagesServer:
    """A simple implementation of a messaging queue.

    The messages server works alongside the events server, and behaves like as
    a message queue for the api server.

    The api server sends messages over a socket, and the messages server deserializes
    and passes them to events server for further delivering.
    """

    __slots__ = ("_auth_service", "_delegate", "_logger")

    @property
    def delegate(self) -> ReferenceType[MessagesDelegate] | None:
        """A weak reference to the delegate."""
        return self._delegate

    def __init__(self, auth_service: AuthService, logger: Logger):
        """Initialize new server.

        Args:
            auth_service (AuthService): The authentication service.
            logger (Logger): The logger for logging errors and incoming messages.
        """
        self._auth_service: AuthService = auth_service
        self._delegate: ReferenceType[MessagesDelegate] | None = None
        self._logger: Logger = logger

    async def listen(self, host: str, port: int) -> None:
        """Start the server on a host and port.

        Args:
            host (str): The host to bind to.
            port (int): The port to bind to.
        """
        server = await asyncio.start_server(self.client_connected, host=host, port=port)
        async with server:
            print(f"Starting tuicub messages server on {host}:{port}")
            self._logger.log("messages_server_start")
            await server.serve_forever()

    async def client_connected(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """The callback called when a client connects.

        The reading stream is read line by line. Each line is deserialized to
        a message envelope, and if the envelope has a valid authentication token,
        the event from the message is passed to the delegate along its recipents.

        Args:
            reader (asyncio.StreamReader): The reading stream.
            writer (asyncio.StreamWriter): The writing stream.
        """
        self._logger.log("messages_server_connect")

        async for data in reader:
            raw_message = data.decode().strip()
            try:
                envelope = MessageEnvelopeSchema().loads(raw_message)

                self._auth_service.authorize_message(secret=envelope.token)

                if self._delegate and (delegate := self._delegate()):
                    await delegate.on_event(
                        event=envelope.message.event, recipents=envelope.message.recipents
                    )
            except Exception as err:
                self._logger.log_error("messages_error", err=err)

    def set_delegate(self, delegate: MessagesDelegate) -> None:
        """Sets the delegate as a weak reference."""
        self._delegate = ref(delegate)
