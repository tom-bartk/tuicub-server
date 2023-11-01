from collections.abc import Callable
from unittest.mock import Mock, create_autospec

import pytest
from theine import Cache

from src.tuicubserver.models.game import Tileset
from src.tuicubserver.services.tilesets import TilesetsService


@pytest.fixture()
def validity_cache() -> Cache:
    cache = create_autospec(Cache)
    cache.get = Mock(return_value=None)
    return cache


@pytest.fixture()
def values_cache() -> Cache:
    cache = create_autospec(Cache)
    cache.get = Mock(return_value=None)
    return cache


@pytest.fixture()
def valid_tilesets() -> Callable[[], frozenset[tuple[int, ...]]]:
    return lambda: frozenset(
        ((1, 2, 3), (1, 2, 12), (1, 11, 12), (4, 5, 6), (1, 2, 3, 4, 5, 6))
    )


@pytest.fixture()
def sut(validity_cache, values_cache, valid_tilesets) -> TilesetsService:
    return TilesetsService(
        valid_tilesets=valid_tilesets,
        validity_cache=validity_cache,
        values_cache=values_cache,
    )


class TestIsValid:
    def test_when_is_cached__returns_cached_value(self, sut, validity_cache) -> None:
        expected = True
        validity_cache.get = Mock(return_value=expected)

        result = sut.is_valid(Tileset((1, 2, 3)))

        assert result == expected

    def test_when_not_cached__stores_computed_value(self, sut, validity_cache) -> None:
        sut.is_valid(Tileset((1, 2, 3)))

        validity_cache.set.assert_called_once()

    def test_when_not_cached__valid_tileset__returns_true(self, sut) -> None:
        expected = True

        result = sut.is_valid(Tileset((1, 2, 3)))

        assert result == expected

    def test_when_not_cached__invalid_tileset__returns_false(self, sut) -> None:
        expected = False

        result = sut.is_valid(Tileset((7, 8, 9)))

        assert result == expected

    def test_when_not_cached__valid_tileset_w_one_joker__returns_true(self, sut) -> None:
        expected = True

        result = sut.is_valid(Tileset((1, 2, 104)))

        assert result == expected

    def test_when_not_cached__valid_tileset_w_two_jokers__returns_true(self, sut) -> None:
        expected = True

        result = sut.is_valid(Tileset((1, 104, 105)))

        assert result == expected

    def test_when_not_cached__invalid_tileset_w_one_joker__returns_false(
        self, sut
    ) -> None:
        expected = False

        result = sut.is_valid(Tileset((1, 7, 104)))

        assert result == expected

    def test_when_not_cached__invalid_tileset_w_two_jokers__returns_false(
        self, sut
    ) -> None:
        expected = False

        result = sut.is_valid(Tileset((7, 104, 105)))

        assert result == expected


class TestValueOf:
    def test_when_is_cached__returns_cached_value(self, sut, values_cache) -> None:
        expected = 42
        values_cache.get = Mock(return_value=expected)

        result = sut.value_of(Tileset((1, 2, 3)))

        assert result == expected

    def test_when_not_cached__stores_computed_value(self, sut, values_cache) -> None:
        sut.value_of(Tileset((1, 2, 3)))

        values_cache.set.assert_called_once()

    def test_when_not_cached__invalid_tileset__returns_zero(
        self, sut, values_cache
    ) -> None:
        expected = 0

        result = sut.value_of(Tileset((7, 8, 9)))

        assert result == expected

    def test_when_not_cached__valid_tileset__returns_correct_value(
        self, sut, values_cache
    ) -> None:
        expected = 9  # (1+1) + (2+1) + (3+1)

        result = sut.value_of(Tileset((1, 2, 3)))

        assert result == expected

    def test_when_not_cached__valid_tileset_w_one_joker__returns_largest_possible(
        self, sut, values_cache
    ) -> None:
        expected = 18  # (1, 2, 3) = 9 (1, 2, 12) = 18

        result = sut.value_of(Tileset((1, 2, 104)))

        assert result == expected

    def test_when_not_cached__valid_tileset_w_two_jokers__returns_largest_possible(
        self, sut, values_cache
    ) -> None:
        expected = 27  # (1, 2, 3) = 9, (1, 2, 12) = 18, (1, 11, 12) = 27

        result = sut.value_of(Tileset((1, 104, 105)))

        assert result == expected
