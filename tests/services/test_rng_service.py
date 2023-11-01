from unittest.mock import Mock, create_autospec, patch

import pytest

from src.tuicubserver.services.rng import RngService, SequenceEmptyError


@pytest.fixture()
def sut() -> RngService:
    return RngService()


class TestPick:
    def test_when_sequence_empty__raises_sequence_empty_error(self, sut) -> None:
        with pytest.raises(SequenceEmptyError):
            sut.pick([])

    def test_when_sequence_not_empty__picks_random_element(self, sut) -> None:
        with patch("random.choice") as mocked_choice:
            sut.pick([1, 2, 3])

            mocked_choice.assert_called_once_with([1, 2, 3])

    def test_when_sequence_not_empty__returns_result_of_random_choice(self, sut) -> None:
        expected = 4
        with patch("random.choice", return_value=expected):
            result = sut.pick([1, 2, 3])

            assert result == expected


class TestShuffle:
    def test_randomly_shuffles_copy_of_input_list(self, sut) -> None:
        expected = [1, 2, 3]
        input_list = create_autospec(list)
        input_list.copy = Mock(return_value=expected)

        with patch("random.shuffle") as mocked_shuffle:
            result = sut.shuffle(input_list)

            input_list.copy.assert_called_once()
            mocked_shuffle.assert_called_once_with(expected)
            assert result == expected
