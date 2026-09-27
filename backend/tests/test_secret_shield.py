"""Tests for the Secret Shield masking utility (services/secret_shield.py)."""

from app.services.secret_shield import (
    contains_secret,
    contains_secret_in_metadata,
    mask_metadata,
    mask_string,
)

_MASK = "[REDACTED]"


class TestMaskString:
    """Unit tests for mask_string."""

    def test_jwt_token_masked(self) -> None:
        # Valid JWT: header.payload.signature
        jwt = (
            "eyJhbGciOiJIUzI1NiJ9"
            ".eyJzdWIiOiJ1c2VyIn0"
            ".SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        )
        result = mask_string(jwt)
        assert _MASK in result
        assert "eyJ" not in result

    def test_aws_access_key_masked(self) -> None:
        result = mask_string("key=AKIAIOSFODNN7EXAMPLE")
        assert _MASK in result

    def test_github_token_masked(self) -> None:
        result = mask_string("token=ghp_abcdefghijklmnopqrstuvwxyz1234567890abcde")
        assert _MASK in result

    def test_bearer_token_masked(self) -> None:
        result = mask_string("Authorization: Bearer mySecretToken123")
        assert _MASK in result

    def test_password_masked(self) -> None:
        result = mask_string("password=my_secret_password")
        assert _MASK in result

    def test_oauth_token_masked(self) -> None:
        result = mask_string("access_token=abc123xyz789abcdef")
        assert _MASK in result

    def test_api_key_masked(self) -> None:
        result = mask_string("api_key=abcdef1234567890abcdef12")
        assert _MASK in result

    def test_cookie_masked(self) -> None:
        result = mask_string("Cookie: session=abc123; user=bob")
        assert _MASK in result

    def test_ssh_private_key_masked(self) -> None:
        pem = (
            "-----BEGIN RSA PRIVATE KEY-----\n"
            "MIIEowIBAAK\n"
            "-----END RSA PRIVATE KEY-----"
        )
        result = mask_string(pem)
        assert _MASK in result

    def test_safe_string_unchanged(self) -> None:
        safe = "function add(a, b) { return a + b; }"
        assert mask_string(safe) == safe

    def test_empty_string_unchanged(self) -> None:
        assert mask_string("") == ""

    def test_multiple_secrets_all_masked(self) -> None:
        text = "api_key=secret123456789abcdef and password=hunter2"
        result = mask_string(text)
        assert result.count(_MASK) >= 2


class TestMaskMetadata:
    """Unit tests for mask_metadata."""

    def test_string_value_masked(self) -> None:
        result = mask_metadata({"token": "ghp_abcdefghijklmnopqrstuvwxyz1234567890"})
        assert _MASK in result["token"]

    def test_safe_value_preserved(self) -> None:
        result = mask_metadata({"language": "python"})
        assert result["language"] == "python"

    def test_nested_dict_masked(self) -> None:
        result = mask_metadata({"headers": {"auth": "Bearer secrettoken123"}})
        assert _MASK in result["headers"]["auth"]

    def test_list_values_masked(self) -> None:
        result = mask_metadata(
            {"lines": ["api_key=12345678901234567890abcdef", "safe"]}
        )
        assert _MASK in result["lines"][0]
        assert result["lines"][1] == "safe"

    def test_integer_values_passed_through(self) -> None:
        result = mask_metadata({"count": 42})
        assert result["count"] == 42

    def test_input_not_mutated(self) -> None:
        original = {"key": "api_key=supersecret123456789012345"}
        mask_metadata(original)
        assert "api_key" in original["key"]  # original unchanged

    def test_empty_dict_returns_empty_dict(self) -> None:
        assert mask_metadata({}) == {}


class TestContainsSecret:
    """Unit tests for contains_secret."""

    def test_detects_jwt(self) -> None:
        jwt = (
            "eyJhbGciOiJIUzI1NiJ9"
            ".eyJzdWIiOiJ1c2VyIn0"
            ".SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        )
        assert contains_secret(jwt) is True

    def test_detects_github_token(self) -> None:
        assert contains_secret("ghp_abcdefghijklmnopqrstuvwxyz1234567890abcde") is True

    def test_safe_string_returns_false(self) -> None:
        assert contains_secret("import os; os.path.join('a', 'b')") is False

    def test_empty_string_returns_false(self) -> None:
        assert contains_secret("") is False


class TestContainsSecretInMetadata:
    """Unit tests for contains_secret_in_metadata."""

    def test_detects_secret_in_top_level_value(self) -> None:
        assert (
            contains_secret_in_metadata(
                {"token": "ghp_abcdefghijklmnopqrstuvwxyz1234567890"}
            )
            is True
        )

    def test_detects_secret_in_nested_value(self) -> None:
        assert contains_secret_in_metadata({"h": {"auth": "Bearer tok123"}}) is True

    def test_safe_metadata_returns_false(self) -> None:
        assert contains_secret_in_metadata({"language": "python", "lines": 42}) is False

    def test_empty_metadata_returns_false(self) -> None:
        assert contains_secret_in_metadata({}) is False
