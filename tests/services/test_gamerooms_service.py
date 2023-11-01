from unittest.mock import Mock, create_autospec, patch
from uuid import uuid4

import pytest

from src.tuicubserver.common import utils
from src.tuicubserver.common.context import Context
from src.tuicubserver.common.errors import NotFoundError
from src.tuicubserver.models.gameroom import Gameroom, NotGameroomOwnerError
from src.tuicubserver.models.user import User
from src.tuicubserver.services.gamerooms import (
    DeleteGameroomResult,
    DisconnectResult,
    GameroomsService,
)


@pytest.fixture()
def gameroom() -> Gameroom:
    return create_autospec(Gameroom)


@pytest.fixture()
def sut(
    games_service, gamerooms_repository, games_repository, game_toolkit
) -> GameroomsService:
    return GameroomsService(
        gamerooms_repository=gamerooms_repository,
        game_toolkit=game_toolkit,
        games_repository=games_repository,
        games_service=games_service,
    )


class TestGetGamerooms:
    def test_returns_gamerooms(self, sut, context, gamerooms_repository) -> None:
        expected = [Mock(), Mock()]
        gamerooms_repository.get_gamerooms = Mock(return_value=expected)

        result = sut.get_gamerooms(context)

        assert result == expected


class TestCreateGameroom:
    def test_returns_created_gamerooms(self, sut, context, gamerooms_repository) -> None:
        expected = Gameroom.create(user=context.user)
        gamerooms_repository.save_gameroom = Mock(return_value=expected)

        result = sut.create_gameroom(context)

        assert result == expected

    def test_saves_created_gameroom_to_repository(
        self, sut, context, gamerooms_repository
    ) -> None:
        with patch("uuid.uuid4", return_value=Mock()), patch.object(
            utils, "timestamp", return_value=Mock()
        ):
            expected = Gameroom.create(user=context.user)
            gamerooms_repository.save_gameroom = Mock(return_value=expected)

            sut.create_gameroom(context)

            gamerooms_repository.save_gameroom.assert_called_once_with(
                session=context.session, gameroom=expected
            )


class TestJoinGameroom:
    def test_returns_saved_gameroom_after_joining(
        self, sut, context, gamerooms_repository
    ) -> None:
        expected = Mock()
        gamerooms_repository.get_gameroom_by_id = Mock(return_value=Mock())
        gamerooms_repository.save_gameroom = Mock(return_value=expected)

        result = sut.join_gameroom(context, gameroom_id="foo")

        assert result == expected

    def test_saves_gameroom_with_joined_user_to_repository(
        self, sut, context, gamerooms_repository, gameroom
    ) -> None:
        expected = Mock()
        gamerooms_repository.get_gameroom_by_id = Mock(return_value=gameroom)
        gameroom.with_joining = Mock(return_value=expected)

        sut.join_gameroom(context, gameroom_id="foo")

        gamerooms_repository.save_gameroom.assert_called_once_with(
            session=context.session, gameroom=expected
        )


class TestLeaveGameroom:
    def test_returns_saved_gameroom_after_leaving(
        self, sut, context, gamerooms_repository, gameroom
    ) -> None:
        expected = Mock()
        gamerooms_repository.get_gameroom_by_id = Mock(return_value=gameroom)
        gameroom.with_leaving = Mock(return_value=expected)

        result = sut.leave_gameroom(context, gameroom_id="foo")

        assert result == expected

    def test_saves_gameroom_without_leaving_user_to_repository(
        self, sut, context, gamerooms_repository, gameroom
    ) -> None:
        expected = Mock()
        gamerooms_repository.get_gameroom_by_id = Mock(return_value=gameroom)
        gameroom.with_leaving = Mock(return_value=expected)

        sut.leave_gameroom(context, gameroom_id="foo")

        gamerooms_repository.save_gameroom.assert_called_once_with(
            session=context.session, gameroom=expected
        )


class TestDeleteGameroom:
    def test_returns_delete_result(
        self, sut, context, gamerooms_repository, gameroom
    ) -> None:
        expected = DeleteGameroomResult(gameroom=gameroom, remaining_users=())
        gamerooms_repository.get_gameroom_by_id = Mock(return_value=gameroom)
        gamerooms_repository.save_gameroom = Mock(return_value=gameroom)

        result = sut.delete_gameroom(context, gameroom_id="foo")

        assert result == expected

    def test_saves_deleted_gameroom_to_repository(
        self, sut, context, gamerooms_repository, gameroom
    ) -> None:
        expected = Mock()
        gamerooms_repository.get_gameroom_by_id = Mock(return_value=gameroom)
        gameroom.deleted = Mock(return_value=expected)

        sut.delete_gameroom(context, gameroom_id="foo")

        gamerooms_repository.save_gameroom.assert_called_once_with(
            session=context.session, gameroom=expected
        )


