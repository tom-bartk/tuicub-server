import asyncio
import json
from uuid import UUID

from attrs import frozen
from marshmallow_generic import EXCLUDE, GenericSchema, fields
from more_itertools import first
from sqlalchemy.orm import sessionmaker

from ..common.logger import Logger
from ..messages.server import MessagesDelegate
from ..models.user import UserToken
from ..services.users import UsersService
from .api_client import EventsApiClient
from .connection import Connection, ConnectionDelegate, TransportClosedError


class EventsServer(ConnectionDelegate, MessagesDelegate):
    """The server that delivers events to connected users in real-time.

    Every user connects to this server after launching `tuicub` in order to receive events
    about changes to the game, or the gameroom.
    """

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        users_service: UsersService,
        api_client: EventsApiClient,
        session_factory: sessionmaker,
        logger: Logger,
    ):
        """Initialize new server.

        Args:
            loop (asyncio.AbstractEventLoop): The `asyncio` loop to create server on.
            users_service (UsersService): The users service for querying connecting users.
            api_client (EventsApiClient): The client to send disconnect notifications to
                the api server.
            session_factory (sessionmaker): The factory for creating database sessions.
            logger (Logger): The logger.
        """
        self._all_connections: set[Connection] = set()
        self._user_id_connection_map: dict[UUID, Connection] = {}
        self._loop: asyncio.AbstractEventLoop = loop
        self._users_service: UsersService = users_service
        self._session_factory: sessionmaker = session_factory
        self._api_client: EventsApiClient = api_client
        self._logger: Logger = logger

    async def listen(self, host: str, port: int) -> None:
        """Start the server on a host and port.

        Args:
            host (str): The host to bind to.
            port (int): The port to bind to.
        """
        server = await self._loop.create_server(self.add_protocol, host=host, port=port)
        async with server:
            print(f"Starting tuicub events server on {host}:{port}")
            await server.serve_forever()

    def connection_on_data(self, connection: Connection, data: str) -> None:
        """The `ConnectionDelegate` callback called when a connection receives new data.

        If the data is a valid connection request, the connection is linked to the
        sending user.

        Args:
            connection (Connection): The connection sending the data.
            data (str): The sent data.
        """
        with self._session_factory() as session:
            try:
                connect_request = ConnectRequestSchema().loads(data, unknown=EXCLUDE)
                self._logger.log(
                    "events_connect_request",
                    token=str(connect_request.token),
                    connection_id=str(connection.id),
                )

                user_token: UserToken = self._users_service.get_user_token(
                    session=session, token=connect_request.token
                )
                self._logger.log(
                    "events_user_connect",
                    user_id=str(connect_request.token),
                    connection_id=str(connection.id),
                )

                self._user_id_connection_map[user_token.user_id] = connection
            except Exception as err:
                self._logger.log_error(
                    "events_error", err=err, connection_id=str(connection.id)
                )

    def connection_connected(self, connection: Connection) -> None:
        """The `ConnectionDelegate` callback called when a connection is estabilished."""
        self._logger.log("events_connect", connection_id=str(connection.id))
        self._all_connections.add(connection)

    def connection_disconnected(self, connection: Connection) -> None:
        """The `ConnectionDelegate` callback called when a connection is lost.

        If the connection has been linked to a user, the api server is notified about
        the disconnected user.
        """
        if user_id := self._user_id_for_connection(connection):
            self._user_id_connection_map.pop(user_id, None)

            try:
                self._api_client.notify_user_disconnected(user_id=user_id)
            except Exception as err:
                self._logger.log_error(
                    "events_error", err=err, connection_id=str(connection.id)
                )
            else:
                self._logger.log(
                    "events_user_disconnect",
                    user_id=str(user_id),
                    connection_id=str(connection.id),
                )
        else:
            self._logger.log("events_disconnect", connection_id=str(connection.id))

        self._all_connections.remove(connection)

    async def on_event(self, event: dict, recipents: list[UUID]) -> None:
        """The `MessagesDelegate` callback called when a message with an event arrives.

        The event is sent to all connections that have been linked to users in the
        `recipents` argument.
        """
        async with asyncio.TaskGroup() as group:
            for user_id in recipents:
                group.create_task(self._send(user_id=user_id, event=event))

    async def _send(self, user_id: UUID, event: dict) -> None:
        if connection := self._user_id_connection_map.get(user_id, None):
            try:
                await connection.write(json.dumps(event))
                self._logger.log(
                    "events_sent",
                    user_id=str(user_id),
                    connection_id=str(connection.id),
                    event_name=event.get("name", "NONE"),
                )
            except TransportClosedError as err:
                self._logger.log_error(
                    "events_error", err=err, connection_id=str(connection.id)
                )

    def _user_id_for_connection(self, connection: Connection) -> UUID | None:
        return first(
            (
                user_id
                for user_id, conn in self._user_id_connection_map.items()
                if conn.id == connection.id
            ),
            None,
        )

    def add_protocol(self) -> asyncio.Protocol:
        """The factory for creating new protocols."""
        connection = Connection()
        connection.set_delegate(self)
        self._all_connections.add(connection)

        return connection.protocol


@frozen
class ConnectRequest:
    """The model for a connect request.

    Attributes:
        token (str): The authentication token of the connecting user.
    """

    token: str


class ConnectRequestSchema(GenericSchema[ConnectRequest]):
    """The schema of the connect request."""

    token = fields.Str(required=True, allow_none=False)
