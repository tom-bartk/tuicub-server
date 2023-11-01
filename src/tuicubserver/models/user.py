import uuid

from attrs import frozen

from ..common.errors import BadRequestError


@frozen
class User:
    """The model representing a user.

    Attributes:
        id (uuid.UUID): The id of the user.
        name (str): The name of the user.
        current_gameroom_id (uuid.UUID | None): An optional id of the gameroom,
            that the user has joined, or is an owner of.
    """

    id: uuid.UUID
    name: str
    current_gameroom_id: uuid.UUID | None

    def ensure_not_in_gameroom(self) -> None:
        """Verify that the user is not in a gameroom.

        Raises:
            AlreadyInGameroomError: Raised when the user is already in a gameroom.
        """
        if self.current_gameroom_id is not None:
            raise AlreadyInGameroomError(gameroom_id=self.current_gameroom_id)


@frozen
class UserToken:
    """The model representing an authentication token.

    Attributes:
        id (uuid.UUID): The id of the authentication token.
        user_id (uuid.UUID): The id of the user that this authentication token belongs to.
            has joined, or is an owner of.
        token (str): The string value of the authentication token.
    """

    id: uuid.UUID
    user_id: uuid.UUID
    token: str


class AlreadyInGameroomError(BadRequestError):
    @property
    def message(self) -> str:
        return "You are already in a gameroom."

    @property
    def error_name(self) -> str:
        return "already_in_gameroom"

    def __init__(self, gameroom_id: uuid.UUID):
        super().__init__(info={"gameroom_id": str(gameroom_id)})