class TestDisconnect:
    @pytest.fixture()
    def user(self, user_id, gameroom_id) -> User:
        return User(name="foo", id=user_id, current_gameroom_id=gameroom_id)

    @pytest.fixture()
    def context(self, session, user) -> Context:
        return Context(session=session, user=user)

    def test_when_user_has_no_current_gameroom__result_has_no_gameroom(
        self, sut, session, gameroom, user_id
    ) -> None:
        context = Context(
            session=session, user=User(name="foo", id=user_id, current_gameroom_id=None)
        )
        expected = DisconnectResult(gameroom=None)

        result = sut.disconnect(context)

        assert result == expected

    def test_when_user_has_nonexisting_current_gameroom__result_has_no_gameroom(
        self, sut, context, gamerooms_repository, gameroom, user, gameroom_id
    ) -> None:
        expected = DisconnectResult(gameroom=None)
        gamerooms_repository.get_gameroom_by_id = Mock(side_effect=NotFoundError)

        result = sut.disconnect(context)

        assert result == expected

    def test_when_user_not_owner__has_current_gameroom_w_running_game__does_not_leave(
        self, sut, context, gamerooms_repository, gameroom, user, user_id_2, gameroom_id
    ) -> None:
        gameroom = Gameroom(
            id=gameroom_id, name="bar", owner_id=user_id_2, users=(user,), game=Mock()
        )
        gamerooms_repository.get_gameroom_by_id = Mock(return_value=gameroom)

        sut.disconnect(context)

        gamerooms_repository.save_gameroom.assert_not_called()

    def test_when_user_is_owner__has_current_gameroom_w_running_game__does_not_delete_gameroom(  # noqa: E501
        self, sut, context, gamerooms_repository, gameroom, user, gameroom_id
    ) -> None:
        gameroom = Gameroom(
            id=gameroom_id, name="bar", owner_id=user.id, users=(user,), game=Mock()
        )
        gamerooms_repository.get_gameroom_by_id = Mock(return_value=gameroom)

        sut.disconnect(context)

        gamerooms_repository.save_gameroom.assert_not_called()

    def test_when_user_is_owner_of_current_gameroom__returns_result_of_deleting_gameroom(
        self, sut, context, gamerooms_repository, gameroom, user, gameroom_id
    ) -> None:
        gameroom = Gameroom(id=gameroom_id, name="bar", owner_id=user.id, users=(user,))
        gamerooms_repository.get_gameroom_by_id = Mock(return_value=gameroom)
        expected = DisconnectResult(
            gameroom=gameroom.deleted(by=user), remaining_users=()
        )

        result = sut.disconnect(context)

        assert result == expected

    def test_when_user_is_not_owner_of_current_gameroom__returns_result_of_leaving_gameroom(  # noqa: E501
        self, sut, context, gamerooms_repository, gameroom, user, gameroom_id
    ) -> None:
        gameroom = Gameroom(id=gameroom_id, name="bar", owner_id=uuid4(), users=(user,))
        gamerooms_repository.get_gameroom_by_id = Mock(return_value=gameroom)
        expected = DisconnectResult(
            gameroom=gameroom.with_leaving(user), remaining_users=()
        )

        result = sut.disconnect(context)

        assert result == expected


class TestStartGame:
    @pytest.fixture()
    def user(self, user_id, gameroom_id) -> User:
        return User(name="foo", id=user_id, current_gameroom_id=gameroom_id)

    @pytest.fixture()
    def context(self, session, user) -> Context:
        return Context(session=session, user=user)

    def test_when_user_is_not_gameroom_owner__raises_not_gameroom_owner_error(
        self, sut, context, user_id, gameroom_id, user, gamerooms_repository
    ) -> None:
        gameroom = Gameroom(id=gameroom_id, name="bar", owner_id=uuid4(), users=(user,))
        gamerooms_repository.get_gameroom_by_id = Mock(return_value=gameroom)

        with pytest.raises(NotGameroomOwnerError):
            sut.start_game(context, gameroom_id="foo")

    def test_when_user_is_gameroom_owner__returns_new_game(
        self, sut, context, game_toolkit, games_repository
    ) -> None:
        expected = Mock()
        games_repository.save_game = Mock(return_value=expected)

        result = sut.start_game(context, gameroom_id="foo")

        assert result == expected

    def test_when_user_is_gameroom_owner__saves_gameroom_with_new_game(
        self, sut, context, gameroom, gamerooms_repository, games_repository
    ) -> None:
        game = Mock()
        expected = Mock()
        gameroom.with_started_game = Mock(return_value=expected)
        games_repository.save_game = Mock(return_value=game)
        gamerooms_repository.get_gameroom_by_id = Mock(return_value=gameroom)

        sut.start_game(context, gameroom_id="foo")

        gamerooms_repository.save_gameroom.assert_called_once_with(
            session=context.session, gameroom=expected
        )
        gameroom.with_started_game.assert_called_once_with(game)

    def test_when_user_is_gameroom_owner__creats_game_from_gameroom(
        self, sut, context, gameroom, gamerooms_repository, game_toolkit, games_repository
    ) -> None:
        gamerooms_repository.get_gameroom_by_id = Mock(return_value=gameroom)

        sut.start_game(context, gameroom_id="foo")

        game_toolkit.create_game.assert_called_once_with(gameroom=gameroom)


class TestFinishGame:
    def test_deletes_gameroom(
        self, sut, context, gameroom, gameroom_id, gamerooms_repository
    ) -> None:
        gamerooms_repository.get_gameroom_by_id = Mock(return_value=gameroom)

        sut.finish_game(context, gameroom_id=gameroom_id)

        gamerooms_repository.delete_gameroom.assert_called_once_with(
            session=context.session, gameroom=gameroom.without_game()
        )

    def test_when_gameroom_has_game__deletes_game(
        self, sut, context, gameroom, gameroom_id, gamerooms_repository, games_service
    ) -> None:
        game = Mock()
        gameroom.game = game
        gamerooms_repository.get_gameroom_by_id = Mock(return_value=gameroom)

        sut.finish_game(context, gameroom_id=gameroom_id)

        games_service.delete.assert_called_once_with(context, game=game)
