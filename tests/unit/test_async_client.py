"""Unit tests for Dyson REST API async client."""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from libdyson_rest.async_client import AsyncDysonClient
from libdyson_rest.exceptions import DysonAPIError, DysonAuthError, DysonConnectionError


class TestAsyncDysonClient:
    """Unit tests for AsyncDysonClient class."""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_client_initialization_with_defaults(self) -> None:
        """Test async client initializes with default values."""
        client = AsyncDysonClient()

        assert client.email is None
        assert client.password is None
        assert client.country == "US"
        assert client.timeout == 30
        assert client.auth_token is None
        assert client.account_id is None

        await client.close()

    @pytest.mark.asyncio
    async def test_client_initialization_with_custom_values(self) -> None:
        """Test async client initializes with custom values."""
        client = AsyncDysonClient(
            email="custom@email.com",
            password="custom_password",
            country="UK",
            timeout=60,
        )

        assert client.email == "custom@email.com"
        assert client.password == "custom_password"
        assert client.country == "UK"
        assert client.timeout == 60

        await client.close()

    @pytest.mark.asyncio
    async def test_authentication_no_credentials(self) -> None:
        """Test authentication fails without credentials."""
        client = AsyncDysonClient()

        with pytest.raises(DysonAuthError) as exc_info:
            await client.authenticate()

        assert "Email and password required" in str(exc_info.value)
        await client.close()

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Test async context manager functionality."""
        async with AsyncDysonClient() as client:
            assert client is not None
            assert hasattr(client, "_client")
        # Client should be automatically closed

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_provision_success(self, mock_get: AsyncMock) -> None:
        """Test successful API provisioning."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = "1.2.3"
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        client = AsyncDysonClient()

        version = await client.provision()

        assert version == "1.2.3"
        assert client._provisioned is True

        mock_get.assert_called_once()
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_provision_connection_error(self, mock_get: AsyncMock) -> None:
        """Test provision handles connection errors."""
        import httpx

        mock_get.side_effect = httpx.RequestError("Network error")

        client = AsyncDysonClient()

        with pytest.raises(DysonConnectionError) as exc_info:
            await client.provision()

        assert "Failed to provision API access" in str(exc_info.value)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_get_user_status_success(self, mock_post: AsyncMock) -> None:
        """Test successful user status retrieval."""
        # Mock response data
        mock_response = Mock()
        mock_response.json.return_value = {
            "accountStatus": "ACTIVE",
            "authenticationMethod": "EMAIL_PWD_2FA",
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = AsyncDysonClient(email="test@example.com")

        user_status = await client.get_user_status()

        assert user_status.account_status.value == "ACTIVE"
        assert user_status.authentication_method.value == "EMAIL_PWD_2FA"

        mock_post.assert_called_once()
        await client.close()

    @pytest.mark.asyncio
    async def test_get_user_status_no_email(self) -> None:
        """Test user status fails without email."""
        client = AsyncDysonClient()

        with pytest.raises(DysonAuthError) as exc_info:
            await client.get_user_status()

        assert "Email required" in str(exc_info.value)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_begin_login_success(self, mock_post: AsyncMock) -> None:
        """Test successful login initiation."""
        # Mock response data
        mock_response = Mock()
        mock_response.json.return_value = {
            "challengeId": "12345678-1234-5678-9abc-123456789abc",
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = AsyncDysonClient(email="test@example.com")

        challenge = await client.begin_login()

        assert challenge.challenge_id is not None  # UUID field

        mock_post.assert_called_once()
        await client.close()

    @pytest.mark.asyncio
    async def test_begin_login_no_email(self) -> None:
        """Test begin login fails without email."""
        client = AsyncDysonClient()

        with pytest.raises(DysonAuthError) as exc_info:
            await client.begin_login()

        assert "Email required" in str(exc_info.value)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_complete_login_success(self, mock_post: AsyncMock) -> None:
        """Test successful login completion."""
        # Mock response data
        mock_response = Mock()
        mock_response.json.return_value = {
            "account": "12345678-1234-5678-1234-567812345678",
            "token": "test_token_123",
            "tokenType": "Bearer",
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = AsyncDysonClient(email="test@example.com", password="password")

        login_info = await client.complete_login("challenge_123", "123456")

        assert str(login_info.account) == "12345678-1234-5678-1234-567812345678"
        assert login_info.token == "test_token_123"
        assert client.auth_token == "test_token_123"
        assert str(client.account_id) == "12345678-1234-5678-1234-567812345678"

        mock_post.assert_called_once()
        await client.close()

    @pytest.mark.asyncio
    async def test_complete_login_no_credentials(self) -> None:
        """Test complete login fails without credentials."""
        client = AsyncDysonClient()

        with pytest.raises(DysonAuthError) as exc_info:
            await client.complete_login("challenge_123", "123456")

        assert "Email and password are required" in str(exc_info.value)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_complete_login_invalid_credentials(
        self, mock_post: AsyncMock
    ) -> None:
        """Test complete login handles invalid credentials."""
        import httpx

        # Mock 401 response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_error = httpx.HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_response
        )
        mock_post.side_effect = mock_error

        client = AsyncDysonClient(email="test@example.com", password="wrong_password")

        with pytest.raises(DysonAuthError) as exc_info:
            await client.complete_login("challenge_123", "123456")

        assert "Invalid credentials or OTP code" in str(exc_info.value)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_complete_login_400_error(self, mock_post: AsyncMock) -> None:
        """Test complete_login handles 400 bad request errors."""
        # Mock 400 response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_response.url = "https://api.example.com/login"
        mock_response.headers = {"Content-Type": "application/json"}
        mock_error = httpx.HTTPStatusError(
            "Bad Request", request=Mock(), response=mock_response
        )
        mock_post.side_effect = mock_error

        client = AsyncDysonClient(email="test@example.com", password="password")

        with pytest.raises(DysonAuthError) as exc_info:
            await client.complete_login("challenge_123", "123456")

        assert "Bad request to Dyson API (400)" in str(exc_info.value)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_begin_login_400_error(self, mock_post: AsyncMock) -> None:
        """Test begin_login handles 400 bad request errors."""
        # Mock 400 response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_response.url = "https://api.example.com/auth"
        mock_error = httpx.HTTPStatusError(
            "Bad Request", request=Mock(), response=mock_response
        )
        mock_post.side_effect = mock_error

        client = AsyncDysonClient(email="test@example.com", password="password")

        with pytest.raises(DysonAuthError) as exc_info:
            await client.begin_login()

        assert "Bad request to Dyson API (400)" in str(exc_info.value)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_get_devices_success(self, mock_get: AsyncMock) -> None:
        """Test successful device retrieval."""
        # Mock response data
        mock_response = Mock()
        mock_response.json.return_value = [
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
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="test_token")

        devices = await client.get_devices()

        assert len(devices) == 1
        assert devices[0].serial_number == "MOCK-TEST-SN12345"
        assert devices[0].name == "Mock Test Device"

        mock_get.assert_called_once()
        await client.close()

    @pytest.mark.asyncio
    async def test_get_devices_not_authenticated(self) -> None:
        """Test device retrieval fails without authentication."""
        client = AsyncDysonClient()

        with pytest.raises(DysonAuthError) as exc_info:
            await client.get_devices()

        assert "Must authenticate before getting devices" in str(exc_info.value)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_get_devices_auth_expired(self, mock_get: AsyncMock) -> None:
        """Test device retrieval handles expired authentication."""
        import httpx

        # Mock 401 response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_error = httpx.HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_response
        )
        mock_get.side_effect = mock_error

        client = AsyncDysonClient(auth_token="expired_token")

        with pytest.raises(DysonAuthError) as exc_info:
            await client.get_devices()

        assert "Authentication token expired or invalid" in str(exc_info.value)
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_get_iot_credentials_success(self, mock_post: AsyncMock) -> None:
        """Test successful IoT credentials retrieval."""
        # Mock response data
        mock_response = Mock()
        mock_response.json.return_value = {
            "Endpoint": "mock-iot-endpoint.example.com",
            "IoTCredentials": {
                "ClientId": "12345678-1234-1234-1234-123456789abc",
                "CustomAuthorizerName": "MockAuthorizer",
                "TokenKey": "mock_token_key",
                "TokenSignature": "mock_token_signature",
                "TokenValue": "87654321-4321-4321-4321-987654321abc",
            },
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = AsyncDysonClient(auth_token="test_token")

        iot_data = await client.get_iot_credentials("MOCK-TEST-SN12345")

        assert iot_data.endpoint == "mock-iot-endpoint.example.com"
        assert iot_data.iot_credentials.custom_authorizer_name == "MockAuthorizer"

        # Verify the correct endpoint and payload were used
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "/v2/authorize/iot-credentials" in str(call_args)
        assert call_args.kwargs["json"] == {"Serial": "MOCK-TEST-SN12345"}

        await client.close()

    @pytest.mark.asyncio
    async def test_get_iot_credentials_not_authenticated(self) -> None:
        """Test IoT credentials retrieval fails without authentication."""
        client = AsyncDysonClient()

        with pytest.raises(DysonAuthError) as exc_info:
            await client.get_iot_credentials("MOCK-TEST-SN12345")

        assert "Must authenticate before getting IoT credentials" in str(exc_info.value)
        await client.close()

    def test_iot_credentials_endpoint_parity(self) -> None:
        """Test that sync and async clients use the same IoT credentials endpoint."""
        from unittest.mock import patch

        from libdyson_rest.client import DysonClient

        # Test the endpoints both clients would call
        with (
            patch(
                "libdyson_rest.async_client.httpx.AsyncClient.post"
            ) as mock_async_post,
            patch("libdyson_rest.client.requests.Session.post") as mock_sync_post,
        ):
            # Configure mock responses
            mock_response = Mock()
            mock_response.json.return_value = {
                "Endpoint": "test-endpoint.example.com",
                "IoTCredentials": {
                    "ClientId": "12345678-1234-1234-1234-123456789abc",
                    "CustomAuthorizerName": "TestAuthorizer",
                    "TokenKey": "test_token_key",
                    "TokenSignature": "test_token_signature",
                    "TokenValue": "87654321-4321-4321-4321-987654321abc",
                },
            }
            mock_response.raise_for_status.return_value = None

            mock_async_post.return_value = mock_response
            mock_sync_post.return_value = mock_response

            # Test async client
            async def test_async():
                async_client = AsyncDysonClient(auth_token="test_token")
                await async_client.get_iot_credentials("TEST-SERIAL-123")
                await async_client.close()
                return mock_async_post.call_args

            import asyncio

            async_call_args = asyncio.run(test_async())

            # Test sync client
            sync_client = DysonClient(auth_token="test_token")
            sync_client.get_iot_credentials("TEST-SERIAL-123")
            sync_call_args = mock_sync_post.call_args
            sync_client.close()

            # Both should use the same endpoint and payload
            assert "/v2/authorize/iot-credentials" in str(async_call_args)
            assert "/v2/authorize/iot-credentials" in str(sync_call_args)
            assert async_call_args.kwargs["json"] == {"Serial": "TEST-SERIAL-123"}
            assert sync_call_args.kwargs["json"] == {"Serial": "TEST-SERIAL-123"}

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_get_pending_release_success(self, mock_get: AsyncMock) -> None:
        """Test successful pending release retrieval."""
        # Mock response data
        mock_response = Mock()
        mock_response.json.return_value = {
            "version": "MOCK.99.99.999.9999",
            "pushed": False,
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        client = AsyncDysonClient(auth_token="test_token")

        pending_release = await client.get_pending_release("MOCK-TEST-SN12345")

        assert pending_release.version == "MOCK.99.99.999.9999"
        assert pending_release.pushed is False

        mock_get.assert_called_once()
        await client.close()

    @pytest.mark.asyncio
    async def test_get_pending_release_not_authenticated(self) -> None:
        """Test pending release retrieval fails without authentication."""
        client = AsyncDysonClient()

        with pytest.raises(DysonAuthError) as exc_info:
            await client.get_pending_release("MOCK-TEST-SN12345")

        assert "Must authenticate before getting pending release info" in str(
            exc_info.value
        )
        await client.close()

    def test_decrypt_local_credentials(self) -> None:
        """Test local credentials decryption (synchronous method)."""
        client = AsyncDysonClient()

        # This would normally require actual encrypted data
        # For now, just test that the method exists and handles errors
        with pytest.raises(DysonAPIError):
            client.decrypt_local_credentials("invalid_data", "MOCK-TEST-SN12345")

    def test_auth_token_property(self) -> None:
        """Test auth token property getter and setter."""
        client = AsyncDysonClient()

        # Test initial state
        assert client.auth_token is None

        # Test setting token
        client.auth_token = "test_token"
        assert client.auth_token == "test_token"
        assert client._auth_token == "test_token"

        # Test clearing token
        client.auth_token = None
        assert client.auth_token is None
        assert client._auth_token is None

    def test_get_auth_token(self) -> None:
        """Test get_auth_token method."""
        client = AsyncDysonClient()

        assert client.get_auth_token() is None

        client.set_auth_token("test_token")
        assert client.get_auth_token() == "test_token"

    def test_set_auth_token(self) -> None:
        """Test set_auth_token method."""
        client = AsyncDysonClient()

        client.set_auth_token("test_token")
        assert client.auth_token == "test_token"

    def test_decrypt_local_credentials_success(self) -> None:
        """Test decrypt_local_credentials method with synthetic test data."""
        import base64
        import json

        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

        client = AsyncDysonClient()

        # Create test password data
        test_password = "test_password_123"
        password_data = {"apPasswordHash": test_password}

        # Convert to JSON and pad to multiple of 16 bytes
        json_data = json.dumps(password_data)
        padded_data = json_data.ljust((len(json_data) + 15) // 16 * 16, "\0")

        # Use the same encryption method as the real implementation
        aes_key = bytes(range(1, 33))  # 1,2,3,...,32
        iv = bytes(16)  # Zero-filled IV

        # Encrypt the test data
        cipher = Cipher(
            algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend()
        )
        encryptor = cipher.encryptor()
        encrypted_bytes = (
            encryptor.update(padded_data.encode("utf-8")) + encryptor.finalize()
        )

        # Base64 encode
        encrypted_b64 = base64.b64encode(encrypted_bytes).decode("ascii")

        # Test decryption
        result = client.decrypt_local_credentials(encrypted_b64, "TEST-SERIAL-123")
        assert result == test_password

    def test_decrypt_local_credentials_sync_async_parity(self) -> None:
        """Test that sync and async clients produce identical decryption results."""
        import base64
        import json

        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

        from libdyson_rest.client import DysonClient

        # Create test password data
        test_password = "sync_async_test_password"
        password_data = {"apPasswordHash": test_password}

        # Convert to JSON and pad to multiple of 16 bytes
        json_data = json.dumps(password_data)
        padded_data = json_data.ljust((len(json_data) + 15) // 16 * 16, "\0")

        # Use the same encryption method as the real implementation
        aes_key = bytes(range(1, 33))  # 1,2,3,...,32
        iv = bytes(16)  # Zero-filled IV

        # Encrypt the test data
        cipher = Cipher(
            algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend()
        )
        encryptor = cipher.encryptor()
        encrypted_bytes = (
            encryptor.update(padded_data.encode("utf-8")) + encryptor.finalize()
        )

        # Base64 encode
        encrypted_b64 = base64.b64encode(encrypted_bytes).decode("ascii")

        # Test both clients
        async_client = AsyncDysonClient()
        sync_client = DysonClient()

        async_result = async_client.decrypt_local_credentials(
            encrypted_b64, "TEST-SERIAL-456"
        )
        sync_result = sync_client.decrypt_local_credentials(
            encrypted_b64, "TEST-SERIAL-456"
        )

        # Both should produce the same result
        assert async_result == sync_result == test_password

        sync_client.close()

    def test_decrypt_local_credentials_invalid_base64(self) -> None:
        """Test decrypt_local_credentials with invalid base64 input."""
        client = AsyncDysonClient()

        with pytest.raises(DysonAPIError, match="Failed to decrypt local credentials"):
            client.decrypt_local_credentials("invalid_base64!", "TEST-SERIAL-123")

    def test_decrypt_local_credentials_invalid_encrypted_data(self) -> None:
        """Test decrypt_local_credentials with valid base64 but invalid
        encrypted data."""
        client = AsyncDysonClient()

        # Valid base64 but not valid encrypted data
        with pytest.raises(DysonAPIError, match="Failed to decrypt local credentials"):
            client.decrypt_local_credentials("dGVzdA==", "TEST-SERIAL-456")

    def test_decrypt_local_credentials_no_mqtt_device(self) -> None:
        """Test decrypt_local_credentials handles devices without MQTT (LEC_ONLY)."""
        client = AsyncDysonClient()

        # LEC_ONLY devices don't have MQTT credentials - should raise ValueError
        with pytest.raises(ValueError, match="Device has no MQTT credentials"):
            client.decrypt_local_credentials("", "BT-DEVICE-123")

        with pytest.raises(ValueError, match="Device has no MQTT credentials"):
            client.decrypt_local_credentials(None, "BT-DEVICE-123")

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_regional_endpoint_australia(self, mock_get: AsyncMock) -> None:
        """Test that Australian clients use the default .com endpoint."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = "1.0.0"
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        client = AsyncDysonClient(
            country="AU", email="test@example.com", password="password"
        )
        await client.provision()

        # Verify AU uses the default .com endpoint
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert "appapi.cp.dyson.com" in args[0]
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_regional_endpoint_new_zealand(self, mock_get: AsyncMock) -> None:
        """Test that New Zealand clients use the default .com endpoint."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = "1.0.0"
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        client = AsyncDysonClient(
            country="NZ", email="test@example.com", password="password"
        )
        await client.provision()

        # Verify NZ uses the default .com endpoint
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert "appapi.cp.dyson.com" in args[0]
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_regional_endpoint_china(self, mock_get: AsyncMock) -> None:
        """Test that Chinese clients use CN endpoint."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = "1.0.0"
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        client = AsyncDysonClient(
            country="CN", email="test@example.com", password="password"
        )
        await client.provision()

        # Verify the correct CN endpoint was called
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert "appapi.cp.dyson.cn" in args[0]
        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.get")
    @pytest.mark.asyncio
    async def test_regional_endpoint_default_fallback(
        self, mock_get: AsyncMock
    ) -> None:
        """Test that unknown countries fall back to .com endpoint."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = "1.0.0"
        mock_get.return_value = mock_response

        # Test with various countries that should fall back to .com
        test_countries = ["US", "GB", "DE", "CA", "JP"]

        for country in test_countries:
            mock_get.reset_mock()
            client = AsyncDysonClient(
                country=country, email="test@example.com", password="password"
            )
            await client.provision()

            # Verify the default .com endpoint was called
            mock_get.assert_called_once()
            args, kwargs = mock_get.call_args
            assert "appapi.cp.dyson.com" in args[0], f"Failed for country {country}"
            await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_trigger_firmware_update_success(self, mock_post: AsyncMock) -> None:
        """Test successful firmware update trigger."""
        # Mock 204 No Content response
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = AsyncDysonClient(auth_token="test_token")

        result = await client.trigger_firmware_update("MOCK-TEST-SN12345")

        assert result is True

        # Verify correct URL was called
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert "/v1/assets/devices/MOCK-TEST-SN12345/pendingrelease" in args[0]

        # Verify headers include required cache-control and content-length
        assert "headers" in kwargs
        headers = kwargs["headers"]
        assert headers["cache-control"] == "no-cache"
        assert headers["content-length"] == "0"

        await client.close()

    @pytest.mark.asyncio
    async def test_trigger_firmware_update_not_authenticated(self) -> None:
        """Test firmware update trigger fails without authentication."""
        client = AsyncDysonClient()

        with pytest.raises(
            DysonAuthError,
            match="Must authenticate before triggering firmware update",
        ):
            await client.trigger_firmware_update("MOCK-TEST-SN12345")

        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_trigger_firmware_update_401_error(
        self, mock_post: AsyncMock
    ) -> None:
        """Test firmware update trigger handles 401 authentication errors."""
        import httpx

        # Mock 401 response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_error = httpx.HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_response
        )
        mock_post.side_effect = mock_error

        client = AsyncDysonClient(auth_token="expired_token")

        with pytest.raises(
            DysonAuthError, match="Authentication token expired or invalid"
        ):
            await client.trigger_firmware_update("MOCK-TEST-SN12345")

        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_trigger_firmware_update_404_error(
        self, mock_post: AsyncMock
    ) -> None:
        """Test firmware update trigger handles 404 device not found errors."""
        import httpx

        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_error = httpx.HTTPStatusError(
            "Not Found", request=Mock(), response=mock_response
        )
        mock_post.side_effect = mock_error

        client = AsyncDysonClient(auth_token="test_token")

        with pytest.raises(
            DysonAPIError,
            match=(
                "Device MOCK-TEST-SN12345 not found or no pending firmware update "
                "available"
            ),
        ):
            await client.trigger_firmware_update("MOCK-TEST-SN12345")

        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_trigger_firmware_update_connection_error(
        self, mock_post: AsyncMock
    ) -> None:
        """Test firmware update trigger handles connection errors."""
        import httpx

        mock_post.side_effect = httpx.RequestError("Connection failed")

        client = AsyncDysonClient(auth_token="test_token")

        with pytest.raises(
            DysonConnectionError, match="Failed to trigger firmware update"
        ):
            await client.trigger_firmware_update("MOCK-TEST-SN12345")

        await client.close()

    @patch("libdyson_rest.async_client.httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_trigger_firmware_update_unexpected_status(
        self, mock_post: AsyncMock
    ) -> None:
        """Test firmware update trigger handles unexpected response status."""
        mock_response = Mock()
        mock_response.status_code = 200  # Unexpected, should be 204
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = AsyncDysonClient(auth_token="test_token")

        with pytest.raises(DysonAPIError, match="Unexpected response status: 200"):
            await client.trigger_firmware_update("MOCK-TEST-SN12345")

        await client.close()
