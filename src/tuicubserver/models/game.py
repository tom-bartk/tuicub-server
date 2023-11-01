from __future__ import annotations

import json
import uuid
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING
from uuid import UUID

from attrs import evolve, field, frozen
from more_itertools import first, flatten, last

from ..common.errors import BadRequestError, ForbiddenError

if TYPE_CHECKING:
    from ..services.rng import RngService

JOKERS = {104, 105}
MAX_TILE_VALUE = 13


@frozen
class Tileset:
    """The set of tiles on the board.

    Attributes:
        tiles (tuple[int, ...]): The sorted tile ids that compose this set.
    """

    tiles: tuple[int, ...] = field(default=())

    def serialize(self) -> str:
        """Returns the string representation."""
        return json.dumps(list(self.tiles))

    def as_list(self) -> list[int]:
        """Returns the list of tile ids in this set."""
        return list(self.tiles)

    @classmethod
    def create(cls, tiles: list[int]) -> Tileset:
        """Create a new set from list of tile ids."""
        return Tileset(tiles=tuple(sorted(tiles)))

    @classmethod
    def deserialize(cls, raw: str) -> Tileset:
        """Create a new set from the string representation."""
        tiles: list[int] = json.loads(raw)
        return Tileset.create(tiles=tiles)

    def contains_jokers(self) -> bool:
        """Returns true if this set contains one or two jokers."""
        return any(tile in JOKERS for tile in self.tiles)

    def filter_jokers(self) -> tuple[int, ...]:
        """Returns tuple of tile ids without the jokers."""
        return tuple(tile for tile in self.tiles if tile not in JOKERS)

    def jokers_count(self) -> int:
        """Returns the number of jokers in this set."""
        return len([tile for tile in self.tiles if tile in JOKERS])

    def with_new_tile(self, tile: int) -> Tileset:
        """Return a copy of the tile set with the added new tile."""
        return Tileset.create([*self.tiles, tile])

    def __len__(self) -> int:
        return len(self.tiles)

    def __hash__(self) -> int:
        return hash(self.tiles)


class Pile:
    """The pile of tiles that players can draw from."""

    __slots__ = "_tiles"

    @property
    def tiles(self) -> tuple[int, ...]:
        """The tile ids currently on this pile."""
        return tuple(self._tiles)

    def __init__(self, tiles: list[int]):
        """Initialize new pile.

        Args:
            tiles (list[int]): The tile ids to put on the tile.
        """
        self._tiles: list[int] = tiles

    def draw(self, pick: Callable[[Sequence[int]], int]) -> int:
        """Draw a tile.

        Args:
            pick (Callable[[Sequence[int]], int]): The function that randomly
                selects an item from a list.

        Returns:
            The id of the drawn tile.
        """
        tile = pick(self._tiles)
        self._tiles.remove(tile)
        return tile

    def draw_rack(self, pick: Callable[[Sequence[int]], int]) -> Tileset:
        """Draw a rack consisting of 14 random tiles.

        Args:
            pick (Callable[[Sequence[int]], int]): The function that randomly
                selects an item from a list.

        Returns:
            The drawn rack.
        """
        rack_size = 14
        return Tileset(tiles=tuple(self.draw(pick) for _ in range(rack_size)))

    def return_rack(
        self, rack: Tileset, shuffle: Callable[[list[int]], list[int]]
    ) -> None:
        """Put tiles from the rack back on the pile.

        Args:
            rack (Tileset): The rack to return.
            shuffle (Callable[[list[int]], list[int]]): The function that shuffles a list.
        """
        self._tiles = shuffle([*self._tiles, *rack.tiles])

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Pile):
            return NotImplemented  # no cov

        return self.tiles == other.tiles

    def __hash__(self) -> int:
        return hash(self.tiles)

    def __len__(self) -> int:
        return len(self._tiles)


