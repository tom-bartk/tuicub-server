from collections.abc import Callable
from unittest.mock import create_autospec

import pytest

from src.tuicubserver.controllers.games import GamesController
from src.tuicubserver.routes.games import attach_games_routes


@pytest.fixture()
def games_controller() -> GamesController:
    return create_autospec(GamesController)


@pytest.fixture()
def sut(games_controller, with_base_context, with_context, app) -> Callable[[], None]:
    def wrapped() -> None:
        attach_games_routes(
            app=app, controller=games_controller, with_context=with_context
        )

    return wrapped


class TestPostGamesIdMoves:
    def test_calls_controller_move(self, sut, games_controller, flask_client) -> None:
        sut()
        flask_client.post("/games/1/moves")

        games_controller.move.assert_called_once()

    def test_authorizes_user(
        self, sut, games_controller, flask_client, auth_service
    ) -> None:
        sut()
        flask_client.post("/games/1/moves")

        auth_service.authorize.assert_called_once()


class TestDeleteGamesIdMoves:
    def test_calls_controller_undo(self, sut, games_controller, flask_client) -> None:
        sut()
        flask_client.delete("/games/1/moves")

        games_controller.undo.assert_called_once()

    def test_authorizes_user(
        self, sut, games_controller, flask_client, auth_service
    ) -> None:
        sut()
        flask_client.delete("/games/1/moves")

        auth_service.authorize.assert_called_once()


class TestPatchGamesIdMoves:
    def test_calls_controller_redo(self, sut, games_controller, flask_client) -> None:
        sut()
        flask_client.patch("/games/1/moves")

        games_controller.redo.assert_called_once()

    def test_authorizes_user(
        self, sut, games_controller, flask_client, auth_service
    ) -> None:
        sut()
        flask_client.patch("/games/1/moves")

        auth_service.authorize.assert_called_once()


class TestPostGamesIdTurnsEnd:
    def test_calls_controller_end_turn(self, sut, games_controller, flask_client) -> None:
        sut()
        flask_client.post("/games/1/turns/end")

        games_controller.end_turn.assert_called_once()

    def test_authorizes_user(
        self, sut, games_controller, flask_client, auth_service
    ) -> None:
        sut()
        flask_client.post("/games/1/turns/end")

        auth_service.authorize.assert_called_once()


class TestPostGamesIdTurnsDraw:
    def test_calls_controller_draw(self, sut, games_controller, flask_client) -> None:
        sut()
        flask_client.post("/games/1/turns/draw")

        games_controller.draw.assert_called_once()

    def test_authorizes_user(
        self, sut, games_controller, flask_client, auth_service
    ) -> None:
        sut()
        flask_client.post("/games/1/turns/draw")

        auth_service.authorize.assert_called_once()
