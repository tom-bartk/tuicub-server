from enum import StrEnum


class GameroomStatus(StrEnum):
    """A current state of a gameroom."""

    STARTING = "STARTING"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    DELETED = "DELETED"