@frozen
class Board:
    """The list of played sets of tiles in a game.

    Attributes:
        tilesets (tuple[Tileset, ...]): The sets of tiles that this board consists of.
    """

    tilesets: tuple[Tileset, ...] = field(default=())

    @classmethod
    def deserialize(cls, raw: list[str]) -> Board:
        """Returns the string representation."""
        return Board(tilesets=tuple(Tileset.deserialize(raw=tileset) for tileset in raw))

    @classmethod
    def create(cls, tilesets: list[list[int]]) -> Board:
        """Create a new board from list of lists of tile ids."""
        return Board(
            tilesets=tuple(Tileset.create(tiles=tileset) for tileset in tilesets)
        )

    def all_tiles(self) -> list[int]:
        """Return a flattened list of all tile ids present on the board."""
        return list(flatten([tileset.tiles for tileset in self.tilesets]))

    def serialize(self) -> list[str]:
        """Return a list of serialized tile sets on the board."""
        return [tileset.serialize() for tileset in self.tilesets]

    def as_list(self) -> list[list[int]]:
        """Return a list of of lists of tile ids on the board."""
        return [tileset.as_list() for tileset in self.tilesets]


@frozen
class Player:
    """The player representing a user in a game.

    Attributes:
        id (UUID): The id of the player.
        name (str): The name of the player.
        rack (Tileset): The current rack of the player.
        user_id (UUID): The id of the user that this player represents.
    """

    id: UUID
    name: str
    rack: Tileset
    user_id: UUID

    def with_rack(self, rack: Tileset) -> Player:
        """Return a copy of the player with a new rack.

        Args:
            rack (Tileset): The rack to set.

        Returns:
            The updated player.
        """
        return evolve(self, rack=rack)


@frozen
class Move:
    """The model of a single tiles move.

    Attributes:
        id (UUID): The id of the move.
        board (Board): The board after the move.
        rack (Tileset): The rack of the player after the move.
        revision (int): The revision of the move inside a turn used for undo/redo.
        turn_id (UUID): The id of the turn that this move belongs to.
    """

    id: UUID
    board: Board
    rack: Tileset
    revision: int
    turn_id: UUID


@frozen
class Turn:
    """The model of a single turn in a game.

    Attributes:
        id (UUID): The id of the turn.
        game_id (UUID): The id of the game that this turn belongs to.
        player_id (UUID): The id of the player that has this turn.
        starting_rack (Tileset): The rack of the player at the start of this turn.
        starting_board (Board): The board at the start of this turn.
        moves (tuple[Move, ...]): Moves made this turn.
        revision (int): The current revision used for undo/redo.
    """

    id: UUID
    game_id: UUID
    player_id: UUID
    starting_rack: Tileset
    starting_board: Board
    moves: tuple[Move, ...] = field(default=())
    revision: int = field(default=0)

    def with_new_move(self, rack: Tileset, board: Board) -> Turn:
        """Return a copy of this turn with a new move.

        Deletes all moves that have revision greater than the revision of the turn.
        The newly created move has a revision equal to the current plus one.
        The turn has it's revision incremeneted by one.

        Args:
            rack (Tileset): The player's rack after the move.
            board (Board): The board after the move.

        Returns:
            The turn with the new move.
        """
        move = Move(
            id=uuid.uuid4(),
            turn_id=self.id,
            revision=self.revision + 1,
            rack=rack,
            board=board,
        )
        return evolve(
            self,
            moves=(*(mv for mv in self.moves if mv.revision <= self.revision), move),
            revision=self.revision + 1,
        )

    def previous_move(self) -> Move | None:
        """Return a previous move.

        Returns the previously performed move. If the turn's revision equals 1,
        returns None.

        Returns:
            The previous move, or None if the turn's revision is 1.

        Raises:
            NoMoveToUndoError: Raised when there are no previous moves.
        """
        if self.revision == 1:
            return None

        move: Move | None = next(
            (move for move in self.moves if move.revision == self.revision - 1), None
        )
        if not move:
            raise NoMoveToUndoError(revision=self.revision)
        return move

    def next_move(self) -> Move:
        """Return a previously undone move.

        Returns:
            The next move.

        Raises:
            NoMoveToRedoError: Raised when there are no next moves.
        """
        move: Move | None = next(
            (move for move in self.moves if move.revision == self.revision + 1), None
        )
        if not move:
            raise NoMoveToRedoError(revision=self.revision)
        return move

    def with_revision(self, revision: int) -> Turn:
        """Return a copy of this turn with a new revision.

        Args:
            revision (int): The revision to set.

        Returns:
            The turn with an updated revision.
        """
        return evolve(self, revision=revision)

    def ensure_has_no_moves(self) -> None:
        """Verify that the player has not made any moves this turn.

        Raises:
            MovesPerformedError: Raised when the player has made one or more moves.
        """
        if self.revision > 0:
            raise MovesPerformedError(revision=self.revision)

    def ensure_has_moves(self) -> None:
        """Verify that the player has made at least one move this turn.

        Raises:
            NoMovesPerformedError: Raised when the player has not made any moves.
        """
        if self.revision == 0:
            raise NoMovesPerformedError(revision=self.revision)


