"""Tests for libdyson-rest data models."""

from libdyson_rest.models import (
    MQTT,
    ConnectedConfiguration,
    ConnectionCategory,
    Device,
    DeviceCategory,
    DysonCredentials,
    DysonDevice,
    DysonDeviceState,
    Firmware,
    PendingRelease,
    RemoteBrokerType,
    credentials_from_dict,
    device_from_dict,
)


def test_dyson_device_creation() -> None:
    """Test DysonDevice dataclass creation."""
    device = DysonDevice(
        serial="ABC123",
        name="Living Room Fan",
        version="1.2.3",
        auto_update=True,
        new_version_available=False,
        product_type="527",
        connection_type="wifi",
    )

    assert device.serial == "ABC123"
    assert device.name == "Living Room Fan"
    assert device.version == "1.2.3"
    assert device.auto_update is True
    assert device.new_version_available is False
    assert device.product_type == "527"
    assert device.connection_type == "wifi"


def test_dyson_device_state_creation() -> None:
    """Test DysonDeviceState dataclass creation."""
    state = DysonDeviceState(
        power=True, speed=5, mode="auto", temperature=22.5, humidity=45, air_quality=3
    )

    assert state.power is True
    assert state.speed == 5
    assert state.mode == "auto"
    assert state.temperature == 22.5
    assert state.humidity == 45
    assert state.air_quality == 3


def test_dyson_device_state_optional_fields() -> None:
    """Test DysonDeviceState with optional fields."""
    state = DysonDeviceState(power=False, speed=0, mode="off")

    assert state.power is False
    assert state.speed == 0
    assert state.mode == "off"
    assert state.temperature is None
    assert state.humidity is None
    assert state.air_quality is None


def test_dyson_credentials_creation() -> None:
    """Test DysonCredentials dataclass creation."""
    creds = DysonCredentials(
        username="user123", password="pass456", hostname="device.local", port=1883
    )

    assert creds.username == "user123"
    assert creds.password == "pass456"
    assert creds.hostname == "device.local"
    assert creds.port == 1883


def test_dyson_credentials_default_port() -> None:
    """Test DysonCredentials with default port."""
    creds = DysonCredentials(
        username="user123", password="pass456", hostname="device.local"
    )

    assert creds.port == 1883


def test_device_from_dict_complete() -> None:
    """Test device_from_dict with complete data."""
    data = {
        "serial": "XYZ789",
        "name": "Bedroom Purifier",
        "version": "2.1.0",
        "auto_update": False,
        "new_version_available": True,
        "product_type": "358",
        "connection_type": "ethernet",
    }

    device = device_from_dict(data)

    assert device.serial == "XYZ789"
    assert device.name == "Bedroom Purifier"
    assert device.version == "2.1.0"
    assert device.auto_update is False
    assert device.new_version_available is True
    assert device.product_type == "358"
    assert device.connection_type == "ethernet"


def test_device_from_dict_missing_fields() -> None:
    """Test device_from_dict with missing fields uses defaults."""
    data = {"serial": "DEF456"}

    device = device_from_dict(data)

    assert device.serial == "DEF456"
    assert device.name == ""
    assert device.version == ""
    assert device.auto_update is False
    assert device.new_version_available is False
    assert device.product_type == ""
    assert device.connection_type == ""


def test_device_from_dict_empty() -> None:
    """Test device_from_dict with empty dictionary."""
    device = device_from_dict({})

    assert device.serial == ""
    assert device.name == ""
    assert device.version == ""
    assert device.auto_update is False
    assert device.new_version_available is False
    assert device.product_type == ""
    assert device.connection_type == ""


def test_credentials_from_dict_complete() -> None:
    """Test credentials_from_dict with complete data."""
    data = {
        "username": "testuser",
        "password": "testpass",
        "hostname": "192.168.1.100",
        "port": 8883,
    }

    creds = credentials_from_dict(data)

    assert creds.username == "testuser"
    assert creds.password == "testpass"
    assert creds.hostname == "192.168.1.100"
    assert creds.port == 8883


def test_credentials_from_dict_missing_fields() -> None:
    """Test credentials_from_dict with missing fields uses defaults."""
    data = {"username": "user", "hostname": "host"}

    creds = credentials_from_dict(data)

    assert creds.username == "user"
    assert creds.password == ""
    assert creds.hostname == "host"
    assert creds.port == 1883


