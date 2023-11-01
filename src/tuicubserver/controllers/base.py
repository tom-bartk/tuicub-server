from typing import Any

from flask import request
from marshmallow import EXCLUDE, Schema
from marshmallow import ValidationError as MarshmallowError
from more_itertools import flatten

from ..common.errors import ValidationError
from ..messages.service import MessagesService

SUCCESS_RESPONSE = {"success": True}


class BaseController:
    """Base class for a resource controller."""

    __slots__ = ("_messages_service",)

    def __init__(self, messages_service: MessagesService):
        """Initialize new controller.

        Args:
            messages_service (MessagesService): The messages service for communicating
                with the events server.
        """
        self._messages_service: MessagesService = messages_service

    def _deserialize_json(self, schema: Schema) -> dict:
        """Deserialize request body into a json dictionary using a schema."""
        body: Any = request.get_json(force=True, silent=True, cache=False) or {}
        return schema.load(body, unknown=EXCLUDE)


class BaseBodySchema(Schema):
    """Base schema for request body schemas."""

    def handle_error(
        self, error: MarshmallowError, data: Any, *args: Any, many: bool, **kwargs: Any
    ) -> Any:
        """Handle validation error.

        Recursively extracts all error messages from all fields and merges them
        into a single reason string.
        """
        reason = " ".join(_unwrap_messages(error.normalized_messages()))
        raise ValidationError(reason=reason)


def _unwrap_messages(value: dict[str, list[str]] | list[str]) -> list[str]:
    if isinstance(value, dict):
        return list(flatten([_unwrap_messages(val) for key, val in value.items()]))
    return value
