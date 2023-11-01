from unittest.mock import Mock, patch

import pytest

from src.tuicubserver.models.user import User, UserToken
from src.tuicubserver.services.users import UsersService


@pytest.fixture()
def sut(users_repository, auth_service) -> UsersService:
    return UsersService(auth_service=auth_service, users_repository=users_repository)


class TestCreateUser:
    def test_returns_created_user_and_token(
        self, sut, base_context, users_repository
    ) -> None:
        user = Mock()
        token = Mock()
        users_repository.save_user = Mock(return_value=user)
        users_repository.save_user_token = Mock(return_value=token)
        expected = (user, token)

        result = sut.create_user(base_context, "foo")

        assert result == expected

    def test_creates_user_with_passed_name(
        self, sut, base_context, users_repository
    ) -> None:
        user_id = Mock()
        expected = User(id=user_id, name="foo", current_gameroom_id=None)

        with patch("uuid.uuid4", return_value=user_id):
            sut.create_user(base_context, "foo")

            users_repository.save_user.assert_called_once_with(
                session=base_context.session, user=expected
            )

    def test_creates_token_for_user(
        self, sut, base_context, users_repository, auth_service
    ) -> None:
        token = Mock()
        auth_service.generate_token = Mock(return_value=token)

        user_id = Mock()
        token_id = Mock()
        expected = UserToken(id=token_id, user_id=user_id, token=token)

        with patch("uuid.uuid4", side_effect=[user_id, token_id]):
            sut.create_user(base_context, "foo")

            users_repository.save_user_token.assert_called_once_with(
                session=base_context.session, user_token=expected
            )


class TestGetUserToken:
    def test_returns_user_token(self, sut, session, users_repository) -> None:
        expected = Mock()
        users_repository.get_user_token_by_token = Mock(return_value=expected)

        result = sut.get_user_token(session, "foo")

        assert result == expected

    def test_queries_repository_with_passed_token(
        self, sut, session, users_repository
    ) -> None:
        expected = Mock()

        sut.get_user_token(session, expected)

        users_repository.get_user_token_by_token.assert_called_once_with(
            session=session, token=expected
        )


class TestGetUserById:
    def test_returns_user_token(self, sut, session, users_repository) -> None:
        expected = Mock()
        users_repository.get_user_by_id = Mock(return_value=expected)

        result = sut.get_user_by_id(session, Mock())

        assert result == expected

    def test_queries_repository_with_passed_id(
        self, sut, session, users_repository
    ) -> None:
        expected = Mock()

        sut.get_user_by_id(session, expected)

        users_repository.get_user_by_id.assert_called_once_with(
            session=session, id=expected
        )
