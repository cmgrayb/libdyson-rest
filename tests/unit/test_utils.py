"""Tests for libdyson-rest utility functions."""

from libdyson_rest.utils import decode_base64, encode_base64, hash_password, safe_json_loads, validate_email


def test_validate_email() -> None:
    """Test email validation function."""
    assert validate_email("test@example.com") is True
    assert validate_email("user.name@domain.co.uk") is True
    assert validate_email("invalid.email") is False
    assert validate_email("@domain.com") is False
    assert validate_email("test@") is False


def test_hash_password() -> None:
    """Test password hashing function."""
    password = "test_password"
    hashed = hash_password(password)

    assert isinstance(hashed, str)
    assert len(hashed) == 64  # SHA256 hex string length
    assert hashed != password
    assert hash_password(password) == hashed  # Same input, same output


def test_encode_decode_base64() -> None:
    """Test base64 encoding and decoding."""
    test_string = "Hello, World!"
    encoded = encode_base64(test_string)
    decoded = decode_base64(encoded)

    assert isinstance(encoded, str)
    assert decoded == test_string


def test_safe_json_loads() -> None:
    """Test safe JSON loading function."""
    # Valid JSON
    valid_json = '{"key": "value", "number": 42}'
    result = safe_json_loads(valid_json)
    assert result == {"key": "value", "number": 42}

    # Invalid JSON
    invalid_json = '{"key": "value"'
    result = safe_json_loads(invalid_json)
    assert result == {}

    # Empty string
    result = safe_json_loads("")
    assert result == {}

    # Non-dict JSON (should return empty dict)
    array_json = "[1, 2, 3]"
    result = safe_json_loads(array_json)
    assert result == {}
