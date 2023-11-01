from uuid import UUID

from .db import (
    DbGame,
    DbGameroom,
    DbGameState,
    DbMove,
    DbPlayer,
    DbTurn,
    DbUser,
    DbUserToken,
)
from .game import Board, Game, GameState, Move, Pile, Player, Tileset, Turn
from .gameroom import Gameroom
from .user import User, UserToken


class Mapper:
    """The mapper that maps between domain and database models."""

    def to_domain_gameroom(self, gameroom: DbGameroom) -> Gameroom:
        """Maps a database gameroom to a domain gameroom."""
        return Gameroom(
            id=gameroom.id,
            name=gameroom.name,
            owner_id=gameroom.owner_id,
            status=gameroom.status,
            game=None if not gameroom.game else self.to_domain_game(gameroom.game),
            users=tuple(self.to_domain_user(user=user) for user in gameroom.users),
            created_at=gameroom.created_at,
        )

    def to_domain_user(self, user: DbUser) -> User:
        """Maps a database user to a domain user."""
        return User(
            id=user.id, name=user.name, current_gameroom_id=user.current_gameroom_id
        )

    def to_domain_user_token(self, user_token: DbUserToken) -> UserToken:
        """Maps a database authentication token to a domain authentication token."""
        return UserToken(
            id=user_token.id, token=user_token.token, user_id=user_token.user_id
        )

    def to_domain_game(self, game: DbGame) -> Game:
        """Maps a database game to a domain game."""
        return Game(
            gameroom_id=game.gameroom_id,
            game_state=self.to_domain_game_state(game_state=game.game_state),
            turn=self.to_domain_turn(turn=game.turn),
            turn_order=tuple(UUID(user_id) for user_id in game.turn_order),
            winner=None if not game.winner else self.to_domain_player(game.winner),
            id=game.id,
            made_meld=tuple(UUID(user_id) for user_id in game.made_meld),
        )

    def to_domain_game_state(self, game_state: DbGameState) -> GameState:
        """Maps a database game state to a domain game state."""
        return GameState(
            id=game_state.id,
            game_id=game_state.game_id,
            players=tuple(self.to_domain_player(player) for player in game_state.players),
            board=Board.deserialize(game_state.board),
            pile=Pile(tiles=game_state.pile),
        )

    def to_domain_player(self, player: DbPlayer) -> Player:
        """Maps a database player to a domain player."""
        return Player(
            id=player.id,
            user_id=player.user_id,
            name=player.name,
            rack=Tileset.create(player.rack),
        )

    def to_domain_turn(self, turn: DbTurn) -> Turn:
        """Maps a database turn to a domain turn."""
        return Turn(
            id=turn.id,
            game_id=turn.game_id,
            player_id=turn.player_id,
            starting_rack=Tileset.create(turn.starting_rack),
            starting_board=Board.deserialize(turn.starting_board),
            moves=tuple(self.to_domain_move(move) for move in turn.moves),
            revision=turn.revision,
        )

    def to_domain_move(self, move: DbMove) -> Move:
        """Maps a database move to a domain move."""
        return Move(
            id=move.id,
            turn_id=move.turn_id,
            revision=move.revision,
            rack=Tileset.create(move.rack),
            board=Board.deserialize(move.board),
        )

    def to_db_gameroom(self, gameroom: Gameroom) -> DbGameroom:
        """Maps a domain gameroom to a database gameroom."""
        return DbGameroom(
            id=gameroom.id,
            name=gameroom.name,
            owner_id=gameroom.owner_id,
            status=gameroom.status,
            game=None if not gameroom.game else self.to_db_game(gameroom.game),
            users=[self.to_db_user(user=user) for user in gameroom.users],
            created_at=gameroom.created_at,
        )

    def to_db_user(self, user: User) -> DbUser:
        """Maps a domain user to a database user."""
        return DbUser(
            id=user.id, name=user.name, current_gameroom_id=user.current_gameroom_id
        )

    def to_db_user_token(self, user_token: UserToken) -> DbUserToken:
        """Maps a domain authentication token to a database authentication token."""
        return DbUserToken(
            id=user_token.id, token=user_token.token, user_id=user_token.user_id
        )

    def to_db_game(self, game: Game) -> DbGame:
        """Maps a domain game to a database game."""
        return DbGame(
            gameroom_id=game.gameroom_id,
            game_state=self.to_db_game_state(game_state=game.game_state),
            turn=self.to_db_turn(turn=game.turn),
            turn_order=tuple(str(user_id) for user_id in game.turn_order),
            id=game.id,
            winner=None
            if not game.winner
            else self.to_db_player(game.winner, game_state_id=game.game_state.id),
            winner_id=None if not game.winner else game.winner.id,
            made_meld=tuple(str(user_id) for user_id in game.made_meld),
        )

    def to_db_game_state(self, game_state: GameState) -> DbGameState:
        """Maps a domain game state to a database game state."""
        return DbGameState(
            id=game_state.id,
            game_id=game_state.game_id,
            players=[
                self.to_db_player(player, game_state_id=game_state.id)
                for player in game_state.players
            ],
            board=game_state.board.serialize(),
            pile=list(game_state.pile.tiles),
        )

    def to_db_player(self, player: Player, game_state_id: UUID) -> DbPlayer:
        """Maps a domain player of a game state with the given id to a database player."""
        return DbPlayer(
            id=player.id,
            user_id=player.user_id,
            name=player.name,
            rack=player.rack.as_list(),
            game_state_id=game_state_id,
        )

    def to_db_turn(self, turn: Turn) -> DbTurn:
        """Maps a domain turn to a database turn."""
        return DbTurn(
            id=turn.id,
            game_id=turn.game_id,
            player_id=turn.player_id,
            starting_rack=turn.starting_rack.as_list(),
            starting_board=turn.starting_board.serialize(),
            moves=[self.to_db_move(move) for move in turn.moves],
            revision=turn.revision,
        )

    def to_db_move(self, move: Move) -> DbMove:
        """Maps a domain move to a database move."""
        return DbMove(
            id=move.id,
            turn_id=move.turn_id,
            rack=move.rack.as_list(),
            board=move.board.serialize(),
            revision=move.revision,
        )
