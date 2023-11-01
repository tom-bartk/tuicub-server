from __future__ import annotations

import uuid

from more_itertools import all_unique, flatten

from ..common.errors import BadRequestError
from ..models.game import Board, Game, GameState, Pile, Player, Tileset, Turn
from ..models.gameroom import Gameroom
from ..models.user import User
from .rng import RngService
from .tilesets import TilesetsService

MIN_MELD_VALUE = 30


class GameToolkit:
    """The service performing core operations on games."""

    __slots__ = ("_rng_service", "_tilesets_service")

    def __init__(self, rng_service: RngService, tilesets_service: TilesetsService):
        """Initialize a new service.

        Args:
            rng_service (RngService): The random numbers generator.
            tilesets_service (TilesetsService): The service for verifying tilesets.
        """
        self._rng_service: RngService = rng_service
        self._tilesets_service: TilesetsService = tilesets_service

    def create_game(self, gameroom: Gameroom) -> Game:
        """Create a new game.

        Creates a new game based on the passed gameroom.
        A player is created for every gameroom user with a randomly drawn rack.
        The first player to move is the first one in the randomized turn order.

        Args:
            gameroom (Gameroom): The gameroom to create a game for.

        Returns:
            The created game.

        Raises:
            NotEnoughPlayersError: Raised when there is only one user in the gameroom.
        """
        if len(gameroom.users) == 1:
            raise NotEnoughPlayersError()

        pile = Pile(tiles=self._rng_service.shuffle(TILE_IDS.copy()))
        players = self._create_players(pile, gameroom.users)

        game_id = uuid.uuid4()
        return Game(
            id=game_id,
            gameroom_id=gameroom.id,
            game_state=GameState(
                id=uuid.uuid4(),
                game_id=game_id,
                players=players,
                board=Board(),
                pile=pile,
            ),
            turn=Turn(
                id=uuid.uuid4(),
                game_id=game_id,
                player_id=players[0].id,
                starting_rack=players[0].rack,
                starting_board=Board(),
            ),
            turn_order=tuple(player.user_id for player in players),
        )

    def perform_move(
        self, rack: Tileset, current: Board, candidate: Board
    ) -> tuple[Tileset, Board]:
        """Move tiles.

        Attempts to perform a move, which will result in the candidate
        board state. For the move to be valid, the candidate board must not
        contain any duplicate tiles, have all the tiles from the current board,
        and all new tiles must come from the player's rack.

        Args:
            rack (Tileset): The current rack of the player.
            current (Board): The current board.
            candidate (Board): The board after the move.

        Returns:
            The pair of the player's rack and the board after the move.

        Raises:
            DuplicateTilesError: Raised when the candidate board has duplicate tiles.
            MissingBoardTilesError: Raised when the candidate board is missing tiles from
                the current board.
            NewTilesNotFromRackError: Raised when there are new tiles that did not
                come from the player's rack.
        """
        _ensure_no_duplicate_tiles(current, candidate, rack)
        _ensure_has_all_previous_tiles(current, candidate, rack)
        _ensure_all_new_tiles_from_rack(current, candidate, rack)

        new_tiles = set(candidate.all_tiles()).difference(current.all_tiles())
        return (Tileset.create(list(set(rack.tiles).difference(new_tiles))), candidate)

    def ensure_board_valid(self, game: Game) -> None:
        """Validate the board.

        Validates the game's board. For the game to have a valid board, it must not
        contain any duplicate tiles, have all the tiles from the board at the start
        of the turn, all new tiles must come from the player's rack, and all tile sets
        must be valid.

        Args:
            game (Game): The game to validate.

        Raises:
            DuplicateTilesError: Raised when the current board has duplicate tiles.
            MissingBoardTilesError: Raised when the current board is missing tiles from
                the board at the start of the turn.
            NewTilesNotFromRackError: Raised when there are new tiles that did not
                come from the player's rack.
            NoNewTilesError: Raised when there are no new tiles on the board.
            InvalidTilesetsError: Raised when there are invalid tile sets on the board.
        """
        rack = game.turn.starting_rack
        current = game.game_state.board
        previous = game.turn.starting_board

        _ensure_no_duplicate_tiles(previous, current, rack)
        _ensure_has_all_previous_tiles(previous, current, rack)
        _ensure_all_new_tiles_from_rack(previous, current, rack)

        new_tiles = set(current.all_tiles()).difference(previous.all_tiles())
        if not new_tiles:
            raise NoNewTilesError(rack=rack, current=previous, candidate=current)

        if not all(
            self._tilesets_service.is_valid(tileset) for tileset in current.tilesets
        ):
            raise InvalidTilesetsError(rack=rack, current=previous, candidate=current)

    def ensure_meld_valid(self, rack: Tileset, current: Board, previous: Board) -> None:
        """Check if a meld is valid.

        Check if the player has made a valid meld. For the meld to be valid board,
        a player must create tile sets only from their own rack, and the combined
        value of the tiles must be greater than or equal 30.

        Args:
            rack (Tileset): The current rack of the player.
            current (Board): The current board.
            previous (Board): The board at the start of the turn.

        Raises:
            InvalidMeldError: Raised when the meld is invalid.
        """
        previous_tilesets = frozenset(frozenset(ts.tiles) for ts in previous.tilesets)
        current_tilesets = frozenset(frozenset(ts.tiles) for ts in current.tilesets)
        new_tilesets = current_tilesets.difference(previous_tilesets)

        new_tilesets_tiles = frozenset(flatten(new_tilesets))
        rack_set = frozenset(rack.tiles)

        if not rack_set.issuperset(new_tilesets_tiles):
            raise InvalidMeldError(rack=rack, current=previous, candidate=current)

        tilesets_value = sum(
            self._tilesets_service.value_of(Tileset.create(list(tileset)))
            for tileset in new_tilesets
        )
        if tilesets_value < MIN_MELD_VALUE:
            raise InvalidMeldError(rack=rack, current=previous, candidate=current)

    def _create_players(self, pile: Pile, users: tuple[User, ...]) -> tuple[Player, ...]:
        return tuple(
            self._rng_service.shuffle(
                [
                    Player(
                        id=uuid.uuid4(),
                        name=user.name,
                        user_id=user.id,
                        rack=pile.draw_rack(self._rng_service.pick),
                    )
                    for user in users
                ]
            )
        )


