"""
libdyson-rest: Python library for interacting with the Dyson REST API.

This library provides a clean interface for communicating with Dyson devices
through their REST API endpoints.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .client import DysonClient
from .exceptions import DysonAPIError, DysonAuthError, DysonConnectionError

__all__ = [
    "DysonClient",
    "DysonAPIError",
    "DysonAuthError",
    "DysonConnectionError",
]
