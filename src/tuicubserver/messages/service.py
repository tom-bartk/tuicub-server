from __future__ import annotations

from typing import TYPE_CHECKING

from ..events.events import (
    BoardChangedEvent,
    GameroomDeletedEvent,
    GameStartedEvent,
    PileCountChangedEvent,
    PlayerLeftEvent,
    PlayersChangedEvent,
    PlayerWonEvent,
    RackChangedEvent,
    TileDrawnEvent,
    TurnEndedEvent,
    TurnStartedEvent,
    UserJoinedEvent,
    UserLeftEvent,
)
from ..models.game import Game
from ..models.gameroom import Gameroom
from ..models.user import User
from .client import MessagesClient
from .message import Message

if TYPE_CHECKING:
    from ..services.gamerooms import DisconnectResult
    from ..services.games import GameDisconnectResult


class MessagesService:
    """The service for creating and sending messages."""

    def __init__(self, client: MessagesClient):
        """Initialize new service.

        Args:
            client (MessagesClient): The client used for delivering messages.
        """
        self._client: MessagesClient = client

    def user_joined(self, sender: User, gameroom: Gameroom) -> None:
        """Send a `user_joined` event.

        Args:
            sender (User): The joining user.
            gameroom (Gameroom): The joined gameroom.
        """
        self._client.send(
            Message.from_event(UserJoinedEvent(user=sender, gameroom=gameroom))
        )

    def user_left(self, sender: User, gameroom: Gameroom) -> None:
        """Send a `user_left` event.

        Args:
            sender (User): The leaving user.
            gameroom (Gameroom): The left gameroom.
        """
        self._client.send(
            Message.from_event(UserLeftEvent(user=sender, gameroom=gameroom))
        )

    def gameroom_deleted(
        self, sender: User, gameroom: Gameroom, remaining_users: tuple[User, ...]
    ) -> None:
        """Send a `gameroom_deleted` event.

        Args:
            sender (User): The deleting user.
            gameroom (Gameroom): The deleted gameroom.
            remaining_users (tuple[User, ...]): The users that were in the gameroom
                not including the sender.
        """
        self._client.send(
            Message.from_event(GameroomDeletedEvent(gameroom, remaining_users))
        )

    def game_started(self, sender: User, game: Game) -> None:
        """Send a `game_started` event to all players but the sender.

        Args:
            sender (User): The starting user.
            game (Game): The started game.
        """
        players_without_sender = (
            p for p in game.game_state.players if p.user_id != sender.id
        )
        for player in players_without_sender:
            self._client.send(Message.from_event(GameStartedEvent(game, player)))

    def tiles_moved(self, sender: User, game: Game) -> None:
        """Send events after tiles are moved.

        Sends `board_changed` and `players_changed` to all players,
        and `rack_changed` to the sender.

        Args:
            sender (User): The sending player.
            game (Game): The game to send to.
        """
        self._client.send(
            Message.from_event(BoardChangedEvent(game)),
            Message.from_event(PlayersChangedEvent(game)),
            Message.from_event(RackChangedEvent(game, sender)),
        )

    def tile_drawn(self, sender: User, tile: int, game: Game) -> None:
        """Send events after drawing a tile.

        Sends `board_changed`, `pile_count_changed`, `players_changed` to all players,
        `tile_drawn`, `rack_changed` and `turn_ended` to the drawing player,
        and `turn_started` to the player after the sending player in the turn order.

        Args:
            sender (User): The drawing player.
            tile (int): The drawn tile.
            game (Game): The game to send to.
        """
        self._client.send(
            Message.from_event(BoardChangedEvent(game)),
            Message.from_event(PileCountChangedEvent(game)),
            Message.from_event(TileDrawnEvent(tile, sender)),
            Message.from_event(RackChangedEvent(game, sender)),
            Message.from_event(PlayersChangedEvent(game)),
            Message.from_event(TurnEndedEvent(sender)),
            Message.from_event(TurnStartedEvent(game)),
        )

    def turn_ended(self, sender: User, game: Game) -> None:
        """Send events after ending a turn.

        If the sender has an empty rack after ending the turn, the game is won, and
        the `player_won` event is sent to all players.

        Otherwise, sends `board_changed` and `players_changed` to all players,
        `turn_ended` to the sender, and `turn_started` to the player after the
        sending player in the turn order.

        Args:
            sender (User): The player ending the turn.
            game (Game): The game to send to.
        """
        if game.winner:
            self._client.send(Message.from_event(PlayerWonEvent(game.winner, game)))
        else:
            self._client.send(
                Message.from_event(BoardChangedEvent(game)),
                Message.from_event(PlayersChangedEvent(game)),
                Message.from_event(TurnEndedEvent(sender)),
                Message.from_event(TurnStartedEvent(game)),
            )

    def disconnected_game(self, sender: User, result: GameDisconnectResult) -> None:
        """Send events after a player has been disconnected.

        Always sends `player_left` and `players_changed` to the remaining players.

        If there is only one player left, the game is won, and the `player_won` event
        is sent to the remaining player.

        Otherwise, sends `pile_count_changed` due to the disconnected player's rack
        being shuffled back to the pile. If it was the disconnecting player turn,
        sends `board_changed` to all players, and `turn_started` to the player after
        the disconnected player in the turn order.

        Args:
            sender (User): The disconnected user.
            result (GameDisconnectResult): The result of the disconnection.
        """
        self._client.send(
            Message.from_event(PlayerLeftEvent(result.player, result.game)),
            Message.from_event(PlayersChangedEvent(result.game)),
        )

        if result.game.winner:
            self._client.send(
                Message.from_event(PlayerWonEvent(result.game.winner, result.game))
            )
        else:
            self._client.send(Message.from_event(PileCountChangedEvent(result.game)))
            if result.turn:
                self._client.send(
                    Message.from_event(BoardChangedEvent(result.game)),
                    Message.from_event(TurnStartedEvent(result.game)),
                )

    def disconnected_gameroom(self, sender: User, result: DisconnectResult) -> None:
        """Send events after a user has been disconnected.

        If the user was not in a gameroom, does not send any events.

        Otherwise, sends `gameroom_deleted`, if the user was an owner of the gameroom,
        or `user_left` if not.

        Args:
            sender (User): The disconnected user.
            result (DisconnectResult): The result of the disconnection.
        """
        if not result.gameroom:
            return

        if result.gameroom.owner_id == sender.id:
            self.gameroom_deleted(
                sender=sender,
                gameroom=result.gameroom,
                remaining_users=result.remaining_users,
            )
        else:
            self.user_left(sender=sender, gameroom=result.gameroom)

    def connect(self) -> None:
        """Connects to the messages server."""
        self._client.connect()
