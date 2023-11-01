import atexit
from io import TextIOWrapper
from pathlib import Path
from typing import Any

import structlog
from flask import Flask, Response


class Logger:
    """A logging interface wrapping the `structlog`."""

    __slots__ = ("_logfile_path", "_logfile", "__weakref__")

    def __init__(self, logfile_path: Path):
        """Initialize new logger.

        Args:
            logfile_path (Path): The path to the file to write logs to.
        """
        self._logfile_path: Path = logfile_path
        self._logfile: TextIOWrapper | None = None

    def configure(self) -> None:
        """Configure the logger."""
        logfile = open(self._logfile_path, "a")  # noqa: SIM115
        atexit.register(logfile.close)
        self._logfile = logfile

        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.ExceptionRenderer(
                    structlog.tracebacks.ExceptionDictTransformer(max_frames=3)
                ),
                structlog.processors.TimeStamper(fmt="iso", key="ts"),
                structlog.processors.JSONRenderer(),
            ],
            logger_factory=structlog.WriteLoggerFactory(file=logfile),
        )

    def log(self, event: str, *args: Any, **kwargs: Any) -> None:
        """Log an event with additional keyword parameters."""
        log = structlog.get_logger()
        log.info(event, **kwargs)

    def log_error(self, event: str, err: Exception, *args: Any, **kwargs: Any) -> None:
        """Log an error with additional keyword parameters."""
        log = structlog.get_logger()
        log.exception(event, exc_info=err, **kwargs)

    def log_response(self, sender: Flask, response: Response, **extra: Any) -> None:
        """Log an HTTP response."""
        self.log("request", code=response.status_code)

    def bind_contextvars(self, *args: Any, **kwargs: Any) -> None:
        """Clears and binds new context parameters to include in log entries."""
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(**kwargs)
