from __future__ import annotations

from attrs import field, frozen

from ..common.context import Context
from ..models.game import Board, Game, Player, Turn
from ..repositories.games import GamesRepository
from .game_toolkit import GameToolkit
from .rng import RngService


class GamesService:
    """The service for querying and manipulating games."""

    __slots__ = ("_game_toolkit", "_games_repository", "_rng_service")

    def __init__(
        self,
        game_toolkit: GameToolkit,
        games_repository: GamesRepository,
        rng_service: RngService,
    ):
        """Initialize new service.

        Args:
            game_toolkit (GameToolkit): The game toolkit.
            games_repository (GamesRepository): The games repository.
            rng_service (RngService): The random numbers generator.
        """
        self._game_toolkit: GameToolkit = game_toolkit
        self._games_repository: GamesRepository = games_repository
        self._rng_service: RngService = rng_service

    def move(self, context: Context, game_id: str, board: list[list[int]]) -> Game:
        """Move tiles.

        Moves tiles from the user's rack and/or the board.

        Args:
            context (Context): The request context.
            game_id (str): The id of the game.
            board (list[list[int]]): The candidate board after the move.

        Returns:
            The game after performing the move.

        Raises:
            NotFoundError: Raised when a game with the given id does not exist.
            GameEndedError: Raised when the game already has a winner.
            UserNotInGameError: Raised when the user is not a part of this game.
            NotUserTurnError: Raised when it is not the user's turn.
            DuplicateTilesError: Raised when there are duplicate tiles on the board.
            MissingBoardTilesError: Raised when the new board is missing tiles from
                the previous board.
            NewTilesNotFromRackError: Raised when there are new tiles that did not
                come from the user's rack.
        """
        game, player = self._ensure_game_player(context, game_id)

        new_rack, new_board = self._game_toolkit.perform_move(
            rack=player.rack,
            current=game.game_state.board,
            candidate=Board.create(tilesets=board),
        )
        game = game.with_new_move(rack=new_rack, board=new_board, player=player)

        return self._games_repository.save_game(session=context.session, game=game)

    def undo(self, context: Context, game_id: str) -> Game:
        """Undo a move.

        Undos a previously performed move.

        Args:
            context (Context): The request context.
            game_id (str): The id of the game.

        Returns:
            The game after undoing a move.

        Raises:
            NotFoundError: Raised when a game with the given id does not exist.
            GameEndedError: Raised when the game already has a winner.
            UserNotInGameError: Raised when the user is not a part of this game.
            NotUserTurnError: Raised when it is not the user's turn.
            NoMoveToUndoError: Raised when there are no moves to undo.
        """
        game, player = self._ensure_game_player(context, game_id)

        game = game.with_undo(player=player)

        return self._games_repository.save_game(session=context.session, game=game)

    def redo(self, context: Context, game_id: str) -> Game:
        """Redo a move.

        Redos a previously undone move.

        Args:
            context (Context): The request context.
            game_id (str): The id of the game.

        Returns:
            The game after redoing a move.

        Raises:
            NotFoundError: Raised when a game with the given id does not exist.
            GameEndedError: Raised when the game already has a winner.
            UserNotInGameError: Raised when the user is not a part of this game.
            NotUserTurnError: Raised when it is not the user's turn.
            NoMoveToRedoError: Raised when there are no moves to redo.
        """
        game, player = self._ensure_game_player(context, game_id)

        game = game.with_redo(player=player)

        return self._games_repository.save_game(session=context.session, game=game)

    def end_turn(self, context: Context, game_id: str) -> Game:
        """End the turn.

        Ends the turn after the user has performed valid moves.

        Args:
            context (Context): The request context.
            game_id (str): The id of the game.

        Returns:
            The game after ending the turn.

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
        game, player = self._ensure_game_player(context, game_id)
        game.turn.ensure_has_moves()
        self._game_toolkit.ensure_board_valid(game=game)

        if not game.has_made_meld(user_id=context.user.id):
            self._game_toolkit.ensure_meld_valid(
                rack=game.turn.starting_rack,
                current=game.game_state.board,
                previous=game.turn.starting_board,
            )
            game = game.with_new_meld(user_id=context.user.id)
        game = game.with_next_turn(current_player=player)

        return self._games_repository.save_game(session=context.session, game=game)

    def draw(self, context: Context, game_id: str) -> tuple[int, Game]:
        """Draw a tile.

        Draws a new tile from the pile and adds it to the user's rack, while also
        ending the user's turn. To draw a tile, the user must not have performed any moves
        this turn.

        Args:
            context (Context): The request context.
            game_id (str): The id of the game.

        Returns:
            The game after drawing a tile.

        Raises:
            NotFoundError: Raised when a game with the given id does not exist.
            GameEndedError: Raised when the game already has a winner.
            UserNotInGameError: Raised when the user is not a part of this game.
            NotUserTurnError: Raised when it is not the user's turn.
            MovesPerformedError: Raised when the user has performed moves this turn.
        """
        game, player = self._ensure_game_player(context, game_id)
        game.turn.ensure_has_no_moves()

        tile = game.game_state.pile.draw(self._rng_service.pick)
        game = game.with_drawn_tile(tile, player)
        game = game.with_next_turn(current_player=player)

        return tile, self._games_repository.save_game(session=context.session, game=game)

    def disconnect(self, context: Context, game: Game) -> GameDisconnectResult:
        """Disconnect a player.

        Disconnects a player from a game by removing them from the players list, and
        returning their rack to the pile. If it was the player's turn, the board is
        restored to the state from the start of the turn, and the next turn is started.
        If only one player remains, the game ends.

        Args:
            context (Context): The request context.
            game (Game): The game to disconnect from.

        Returns:
            The game after disconnecting the player.

        Raises:
            UserNotInGameError: Raised when the player is not part of the game.
            GameEndedError: Raised when the game already has a winner.
        """
        game.ensure_not_ended()
        player = game.player_for_user_id(context.user.id)

        game, turn = game.with_disconnected_player(player, rng=self._rng_service)

        game = self._games_repository.save_game(session=context.session, game=game)
        return GameDisconnectResult(game=game, player=player, turn=turn)

    def delete(self, context: Context, game: Game) -> None:
        """Delete a game.

        Args:
            context (Context): The request context.
            game (Game): The game to delete.
        """
        self._games_repository.delete_game(session=context.session, game=game)

    def _ensure_game_player(self, context: Context, game_id: str) -> tuple[Game, Player]:
        game = self._games_repository.get_game_by_id(session=context.session, id=game_id)
        game.ensure_not_ended()

        player = game.player_for_user_id(user_id=context.user.id)
        game.ensure_has_turn(player)

        return game, player


@frozen
class GameDisconnectResult:
    """The result of disconnecting from a game."""

    game: Game
    """The game the player disconnected from."""

    player: Player
    """The disconnecting player."""

    turn: Turn | None = field(default=None)
    """The next turn if it was the disconnected player's turn."""
