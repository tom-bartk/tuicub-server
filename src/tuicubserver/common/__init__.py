from pathlib import Path

from .config import Config
from .db import Database
from .logger import Logger


class Common:
    @property
    def config(self) -> Config:
        return self._config

    @property
    def logger(self) -> Logger:
        return self._logger

    @property
    def db(self) -> Database:
        return self._db

    def __init__(self) -> None:
        self._config: Config = Config.load()

        self._logger: Logger = Logger(logfile_path=Path(self._config.logfile_path))
        self._logger.configure()

        self._db: Database = Database(connstr=self._config.db_url)
