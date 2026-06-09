"""Tests for libdyson-rest exceptions."""

from libdyson_rest.exceptions import (
    DysonAPIError,
    DysonAuthError,
    DysonConnectionError,
    DysonDeviceError,
    DysonValidationError,
)


def test_dyson_api_error() -> None:
    """Test DysonAPIError exception."""
    error = DysonAPIError("Test error")
    assert str(error) == "Test error"
    assert isinstance(error, Exception)
    assert error.raw is None


def test_dyson_api_error_with_raw() -> None:
    """Test DysonAPIError exception with raw response body."""
    raw_body = '{"items": [1, 2, 3]}'
    error = DysonAPIError("Unexpected format", raw=raw_body)
    assert str(error) == "Unexpected format"
    assert error.raw == raw_body


def test_dyson_connection_error() -> None:
    """Test DysonConnectionError exception."""
    error = DysonConnectionError("Connection failed")
    assert str(error) == "Connection failed"
    assert isinstance(error, DysonAPIError)


def test_dyson_auth_error() -> None:
    """Test DysonAuthError exception."""
    error = DysonAuthError("Authentication failed")
    assert str(error) == "Authentication failed"
    assert isinstance(error, DysonAPIError)


def test_dyson_device_error() -> None:
    """Test DysonDeviceError exception."""
    error = DysonDeviceError("Device error")
    assert str(error) == "Device error"
    assert isinstance(error, DysonAPIError)


def test_dyson_validation_error() -> None:
    """Test DysonValidationError exception."""
    error = DysonValidationError("Validation failed")
    assert str(error) == "Validation failed"
    assert isinstance(error, DysonAPIError)
