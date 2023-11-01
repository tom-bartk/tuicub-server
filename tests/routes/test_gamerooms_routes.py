from collections.abc import Callable
from unittest.mock import create_autospec

import pytest

from src.tuicubserver.controllers.gamerooms import GameroomsController
from src.tuicubserver.routes.gamerooms import attach_gamerooms_routes


@pytest.fixture()
def gamerooms_controller() -> GameroomsController:
    return create_autospec(GameroomsController)


@pytest.fixture()
def sut(gamerooms_controller, with_base_context, with_context, app) -> Callable[[], None]:
    def wrapped() -> None:
        attach_gamerooms_routes(
            app=app,
            controller=gamerooms_controller,
            with_context=with_context,
            with_base_context=with_base_context,
        )

    return wrapped


class TestPostGamerooms:
    def test_calls_controller_create_gameroom(
        self, sut, gamerooms_controller, flask_client
    ) -> None:
        sut()
        flask_client.post("/gamerooms")

        gamerooms_controller.create_gameroom.assert_called_once()

    def test_authorizes_user(
        self, sut, gamerooms_controller, flask_client, auth_service
    ) -> None:
        sut()
        flask_client.post("/gamerooms")

        auth_service.authorize.assert_called_once()


class TestGetGamerooms:
    def test_calls_controller_get_gamerooms(
        self, sut, gamerooms_controller, flask_client
    ) -> None:
        sut()
        flask_client.get("/gamerooms")

        gamerooms_controller.get_gamerooms.assert_called_once()

    def test_authorizes_user(
        self, sut, gamerooms_controller, flask_client, auth_service
    ) -> None:
        sut()
        flask_client.post("/gamerooms")

        auth_service.authorize.assert_called_once()


class TestPostGameroomsIdUsers:
    def test_calls_controller_join_gameroom(
        self, sut, gamerooms_controller, flask_client
    ) -> None:
        sut()
        flask_client.post("/gamerooms/1/users")

        gamerooms_controller.join_gameroom.assert_called_once()

    def test_authorizes_user(
        self, sut, gamerooms_controller, flask_client, auth_service
    ) -> None:
        sut()
        flask_client.post("/gamerooms/1/users")

        auth_service.authorize.assert_called_once()


class TestDeleteGameroomsIdUsers:
    def test_calls_controller_leave_gameroom(
        self, sut, gamerooms_controller, flask_client
    ) -> None:
        sut()
        flask_client.delete("/gamerooms/1/users")

        gamerooms_controller.leave_gameroom.assert_called_once()

    def test_authorizes_user(
        self, sut, gamerooms_controller, flask_client, auth_service
    ) -> None:
        sut()
        flask_client.delete("/gamerooms/1/users")

        auth_service.authorize.assert_called_once()


class TestDeleteGameroomsId:
    def test_calls_controller_delete_gameroom(
        self, sut, gamerooms_controller, flask_client
    ) -> None:
        sut()
        flask_client.delete("/gamerooms/1")

        gamerooms_controller.delete_gameroom.assert_called_once()

    def test_authorizes_user(
        self, sut, gamerooms_controller, flask_client, auth_service
    ) -> None:
        sut()
        flask_client.delete("/gamerooms/1")

        auth_service.authorize.assert_called_once()


class TestPostGameroomsIdGame:
    def test_calls_controller_start_game(
        self, sut, gamerooms_controller, flask_client
    ) -> None:
        sut()
        flask_client.post("/gamerooms/1/game")

        gamerooms_controller.start_game.assert_called_once()

    def test_authorizes_user(
        self, sut, gamerooms_controller, flask_client, auth_service
    ) -> None:
        sut()
        flask_client.post("/gamerooms/1/game")

        auth_service.authorize.assert_called_once()


class TestPostGameroomsDisconnect:
    def test_calls_controller_start_game(
        self, sut, gamerooms_controller, flask_client
    ) -> None:
        sut()
        flask_client.post("/gamerooms/disconnect")

        gamerooms_controller.disconnect.assert_called_once()
