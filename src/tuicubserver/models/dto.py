from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from functools import cmp_to_key
from uuid import UUID

from attrs import frozen
from marshmallow import Schema, fields

from .game import Game, Player
from .gameroom import Gameroom
from .status import GameroomStatus
from .user import User


class BaseDto(ABC):
    """Base class for all dtos."""

    @abstractmethod
    def serialize(self) -> dict:
        """Returns the dictionary representation of the dto."""


@frozen
class UserDto(BaseDto):
    """The dto for a user."""

    id: UUID
    name: str

    @classmethod
    def create(cls, user: User) -> UserDto:
        """Returns a dto of the user."""
        return UserDto(id=user.id, name=user.name)

    def serialize(self) -> dict:
        return UserSchema().dump(self)


@frozen
class PlayerDto(BaseDto):
    """The dto for a player."""

    user_id: UUID
    name: str
    tiles_count: int
    has_turn: bool

    def serialize(self) -> dict:
        return PlayerSchema().dump(self)


@frozen
class GameStateDto(BaseDto):
    """The dto for a game state."""

    id: UUID
    players: list[PlayerDto]
    board: list[list[int]]
    pile_count: int
    rack: list[int]

    @classmethod
    def create(cls, game: Game, user: User) -> GameStateDto:
        """Returns a game state dto for the user."""
        game_state = game.game_state
        player: Player | None = next(
            (player for player in game_state.players if player.user_id == user.id), None
        )

        return GameStateDto(
            id=game_state.id,
            players=create_players(game),
            board=game_state.board.as_list(),
            pile_count=len(game_state.pile),
            rack=[] if not player else player.rack.as_list(),
        )

    @classmethod
    def for_player(cls, game: Game, player: Player) -> GameStateDto:
        """Returns a game state dto for the player."""
        game_state = game.game_state
        return GameStateDto(
            id=game_state.id,
            players=create_players(game),
            board=game_state.board.as_list(),
            pile_count=len(game_state.pile),
            rack=player.rack.as_list(),
        )

    def serialize(self) -> dict:
        return GameStateSchema().dump(self)


@frozen
class GameDto(BaseDto):
    """The dto for a game."""

    id: UUID
    game_state: GameStateDto
    gameroom_id: UUID
    winner: PlayerDto | None

    @classmethod
    def create(cls, game: Game, user: User) -> GameDto:
        """Returns a game dto for the user."""
        winner: PlayerDto | None = None
        if game.winner:
            winner = PlayerDto(
                user_id=game.winner.user_id,
                name=game.winner.name,
                tiles_count=len(game.winner.rack),
                has_turn=game.turn.player_id == game.winner.id,
            )

        return GameDto(
            id=game.id,
            game_state=GameStateDto.create(game, user),
            gameroom_id=game.gameroom_id,
            winner=winner,
        )

    @classmethod
    def for_player(cls, game: Game, player: Player) -> GameDto:
        """Returns a game dto for the player."""
        winner: PlayerDto | None = None
        if game.winner:
            winner = PlayerDto(
                user_id=game.winner.user_id,
                name=game.winner.name,
                tiles_count=len(game.winner.rack),
                has_turn=game.turn.player_id == game.winner.id,
            )

        return GameDto(
            id=game.id,
            game_state=GameStateDto.for_player(game, player),
            gameroom_id=game.gameroom_id,
            winner=winner,
        )

    def serialize(self) -> dict:
        return GameSchema().dump(self)


@frozen
class GameroomDto(BaseDto):
    """The dto for a gameroom."""

    id: UUID
    name: str
    owner_id: UUID
    created_at: datetime
    status: GameroomStatus
    users: list[UserDto]
    game_id: UUID | None

    @classmethod
    def create(cls, gameroom: Gameroom) -> GameroomDto:
        """Returns a gameroom dto."""
        return GameroomDto(
            id=gameroom.id,
            name=gameroom.name,
            owner_id=gameroom.owner_id,
            created_at=gameroom.created_at,
            status=gameroom.status,
            users=[UserDto.create(user) for user in gameroom.users],
            game_id=None if not gameroom.game else gameroom.game.id,
        )

    def serialize(self) -> dict:
        return GameroomSchema().dump(self)


def create_players(game: Game) -> list[PlayerDto]:
    """Create a list of player dtos from a game.

    The players are sorted by the turn order.

    Args:
        game (Game): The game to create players from.

    Returns:
        The sorted list of player dtos.
    """
    turn_order: tuple[UUID, ...] = game.turn_order
    players: list[PlayerDto] = [
        PlayerDto(
            user_id=player.user_id,
            name=player.name,
            tiles_count=len(player.rack),
            has_turn=game.turn.player_id == player.id,
        )
        for player in game.game_state.players
    ]

    def order(lhs: PlayerDto, rhs: PlayerDto) -> int:
        lhs_index = turn_order.index(lhs.user_id)
        rhs_index = turn_order.index(rhs.user_id)
        if lhs_index == rhs_index:
            return 0
        elif lhs_index < rhs_index:
            return -1
        else:
            return 1

    return sorted(players, key=cmp_to_key(order))


class UserSchema(Schema):
    """The schema for a user."""

    id = fields.UUID()
    name = fields.Str()


class GameroomSchema(Schema):
    """The schema for a gameroom."""

    id = fields.UUID()
    name = fields.Str()
    owner_id = fields.UUID()
    status = fields.Enum(GameroomStatus, by_value=True)
    created_at = fields.DateTime(format="timestamp_ms")
    users = fields.List(fields.Nested(UserSchema))
    game_id = fields.UUID(allow_none=True, required=False)


class PlayerSchema(Schema):
    """The schema for a player."""

    name = fields.Str()
    user_id = fields.UUID(required=False, allow_none=True)
    tiles_count = fields.Int()
    has_turn = fields.Bool()


class GameStateSchema(Schema):
    """The schema for a game state."""

    players = fields.List(fields.Nested(PlayerSchema))
    board = fields.List(fields.List(fields.Int))
    pile_count = fields.Int()
    rack = fields.List(fields.Int)


class GameSchema(Schema):
    """The schema for a game."""

    id = fields.UUID()
    gameroom_id = fields.UUID(required=False, allow_none=True)
    game_state = fields.Nested(GameStateSchema)
    winner = fields.Nested(PlayerSchema, allow_none=True)
