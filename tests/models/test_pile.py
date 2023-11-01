from src.tuicubserver.models.game import Pile, Tileset


class TestDraw:
    def test_returns_random_tile(self, rng_service) -> None:
        sut = Pile([1, 2, 3])
        expected = 1  # rng_service.pick returns first element

        result = sut.draw(rng_service.pick)

        assert result == expected

    def test_removes_drawn_tile_from_pile(self, rng_service) -> None:
        sut = Pile([1, 2, 3])
        expected = (2, 3)

        sut.draw(rng_service.pick)

        assert sut.tiles == expected


class TestDrawRack:
    def test_returns_random_rack(self, rng_service) -> None:
        sut = Pile([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])
        expected = Tileset.create([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14])

        result = sut.draw_rack(rng_service.pick)

        assert result == expected

    def test_removes_drawn_tiles_from_pile(self, rng_service) -> None:
        sut = Pile([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])
        expected = (15,)

        sut.draw_rack(rng_service.pick)

        assert sut.tiles == expected


class TestReturnRack:
    def test_puts_tiles_from_rack_back_to_pile(self, rng_service) -> None:
        sut = Pile([1, 2, 3])
        expected = (1, 2, 3, 4, 5, 6)

        sut.return_rack(Tileset.create([4, 5, 6]), shuffle=rng_service.shuffle)

        assert sut.tiles == expected


class TestHash:
    def test_returns_hash_of_tiles(self) -> None:
        sut = Pile([1, 2, 3])
        expected = hash((1, 2, 3))

        result = hash(sut)

        assert result == expected
