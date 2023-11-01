from unittest.mock import Mock

import pytest

from src.tuicubserver.common.context import Context
from src.tuicubserver.common.errors import UnauthorizedError, ValidationError
from src.tuicubserver.controllers.gamerooms import SUCCESS_RESPONSE, GameroomsController
from src.tuicubserver.models.dto import GameDto, GameroomDto
from src.tuicubserver.services.gamerooms import DeleteGameroomResult, DisconnectResult
from src.tuicubserver.services.games import GameDisconnectResult


@pytest.fixture()
def sut(
    auth_service, gamerooms_service, games_service, users_service, messages_service
) -> GameroomsController:
    return GameroomsController(
        auth_service=auth_service,
        gamerooms_service=gamerooms_service,
        games_service=games_service,
        users_service=users_service,
        messages_service=messages_service,
    )


class TestCreateGameroom:
    def test_returns_serialized_gameroom(self, sut, context, gamerooms_service, gameroom):
        gamerooms_service.create_gameroom = Mock(return_value=gameroom)
        expected = GameroomDto.create(gameroom).serialize()

        result = sut.create_gameroom(context=context)

        assert result == expected

    def test_passes_context_to_service(self, sut, context, gamerooms_service, gameroom):
        gamerooms_service.create_gameroom = Mock(return_value=gameroom)

        sut.create_gameroom(context=context)

        gamerooms_service.create_gameroom.assert_called_once_with(context=context)


class TestGetGamerooms:
    def test_returns_serialized_gamerooms(
        self, sut, context, gamerooms_service, gameroom
    ):
        gamerooms_service.get_gamerooms = Mock(return_value=[gameroom, gameroom])
        expected = [
            GameroomDto.create(gameroom).serialize(),
            GameroomDto.create(gameroom).serialize(),
        ]

        result = sut.get_gamerooms(context=context)

        assert result == expected

    def test_passes_context_to_service(self, sut, context, gamerooms_service, gameroom):
        gamerooms_service.get_gamerooms = Mock(return_value=[gameroom])

        sut.get_gamerooms(context=context)

        gamerooms_service.get_gamerooms.assert_called_once_with(context=context)


class TestJoinGameroom:
    def test_returns_serialized_gameroom(self, sut, context, gamerooms_service, gameroom):
        gamerooms_service.join_gameroom = Mock(return_value=gameroom)
        expected = GameroomDto.create(gameroom).serialize()

        result = sut.join_gameroom(context=context, id="foo")

        assert result == expected

    def test_passes_context_to_service(self, sut, context, gamerooms_service, gameroom):
        gamerooms_service.join_gameroom = Mock(return_value=gameroom)

        sut.join_gameroom(context=context, id="foo")

        gamerooms_service.join_gameroom.assert_called_once_with(
            context=context, gameroom_id="foo"
        )

    def test_sends_user_joined_message(
        self, sut, gamerooms_service, gameroom, messages_service, create_context, user
    ) -> None:
        context: Context = create_context(user=user)
        gamerooms_service.join_gameroom = Mock(return_value=gameroom)

        sut.join_gameroom(context=context, id="foo")

        messages_service.user_joined.assert_called_once_with(
            sender=user, gameroom=gameroom
        )


class TestLeaveGameroom:
    def test_returns_serialized_gameroom(self, sut, context, gamerooms_service, gameroom):
        gamerooms_service.leave_gameroom = Mock(return_value=gameroom)
        expected = GameroomDto.create(gameroom).serialize()

        result = sut.leave_gameroom(context=context, id="foo")

        assert result == expected

    def test_passes_context_to_service(self, sut, context, gamerooms_service, gameroom):
        gamerooms_service.leave_gameroom = Mock(return_value=gameroom)

        sut.leave_gameroom(context=context, id="foo")

        gamerooms_service.leave_gameroom.assert_called_once_with(
            context=context, gameroom_id="foo"
        )

    def test_sends_user_left_message(
        self, sut, gamerooms_service, gameroom, messages_service, create_context, user
    ) -> None:
        context: Context = create_context(user=user)
        gamerooms_service.leave_gameroom = Mock(return_value=gameroom)

        sut.leave_gameroom(context=context, id="foo")

        messages_service.user_left.assert_called_once_with(sender=user, gameroom=gameroom)


class TestDeleteGameroom:
    def test_returns_serialized_gameroom(self, sut, context, gamerooms_service, gameroom):
        gamerooms_service.delete_gameroom = Mock(
            return_value=DeleteGameroomResult(gameroom=gameroom, remaining_users=())
        )
        expected = GameroomDto.create(gameroom).serialize()

        result = sut.delete_gameroom(context=context, id="foo")

        assert result == expected

    def test_passes_context_to_service(self, sut, context, gamerooms_service, gameroom):
        gamerooms_service.delete_gameroom = Mock(
            return_value=DeleteGameroomResult(gameroom=gameroom, remaining_users=())
        )

        sut.delete_gameroom(context=context, id="foo")

        gamerooms_service.delete_gameroom.assert_called_once_with(
            context=context, gameroom_id="foo"
        )

    def test_sends_gameroom_deleted_message(
        self, sut, gamerooms_service, gameroom, messages_service, create_context, user
    ) -> None:
        context: Context = create_context(user=user)
        result = DeleteGameroomResult(gameroom=gameroom, remaining_users=())
        gamerooms_service.delete_gameroom = Mock(return_value=result)

        sut.delete_gameroom(context=context, id="foo")

        messages_service.gameroom_deleted.assert_called_once_with(
            sender=user, gameroom=result.gameroom, remaining_users=result.remaining_users
        )


