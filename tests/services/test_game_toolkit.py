from datetime import datetime
from unittest.mock import Mock, PropertyMock, create_autospec
from uuid import UUID, uuid4

import pytest

from src.tuicubserver.models.game import (
    Board,
    Game,
    GameState,
    Move,
    Pile,
    Player,
    Tileset,
    Turn,
)
from src.tuicubserver.models.gameroom import Gameroom, GameroomStatus
from src.tuicubserver.models.user import User
from src.tuicubserver.services.game_toolkit import (
    DuplicateTilesError,
    GameToolkit,
    InvalidMeldError,
    InvalidTilesetsError,
    MissingBoardTilesError,
    NewTilesNotFromRackError,
    NoNewTilesError,
    NotEnoughPlayersError,
)
from tests.utils import not_raises


@pytest.fixture()
def universal_id() -> UUID:
    return uuid4()


@pytest.fixture()
def user_id_1() -> UUID:
    return uuid4()


@pytest.fixture()
def user_id_2() -> UUID:
    return uuid4()


@pytest.fixture()
def user_1(user_id_1, gameroom_id) -> User:
    return User(id=user_id_1, name="foo", current_gameroom_id=gameroom_id)


@pytest.fixture()
def user_2(user_id_2, gameroom_id) -> User:
    return User(id=user_id_2, name="bar", current_gameroom_id=gameroom_id)


@pytest.fixture()
def player_1(player_id_1, user_id_1, game_state_id) -> Player:
    return Player(
        id=player_id_1,
        name="foo",
        rack=Tileset.create([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]),
        user_id=user_id_1,
    )


@pytest.fixture()
def player_2(player_id_2, user_id_2, game_state_id) -> Player:
    return Player(
        id=player_id_2,
        name="bar",
        rack=Tileset.create([14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]),
        user_id=user_id_2,
    )


@pytest.fixture()
def move_1(move_id_1, turn_id) -> Move:
    return Move(
        id=move_id_1,
        revision=1,
        rack=Tileset.create([4, 5, 6]),
        board=Board.create([[1, 2, 3]]),
        turn_id=turn_id,
    )


@pytest.fixture()
def move_2(move_id_2, turn_id) -> Move:
    return Move(
        id=move_id_2,
        revision=2,
        rack=Tileset.create([6, 7, 8]),
        board=Board.create([[4, 5, 6]]),
        turn_id=turn_id,
    )


@pytest.fixture()
def turn(turn_id, player_id_1, game_id, move_1, move_2) -> Turn:
    return Turn(
        id=turn_id,
        revision=42,
        starting_rack=Tileset.create([6, 7, 8]),
        starting_board=Board.create([[1, 2, 3], [4, 5, 6]]),
        player_id=player_id_1,
        game_id=game_id,
        moves=(move_1, move_2),
    )


@pytest.fixture()
def game_state(game_state_id, game_id, player_1, player_2) -> GameState:
    return GameState(
        id=game_state_id,
        game_id=game_id,
        players=(player_1, player_2),
        board=Board.create([[1, 2, 3], [4, 5, 6]]),
        pile=Pile([7, 8, 9]),
    )


@pytest.fixture()
def game(
    game_id, game_state_id, game_state, turn, player_id_1, player_id_2, gameroom_id
) -> Game:
    return Game(
        id=game_id,
        gameroom_id=gameroom_id,
        game_state=game_state,
        turn=turn,
        turn_order=(player_id_1, player_id_2),
        winner=None,
        made_meld=(player_id_1,),
    )


@pytest.fixture()
def gameroom(
    gameroom_id,
    user_id_1,
    user_1,
    user_2,
) -> Gameroom:
    return Gameroom(
        id=gameroom_id,
        name="foobar",
        owner_id=user_id_1,
        status=GameroomStatus.RUNNING,
        game=None,
        users=(user_1, user_2),
        created_at=datetime.now(),
    )


@pytest.fixture()
def sut(tileset_service, rng_service) -> GameToolkit:
    return GameToolkit(rng_service=rng_service, tilesets_service=tileset_service)


