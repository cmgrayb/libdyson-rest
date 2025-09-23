"""Tests for libdyson-rest utility functions."""

from libdyson_rest.utils import (
    decode_base64,
    encode_base64,
    get_api_hostname,
    hash_password,
    safe_json_loads,
    validate_email,
)


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


def test_get_api_hostname_regional_endpoints() -> None:
    """Test that known regional country codes return correct endpoints."""
    assert get_api_hostname("AU") == "https://appapi.cp.dyson.au"
    assert get_api_hostname("NZ") == "https://appapi.cp.dyson.nz"
    assert get_api_hostname("CN") == "https://appapi.cp.dyson.cn"


def test_get_api_hostname_default_fallback() -> None:
    """Test that unknown/default countries return the .com endpoint."""
    # US (default)
    assert get_api_hostname("US") == "https://appapi.cp.dyson.com"

    # Other countries without dedicated endpoints
    test_countries = ["GB", "DE", "FR", "CA", "JP", "KR", "IT", "ES"]
    for country in test_countries:
        result = get_api_hostname(country)
        assert result == "https://appapi.cp.dyson.com", f"Failed for {country}"


def test_get_api_hostname_edge_cases() -> None:
    """Test edge cases for API hostname resolution."""
    # Empty string
    assert get_api_hostname("") == "https://appapi.cp.dyson.com"

    # Invalid/malformed country codes
    invalid_codes = ["USA", "AUS", "123", "A", "ABC", "!@#", "XX"]
    for invalid_code in invalid_codes:
        result = get_api_hostname(invalid_code)
        assert result == "https://appapi.cp.dyson.com", f"Failed for {invalid_code}"


def test_get_api_hostname_case_sensitivity() -> None:
    """Test that country code matching is case-sensitive."""
    # Lowercase versions should fall back to default (exact match only)
    assert get_api_hostname("au") == "https://appapi.cp.dyson.com"
    assert get_api_hostname("nz") == "https://appapi.cp.dyson.com"
    assert get_api_hostname("cn") == "https://appapi.cp.dyson.com"

    # Only uppercase should match regional endpoints
    assert get_api_hostname("AU") == "https://appapi.cp.dyson.au"
    assert get_api_hostname("NZ") == "https://appapi.cp.dyson.nz"
    assert get_api_hostname("CN") == "https://appapi.cp.dyson.cn"


def test_get_api_hostname_deterministic() -> None:
    """Test that the function returns consistent results."""
    test_inputs = ["AU", "US", "GB", "CN", "NZ", "XX"]

    for country in test_inputs:
        result1 = get_api_hostname(country)
        result2 = get_api_hostname(country)
        assert result1 == result2, f"Function not deterministic for {country}"