class TestStartGame:
    def test_returns_serialized_game(self, sut, context, gamerooms_service, game, user):
        gamerooms_service.start_game = Mock(return_value=game)
        expected = GameDto.create(game, user).serialize()

        result = sut.start_game(context=context, id="foo")

        assert result == expected

    def test_passes_context_to_service(self, sut, context, gamerooms_service, game):
        gamerooms_service.start_game = Mock(return_value=game)

        sut.start_game(context=context, id="foo")

        gamerooms_service.start_game.assert_called_once_with(
            context=context, gameroom_id="foo"
        )

    def test_sends_game_started_message(
        self, sut, gamerooms_service, game, messages_service, create_context, user
    ) -> None:
        context: Context = create_context(user=user)
        gamerooms_service.start_game = Mock(return_value=game)

        sut.start_game(context=context, id="foo")

        messages_service.game_started.assert_called_once_with(sender=user, game=game)


class TestDisconnect:
    def test_when_authorization_fails__does_not_disconnect(
        self, sut, app, base_context, user_id, auth_service, gamerooms_service
    ):
        auth_service.authorize_events_server = Mock(side_effect=UnauthorizedError)

        with app.test_request_context(
            json={"user_id": str(user_id)}, headers={"Authorization": "Bearer token"}
        ):
            with pytest.raises(UnauthorizedError):
                sut.disconnect(context=base_context)

            auth_service.authorize_events_server.assert_called_once()
            gamerooms_service.disconnect.assert_not_called()

    def test_when_result_has_no_gameroom__does_not_send_disconnected_gameroom_message(
        self, sut, app, base_context, user_id, gamerooms_service, messages_service
    ):
        gamerooms_service.disconnect = Mock(return_value=DisconnectResult())

        with app.test_request_context(json={"user_id": str(user_id)}):
            result = sut.disconnect(context=base_context)

            messages_service.disconnected_gameroom.assert_not_called()
            assert result == SUCCESS_RESPONSE

    def test_when_result_has_gameroom_no_game__sends_disconnected_gameroom_message(
        self,
        sut,
        app,
        base_context,
        user,
        user_id,
        gamerooms_service,
        messages_service,
        users_service,
    ):
        expected = DisconnectResult(gameroom=Mock())
        gamerooms_service.disconnect = Mock(return_value=expected)
        users_service.get_user_by_id = Mock(return_value=user)

        with app.test_request_context(json={"user_id": str(user_id)}):
            result = sut.disconnect(context=base_context)

            messages_service.disconnected_gameroom.assert_called_once_with(
                sender=user, result=expected
            )
            assert result == SUCCESS_RESPONSE

    def test_when_result_has_gameroom_and_game__sends_disconnected_game_message(
        self,
        sut,
        app,
        base_context,
        user,
        user_id,
        gamerooms_service,
        messages_service,
        users_service,
        games_service,
    ):
        expected = GameDisconnectResult(game=Mock(), player=Mock())
        gamerooms_service.disconnect = Mock(
            return_value=DisconnectResult(gameroom=Mock(), game=Mock())
        )
        games_service.disconnect = Mock(return_value=expected)
        users_service.get_user_by_id = Mock(return_value=user)

        with app.test_request_context(json={"user_id": str(user_id)}):
            sut.disconnect(context=base_context)

            messages_service.disconnected_game.assert_called_once_with(
                sender=user, result=expected
            )

    def test_when_result_has_gameroom_and_game_with_winner__finishes_games(
        self,
        sut,
        app,
        base_context,
        user,
        user_id,
        gamerooms_service,
        messages_service,
        users_service,
        games_service,
    ):
        expected = GameDisconnectResult(game=Mock(), player=Mock())
        gamerooms_service.disconnect = Mock(
            return_value=DisconnectResult(gameroom=Mock(), game=Mock())
        )
        games_service.disconnect = Mock(return_value=expected)
        users_service.get_user_by_id = Mock(return_value=user)

        with app.test_request_context(json={"user_id": str(user_id)}):
            sut.disconnect(context=base_context)

            gamerooms_service.finish_game.assert_called_once()

    def test_queries_user_by_id_from_body(
        self, sut, app, base_context, user, user_id, users_service
    ):
        with app.test_request_context(json={"user_id": str(user_id)}):
            sut.disconnect(context=base_context)

            users_service.get_user_by_id.assert_called_once_with(
                session=base_context.session, user_id=user_id
            )

    def test_when_user_id_not_in_body__raises_validation_error(
        self, sut, app, base_context
    ) -> None:
        with app.test_request_context(json={}):
            with pytest.raises(ValidationError, match="A valid 'user_id' is required"):
                sut.disconnect(context=base_context)

    def test_when_user_id_has_invalid_format__raises_validation_error(
        self, sut, app, base_context
    ) -> None:
        with app.test_request_context(json={"user_id": "foo"}):
            with pytest.raises(ValidationError, match="Not a valid UUID"):
                sut.disconnect(context=base_context)
