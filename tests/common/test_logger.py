from io import TextIOWrapper
from pathlib import Path
from unittest.mock import Mock, create_autospec, patch

import pytest
import structlog
from flask import Flask, Response

from src.tuicubserver.common.logger import Logger


@pytest.fixture()
def logfile_path() -> Path:
    return create_autospec(Path)


@pytest.fixture()
def sut(logfile_path) -> Logger:
    return Logger(logfile_path=logfile_path)


@pytest.fixture()
def mock_open() -> Mock:
    context_manager = Mock()
    context_manager.__enter__ = Mock()
    context_manager.__exit__ = Mock()
    return context_manager


@pytest.fixture()
def mock_log() -> structlog.types.FilteringBoundLogger:
    return create_autospec(structlog.types.FilteringBoundLogger)


class TestConfigure:
    def test_opens_logfile_for_appending(self, sut, logfile_path) -> None:
        with patch("builtins.open") as mocked_open:
            sut.configure()

            mocked_open.assert_called_with(logfile_path, "a")

    def test_registers_close_logfile_atexit_callback(self, sut) -> None:
        logfile = create_autospec(TextIOWrapper)
        with patch("builtins.open", return_value=logfile), patch(
            "atexit.register"
        ) as mocked_register:
            sut.configure()

            mocked_register.assert_called_with(logfile.close)

    def test_configures_structlog(self, sut) -> None:
        with patch("builtins.open"), patch("structlog.configure") as mocked_configure:
            sut.configure()

            mocked_configure.assert_called_once()


class TestLog:
    def test_logs_info_with_event_and_passed_kwargs(self, sut, mock_log) -> None:
        with patch("structlog.get_logger", return_value=mock_log):
            sut.log("foo", bar="baz", foobar=42)

            mock_log.info.assert_called_once_with("foo", bar="baz", foobar=42)


class TestLogError:
    def test_logs_exception_with_event__error_as_exc_info_and_kwargs(
        self, sut, mock_log
    ) -> None:
        err = create_autospec(Exception)

        with patch("structlog.get_logger", return_value=mock_log):
            sut.log_error("foo", err=err, bar="baz")

            mock_log.exception.assert_called_once_with("foo", exc_info=err, bar="baz")


class TestLogResponse:
    def test_logs_info_request_event_with_response_status_code(
        self, sut, mock_log
    ) -> None:
        response = create_autospec(Response)
        response.status_code = 42
        sender = create_autospec(Flask)

        with patch("structlog.get_logger", return_value=mock_log):
            sut.log_response(sender=sender, response=response)

            mock_log.info.assert_called_once_with("request", code=42)


class TestBindContextVars:
    def test_clears_context_vars_and_binds_new_from_kwargs(self, sut, mock_log) -> None:
        with patch(
            "structlog.contextvars.clear_contextvars"
        ) as mocked_clear_contextvars, patch(
            "structlog.contextvars.bind_contextvars"
        ) as mocked_bind_contextvars:
            sut.bind_contextvars(foo=42, bar="baz")

            mocked_clear_contextvars.assert_called_once()
            mocked_bind_contextvars.assert_called_once_with(foo=42, bar="baz")
