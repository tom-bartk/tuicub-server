from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from ..models.game import Game
    from ..models.gameroom import Gameroom
    from ..models.user import User


class Recipents(Sequence[UUID]):
    """Recipents of a message."""

    __slots__ = ("_recipents",)

    def __init__(self, recipents: Sequence[UUID]):
        """Initialize new recipents.

        Args:
            recipents (Sequence[UUID]): The sequence of recipents ids.
        """
        self._recipents: Sequence[UUID] = recipents

    def __getitem__(self, key, /):  # noqa: ANN001
        return self._recipents[key]

    def __len__(self) -> int:
        return len(self._recipents)


class AllUsersButSender(Recipents):
    """Recipents are all users in a gameroom, except for the sender."""

    __slots__ = ()

    def __init__(self, sender: User, gameroom: Gameroom):
        """Initialize new recipents.

        Args:
            sender (User): The sender of the message.
            gameroom (Gameroom): The gameroom of the sende.r
        """
        super().__init__(
            recipents=[user.id for user in gameroom.users if user.id != sender.id]
        )


class SingleRecipent(Recipents):
    """A single recipent."""

    __slots__ = ()

    def __init__(self, user_id: UUID):
        """Initialize new recipents.

        Args:
            user_id (UUID): The id of the sender.
        """
        super().__init__(recipents=[user_id])


class AllPlayers(Recipents):
    """Recipents are all players in a game."""

    __slots__ = ()

    def __init__(self, game: Game):
        """Initialize new recipents.

        Args:
            game (Game): The game to send the message to.
        """
        super().__init__(recipents=[player.user_id for player in game.game_state.players])
