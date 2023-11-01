from unittest.mock import Mock, create_autospec
from uuid import uuid4

import pytest

from src.tuicubserver.models.game import (
    Board,
    Game,
    GameEndedError,
    MovesPerformedError,
    NoMovesPerformedError,
    NotUserTurnError,
    Player,
    Tileset,
    UserNotInGameError,
)
from src.tuicubserver.models.gameroom import Gameroom
from src.tuicubserver.services.game_toolkit import (
    GameToolkit,
    InvalidMeldError,
    InvalidTilesetsError,
)
from src.tuicubserver.services.games import GameDisconnectResult, GamesService


@pytest.fixture()
def gameroom() -> Gameroom:
    return create_autospec(Gameroom)


@pytest.fixture()
def sut(games_repository, game_toolkit, rng_service) -> GamesService:
    return GamesService(
        game_toolkit=game_toolkit,
        games_repository=games_repository,
        rng_service=rng_service,
    )


@pytest.fixture()
def board() -> list[list[int]]:
    return [[1, 2, 3], [4, 5, 6]]


@pytest.fixture()
def new_board() -> Board:
    return create_autospec(Board)


@pytest.fixture()
def new_rack() -> Tileset:
    return create_autospec(Tileset)


@pytest.fixture()
def player() -> Player:
    return create_autospec(Player)


@pytest.fixture()
def game(player) -> Game:
    game = create_autospec(Game)
    game.player_for_user_id = Mock(return_value=player)
    return game


@pytest.fixture()
def game_without_player(player) -> Game:
    game = create_autospec(Game)
    game.player_for_user_id = Mock(
        side_effect=UserNotInGameError(user_id=uuid4(), players=())
    )
    return game


@pytest.fixture()
def ended_game(player) -> Game:
    game = create_autospec(Game)
    game.ensure_not_ended = Mock(side_effect=GameEndedError)
    return game


@pytest.fixture()
def game_with_player_no_turn(player) -> Game:
    game = create_autospec(Game)
    game.player_for_user_id = Mock(return_value=player)
    game.ensure_has_turn = Mock(
        side_effect=NotUserTurnError(player_id=uuid4(), current_player_id=uuid4())
    )
    return game


@pytest.fixture()
def game_toolkit(new_board, new_rack) -> GameToolkit:
    game_toolkit = create_autospec(GameToolkit)
    game_toolkit.perform_move = Mock(return_value=(new_rack, new_board))
    game_toolkit.draw_tile = Mock(return_value=(Mock(), Mock()))
    return game_toolkit


class TestMove:
    def test_when_user_not_in_game__raises_user_not_in_game_error(
        self, sut, context, games_repository, game_without_player
    ) -> None:
        games_repository.get_game_by_id = Mock(return_value=game_without_player)

        with pytest.raises(UserNotInGameError):
            sut.move(context, game_id="foo", board=[])

    def test_when_user_has_no_turn__raises_not_user_turn_error(
        self, sut, context, games_repository, game_with_player_no_turn
    ) -> None:
        games_repository.get_game_by_id = Mock(return_value=game_with_player_no_turn)

        with pytest.raises(NotUserTurnError):
            sut.move(context, game_id="foo", board=[])

    def test_when_game_ended__raises_game_ended_error(
        self, sut, context, games_repository, ended_game
    ) -> None:
        games_repository.get_game_by_id = Mock(return_value=ended_game)

        with pytest.raises(GameEndedError):
            sut.move(context, game_id="foo", board=[])

    def test_when_preconditions_ok__performs_move_using_toolkit(
        self, sut, context, games_repository, game_toolkit, game, player, board
    ) -> None:
        games_repository.get_game_by_id = Mock(return_value=game)

        sut.move(context, game_id="foo", board=board)

        game_toolkit.perform_move.assert_called_once_with(
            rack=player.rack, current=game.game_state.board, candidate=Board.create(board)
        )

    def test_when_preconditions_ok__saves_game_with_new_move(
        self, sut, context, games_repository, game, player, new_rack, new_board
    ) -> None:
        expected = Mock()
        games_repository.get_game_by_id = Mock(return_value=game)
        game.with_new_move = Mock(return_value=expected)

        sut.move(context, game_id="foo", board=[])

        game.with_new_move.assert_called_once_with(
            rack=new_rack, board=new_board, player=player
        )
        games_repository.save_game.assert_called_once_with(
            session=context.session, game=expected
        )

    def test_when_preconditions_ok__returns_game_with_new_move(
        self, sut, context, games_repository, game, player, new_rack, new_board
    ) -> None:
        expected = Mock()
        games_repository.get_game_by_id = Mock(return_value=game)
        game.with_new_move = Mock(return_value=expected)

        result = sut.move(context, game_id="foo", board=[])

        assert result == expected


