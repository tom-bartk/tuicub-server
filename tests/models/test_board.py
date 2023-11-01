from src.tuicubserver.models.game import Board


class TestSerialize:
    def test_returns_list_of_string_list_of_tile_ids(self) -> None:
        sut = Board.create([[1, 2, 3], [4, 5, 6]])
        expected = ["[1, 2, 3]", "[4, 5, 6]"]

        result = sut.serialize()

        assert result == expected


class TestAsList:
    def test_returns_list_of_list_of_tile_ids(self) -> None:
        sut = Board.create([[1, 2, 3], [4, 5, 6]])
        expected = [[1, 2, 3], [4, 5, 6]]

        result = sut.as_list()

        assert result == expected


class TestAllTiles:
    def test_returns_flattened_list_of_list_of_tile_ids(self) -> None:
        sut = Board.create([[1, 2, 3], [4, 5, 6]])
        expected = [1, 2, 3, 4, 5, 6]

        result = sut.all_tiles()

        assert result == expected


class TestDeserialize:
    def test_returns_board_created_from_list_of_string_list_of_tiles(self) -> None:
        expected = Board.create([[1, 2, 3], [4, 5, 6]])

        result = Board.deserialize(["[3, 1, 2]", "[5, 6, 4]"])

        assert result == expected