def test_credentials_from_dict_empty() -> None:
    """Test credentials_from_dict with empty dictionary."""
    creds = credentials_from_dict({})

    assert creds.username == ""
    assert creds.password == ""
    assert creds.hostname == ""
    assert creds.port == 1883


def test_pending_release_creation() -> None:
    """Test PendingRelease dataclass creation."""
    release = PendingRelease(version="438MPF.00.01.007.0002", pushed=False)

    assert release.version == "438MPF.00.01.007.0002"
    assert release.pushed is False


def test_pending_release_from_dict() -> None:
    """Test PendingRelease creation from dictionary."""
    from libdyson_rest.types import PendingReleaseResponseDict

    data: PendingReleaseResponseDict = {
        "version": "438MPF.00.01.007.0002",
        "pushed": False,
    }

    release = PendingRelease.from_dict(data)

    assert release.version == "438MPF.00.01.007.0002"
    assert release.pushed is False


def test_device_to_dict_basic() -> None:
    """Test Device.to_dict() with basic data."""
    device = Device(
        category=DeviceCategory.ENVIRONMENT_CLEANER,
        connection_category=ConnectionCategory.WIFI_ONLY,
        model="ABC123",
        name="Test Device",
        serial_number="SN123456",
        type="520",
        variant=None,
        connected_configuration=None,
    )

    result = device.to_dict()

    expected = {
        "category": "ec",
        "connectionCategory": "wifiOnly",
        "model": "ABC123",
        "name": "Test Device",
        "serialNumber": "SN123456",
        "type": "520",
    }

    assert result == expected


def test_device_to_dict_with_variant() -> None:
    """Test Device.to_dict() with variant field."""
    device = Device(
        category=DeviceCategory.ENVIRONMENT_CLEANER,
        connection_category=ConnectionCategory.WIFI_ONLY,
        model="ABC123",
        name="Test Device",
        serial_number="SN123456",
        type="520",
        variant="EU",
        connected_configuration=None,
    )

    result = device.to_dict()

    assert result["variant"] == "EU"


def test_device_to_dict_with_connected_config() -> None:
    """Test Device.to_dict() with connected configuration."""
    firmware = Firmware(
        auto_update_enabled=True,
        new_version_available=False,
        version="1.0.0",
        capabilities=["Scheduling"],
        minimum_app_version="2.0.0",
    )

    mqtt = MQTT(
        local_broker_credentials={"user": "test", "pass": "secret"},
        mqtt_root_topic_level="root/topic",
        remote_broker_type=RemoteBrokerType.WSS,
    )

    config = ConnectedConfiguration(firmware=firmware, mqtt=mqtt)

    device = Device(
        category=DeviceCategory.ENVIRONMENT_CLEANER,
        connection_category=ConnectionCategory.WIFI_ONLY,
        model="ABC123",
        name="Test Device",
        serial_number="SN123456",
        type="520",
        variant=None,
        connected_configuration=config,
    )

    result = device.to_dict()

    assert "connectedConfiguration" in result
    assert "firmware" in result["connectedConfiguration"]
    assert "mqtt" in result["connectedConfiguration"]

    firmware_dict = result["connectedConfiguration"]["firmware"]
    assert firmware_dict["autoUpdateEnabled"] is True
    assert firmware_dict["newVersionAvailable"] is False
    assert firmware_dict["version"] == "1.0.0"
    assert firmware_dict["capabilities"] == ["Scheduling"]
    assert firmware_dict["minimumAppVersion"] == "2.0.0"

    mqtt_dict = result["connectedConfiguration"]["mqtt"]
    assert mqtt_dict["localBrokerCredentials"] == {"user": "test", "pass": "secret"}
    assert mqtt_dict["mqttRootTopicLevel"] == "root/topic"
    assert mqtt_dict["remoteBrokerType"] == "wss"


def test_device_to_dict_with_config_no_capabilities() -> None:
    """Test Device.to_dict() with connected config but no capabilities."""
    firmware = Firmware(
        auto_update_enabled=True,
        new_version_available=False,
        version="1.0.0",
        capabilities=None,
        minimum_app_version=None,
    )

    mqtt = MQTT(
        local_broker_credentials={"user": "test"},
        mqtt_root_topic_level="root/topic",
        remote_broker_type=RemoteBrokerType.WSS,
    )

    config = ConnectedConfiguration(firmware=firmware, mqtt=mqtt)

    device = Device(
        category=DeviceCategory.ENVIRONMENT_CLEANER,
        connection_category=ConnectionCategory.WIFI_ONLY,
        model="ABC123",
        name="Test Device",
        serial_number="SN123456",
        type="520",
        variant=None,
        connected_configuration=config,
    )

    result = device.to_dict()

    firmware_dict = result["connectedConfiguration"]["firmware"]
    assert "capabilities" not in firmware_dict
    assert "minimumAppVersion" not in firmware_dict


