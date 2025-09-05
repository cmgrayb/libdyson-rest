"""
Tests for IoT model classes.

These tests cover the IoT credentials and data models.
"""

from typing import Any, Dict
from uuid import UUID

import pytest

from libdyson_rest.models.iot import IoTCredentials, IoTData
from libdyson_rest.validation import JSONValidationError


class TestIoTCredentials:
    """Test IoTCredentials model."""

    def test_iot_credentials_creation(self) -> None:
        """Test creating IoTCredentials instance."""
        client_id = UUID("12345678-1234-5678-9abc-123456789abc")
        token_value = UUID("87654321-4321-8765-cba9-987654321abc")

        credentials = IoTCredentials(
            client_id=client_id,
            custom_authorizer_name="TestAuthorizer",
            token_key="test_key",
            token_signature="test_signature",
            token_value=token_value,
        )

        assert credentials.client_id == client_id
        assert credentials.custom_authorizer_name == "TestAuthorizer"
        assert credentials.token_key == "test_key"
        assert credentials.token_signature == "test_signature"
        assert credentials.token_value == token_value

    def test_iot_credentials_from_dict_success(self) -> None:
        """Test creating IoTCredentials from dictionary."""
        data = {
            "ClientId": "12345678-1234-5678-9abc-123456789abc",
            "CustomAuthorizerName": "TestAuthorizer",
            "TokenKey": "test_key",
            "TokenSignature": "test_signature",
            "TokenValue": "87654321-4321-8765-cba9-987654321abc",
        }

        credentials = IoTCredentials.from_dict(data)

        assert str(credentials.client_id) == "12345678-1234-5678-9abc-123456789abc"
        assert credentials.custom_authorizer_name == "TestAuthorizer"
        assert credentials.token_key == "test_key"
        assert credentials.token_signature == "test_signature"
        assert str(credentials.token_value) == "87654321-4321-8765-cba9-987654321abc"

    def test_iot_credentials_from_dict_missing_field(self) -> None:
        """Test IoTCredentials from dictionary with missing field."""
        data: Dict[str, Any] = {
            "ClientId": "12345678-1234-5678-9abc-123456789abc",
            "CustomAuthorizerName": "TestAuthorizer",
            "TokenKey": "test_key",
            # Missing TokenSignature and TokenValue
        }

        with pytest.raises(JSONValidationError, match="Missing required field"):
            IoTCredentials.from_dict(data)

    def test_iot_credentials_from_dict_invalid_uuid(self) -> None:
        """Test IoTCredentials from dictionary with invalid UUID."""
        data = {
            "ClientId": "invalid-uuid",
            "CustomAuthorizerName": "TestAuthorizer",
            "TokenKey": "test_key",
            "TokenSignature": "test_signature",
            "TokenValue": "87654321-4321-8765-cba9-987654321abc",
        }

        with pytest.raises(JSONValidationError, match="Invalid UUID format"):
            IoTCredentials.from_dict(data)

    def test_iot_credentials_to_dict(self) -> None:
        """Test converting IoTCredentials to dictionary."""
        client_id = UUID("12345678-1234-5678-9abc-123456789abc")
        token_value = UUID("87654321-4321-8765-cba9-987654321abc")

        credentials = IoTCredentials(
            client_id=client_id,
            custom_authorizer_name="TestAuthorizer",
            token_key="test_key",
            token_signature="test_signature",
            token_value=token_value,
        )

        result = credentials.to_dict()

        expected = {
            "ClientId": "12345678-1234-5678-9abc-123456789abc",
            "CustomAuthorizerName": "TestAuthorizer",
            "TokenKey": "test_key",
            "TokenSignature": "test_signature",
            "TokenValue": "87654321-4321-8765-cba9-987654321abc",
        }

        assert result == expected


class TestIoTData:
    """Test IoTData model."""

    def test_iot_data_creation(self) -> None:
        """Test creating IoTData instance."""
        client_id = UUID("12345678-1234-5678-9abc-123456789abc")
        token_value = UUID("87654321-4321-8765-cba9-987654321abc")

        credentials = IoTCredentials(
            client_id=client_id,
            custom_authorizer_name="TestAuthorizer",
            token_key="test_key",
            token_signature="test_signature",
            token_value=token_value,
        )

        iot_data = IoTData(
            endpoint="https://example.amazonaws.com",
            iot_credentials=credentials,
        )

        assert iot_data.endpoint == "https://example.amazonaws.com"
        assert iot_data.iot_credentials == credentials

    def test_iot_data_from_dict_success(self) -> None:
        """Test creating IoTData from dictionary."""
        data = {
            "Endpoint": "https://example.amazonaws.com",
            "IoTCredentials": {
                "ClientId": "12345678-1234-5678-9abc-123456789abc",
                "CustomAuthorizerName": "TestAuthorizer",
                "TokenKey": "test_key",
                "TokenSignature": "test_signature",
                "TokenValue": "87654321-4321-8765-cba9-987654321abc",
            },
        }

        iot_data = IoTData.from_dict(data)

        assert iot_data.endpoint == "https://example.amazonaws.com"
        assert iot_data.iot_credentials.custom_authorizer_name == "TestAuthorizer"
        assert (
            str(iot_data.iot_credentials.client_id)
            == "12345678-1234-5678-9abc-123456789abc"
        )

    def test_iot_data_from_dict_missing_endpoint(self) -> None:
        """Test IoTData from dictionary with missing endpoint."""
        data: Dict[str, Any] = {
            "IoTCredentials": {
                "ClientId": "12345678-1234-5678-9abc-123456789abc",
                "CustomAuthorizerName": "TestAuthorizer",
                "TokenKey": "test_key",
                "TokenSignature": "test_signature",
                "TokenValue": "87654321-4321-8765-cba9-987654321abc",
            }
        }

        with pytest.raises(
            JSONValidationError, match="Missing required field: Endpoint"
        ):
            IoTData.from_dict(data)

    def test_iot_data_from_dict_missing_credentials(self) -> None:
        """Test IoTData from dictionary with missing credentials."""
        data: Dict[str, Any] = {
            "Endpoint": "https://example.amazonaws.com",
        }

        with pytest.raises(
            JSONValidationError, match="Missing required field: IoTCredentials"
        ):
            IoTData.from_dict(data)

    def test_iot_data_to_dict(self) -> None:
        """Test converting IoTData to dictionary."""
        client_id = UUID("12345678-1234-5678-9abc-123456789abc")
        token_value = UUID("87654321-4321-8765-cba9-987654321abc")

        credentials = IoTCredentials(
            client_id=client_id,
            custom_authorizer_name="TestAuthorizer",
            token_key="test_key",
            token_signature="test_signature",
            token_value=token_value,
        )

        iot_data = IoTData(
            endpoint="https://example.amazonaws.com",
            iot_credentials=credentials,
        )

        result = iot_data.to_dict()

        expected = {
            "Endpoint": "https://example.amazonaws.com",
            "IoTCredentials": {
                "ClientId": "12345678-1234-5678-9abc-123456789abc",
                "CustomAuthorizerName": "TestAuthorizer",
                "TokenKey": "test_key",
                "TokenSignature": "test_signature",
                "TokenValue": "87654321-4321-8765-cba9-987654321abc",
            },
        }

        assert result == expected