def _ensure_has_all_previous_tiles(
    previous: Board, current: Board, rack: Tileset
) -> None:
    previous_tiles = set(previous.all_tiles())
    current_tiles = set(current.all_tiles())
    if not current_tiles.issuperset(previous_tiles):
        raise MissingBoardTilesError(rack=rack, current=previous, candidate=current)


def _ensure_all_new_tiles_from_rack(
    previous: Board, current: Board, rack: Tileset
) -> None:
    new_tiles = set(current.all_tiles()).difference(previous.all_tiles())
    if not set(rack.tiles).issuperset(new_tiles):
        raise NewTilesNotFromRackError(rack=rack, current=previous, candidate=current)


def _ensure_no_duplicate_tiles(previous: Board, current: Board, rack: Tileset) -> None:
    if not all_unique(current.all_tiles()):
        raise DuplicateTilesError(rack=rack, current=previous, candidate=current)


class MoveError(BadRequestError):
    """The base error class for all moves related errors."""

    def __init__(self, rack: Tileset, current: Board, candidate: Board):
        super().__init__(
            {
                "rack": rack.as_list(),
                "current_board": current.as_list(),
                "candidate_board": candidate.as_list(),
            }
        )


class NotEnoughPlayersError(BadRequestError):
    @property
    def message(self) -> str:
        return "At least two users are needed to start the game."

    @property
    def error_name(self) -> str:
        return "not_enough_players"


class NoNewTilesError(MoveError):
    @property
    def message(self) -> str:
        return "There are no new tiles on the board."

    @property
    def error_name(self) -> str:
        return "no_new_tiles"


class DuplicateTilesError(MoveError):
    @property
    def message(self) -> str:
        return "Board contains duplicate tiles."

    @property
    def error_name(self) -> str:
        return "duplicate_tiles"


class MissingBoardTilesError(MoveError):
    @property
    def message(self) -> str:
        return "The new board is missing tiles from the current one."

    @property
    def error_name(self) -> str:
        return "missing_board_tiles"


class NewTilesNotFromRackError(MoveError):
    @property
    def message(self) -> str:
        return "Not all played tiles are from your rack."

    @property
    def error_name(self) -> str:
        return "new_tiles_not_from_rack"


class InvalidTilesetsError(MoveError):
    @property
    def message(self) -> str:
        return "The are invalid tiles sets on the board."

    @property
    def error_name(self) -> str:
        return "invalid_tilesets"


class InvalidMeldError(MoveError):
    @property
    def message(self) -> str:
        return "The attempted meld is invalid."

    @property
    def error_name(self) -> str:
        return "invalid_meld"


TILE_IDS = list(range(106))
