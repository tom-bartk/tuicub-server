import asyncio
from collections.abc import Callable
from datetime import datetime
from typing import ParamSpec, TypeVar
from unittest.mock import Mock, PropertyMock, create_autospec
from uuid import UUID, uuid4

import pytest
from flask import Flask
from sqlalchemy.orm import Session, sessionmaker

from src.tuicubserver.common.context import BaseContext, Context
from src.tuicubserver.common.logger import Logger
from src.tuicubserver.messages.service import MessagesService
from src.tuicubserver.models.game import (
    Board,
    Game,
    GameState,
    Move,
    Pile,
    Player,
    Tileset,
    Turn,
)
from src.tuicubserver.models.gameroom import Gameroom, GameroomStatus
from src.tuicubserver.models.mapper import Mapper
from src.tuicubserver.models.user import User, UserToken
from src.tuicubserver.repositories.gamerooms import GameroomsRepository
from src.tuicubserver.repositories.games import GamesRepository
from src.tuicubserver.repositories.users import UsersRepository
from src.tuicubserver.services import Services
from src.tuicubserver.services.auth import AuthService
from src.tuicubserver.services.game_toolkit import GameToolkit
from src.tuicubserver.services.gamerooms import GameroomsService
from src.tuicubserver.services.games import GamesService
from src.tuicubserver.services.rng import RngService
from src.tuicubserver.services.tilesets import TilesetsService
from src.tuicubserver.services.users import UsersService

P = ParamSpec("P")
T = TypeVar("T")


@pytest.fixture()
def app() -> Flask:
    app = Flask(__name__)
    app.config.update({"TESTING": True})
    app.testing = True
    return app


@pytest.fixture()
def flask_client(app):
    app.testing = True
    return app.test_client()


@pytest.fixture()
def logger() -> Logger:
    return create_autospec(Logger)


@pytest.fixture()
def with_base_context(
    session_factory, logger
) -> Callable[
    [Callable[[BaseContext, P.args, P.kwargs], T]], Callable[[P.args, P.kwargs], T]
]:
    return BaseContext.base_decorator(session_factory, logger)


@pytest.fixture()
def with_context(
    services, session_factory, logger
) -> Callable[
    [Callable[[Context, P.args, P.kwargs], T]], Callable[[P.args, P.kwargs], T]
]:
    return Context.decorator(services, session_factory, logger)


@pytest.fixture()
def gameroom_id() -> UUID:
    return uuid4()


@pytest.fixture()
def loop() -> asyncio.AbstractEventLoop:
    return create_autospec(asyncio.AbstractEventLoop)


@pytest.fixture()
def user_id() -> UUID:
    return uuid4()


@pytest.fixture()
def session_factory(session) -> sessionmaker:
    session_factory = create_autospec(sessionmaker)

    _context_manager = Mock()
    _context_manager.__enter__ = Mock(return_value=session)
    _context_manager.__exit__ = Mock()

    session_factory.return_value = _context_manager
    return session_factory


@pytest.fixture()
def user_no_gameroom(user_id: UUID) -> User:
    return User(id=user_id, name="John", current_gameroom_id=None)


@pytest.fixture()
def user_token(user_id: UUID) -> UserToken:
    return UserToken(id=uuid4(), token="t0k3n", user_id=user_id)


@pytest.fixture()
def user(user_id: UUID, gameroom_id: UUID) -> User:
    return User(id=user_id, name="John", current_gameroom_id=gameroom_id)


@pytest.fixture()
def services(
    auth_service, games_service, gamerooms_service, users_service, messages_service
) -> Services:
    services = create_autospec(Services)
    type(services).auth = PropertyMock(return_value=auth_service)
    type(services).games = PropertyMock(return_value=games_service)
    type(services).gamerooms = PropertyMock(return_value=gamerooms_service)
    type(services).users = PropertyMock(return_value=users_service)
    type(services).messages = PropertyMock(return_value=messages_service)
    return services


@pytest.fixture()
def users_service() -> UsersService:
    return create_autospec(UsersService)


@pytest.fixture()
def gamerooms_service() -> GameroomsService:
    return create_autospec(GameroomsService)


@pytest.fixture()
def games_service() -> GamesService:
    return create_autospec(GamesService)


@pytest.fixture()
def auth_service() -> AuthService:
    return create_autospec(AuthService)


@pytest.fixture()
def tileset_service() -> TilesetsService:
    return create_autospec(TilesetsService)


@pytest.fixture()
def game_toolkit() -> GameToolkit:
    return create_autospec(GameToolkit)


@pytest.fixture()
def messages_service() -> MessagesService:
    return create_autospec(MessagesService)


@pytest.fixture()
def rng_service() -> RngService:
    service = create_autospec(RngService)

    def pick(seq):
        return seq[0]

    service.pick = Mock(side_effect=pick)

    def shuffle(seq):
        return seq

    service.shuffle = Mock(side_effect=shuffle)
    return service


@pytest.fixture()
def users_repository() -> UsersRepository:
    return create_autospec(UsersRepository)


