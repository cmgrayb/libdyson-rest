"""
Device model classes for libdyson-rest.

These models represent the device data structures from the Dyson API.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class DeviceCategory(Enum):
    """Device category enumeration."""

    ENVIRONMENT_CLEANER = "ec"  # air filters etc
    FLOOR_CLEANER = "flrc"
    HAIR_CARE = "hc"
    LIGHT = "light"
    ROBOT = "robot"
    WEARABLE = "wearable"


class ConnectionCategory(Enum):
    """Device connection category enumeration."""

    LEC_AND_WIFI = "lecAndWifi"  # Bluetooth and Wi-Fi
    LEC_ONLY = "lecOnly"  # Bluetooth only
    NON_CONNECTED = "nonConnected"
    WIFI_ONLY = "wifiOnly"


class RemoteBrokerType(Enum):
    """Remote broker type enumeration."""

    WSS = "wss"


class CapabilityString(Enum):
    """Device capability enumeration."""

    ADVANCE_OSCILLATION_DAY1 = "AdvanceOscillationDay1"
    SCHEDULING = "Scheduling"
    ENVIRONMENTAL_DATA = "EnvironmentalData"
    EXTENDED_AQ = "ExtendedAQ"
    CHANGE_WIFI = "ChangeWifi"


@dataclass
class Firmware:
    """Device firmware information."""

    auto_update_enabled: bool
    new_version_available: bool
    version: str
    capabilities: Optional[List[CapabilityString]] = None

    @classmethod
    def from_dict(cls, data: Dict) -> "Firmware":
        """Create Firmware instance from dictionary."""
        capabilities = None
        if "capabilities" in data:
            capabilities = [CapabilityString(cap) for cap in data["capabilities"]]

        return cls(
            auto_update_enabled=data["autoUpdateEnabled"],
            new_version_available=data["newVersionAvailable"],
            version=data["version"],
            capabilities=capabilities,
        )


@dataclass
class MQTT:
    """MQTT connection configuration."""

    local_broker_credentials: str
    mqtt_root_topic_level: str
    remote_broker_type: RemoteBrokerType

    @classmethod
    def from_dict(cls, data: Dict) -> "MQTT":
        """Create MQTT instance from dictionary."""
        return cls(
            local_broker_credentials=data["localBrokerCredentials"],
            mqtt_root_topic_level=data["mqttRootTopicLevel"],
            remote_broker_type=RemoteBrokerType(data["remoteBrokerType"]),
        )


@dataclass
class ConnectedConfiguration:
    """Connected device configuration."""

    firmware: Firmware
    mqtt: MQTT

    @classmethod
    def from_dict(cls, data: Dict) -> "ConnectedConfiguration":
        """Create ConnectedConfiguration instance from dictionary."""
        return cls(
            firmware=Firmware.from_dict(data["firmware"]),
            mqtt=MQTT.from_dict(data["mqtt"]),
        )


@dataclass
class Device:
    """Dyson device information."""

    category: DeviceCategory
    connection_category: ConnectionCategory
    model: str
    name: str
    serial_number: str
    type: str
    variant: Optional[str] = None
    connected_configuration: Optional[ConnectedConfiguration] = None

    @classmethod
    def from_dict(cls, data: Dict) -> "Device":
        """Create Device instance from dictionary."""
        connected_config = None
        if "connectedConfiguration" in data:
            connected_config = ConnectedConfiguration.from_dict(data["connectedConfiguration"])

        return cls(
            category=DeviceCategory(data["category"]),
            connection_category=ConnectionCategory(data["connectionCategory"]),
            model=data["model"],
            name=data["name"],
            serial_number=data["serialNumber"],
            type=data["type"],
            variant=data.get("variant"),
            connected_configuration=connected_config,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Device instance to dictionary."""
        result: Dict[str, Any] = {
            "category": self.category.value,
            "connectionCategory": self.connection_category.value,
            "model": self.model,
            "name": self.name,
            "serialNumber": self.serial_number,
            "type": self.type,
        }

        if self.variant:
            result["variant"] = self.variant

        if self.connected_configuration:
            firmware_dict = {
                "autoUpdateEnabled": self.connected_configuration.firmware.auto_update_enabled,
                "newVersionAvailable": self.connected_configuration.firmware.new_version_available,
                "version": self.connected_configuration.firmware.version,
            }

            if self.connected_configuration.firmware.capabilities:
                firmware_dict["capabilities"] = [
                    cap.value for cap in self.connected_configuration.firmware.capabilities
                ]

            result["connectedConfiguration"] = {
                "firmware": firmware_dict,
                "mqtt": {
                    "localBrokerCredentials": self.connected_configuration.mqtt.local_broker_credentials,
                    "mqttRootTopicLevel": self.connected_configuration.mqtt.mqtt_root_topic_level,
                    "remoteBrokerType": self.connected_configuration.mqtt.remote_broker_type.value,
                },
            }

        return result
