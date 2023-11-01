from typing import Any

from flask import request
from marshmallow import fields

from ..common.context import BaseContext, Context
from ..models.dto import GameDto, GameroomDto
from ..services.auth import AuthService
from ..services.gamerooms import GameroomsService
from ..services.games import GamesService
from ..services.users import UsersService
from .base import SUCCESS_RESPONSE, BaseBodySchema, BaseController


class GameroomsController(BaseController):
    """The controller for the gamerooms resource."""

    __slots__ = (
        "_auth_service",
        "_games_service",
        "_gamerooms_service",
        "_users_service",
    )

    def __init__(
        self,
        auth_service: AuthService,
        games_service: GamesService,
        gamerooms_service: GameroomsService,
        users_service: UsersService,
        *args: Any,
        **kwargs: Any,
    ):
        """Initialize new controller.

        Args:
            auth_service (AuthService): The authentication service.
            games_service (GamesService): The games service.
            gamerooms_service (GameroomsService): The gamerooms service.
            users_service (UsersService): The users service.
            args (Any): Additional positional arguments.
            kwargs (Any): Additional keyword arguments.
        """
        self._auth_service: AuthService = auth_service
        self._gamerooms_service: GameroomsService = gamerooms_service
        self._games_service: GamesService = games_service
        self._users_service: UsersService = users_service
        super().__init__(*args, **kwargs)

    def get_gamerooms(self, context: Context) -> list[dict]:
        """Get all active gamerooms.

        Returns a list of gamerooms that don't have deleted status.

        Args:
            context (Context): The request context.

        Returns:
            The list of active gamerooms.
        """
        gamerooms = self._gamerooms_service.get_gamerooms(context=context)
        return [GameroomDto.create(gameroom).serialize() for gameroom in gamerooms]

    def create_gameroom(self, context: Context) -> dict:
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
        gameroom = self._gamerooms_service.create_gameroom(context=context)
        return GameroomDto.create(gameroom).serialize()

    def join_gameroom(self, context: Context, id: str) -> dict:
        """Join a gameroom.

        Joins a gameroom that has a starting status and less than 4 users.

        Args:
            context (Context): The request context.
            id (str): The id of the gameroom to join.

        Sends:
            UserJoinedEvent: To all the other users, with the joining user as data.

        Returns:
            The joined gameroom.

        Raises:
            NotFoundError: Raised when a gameroom with the given id does not exist.
            AlreadyInGameroomError: Raised when the user is already in a gameroom.
            GameAlreadyStartedError: Raised when a game has already started.
            GameroomFullError: Raised when there are already 4 users in the gameroom.
        """
        gameroom = self._gamerooms_service.join_gameroom(context=context, gameroom_id=id)
        self._messages_service.user_joined(sender=context.user, gameroom=gameroom)
        return GameroomDto.create(gameroom).serialize()

    def leave_gameroom(self, context: Context, id: str) -> dict:
        """Leave a gameroom.

        Leaves a gameroom that the user is in and has a starting status.

        Args:
            context (Context): The request context.
            id (str): The id of the gameroom to leave.

        Sends:
            UserLeftEvent: To all remaining users, with the leaving user as data.

        Returns:
            The left gameroom.

        Raises:
            NotFoundError: Raised when a gameroom with the given id does not exist.
            UserNotInGameroomError: Raised when the user is not in this gameroom.
            LeavingOwnGameroomError: Raised when the user attempts to leave their
                own gameroom.
            GameAlreadyStartedError: Raised when a game has already started.
        """
        gameroom = self._gamerooms_service.leave_gameroom(context=context, gameroom_id=id)
        self._messages_service.user_left(sender=context.user, gameroom=gameroom)
        return GameroomDto.create(gameroom).serialize()

    def delete_gameroom(self, context: Context, id: str) -> dict:
        """Delete a gameroom.

        Deletes a gameroom that the user is an owner of.

        Args:
            context (Context): The request context.
            id (str): The id of the gameroom to delete.

        Sends:
            GameroomDeletedEvent: To all the other users, with the gameroom as data.

        Returns:
            The deleted gameroom.

        Raises:
            NotFoundError: Raised when a gameroom with the given id does not exist.
            NotGameroomOwnerError: Raised when the user is not the owner of this gameroom.
            GameAlreadyStartedError: Raised when a game has already started.
        """
        result = self._gamerooms_service.delete_gameroom(context=context, gameroom_id=id)
        self._messages_service.gameroom_deleted(
            sender=context.user,
            gameroom=result.gameroom,
            remaining_users=result.remaining_users,
        )
        return GameroomDto.create(result.gameroom).serialize()

    def start_game(self, context: Context, id: str) -> dict:
        """Start a game.

        Starts the game in this gameroom with users as players. Only the
        gameroom's owner can start the game.

        Args:
            context (Context): The request context.
            id (str): The id of the gameroom to start the game in.

        Sends:
            GameStartedEvent: To all the other users, with the game as data.

        Returns:
            The started game.

        Raises:
            NotFoundError: Raised when a gameroom with the given id does not exist.
            NotGameroomOwnerError: Raised when the user is not the owner of this gameroom.
            GameAlreadyStartedError: Raised when a game has already started.
            NotEnoughPlayersError: Raised when there is only one user in the gameroom.
        """
        game = self._gamerooms_service.start_game(context=context, gameroom_id=id)
        self._messages_service.game_started(sender=context.user, game=game)
        return GameDto.create(game, context.user).serialize()

    def disconnect(self, context: BaseContext) -> dict:
        """User disconnected callback.

        Called by the events server whenever a user disconnects.
        The disconnected user id is passed in the request body.

        Args:
            context (BaseContext): The request context.

        Sends:
            GameroomDeletedEvent: Sent to all gameroom users when the disconnected user
                owns the gameroom, and the game has not started.
            UserLeftEvent: Sent to all gameroom users when the disconnected user
                is not the owner, and the game has not started.
            PlayerWonEvent: Sent to all players when a game is running and the game
                has a winner due to the player leaving.
            PlayerLeftEvent: Sent to all players when a game is running.
            PlayersChangedEvent: Sent to all players when a game is running.
            PileCountChangedEvent: Sent to all players when a game is running and
                has no winner.
            BoardChangedEvent: Sent to all players when a game is running, has no winner,
                and it was the disconnected player's turn.
            TurnStartedEvent: Sent to all players when a game is running, has no winner,
                and it was the disconnected player's turn.

        Returns:
            The success response.

        Raises:
            ValidationError: Raised when the user id is missing form the request body
                or is not a valid UUID.
        """
        self._auth_service.authorize_events_server(headers=request.headers)

        body: dict = self._deserialize_json(DisconnectUserBodySchema())
        user = self._users_service.get_user_by_id(
            session=context.session, user_id=body["user_id"]
        )
        _context = Context(user=user, session=context.session)

        gameroom_result = self._gamerooms_service.disconnect(context=_context)

        if not gameroom_result.gameroom:
            return SUCCESS_RESPONSE

        if gameroom_result.game:
            game_result = self._games_service.disconnect(
                _context, game=gameroom_result.game
            )

            if game_result.game.winner:
                self._gamerooms_service.finish_game(
                    _context, gameroom_id=game_result.game.gameroom_id
                )

            self._messages_service.disconnected_game(sender=user, result=game_result)
        else:
            self._messages_service.disconnected_gameroom(
                sender=user, result=gameroom_result
            )

        return SUCCESS_RESPONSE


class DisconnectUserBodySchema(BaseBodySchema):
    """The schema of the disconnect request body."""

    user_id = fields.UUID(
        required=True,
        error_messages={"required": "A valid 'user_id' is required."},
    )
