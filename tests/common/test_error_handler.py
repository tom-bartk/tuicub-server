import pytest
from sqlalchemy.exc import OperationalError

from src.tuicubserver.common.errors import ErrorHandler, ErrorResponse, TuicubError


class MockError(TuicubError):
    @property
    def code(self) -> int:
        return 42

    @property
    def message(self) -> str:
        return "foo"

    @property
    def error_name(self) -> str:
        return "bar"

    def __init__(self):
        super().__init__(info={"foo": "bar"})


@pytest.fixture()
def sut(logger) -> ErrorHandler:
    return ErrorHandler(logger=logger)


class TestHandleTuicubError:
    def test_logs_error(self, sut, logger) -> None:
        error = MockError()
        sut.handle_tuicub_error(error=error)

        logger.log.assert_called_once_with(
            "error", error_name=error.error_name, error_info=error.info
        )

    def test_returns_error_response(self, sut) -> None:
        error = MockError()
        expected = ErrorResponse(message="foo", code=42)

        result = sut.handle_tuicub_error(error=error)

        assert result.response == expected.response
        assert result.status_code == 42
        assert isinstance(result, ErrorResponse)


class TestHandleSqlalchemyError:
    def test_logs_error(self, sut, logger) -> None:
        error = OperationalError(statement=None, params=None, orig=ValueError())
        sut.handle_sqlalchemy_error(error=error)

        logger.log.assert_called_once_with(
            "error", error_name="sqlalchemy", error_info={}
        )

    def test_returns_error_response(self, sut) -> None:
        error = OperationalError(statement=None, params=None, orig=ValueError())
        expected = ErrorResponse(
            message="Another operation is pending. Try again.", code=400
        )

        result = sut.handle_sqlalchemy_error(error=error)

        assert result.response == expected.response
        assert result.status_code == 400
        assert isinstance(result, ErrorResponse)