class TestCreateGame:
    def test_when_only_one_user_in_gameroom__raises_not_enough_players_error(
        self, sut, gameroom_id, user_id_1, user_1
    ) -> None:
        gameroom = Gameroom(
            id=gameroom_id,
            name="foobar",
            owner_id=user_id_1,
            status=GameroomStatus.RUNNING,
            game=None,
            users=(user_1,),
            created_at=datetime.now(),
        )
        with pytest.raises(NotEnoughPlayersError):
            sut.create_game(gameroom)

    def test_created_game_has_empty_board(self, sut, gameroom) -> None:
        result = sut.create_game(gameroom)

        assert result.game_state.board == Board()

    def test_created_game_has_players_created_from_users(self, sut, gameroom) -> None:
        result = sut.create_game(gameroom)

        assert result.game_state.players[0].user_id == gameroom.users[0].id
        assert result.game_state.players[1].user_id == gameroom.users[1].id

        assert result.game_state.players[0].name == gameroom.users[0].name
        assert result.game_state.players[1].name == gameroom.users[1].name

    def test_created_game_has_players_with_drawn_racks(self, sut, gameroom) -> None:
        result = sut.create_game(gameroom)

        assert result.game_state.players[0].rack == Tileset.create(
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
        )
        assert result.game_state.players[1].rack == Tileset.create(
            [14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]
        )

    def test_created_game_has_empty_list_of_made_meld_players(
        self, sut, gameroom
    ) -> None:
        result = sut.create_game(gameroom)

        assert result.made_meld == ()

    def test_created_game_has_correct_turn_order(self, sut, gameroom) -> None:
        result = sut.create_game(gameroom)

        assert result.turn_order == (gameroom.users[0].id, gameroom.users[1].id)

    def test_created_game_has_correct_turn(self, sut, gameroom) -> None:
        result = sut.create_game(gameroom)

        assert result.turn.starting_rack == Tileset.create(
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
        )
        assert result.turn.starting_board == Board()
        assert result.turn.revision == 0


class TestPerformMove:
    def test_when_candidate_has_duplicate_tiles__raises_duplicate_tiles_error(
        self, sut
    ) -> None:
        candidate = Board.create([[1, 2, 3], [1, 4, 8]])

        with pytest.raises(DuplicateTilesError):
            sut.perform_move(rack=Tileset(), current=Board(), candidate=candidate)

    def test_when_candidate_missing_tiles_from_current__raises_missing_board_tiles_error(
        self, sut
    ) -> None:
        current = Board.create([[4, 5, 6, 7]])
        candidate = Board.create([[1, 2, 3], [4, 5, 6]])

        with pytest.raises(MissingBoardTilesError):
            sut.perform_move(rack=Tileset(), current=current, candidate=candidate)

    def test_when_candidate_has_new_tiles_not_from_rack__raises_new_tiles_not_from_rack_error(  # noqa: E501
        self, sut
    ) -> None:
        rack = Tileset.create([4, 5])
        current = Board.create([[1, 2, 3]])
        candidate = Board.create([[1, 2, 3], [4, 5, 6]])

        with pytest.raises(NewTilesNotFromRackError):
            sut.perform_move(rack=rack, current=current, candidate=candidate)

    def test_when_move_valid__returns_rack_without_moved_tiles(self, sut) -> None:
        rack = Tileset.create([4, 5, 6, 7, 8])
        current = Board.create([[1, 2, 3]])
        candidate = Board.create([[1, 2, 3], [4, 5, 6]])
        expected = Tileset.create([7, 8])

        result, _ = sut.perform_move(rack=rack, current=current, candidate=candidate)

        assert result == expected

    def test_when_move_valid__returns_candidate_board(self, sut) -> None:
        rack = Tileset.create([4, 5, 6, 7, 8])
        current = Board.create([[1, 2, 3]])
        candidate = Board.create([[1, 2, 3], [4, 5, 6]])

        _, result = sut.perform_move(rack=rack, current=current, candidate=candidate)

        assert result == candidate


