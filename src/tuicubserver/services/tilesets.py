from collections.abc import Callable

from theine import Cache

from ..models.game import Tileset


class TilesetsService:
    """The service for validating tilesets."""

    def __init__(
        self,
        valid_tilesets: Callable[[], frozenset[tuple[int, ...]]],
        validity_cache: Cache,
        values_cache: Cache,
    ):
        """Initialize new service.

        Args:
            valid_tilesets (Callable[[], frozenset[tuple[int, ...]]]): The getter function
                returning a set of all possible valid tile sets without jokers.
            validity_cache (Cache): The cache for valid tile sets.
            values_cache (Cache): The cache for tile sets values.
        """
        self._validity_cache: Cache = validity_cache
        self._values_cache: Cache = values_cache
        self._valid_tilesets: frozenset[tuple[int, ...]] = frozenset()
        self._valid_tilesets_getter: Callable[
            [], frozenset[tuple[int, ...]]
        ] = valid_tilesets

    def is_valid(self, tileset: Tileset) -> bool:
        """Check if a tile set is valid.

        A valid tile set is either a run or a group. A valid group consists of three or
        four tiles with the same number, but different color. A valid run is composed of
        three or more, same-colored tiles, in consecutive number order.

        Args:
            tileset (Tileset): The tile set to validate.

        Returns:
            True if the tile set is valid, false otherwise.
        """
        cached: bool | None = self._validity_cache.get(hash(tileset))
        if cached is not None:
            return cached

        result = self._is_valid(tileset)
        self._validity_cache.set(hash(tileset), result)

        return result

    def value_of(self, tileset: Tileset) -> int:
        """Get the sum of tiles numbers for a tile set.

        Args:
            tileset (Tileset): The tile set to get the value of.

        Returns:
            The sum of all tiles numbers in the tile set.
        """
        cached: int | None = self._values_cache.get(hash(tileset))
        if cached is not None:
            return cached

        if not self.is_valid(tileset):
            return 0

        result = self._value_of(tileset)
        self._values_cache.set(hash(tileset), result)

        return result

    def _value_of(self, tileset: Tileset) -> int:
        if tileset.contains_jokers():
            tiles_without_jokers = tileset.filter_jokers()
            jokers_count = tileset.jokers_count()
            tiles_without_jokers_count = len(tiles_without_jokers)

            matching = frozenset(
                _tileset
                for _tileset in self._get_valid_tilesets()
                if (len(_tileset) - jokers_count) == tiles_without_jokers_count
                and all(tile in _tileset for tile in tiles_without_jokers)
            )
            return tileset_value(max(matching, key=tileset_value))

        return tileset_value(tileset.tiles)

    def _is_valid(self, tileset: Tileset) -> bool:
        if tileset.contains_jokers():
            tiles_without_jokers = tileset.filter_jokers()
            num_jokers = tileset.jokers_count()
            num_tiles_without_jokers = len(tiles_without_jokers)

            for _tileset in self._get_valid_tilesets():
                if (len(_tileset) - num_jokers) == num_tiles_without_jokers and all(
                    tile in _tileset for tile in tiles_without_jokers
                ):
                    return True
            return False

        return tuple(sorted(tileset.tiles)) in self._get_valid_tilesets()

    def _get_valid_tilesets(self) -> frozenset[tuple[int, ...]]:
        if not self._valid_tilesets:
            self._valid_tilesets = self._valid_tilesets_getter()
        return self._valid_tilesets


def tileset_value(tileset: tuple[int, ...]) -> int:
    return sum(tile % 13 + 1 for tile in tileset)