@pytest.fixture()
def games_repository() -> GamesRepository:
    def save_game(session, game):
        return game

    repository = create_autospec(GamesRepository)
    repository.save_game = Mock(side_effect=save_game)
    return repository


@pytest.fixture()
def gamerooms_repository() -> GameroomsRepository:
    def save_gameroom(session, gameroom):
        return gameroom

    repository = create_autospec(GameroomsRepository)
    repository.save_gameroom = Mock(side_effect=save_gameroom)
    return repository


@pytest.fixture()
def session() -> Session:
    return create_autospec(Session)


@pytest.fixture()
def create_context(session: Session) -> Callable[[User], Context]:
    def factory(user: User) -> Context:
        return Context(user=user, session=session)

    return factory


@pytest.fixture()
def context() -> Context:
    return create_autospec(Context)


@pytest.fixture()
def base_context(session: Session) -> BaseContext:
    return BaseContext(session=session)


@pytest.fixture()
def gameroom(user: User, gameroom_id: UUID) -> Gameroom:
    return Gameroom(
        id=gameroom_id,
        name="foo",
        owner_id=user.id,
        users=(user,),
        status=GameroomStatus.STARTING,
        game=None,
        created_at=datetime.fromtimestamp(1697480719),
    )


@pytest.fixture()
def game_state() -> GameState:
    return GameState(
        id=uuid4(), game_id=uuid4(), players=(), board=Board(), pile=Pile(tiles=[])
    )


@pytest.fixture()
def game(game_state: GameState, gameroom_id: UUID, user: User) -> Game:
    return Game(
        id=uuid4(),
        gameroom_id=gameroom_id,
        game_state=game_state,
        turn=Turn(
            id=uuid4(),
            game_id=uuid4(),
            player_id=user.id,
            starting_rack=Tileset(tiles=()),
            starting_board=Board(),
        ),
        turn_order=(),
        made_meld=(),
        winner=None,
    )


@pytest.fixture()
def mapper() -> Mapper:
    return create_autospec(Mapper)


@pytest.fixture()
def created_at() -> datetime:
    return datetime.now()


@pytest.fixture()
def user_id_1() -> UUID:
    return uuid4()


@pytest.fixture()
def user_id_2() -> UUID:
    return uuid4()


@pytest.fixture()
def user_id_3() -> UUID:
    return uuid4()


@pytest.fixture()
def game_id() -> UUID:
    return uuid4()


@pytest.fixture()
def game_state_id() -> UUID:
    return uuid4()


@pytest.fixture()
def turn_id() -> UUID:
    return uuid4()


@pytest.fixture()
def player_id_1() -> UUID:
    return uuid4()


@pytest.fixture()
def player_id_2() -> UUID:
    return uuid4()


@pytest.fixture()
def player_id_3() -> UUID:
    return uuid4()


@pytest.fixture()
def move_id_1() -> UUID:
    return uuid4()


@pytest.fixture()
def move_id_2() -> UUID:
    return uuid4()


@pytest.fixture()
def move_id_3() -> UUID:
    return uuid4()


@pytest.fixture()
def player_1(player_id_1, user_id_1, game_state_id) -> Player:
    return Player(
        id=player_id_1,
        name="foo",
        rack=Tileset.create([7, 8, 9]),
        user_id=user_id_1,
    )


@pytest.fixture()
def player_2(player_id_2, user_id_2, game_state_id) -> Player:
    return Player(
        id=player_id_2,
        name="bar",
        rack=Tileset.create([10, 11, 12]),
        user_id=user_id_2,
    )


@pytest.fixture()
def player_3(player_id_3, user_id_3, game_state_id) -> Player:
    return Player(
        id=player_id_3,
        name="baz",
        rack=Tileset.create([13, 14, 15]),
        user_id=user_id_3,
    )


@pytest.fixture()
def move_1(move_id_1, turn_id) -> Move:
    return Move(
        id=move_id_1,
        revision=1,
        rack=Tileset.create([7, 8, 9, 10, 11, 12]),
        board=Board.create([[1, 2, 3], [4, 5, 6]]),
        turn_id=turn_id,
    )


@pytest.fixture()
def move_2(move_id_2, turn_id) -> Move:
    return Move(
        id=move_id_2,
        revision=2,
        rack=Tileset.create([10, 11, 12]),
        board=Board.create([[1, 2, 3], [4, 5, 6], [7, 8, 9]]),
        turn_id=turn_id,
    )


@pytest.fixture()
def move_3(move_id_3, turn_id) -> Move:
    return Move(
        id=move_id_3,
        revision=3,
        rack=Tileset.create([12]),
        board=Board.create([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11]]),
        turn_id=turn_id,
    )


@pytest.fixture()
def user_1(user_id_1, gameroom_id) -> User:
    return User(id=user_id_1, name="foo", current_gameroom_id=gameroom_id)


@pytest.fixture()
def user_2(user_id_2, gameroom_id) -> User:
    return User(id=user_id_2, name="bar", current_gameroom_id=gameroom_id)
