"""
Custom exceptions for libdyson-rest.
"""


class DysonAPIError(Exception):
    """Base exception for all Dyson API related errors."""

    pass


class DysonConnectionError(DysonAPIError):
    """Raised when connection to Dyson API fails."""

    pass


class DysonAuthError(DysonAPIError):
    """Raised when authentication with Dyson API fails."""

    pass


class DysonDeviceError(DysonAPIError):
    """Raised when device operation fails."""

    pass


class DysonValidationError(DysonAPIError):
    """Raised when input validation fails."""

    pass
