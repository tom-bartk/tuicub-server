from typing import Any

from marshmallow import fields, validate

from ..common.context import Context
from ..models.dto import GameStateDto
from ..services.gamerooms import GameroomsService
from ..services.games import GamesService
from .base import BaseBodySchema, BaseController


class GamesController(BaseController):
    """The controller for the games resource."""

    __slots__ = ("_games_service", "_gamerooms_service")

    def __init__(
        self,
        games_service: GamesService,
        gamerooms_service: GameroomsService,
        *args: Any,
        **kwargs: Any,
    ):
        """Initialize new controller.

        Args:
            gamerooms_service (GameroomsService): The gamerooms service.
            games_service (GamesService): The games service.
            args (Any): Additional positional arguments.
            kwargs (Any): Additional keyword arguments.
        """
        self._games_service: GamesService = games_service
        self._gamerooms_service: GameroomsService = gamerooms_service
        super().__init__(*args, **kwargs)

    def move(self, context: Context, id: str) -> dict:
        """Move tiles.

        Moves tiles from the user's rack and/or the board. The resulting board
        should be passed in the request body as a list of lists of tile ids, representing
        the new sets of tiles.

        Args:
            context (Context): The request context.
            id (str): The id of the game.

        Sends:
            RackChangedEvent: Sent to the user performing the move.
            PlayersChangedEvent: Sent to all players.
            BoardChangedEvent: Sent to all players.

        Returns:
            The game state after performing the move.

        Raises:
            NotFoundError: Raised when a game with the given id does not exist.
            ValidationError: Raised when the board is missing from the request body
                or is not a valid list of lists of tile ids.
            GameEndedError: Raised when the game already has a winner.
            UserNotInGameError: Raised when the user is not a part of this game.
            NotUserTurnError: Raised when it is not the user's turn.
            DuplicateTilesError: Raised when there are duplicate tiles on the board.
            MissingBoardTilesError: Raised when the new board is missing tiles from
                the previous board.
            NewTilesNotFromRackError: Raised when there are new tiles that did not
                come from the user's rack.
        """
        body: dict = self._deserialize_json(MoveTilesBodySchema())
        game = self._games_service.move(context=context, game_id=id, board=body["board"])
        self._messages_service.tiles_moved(sender=context.user, game=game)
        return GameStateDto.create(game, context.user).serialize()

    def undo(self, context: Context, id: str) -> dict:
        """Undo a move.

        Undos a previously performed move restoring the board and the user's rack
        to the state from before the move.

        Args:
            context (Context): The request context.
            id (str): The id of the game.

        Sends:
            RackChangedEvent: Sent to the user undoing a move.
            PlayersChangedEvent: Sent to all players.
            BoardChangedEvent: Sent to all players.

        Returns:
            The game state after undoing a move.

        Raises:
            NotFoundError: Raised when a game with the given id does not exist.
            GameEndedError: Raised when the game already has a winner.
            UserNotInGameError: Raised when the user is not a part of this game.
            NotUserTurnError: Raised when it is not the user's turn.
            NoMoveToUndoError: Raised when there are no moves to undo.
        """
        game = self._games_service.undo(context=context, game_id=id)
        self._messages_service.tiles_moved(sender=context.user, game=game)
        return GameStateDto.create(game, context.user).serialize()

    def redo(self, context: Context, id: str) -> dict:
        """Redo a move.

        Redos a previously undone move.

        Args:
            context (Context): The request context.
            id (str): The id of the game.

        Sends:
            RackChangedEvent: Sent to the user redoing a move.
            PlayersChangedEvent: Sent to all players.
            BoardChangedEvent: Sent to all players.

        Returns:
            The game state after redoing a move.

        Raises:
            NotFoundError: Raised when a game with the given id does not exist.
            GameEndedError: Raised when the game already has a winner.
            UserNotInGameError: Raised when the user is not a part of this game.
            NotUserTurnError: Raised when it is not the user's turn.
            NoMoveToRedoError: Raised when there are no moves to redo.
        """
        game = self._games_service.redo(context=context, game_id=id)
        self._messages_service.tiles_moved(sender=context.user, game=game)
        return GameStateDto.create(game, context.user).serialize()

    def end_turn(self, context: Context, id: str) -> dict:
        """End the turn.

        Ends the turn after the user has performed valid moves.

        Args:
            context (Context): The request context.
            id (str): The id of the game.

        Sends:
            PlayerWonEvent: Sent to all players if the user ending their turn has no more
                tiles left in their rack.
            PlayersChangedEvent: Sent to all players if the game has no winner.
            BoardChangedEvent: Sent to all players if the game has no winner.
            TurnEndedEvent: Sent to the user ending their turn if the game has no winner.
            TurnStartedEvent: Sent to the player next in the turn order if the game
                has no winner.

        Returns:
            The game state after ending the turn.

        Raises:
            NotFoundError: Raised when a game with the given id does not exist.
            GameEndedError: Raised when the game already has a winner.
            UserNotInGameError: Raised when the user is not a part of this game.
            NotUserTurnError: Raised when it is not the user's turn.
            NoMovesPerformedError: Raised when the user has not performed any moves.
            NoNewTilesError: Raised when no new tiles have been played.
            InvaildMeldError: Raised when the user has not yet made a valid meld,
                and the current meld is invalid.
        """
        game = self._games_service.end_turn(context=context, game_id=id)
        self._messages_service.turn_ended(sender=context.user, game=game)
        if game.winner:
            self._gamerooms_service.finish_game(
                context=context, gameroom_id=game.gameroom_id
            )

        return GameStateDto.create(game, context.user).serialize()

    def draw(self, context: Context, id: str) -> dict:
        """Draw a tile.

        Draws a new tile from the pile and adds it to the user's rack, while also
        ending the user's turn. To draw a tile, the user must not perform any moves
        this turn.

        Args:
            context (Context): The request context.
            id (str): The id of the game.

        Sends:
            PileCountChangedEvent: Sent to all players.
            TileDrawnEvent: Sent to the drawing user.
            RackChangedEvent: Sent to the drawing user.
            PlayersChangedEvent: Sent to all players.
            BoardChangedEvent: Sent to all players.
            TurnEndedEvent: Sent to the drawing user.
            TurnStartedEvent: Sent to the player next in the turn order.

        Returns:
            The game state after drawing a tile.

        Raises:
            NotFoundError: Raised when a game with the given id does not exist.
            GameEndedError: Raised when the game already has a winner.
            UserNotInGameError: Raised when the user is not a part of this game.
            NotUserTurnError: Raised when it is not the user's turn.
            MovesPerformedError: Raised when the user has performed moves this turn.
        """
        tile, game = self._games_service.draw(context=context, game_id=id)
        self._messages_service.tile_drawn(sender=context.user, tile=tile, game=game)
        return GameStateDto.create(game, context.user).serialize()


class MoveTilesBodySchema(BaseBodySchema):
    """The schema of the move tiles request body."""

    board = fields.List(
        fields.List(fields.Integer(validate=validate.Range(min=0, max=105))),
        required=True,
        error_messages={"required": "A valid 'board' is required."},
    )
