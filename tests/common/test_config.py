from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.tuicubserver.common.config import Config


@pytest.fixture()
def mock_open() -> Mock:
    context_manager = Mock()
    context_manager.__enter__ = Mock()
    context_manager.__exit__ = Mock()
    return context_manager


class TestLoad:
    def test_when_tuicubserv_conf_env_variable_is_exisitng_file__loads_config_from_it(
        self, mock_open
    ) -> None:
        config_dict = {
            "db": {"url": "sqlite://db"},
            "messages": {"host": "foo", "port": 42, "secret": "bar"},
            "events": {"secret": "baz"},
            "logging": {"logfile": "foobar"},
        }
        expected = Config(
            db_url="sqlite://db",
            logfile_path="foobar",
            messages_host="foo",
            messages_port=42,
            messages_secret="fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9",  # sha256 of 'bar' # noqa: E501
            events_secret="baa5a0964d3320fbc0c6a922140453c8513ea24ab8fd0577034804a967248096",  # sha256 of 'baz' # noqa: E501
        )

        with patch.dict("os.environ", {"TUICUBSERV_CONF": "foo"}, clear=True), patch(
            "builtins.open", return_value=mock_open
        ) as mocked_open, patch("tomllib.load", return_value=config_dict), patch.object(
            Path, "exists", return_value=True
        ):
            result = Config.load()

            mocked_open.assert_called_once_with(Path("foo"), "rb")
            assert result == expected

    def test_when_no_tuicubserv_conf_env_variable__falls_back_to_default_config_path(
        self, mock_open
    ) -> None:
        with patch.dict("os.environ", {}, clear=True), patch(
            "builtins.open", return_value=mock_open
        ) as mocked_open, patch("tomllib.load", return_value={}), patch.object(
            Path, "exists", return_value=True
        ):
            Config.load()

            mocked_open.assert_called_once_with(Path("config.toml"), "rb")

    def test_when_no_tuicubserv_conf_env_variable__fallback_does_not_exists__returns_default_config(  # noqa: E501
        self,
    ) -> None:
        expected = Config(
            db_url=Config.Defaults.db_url,
            logfile_path=Config.Defaults.logfile_path,
            messages_host=Config.Defaults.messages_host,
            messages_port=Config.Defaults.messages_port,
            messages_secret="057ba03d6c44104863dc7361fe4578965d1887360f90a0895882e58a6248fc86",  # sha256 of 'changeme' # noqa: E501
            events_secret="057ba03d6c44104863dc7361fe4578965d1887360f90a0895882e58a6248fc86",  # sha256 of 'changeme' # noqa: E501
        )

        with patch.object(Path, "exists", return_value=False), patch.dict(
            "os.environ", {}, clear=True
        ):
            result = Config.load()

            assert result == expected
