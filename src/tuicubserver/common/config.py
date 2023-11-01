from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any, TypeVar

from attrs import frozen

from .utils import sha256


@frozen
class Config:
    """The configuration object.

    Attributes:
        db_url (str): The url to use when connecting to the database.
            Defaults to "sqlite://".
        logfile_path (str): The path of a file to write logs to.
            Defaults to "/tmp/tuicubserver.log".
        messages_host (str): The host of the messages server. Defaults to "localhost".
        messages_port (int): The port of the messages server. Defaults to 12421.
        messages_secret (str): The secret to use when authenticating messages.
            Defaults to "change_me".
        events_secret (str): The secret to use for disconnect callbacks to the API Server.
            Defaults to "change_me".
    """

    class Defaults:
        db_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/tuicub"
        logfile_path: str = "/tmp/tuicubserver.log"
        messages_host: str = "api.tuicub.com"
        messages_port: int = 23433
        messages_secret: str = "changeme"
        events_secret: str = "changeme"

    db_url: str
    logfile_path: str
    messages_host: str
    messages_port: int
    messages_secret: str
    events_secret: str

    @classmethod
    def load(cls) -> Config:
        """Load a config from the config file.

        The path to the config file is read from the `TUICUBSERV_CONF` environment
        variable.

        If the variable is not set, falls back to reading `config.toml`
        from the current working directory.

        If none of the files exist, falls back to using default values.

        Returns:
            The loded configuration.
        """
        try:
            config_path = Path(os.environ["TUICUBSERV_CONF"])
        except Exception:
            config_path = Path("config.toml")

        db_url = Config.Defaults.db_url
        logfile_path = Config.Defaults.logfile_path
        messages_host = Config.Defaults.messages_host
        messages_port = Config.Defaults.messages_port
        messages_secret = Config.Defaults.messages_secret
        events_secret = Config.Defaults.events_secret

        if config_path.exists():
            with open(config_path, "rb") as config_file:
                config_dict = tomllib.load(config_file)

                db = _subdict("db", config_dict)
                db_url = _get("url", str, db, default=Config.Defaults.db_url)

                logging = _subdict("logging", config_dict)
                logfile_path = _get(
                    "logfile", str, logging, default=Config.Defaults.logfile_path
                )

                messages = _subdict("messages", config_dict)
                messages_host = _get(
                    "host", str, messages, default=Config.Defaults.messages_host
                )
                messages_port = _get(
                    "port", int, messages, default=Config.Defaults.messages_port
                )
                messages_secret = _get(
                    "secret", str, messages, default=Config.Defaults.messages_secret
                )

                events = _subdict("events", config_dict)
                events_secret = _get(
                    "secret", str, events, default=Config.Defaults.events_secret
                )

        return Config(
            db_url=db_url,
            logfile_path=logfile_path,
            messages_host=messages_host,
            messages_port=messages_port,
            messages_secret=sha256(messages_secret),
            events_secret=sha256(events_secret),
        )


_T = TypeVar("_T")


def _get(key: str, type_: type[_T], dict_: dict[str, Any], default: _T) -> _T:
    if (value := dict_.get(key, None)) and isinstance(value, type_):
        return value
    return default


def _subdict(key: str, dict_: dict[str, Any]) -> dict[str, Any]:
    if (subdict := dict_.get(key, None)) and isinstance(subdict, dict):
        return subdict
    return {}
