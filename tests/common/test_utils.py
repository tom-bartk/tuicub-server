from werkzeug.datastructures import Headers

from src.tuicubserver.common.utils import is_host_valid, parse_token


class TestParseToken:
    def test_when_no_authorization_header__returns_empty_string(self) -> None:
        headers = Headers((("Host", "localhost"),))
        expected = ""

        result = parse_token(headers)

        assert result == expected

    def test_when_authorization_header_does_not_start_w_bearer__returns_empty_string(
        self,
    ) -> None:
        headers = Headers((("Host", "localhost"), ("Authorization", "letmein")))
        expected = ""

        result = parse_token(headers)

        assert result == expected

    def test_when_authorization_header_has_valid_bearer__returns_value_after_bearer(
        self,
    ) -> None:
        headers = Headers((("Host", "localhost"), ("Authorization", "Bearer letmein")))
        expected = "letmein"

        result = parse_token(headers)

        assert result == expected


class TestIsHostValid:
    def test_when_host_is_valid_ipv4__returns_true(self) -> None:
        expected = True

        result = is_host_valid("192.168.42.13")

        assert result == expected

    def test_when_host_is_valid_ipv6__returns_true(self) -> None:
        expected = True

        result = is_host_valid("2001:0db8:85a3:0000:0000:8a2e:0370:7334")

        assert result == expected

    def test_when_host_is_localhost__returns_true(self) -> None:
        expected = True

        result = is_host_valid("localhost")

        assert result == expected

    def test_when_host_is_valid_fqdn__returns_true(self) -> None:
        expected = True

        result = is_host_valid("api.tuicub.com.")

        assert result == expected

    def test_when_host_is_invalid_ipv4__returns_false(self) -> None:
        expected = False

        result = is_host_valid("192.168.42")

        assert result == expected

    def test_when_host_is_invalid_ipv6__returns_false(self) -> None:
        expected = False

        result = is_host_valid("zzzz:0db8:85a3:0000:0000:8a2e:0370:7334")

        assert result == expected

    def test_when_host_is_invalid_fqdn__returns_false(self) -> None:
        expected = False

        result = is_host_valid("api.tuicub.com;sleep 1")

        assert result == expected

    def test_when_host_is_longer_than_253_chars__returns_false(self) -> None:
        expected = False
        host = (
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        )

        result = is_host_valid(host)

        assert result == expected
