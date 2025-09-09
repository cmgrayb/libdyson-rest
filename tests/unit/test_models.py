"""Tests for libdyson-rest data models."""

from libdyson_rest.models import (
    DysonCredentials,
    DysonDevice,
    DysonDeviceState,
    PendingRelease,
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
