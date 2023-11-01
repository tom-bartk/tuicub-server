from unittest.mock import patch

from src.tuicubserver.common import Common
from src.tuicubserver.common.config import Config
from src.tuicubserver.common.db import Database
from src.tuicubserver.common.logger import Logger


class TestCommon:
    def test_initializes_config_and_logger(self) -> None:
        with patch.object(Config, "load") as mocked_load, patch.object(
            Logger, "configure"
        ) as mocked_configure:
            Common()

            mocked_load.assert_called_once()
            mocked_configure.assert_called_once()

    def test_creates_valid_instances(self) -> None:
        sut = Common()

        assert isinstance(sut.config, Config)
        assert isinstance(sut.logger, Logger)
        assert isinstance(sut.db, Database)
