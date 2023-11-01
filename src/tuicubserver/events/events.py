from __future__ import annotations

__pdoc__ = {}

from abc import ABC, abstractmethod
from typing import NamedTuple

from ..messages.recipents import AllPlayers, AllUsersButSender, Recipents, SingleRecipent
from ..models.dto import GameDto, GameroomDto, PlayerDto, UserDto, create_players
from ..models.game import Game, Player
from ..models.gameroom import Gameroom
from ..models.user import User

__all__ = [
    "BoardChangedEvent",
    "GameStartedEvent",
    "GameroomDeletedEvent",
    "PileCountChangedEvent",
    "PlayerLeftEvent",
    "PlayerWonEvent",
    "PlayersChangedEvent",
    "RackChangedEvent",
    "TileDrawnEvent",
    "TurnEndedEvent",
    "TurnStartedEvent",
    "UserJoinedEvent",
    "UserLeftEvent",
]


class Event(ABC):
    """Base class for all events."""

    __slots__ = "_recipents"

    @property
    @abstractmethod
    def event_name(self) -> str:
        """@private The name of the event."""

    @property
    def recipents(self) -> Recipents:
        """@private The recipents of the event."""
        return self._recipents

    def __init__(self, recipents: Recipents):
        """@private Initialize new event.

        Args:
            recipents (Recipents): The recipents of the event.
        """
        self._recipents: Recipents = recipents

    def serialize(self) -> dict:
        """@private Serializes the event as a dictionary."""
        return {}


class UserEvent(Event):
    """Base class for user events."""

    __slots__ = "_user"

    def __init__(self, user: User, gameroom: Gameroom):
        self._user: UserDto = UserDto.create(user=user)
        super().__init__(recipents=AllUsersButSender(sender=user, gameroom=gameroom))

    def serialize(self) -> dict:
        return {"user": self._user.serialize()}


class UserJoinedEvent(UserEvent):
    """Event `user_joined` sent when a user joins a gameroom.

    Sent to all users in the gameroom, except for the joining user.

    Example:
        ```json
        {
            "name": "user_joined",
            "data": {
                "user": {
                    "name": "John",
                    "id": "0f62328b-782b-45f8-aed6-89c6663498bc"
                }
            }
        }
        ```

    Attributes:
        user: The user that joined the gameroom.
    """

    __slots__ = ()

    @property
    def event_name(self) -> str:
        return "user_joined"


class UserLeftEvent(UserEvent):
    """Event `user_left` sent when a user leaves a gameroom.

    Sent to all users in the gameroom, except for the leaving user.

    Example:
        ```json
        {
            "name": "user_left",
            "data": {
                "user": {
                    "name": "John",
                    "id": "0f62328b-782b-45f8-aed6-89c6663498bc"
                }
            }
        }
        ```

    Attributes:
        user: The user that left the gameroom.
    """

    __slots__ = ()

    @property
    def event_name(self) -> str:
        return "user_left"


class GameroomDeletedEvent(Event):
    """Event `gameroom_deleted` sent when the gameroom's owner delets the gameroom.

    Sent to all users that were in the gameroom, except for the owner.

    Example:
        ```json
        {
            "name": "gameroom_deleted",
            "data": {
                "gameroom": {
                    "example": {
                        "created_at": 1698397784856.701,
                        "game_id": null,
                        "id": "e0707a00-4e18-403a-8799-13afc5b0b9e3",
                        "name": "Alice's gameroom.",
                        "owner_id": "e82c6a92-a0f2-4019-903f-999bc26c8807",
                        "status": "DELETED",
                        "users": []
                    }
                }
            }
        }
        ```

    Attributes:
        gameroom: The deleted gameroom.
    """

    __slots__ = "_gameroom"

    def __init__(self, gameroom: Gameroom, remaining_users: tuple[User, ...]):
        self._gameroom: GameroomDto = GameroomDto.create(gameroom)
        super().__init__(recipents=Recipents([u.id for u in remaining_users]))

    def serialize(self) -> dict:
        return {"gameroom": self._gameroom.serialize()}

    @property
    def event_name(self) -> str:
        return "gameroom_deleted"


