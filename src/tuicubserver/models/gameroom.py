from __future__ import annotations

import datetime
import uuid

from attrs import evolve, field, frozen

from ..common import utils
from ..common.errors import BadRequestError, ForbiddenError
from .game import Game
from .status import GameroomStatus
from .user import User


@frozen
class Gameroom:
    """The model representing a gameroom.

    Attributes:
        id (uuid.UUID): The id of the gameroom.
        name (str): The name of the gameroom.
        owner_id (uuid.UUID): The id the gameroom that the game belongs to.
        users (tuple[User, ...]): Users that joined this gameroom, including the owner.
        created_at (datetime.datetime): The gameroom's date of creation.
        game (Game | None): An optional game started in this gameroom.
        status (GameroomStatus): The status of the gameroom.
    """

    id: uuid.UUID
    name: str
    owner_id: uuid.UUID
    users: tuple[User, ...]
    created_at: datetime.datetime = field(factory=utils.timestamp)
    game: Game | None = field(default=None)
    status: GameroomStatus = field(default=GameroomStatus.STARTING)

    @classmethod
    def create(cls, user: User, id: uuid.UUID | None = None) -> Gameroom:
        """Create a new gameroom with the user as owner.

        Creates a new gameroom named after the owner. The created gameroom has a starting
        status and one user, the owner.

        Args:
            user (User): The user creating the gameroom.
            id (uuid.UUID | None): An optional id of the gameroom. Defaults to None.

        Returns:
            The created gameroom.

        Raises:
            AlreadyInGameroomError: Raised when the user is already in a gameroom.
        """
        user.ensure_not_in_gameroom()
        return Gameroom(
            id=id or uuid.uuid4(),
            name=f"{user.name}'s gameroom.",
            owner_id=user.id,
            users=(user,),
            created_at=utils.timestamp(),
        )

    def with_joining(self, user: User) -> Gameroom:
        """Return a copy of the gameroom with a new user.

        Args:
            user (User): The joining user.

        Returns:
            The gameroom with the joined user.

        Raises:
            AlreadyInGameroomError: Raised when the user is already in a gameroom.
            GameAlreadyStartedError: Raised when a game has already started.
            GameroomFullError: Raised when there are already 4 users in the gameroom.
        """
        user.ensure_not_in_gameroom()
        self.ensure_starting()

        max_gameroom_users_count = 4
        if len(self.users) == max_gameroom_users_count:
            raise GameroomFullError(users=self.users)
        return evolve(self, users=(*self.users, user))

    def with_leaving(self, user: User) -> Gameroom:
        """Return a copy of the gameroom without the user.

        Args:
            user (User): The leaving user.

        Returns:
            The gameroom without the user.

        Raises:
            UserNotInGameroomError: Raised when the user is not in this gameroom.
            LeavingOwnGameroomError: Raised when the user attempts to leave their
                own gameroom.
            GameAlreadyStartedError: Raised when a game has already started.
        """
        self._ensure_has_user(user)
        self.ensure_starting()

        if self.owner_id == user.id:
            raise LeavingOwnGameroomError()

        return evolve(self, users=tuple(u for u in self.users if u.id != user.id))

    def with_started_game(self, game: Game) -> Gameroom:
        """Returns a copy of the gameroom with a new game and running status."""
        return evolve(self, game=game, status=GameroomStatus.RUNNING)

    def without_game(self) -> Gameroom:
        """Returns a copy of the gameroom without a game."""
        return evolve(self, game=None)

    def deleted(self, by: User) -> Gameroom:
        """Return a copy of the gameroom deleted by the user.

        Removes all users from the gameroom and sets it's status to deleted.

        Args:
            by (User): The deleting user.

        Returns:
            The deleted gameroom.

        Raises:
            NotGameroomOwnerError: Raised when the user is not the owner of this gameroom.
            GameAlreadyStartedError: Raised when a game has already started.
        """
        self.ensure_is_owner(user=by)
        self.ensure_starting()

        return evolve(self, users=(), status=GameroomStatus.DELETED)

    def ensure_is_owner(self, user: User) -> None:
        """Verify if the user owns the gameroom.

        Args:
            user (User): The user to verify.

        Raises:
            NotGameroomOwnerError: Raised when the user is not the owner of this gameroom.
        """
        if not self.is_owner(user):
            raise NotGameroomOwnerError(user_id=user.id, owner_id=self.owner_id)

    def ensure_starting(self) -> None:
        """Verify that the gameroom has a starting status.

        Raises:
            GameAlreadyStartedError: Raised when a game has already started.
        """
        if self.status != GameroomStatus.STARTING:
            raise GameAlreadyStartedError(status=self.status)

    def is_owner(self, user: User) -> bool:
        """Returns true if the user is the owner of the gameroom."""
        return self.owner_id == user.id

    def _ensure_has_user(self, user: User) -> None:
        user_ids = {u.id for u in self.users}
        if user.id not in user_ids:
            raise UserNotInGameroomError(user_id=user.id, user_ids=user_ids)


class GameAlreadyStartedError(BadRequestError):
    @property
    def message(self) -> str:
        return "A game has already started in this gameroom."

    @property
    def error_name(self) -> str:
        return "game_already_started"

    def __init__(self, status: GameroomStatus):
        super().__init__(info={"gameroom_status": status.value})


class GameroomFullError(BadRequestError):
    @property
    def message(self) -> str:
        return "Gameroom is full."

    @property
    def error_name(self) -> str:
        return "gameroom_full"

    def __init__(self, users: tuple[User, ...]):
        super().__init__(info={"users": [str(user.id) for user in users]})


class UserNotInGameroomError(ForbiddenError):
    @property
    def message(self) -> str:
        return "You are not in this gameroom."

    @property
    def error_name(self) -> str:
        return "user_not_in_gameroom"

    def __init__(self, user_id: uuid.UUID, user_ids: set[uuid.UUID]):
        super().__init__(
            info={"user_id": str(user_id), "users": [str(uid) for uid in user_ids]}
        )


class NotGameroomOwnerError(ForbiddenError):
    @property
    def message(self) -> str:
        return "Only the gameroom's owner can perform this action."

    @property
    def error_name(self) -> str:
        return "not_gameroom_owner"

    def __init__(self, user_id: uuid.UUID, owner_id: uuid.UUID):
        super().__init__(info={"user_id": str(user_id), "owner_id": str(owner_id)})


class LeavingOwnGameroomError(BadRequestError):
    @property
    def message(self) -> str:
        return "Can't leave your own gameroom. Delete it instead."

    @property
    def error_name(self) -> str:
        return "leaving_own_gameroom"
