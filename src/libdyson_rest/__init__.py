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
- Both synchronous and asynchronous client support

Basic Usage (Synchronous):
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

Basic Usage (Asynchronous):
    from libdyson_rest import AsyncDysonClient

    async def main():
        async with AsyncDysonClient(
            email="your@email.com", password="password"
        ) as client:
            # Two-step authentication
            challenge = await client.begin_login()
            # Check email for OTP code
            login_info = await client.complete_login(
                str(challenge.challenge_id), "123456"
            )

            # Get devices
            devices = await client.get_devices()
            for device in devices:
                print(f"Device: {device.name} ({device.serial_number})")
"""

__version__ = "0.14.0b2"
__author__ = "Christopher Gray"
__email__ = "79777799+cmgrayb@users.noreply.github.com"

from contextlib import suppress

from .client import DysonClient

# Conditionally import async client (requires httpx)
with suppress(ImportError):
    from .async_client import AsyncDysonClient
from .exceptions import (
    DysonAPIError,
    DysonAuthError,
    DysonConnectionError,
    DysonDeviceError,
    DysonValidationError,
)
from .models import (
    CleanedFootprint,
    CleaningProgramme,
    CleaningStrategy,
    CleanMapPosition,
    CleanRecord,
    CleanTimelineEvent,
    ConnectionCategory,
    DailyAirQualityData,
    Device,
    DeviceCategory,
    DustMapData,
    IoTData,
    LoginChallenge,
    LoginInformation,
    OutdoorAirQualityData,
    PendingRelease,
    PersistentMap,
    PersistentMapMeta,
    RecommendedCleanMap,
    ScheduledEvent,
    ScheduledEventsData,
    UserStatus,
    ZoneDustBreakdown,
    ZoneMeta,
    ZonePrediction,
)

__all__ = [
    # Core clients
    "DysonClient",
    "AsyncDysonClient",
    # Exceptions
    "DysonAPIError",
    "DysonAuthError",
    "DysonConnectionError",
    "DysonDeviceError",
    "DysonValidationError",
    # Core device models
    "Device",
    "DeviceCategory",
    "ConnectionCategory",
    "IoTData",
    "LoginChallenge",
    "LoginInformation",
    "PendingRelease",
    "UserStatus",
    # Vis Nav robot models
    "CleanedFootprint",
    "CleaningProgramme",
    "CleaningStrategy",
    "CleanMapPosition",
    "CleanRecord",
    "CleanTimelineEvent",
    "DustMapData",
    "PersistentMap",
    "PersistentMapMeta",
    "RecommendedCleanMap",
    "ZoneDustBreakdown",
    "ZoneMeta",
    "ZonePrediction",
    # EC air purifier models
    "DailyAirQualityData",
    "OutdoorAirQualityData",
    "ScheduledEvent",
    "ScheduledEventsData",
]
