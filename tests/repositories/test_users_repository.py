from unittest.mock import Mock, PropertyMock, create_autospec
from uuid import uuid4

import pytest
from sqlalchemy import ScalarResult

from src.tuicubserver.common.errors import NotFoundError, UnauthorizedError
from src.tuicubserver.models.db import DbUserToken
from src.tuicubserver.repositories.users import UsersRepository


@pytest.fixture()
def sut(mapper) -> UsersRepository:
    return UsersRepository(mapper=mapper)


class TestGetUserById:
    def test_returns_mapped_db_model(self, sut, session, mapper) -> None:
        expected = Mock()
        mapper.to_domain_user = Mock(return_value=expected)

        result = sut.get_user_by_id(session=session, id=uuid4())

        assert result == expected


class TestGetUserByToken:
    def test_when_no_token_found__raises_unauthorized_error(self, sut, session) -> None:
        scalars = create_autospec(ScalarResult)
        scalars.first = Mock(return_value=None)

        session.scalars = Mock(return_value=scalars)

        with pytest.raises(UnauthorizedError):
            sut.get_user_by_token(session=session, token="foo")

    def test_when_token_found__no_user_found__raises_unauthorized_error(
        self, sut, session
    ) -> None:
        scalars = create_autospec(ScalarResult)
        token = create_autospec(DbUserToken)
        type(token).user_id = PropertyMock(return_value=uuid4())
        scalars.first = Mock(return_value=token)

        session.scalars = Mock(return_value=scalars)
        session.get = Mock(side_effect=NotFoundError)

        with pytest.raises(UnauthorizedError):
            sut.get_user_by_token(session=session, token="foo")

    def test_when_token_and_user_found__returns_mapped_db_user(
        self, sut, session, mapper
    ) -> None:
        scalars = create_autospec(ScalarResult)
        token = create_autospec(DbUserToken)
        type(token).user_id = PropertyMock(return_value=uuid4())
        scalars.first = Mock(return_value=token)

        session.scalars = Mock(return_value=scalars)

        expected = Mock()
        mapper.to_domain_user = Mock(return_value=expected)

        result = sut.get_user_by_token(session=session, token="foo")

        assert result == expected


class TestSaveUser:
    def test_uses_user_mapper(self, sut, session, mapper, user) -> None:
        sut.save_user(session=session, user=user)

        mapper.to_db_user.assert_called_once_with(user)

    def test_uses_user_db_mapper(self, sut, session, mapper, user) -> None:
        expected = Mock()
        session.merge = Mock(return_value=expected)

        sut.save_user(session=session, user=user)

        mapper.to_domain_user.assert_called_once_with(expected)

    def test_returns_user_db_mapper_result(self, sut, session, mapper, user) -> None:
        expected = Mock()
        mapper.to_domain_user = Mock(return_value=expected)

        result = sut.save_user(session=session, user=user)

        assert result == expected


class TestSaveUserToken:
    def test_uses_user_token_mapper(self, sut, session, mapper, user_token) -> None:
        sut.save_user_token(session=session, user_token=user_token)

        mapper.to_db_user_token.assert_called_once_with(user_token)

    def test_uses_user_token_db_mapper(self, sut, session, mapper, user_token) -> None:
        expected = Mock()
        session.merge = Mock(return_value=expected)

        sut.save_user_token(session=session, user_token=user_token)

        mapper.to_domain_user_token.assert_called_once_with(expected)

    def test_returns_user_token_db_mapper_result(
        self, sut, session, mapper, user_token
    ) -> None:
        expected = Mock()
        mapper.to_domain_user_token = Mock(return_value=expected)

        result = sut.save_user_token(session=session, user_token=user_token)

        assert result == expected


class TestGetUserTokenByToken:
    def test_when_no_token_found__raises_unauthorized_error(self, sut, session) -> None:
        scalars = create_autospec(ScalarResult)
        scalars.first = Mock(return_value=None)
        session.scalars = Mock(return_value=scalars)

        with pytest.raises(UnauthorizedError):
            sut.get_user_token_by_token(session=session, token="foo")

    def test_when_token_found__returns_mapped_db_user_token(
        self, sut, session, mapper
    ) -> None:
        expected = Mock()
        mapper.to_domain_user_token = Mock(return_value=expected)

        result = sut.get_user_token_by_token(session=session, token="foo")

        assert result == expected