class TestUndo:
    def test_when_user_not_in_game__raises_user_not_in_game_error(
        self, sut, context, games_repository, game_without_player
    ) -> None:
        games_repository.get_game_by_id = Mock(return_value=game_without_player)

        with pytest.raises(UserNotInGameError):
            sut.undo(context, game_id="foo")

    def test_when_user_has_no_turn__raises_not_user_turn_error(
        self, sut, context, games_repository, game_with_player_no_turn
    ) -> None:
        games_repository.get_game_by_id = Mock(return_value=game_with_player_no_turn)

        with pytest.raises(NotUserTurnError):
            sut.undo(context, game_id="foo")

    def test_when_game_ended__raises_game_ended_error(
        self, sut, context, games_repository, ended_game
    ) -> None:
        games_repository.get_game_by_id = Mock(return_value=ended_game)

        with pytest.raises(GameEndedError):
            sut.undo(context, game_id="foo")

    def test_when_preconditions_ok__saves_game_with_previous_move(
        self, sut, context, games_repository, game, player
    ) -> None:
        expected = Mock()
        games_repository.get_game_by_id = Mock(return_value=game)
        game.with_undo = Mock(return_value=expected)

        sut.undo(context, game_id="foo")

        game.with_undo.assert_called_once_with(player=player)
        games_repository.save_game.assert_called_once_with(
            session=context.session, game=expected
        )

    def test_when_preconditions_ok__returns_game_with_previous_move(
        self, sut, context, games_repository, game, player
    ) -> None:
        expected = Mock()
        games_repository.get_game_by_id = Mock(return_value=game)
        game.with_undo = Mock(return_value=expected)

        result = sut.undo(context, game_id="foo")

        assert result == expected


class TestRedo:
    def test_when_user_not_in_game__raises_user_not_in_game_error(
        self, sut, context, games_repository, game_without_player
    ) -> None:
        games_repository.get_game_by_id = Mock(return_value=game_without_player)

        with pytest.raises(UserNotInGameError):
            sut.redo(context, game_id="foo")

    def test_when_user_has_no_turn__raises_not_user_turn_error(
        self, sut, context, games_repository, game_with_player_no_turn
    ) -> None:
        games_repository.get_game_by_id = Mock(return_value=game_with_player_no_turn)

        with pytest.raises(NotUserTurnError):
            sut.redo(context, game_id="foo")

    def test_when_game_ended__raises_game_ended_error(
        self, sut, context, games_repository, ended_game
    ) -> None:
        games_repository.get_game_by_id = Mock(return_value=ended_game)

        with pytest.raises(GameEndedError):
            sut.redo(context, game_id="foo")

    def test_when_preconditions_ok__saves_game_with_next_move(
        self, sut, context, games_repository, game, player
    ) -> None:
        expected = Mock()
        games_repository.get_game_by_id = Mock(return_value=game)
        game.with_redo = Mock(return_value=expected)

        sut.redo(context, game_id="foo")

        game.with_redo.assert_called_once_with(player=player)
        games_repository.save_game.assert_called_once_with(
            session=context.session, game=expected
        )

    def test_when_preconditions_ok__returns_game_with_next_move(
        self, sut, context, games_repository, game, player
    ) -> None:
        expected = Mock()
        games_repository.get_game_by_id = Mock(return_value=game)
        game.with_redo = Mock(return_value=expected)

        result = sut.redo(context, game_id="foo")

        assert result == expected


class TestEndTurn:
    def test_when_user_not_in_game__raises_user_not_in_game_error(
        self, sut, context, games_repository, game_without_player
    ) -> None:
        games_repository.get_game_by_id = Mock(return_value=game_without_player)

        with pytest.raises(UserNotInGameError):
            sut.end_turn(context, game_id="foo")

    def test_when_user_has_no_turn__raises_not_user_turn_error(
        self, sut, context, games_repository, game_with_player_no_turn
    ) -> None:
        games_repository.get_game_by_id = Mock(return_value=game_with_player_no_turn)

        with pytest.raises(NotUserTurnError):
            sut.end_turn(context, game_id="foo")

    def test_when_game_ended__raises_game_ended_error(
        self, sut, context, games_repository, ended_game
    ) -> None:
        games_repository.get_game_by_id = Mock(return_value=ended_game)

        with pytest.raises(GameEndedError):
            sut.end_turn(context, game_id="foo")

    def test_when_turn_has_no_moves__raises_no_moves_performed_error(
        self, sut, context, games_repository, game
    ) -> None:
        game.turn.ensure_has_moves = Mock(side_effect=NoMovesPerformedError(revision=0))
        games_repository.get_game_by_id = Mock(return_value=game)

        with pytest.raises(NoMovesPerformedError):
            sut.end_turn(context, game_id="foo")

    def test_when_board_invalid__raises_invalid_move_error(
        self, sut, context, games_repository, game, game_toolkit
    ) -> None:
        games_repository.get_game_by_id = Mock(return_value=game)
        game_toolkit.ensure_board_valid = Mock(
            side_effect=InvalidTilesetsError(
                rack=Tileset(), current=Board(), candidate=Board()
            )
        )

        with pytest.raises(InvalidTilesetsError):
            sut.end_turn(context, game_id="foo")

    def test_when_preconditions_ok__no_meld__meld_invalid__raises_invalid_meld_error(
        self, sut, context, games_repository, game, game_toolkit
    ) -> None:
        games_repository.get_game_by_id = Mock(return_value=game)
        game.has_made_meld = Mock(return_value=False)
        game_toolkit.ensure_meld_valid = Mock(
            side_effect=InvalidMeldError(
                rack=Tileset(), current=Board(), candidate=Board()
            )
        )

        with pytest.raises(InvalidMeldError):
            sut.end_turn(context, game_id="foo")

    def test_when_preconditions_ok__no_meld__meld_valid__marks_user_as_made_meld(
        self, sut, context, games_repository, game, game_toolkit
    ) -> None:
        games_repository.get_game_by_id = Mock(return_value=game)
        game.has_made_meld = Mock(return_value=False)

        sut.end_turn(context, game_id="foo")

        game.with_new_meld.assert_called_once()

    def test_when_preconditions_ok__returns_game_with_new_turn(
        self, sut, context, games_repository, game, game_toolkit
    ) -> None:
        expected = Mock()
        games_repository.get_game_by_id = Mock(return_value=game)
        game.with_next_turn = Mock(return_value=expected)

        result = sut.end_turn(context, game_id="foo")

        assert result == expected


