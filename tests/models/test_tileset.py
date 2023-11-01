from src.tuicubserver.models.game import Tileset


class TestSerialize:
    def test_returns_string_list_of_tile_ids(self) -> None:
        sut = Tileset.create([1, 2, 3])
        expected = "[1, 2, 3]"

        result = sut.serialize()

        assert result == expected


class TestAsList:
    def test_returns_list_of_tile_ids(self) -> None:
        sut = Tileset.create([1, 2, 3])
        expected = [1, 2, 3]

        result = sut.as_list()

        assert result == expected


class TestCreate:
    def test_returns_tileset_with_sorted_tuple_of_tiles(self) -> None:
        expected = (1, 2, 3)

        result = Tileset.create([3, 1, 2])

        assert result.tiles == expected


class TestDeserialize:
    def test_returns_tileset_created_from_string_list_of_tiles(self) -> None:
        expected = Tileset.create([1, 2, 3])

        result = Tileset.deserialize("[3, 1, 2]")

        assert result == expected


class TestContainsJokers:
    def test_when_contains_tile_104__returns_true(self) -> None:
        sut = Tileset.create([1, 2, 104])
        expected = True

        result = sut.contains_jokers()

        assert result == expected

    def test_when_contains_tile_105__returns_true(self) -> None:
        sut = Tileset.create([1, 2, 105])
        expected = True

        result = sut.contains_jokers()

        assert result == expected

    def test_when_contains_no_tile_104_or_105__returns_false(self) -> None:
        sut = Tileset.create([1, 2, 3])
        expected = False

        result = sut.contains_jokers()

        assert result == expected


class TestFilterJokers:
    def test_returns_tuple_of_tiles_without_tiles_104_or_105(self) -> None:
        sut = Tileset.create([1, 2, 104, 105, 3])
        expected = (1, 2, 3)

        result = sut.filter_jokers()

        assert result == expected


class TestJokersCount:
    def test_when_contains_tiles_104_and_105__returns_2(self) -> None:
        sut = Tileset.create([1, 2, 104, 105, 3])
        expected = 2

        result = sut.jokers_count()

        assert result == expected

    def test_when_contains_tile_104_and_not_105__returns_1(self) -> None:
        sut = Tileset.create([1, 2, 104])
        expected = 1

        result = sut.jokers_count()

        assert result == expected

    def test_when_contains_tile_105_and_not_104__returns_1(self) -> None:
        sut = Tileset.create([1, 2, 105])
        expected = 1

        result = sut.jokers_count()

        assert result == expected


class TestLen:
    def test_returns_length_of_tiles_list(self) -> None:
        sut = Tileset.create([1, 2, 3])
        expected = 3

        result = len(sut)

        assert result == expected
