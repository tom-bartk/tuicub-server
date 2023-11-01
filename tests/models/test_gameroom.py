from datetime import datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest

from src.tuicubserver.models.gameroom import (
    GameAlreadyStartedError,
    Gameroom,
    GameroomFullError,
    GameroomStatus,
    LeavingOwnGameroomError,
    NotGameroomOwnerError,
    UserNotInGameroomError,
)
from src.tuicubserver.models.user import AlreadyInGameroomError, User
from tests.utils import not_raises


class TestWithJoining:
    def test_when_already_has_four_users__raises_gameroom_full_error(self) -> None:
        user = User(id=uuid4(), name="foo", current_gameroom_id=None)
        sut = Gameroom(
            id=uuid4(),
            name="foo",
            owner_id=Mock(),
            users=(Mock(), Mock(), Mock(), Mock()),
            created_at=datetime.now(),
        )

        with pytest.raises(GameroomFullError):
            sut.with_joining(user)

    def test_when_does_not_have_starting_status__raises_gameroom_already_started_error(
        self,
    ) -> None:
        user = User(id=uuid4(), name="foo", current_gameroom_id=None)
        sut = Gameroom(
            id=uuid4(),
            name="foo",
            status=GameroomStatus.RUNNING,
            owner_id=Mock(),
            users=(Mock(), Mock(), Mock()),
            created_at=datetime.now(),
        )

        with pytest.raises(GameAlreadyStartedError):
            sut.with_joining(user)

    def test_when_user_already_in_gameroom__raises_already_in_gameroom_error(
        self,
    ) -> None:
        user = User(id=uuid4(), name="foo", current_gameroom_id=uuid4())
        sut = Gameroom(
            id=uuid4(),
            name="foo",
            owner_id=Mock(),
            users=(Mock(), Mock(), Mock()),
            created_at=datetime.now(),
        )

        with pytest.raises(AlreadyInGameroomError):
            sut.with_joining(user)

    def test_when_preconditions_ok__returns_gameroom_with_joined_user(
        self,
    ) -> None:
        user = User(id=uuid4(), name="foo", current_gameroom_id=None)
        sut = Gameroom(
            id=uuid4(),
            name="foo",
            owner_id=Mock(),
            users=(Mock(), Mock(), Mock()),
            created_at=datetime.now(),
        )
        expected = Gameroom(
            id=sut.id,
            name="foo",
            owner_id=sut.owner_id,
            users=(*sut.users, user),
            created_at=sut.created_at,
        )

        result = sut.with_joining(user)

        assert result == expected


class TestWithLeaving:
    def test_when_user_not_in_gameroom_raises_user_not_in_gameroom_error(self) -> None:
        user_1 = User(id=uuid4(), name="foo", current_gameroom_id=None)
        user_2 = User(id=uuid4(), name="bar", current_gameroom_id=None)
        sut = Gameroom(
            id=uuid4(),
            name="foo",
            owner_id=user_2.id,
            users=(user_2,),
            created_at=datetime.now(),
        )

        with pytest.raises(UserNotInGameroomError):
            sut.with_leaving(user_1)

    def test_when_does_not_have_starting_status__raises_gameroom_already_started_error(
        self,
    ) -> None:
        user_1 = User(id=uuid4(), name="foo", current_gameroom_id=None)
        user_2 = User(id=uuid4(), name="bar", current_gameroom_id=None)
        sut = Gameroom(
            id=uuid4(),
            name="foo",
            status=GameroomStatus.RUNNING,
            owner_id=user_2.id,
            users=(user_1, user_2),
            created_at=datetime.now(),
        )

        with pytest.raises(GameAlreadyStartedError):
            sut.with_leaving(user_1)

    def test_when_user_is_owner__raises_leaving_own_gameroom_error(self) -> None:
        user_1 = User(id=uuid4(), name="foo", current_gameroom_id=None)
        user_2 = User(id=uuid4(), name="bar", current_gameroom_id=None)
        sut = Gameroom(
            id=uuid4(),
            name="foo",
            owner_id=user_1.id,
            users=(user_1, user_2),
            created_at=datetime.now(),
        )

        with pytest.raises(LeavingOwnGameroomError):
            sut.with_leaving(user_1)

    def test_when_preconditions_ok__returns_gameroom_without_user(self) -> None:
        user_1 = User(id=uuid4(), name="foo", current_gameroom_id=None)
        user_2 = User(id=uuid4(), name="bar", current_gameroom_id=None)
        sut = Gameroom(
            id=uuid4(),
            name="foo",
            owner_id=user_2.id,
            users=(user_1, user_2),
            created_at=datetime.now(),
        )
        expected = Gameroom(
            id=sut.id,
            name="foo",
            owner_id=sut.owner_id,
            users=(user_2,),
            created_at=sut.created_at,
        )

        result = sut.with_leaving(user_1)

        assert result == expected


