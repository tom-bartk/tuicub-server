from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    ARRAY,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Uuid,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .status import GameroomStatus


class DbBase(DeclarativeBase):
    """The base model for all database models."""

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    """The primary key."""


class DbUserToken(DbBase):
    """The database model for an authentication token."""

    __tablename__ = "user_token"

    token: Mapped[str] = mapped_column(String(64))
    """The value of the token used for authentication."""

    # Foreign keys
    user_id: Mapped[UUID] = mapped_column(Uuid)
    """The id of the user that the authentication token belongs to."""

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DbUserToken):
            return NotImplemented

        return (
            self.id == other.id
            and self.token == other.token
            and self.user_id == other.user_id
        )


class DbUser(DbBase):
    """The database model for a user."""

    __tablename__ = "user"

    name: Mapped[str] = mapped_column(String(64))
    """The name of the user."""

    # Foreign keys
    current_gameroom_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("gameroom.id"), nullable=True
    )
    """The optional id of the gameroom that the user is currently in."""

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DbUser):
            return NotImplemented
        return (
            self.id == other.id
            and self.name == other.name
            and self.current_gameroom_id == other.current_gameroom_id
        )


class DbGameroom(DbBase):
    """The database model for a gameroom."""

    __tablename__ = "gameroom"

    name: Mapped[str] = mapped_column(String)
    """The name of the gameroom."""

    owner_id: Mapped[UUID] = mapped_column(Uuid)
    """The id of the user that owns this gameroom."""

    status: Mapped[GameroomStatus] = mapped_column(Enum(GameroomStatus))
    """The status of the gameroom."""

    created_at: Mapped[datetime] = mapped_column(DateTime)
    """The gameroom's date of creation."""

    # Relationships
    users: Mapped[list[DbUser]] = relationship()
    """Users that joined this gameroom, including the owner."""

    game: Mapped[DbGame | None] = relationship(
        back_populates="gameroom", cascade="all, delete-orphan"
    )
    """An optional game started in this gameroom."""

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DbGameroom):
            return NotImplemented
        return (
            self.id == other.id
            and self.name == other.name
            and self.owner_id == other.owner_id
            and self.status == other.status
            and self.created_at == other.created_at
            and self.users == other.users
            and self.game == other.game
        )


class DbPlayer(DbBase):
    """The database model for a player."""

    __tablename__ = "player"

    name: Mapped[str] = mapped_column(String(64))
    """The name of the player."""

    rack: Mapped[list[int]] = mapped_column(ARRAY(Integer))
    """The current rack of the player."""

    user_id: Mapped[UUID] = mapped_column(Uuid)
    """The id of the user that the player represents."""

    # Foreign keys
    game_state_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("game_state.id"))
    """The id of the game state that this players belongs to."""

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DbPlayer):
            return NotImplemented
        return (
            self.id == other.id
            and self.name == other.name
            and self.rack == other.rack
            and self.user_id == other.user_id
            and self.game_state_id == other.game_state_id
        )


class DbMove(DbBase):
    """The database model for a tiles move."""

    __tablename__ = "move"

    revision: Mapped[int]
    """The revision of the move inside a turn used for undo/redo."""

    board: Mapped[list[str]] = mapped_column(ARRAY(String))
    """The board after the move."""

    rack: Mapped[list[int]] = mapped_column(ARRAY(Integer))
    """The rack of the player after the move."""

    # Foreign keys
    turn_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("turn.id"))
    """The id of the turn that this move belongs to."""

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DbMove):
            return NotImplemented
        return (
            self.id == other.id
            and self.revision == other.revision
            and self.board == other.board
            and self.rack == other.rack
            and self.turn_id == other.turn_id
        )


class DbTurn(DbBase):
    """The database model for a turn."""

    __tablename__ = "turn"

    revision: Mapped[int]
    """The current revision used for undo/redo."""

    starting_board: Mapped[list[str]] = mapped_column(ARRAY(String))
    """The board at the start of this turn."""

    starting_rack: Mapped[list[int]] = mapped_column(ARRAY(Integer))
    """The rack of the player at the start of this turn."""

    player_id: Mapped[UUID] = mapped_column(Uuid)
    """The id of the player that has this turn."""

    # Foreign keys
    game_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("game.id"))
    """The id of the game that this turn belongs to."""

    # Relationships
    moves: Mapped[list[DbMove]] = relationship(cascade="all, delete-orphan")
    """Moves made this turn."""

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DbTurn):
            return NotImplemented
        return (
            self.id == other.id
            and self.revision == other.revision
            and self.starting_board == other.starting_board
            and self.starting_rack == other.starting_rack
            and self.player_id == other.player_id
            and self.game_id == other.game_id
            and self.moves == other.moves
        )


class DbGameState(DbBase):
    """The database model for a game state."""

    __tablename__ = "game_state"

    board: Mapped[list[str]] = mapped_column(ARRAY(String))
    """The board of the game."""

    pile: Mapped[list[int]] = mapped_column(ARRAY(Integer))
    """The pile of tiles that players draw from."""

    # Foreign keys
    game_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("game.id"))
    """The id of the game that this game state belongs to."""

    # Relationships
    players: Mapped[list[DbPlayer]] = relationship(cascade="all, delete-orphan")
    """The players participating in this game."""

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DbGameState):
            return NotImplemented
        return (
            self.id == other.id
            and self.pile == other.pile
            and self.board == other.board
            and self.game_id == other.game_id
            and self.players == other.players
        )


class DbGame(DbBase):
    """The database model for a game."""

    __tablename__ = "game"

    turn_order: Mapped[tuple[str, ...]] = mapped_column(ARRAY(String, as_tuple=True))
    """The list of user ids representing the order of turns."""

    made_meld: Mapped[tuple[str, ...]] = mapped_column(ARRAY(String, as_tuple=True))
    """The registry of users that have made a valid meld."""

    # Foreign keys
    gameroom_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("gameroom.id"))
    """The id of the gameroom that this game belongs to."""

    winner_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("player.id", name="fk_winner"), nullable=True
    )
    """The optional id of the player that won the game."""

    # Relationships
    game_state: Mapped[DbGameState] = relationship(cascade="all, delete-orphan")
    """The game state of this game."""

    gameroom: Mapped[DbGameroom] = relationship(back_populates="game")
    """The gameroom that this game belongs to."""

    turn: Mapped[DbTurn] = relationship(cascade="all, delete-orphan")
    """The current turn."""

    winner: Mapped[DbPlayer | None] = relationship(
        primaryjoin=winner_id == DbPlayer.id, post_update=True
    )
    """The optional player that won the game."""

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DbGame):
            return NotImplemented
        return (
            self.id == other.id
            and self.turn_order == other.turn_order
            and self.made_meld == other.made_meld
            and self.gameroom_id == other.gameroom_id
            and self.winner_id == other.winner_id
            and self.game_state == other.game_state
            and self.turn == other.turn
            and self.winner == other.winner
        )
