import string
from unittest.mock import Mock

import pytest
from werkzeug.datastructures import Headers

from src.tuicubserver.common.errors import UnauthorizedError
from src.tuicubserver.services.auth import AuthService
from tests.utils import not_raises


@pytest.fixture()
def events_secret() -> str:
    return "s3cr3t"


@pytest.fixture()
def messages_secret() -> str:
    return "s3cr3t_tw0"


@pytest.fixture()
def sut(users_repository, events_secret, messages_secret) -> AuthService:
    return AuthService(
        users_repository=users_repository,
        events_secret=events_secret,
        messages_secret=messages_secret,
    )


class TestAuthorize:
    def test_when_no_authorization_header__raises_unauthorized_error(
        self, sut, session
    ) -> None:
        with pytest.raises(UnauthorizedError):
            sut.authorize(session, headers=Headers())

    def test_when_authorization_header_has_no_bearer__raises_unauthorized_error(
        self, sut, session
    ) -> None:
        with pytest.raises(UnauthorizedError):
            sut.authorize(session, headers=Headers((("Authorization", "Let me in"),)))

    def test_when_authorization_header_is_valid__returns_user_by_token(
        self, sut, session, users_repository
    ) -> None:
        expected = Mock()
        users_repository.get_user_by_token = Mock(return_value=expected)

        result = sut.authorize(
            session, headers=Headers((("Authorization", "Bearer token"),))
        )

        assert result == expected

    def test_when_authorization_header_is_valid__queries_repository_with_token(
        self, sut, session, users_repository
    ) -> None:
        sut.authorize(session, headers=Headers((("Authorization", "Bearer t0k3n"),)))

        users_repository.get_user_by_token.assert_called_once_with(
            session=session, token="t0k3n"
        )


class TestAuthorizeEventsServer:
    def test_when_no_authorization_header__raises_unauthorized_error(self, sut) -> None:
        with pytest.raises(UnauthorizedError):
            sut.authorize_events_server(headers=Headers())

    def test_when_authorization_header_has_no_bearer__raises_unauthorized_error(
        self, sut
    ) -> None:
        with pytest.raises(UnauthorizedError):
            sut.authorize_events_server(
                headers=Headers((("Authorization", "Let me in"),))
            )

    def test_when_authorization_header_has_correct_secret__does_not_raise(
        self, sut, session, events_secret
    ) -> None:
        with not_raises(UnauthorizedError):
            sut.authorize_events_server(
                headers=Headers((("Authorization", f"Bearer {events_secret}"),))
            )

    def test_when_authorization_header_has_incorrect_secret__raises_unauthorized_error(
        self, sut, session, events_secret
    ) -> None:
        with pytest.raises(UnauthorizedError):
            sut.authorize_events_server(
                headers=Headers((("Authorization", "Bearer letmein"),))
            )


class TestAuthorizeMessage:
    def test_when_secret_is_correct__does_not_raise(
        self, sut, session, messages_secret
    ) -> None:
        with not_raises(UnauthorizedError):
            sut.authorize_message(secret=messages_secret)

    def test_when_secret_is_incorrect__raises_unauthorized_error(
        self, sut, session, messages_secret
    ) -> None:
        with pytest.raises(UnauthorizedError):
            sut.authorize_message(secret="letmein")


class TestGenerateToken:
    def test_returns_string_of_length_64(self, sut) -> None:
        result = sut.generate_token()

        assert len(result) == 64

    def test_returns_hex_string(self, sut) -> None:
        result = sut.generate_token()

        assert all(c in string.hexdigits for c in result)
