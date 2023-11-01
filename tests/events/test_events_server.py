import asyncio
from unittest.mock import AsyncMock, Mock, call, create_autospec
from uuid import uuid4

import pytest
from requests.exceptions import ConnectionError

from src.tuicubserver.events.api_client import EventsApiClient
from src.tuicubserver.events.connection import (
    Connection,
    TransportClosedError,
    TuicubProtocol,
)
from src.tuicubserver.events.server import EventsServer
from src.tuicubserver.models.user import UserToken


@pytest.fixture()
def api_client() -> EventsApiClient:
    return create_autospec(EventsApiClient)


@pytest.fixture()
def sut(loop, users_service, session_factory, api_client, logger) -> EventsServer:
    return EventsServer(
        loop=loop,
        users_service=users_service,
        session_factory=session_factory,
        api_client=api_client,
        logger=logger,
    )


@pytest.mark.asyncio()
class TestListen:
    async def test_creates_server_on_host_port(self, sut, loop):
        await sut.listen(host="localhost", port=8888)

        loop.create_server.assert_awaited_once_with(
            sut.add_protocol, host="localhost", port=8888
        )

    async def test_starts_serving_forever(self, sut, loop):
        server = create_autospec(asyncio.AbstractServer)
        loop.create_server = AsyncMock(return_value=server)

        await sut.listen(host="localhost", port=8888)

        server.serve_forever.assert_awaited_once_with()


class TestConnectionOnData:
    def test_when_data_is_valid_connect_request__queries_service_for_user_token(
        self, sut, users_service, session
    ):
        connection = create_autospec(Connection)
        expected = "foo"

        sut.connection_on_data(connection, data='{"token": "foo"}')

        users_service.get_user_token.assert_called_once_with(
            session=session, token=expected
        )

    def test_when_data_is_invalid_connect_request__logs_error(self, sut, logger):
        connection = create_autospec(Connection)

        sut.connection_on_data(connection, data="foo")

        logger.log_error.assert_called_once()


class TestConnectionDisconnected:
    def test_when_connection_sent_connect_request__notifies_api_user_disconnected(
        self, sut, users_service, api_client
    ):
        connection = create_autospec(Connection)
        user_token = UserToken(id=uuid4(), user_id=uuid4(), token="foo")
        users_service.get_user_token = Mock(return_value=user_token)

        sut.connection_connected(connection)
        sut.connection_on_data(connection, data='{"token": "foo"}')
        sut.connection_disconnected(connection)

        api_client.notify_user_disconnected.assert_called_once_with(user_token.user_id)

    def test_when_connection_sent_connect_request__api_client_raises__logs_error(
        self, sut, users_service, api_client, logger
    ):
        connection = create_autospec(Connection)
        user_token = UserToken(id=uuid4(), user_id=uuid4(), token="foo")
        users_service.get_user_token = Mock(return_value=user_token)
        api_client.notify_user_disconnected = Mock(side_effect=ConnectionError)

        sut.connection_connected(connection)
        sut.connection_on_data(connection, data='{"token": "foo"}')
        sut.connection_disconnected(connection)

        logger.log_error.assert_called_once()

    def test_when_connection__no_connect_request__logs_events_disconnect(
        self, sut, logger
    ):
        connection = create_autospec(Connection)
        expected_calls = [
            call("events_connect", connection_id=str(connection.id)),
            call("events_disconnect", connection_id=str(connection.id)),
        ]

        sut.connection_connected(connection)
        sut.connection_disconnected(connection)

        logger.log.assert_has_calls(expected_calls)


@pytest.mark.asyncio()
class TestOnEvent:
    async def test_when_conn_sent_request__user_id_in_recipents__writes_json_event(  # noqa: E501
        self, sut, users_service
    ):
        connection = create_autospec(Connection)
        user_token = UserToken(id=uuid4(), user_id=uuid4(), token="foo")
        users_service.get_user_token = Mock(return_value=user_token)

        sut.connection_connected(connection)
        sut.connection_on_data(connection, data='{"token": "foo"}')
        await sut.on_event({"foo": "bar"}, recipents=[user_token.user_id])

        connection.write.assert_awaited_once_with('{"foo": "bar"}')

    async def test_when_conn_sent_request__user_id_in_recipents__conn_transport_closed__logs_error(  # noqa: E501
        self, sut, users_service, logger
    ):
        connection = create_autospec(Connection)
        error = TransportClosedError()
        connection.write = Mock(side_effect=error)
        user_token = UserToken(id=uuid4(), user_id=uuid4(), token="foo")
        users_service.get_user_token = Mock(return_value=user_token)

        sut.connection_connected(connection)
        sut.connection_on_data(connection, data='{"token": "foo"}')
        await sut.on_event({"foo": "bar"}, recipents=[user_token.user_id])

        logger.log_error.assert_called_with(
            "events_error", err=error, connection_id=str(connection.id)
        )

    async def test_when_two_conns_sent_request__conn_2_disconnected__both_user_ids_in_recipents__writes_only_to_conn_1(  # noqa: E501
        self, sut, users_service
    ):
        connection_1 = create_autospec(Connection)
        connection_2 = create_autospec(Connection)
        user_token_1 = UserToken(id=uuid4(), user_id=uuid4(), token="foo")
        user_token_2 = UserToken(id=uuid4(), user_id=uuid4(), token="bar")
        users_service.get_user_token = Mock(side_effect=[user_token_1, user_token_2])

        sut.connection_connected(connection_1)
        sut.connection_on_data(connection_1, data='{"token": "foo"}')
        sut.connection_connected(connection_2)
        sut.connection_on_data(connection_2, data='{"token": "bar"}')
        sut.connection_disconnected(connection_2)
        await sut.on_event(
            {"foo": "bar"},
            recipents=[user_token_1.user_id, user_token_2.user_id],
        )

        connection_1.write.assert_awaited_once_with('{"foo": "bar"}')
        connection_2.write.assert_not_awaited()


class TestAddProtocol:
    def test_returns_tuicub_protocol(self, sut):
        result = sut.add_protocol()

        assert isinstance(result, TuicubProtocol)