class TestWithStartedGame:
    def test_returns_gameroom_with_game_and_running_status(self) -> None:
        game = Mock()
        sut = Gameroom(
            id=uuid4(),
            name="foo",
            owner_id=Mock(),
            users=(),
            created_at=datetime.now(),
        )
        expected = Gameroom(
            id=sut.id,
            name="foo",
            owner_id=sut.owner_id,
            users=(),
            created_at=sut.created_at,
            status=GameroomStatus.RUNNING,
            game=game,
        )

        result = sut.with_started_game(game)

        assert result == expected


class TestWithoutGame:
    def test_returns_gameroom_with_game_eq_none(self) -> None:
        sut = Gameroom(
            id=uuid4(),
            name="foo",
            owner_id=Mock(),
            users=(),
            created_at=datetime.now(),
            game=Mock(),
        )
        expected = Gameroom(
            id=sut.id,
            name="foo",
            owner_id=sut.owner_id,
            users=(),
            created_at=sut.created_at,
            game=None,
        )

        result = sut.without_game()

        assert result == expected


class TestDeleted:
    def test_when_user_is_not_owner__raises_not_gameroom_owner_error(self) -> None:
        gameroom_id = uuid4()
        user = User(id=uuid4(), name="foo", current_gameroom_id=gameroom_id)
        sut = Gameroom(
            id=gameroom_id,
            name="foo",
            owner_id=uuid4(),
            users=(user,),
            created_at=datetime.now(),
        )

        with pytest.raises(NotGameroomOwnerError):
            sut.deleted(by=user)

    def test_when_does_not_have_starting_status__raises_gameroom_already_started_error(
        self,
    ) -> None:
        user_1 = User(id=uuid4(), name="foo", current_gameroom_id=None)
        user_2 = User(id=uuid4(), name="bar", current_gameroom_id=None)
        sut = Gameroom(
            id=uuid4(),
            name="foo",
            status=GameroomStatus.RUNNING,
            owner_id=user_1.id,
            users=(user_1, user_2),
            created_at=datetime.now(),
        )

        with pytest.raises(GameAlreadyStartedError):
            sut.deleted(by=user_1)

    def test_when_preconditions_ok__returns_gameroom_with_empty_users_and_deleted_status(
        self,
    ) -> None:
        user_id = uuid4()
        gameroom_id = uuid4()
        user = User(id=user_id, name="foo", current_gameroom_id=gameroom_id)
        sut = Gameroom(
            id=gameroom_id,
            name="foo",
            owner_id=user_id,
            status=GameroomStatus.STARTING,
            users=(user,),
            created_at=datetime.now(),
        )
        expected = Gameroom(
            id=gameroom_id,
            name="foo",
            owner_id=user_id,
            status=GameroomStatus.DELETED,
            users=(),
            created_at=sut.created_at,
        )

        result = sut.deleted(by=user)

        assert result == expected


class TestEnsureIsOwner:
    def test_when_user_is_not_owner__raises_not_gameroom_owner_error(self) -> None:
        gameroom_id = uuid4()
        user = User(id=uuid4(), name="foo", current_gameroom_id=gameroom_id)
        sut = Gameroom(
            id=gameroom_id,
            name="foo",
            owner_id=uuid4(),
            users=(user,),
            created_at=datetime.now(),
        )

        with pytest.raises(NotGameroomOwnerError):
            sut.ensure_is_owner(user)

    def test_when_user_is_owner__does_not_raise(self) -> None:
        gameroom_id = uuid4()
        user = User(id=uuid4(), name="foo", current_gameroom_id=gameroom_id)
        sut = Gameroom(
            id=gameroom_id,
            name="foo",
            owner_id=user.id,
            users=(user,),
            created_at=datetime.now(),
        )

        with not_raises(NotGameroomOwnerError):
            sut.ensure_is_owner(user)
