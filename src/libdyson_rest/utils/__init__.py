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
    Known regional endpoints include Australia (AU), New Zealand (NZ), and China (CN).
    All other countries, including the United States (US), use the default endpoint.

    Args:
        country: ISO 3166-1 alpha-2 country code (e.g., 'US', 'AU', 'NZ', 'CN')

    Returns:
        The appropriate API hostname URL for the given country

    Examples:
        >>> get_api_hostname('AU')
        'https://appapi.cp.dyson.au'
        >>> get_api_hostname('US')
        'https://appapi.cp.dyson.com'
        >>> get_api_hostname('GB')  # Unknown region defaults to .com
        'https://appapi.cp.dyson.com'

    Note:
        This function provides automatic regional endpoint resolution for improved
        connectivity in regions with dedicated Dyson API servers. Countries without
        dedicated endpoints gracefully fall back to the primary .com endpoint.
    """
    # Regional endpoint mappings for countries with dedicated API servers
    regional_endpoints = {
        "AU": "https://appapi.cp.dyson.au",  # Australia
        "NZ": "https://appapi.cp.dyson.nz",  # New Zealand
        "CN": "https://appapi.cp.dyson.cn",  # China
    }

    # Return regional endpoint if available, otherwise default to .com
    return regional_endpoints.get(country, "https://appapi.cp.dyson.com")
