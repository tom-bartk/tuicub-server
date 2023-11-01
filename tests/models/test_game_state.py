from collections.abc import Callable

import pytest

from src.tuicubserver.models.game import (
    Board,
    GameState,
    Pile,
    Player,
    PlayerNotFoundError,
    Tileset,
)


@pytest.fixture()
def make_sut(
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


class TestPlayerForId:
    def test_when_player_with_given_id_present__returns_player(
        self, make_sut, player_1, player_2, player_id_2
    ) -> None:
        sut = make_sut(players=(player_1, player_2))
        expected = player_2

        result = sut.player_for_id(player_id_2)

        assert result == expected

    def test_when_player_with_given_id_not_present__raises_player_not_found_error(
        self, make_sut, player_1, player_2, player_id_3
    ) -> None:
        sut = make_sut(players=(player_1, player_2))

        with pytest.raises(PlayerNotFoundError):
            sut.player_for_id(player_id_3)


class TestWithUpdatedPlayer:
    def test_when_player_with_given_id_present__returns_game_state_with_updated_player(
        self, make_sut, player_1, player_2
    ) -> None:
        sut = make_sut(players=(player_1, player_2))
        updated_player = Player(
            id=player_1.id,
            user_id=player_1.user_id,
            name=player_1.name,
            rack=Tileset.create([13, 42]),
        )
        expected = (updated_player, player_2)

        result = sut.with_updated_player(updated_player)

        assert result.players == expected

    def test_when_player_with_given_id_not_present__raises_player_not_found_error(
        self, make_sut, player_1, player_2, player_3
    ) -> None:
        sut = make_sut(players=(player_1, player_2))

        with pytest.raises(PlayerNotFoundError):
            sut.with_updated_player(player_3)


class TestWithBoard:
    def test_returns_game_state_with_updated_board(self, make_sut) -> None:
        sut = make_sut()
        expected = Board.create([[13, 42], [100, 101]])

        result = sut.with_board(expected)

        assert result.board == expected