@frozen
class GameState:
    """The model representing a state of a game.

    Attributes:
        id (UUID): The id of the game state.
        game_id (UUID): The id the game that this game state belongs to.
        players (tuple[Player, ...]): The players participating in this game.
        board (Board): The current board of the game.
        pile (Pile): The current pile of the game.
    """

    id: UUID
    game_id: UUID
    players: tuple[Player, ...]
    board: Board
    pile: Pile

    def player_for_id(self, id: UUID) -> Player:
        """Get a player for an id.

        Args:
            id (UUID): The id of the player.

        Returns:
            The player for the given id.

        Raises:
            PlayerNotFoundError: Raised when a player with the id is not in the game.
        """
        if player := next((player for player in self.players if player.id == id), None):
            return player
        raise PlayerNotFoundError(player_id=id)

    def with_updated_player(self, player: Player) -> GameState:
        """Return a copy of this game state with an updated player.

        Args:
            player (Player): The player to update.

        Returns:
            The game state with an updated player.

        Raises:
            PlayerNotFoundError: Raised when the player is not in this game.
        """
        player_ids = [p.id for p in self.players]
        if player.id not in player_ids:
            raise PlayerNotFoundError(player_id=player.id)

        player_index = player_ids.index(player.id)

        players = list(self.players)
        players[player_index] = player

        return evolve(self, players=tuple(players))

    def with_board(self, board: Board) -> GameState:
        """Return a copy of this game state with a new board.

        Args:
            board (Board): The board to set.

        Returns:
            The game state with an updated board.
        """
        return evolve(self, board=board)


