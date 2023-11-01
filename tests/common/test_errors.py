from src.tuicubserver.common.errors import (
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)


class MockBadRequestError(BadRequestError):
    @property
    def message(self) -> str:
        return "foo"

    @property
    def error_name(self) -> str:
        return "bar"


class TestErrors:
    def test_bad_request__has_400_code(self) -> None:
        sut = MockBadRequestError()
        expected = 400

        result = sut.code

        assert result == expected

    def test_unauthorized__has_401_code(self) -> None:
        sut = UnauthorizedError()
        expected = 401

        result = sut.code

        assert result == expected

    def test_forbidden__has_403_code(self) -> None:
        sut = ForbiddenError()
        expected = 403

        result = sut.code

        assert result == expected

    def test_not_found__has_404_code(self) -> None:
        sut = NotFoundError()
        expected = 404

        result = sut.code

        assert result == expected
