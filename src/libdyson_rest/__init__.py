"""
libdyson-rest: Python library for interacting with the Dyson REST API.

This library provides a clean interface for communicating with Dyson devices
through their official REST API endpoints as documented in the OpenAPI specification.

Key Features:
- Full OpenAPI specification compliance
- Two-step authentication with OTP codes
- Complete device management and IoT credentials
- Type-safe data models
- Comprehensive error handling
- Context manager support

Basic Usage:
    from libdyson_rest import DysonClient

    client = DysonClient(email="your@email.com", password="password")

    # Two-step authentication
    challenge = client.begin_login()
    # Check email for OTP code
    login_info = client.complete_login(str(challenge.challenge_id), "123456")

    # Get devices
    devices = client.get_devices()
    for device in devices:
        print(f"Device: {device.name} ({device.serial_number})")
"""

__version__ = "0.5.0"
__author__ = "libdyson-rest contributors"
__email__ = "contributors@libdyson-rest.dev"

from .client import DysonClient
from .exceptions import (
    DysonAPIError,
    DysonAuthError,
    DysonConnectionError,
    DysonDeviceError,
    DysonValidationError,
)
from .models import (
    ConnectionCategory,
    Device,
    DeviceCategory,
    IoTData,
    LoginChallenge,
    LoginInformation,
    UserStatus,
)

__all__ = [
    # Core client
    "DysonClient",
    # Exceptions
    "DysonAPIError",
    "DysonAuthError",
    "DysonConnectionError",
    "DysonDeviceError",
    "DysonValidationError",
    # Key models
    "Device",
    "DeviceCategory",
    "ConnectionCategory",
    "IoTData",
    "LoginChallenge",
    "LoginInformation",
    "UserStatus",
]