@frozen
class Game:
    """The model representing a game.

    Attributes:
        id (UUID): The id of the game.
        gameroom_id (UUID): The id the gameroom that the game belongs to.
        game_state (GameState): The current state of the game.
        turn (Turn): The current turn of the game.
        turn_order (tuple[UUID, ...]): The list of user ids representing
            the order of turns.
        made_meld (tuple[UUID, ...]): The registry of users that have made a valid meld.
        winner (Player | None): The optional winner of the game.
    """

    id: UUID
    gameroom_id: UUID
    game_state: GameState
    turn: Turn
    turn_order: tuple[UUID, ...]
    made_meld: tuple[UUID, ...] = field(default=())
    winner: Player | None = field(default=None)

    def new_tiles(self) -> list[int]:
        """Return all new tile ids that have been played this turn."""
        return list(
            set(self.game_state.board.all_tiles()).difference(
                self.turn.starting_board.all_tiles()
            )
        )

    def current_player(self) -> Player:
        """Return the player that currently has the turn."""
        return self.game_state.player_for_id(id=self.turn.player_id)

    def player_after(self, player: Player) -> Player:
        """Return a player that is next in the turn order.

        Args:
            player (Player): The player to get the next player for.

        Returns:
            The player next in the turn order.

        Raises:
            UserNotInGameError: Raised when the user of the player is not in the game.
        """
        if last(self.turn_order) == player.user_id:
            return self.player_for_user_id(user_id=first(self.turn_order))
        else:
            index = self.turn_order.index(player.user_id)
            return self.player_for_user_id(user_id=self.turn_order[index + 1])

    def player_for_user_id(self, user_id: UUID) -> Player:
        """Return a player for the given user id.

        Args:
            user_id (UUID): The id of the user to find the player for.

        Returns:
            The player for the given user id.

        Raises:
            UserNotInGameError: Raised when the user is not in the game.
        """
        try:
            return next(
                player for player in self.game_state.players if player.user_id == user_id
            )
        except Exception as e:
            raise UserNotInGameError(
                user_id=user_id, players=self.game_state.players
            ) from e

    def ensure_has_turn(self, player: Player) -> None:
        """Verify that it is the player's turn.

        Args:
            player (Player): The player to verify.

        Raises:
            NotUserTurnError: Raised when it is not the player's turn.
        """
        if player.id != self.turn.player_id:
            raise NotUserTurnError(
                player_id=player.id, current_player_id=self.turn.player_id
            )

    def ensure_not_ended(self) -> None:
        """Verify that the game has not ended.

        Raises:
            GameEndedError: Raised when the game already has a winner.
        """
        if self.winner is not None:
            raise GameEndedError()

    def has_made_meld(self, user_id: UUID) -> bool:
        """Return true if the user with the given id has made a valid meld."""
        return user_id in self.made_meld

    def with_new_meld(self, user_id: UUID) -> Game:
        """Return a copy of this game with a new user id added to the melds registry.

        Args:
            user_id (UUID): The user id to add.

        Returns:
            The game with an updated registry of melds.
        """
        return evolve(self, made_meld=(*self.made_meld, user_id))

    def with_new_move(self, rack: Tileset, board: Board, player: Player) -> Game:
        """Return a copy of this game with a new move added to the turn.

        The rack of the player and the board are updated to the values after the move.

        Args:
            rack (Tileset): The player's rack after the move.
            board (Board): The board after the move.
            player (Player): The player performing the move.

        Returns:
            The game after performing the move.

        Raises:
            PlayerNotFoundError: Raised when the player is not in this game.
        """
        return evolve(
            self,
            game_state=self.game_state.with_updated_player(
                player.with_rack(rack)
            ).with_board(board),
            turn=self.turn.with_new_move(rack=rack, board=board),
        )

    def with_next_turn(self, current_player: Player) -> Game:
        """Return a copy of the game with a next turn.

        Args:
            current_player (Player): The player that currently has turn.

        Returns:
            The game with a next turn.
        """
        if not current_player.rack.tiles:
            return evolve(self, winner=current_player)
        else:
            next_player = self.player_after(current_player)
            turn = Turn(
                id=uuid.uuid4(),
                game_id=self.id,
                player_id=next_player.id,
                starting_rack=next_player.rack,
                starting_board=self.game_state.board,
            )
            return evolve(self, turn=turn)

    def with_undo(self, player: Player) -> Game:
        """Return a copy of the game with an undone move.

        Args:
            player (Player): The player undoing the move.

        Returns:
            The game with an undone move.

        Raises:
            NoMoveToUndoError: Raised when there are no moves to undo.
        """
        move = self.turn.previous_move()
        if not move:
            return evolve(
                self,
                game_state=self.game_state.with_updated_player(
                    player.with_rack(self.turn.starting_rack)
                ).with_board(self.turn.starting_board),
                turn=self.turn.with_revision(0),
            )

        return evolve(
            self,
            game_state=self.game_state.with_updated_player(
                player.with_rack(move.rack)
            ).with_board(move.board),
            turn=self.turn.with_revision(move.revision),
        )

    def with_redo(self, player: Player) -> Game:
        """Return a copy of the game with a redone move.

        Args:
            player (Player): The player redoing the move.

        Returns:
            The game with a redone move.

        Raises:
            NoMoveToRedoError: Raised when there are no moves to redo.
        """
        move = self.turn.next_move()
        return evolve(
            self,
            game_state=self.game_state.with_updated_player(
                player.with_rack(move.rack)
            ).with_board(move.board),
            turn=self.turn.with_revision(move.revision),
        )

    def with_drawn_tile(self, tile: int, player: Player) -> Game:
        """Return a copy of the game with a tile added to the player's rack.

        Args:
            tile (int): The drawn tile.
            player (Player): The player that drawn the tile.

        Returns:
            The game with an updated player.
        """
        return evolve(
            self,
            game_state=self.game_state.with_updated_player(
                player.with_rack(player.rack.with_new_tile(tile))
            ),
        )

    def with_disconnected_player(
        self, player: Player, rng: RngService
    ) -> tuple[Game, Turn | None]:
        """Return a copy of the game after the player disconnects.

        Removes the player from the game, and returns their rack to the pile.
        If it was the player's turn, the board is restored to the state from the start of
        the turn, and the next turn is started. If only one player remains, the game ends.

        Args:
            player (Player): The disconnecting player.
            rng (RngService): The rng service used for shuffling the pile.

        Returns:
            A pair of the updated game, and an optional new turn, if the disconnect
            resulted in starting a new turn.
        """
        players = tuple(
            [player_ for player_ in self.game_state.players if player_.id != player.id]
        )
        game_state = evolve(self.game_state, players=players)

        if len(players) == 1:
            return evolve(self, game_state=game_state, winner=first(players)), None

        self.game_state.pile.return_rack(rack=player.rack, shuffle=rng.shuffle)
        turn_order = tuple(uid for uid in self.turn_order if uid != player.user_id)

        if self.turn.player_id == player.id:
            next_player = self.player_after(player)
            game_state = evolve(game_state, board=self.turn.starting_board)
            turn = Turn(
                id=uuid.uuid4(),
                game_id=self.id,
                player_id=next_player.id,
                starting_rack=next_player.rack,
                starting_board=self.turn.starting_board,
            )
            return (
                evolve(self, turn=turn, game_state=game_state, turn_order=turn_order),
                turn,
            )
        return (
            evolve(self, game_state=game_state, turn_order=turn_order),
            None,
        )


