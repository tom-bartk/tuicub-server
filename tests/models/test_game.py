from collections.abc import Callable
from uuid import UUID, uuid4

import pytest

from src.tuicubserver.models.game import (
    Board,
    Game,
    GameEndedError,
    GameState,
    Move,
    NotUserTurnError,
    Pile,
    Player,
    Tileset,
    Turn,
    UserNotInGameError,
)
from tests.utils import not_raises


@pytest.fixture()
def make_turn(
    turn_id, game_id, player_id_1
) -> Callable[
    [int | None, UUID | None, Tileset | None, Board | None, tuple[Move, ...] | None], Turn
]:
    def factory(
        revision: int | None = None,
        player_id: UUID | None = None,
        starting_rack: Tileset | None = None,
        starting_board: Board | None = None,
        moves: tuple[Move, ...] | None = None,
    ) -> Turn:
        return Turn(
            id=turn_id,
            revision=revision if revision is not None else 0,
            starting_rack=starting_rack or Tileset.create([7, 8, 9]),
            starting_board=starting_board or Board.create([[1, 2, 3], [4, 5, 6]]),
            player_id=player_id or player_id_1,
            game_id=game_id,
            moves=moves if moves is not None else (),
        )

    return factory


@pytest.fixture()
def make_game_state(
    game_state_id, game_id, player_1, player_2
) -> Callable[[tuple[Player, ...] | None, Pile | None, Board | None], GameState]:
    def factory(
        players: tuple[Player, ...] | None = None,
        pile: Pile | None = None,
        board: Board | None = None,
    ) -> GameState:
        return GameState(
            id=game_state_id,
            players=players or (player_1, player_2),
            game_id=game_id,
            board=board or Board.create([[1, 2, 3], [4, 5, 6]]),
            pile=pile or Pile([16, 17, 18]),
        )

    return factory


@pytest.fixture()
def make_sut(
    gameroom_id,
    game_id,
    make_turn,
    make_game_state,
    user_id_1,
    user_id_2,
    player_id_1,
    player_id_2,
) -> Callable[
    [
        Player | None,
        GameState | None,
        Turn | None,
        tuple[UUID, ...] | None,
        tuple[UUID, ...] | None,
    ],
    Game,
]:
    def factory(
        winner: Player | None = None,
        game_state: GameState | None = None,
        turn: Turn | None = None,
        turn_order: tuple[UUID, ...] | None = None,
        made_meld: tuple[UUID, ...] | None = None,
    ) -> Game:
        return Game(
            id=game_id,
            gameroom_id=gameroom_id,
            game_state=game_state or make_game_state(),
            turn=turn or make_turn(),
            turn_order=turn_order
            if turn_order is not None
            else (player_id_1, player_id_2),
            winner=winner,
            made_meld=made_meld if made_meld is not None else (),
        )

    return factory


class TestNewTiles:
    def test_returns_list_of_tiles_present_on_board_but_not_in_turn_starting_board(
        self, make_sut, make_turn, make_game_state
    ) -> None:
        sut = make_sut(
            game_state=make_game_state(board=Board.create([[1, 2, 3, 4], [5, 6, 7, 8]])),
            turn=make_turn(starting_board=Board.create([[1, 2, 3], [4, 5, 6]])),
        )
        expected = [7, 8]

        result = sut.new_tiles()

        assert result == expected


class TestCurrentPlayer:
    def test_returns_current_player(
        self, make_sut, make_turn, make_game_state, player_1, player_2, player_id_2
    ) -> None:
        sut = make_sut(
            game_state=make_game_state(players=(player_1, player_2)),
            turn=make_turn(player_id=player_id_2),
        )
        expected = player_2

        result = sut.current_player()

        assert result == expected


class TestPlayerAfter:
    def test_when_player_is_last_in_turn_order__returns_first_from_turn_order(
        self, make_sut, make_game_state, player_1, player_2, user_id_1, user_id_2
    ) -> None:
        sut = make_sut(
            game_state=make_game_state(players=(player_1, player_2)),
            turn_order=(user_id_1, user_id_2),
        )
        expected = player_1

        result = sut.player_after(player_2)

        assert result == expected

    def test_when_player_is_not_last_in_turn_order__returns_next_from_turn_order(
        self, make_sut, make_game_state, player_1, player_2, user_id_1, user_id_2
    ) -> None:
        sut = make_sut(
            game_state=make_game_state(players=(player_1, player_2)),
            turn_order=(user_id_1, user_id_2),
        )
        expected = player_2

        result = sut.player_after(player_1)

        assert result == expected


