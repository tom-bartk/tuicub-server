import random
import time
from collections.abc import Sequence
from typing import TypeVar

_T = TypeVar("_T")


class RngService:
    """The random numbers generator."""

    __slots__ = ()

    def __init__(self, seed: int | None = None):
        """Initializes new service.

        Args:
            seed (int | None): The seed to use for seeding the generator.
        """
        random.seed(seed if seed is not None else time.time())

    def pick(self, seq: Sequence[_T]) -> _T:
        """Pick a random value from the sequence.

        Args:
            seq (Sequence[_T]): The sequence to pick from.

        Returns:
            The picked value.

        Raises:
            SequenceEmptyError: Raised when the sequence is empty.
        """
        if not seq:
            raise SequenceEmptyError()
        return random.choice(seq)

    def shuffle(self, seq: list[_T]) -> list[_T]:
        """Shuffle a sequence.

        Args:
            seq (list[_T]): The sequence to shuffle.

        Returns:
            The shuffled copy of the sequence.
        """
        seq_copy = seq.copy()
        random.shuffle(seq_copy)
        return seq_copy


class SequenceEmptyError(Exception):
    def __init__(self):
        super().__init__("Sequence is empty.")
