"""Utility functions for libdyson-rest."""

import base64
import hashlib
import json
from typing import Any, Dict


def validate_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email address to validate

    Returns:
        True if email format is valid, False otherwise
    """
    import re

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def hash_password(password: str) -> str:
    """
    Hash a password for secure storage.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return hashlib.sha256(password.encode()).hexdigest()


def encode_base64(data: str) -> str:
    """
    Encode string to base64.

    Args:
        data: String to encode

    Returns:
        Base64 encoded string
    """
    return base64.b64encode(data.encode()).decode()


def decode_base64(data: str) -> str:
    """
    Decode base64 string.

    Args:
        data: Base64 encoded string

    Returns:
        Decoded string
    """
    return base64.b64decode(data.encode()).decode()


def safe_json_loads(data: str) -> Dict[str, Any]:
    """
    Safely load JSON data with error handling.

    Args:
        data: JSON string to parse

    Returns:
        Parsed JSON data or empty dict if parsing fails
    """
    try:
        result = json.loads(data)
        return result if isinstance(result, dict) else {}
    except json.JSONDecodeError:
        return {}
