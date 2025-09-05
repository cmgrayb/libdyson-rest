"""
Tests for validation utilities.

These tests cover the runtime validation functions used throughout the library
for safe JSON parsing and data extraction.
"""

from typing import Any, Dict
from uuid import UUID

import pytest

from libdyson_rest.validation import (
    JSONValidationError,
    safe_get_bool,
    safe_get_dict,
    safe_get_list,
    safe_get_optional_dict,
    safe_get_optional_list,
    safe_get_optional_str,
    safe_get_str,
    safe_parse_uuid,
    validate_json_response,
)


class TestJSONValidationError:
    """Test JSONValidationError exception."""

    def test_validation_error_creation(self) -> None:
        """Test creating JSONValidationError."""
        error = JSONValidationError("Test validation error")
        assert str(error) == "Test validation error"
        assert isinstance(error, Exception)


class TestSafeGetStr:
    """Test safe_get_str function."""

    def test_safe_get_str_success(self) -> None:
        """Test successful string extraction."""
        data = {"name": "test_value"}
        result = safe_get_str(data, "name")
        assert result == "test_value"

    def test_safe_get_str_with_field_path(self) -> None:
        """Test string extraction with field path."""
        data = {"name": "test_value"}
        result = safe_get_str(data, "name", "user")
        assert result == "test_value"

    def test_safe_get_str_missing_key(self) -> None:
        """Test string extraction with missing key."""
        data: Dict[str, Any] = {}
        with pytest.raises(JSONValidationError, match="Missing required field: name"):
            safe_get_str(data, "name")

    def test_safe_get_str_missing_key_with_path(self) -> None:
        """Test string extraction with missing key and field path."""
        data: Dict[str, Any] = {}
        with pytest.raises(JSONValidationError, match="Missing required field: user.name"):
            safe_get_str(data, "name", "user")

    def test_safe_get_str_wrong_type(self) -> None:
        """Test string extraction with wrong type."""
        data = {"name": 123}
        with pytest.raises(JSONValidationError, match="Expected str for name, got int"):
            safe_get_str(data, "name")

    def test_safe_get_str_none_value(self) -> None:
        """Test string extraction with None value."""
        data = {"name": None}
        with pytest.raises(JSONValidationError, match="Expected str for name, got NoneType"):
            safe_get_str(data, "name")


class TestSafeGetOptionalStr:
    """Test safe_get_optional_str function."""

    def test_safe_get_optional_str_success(self) -> None:
        """Test successful optional string extraction."""
        data = {"name": "test_value"}
        result = safe_get_optional_str(data, "name")
        assert result == "test_value"

    def test_safe_get_optional_str_missing_key(self) -> None:
        """Test optional string extraction with missing key."""
        data: Dict[str, Any] = {}
        result = safe_get_optional_str(data, "name")
        assert result is None

    def test_safe_get_optional_str_none_value(self) -> None:
        """Test optional string extraction with None value."""
        data = {"name": None}
        result = safe_get_optional_str(data, "name")
        assert result is None

    def test_safe_get_optional_str_wrong_type(self) -> None:
        """Test optional string extraction with wrong type."""
        data = {"name": 123}
        with pytest.raises(JSONValidationError, match="Expected str or None for name, got int"):
            safe_get_optional_str(data, "name")


class TestSafeGetBool:
    """Test safe_get_bool function."""

    def test_safe_get_bool_true(self) -> None:
        """Test successful bool extraction - True."""
        data = {"active": True}
        result = safe_get_bool(data, "active")
        assert result is True

    def test_safe_get_bool_false(self) -> None:
        """Test successful bool extraction - False."""
        data = {"active": False}
        result = safe_get_bool(data, "active")
        assert result is False

    def test_safe_get_bool_missing_key(self) -> None:
        """Test bool extraction with missing key."""
        data: Dict[str, Any] = {}
        with pytest.raises(JSONValidationError, match="Missing required field: active"):
            safe_get_bool(data, "active")

    def test_safe_get_bool_wrong_type(self) -> None:
        """Test bool extraction with wrong type."""
        data = {"active": "true"}
        with pytest.raises(JSONValidationError, match="Expected bool for active, got str"):
            safe_get_bool(data, "active")


class TestSafeGetList:
    """Test safe_get_list function."""

    def test_safe_get_list_success(self) -> None:
        """Test successful list extraction."""
        data = {"items": [1, 2, 3]}
        result = safe_get_list(data, "items")
        assert result == [1, 2, 3]

    def test_safe_get_list_empty(self) -> None:
        """Test list extraction with empty list."""
        data: Dict[str, Any] = {"items": []}
        result = safe_get_list(data, "items")
        assert result == []

    def test_safe_get_list_missing_key(self) -> None:
        """Test list extraction with missing key."""
        data: Dict[str, Any] = {}
        with pytest.raises(JSONValidationError, match="Missing required field: items"):
            safe_get_list(data, "items")

    def test_safe_get_list_wrong_type(self) -> None:
        """Test list extraction with wrong type."""
        data = {"items": "not_a_list"}
        with pytest.raises(JSONValidationError, match="Expected list for items, got str"):
            safe_get_list(data, "items")


