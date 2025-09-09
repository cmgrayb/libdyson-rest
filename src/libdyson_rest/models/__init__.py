"""
Data models for libdyson-rest.

This module contains all data model classes for the Dyson REST API.
"""

from .auth import (
    AuthenticationMethod,
    LoginChallenge,
    LoginInformation,
    TokenType,
    UserStatus,
)
from .device import (
    MQTT,
    CapabilityString,
    ConnectedConfiguration,
    ConnectionCategory,
    Device,
    DeviceCategory,
    Firmware,
    PendingRelease,
    RemoteBrokerType,
)
from .iot import IoTCredentials, IoTData

__all__ = [
    # Auth models
    "AuthenticationMethod",
    "LoginChallenge",
    "LoginInformation",
    "TokenType",
    "UserStatus",
    # Device models
    "CapabilityString",
    "ConnectedConfiguration",
    "ConnectionCategory",
    "Device",
    "DeviceCategory",
    "Firmware",
    "MQTT",
    "PendingRelease",
    "RemoteBrokerType",
    # IoT models
    "IoTCredentials",
    "IoTData",
]

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class DysonDevice:
    """Represents a Dyson device."""

    serial: str
    name: str
    version: str
    auto_update: bool
    new_version_available: bool
    product_type: str
    connection_type: str


@dataclass
class DysonDeviceState:
    """Represents the current state of a Dyson device."""

    power: bool
    speed: int
    mode: str
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    air_quality: Optional[int] = None


@dataclass
class DysonCredentials:
    """Credentials for Dyson device connection."""

    username: str
    password: str
    hostname: str
    port: int = 1883


def device_from_dict(data: Dict[str, Any]) -> DysonDevice:
    """
    Create a DysonDevice from dictionary data.

    Args:
        data: Dictionary containing device information

    Returns:
        DysonDevice instance
    """
    return DysonDevice(
        serial=data.get("serial", ""),
        name=data.get("name", ""),
        version=data.get("version", ""),
        auto_update=data.get("auto_update", False),
        new_version_available=data.get("new_version_available", False),
        product_type=data.get("product_type", ""),
        connection_type=data.get("connection_type", ""),
    )


def credentials_from_dict(data: Dict[str, Any]) -> DysonCredentials:
    """
    Create DysonCredentials from dictionary data.

    Args:
        data: Dictionary containing credential information

    Returns:
        DysonCredentials instance
    """
    return DysonCredentials(
        username=data.get("username", ""),
        password=data.get("password", ""),
        hostname=data.get("hostname", ""),
        port=data.get("port", 1883),
    )
