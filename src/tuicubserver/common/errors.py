import json
from abc import ABC, abstractmethod

from flask import Response
from sqlalchemy.exc import OperationalError

from .logger import Logger


class TuicubError(Exception, ABC):
    """Base class for all application errors."""

    @property
    @abstractmethod
    def code(self) -> int:
        """The HTTP status code of the error."""

    @property
    @abstractmethod
    def message(self) -> str:
        """The error message for the user."""

    @property
    @abstractmethod
    def error_name(self) -> str:
        """The name of the error used for logging."""

    @property
    def info(self) -> dict | None:
        """Optional context data containing relevant parameters that caused the error."""
        return self._info

    def __init__(self, info: dict | None = None):
        """Initialize new error.

        Args:
            info (dict | None): Optional context data.
        """
        self._info: dict | None = info
        super().__init__(self.message)


class BadRequestError(TuicubError):
    @property
    def code(self) -> int:
        return 400


class UnauthorizedError(TuicubError):
    @property
    def code(self) -> int:
        return 401

    @property
    def message(self) -> str:
        return "The authentication token is either missing or is invalid."

    @property
    def error_name(self) -> str:
        return "unauthorized"


class ForbiddenError(TuicubError):
    @property
    def code(self) -> int:
        return 403

    @property
    def message(self) -> str:
        return "Forbidden."

    @property
    def error_name(self) -> str:
        return "forbidden"


class NotFoundError(TuicubError):
    @property
    def code(self) -> int:
        return 404

    @property
    def message(self) -> str:
        return "Resource not found."

    @property
    def error_name(self) -> str:
        return "not_found"


class ValidationError(BadRequestError):
    @property
    def message(self) -> str:
        return f"Invalid input: {self._reason}"

    @property
    def error_name(self) -> str:
        return "validation"

    def __init__(self, reason: str):
        self._reason: str = reason
        super().__init__()


class InvalidIdentifierError(BadRequestError):
    @property
    def message(self) -> str:
        return "The identifier is not a valid UUID."

    @property
    def error_name(self) -> str:
        return "invalid_identifier"


class ErrorHandler:
    """An error handler for application errors."""

    __slot__ = ("_logger",)

    def __init__(self, logger: Logger):
        """Initialize new error handler.

        Args:
            logger (Logger): The logger to log errors with.
        """
        self._logger: Logger = logger

    def handle_tuicub_error(self, error: TuicubError) -> Response:
        """Handle an application error.

        Args:
            error (TuicubError): The error to handle.

        Returns:
            An instance of `flask.Response` containing details of the error.
        """
        self._logger.log("error", error_name=error.error_name, error_info=error.info)
        return ErrorResponse(message=error.message, code=error.code)

    def handle_sqlalchemy_error(self, error: OperationalError) -> Response:
        """Handle a database error.

        Args:
            error (TuicubError): The error to handle.

        Returns:
            An instance of `flask.Response` containing details of the error.
        """
        self._logger.log("error", error_name="sqlalchemy", error_info={})
        return ErrorResponse(message="Another operation is pending. Try again.", code=400)


class ErrorResponse(Response):
    """An HTTP response for an application error."""

    def __init__(self, message: str, code: int):
        super().__init__(
            json.dumps({"message": message}), status=code, content_type="application/json"
        )
