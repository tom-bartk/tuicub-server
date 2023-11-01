from uuid import uuid4

import pytest

from src.tuicubserver.models.user import AlreadyInGameroomError, User


class TestEnsureNotInGameroom:
    def test_when_current_gameroom_id_is_not_none__raises_already_in_gameroom_error(
        self,
    ) -> None:
        sut = User(id=uuid4(), name="foo", current_gameroom_id=uuid4())

        with pytest.raises(AlreadyInGameroomError):
            sut.ensure_not_in_gameroom()
