from uuid import UUID, uuid4

import pytest

from src.tuicubserver.models.db import (
    DbGame,
    DbGameroom,
    DbGameState,
    DbMove,
    DbPlayer,
    DbTurn,
    DbUser,
    DbUserToken,
)
from src.tuicubserver.models.game import (
    Board,
    Game,
    GameState,
    Move,
    Pile,
    Tileset,
    Turn,
)
from src.tuicubserver.models.gameroom import Gameroom, GameroomStatus
from src.tuicubserver.models.mapper import Mapper
from src.tuicubserver.models.user import User, UserToken


@pytest.fixture()
def user_token_id() -> UUID:
    return uuid4()


@pytest.fixture()
def sut() -> Mapper:
    return Mapper()


@pytest.fixture()
def db_user_1(user_id_1, gameroom_id) -> DbUser:
    return DbUser(id=user_id_1, name="foo", current_gameroom_id=gameroom_id)


@pytest.fixture()
def db_user_2(user_id_2, gameroom_id) -> DbUser:
    return DbUser(id=user_id_2, name="bar", current_gameroom_id=gameroom_id)


@pytest.fixture()
def db_user_token(user_token_id, user_id_1) -> DbUserToken:
    return DbUserToken(id=user_token_id, token="baz", user_id=user_id_1)


@pytest.fixture()
def db_player_1(player_id_1, user_id_1, game_state_id) -> DbPlayer:
    return DbPlayer(
        id=player_id_1,
        name="foo",
        rack=[7, 8, 9],
        user_id=user_id_1,
        game_state_id=game_state_id,
    )


@pytest.fixture()
def db_player_2(player_id_2, user_id_2, game_state_id) -> DbPlayer:
    return DbPlayer(
        id=player_id_2,
        name="bar",
        rack=[10, 11, 12],
        user_id=user_id_2,
        game_state_id=game_state_id,
    )


@pytest.fixture()
def db_move_1(move_id_1, turn_id) -> DbMove:
    return DbMove(
        id=move_id_1,
        revision=1,
        board=["[1, 2, 3]"],
        rack=[4, 5, 6],
        turn_id=turn_id,
    )


@pytest.fixture()
def db_move_2(move_id_2, turn_id) -> DbMove:
    return DbMove(
        id=move_id_2,
        revision=2,
        board=["[4, 5, 6]"],
        rack=[6, 7, 8],
        turn_id=turn_id,
    )


@pytest.fixture()
def db_turn(turn_id, player_id_1, game_id, db_move_1, db_move_2) -> DbTurn:
    return DbTurn(
        id=turn_id,
        revision=42,
        starting_board=["[1, 2, 3]", "[4, 5, 6]"],
        starting_rack=[6, 7, 8],
        player_id=player_id_1,
        game_id=game_id,
        moves=[db_move_1, db_move_2],
    )


@pytest.fixture()
def db_game_state(game_state_id, game_id, db_player_1, db_player_2) -> DbGameState:
    return DbGameState(
        id=game_state_id,
        game_id=game_id,
        players=[db_player_1, db_player_2],
        board=["[1, 2, 3]", "[4, 5, 6]"],
        pile=[7, 8, 9],
    )


@pytest.fixture()
def db_game(
    game_id, game_state_id, db_game_state, db_turn, player_id_1, player_id_2, gameroom_id
) -> DbGame:
    return DbGame(
        id=game_id,
        gameroom_id=gameroom_id,
        game_state=db_game_state,
        turn=db_turn,
        turn_order=(str(player_id_1), str(player_id_2)),
        winner=None,
        winner_id=None,
        made_meld=(str(player_id_1),),
    )


@pytest.fixture()
def db_gameroom(
    created_at,
    gameroom_id,
    user_id_1,
    db_game,
    db_user_1,
    db_user_2,
) -> DbGameroom:
    return DbGameroom(
        id=gameroom_id,
        name="foobar",
        owner_id=user_id_1,
        status=GameroomStatus.RUNNING,
        game=db_game,
        users=[db_user_1, db_user_2],
        created_at=created_at,
    )


@pytest.fixture()
def user_1(user_id_1, gameroom_id) -> User:
    return User(id=user_id_1, name="foo", current_gameroom_id=gameroom_id)


@pytest.fixture()
def user_2(user_id_2, gameroom_id) -> User:
    return User(id=user_id_2, name="bar", current_gameroom_id=gameroom_id)


@pytest.fixture()
def user_token(user_token_id, user_id_1) -> UserToken:
    return UserToken(id=user_token_id, token="baz", user_id=user_id_1)


