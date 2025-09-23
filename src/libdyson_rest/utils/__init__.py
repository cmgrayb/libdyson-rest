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


def get_api_hostname(country: str) -> str:
    """
    Determine the appropriate Dyson API hostname based on country code.

    This function maps country codes to their respective regional API endpoints.
    Currently only China (CN) has a dedicated regional endpoint.

    Args:
        country: ISO 3166-1 alpha-2 country code (e.g., 'US', 'CN', 'GB')

    Returns:
        The appropriate API hostname URL for the given country

    Examples:
        >>> get_api_hostname('CN')
        'https://appapi.cp.dyson.cn'
        >>> get_api_hostname('US')
        'https://appapi.cp.dyson.com'
        >>> get_api_hostname('GB')
        'https://appapi.cp.dyson.com'

    Note:
        This function provides automatic regional endpoint resolution. Countries with
        dedicated regional endpoints use their specific servers, while all others
        use the default global endpoint.
    """
    # Regional endpoint mappings for countries with dedicated API servers
    regional_endpoints = {
        "CN": "https://appapi.cp.dyson.cn",  # China
    }

    # Return regional endpoint if available, otherwise default to .com
    return regional_endpoints.get(country, "https://appapi.cp.dyson.com")
