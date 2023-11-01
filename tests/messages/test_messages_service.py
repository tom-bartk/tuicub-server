from unittest.mock import call, create_autospec

import pytest

from src.tuicubserver.events.events import (
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
from src.tuicubserver.messages.client import MessagesClient
from src.tuicubserver.messages.message import Message
from src.tuicubserver.messages.service import MessagesService
from src.tuicubserver.models.game import Board, Game, GameState, Pile, Tileset, Turn
from src.tuicubserver.models.gameroom import Gameroom, GameroomStatus
from src.tuicubserver.services.gamerooms import DisconnectResult
from src.tuicubserver.services.games import GameDisconnectResult


@pytest.fixture()
def messages_client() -> MessagesClient:
    return create_autospec(MessagesClient)


@pytest.fixture()
def sut(messages_client) -> MessagesService:
    return MessagesService(client=messages_client)


@pytest.fixture()
def gameroom(gameroom_id, user_1, user_2, user_id_1, created_at) -> Gameroom:
    return Gameroom(
        id=gameroom_id,
        name="foobar",
        owner_id=user_id_1,
        status=GameroomStatus.RUNNING,
        game=None,
        users=(user_1, user_2),
        created_at=created_at,
    )


@pytest.fixture()
def turn(turn_id, player_id_1, game_id, move_1, move_2) -> Turn:
    return Turn(
        id=turn_id,
        revision=42,
        starting_rack=Tileset.create([6, 7, 8]),
        starting_board=Board.create([[1, 2, 3], [4, 5, 6]]),
        player_id=player_id_1,
        game_id=game_id,
        moves=(move_1, move_2),
    )


@pytest.fixture()
def game_state(game_state_id, game_id, player_1, player_2, player_3) -> GameState:
    return GameState(
        id=game_state_id,
        game_id=game_id,
        players=(player_1, player_2, player_3),
        board=Board.create([[1, 2, 3], [4, 5, 6]]),
        pile=Pile([7, 8, 9]),
    )


@pytest.fixture()
def game(
    game_id,
    game_state_id,
    game_state,
    turn,
    user_id_1,
    user_id_2,
    user_id_3,
    gameroom_id,
) -> Game:
    return Game(
        id=game_id,
        gameroom_id=gameroom_id,
        game_state=game_state,
        turn=turn,
        turn_order=(user_id_1, user_id_2, user_id_3),
        winner=None,
        made_meld=(user_id_1,),
    )


@pytest.fixture()
def won_game(
    game_id,
    game_state_id,
    game_state,
    turn,
    player_1,
    user_id_1,
    user_id_2,
    user_id_3,
    gameroom_id,
) -> Game:
    return Game(
        id=game_id,
        gameroom_id=gameroom_id,
        game_state=game_state,
        turn=turn,
        turn_order=(user_id_1, user_id_2, user_id_3),
        winner=player_1,
        made_meld=(user_id_1,),
    )


class TestUserJoined:
    def test_sends_user_joined_event(self, sut, messages_client, user, gameroom) -> None:
        expected = Message.from_event(UserJoinedEvent(user, gameroom))

        sut.user_joined(sender=user, gameroom=gameroom)

        messages_client.send.assert_called_once_with(expected)


class TestUserLeft:
    def test_sends_user_joined_event(self, sut, messages_client, user, gameroom) -> None:
        expected = Message.from_event(UserLeftEvent(user, gameroom))

        sut.user_left(sender=user, gameroom=gameroom)

        messages_client.send.assert_called_once_with(expected)


class TestGameroomDeleted:
    def test_sends_gameroom_deleted_event(
        self, sut, messages_client, gameroom, user_1, user_2
    ) -> None:
        expected = Message.from_event(
            GameroomDeletedEvent(gameroom=gameroom, remaining_users=(user_2,))
        )

        sut.gameroom_deleted(sender=user_1, gameroom=gameroom, remaining_users=(user_2,))

        messages_client.send.assert_called_once_with(expected)


class TestGameStarted:
    def test_sends_gameroom_deleted_event_to_all_players_but_sender(
        self, sut, messages_client, game, user_1, player_1, player_2, player_3
    ) -> None:
        expected_calls = [
            call(Message.from_event(GameStartedEvent(game, player_2))),
            call(Message.from_event(GameStartedEvent(game, player_3))),
        ]

        sut.game_started(sender=user_1, game=game)

        messages_client.send.assert_has_calls(expected_calls)


class TestTilesMoved:
    def test_sends_board_changed__players_changed__rack_changed_events(
        self, sut, messages_client, game, user_1
    ) -> None:
        expected = (
            Message.from_event(BoardChangedEvent(game)),
            Message.from_event(PlayersChangedEvent(game)),
            Message.from_event(RackChangedEvent(game, user_1)),
        )

        sut.tiles_moved(sender=user_1, game=game)

        messages_client.send.assert_called_once_with(*expected)


class TestTileDrawn:
    def test_sends_correct_messages(self, sut, messages_client, game, user_1) -> None:
        expected = (
            Message.from_event(BoardChangedEvent(game)),
            Message.from_event(PileCountChangedEvent(game)),
            Message.from_event(TileDrawnEvent(42, user_1)),
            Message.from_event(RackChangedEvent(game, user_1)),
            Message.from_event(PlayersChangedEvent(game)),
            Message.from_event(TurnEndedEvent(user_1)),
            Message.from_event(TurnStartedEvent(game)),
        )

        sut.tile_drawn(sender=user_1, tile=42, game=game)

        messages_client.send.assert_called_once_with(*expected)


class TestTurnEnded:
    def test_when_game_has_no_winner__sends_correct_messages(
        self, sut, messages_client, game, user_1
    ) -> None:
        expected = (
            Message.from_event(BoardChangedEvent(game)),
            Message.from_event(PlayersChangedEvent(game)),
            Message.from_event(TurnEndedEvent(user_1)),
            Message.from_event(TurnStartedEvent(game)),
        )

        sut.turn_ended(sender=user_1, game=game)

        messages_client.send.assert_called_once_with(*expected)

    def test_when_game_has_winner__sends_player_won_message(
        self, sut, messages_client, won_game, player_1, user_1
    ) -> None:
        expected = Message.from_event(PlayerWonEvent(player_1, won_game))

        sut.turn_ended(sender=user_1, game=won_game)

        messages_client.send.assert_called_once_with(expected)


class TestDisconnectedGame:
    def test_when_game_has_no_winner__no_new_turn__sends_correct_messages(
        self, sut, messages_client, game, user_1, player_1
    ) -> None:
        result = GameDisconnectResult(game=game, player=player_1, turn=None)
        expected_calls = [
            call(
                Message.from_event(PlayerLeftEvent(result.player, result.game)),
                Message.from_event(PlayersChangedEvent(result.game)),
            ),
            call(Message.from_event(PileCountChangedEvent(result.game))),
        ]

        sut.disconnected_game(sender=user_1, result=result)

        messages_client.send.assert_has_calls(expected_calls)

    def test_when_game_has_no_winner__has_new_turn__sends_correct_messages(
        self, sut, messages_client, game, user_1, player_1, turn
    ) -> None:
        result = GameDisconnectResult(game=game, player=player_1, turn=turn)
        expected_calls = [
            call(
                Message.from_event(PlayerLeftEvent(result.player, result.game)),
                Message.from_event(PlayersChangedEvent(result.game)),
            ),
            call(Message.from_event(PileCountChangedEvent(result.game))),
            call(
                Message.from_event(BoardChangedEvent(result.game)),
                Message.from_event(TurnStartedEvent(result.game)),
            ),
        ]

        sut.disconnected_game(sender=user_1, result=result)

        messages_client.send.assert_has_calls(expected_calls)

    def test_when_game_has_winner__sends_correct_messages(
        self, sut, messages_client, won_game, player_1, user_1
    ) -> None:
        result = GameDisconnectResult(game=won_game, player=player_1, turn=None)
        expected_calls = [
            call(
                Message.from_event(PlayerLeftEvent(result.player, result.game)),
                Message.from_event(PlayersChangedEvent(result.game)),
            ),
            call(Message.from_event(PlayerWonEvent(player_1, won_game))),
        ]

        sut.disconnected_game(sender=user_1, result=result)

        messages_client.send.assert_has_calls(expected_calls)


class TestDisconnectedGameroom:
    def test_when_result_has_no_gameroom__does_not_send_messages(
        self, sut, messages_client, user_1
    ) -> None:
        result = DisconnectResult(gameroom=None)

        sut.disconnected_gameroom(sender=user_1, result=result)

        messages_client.send.assert_not_called()

    def test_when_result_has_gameroom__sender_is_owner__sends_gameroom_deleted_message(
        self, sut, messages_client, gameroom, user_1
    ) -> None:
        result = DisconnectResult(gameroom=gameroom)
        expected = Message.from_event(
            GameroomDeletedEvent(
                gameroom=gameroom, remaining_users=result.remaining_users
            )
        )

        sut.disconnected_gameroom(sender=user_1, result=result)

        messages_client.send.assert_called_once_with(expected)

    def test_when_result_has_gameroom__sender_is_not_owner__sends_user_left_message(
        self, sut, messages_client, gameroom, user_2
    ) -> None:
        result = DisconnectResult(gameroom=gameroom)
        expected = Message.from_event(UserLeftEvent(user_2, gameroom))

        sut.disconnected_gameroom(sender=user_2, result=result)

        messages_client.send.assert_called_once_with(expected)


class TestConnect:
    def test_connects_client(self, sut, messages_client) -> None:
        sut.connect()

        messages_client.connect.assert_called_once()
