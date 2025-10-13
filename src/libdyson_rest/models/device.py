"""
Device model classes for libdyson-rest.

These models represent the device data structures from the Dyson API.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, cast

from ..types import (
    ConnectedConfigurationResponseDict,
    DeviceResponseDict,
    FirmwareResponseDict,
    MQTTResponseDict,
    PendingReleaseResponseDict,
)
from ..validation import (
    safe_get_bool,
    safe_get_dict,
    safe_get_optional_dict,
    safe_get_optional_list,
    safe_get_optional_str,
    safe_get_str,
    validate_json_response,
)


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
    minimum_app_version: Optional[str] = None

    @classmethod
    def from_dict(cls, data: FirmwareResponseDict) -> "Firmware":
        """Create Firmware instance from dictionary."""
        validated_data = validate_json_response(data, "Firmware")

        capabilities = None
        capabilities_list = safe_get_optional_list(validated_data, "capabilities")
        if capabilities_list is not None:
            capabilities = [CapabilityString(cap) for cap in capabilities_list]

        return cls(
            auto_update_enabled=safe_get_bool(validated_data, "autoUpdateEnabled"),
            new_version_available=safe_get_bool(validated_data, "newVersionAvailable"),
            version=safe_get_str(validated_data, "version"),
            capabilities=capabilities,
            minimum_app_version=safe_get_optional_str(
                validated_data, "minimumAppVersion"
            ),
        )


@dataclass
class PendingRelease:
    """Pending firmware release information."""

    version: str
    pushed: bool

    @classmethod
    def from_dict(cls, data: PendingReleaseResponseDict) -> "PendingRelease":
        """Create PendingRelease instance from dictionary."""
        validated_data = validate_json_response(data, "PendingRelease")
        return cls(
            version=safe_get_str(validated_data, "version"),
            pushed=safe_get_bool(validated_data, "pushed"),
        )


@dataclass
class MQTT:
    """MQTT connection configuration."""

    local_broker_credentials: str
    mqtt_root_topic_level: str
    remote_broker_type: RemoteBrokerType

    @classmethod
    def from_dict(cls, data: MQTTResponseDict) -> "MQTT":
        """Create MQTT instance from dictionary."""
        validated_data = validate_json_response(data, "MQTT")
        return cls(
            local_broker_credentials=safe_get_str(
                validated_data, "localBrokerCredentials"
            ),
            mqtt_root_topic_level=safe_get_str(validated_data, "mqttRootTopicLevel"),
            remote_broker_type=RemoteBrokerType(
                safe_get_str(validated_data, "remoteBrokerType")
            ),
        )


@dataclass
class ConnectedConfiguration:
    """Connected device configuration."""

    firmware: Firmware
    mqtt: MQTT

    @classmethod
    def from_dict(
        cls, data: ConnectedConfigurationResponseDict
    ) -> "ConnectedConfiguration":
        """Create ConnectedConfiguration instance from dictionary."""
        validated_data = validate_json_response(data, "ConnectedConfiguration")
        firmware_data = safe_get_dict(validated_data, "firmware")
        mqtt_data = safe_get_dict(validated_data, "mqtt")
        return cls(
            firmware=Firmware.from_dict(cast(FirmwareResponseDict, firmware_data)),
            mqtt=MQTT.from_dict(cast(MQTTResponseDict, mqtt_data)),
        )


@dataclass
class Device:
    """Dyson device information."""

    category: DeviceCategory
    connection_category: ConnectionCategory
    model: Optional[str]
    name: str
    serial_number: str
    type: str
    variant: Optional[str] = None
    connected_configuration: Optional[ConnectedConfiguration] = None

    @classmethod
    def from_dict(cls, data: DeviceResponseDict) -> "Device":
        """Create Device instance from dictionary."""
        validated_data = validate_json_response(data, "Device")

        connected_config = None
        connected_config_data = safe_get_optional_dict(
            validated_data, "connectedConfiguration"
        )
        if connected_config_data is not None:
            config_dict = cast(
                ConnectedConfigurationResponseDict, connected_config_data
            )
            connected_config = ConnectedConfiguration.from_dict(config_dict)

        # Handle null/missing names with fallback
        device_name = safe_get_optional_str(validated_data, "name")
        if not device_name:
            serial_number = safe_get_str(validated_data, "serialNumber")
            device_name = f"Dyson {serial_number}"

        return cls(
            category=DeviceCategory(safe_get_str(validated_data, "category")),
            connection_category=ConnectionCategory(
                safe_get_str(validated_data, "connectionCategory")
            ),
            model=safe_get_optional_str(validated_data, "model"),
            name=device_name,
            serial_number=safe_get_str(validated_data, "serialNumber"),
            type=safe_get_str(validated_data, "type"),
            variant=safe_get_optional_str(validated_data, "variant"),
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
                    cap.value
                    for cap in self.connected_configuration.firmware.capabilities
                ]

            if self.connected_configuration.firmware.minimum_app_version:
                firmware_dict["minimumAppVersion"] = (
                    self.connected_configuration.firmware.minimum_app_version
                )

            result["connectedConfiguration"] = {
                "firmware": firmware_dict,
                "mqtt": {
                    "localBrokerCredentials": self.connected_configuration.mqtt.local_broker_credentials,
                    "mqttRootTopicLevel": self.connected_configuration.mqtt.mqtt_root_topic_level,
                    "remoteBrokerType": self.connected_configuration.mqtt.remote_broker_type.value,
                },
            }

        return result