def test_device_from_dict_with_null_name() -> None:
    """Test Device.from_dict with null name uses fallback."""
    from typing import cast

    from libdyson_rest.types import DeviceResponseDict

    device_data = cast(
        DeviceResponseDict,
        {
            "serialNumber": "SN123456789",
            "name": None,  # Null name from API
            "model": "AM07",
            "type": "520",
            "category": "ec",
            "connectionCategory": "wifiOnly",
        },
    )

    device = Device.from_dict(device_data)

    # Should generate fallback name using serial number
    assert device.name == "Dyson SN123456789"
    assert device.serial_number == "SN123456789"
    assert device.model == "AM07"
    assert device.type == "520"
    assert device.category == DeviceCategory.ENVIRONMENT_CLEANER
    assert device.connection_category == ConnectionCategory.WIFI_ONLY


def test_device_from_dict_with_missing_name() -> None:
    """Test Device.from_dict with missing name field uses fallback."""
    from typing import cast

    from libdyson_rest.types import DeviceResponseDict

    # Create a dict without name field and cast to DeviceResponseDict
    device_data_raw = {
        "serialNumber": "SN987654321",
        # name field completely missing
        "model": "TP02",
        "type": "527",
        "category": "ec",
        "connectionCategory": "wifiOnly",
    }
    device_data = cast(DeviceResponseDict, device_data_raw)

    device = Device.from_dict(device_data)

    # Should generate fallback name using serial number
    assert device.name == "Dyson SN987654321"
    assert device.serial_number == "SN987654321"
    assert device.model == "TP02"
    assert device.type == "527"
    assert device.category == DeviceCategory.ENVIRONMENT_CLEANER
    assert device.connection_category == ConnectionCategory.WIFI_ONLY


def test_device_from_dict_with_empty_name() -> None:
    """Test Device.from_dict with empty string name uses fallback."""
    from typing import cast

    from libdyson_rest.types import DeviceResponseDict

    device_data = cast(
        DeviceResponseDict,
        {
            "serialNumber": "SN456789123",
            "name": "",  # Empty string name
            "model": "HP01",
            "type": "469",
            "category": "ec",
            "connectionCategory": "wifiOnly",
        },
    )

    device = Device.from_dict(device_data)

    # Should generate fallback name using serial number
    assert device.name == "Dyson SN456789123"
    assert device.serial_number == "SN456789123"
    assert device.model == "HP01"
    assert device.type == "469"
    assert device.category == DeviceCategory.ENVIRONMENT_CLEANER
    assert device.connection_category == ConnectionCategory.WIFI_ONLY


def test_device_from_dict_with_valid_name() -> None:
    """Test Device.from_dict with valid name preserves original name."""
    from typing import cast

    from libdyson_rest.types import DeviceResponseDict

    device_data = cast(
        DeviceResponseDict,
        {
            "serialNumber": "SN111222333",
            "name": "Living Room Purifier",
            "model": "TP07",
            "type": "438",
            "category": "ec",
            "connectionCategory": "wifiOnly",
        },
    )

    device = Device.from_dict(device_data)

    # Should keep the original name
    assert device.name == "Living Room Purifier"
    assert device.serial_number == "SN111222333"
    assert device.model == "TP07"
    assert device.type == "438"
    assert device.category == DeviceCategory.ENVIRONMENT_CLEANER
    assert device.connection_category == ConnectionCategory.WIFI_ONLY


def test_capability_string_unknown_capabilities() -> None:
    """Test that unknown capabilities are supported without breaking."""
    # Test that unknown capabilities work (like AdvanceOscillationDay0)
    firmware = Firmware(
        auto_update_enabled=True,
        new_version_available=False,
        version="1.0.0",
        capabilities=[
            "AdvanceOscillationDay0",  # Previously unknown capability
            "AdvanceOscillationDay1",
            "Scheduling",
            "SomeNewCapability",  # Future unknown capability
        ],
        minimum_app_version=None,
    )

    assert len(firmware.capabilities) == 4
    assert "AdvanceOscillationDay0" in firmware.capabilities
    assert "AdvanceOscillationDay1" in firmware.capabilities
    assert "Scheduling" in firmware.capabilities
    assert "SomeNewCapability" in firmware.capabilities
