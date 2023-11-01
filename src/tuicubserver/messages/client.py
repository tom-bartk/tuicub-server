import socket

from .message import Message, MessageEnvelope, MessageEnvelopeSchema


class MessagesClient:
    """The client for delivering messages over a socket."""

    def __init__(self, host: str, port: int, token: str, schema: MessageEnvelopeSchema):
        """Initialize new client.

        Args:
            host (str): The host to connect to.
            port (int): The port to connect to.
            token (str): The authentication token to include in a message.
            schema (MessageEnvelopeSchema): The schema for serializing messages.
        """
        self._socket: socket.socket | None = None
        self._token: str = token
        self._host: str = host
        self._port: int = port
        self._schema: MessageEnvelopeSchema = schema

    def send(self, *messages: Message) -> None:
        """Send messages.

        The messages are serialized and authenticated using a token.

        Args:
            messages (Message): The messages to send.
        """
        if self._socket:
            for message in messages:
                serialized = self._schema.dumps(
                    MessageEnvelope(token=self._token, message=message)
                )

                self._socket.sendall(f"{serialized}\n".encode())

    def connect(self) -> None:
        """Connect to the host and port passed on initialization."""
        self._socket = socket.create_connection((self._host, self._port))