class TestPlayerForUser:
    def test_when_user_in_game__returns_player(
        self, make_sut, make_game_state, player_1, player_2, user_id_1
    ) -> None:
        sut = make_sut(game_state=make_game_state(players=(player_1, player_2)))
        expected = player_1

        result = sut.player_for_user_id(user_id_1)

        assert result == expected

    def test_when_user_not_in_game__raises_user_not_in_game_error(
        self, make_sut, make_game_state, player_1, player_2
    ) -> None:
        sut = make_sut(game_state=make_game_state(players=(player_1, player_2)))

        with pytest.raises(UserNotInGameError):
            sut.player_for_user_id(uuid4())


class TestWithDisconnectedPlayer:
    def test_when_2_players__returns_game_with_other_player_as_winner(
        self, make_sut, make_game_state, player_1, player_2, rng_service
    ) -> None:
        sut = make_sut(game_state=make_game_state(players=(player_1, player_2)))

        game, turn = sut.with_disconnected_player(player_2, rng=rng_service)

        assert game.winner == player_1
        assert not turn

    def test_when_more_than_2_players__not_players_turn__returns_game_without_player__none_turn(  # noqa: E501
        self,
        make_sut,
        make_game_state,
        make_turn,
        player_1,
        player_2,
        player_3,
        rng_service,
        user_id_1,
        user_id_2,
        user_id_3,
    ) -> None:
        sut = make_sut(
            game_state=make_game_state(players=(player_1, player_2, player_3)),
            turn=make_turn(player_id=player_1),
            turn_order=(user_id_1, user_id_2, user_id_3),
        )

        game, turn = sut.with_disconnected_player(player_3, rng=rng_service)

        assert not game.winner
        assert not turn
        assert game.game_state.players == (player_1, player_2)
        assert game.turn_order == (user_id_1, user_id_2)

    def test_when_more_than_2_players__returns_rack_to_pile(
        self, make_sut, make_game_state, player_1, player_2, player_3, rng_service
    ) -> None:
        sut = make_sut(
            game_state=make_game_state(
                players=(player_1, player_2, player_3), pile=Pile([1, 2, 3])
            )
        )

        game, _ = sut.with_disconnected_player(player_3, rng=rng_service)

        assert game.game_state.pile.tiles == (1, 2, 3, *player_3.rack.tiles)

    def test_when_more_than_2_players__players_turn__returns_game_without_player_with_next_turn(  # noqa: E501
        self,
        make_sut,
        make_game_state,
        make_turn,
        player_1,
        player_2,
        player_3,
        rng_service,
        user_id_1,
        user_id_2,
        user_id_3,
    ) -> None:
        sut = make_sut(
            game_state=make_game_state(players=(player_1, player_2, player_3)),
            turn=make_turn(player_id=player_2.id),
            turn_order=(user_id_1, user_id_2, user_id_3),
        )

        game, turn = sut.with_disconnected_player(player_2, rng=rng_service)

        assert game.turn == turn
        assert turn.player_id == player_3.id
        assert turn.starting_rack == player_3.rack


class TestEnsureHasTurn:
    def test_when_player_does_not_have_turn__raises_not_user_turn_error(
        self, make_sut, make_game_state, make_turn, player_1, player_2, player_id_2
    ) -> None:
        sut = make_sut(
            game_state=make_game_state(players=(player_1, player_2)),
            turn=make_turn(player_id=player_id_2),
        )

        with pytest.raises(NotUserTurnError):
            sut.ensure_has_turn(player_1)

    def test_when_player_has_turn__does_not_raise_user_turn_error(
        self, make_sut, make_game_state, make_turn, player_1, player_2, player_id_2
    ) -> None:
        sut = make_sut(
            game_state=make_game_state(players=(player_1, player_2)),
            turn=make_turn(player_id=player_id_2),
        )

        with not_raises(NotUserTurnError):
            sut.ensure_has_turn(player_2)


class TestEnsureNotEnded:
    def test_when_winner_is_not_none__raises_game_ended_error(
        self, make_sut, player_1
    ) -> None:
        sut = make_sut(winner=player_1)

        with pytest.raises(GameEndedError):
            sut.ensure_not_ended()

    def test_when_winner_is_none__does_not_raise_game_ended_error(self, make_sut) -> None:
        sut = make_sut(winner=None)

        with not_raises(GameEndedError):
            sut.ensure_not_ended()


class TestHasMadeMeld:
    def test_when_user_id_in_made_meld__returns_true(
        self, make_sut, user_id_1, user_id_2
    ) -> None:
        sut = make_sut(made_meld=(user_id_1, user_id_2))
        expected = True

        result = sut.has_made_meld(user_id=user_id_1)

        assert result == expected

    def test_when_user_id_not_in_made_meld__returns_false(
        self, make_sut, user_id_1, user_id_2
    ) -> None:
        sut = make_sut(made_meld=(user_id_2,))
        expected = False

        result = sut.has_made_meld(user_id=user_id_1)

        assert result == expected