class BoardChangedEvent(Event):
    """Event **`board_changed`** sent when tiles on the board change.

    The board can change when a player plays any tiles, undos or redos a move,
    or the player that currently has a turn disconnects.

    Sent to all players in the game.

    Example:
        ```json
        {
            "name": "board_changed",
            "data": {
                "board": [[4, 5, 6], [7, 8, 9, 10, 11]],
                "new_tiles": [10, 11]
            }
        }
        ```

    Attributes:
        board: The current state of the board represented as a list of
            lists of tiles.
        new_tiles: The list of new tiles that have been played this turn.
    """

    __slots__ = ("_board", "_new_tiles")

    def __init__(self, game: Game):
        self._board = game.game_state.board.as_list()
        self._new_tiles = game.new_tiles()
        super().__init__(recipents=AllPlayers(game))

    @property
    def event_name(self) -> str:
        return "board_changed"

    def serialize(self) -> dict:
        board = [_sorted_tileset(tileset) for tileset in self._board]
        return {"board": board, "new_tiles": self._new_tiles}


class GameStartedEvent(Event):
    """Event `game_started` sent when the gameroom's owner starts the game.

    Sent to all users in the gameroom, except for the owner.

    Example:
        ```json
        {
            "name": "game_started",
            "data": {
                "game": {
                    "game_state": {
                        "board": [],
                        "pile_count": 78,
                        "players": [
                            {
                                "has_turn": true,
                                "name": "Alice",
                                "tiles_count": 14,
                                "user_id": "45bef5a4-c8a2-4c6a-88ea-334f13c5ec58"
                            },
                            {
                                "has_turn": false,
                                "name": "Bob",
                                "tiles_count": 14,
                                "user_id": "b44ede8d-e9f0-401f-ab71-1c0c9efcce97"
                            }
                        ],
                        "rack": [1, 5, 6, 9, 13, 14, 36, 65, 70, 74, 81, 87, 94, 95]
                    },
                    "gameroom_id": "e4812a6f-90df-4db8-ae4e-48758e8a0685",
                    "id": "6250f76c-9343-466e-8918-62578b9e63c9",
                    "winner": null
                }
            }
        }
        ```

    Attributes:
        game: The started game.
    """

    __slots__ = "_game"

    def __init__(self, game: Game, player: Player):
        self._game: GameDto = GameDto.for_player(game, player)
        super().__init__(recipents=SingleRecipent(player.user_id))

    @property
    def event_name(self) -> str:
        return "game_started"

    def serialize(self) -> dict:
        return {"game": self._game.serialize()}


class PileCountChangedEvent(Event):
    """Event `pile_count_changed` sent when the number of tiles on the pile changes.

    Pile count changes when a player draws a tile, or a player disconnects and their
    rack is shuffled back to the pile.

    Sent to all players in the game.

    Example:
        ```json
        {
            "name": "pile_count_changed",
            "data": {
                "pile_count": 78
            }
        }
        ```

    Attributes:
        pile_count: The current number of tiles on the pile.
    """

    __slots__ = "_pile_count"

    def __init__(self, game: Game):
        self._pile_count = len(game.game_state.pile)
        super().__init__(recipents=AllPlayers(game))

    @property
    def event_name(self) -> str:
        return "pile_count_changed"

    def serialize(self) -> dict:
        return {"pile_count": self._pile_count}


class PlayerLeftEvent(Event):
    """Event `player_left` sent when a player leaves the game.

    Sent to all players in the game, except for the leaving player.

    Example:
        ```json
        {
            "name": "player_left",
            "data": {
                "player": {
                    "has_turn": false,
                    "name": "Bob",
                    "tiles_count": 0,
                    "user_id": "b44ede8d-e9f0-401f-ab71-1c0c9efcce97"
                }
            }
        }
        ```

    Attributes:
        player: The player that left the game.
    """

    __slots__ = "_player"

    def __init__(self, player: Player, game: Game):
        self._player = PlayerDto(
            user_id=player.user_id, name=player.name, tiles_count=0, has_turn=False
        )
        super().__init__(recipents=AllPlayers(game))

    @property
    def event_name(self) -> str:
        return "player_left"

    def serialize(self) -> dict:
        return {"player": self._player.serialize()}


class PlayerWonEvent(Event):
    """Event `player_won` sent when a player wins the game.

    A player wins a game if they end a turn with no tiles left in their rack,
    or all other players disconnect.

    Sent to all players in the game.

    Example:
        ```json
        {
            "name": "player_won",
            "data": {
                "winner": {
                    "has_turn": false,
                    "name": "Bob",
                    "tiles_count": 0,
                    "user_id": "b44ede8d-e9f0-401f-ab71-1c0c9efcce97"
                }
            }
        }
        ```

    Attributes:
        winner: The player that won the game.
    """

    __slots__ = "_winner"

    def __init__(self, winner: Player, game: Game):
        self._winner = PlayerDto(
            user_id=winner.user_id, name=winner.name, tiles_count=0, has_turn=False
        )
        super().__init__(recipents=AllPlayers(game))

    @property
    def event_name(self) -> str:
        return "player_won"

    def serialize(self) -> dict:
        return {"winner": self._winner.serialize()}