class TestSafeGetOptionalList:
    """Test safe_get_optional_list function."""

    def test_safe_get_optional_list_success(self) -> None:
        """Test successful optional list extraction."""
        data = {"items": [1, 2, 3]}
        result = safe_get_optional_list(data, "items")
        assert result == [1, 2, 3]

    def test_safe_get_optional_list_missing_key(self) -> None:
        """Test optional list extraction with missing key."""
        data: Dict[str, Any] = {}
        result = safe_get_optional_list(data, "items")
        assert result is None

    def test_safe_get_optional_list_none_value(self) -> None:
        """Test optional list extraction with None value."""
        data = {"items": None}
        result = safe_get_optional_list(data, "items")
        assert result is None

    def test_safe_get_optional_list_wrong_type(self) -> None:
        """Test optional list extraction with wrong type."""
        data = {"items": "not_a_list"}
        with pytest.raises(JSONValidationError, match="Expected list or None for items, got str"):
            safe_get_optional_list(data, "items")


class TestSafeGetDict:
    """Test safe_get_dict function."""

    def test_safe_get_dict_success(self) -> None:
        """Test successful dict extraction."""
        data = {"config": {"key": "value"}}
        result = safe_get_dict(data, "config")
        assert result == {"key": "value"}

    def test_safe_get_dict_empty(self) -> None:
        """Test dict extraction with empty dict."""
        data: Dict[str, Any] = {"config": {}}
        result = safe_get_dict(data, "config")
        assert result == {}

    def test_safe_get_dict_missing_key(self) -> None:
        """Test dict extraction with missing key."""
        data: Dict[str, Any] = {}
        with pytest.raises(JSONValidationError, match="Missing required field: config"):
            safe_get_dict(data, "config")

    def test_safe_get_dict_wrong_type(self) -> None:
        """Test dict extraction with wrong type."""
        data = {"config": "not_a_dict"}
        with pytest.raises(JSONValidationError, match="Expected dict for config, got str"):
            safe_get_dict(data, "config")


class TestSafeGetOptionalDict:
    """Test safe_get_optional_dict function."""

    def test_safe_get_optional_dict_success(self) -> None:
        """Test successful optional dict extraction."""
        data = {"config": {"key": "value"}}
        result = safe_get_optional_dict(data, "config")
        assert result == {"key": "value"}

    def test_safe_get_optional_dict_missing_key(self) -> None:
        """Test optional dict extraction with missing key."""
        data: Dict[str, Any] = {}
        result = safe_get_optional_dict(data, "config")
        assert result is None

    def test_safe_get_optional_dict_none_value(self) -> None:
        """Test optional dict extraction with None value."""
        data = {"config": None}
        result = safe_get_optional_dict(data, "config")
        assert result is None

    def test_safe_get_optional_dict_wrong_type(self) -> None:
        """Test optional dict extraction with wrong type."""
        data = {"config": "not_a_dict"}
        with pytest.raises(JSONValidationError, match="Expected dict or None for config, got str"):
            safe_get_optional_dict(data, "config")


class TestSafeParseUUID:
    """Test safe_parse_uuid function."""

    def test_safe_parse_uuid_success(self) -> None:
        """Test successful UUID parsing."""
        uuid_str = "12345678-1234-5678-9abc-123456789abc"
        result = safe_parse_uuid(uuid_str)
        assert result == UUID(uuid_str)

    def test_safe_parse_uuid_with_field_path(self) -> None:
        """Test UUID parsing with field path."""
        uuid_str = "12345678-1234-5678-9abc-123456789abc"
        result = safe_parse_uuid(uuid_str, "user.id")
        assert result == UUID(uuid_str)

    def test_safe_parse_uuid_invalid_format(self) -> None:
        """Test UUID parsing with invalid UUID format."""
        with pytest.raises(JSONValidationError, match="Invalid UUID format for "):
            safe_parse_uuid("not-a-uuid")

    def test_safe_parse_uuid_invalid_format_with_path(self) -> None:
        """Test UUID parsing with invalid UUID format and field path."""
        with pytest.raises(JSONValidationError, match="Invalid UUID format for user.id"):
            safe_parse_uuid("not-a-uuid", "user.id")


class TestValidateJsonResponse:
    """Test validate_json_response function."""

    def test_validate_json_response_success(self) -> None:
        """Test successful JSON response validation."""
        data = {"key": "value"}
        result = validate_json_response(data, "TestModel")
        assert result == data

    def test_validate_json_response_not_dict(self) -> None:
        """Test JSON response validation with non-dict input."""
        with pytest.raises(JSONValidationError, match="Expected dict for TestModel, got str"):
            validate_json_response("not_a_dict", "TestModel")

    def test_validate_json_response_none(self) -> None:
        """Test JSON response validation with None input."""
        with pytest.raises(JSONValidationError, match="Expected dict for TestModel, got NoneType"):
            validate_json_response(None, "TestModel")

    def test_validate_json_response_list(self) -> None:
        """Test JSON response validation with list input."""
        with pytest.raises(JSONValidationError, match="Expected dict for TestModel, got list"):
            validate_json_response([1, 2, 3], "TestModel")
