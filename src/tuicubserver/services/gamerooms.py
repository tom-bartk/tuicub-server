from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from attrs import field, frozen

from ..common.context import Context
from ..models.game import Game
from ..models.gameroom import Gameroom
from ..models.user import User
from ..repositories.gamerooms import GameroomsRepository
from ..repositories.games import GamesRepository
from .game_toolkit import GameToolkit
from .games import GamesService


class GameroomsService:
    """The service for querying and manipulating gamerooms."""

    __slots__ = (
        "_game_toolkit",
        "_games_repository",
        "_games_service",
        "_gamerooms_repository",
    )

    def __init__(
        self,
        game_toolkit: GameToolkit,
        games_repository: GamesRepository,
        games_service: GamesService,
        gamerooms_repository: GameroomsRepository,
    ):
        """Initialize new service.

        Args:
            game_toolkit (GameToolkit): The game toolkit for creating new games.
            games_repository (GamesRepository): The games repository.
            games_service (GamesService): The games service.
            gamerooms_repository (GameroomsRepository): The gamerooms repository.
        """
        self._game_toolkit: GameToolkit = game_toolkit
        self._games_repository: GamesRepository = games_repository
        self._games_service: GamesService = games_service
        self._gamerooms_repository: GameroomsRepository = gamerooms_repository

    def get_gamerooms(self, context: Context) -> Sequence[Gameroom]:
        """Get all active gamerooms.

        Returns a list of gamerooms that don't have deleted status.

        Args:
            context (Context): The request context.

        Returns:
            The list of active gamerooms.
        """
        return self._gamerooms_repository.get_gamerooms(session=context.session)

    def create_gameroom(self, context: Context) -> Gameroom:
        """Create a new gameroom.

        Creates a new gameroom named after the requesting user.
        The created gameroom has a starting status and one user, the owner.

        Args:
            context (Context): The request context.

        Returns:
            The created gameroom.

        Raises:
            AlreadyInGameroomError: Raised when the user is already in a gameroom.
        """
        return self._gamerooms_repository.save_gameroom(
            session=context.session, gameroom=Gameroom.create(user=context.user)
        )

    def join_gameroom(self, context: Context, gameroom_id: str | UUID) -> Gameroom:
        """Join a gameroom.

        Joins a gameroom that has a starting status and less than 4 users.

        Args:
            context (Context): The request context.
            gameroom_id (str | UUID): The id of the gameroom to join.

        Returns:
            The joined gameroom.

        Raises:
            NotFoundError: Raised when a gameroom with the given id does not exist.
            AlreadyInGameroomError: Raised when the user is already in a gameroom.
            GameAlreadyStartedError: Raised when a game has already started.
            GameroomFullError: Raised when there are already 4 users in the gameroom.
        """
        gameroom = self._gamerooms_repository.get_gameroom_by_id(
            session=context.session, id=gameroom_id
        )

        return self._gamerooms_repository.save_gameroom(
            session=context.session, gameroom=gameroom.with_joining(user=context.user)
        )

    def leave_gameroom(self, context: Context, gameroom_id: str | UUID) -> Gameroom:
        """Leave a gameroom.

        Leaves a gameroom that the user is in and has a starting status.

        Args:
            context (Context): The request context.
            gameroom_id (str | UUID): The id of the gameroom to leave.

        Returns:
            The left gameroom.

        Raises:
            NotFoundError: Raised when a gameroom with the given id does not exist.
            UserNotInGameroomError: Raised when the user is not in this gameroom.
            LeavingOwnGameroomError: Raised when the user attempts to leave their
                own gameroom.
            GameAlreadyStartedError: Raised when a game has already started.
        """
        gameroom = self._gamerooms_repository.get_gameroom_by_id(
            session=context.session, id=gameroom_id
        )
        return self._gamerooms_repository.save_gameroom(
            session=context.session, gameroom=gameroom.with_leaving(user=context.user)
        )

    def delete_gameroom(
        self, context: Context, gameroom_id: str | UUID
    ) -> DeleteGameroomResult:
        """Delete a gameroom.

        Deletes a gameroom that the user is an owner of.

        Args:
            context (Context): The request context.
            gameroom_id (str | UUID): The id of the gameroom to delete.

        Returns:
            The result of deleting the gameroom.

        Raises:
            NotFoundError: Raised when a gameroom with the given id does not exist.
            NotGameroomOwnerError: Raised when the user is not the owner of this gameroom.
            GameAlreadyStartedError: Raised when a game has already started.
        """
        gameroom = self._gamerooms_repository.get_gameroom_by_id(
            session=context.session, id=gameroom_id
        )
        return DeleteGameroomResult(
            gameroom=self._gamerooms_repository.save_gameroom(
                session=context.session, gameroom=gameroom.deleted(by=context.user)
            ),
            remaining_users=tuple(
                user for user in gameroom.users if user.id != context.user.id
            ),
        )

    def start_game(self, context: Context, gameroom_id: str | UUID) -> Game:
        """Start a game.

        Starts the game in this gameroom with users as players. Only the
        gameroom's owner can start the game.

        Args:
            context (Context): The request context.
            gameroom_id (str | UUID): The id of the gameroom to start the game in.

        Returns:
            The started game.

        Raises:
            NotFoundError: Raised when a gameroom with the given id does not exist.
            NotGameroomOwnerError: Raised when the user is not the owner of this gameroom.
            GameAlreadyStartedError: Raised when a game has already started.
            NotEnoughPlayersError: Raised when there is only one user in the gameroom.
        """
        gameroom: Gameroom = self._gamerooms_repository.get_gameroom_by_id(
            session=context.session, id=gameroom_id
        )
        gameroom.ensure_is_owner(context.user)
        gameroom.ensure_starting()

        game = self._games_repository.save_game(
            session=context.session,
            game=self._game_toolkit.create_game(gameroom=gameroom),
        )
        self._gamerooms_repository.save_gameroom(
            session=context.session, gameroom=gameroom.with_started_game(game)
        )

        return game

    def disconnect(self, context: Context) -> DisconnectResult:
        """Disconnect a user.

        If the game has not started, the user leaves the gameroom if they are not the
        owner, or the gameroom is deleted if they are.

        If the game is running, does nothing.

        Args:
            context (BaseContext): The request context.

        Returns:
            The result of the disconnect.
        """
        gameroom = self._get_gameroom_for_user(context=context)
        if not gameroom:
            return DisconnectResult()

        if gameroom.game:
            return DisconnectResult(
                gameroom=gameroom, game=gameroom.game, remaining_users=gameroom.users
            )

        if gameroom.is_owner(context.user):
            result = self.delete_gameroom(context=context, gameroom_id=gameroom.id)
            return DisconnectResult(
                gameroom=result.gameroom,
                game=gameroom.game,
                remaining_users=result.remaining_users,
            )
        else:
            gameroom = self.leave_gameroom(context=context, gameroom_id=gameroom.id)
            return DisconnectResult(
                gameroom=gameroom, game=gameroom.game, remaining_users=gameroom.users
            )

    def finish_game(self, context: Context, gameroom_id: UUID) -> None:
        """Finish a game in a gameroom.

        Deletes the game and it's gameroom from the database, along with all
        children objects.

        Args:
            context (Context): context
            gameroom_id (UUID): gameroom_id

        Returns:
            None:
        """
        gameroom = self._gamerooms_repository.get_gameroom_by_id(
            session=context.session, id=gameroom_id
        )

        if gameroom.game:
            self._games_service.delete(context, game=gameroom.game)

        self._gamerooms_repository.delete_gameroom(
            session=context.session, gameroom=gameroom.without_game()
        )

    def _get_gameroom_for_user(self, context: Context) -> Gameroom | None:
        gameroom_id: UUID | None = context.user.current_gameroom_id
        if not gameroom_id:
            return None

        try:
            return self._gamerooms_repository.get_gameroom_by_id(
                session=context.session, id=gameroom_id
            )
        except Exception:
            return None


@frozen
class DeleteGameroomResult:
    """The result of deleting a gameroom."""

    gameroom: Gameroom
    """The gameroom after deletion."""

    remaining_users: tuple[User, ...]
    """The other users that were in the gameroom during the deletion."""


@frozen
class DisconnectResult:
    """The result of disconnecting from a gameroom."""

    gameroom: Gameroom | None = field(default=None)
    """The optional gameroom of the disconnected user."""

    game: Game | None = field(default=None)
    """The optional current game of the gameroom."""

    remaining_users: tuple[User, ...] = field(default=())
    """The other users in the gameroom."""
