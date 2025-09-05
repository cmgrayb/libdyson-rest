"""
JSON validation utilities for type-safe API response parsing.

These utilities provide runtime validation of JSON responses to ensure
they match expected TypedDict schemas.
"""

import logging
from typing import Any, Dict, TypeVar
from uuid import UUID

logger = logging.getLogger(__name__)

T = TypeVar("T")


class JSONValidationError(Exception):
    """Raised when JSON response doesn't match expected schema."""

    pass


def safe_get_str(data: Dict[str, Any], key: str, field_path: str = "") -> str:
    """
    Safely extract string from dict with runtime validation.

    Args:
        data: Dictionary to extract from
        key: Key to extract
        field_path: Path for error reporting

    Returns:
        String value

    Raises:
        JSONValidationError: If value is not a string or missing
    """
    full_path = f"{field_path}.{key}" if field_path else key

    if key not in data:
        raise JSONValidationError(f"Missing required field: {full_path}")

    value = data[key]
    if not isinstance(value, str):
        raise JSONValidationError(
            f"Expected str for {full_path}, got {type(value).__name__}"
        )

    return value


def safe_get_optional_str(
    data: Dict[str, Any], key: str, field_path: str = ""
) -> str | None:
    """
    Safely extract optional string from dict.

    Args:
        data: Dictionary to extract from
        key: Key to extract
        field_path: Path for error reporting

    Returns:
        String value or None

    Raises:
        JSONValidationError: If value exists but is not a string
    """
    full_path = f"{field_path}.{key}" if field_path else key

    if key not in data:
        return None

    value = data[key]
    if value is None:
        return None

    if not isinstance(value, str):
        raise JSONValidationError(
            f"Expected str or None for {full_path}, got {type(value).__name__}"
        )

    return value


def safe_get_bool(data: Dict[str, Any], key: str, field_path: str = "") -> bool:
    """
    Safely extract boolean from dict with runtime validation.

    Args:
        data: Dictionary to extract from
        key: Key to extract
        field_path: Path for error reporting

    Returns:
        Boolean value

    Raises:
        JSONValidationError: If value is not a boolean or missing
    """
    full_path = f"{field_path}.{key}" if field_path else key

    if key not in data:
        raise JSONValidationError(f"Missing required field: {full_path}")

    value = data[key]
    if not isinstance(value, bool):
        raise JSONValidationError(
            f"Expected bool for {full_path}, got {type(value).__name__}"
        )

    return value


def safe_get_list(data: Dict[str, Any], key: str, field_path: str = "") -> list[Any]:
    """
    Safely extract list from dict with runtime validation.

    Args:
        data: Dictionary to extract from
        key: Key to extract
        field_path: Path for error reporting

    Returns:
        List value

    Raises:
        JSONValidationError: If value is not a list or missing
    """
    full_path = f"{field_path}.{key}" if field_path else key

    if key not in data:
        raise JSONValidationError(f"Missing required field: {full_path}")

    value = data[key]
    if not isinstance(value, list):
        raise JSONValidationError(
            f"Expected list for {full_path}, got {type(value).__name__}"
        )

    return value


def safe_get_optional_list(
    data: Dict[str, Any], key: str, field_path: str = ""
) -> list[Any] | None:
    """
    Safely extract optional list from dict.

    Args:
        data: Dictionary to extract from
        key: Key to extract
        field_path: Path for error reporting

    Returns:
        List value or None

    Raises:
        JSONValidationError: If value exists but is not a list
    """
    full_path = f"{field_path}.{key}" if field_path else key

    if key not in data:
        return None

    value = data[key]
    if value is None:
        return None

    if not isinstance(value, list):
        raise JSONValidationError(
            f"Expected list or None for {full_path}, got {type(value).__name__}"
        )

    return value


def safe_get_dict(
    data: Dict[str, Any], key: str, field_path: str = ""
) -> Dict[str, Any]:
    """
    Safely extract nested dict from dict with runtime validation.

    Args:
        data: Dictionary to extract from
        key: Key to extract
        field_path: Path for error reporting

    Returns:
        Dictionary value

    Raises:
        JSONValidationError: If value is not a dict or missing
    """
    full_path = f"{field_path}.{key}" if field_path else key

    if key not in data:
        raise JSONValidationError(f"Missing required field: {full_path}")

    value = data[key]
    if not isinstance(value, dict):
        raise JSONValidationError(
            f"Expected dict for {full_path}, got {type(value).__name__}"
        )

    return value


def safe_get_optional_dict(
    data: Dict[str, Any], key: str, field_path: str = ""
) -> Dict[str, Any] | None:
    """
    Safely extract optional nested dict from dict.

    Args:
        data: Dictionary to extract from
        key: Key to extract
        field_path: Path for error reporting

    Returns:
        Dictionary value or None

    Raises:
        JSONValidationError: If value exists but is not a dict
    """
    full_path = f"{field_path}.{key}" if field_path else key

    if key not in data:
        return None

    value = data[key]
    if value is None:
        return None

    if not isinstance(value, dict):
        raise JSONValidationError(
            f"Expected dict or None for {full_path}, got {type(value).__name__}"
        )

    return value


def safe_parse_uuid(value: str, field_path: str = "") -> UUID:
    """
    Safely parse UUID string.

    Args:
        value: String to parse as UUID
        field_path: Path for error reporting

    Returns:
        UUID object

    Raises:
        JSONValidationError: If string is not a valid UUID
    """
    try:
        return UUID(value)
    except ValueError as e:
        raise JSONValidationError(
            f"Invalid UUID format for {field_path}: {value}"
        ) from e


def validate_json_response(
    response_data: Any, field_path: str = "response"
) -> Dict[str, Any]:
    """
    Validate that response data is a dictionary.

    Args:
        response_data: Raw response data from JSON parsing
        field_path: Path for error reporting

    Returns:
        Validated dictionary

    Raises:
        JSONValidationError: If response is not a dictionary
    """
    if not isinstance(response_data, dict):
        raise JSONValidationError(
            f"Expected dict for {field_path}, got {type(response_data).__name__}"
        )

    return response_data