class TestEnsureBoardValid:
    @pytest.fixture()
    def turn(self) -> Turn:
        return create_autospec(Turn)

    @pytest.fixture()
    def game_state(self) -> GameState:
        return create_autospec(GameState)

    @pytest.fixture()
    def game(self, turn, game_state) -> Game:
        game = create_autospec(Game)
        type(game).turn = PropertyMock(return_value=turn)
        type(game).game_state = PropertyMock(return_value=game_state)
        return game

    def test_when_board_has_duplicate_tiles__raises_duplicate_tiles_error(
        self, sut, game, game_state, turn
    ) -> None:
        type(game_state).board = PropertyMock(
            return_value=Board.create([[1, 2, 3], [1, 4, 8]])
        )

        with pytest.raises(DuplicateTilesError):
            sut.ensure_board_valid(game)

    def test_when_board_missing_tiles_from_starting_board__raises_missing_board_tiles_error(  # noqa: E501
        self, sut, game, game_state, turn
    ) -> None:
        type(game_state).board = PropertyMock(
            return_value=Board.create([[1, 2, 3], [4, 5, 6]])
        )
        type(turn).starting_board = PropertyMock(
            return_value=Board.create([[4, 5, 6, 7]])
        )

        with pytest.raises(MissingBoardTilesError):
            sut.ensure_board_valid(game)

    def test_when_board_has_no_new_tiles_from_starting_board__raises_no_new_tiles_error(  # noqa: E501
        self, sut, game, game_state, turn
    ) -> None:
        type(game_state).board = PropertyMock(
            return_value=Board.create([[1, 2, 3], [4, 5, 6]])
        )
        type(turn).starting_board = PropertyMock(
            return_value=Board.create([[1, 2, 3], [4, 5, 6]])
        )

        with pytest.raises(NoNewTilesError):
            sut.ensure_board_valid(game)

    def test_when_candidate_has_new_tiles_not_from_rack__raises_new_tiles_not_from_rack_error(  # noqa: E501
        self, sut, game, game_state, turn
    ) -> None:
        type(game_state).board = PropertyMock(
            return_value=Board.create([[1, 2, 3], [4, 5, 6]])
        )
        type(turn).starting_board = PropertyMock(return_value=Board.create([[1, 2, 3]]))
        type(turn).starting_rack = PropertyMock(return_value=Tileset.create([4, 5]))

        with pytest.raises(NewTilesNotFromRackError):
            sut.ensure_board_valid(game)

    def test_when_board_has_invalid_tilesets__raises_invalid_tilesets_error(
        self, sut, tileset_service, game, game_state, turn
    ) -> None:
        def is_valid(tileset):
            if tileset == Tileset.create([4, 5, 8]):
                return False
            return True

        tileset_service.is_valid = Mock(side_effect=is_valid)

        type(game_state).board = PropertyMock(
            return_value=Board.create([[1, 2, 3], [4, 5, 8]])
        )
        type(turn).starting_board = PropertyMock(return_value=Board.create([[1, 2, 3]]))
        type(turn).starting_rack = PropertyMock(
            return_value=Tileset.create([4, 5, 6, 7, 8])
        )

        with pytest.raises(InvalidTilesetsError):
            sut.ensure_board_valid(game)


class TestEnsureMeldValid:
    def test_when_player_used_tiles_not_from_their_rack__raises_invalid_meld_error(
        self, sut
    ) -> None:
        rack = Tileset.create([5, 6, 7])
        previous = Board.create([[1, 2, 3, 4]])
        current = Board.create([[1, 2, 3], [4, 5, 6]])

        with pytest.raises(InvalidMeldError):
            sut.ensure_meld_valid(rack=rack, current=current, previous=previous)

    def test_when_value_of_played_tiles_is_less_than_minimum__raises_invalid_meld_error(
        self, sut, tileset_service
    ) -> None:
        rack = Tileset.create([4, 5, 6, 7, 8, 9])
        previous = Board.create([[1, 2, 3]])
        current = Board.create([[1, 2, 3], [4, 5, 6], [7, 8, 9]])

        tileset_service.value_of = Mock(return_value=1)

        with pytest.raises(InvalidMeldError):
            sut.ensure_meld_valid(rack=rack, current=current, previous=previous)

    def test_when_value_of_played_tiles_is_sufficent__does_not_raise_invalid_meld_error(
        self, sut, tileset_service
    ) -> None:
        rack = Tileset.create([4, 5, 6, 7, 8, 9])
        previous = Board.create([[1, 2, 3]])
        current = Board.create([[1, 2, 3], [4, 5, 6], [7, 8, 9]])

        tileset_service.value_of = Mock(return_value=15)  # min = 30, 2 * 15 == 30

        with not_raises(InvalidMeldError):
            sut.ensure_meld_valid(rack=rack, current=current, previous=previous)
