"""Integration tests for AsyncDysonClient."""

from unittest.mock import Mock, patch

import pytest

from libdyson_rest import AsyncDysonClient
from libdyson_rest.exceptions import DysonAuthError

# Pytest async configuration
pytestmark = pytest.mark.asyncio


class TestAsyncDysonClientIntegration:
    """Integration tests for AsyncDysonClient."""

    async def test_client_lifecycle(self) -> None:
        """Test complete client lifecycle."""
        async with AsyncDysonClient() as client:
            # Test initialization
            assert client is not None
            assert client.country == "US"
            assert client.culture == "en-US"
            assert client.timeout == 30

        # Client should be closed automatically

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    async def test_provision_integration(self, mock_get) -> None:
        """Test provision integration workflow."""
        # Mock successful provision response
        mock_response = Mock()
        mock_response.json.return_value = "1.2.3"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        async with AsyncDysonClient() as client:
            version = await client.provision()
            assert version == "1.2.3"
            assert client._provisioned is True

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    async def test_auth_flow_integration(self, mock_post) -> None:
        """Test authentication flow integration."""
        # Mock begin_login response
        login_response = Mock()
        login_response.json.return_value = {
            "challengeId": "12345678-1234-5678-9abc-123456789abc",
        }
        login_response.raise_for_status.return_value = None

        # Mock complete_login response
        complete_response = Mock()
        complete_response.json.return_value = {
            "account": "87654321-4321-8765-cba9-987654321abc",
            "token": "test_bearer_token_123",
            "tokenType": "Bearer",
        }
        complete_response.raise_for_status.return_value = None

        mock_post.side_effect = [login_response, complete_response]

        async with AsyncDysonClient(
            email="test@example.com", password="test_password"
        ) as client:
            # Begin login
            challenge = await client.begin_login()
            assert challenge.challenge_id is not None

            # Complete login
            login_info = await client.complete_login(
                str(challenge.challenge_id), "123456"
            )
            assert login_info.token == "test_bearer_token_123"
            assert client.auth_token == "test_bearer_token_123"

    async def test_auth_token_persistence(self) -> None:
        """Test auth token setting and persistence."""
        async with AsyncDysonClient() as client:
            # Test initial state
            assert client.auth_token is None

            # Set token
            client.set_auth_token("persistent_token")
            assert client.get_auth_token() == "persistent_token"
            assert client.auth_token == "persistent_token"

            # Clear token
            client.auth_token = None
            assert client.auth_token is None

    async def test_configuration_validation(self) -> None:
        """Test client configuration validation."""
        # Test invalid country
        with pytest.raises(ValueError, match="Country must be"):
            AsyncDysonClient(country="USA")

        # Test invalid culture
        with pytest.raises(ValueError, match="Culture must be"):
            AsyncDysonClient(culture="english")

        # Test valid configurations
        async with AsyncDysonClient(country="UK", culture="en-GB") as client:
            assert client.country == "UK"
            assert client.culture == "en-GB"

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    async def test_device_operations_workflow(self, mock_get) -> None:
        """Test device operations workflow."""
        # Mock devices response
        devices_response = Mock()
        devices_response.json.return_value = [
            {
                "serialNumber": "MOCK-TEST-SN12345",
                "name": "Mock Test Device",
                "type": "MOCK_TYPE",
                "Version": "99.99.99",
                "LocalCredentials": "mock_encrypted_credentials_data",
                "AutoUpdate": True,
                "NewVersionAvailable": False,
                "ProductType": "MOCK_PRODUCT",
                "ConnectionType": "wifiConnected",
                "category": "ec",
                "connectionCategory": "wifiOnly",
            }
        ]
        devices_response.raise_for_status.return_value = None

        # Mock IoT credentials response
        iot_response = Mock()
        iot_response.json.return_value = {
            "Endpoint": "mock-iot-endpoint.example.com",
            "IoTCredentials": {
                "ClientId": "12345678-1234-1234-1234-123456789abc",
                "CustomAuthorizerName": "MockAuthorizer",
                "TokenKey": "mock_token_key",
                "TokenSignature": "mock_token_signature",
                "TokenValue": "87654321-4321-4321-4321-987654321abc",
            },
        }
        iot_response.raise_for_status.return_value = None

        # Mock pending release response
        release_response = Mock()
        release_response.json.return_value = {
            "version": "MOCK.99.99.999.9999",
            "pushed": False,
        }
        release_response.raise_for_status.return_value = None

        mock_get.side_effect = [devices_response, iot_response, release_response]

        async with AsyncDysonClient(auth_token="test_token") as client:
            # Get devices
            devices = await client.get_devices()
            assert len(devices) == 1
            assert devices[0].serial_number == "MOCK-TEST-SN12345"

            # Get IoT credentials
            iot_data = await client.get_iot_credentials("MOCK-TEST-SN12345")
            assert iot_data.endpoint == "mock-iot-endpoint.example.com"

            # Get pending release
            pending_release = await client.get_pending_release("MOCK-TEST-SN12345")
            assert pending_release.version == "MOCK.99.99.999.9999"

    async def test_error_handling_integration(self) -> None:
        """Test error handling in integration scenarios."""
        async with AsyncDysonClient() as client:
            # Test authentication required errors
            with pytest.raises(DysonAuthError):
                await client.get_devices()

            with pytest.raises(DysonAuthError):
                await client.get_iot_credentials("test_serial")

            with pytest.raises(DysonAuthError):
                await client.get_pending_release("test_serial")

            # Test missing credentials errors
            with pytest.raises(DysonAuthError):
                await client.begin_login()

            with pytest.raises(DysonAuthError):
                await client.complete_login("challenge_id", "123456")

    async def test_context_manager_error_handling(self) -> None:
        """Test context manager handles errors properly."""
        try:
            async with AsyncDysonClient():
                # Simulate an error
                raise ValueError("Test error")
        except ValueError:
            # Client should still be closed properly
            pass
        # No assertions needed - if close() fails, it will raise an exception

    async def test_concurrent_operations(self) -> None:
        """Test that multiple async operations can be performed."""
        import asyncio

        async def create_and_close_client():
            async with AsyncDysonClient() as client:
                return client.timeout

        # Run multiple clients concurrently
        tasks = [create_and_close_client() for _ in range(3)]
        results = await asyncio.gather(*tasks)

        assert all(timeout == 30 for timeout in results)