class TestWithNewMeld:
    def test_returns_game_with_new_user_id_in_made_meld(
        self, make_sut, user_id_1, user_id_2
    ) -> None:
        sut = make_sut(made_meld=(user_id_1,))
        expected = (user_id_1, user_id_2)

        result = sut.with_new_meld(user_id=user_id_2)

        assert result.made_meld == expected


class TestWithNextTurn:
    def test_when_current_player_has_empty_rack__returns_game_with_current_player_as_winner(  # noqa: E501
        self, make_sut, player_id_1, player_2, user_id_1, make_game_state, make_turn
    ) -> None:
        current_player = Player(
            id=player_id_1, user_id=user_id_1, name="foo", rack=Tileset.create([])
        )
        sut = make_sut(
            game_state=make_game_state(players=(current_player, player_2)),
            turn=make_turn(player_id=player_id_1),
        )

        result = sut.with_next_turn(current_player=current_player)

        assert result.winner == current_player

    def test_when_current_player_has_nonempty_rack__returns_game_with_next_turn(
        self,
        make_sut,
        player_1,
        player_2,
        user_id_1,
        user_id_2,
        make_game_state,
        make_turn,
    ) -> None:
        current_board = Board.create([[1, 2, 3], [4, 5, 6]])
        sut = make_sut(
            game_state=make_game_state(players=(player_1, player_2), board=current_board),
            turn=make_turn(player_id=player_1.id),
            turn_order=(user_id_1, user_id_2),
        )

        result = sut.with_next_turn(current_player=player_1)

        assert result.turn.player_id == player_2.id
        assert result.turn.starting_board == current_board
        assert result.turn.starting_rack == player_2.rack


class TestWithNewMove:
    def test_returns_game_with_updated_board_and_turn(
        self, make_sut, player_1, player_2, make_game_state, make_turn
    ) -> None:
        rack = Tileset.create([7, 8, 9])
        board = Board.create([[1, 2, 3], [4, 5, 6], [10, 11, 12]])
        sut = make_sut(
            game_state=make_game_state(players=(player_1, player_2)),
            turn=make_turn(revision=0, moves=(), player_id=player_1.id),
        )

        result = sut.with_new_move(rack=rack, board=board, player=player_1)

        assert result.game_state.board == board
        assert result.game_state.players[0].rack == rack
        assert result.turn.revision == 1
        assert len(result.turn.moves) == 1
        assert result.turn.moves[0].rack == rack
        assert result.turn.moves[0].board == board


class TestWithUndo:
    def test_when_turn_revision_gte_2__returns_game_with_board_and_rack_from_previous_move(  # noqa: E501
        self, make_sut, player_1, player_2, move_1, move_2, make_game_state, make_turn
    ) -> None:
        sut = make_sut(
            game_state=make_game_state(players=(player_1, player_2)),
            turn=make_turn(revision=2, moves=(move_1, move_2), player_id=player_1.id),
        )

        result = sut.with_undo(player=player_1)

        assert result.game_state.board == move_1.board
        assert result.game_state.players[0].rack == move_1.rack
        assert result.turn.revision == 1

    def test_when_turn_revision_eq_1__returns_game_with_board_and_rack_from_turn_starting(  # noqa: E501
        self, make_sut, player_1, player_2, move_1, make_game_state, make_turn
    ) -> None:
        sut = make_sut(
            game_state=make_game_state(players=(player_1, player_2)),
            turn=make_turn(revision=1, moves=(move_1,), player_id=player_1.id),
        )

        result = sut.with_undo(player=player_1)

        assert result.game_state.board == result.turn.starting_board
        assert result.game_state.players[0].rack == result.turn.starting_rack
        assert result.turn.revision == 0


class TestWithRedo:
    def test_returns_game_with_board_and_rack_from_next_move(
        self, make_sut, player_1, player_2, move_1, move_2, make_game_state, make_turn
    ) -> None:
        sut = make_sut(
            game_state=make_game_state(players=(player_1, player_2)),
            turn=make_turn(revision=1, moves=(move_1, move_2), player_id=player_1.id),
        )

        result = sut.with_redo(player=player_1)

        assert result.game_state.board == move_2.board
        assert result.game_state.players[0].rack == move_2.rack
        assert result.turn.revision == 2


class TestWithDrawnTile:
    def test_returns_game_with_updated_player_rack(
        self, make_sut, player_1, player_2, make_game_state
    ) -> None:
        sut = make_sut(game_state=make_game_state(players=(player_1, player_2)))

        result = sut.with_drawn_tile(tile=105, player=player_1)

        assert result.game_state.players[0].rack.tiles == (7, 8, 9, 105)