class PlayersChangedEvent(Event):
    """Event `players_changed` sent when anything about the players change.

    That includes the list of players itself, the number of tiles in the rack of each
    player, or the current turn state.

    Sent to all players in the game.

    Example:
        ```json
        {
            "name": "players_changed",
            "data": {
                "players": [
                    {
                        "name": "Alice",
                        "has_turn": false,
                        "tiles_count": 15,
                        "user_id": "adf8a233-50eb-4dab-9bc3-31de04f77285"
                    },
                    {
                        "name": "Bob",
                        "has_turn": true,
                        "tiles_count": 10,
                        "user_id": "69b3f428-efe2-4a19-81df-d004cac7ef5e"
                    }
                ]
            }
        }
        ```

    Attributes:
        players: The updated list of players.
    """

    __slots__ = "_players"

    def __init__(self, game: Game):
        self._players = create_players(game)
        super().__init__(recipents=AllPlayers(game))

    @property
    def event_name(self) -> str:
        return "players_changed"

    def serialize(self) -> dict:
        return {"players": [player.serialize() for player in self._players]}


class RackChangedEvent(Event):
    """Event `rack_changed` sent when tiles in the player's rack change.

    Tiles in the rack can change when the player draws or play tiles.

    Sent to the player whose rack has changed.

    Example:
        ```json
        {
            "name": "rack_changed",
            "data": {
                "rack": [2, 4, 6, 8, 10, 11, 12, 13]
            }
        }
        ```

    Attributes:
        rack: The updated rack.
    """

    __slots__ = "_rack"

    def __init__(self, game: Game, user: User):
        self._rack = game.player_for_user_id(user.id).rack.as_list()
        super().__init__(recipents=SingleRecipent(user.id))

    @property
    def event_name(self) -> str:
        return "rack_changed"

    def serialize(self) -> dict:
        return {"rack": _sorted_tileset(self._rack)}


class TileDrawnEvent(Event):
    """Event `tile_drawn` sent when a player draws a tile.

    Sent to the drawing player.

    Example:
        ```json
        {
            "name": "tile_drawn",
            "data": {
                "tile": 42
            }
        }
        ```

    Attributes:
        tile: The id of the drawn tile.
    """

    __slots__ = "_tile"

    def __init__(self, tile: int, user: User):
        self._tile = tile
        super().__init__(recipents=SingleRecipent(user.id))

    @property
    def event_name(self) -> str:
        return "tile_drawn"

    def serialize(self) -> dict:
        return {"tile": self._tile}


class TurnEndedEvent(Event):
    """Event `turn_ended` sent when a turn of a player ends.

    Turn ends when a player chooses to end it after playing at least one tile, or
    after drawing a tile.

    Sent to the player that has ended their turn.

    Example:
        ```json
        {
            "name": "turn_ended",
            "data": {}
        }
        ```
    """

    __slots__ = ("_recipents",)

    def __init__(self, user: User):
        super().__init__(recipents=SingleRecipent(user.id))

    @property
    def event_name(self) -> str:
        return "turn_ended"


class TurnStartedEvent(Event):
    """Event `turn_started` sent when a turn of a player starts.

    Turn starts when another player ends their turn or disconnects.

    Sent to the player that has started their turn.

    Example:
        ```json
        {
            "name": "turn_started",
            "data": {}
        }
        ```
    """

    __slots__ = ("_recipents",)

    def __init__(self, game: Game):
        super().__init__(recipents=SingleRecipent(game.current_player().user_id))

    @property
    def event_name(self) -> str:
        return "turn_started"


class _TileNode(NamedTuple):
    id: int
    order: int


def _sorted_tileset(tileset: list[int]) -> list[int]:
    deck_size = 52
    jokers = {104, 105}
    return [
        node.id
        for node in sorted(
            [
                _TileNode(id=tile, order=tile)
                if (tile < deck_size or tile in jokers)
                else _TileNode(id=tile, order=tile - deck_size)
                for tile in tileset
            ],
            key=lambda node: node.order,
        )
    ]


__pdoc__["Event.serialize"] = False