class UserNotInGameError(ForbiddenError):
    @property
    def message(self) -> str:
        return "You are not in this game."

    @property
    def error_name(self) -> str:
        return "user_not_in_game"

    def __init__(self, user_id: UUID, players: tuple[Player, ...]):
        super().__init__(
            info={
                "user_id": str(user_id),
                "users": [str(player.user_id) for player in players],
            }
        )


class NotUserTurnError(ForbiddenError):
    @property
    def message(self) -> str:
        return "Please wait for your turn."

    @property
    def error_name(self) -> str:
        return "not_user_turn"

    def __init__(self, player_id: UUID, current_player_id: UUID):
        super().__init__(
            info={
                "player_id": str(player_id),
                "current_player_id": str(current_player_id),
            }
        )


class NoMoveToUndoError(BadRequestError):
    @property
    def message(self) -> str:
        return "No moves to undo."

    @property
    def error_name(self) -> str:
        return "no_move_to_undo"

    def __init__(self, revision: int):
        super().__init__(info={"revision": revision})


class NoMoveToRedoError(BadRequestError):
    @property
    def message(self) -> str:
        return "No moves to redo."

    @property
    def error_name(self) -> str:
        return "no_move_to_redo"

    def __init__(self, revision: int):
        super().__init__(info={"revision": revision})


class NoMovesPerformedError(BadRequestError):
    @property
    def message(self) -> str:
        return "You can't end a turn without playing any tiles."

    @property
    def error_name(self) -> str:
        return "no_moves_performed"

    def __init__(self, revision: int):
        super().__init__(info={"revision": revision})


class MovesPerformedError(BadRequestError):
    @property
    def message(self) -> str:
        return "You can't draw a tile after performing a move."

    @property
    def error_name(self) -> str:
        return "moves_performed"

    def __init__(self, revision: int):
        super().__init__(info={"revision": revision})


class PlayerNotFoundError(BadRequestError):
    @property
    def message(self) -> str:
        return "Player not found."

    @property
    def error_name(self) -> str:
        return "player_not_found"

    def __init__(self, player_id: UUID):
        super().__init__(info={"player_id": str(player_id)})


class GameEndedError(BadRequestError):
    @property
    def message(self) -> str:
        return "Game has already ended."

    @property
    def error_name(self) -> str:
        return "game_ended"
