from collections.abc import Callable
from uuid import UUID

import pytest

from src.tuicubserver.models.game import (
    Board,
    Move,
    MovesPerformedError,
    NoMovesPerformedError,
    NoMoveToRedoError,
    NoMoveToUndoError,
    Tileset,
    Turn,
)
from tests.utils import not_raises


@pytest.fixture()
def make_sut(
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
            starting_rack=starting_rack or Tileset.create([4, 5, 6, 7, 8, 9, 10, 11, 12]),
            starting_board=starting_board or Board.create([[1, 2, 3]]),
            player_id=player_id or player_id_1,
            game_id=game_id,
            moves=moves if moves is not None else (),
        )

    return factory


class TestWithNewMove:
    def test_when_moves_empty__revision_0__returns_turn_with_new_move_and_revision_1(
        self, make_sut
    ) -> None:
        sut = make_sut(moves=(), revision=0)
        rack = Tileset.create([7, 8, 9, 10, 11, 12])
        board = Board.create([[1, 2, 3], [4, 5, 6]])

        result = sut.with_new_move(rack, board)

        assert result.revision == 1
        assert len(result.moves) == 1
        assert result.moves[0].revision == 1
        assert result.moves[0].rack == rack
        assert result.moves[0].board == board

    def test_when_has_2_moves__revision_2__returns_turn_with_new_move_and_revision_3(
        self, make_sut, move_1, move_2
    ) -> None:
        sut = make_sut(moves=(move_1, move_2), revision=2)
        rack = Tileset.create([12])
        board = Board.create([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11]])

        result = sut.with_new_move(rack, board)

        assert result.revision == 3
        assert len(result.moves) == 3
        assert result.moves[2].revision == 3
        assert result.moves[2].rack == rack
        assert result.moves[2].board == board

    def test_when_has_3_moves__revision_1__returns_move_1_and_new_move_with_revision_2(
        self, make_sut, move_1, move_2, move_3
    ) -> None:
        sut = make_sut(moves=(move_1, move_2, move_3), revision=1)
        rack = Tileset.create([7, 8, 9])
        board = Board.create([[1, 2, 3], [4, 5, 6], [10, 11, 12]])

        assert sut.revision == 1
        assert len(sut.moves) == 3

        result = sut.with_new_move(rack, board)

        assert result.revision == 2
        assert len(result.moves) == 2
        assert result.moves[1].revision == 2
        assert result.moves[1].rack == rack
        assert result.moves[1].board == board
        assert result.moves[0] == move_1
        assert move_2 not in result.moves
        assert move_3 not in result.moves


class TestPreviousMove:
    def test_when_revision_1__returns_none(self, make_sut, move_1) -> None:
        sut = make_sut(moves=(move_1,), revision=1)

        result = sut.previous_move()

        assert not result

    def test_when_revision_0__raises_no_move_to_undo_error(self, make_sut) -> None:
        sut = make_sut(moves=(), revision=0)

        with pytest.raises(NoMoveToUndoError):
            sut.previous_move()

    def test_when_has_2_moves__revision_2__returns_move_1(
        self, make_sut, move_1, move_2
    ) -> None:
        sut = make_sut(moves=(move_1, move_2), revision=2)
        expected = move_1

        result = sut.previous_move()

        assert result == expected

    def test_when_has_3_moves__revision_2__returns_move_1(
        self, make_sut, move_1, move_2, move_3
    ) -> None:
        sut = make_sut(moves=(move_1, move_2, move_3), revision=2)
        expected = move_1

        result = sut.previous_move()

        assert result == expected

    def test_when_has_3_moves__revision_3__returns_move_2(
        self, make_sut, move_1, move_2, move_3
    ) -> None:
        sut = make_sut(moves=(move_1, move_2, move_3), revision=3)
        expected = move_2

        result = sut.previous_move()

        assert result == expected


class TestNextMove:
    def test_when_has_no_moves__raises_no_move_to_redo_error(self, make_sut) -> None:
        sut = make_sut(moves=(), revision=0)

        with pytest.raises(NoMoveToRedoError):
            sut.next_move()

    def test_when_has_1_move__revision_0__returns_move_1(self, make_sut, move_1) -> None:
        sut = make_sut(moves=(move_1,), revision=0)
        expected = move_1

        result = sut.next_move()

        assert result == expected

    def test_when_has_1_move__revision_1__raises_no_move_to_redo_error(
        self, make_sut, move_1
    ) -> None:
        sut = make_sut(moves=(move_1,), revision=1)

        with pytest.raises(NoMoveToRedoError):
            sut.next_move()

    def test_when_has_3_moves__revision_2__returns_move_3(
        self, make_sut, move_1, move_2, move_3
    ) -> None:
        sut = make_sut(moves=(move_1, move_2, move_3), revision=2)
        expected = move_3

        result = sut.next_move()

        assert result == expected

    def test_when_has_3_moves__revision_1__returns_move_2(
        self, make_sut, move_1, move_2, move_3
    ) -> None:
        sut = make_sut(moves=(move_1, move_2, move_3), revision=1)
        expected = move_2

        result = sut.next_move()

        assert result == expected


class TestWithRevision:
    def test_returns_turn_with_updated_revision(self, make_sut) -> None:
        sut = make_sut(moves=(), revision=0)
        expected = 1

        result = sut.with_revision(1)

        assert result.revision == expected


class TestEnsureHasNoMoves:
    def test_when_revision_greater_than_0__raises_moves_performed_error(
        self, make_sut, move_1
    ) -> None:
        sut = make_sut(moves=(move_1,), revision=1)

        with pytest.raises(MovesPerformedError):
            sut.ensure_has_no_moves()

    def test_when_revision_0__does_not_raise_moves_performed_error(
        self, make_sut
    ) -> None:
        sut = make_sut(moves=(), revision=0)

        with not_raises(MovesPerformedError):
            sut.ensure_has_no_moves()


class TestEnsureHasMoves:
    def test_when_revision_0__raises_no_moves_performed_error(self, make_sut) -> None:
        sut = make_sut(moves=(), revision=0)

        with pytest.raises(NoMovesPerformedError):
            sut.ensure_has_moves()

    def test_when_revision_greater_than_0__does_not_raise_no_moves_performed_error(
        self, make_sut, move_1
    ) -> None:
        sut = make_sut(moves=(move_1,), revision=1)

        with not_raises(NoMovesPerformedError):
            sut.ensure_has_moves()