@pytest.fixture()
def move_1(move_id_1, turn_id) -> Move:
    return Move(
        id=move_id_1,
        revision=1,
        rack=Tileset.create([4, 5, 6]),
        board=Board.create([[1, 2, 3]]),
        turn_id=turn_id,
    )


@pytest.fixture()
def move_2(move_id_2, turn_id) -> Move:
    return Move(
        id=move_id_2,
        revision=2,
        rack=Tileset.create([6, 7, 8]),
        board=Board.create([[4, 5, 6]]),
        turn_id=turn_id,
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
def game_state(game_state_id, game_id, player_1, player_2) -> GameState:
    return GameState(
        id=game_state_id,
        game_id=game_id,
        players=(player_1, player_2),
        board=Board.create([[1, 2, 3], [4, 5, 6]]),
        pile=Pile([7, 8, 9]),
    )


@pytest.fixture()
def game(
    game_id, game_state_id, game_state, turn, player_id_1, player_id_2, gameroom_id
) -> Game:
    return Game(
        id=game_id,
        gameroom_id=gameroom_id,
        game_state=game_state,
        turn=turn,
        turn_order=(player_id_1, player_id_2),
        winner=None,
        made_meld=(player_id_1,),
    )


@pytest.fixture()
def gameroom(
    created_at,
    gameroom_id,
    game_state_id,
    game_state,
    user_id_1,
    game,
    user_1,
    user_2,
) -> Gameroom:
    return Gameroom(
        id=gameroom_id,
        name="foobar",
        owner_id=user_id_1,
        status=GameroomStatus.RUNNING,
        game=game,
        users=(user_1, user_2),
        created_at=created_at,
    )


class TestMapper:
    def test_map_db_player__returns_mapped_player(
        self, sut, player_1, db_player_1
    ) -> None:
        result = sut.to_domain_player(db_player_1)

        assert result == player_1

    def test_map_db_turn__returns_mapped_turn(self, sut, turn, db_turn) -> None:
        result = sut.to_domain_turn(db_turn)

        assert result == turn

    def test_map_db_move__returns_mapped_move(self, sut, move_1, db_move_1) -> None:
        result = sut.to_domain_move(db_move_1)

        assert result == move_1

    def test_map_db_game_state__returns_mapped_game_state(
        self, sut, game_state, db_game_state
    ) -> None:
        result = sut.to_domain_game_state(db_game_state)

        assert result == game_state

    def test_map_db_game__returns_mapped_game(self, sut, game, db_game) -> None:
        result = sut.to_domain_game(db_game)

        assert result == game

    def test_map_db_gameroom__returns_mapped_gameroom(
        self, sut, gameroom, db_gameroom
    ) -> None:
        result = sut.to_domain_gameroom(db_gameroom)

        assert result == gameroom

    def test_map_db_user__returns_mapped_user(self, sut, user_1, db_user_1) -> None:
        result = sut.to_domain_user(db_user_1)

        assert result == user_1

    def test_map_db_user_token__returns_mapped_user_token(
        self, sut, user_token, db_user_token
    ) -> None:
        result = sut.to_domain_user_token(db_user_token)

        assert result == user_token

    def test_map_player__returns_mapped_db_player(
        self, sut, player_1, db_player_1, game_state_id
    ) -> None:
        result = sut.to_db_player(player_1, game_state_id=game_state_id)

        assert result == db_player_1

    def test_map_turn__returns_mapped_db_turn(self, sut, turn, db_turn) -> None:
        result = sut.to_db_turn(turn)

        assert result == db_turn

    def test_map_move__returns_mapped_db_move(self, sut, move_1, db_move_1) -> None:
        result = sut.to_db_move(move_1)

        assert result == db_move_1

    def test_map_game_state__returns_mapped_db_game_state(
        self, sut, game_state, db_game_state
    ) -> None:
        result = sut.to_db_game_state(game_state)

        assert result == db_game_state

    def test_map_game__returns_mapped_db_game(self, sut, game, db_game) -> None:
        result = sut.to_db_game(game)

        assert result == db_game

    def test_map_gameroom__returns_mapped_db_gameroom(
        self, sut, gameroom, db_gameroom
    ) -> None:
        result = sut.to_db_gameroom(gameroom)

        assert result == db_gameroom

    def test_map_user__returns_mapped_db_user(self, sut, user_1, db_user_1) -> None:
        result = sut.to_db_user(user_1)

        assert result == db_user_1

    def test_map_user_token__returns_mapped_db_user_token(
        self, sut, user_token, db_user_token
    ) -> None:
        result = sut.to_db_user_token(user_token)

        assert result == db_user_token
