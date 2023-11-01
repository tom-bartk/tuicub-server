from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from attrs import frozen
from marshmallow_generic import GenericSchema, fields

if TYPE_CHECKING:
    from ..events.events import Event


@frozen
class Message:
    """A message to the events server containing a serialized event and recipents.

    Attributes:
        recipents (list[uuid.UUID]): The list of recipents of the event.
        event (dict): The serialized event.
    """

    recipents: list[uuid.UUID]
    event: dict

    @classmethod
    def from_event(cls, event: Event) -> Message:
        """Create a message for the event.

        Args:
            event (Event): The event to create a message for.

        Returns:
            The created message.
        """
        payload = {"name": event.event_name, "data": event.serialize()}
        return Message(recipents=list(event.recipents), event=payload)


@frozen
class MessageEnvelope:
    """A wrapper object for a message that includes an authentication token.

    Attributes:
        token (str): The authentication token.
        message (Message): The wrapped message.
    """

    token: str
    message: Message


class MessageSchema(GenericSchema[Message]):
    """The schema for serializing and deserializing messages."""

    class Meta:
        ordered = True

    recipents = fields.List(fields.UUID())
    event = fields.Dict(required=True, allow_none=False)


class MessageEnvelopeSchema(GenericSchema[MessageEnvelope]):
    """The schema for serializing and deserializing message envelopes."""

    class Meta:
        ordered = True

    token = fields.Str(required=True, allow_none=False)
    message = fields.Nested(MessageSchema)
