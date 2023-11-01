from src.tuicubserver.models.game import Player, Tileset


class TestWithRack:
    def test_returns_player_with_new_rack(self, player_id_1, user_id_1) -> None:
        sut = Player(
            id=player_id_1, user_id=user_id_1, name="foo", rack=Tileset.create([1, 2, 3])
        )
        expected = Player(
            id=player_id_1,
            user_id=user_id_1,
            name="foo",
            rack=Tileset.create([1, 2, 3, 4, 5, 6]),
        )

        result = sut.with_rack(Tileset.create([1, 2, 3, 4, 5, 6]))

        assert result == expected
