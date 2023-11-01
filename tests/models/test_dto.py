from unittest.mock import create_autospec

from attrs import evolve

from src.tuicubserver.models.dto import GameDto, PlayerDto, create_players
from src.tuicubserver.models.game import Game, GameState, Player, Tileset, Turn


class TestGameDto:
    def test_create__when_game_has_winner__creates_winner_dto(
        self, game, player_1, user_1
    ) -> None:
        game = evolve(game, winner=player_1)
        expected = PlayerDto(
            user_id=game.winner.user_id,
            name=game.winner.name,
            tiles_count=len(game.winner.rack),
            has_turn=game.turn.player_id == game.winner.id,
        )

        result = GameDto.create(game, user_1)

        assert result.winner == expected

    def test_for_player__when_game_has_winner__creates_winner_dto(
        self, game, player_1, user_1
    ) -> None:
        game = evolve(game, winner=player_1)
        expected = PlayerDto(
            user_id=game.winner.user_id,
            name=game.winner.name,
            tiles_count=len(game.winner.rack),
            has_turn=game.turn.player_id == game.winner.id,
        )

        result = GameDto.for_player(game, player_1)

        assert result.winner == expected


class TestCreatePlayers:
    def test_returns_players_ordered_by_turn_order(
        self, user_id_1, user_id_2, user_id_3, player_id_1, player_id_2, player_id_3
    ):
        player_1 = Player(id=player_id_1, user_id=user_id_1, name="foo", rack=Tileset())
        player_2 = Player(id=player_id_1, user_id=user_id_1, name="foo", rack=Tileset())
        player_3 = Player(id=player_id_2, user_id=user_id_2, name="bar", rack=Tileset())
        player_4 = Player(id=player_id_3, user_id=user_id_3, name="baz", rack=Tileset())

        game = create_autospec(Game)
        game.turn_order = (user_id_1, user_id_2, user_id_3)
        game.game_state = create_autospec(GameState)
        game.game_state.players = (player_1, player_2, player_4, player_3)
        game.turn = create_autospec(Turn)
        game.turn.player_id = player_id_2

        expected = [
            PlayerDto(user_id=user_id_1, name="foo", tiles_count=0, has_turn=False),
            PlayerDto(user_id=user_id_1, name="foo", tiles_count=0, has_turn=False),
            PlayerDto(user_id=user_id_2, name="bar", tiles_count=0, has_turn=True),
            PlayerDto(user_id=user_id_3, name="baz", tiles_count=0, has_turn=False),
        ]

        result = create_players(game)

        assert result == expected