class TestDraw:
    def test_when_user_not_in_game__raises_user_not_in_game_error(
        self, sut, context, games_repository, game_without_player
    ) -> None:
        games_repository.get_game_by_id = Mock(return_value=game_without_player)

        with pytest.raises(UserNotInGameError):
            sut.draw(context, game_id="foo")

    def test_when_user_has_no_turn__raises_not_user_turn_error(
        self, sut, context, games_repository, game_with_player_no_turn
    ) -> None:
        games_repository.get_game_by_id = Mock(return_value=game_with_player_no_turn)

        with pytest.raises(NotUserTurnError):
            sut.draw(context, game_id="foo")

    def test_when_game_ended__raises_game_ended_error(
        self, sut, context, games_repository, ended_game
    ) -> None:
        games_repository.get_game_by_id = Mock(return_value=ended_game)

        with pytest.raises(GameEndedError):
            sut.draw(context, game_id="foo")

    def test_when_turn_has_moves__raises_has_performed_moves_error(
        self, sut, context, games_repository, game
    ) -> None:
        game.turn.ensure_has_no_moves = Mock(side_effect=MovesPerformedError(revision=0))
        games_repository.get_game_by_id = Mock(return_value=game)

        with pytest.raises(MovesPerformedError):
            sut.draw(context, game_id="foo")

    def test_when_preconditions_ok__draws_tile_from_pile(
        self, sut, context, games_repository, game
    ) -> None:
        games_repository.get_game_by_id = Mock(return_value=game)

        sut.draw(context, game_id="foo")

        game.game_state.pile.draw.assert_called_once()

    def test_when_preconditions_ok__returns_game_with_next_turn(
        self, sut, context, games_repository, game, game_toolkit
    ) -> None:
        expected = Mock()
        games_repository.get_game_by_id = Mock(return_value=game)
        game.with_drawn_tile = Mock(return_value=game)
        game.with_next_turn = Mock(return_value=expected)

        _, result = sut.draw(context, game_id="foo")

        assert result == expected


class TestDisconnect:
    def test_when_user_not_in_game__raises_user_not_in_game_error(
        self, sut, context, game_without_player
    ) -> None:
        with pytest.raises(UserNotInGameError):
            sut.disconnect(context, game=game_without_player)

    def test_when_game_ended__raises_game_ended_error(
        self, sut, context, ended_game
    ) -> None:
        with pytest.raises(GameEndedError):
            sut.disconnect(context, game=ended_game)

    def test_when_preconditions_ok__saves_game_with_disconnected_player(
        self, sut, context, games_repository, game
    ) -> None:
        expected_game = Mock()
        game.with_disconnected_player = Mock(return_value=(expected_game, Mock()))

        sut.disconnect(context, game=game)

        games_repository.save_game.assert_called_once_with(
            session=context.session, game=expected_game
        )

    def test_when_preconditions_ok__returns_correct_disconnect_result(
        self, sut, context, games_repository, game
    ) -> None:
        _game = create_autospec(Game)
        _turn = Mock()
        _player = Mock()
        game.with_disconnected_player = Mock(return_value=(_game, _turn))
        game.player_for_user_id = Mock(return_value=_player)
        expected = GameDisconnectResult(game=_game, player=_player, turn=_turn)

        result = sut.disconnect(context, game=game)

        assert result == expected


class TestDelete:
    def test_deletes_game(self, sut, context, game, games_repository) -> None:
        sut.delete(context, game=game)

        games_repository.delete_game.assert_called_once_with(
            session=context.session, game=game
        )
