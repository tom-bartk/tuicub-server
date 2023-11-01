from unittest.mock import Mock, PropertyMock, create_autospec

import pytest

from src.tuicubserver.common.errors import ValidationError
from src.tuicubserver.controllers.games import GamesController
from src.tuicubserver.models.dto import GameStateDto
from src.tuicubserver.models.game import Game


@pytest.fixture()
def sut(gamerooms_service, games_service, messages_service) -> GamesController:
    return GamesController(
        games_service=games_service,
        gamerooms_service=gamerooms_service,
        messages_service=messages_service,
    )


class TestMove:
    def test_returns_serialized_game_state(
        self, sut, app, context, games_service, game, user
    ):
        games_service.move = Mock(return_value=game)
        expected = GameStateDto.create(game, user).serialize()

        with app.test_request_context(json={"board": [[1, 2, 3]]}):
            result = sut.move(context=context, id="foo")

            assert result == expected

    def test_passes_context_to_service(self, sut, app, context, games_service, game):
        games_service.move = Mock(return_value=game)

        with app.test_request_context(json={"board": [[1, 2, 3]]}):
            sut.move(context=context, id="foo")

            games_service.move.assert_called_once_with(
                context=context, game_id="foo", board=[[1, 2, 3]]
            )

    def test_sends_tiles_moved_message(
        self, sut, app, context, game, messages_service, games_service
    ):
        games_service.move = Mock(return_value=game)

        with app.test_request_context(json={"board": [[1, 2, 3]]}):
            sut.move(context=context, id="foo")

            messages_service.tiles_moved.assert_called_once_with(
                sender=context.user, game=game
            )

    def test_when_board_not_in_body__raises_validation_error(
        self, sut, app, base_context
    ) -> None:
        with app.test_request_context(json={}):
            with pytest.raises(ValidationError, match="A valid 'board' is required"):
                sut.move(context=base_context, id="foo")

    def test_when_board_contains_non_list_element__raises_validation_error(
        self, sut, app, base_context
    ) -> None:
        with app.test_request_context(json={"board": ["foo", [1, 2, 3]]}):
            with pytest.raises(ValidationError, match="Not a valid list"):
                sut.move(context=base_context, id="foo")

    def test_when_board_contains_out_of_range_element__raises_validation_error(
        self, sut, app, base_context
    ) -> None:
        with app.test_request_context(json={"board": [[1, 1337, 3]]}):
            with pytest.raises(
                ValidationError,
                match="greater than or equal to 0 and less than or equal to 105",
            ):
                sut.move(context=base_context, id="foo")


class TestUndo:
    def test_returns_serialized_game_state(self, sut, context, games_service, game, user):
        games_service.undo = Mock(return_value=game)
        expected = GameStateDto.create(game, user).serialize()

        result = sut.undo(context=context, id="foo")

        assert result == expected

    def test_passes_context_to_service(self, sut, context, games_service, game):
        games_service.undo = Mock(return_value=game)

        sut.undo(context=context, id="foo")

        games_service.undo.assert_called_once_with(context=context, game_id="foo")

    def test_sends_tiles_moved_message(
        self, sut, context, game, messages_service, games_service
    ):
        games_service.undo = Mock(return_value=game)

        sut.undo(context=context, id="foo")

        messages_service.tiles_moved.assert_called_once_with(
            sender=context.user, game=game
        )


class TestRedo:
    def test_returns_serialized_game_state(self, sut, context, games_service, game, user):
        games_service.redo = Mock(return_value=game)
        expected = GameStateDto.create(game, user).serialize()

        result = sut.redo(context=context, id="foo")

        assert result == expected

    def test_passes_context_to_service(self, sut, context, games_service, game):
        games_service.redo = Mock(return_value=game)

        sut.redo(context=context, id="foo")

        games_service.redo.assert_called_once_with(context=context, game_id="foo")

    def test_sends_tiles_moved_message(
        self, sut, context, game, messages_service, games_service
    ):
        games_service.redo = Mock(return_value=game)

        sut.redo(context=context, id="foo")

        messages_service.tiles_moved.assert_called_once_with(
            sender=context.user, game=game
        )


class TestEndTurn:
    def test_returns_serialized_game_state(self, sut, context, games_service, game, user):
        games_service.end_turn = Mock(return_value=game)
        expected = GameStateDto.create(game, user).serialize()

        result = sut.end_turn(context=context, id="foo")

        assert result == expected

    def test_passes_context_to_service(self, sut, context, games_service, game):
        games_service.end_turn = Mock(return_value=game)

        sut.end_turn(context=context, id="foo")

        games_service.end_turn.assert_called_once_with(context=context, game_id="foo")

    def test_sends_turn_ended_message(
        self, sut, context, game, messages_service, games_service
    ):
        games_service.end_turn = Mock(return_value=game)

        sut.end_turn(context=context, id="foo")

        messages_service.turn_ended.assert_called_once_with(
            sender=context.user, game=game
        )

    def test_when_game_has_winner__calls_finish_game_on_gamerooms_service(
        self, sut, context, games_service, gameroom_id, gamerooms_service
    ):
        game = create_autospec(Game)
        type(game).winner = PropertyMock(return_value=Mock())
        type(game).gameroom_id = PropertyMock(return_value=gameroom_id)
        games_service.end_turn = Mock(return_value=game)

        sut.end_turn(context=context, id="foo")

        gamerooms_service.finish_game.assert_called_once_with(
            context=context, gameroom_id=gameroom_id
        )


class TestDraw:
    def test_returns_serialized_game_state(self, sut, context, games_service, game, user):
        tile = Mock()
        games_service.draw = Mock(return_value=(tile, game))
        expected = GameStateDto.create(game, user).serialize()

        result = sut.draw(context=context, id="foo")

        assert result == expected

    def test_passes_context_to_service(self, sut, context, games_service, game):
        tile = Mock()
        games_service.draw = Mock(return_value=(tile, game))

        sut.draw(context=context, id="foo")

        games_service.draw.assert_called_once_with(context=context, game_id="foo")

    def test_sends_tile_drawn_message(
        self, sut, context, game, messages_service, games_service
    ):
        tile = Mock()
        games_service.draw = Mock(return_value=(tile, game))

        sut.draw(context=context, id="foo")

        messages_service.tile_drawn.assert_called_once_with(
            sender=context.user, tile=tile, game=game
        )
