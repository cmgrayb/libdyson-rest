"""Unit tests for Dyson REST API client."""

from unittest.mock import Mock, patch

import pytest
import requests

from libdyson_rest.client import DysonClient
from libdyson_rest.exceptions import DysonAPIError, DysonAuthError, DysonConnectionError


class TestDysonClient:
    """Unit tests for DysonClient class."""

    def test_client_initialization_with_defaults(self) -> None:
        """Test client initializes with default values."""
        client = DysonClient()

        assert client.email is None
        assert client.password is None
        assert client.country == "US"
        assert client.timeout == 30
        assert client.auth_token is None
        assert client.account_id is None

        client.close()

    def test_client_initialization_with_custom_values(self) -> None:
        """Test client initializes with custom values."""
        client = DysonClient(
            email="custom@email.com",
            password="custom_password",
            country="UK",
            timeout=60,
        )

        assert client.email == "custom@email.com"
        assert client.password == "custom_password"
        assert client.country == "UK"
        assert client.timeout == 60

        client.close()

    def test_authentication_no_credentials(self) -> None:
        """Test authentication fails without credentials."""
        client = DysonClient()

        with pytest.raises(DysonAuthError) as exc_info:
            client.authenticate()

        assert "Email and password are required" in str(exc_info.value)
        client.close()

    @patch("requests.Session.post")
    def test_authentication_success(self, mock_post: Mock) -> None:
        """Test successful user status check."""
        # Setup mock response for get_user_status
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "accountStatus": "ACTIVE",
            "authenticationMethod": "EMAIL_PWD_2FA",
        }
        mock_post.return_value = mock_response

        client = DysonClient(email="test@example.com", password="password")
        # Test individual method instead of full authenticate()
        user_status = client.get_user_status()

        assert user_status.account_status.value == "ACTIVE"
        assert user_status.authentication_method.value == "EMAIL_PWD_2FA"

        client.close()

    @patch("requests.Session.post")
    def test_begin_login_success(self, mock_post: Mock) -> None:
        """Test successful begin login."""
        # Setup mock response for begin_login
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "challengeId": "12345678-1234-5678-9abc-123456789abc",
        }
        mock_post.return_value = mock_response

        client = DysonClient(email="test@example.com", password="password")
        challenge = client.begin_login()

        assert str(challenge.challenge_id) == "12345678-1234-5678-9abc-123456789abc"

        client.close()

    @patch("requests.Session.post")
    def test_complete_login_success(self, mock_post: Mock) -> None:
        """Test successful complete login."""
        # Setup mock response for complete_login
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "account": "12345678-1234-5678-9abc-123456789abc",
            "token": "test_bearer_token_123",
            "tokenType": "Bearer",
        }
        mock_post.return_value = mock_response

        client = DysonClient(email="test@example.com", password="password")
        login_info = client.complete_login(
            "12345678-1234-5678-9abc-123456789abc", "123456"
        )

        assert str(login_info.account) == "12345678-1234-5678-9abc-123456789abc"
        assert login_info.token == "test_bearer_token_123"
        assert client.auth_token == "test_bearer_token_123"
        assert "Authorization" in client.session.headers

        # Check authorization header was set
        auth_header = client.session.headers.get("Authorization")
        assert auth_header == "Bearer test_bearer_token_123"

    @patch("requests.Session.post")
    def test_authentication_with_invalid_country(self, mock_post: Mock) -> None:
        """Test authentication with invalid country code."""
        with pytest.raises(
            ValueError,
            match="Country must be a 2-character uppercase ISO 3166-1 alpha-2 code",
        ):
            DysonClient(
                email="test@example.com", password="password", country="invalid"
            )

    @patch("requests.Session.post")
    def test_authentication_with_invalid_culture(self, mock_post: Mock) -> None:
        """Test authentication with invalid culture code."""
        with pytest.raises(ValueError, match="Culture must be in format 'xx-YY'"):
            DysonClient(
                email="test@example.com", password="password", culture="invalid"
            )

    @patch("requests.Session.get")
    def test_provision_success(self, mock_get: Mock) -> None:
        """Test successful provision call."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"version": "1.0.0"}
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        client = DysonClient(email="test@example.com", password="password")
        version = client.provision()

        assert version == "{'version': '1.0.0'}"
        assert client._provisioned is True
        mock_get.assert_called_once()

    @patch("requests.Session.get")
    def test_provision_connection_error(self, mock_get: Mock) -> None:
        """Test provision with connection error."""
        mock_get.side_effect = requests.RequestException("Connection failed")

        client = DysonClient(email="test@example.com", password="password")
        with pytest.raises(
            DysonConnectionError, match="Failed to provision API access"
        ):
            client.provision()

    def test_client_with_auth_token_initialization(self) -> None:
        """Test client initialization with auth token."""
        client = DysonClient(
            email="test@example.com", password="password", auth_token="test_token"
        )
        assert client.auth_token == "test_token"
        assert client.session.headers.get("Authorization") == "Bearer test_token"

    def test_get_set_auth_token(self) -> None:
        """Test get and set auth token methods."""
        client = DysonClient(email="test@example.com", password="password")

        # Initially no token
        assert client.get_auth_token() is None

        # Set a token
        client.set_auth_token("new_token")
        assert client.get_auth_token() == "new_token"
        assert client.session.headers.get("Authorization") == "Bearer new_token"

        client.close()

    def test_decrypt_local_credentials_invalid_data(self) -> None:
        """Test decrypt_local_credentials handles invalid data."""
        client = DysonClient()

        # Test with invalid base64 data
        with pytest.raises(DysonAPIError, match="Failed to decrypt local credentials"):
            client.decrypt_local_credentials("invalid_base64!", "SERIAL123")

        client.close()

    def test_context_manager(self) -> None:
        """Test client works as context manager."""
        with DysonClient(email="test@example.com") as client:
            assert client.email == "test@example.com"
            # Client session should be active
            assert client.session is not None

        # After exiting context, client should be closed
        # (In real implementation, session would be closed)

    @patch("libdyson_rest.client.requests.Session.get")
    def test_get_pending_release_success(self, mock_get: Mock) -> None:
        """Test successful pending release retrieval."""
        # Mock response data
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "version": "MOCK.99.99.999.9999",
            "pushed": False,
        }
        mock_get.return_value = mock_response

        client = DysonClient(auth_token="test_token")

        pending_release = client.get_pending_release("MOCK-TEST-SN12345")

        assert pending_release.version == "MOCK.99.99.999.9999"
        assert pending_release.pushed is False

        # Verify correct URL was called
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert "/v1/assets/devices/MOCK-TEST-SN12345/pendingrelease" in args[0]

        client.close()

    def test_get_pending_release_not_authenticated(self) -> None:
        """Test pending release retrieval fails without authentication."""
        client = DysonClient()

        with pytest.raises(
            DysonAuthError,
            match="Must authenticate before getting pending release info",
        ):
            client.get_pending_release("MOCK-TEST-SN12345")

        client.close()

    @patch("libdyson_rest.client.requests.Session.get")
    def test_get_pending_release_api_error(self, mock_get: Mock) -> None:
        """Test pending release retrieval handles API errors."""
        mock_get.side_effect = requests.RequestException("Network error")

        client = DysonClient(auth_token="test_token")

        with pytest.raises(DysonConnectionError, match="Failed to get pending release"):
            client.get_pending_release("MOCK-TEST-SN12345")

        client.close()

    @patch("libdyson_rest.client.requests.Session.post")
    def test_complete_login_401_error(self, mock_post: Mock) -> None:
        """Test complete_login handles 401 authentication errors."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_error = requests.RequestException("Unauthorized")
        mock_error.response = mock_response
        mock_post.side_effect = mock_error

        client = DysonClient("test@example.com", "password")

        with pytest.raises(DysonAuthError, match="Invalid credentials or OTP code"):
            client.complete_login("challenge123", "123456")

        client.close()

    @patch("libdyson_rest.client.requests.Session.post")
    def test_complete_login_400_error(self, mock_post: Mock) -> None:
        """Test complete_login handles 400 bad request errors."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_response.url = "https://api.example.com/login"
        mock_error = requests.RequestException("Bad Request")
        mock_error.response = mock_response
        mock_error.request = Mock()
        mock_error.request.headers = {"Content-Type": "application/json"}
        mock_post.side_effect = mock_error

        client = DysonClient("test@example.com", "password")

        with pytest.raises(DysonAuthError, match="Bad request to Dyson API \\(400\\)"):
            client.complete_login("challenge123", "123456")

        client.close()

    @patch("libdyson_rest.client.requests.Session.post")
    def test_complete_login_400_error_logging_exception(self, mock_post: Mock) -> None:
        """Test complete_login handles 400 errors when logging fails."""
        mock_response = Mock()
        mock_response.status_code = 400
        # Make response.text raise an exception to test logging error handling
        mock_response.text = Mock(side_effect=AttributeError("No text"))
        mock_response.url = "https://api.example.com/login"
        mock_error = requests.RequestException("Bad Request")
        mock_error.response = mock_response
        mock_post.side_effect = mock_error

        client = DysonClient("test@example.com", "password")

        with pytest.raises(DysonAuthError, match="Bad request to Dyson API \\(400\\)"):
            client.complete_login("challenge123", "123456")

        client.close()

    @patch("libdyson_rest.client.requests.Session.post")
    def test_complete_login_connection_error(self, mock_post: Mock) -> None:
        """Test complete_login handles general connection errors."""
        mock_post.side_effect = requests.RequestException("Connection failed")

        client = DysonClient("test@example.com", "password")

        with pytest.raises(DysonConnectionError, match="Failed to complete login"):
            client.complete_login("challenge123", "123456")

        client.close()

    @patch("libdyson_rest.client.requests.Session.post")
    def test_complete_login_invalid_json_response(self, mock_post: Mock) -> None:
        """Test complete_login handles invalid JSON responses."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = DysonClient("test@example.com", "password")

        with pytest.raises(DysonAPIError, match="Invalid login response"):
            client.complete_login("challenge123", "123456")

        client.close()

    @patch("libdyson_rest.client.requests.Session.post")
    def test_complete_login_missing_key_response(self, mock_post: Mock) -> None:
        """Test complete_login handles responses with missing keys."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"invalid": "data"}  # Missing required keys
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = DysonClient("test@example.com", "password")

        # The validation layer raises JSONValidationError, which gets caught and
        # re-raised as DysonAPIError
        with pytest.raises(DysonAPIError, match="Invalid login response"):
            client.complete_login("challenge123", "123456")

        client.close()

    @patch("requests.Session.get")
    def test_regional_endpoint_australia(self, mock_get: Mock) -> None:
        """Test that Australian clients use the default .com endpoint."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"version": "1.0.0"}
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        client = DysonClient(
            country="AU", email="test@example.com", password="password"
        )
        client.provision()

        # Verify AU uses the default .com endpoint
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert "appapi.cp.dyson.com" in args[0]
        client.close()

    @patch("requests.Session.get")
    def test_regional_endpoint_new_zealand(self, mock_get: Mock) -> None:
        """Test that New Zealand clients use the default .com endpoint."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.status_code = 200
        mock_response.json.return_value = {"version": "1.0.0"}
        mock_get.return_value = mock_response

        client = DysonClient(
            country="NZ", email="test@example.com", password="password"
        )
        client.provision()

        # Verify NZ uses the default .com endpoint
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert "appapi.cp.dyson.com" in args[0]
        client.close()

    @patch("requests.Session.get")
    def test_regional_endpoint_china(self, mock_get: Mock) -> None:
        """Test that Chinese clients use CN endpoint."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"version": "1.0.0"}
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        client = DysonClient(
            country="CN", email="test@example.com", password="password"
        )
        client.provision()

        # Verify the correct CN endpoint was called
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert "appapi.cp.dyson.cn" in args[0]
        client.close()

    @patch("requests.Session.get")
    def test_regional_endpoint_default_fallback(self, mock_get: Mock) -> None:
        """Test that unknown countries fall back to .com endpoint."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"version": "1.0.0"}
        mock_get.return_value = mock_response

        # Test with various countries that should fall back to .com
        test_countries = ["US", "GB", "DE", "CA", "JP"]

        for country in test_countries:
            mock_get.reset_mock()
            client = DysonClient(
                country=country, email="test@example.com", password="password"
            )
            client.provision()

            # Verify the default .com endpoint was called
            mock_get.assert_called_once()
            args, kwargs = mock_get.call_args
            assert "appapi.cp.dyson.com" in args[0], f"Failed for country {country}"
            client.close()

    @patch("libdyson_rest.client.requests.Session.post")
    def test_trigger_firmware_update_success(self, mock_post: Mock) -> None:
        """Test successful firmware update trigger."""
        # Mock 204 No Content response
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = DysonClient(auth_token="test_token")

        result = client.trigger_firmware_update("MOCK-TEST-SN12345")

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

        client.close()

    def test_trigger_firmware_update_not_authenticated(self) -> None:
        """Test firmware update trigger fails without authentication."""
        client = DysonClient()

        with pytest.raises(
            DysonAuthError,
            match="Must authenticate before triggering firmware update",
        ):
            client.trigger_firmware_update("MOCK-TEST-SN12345")

        client.close()

    @patch("libdyson_rest.client.requests.Session.post")
    def test_trigger_firmware_update_401_error(self, mock_post: Mock) -> None:
        """Test firmware update trigger handles 401 authentication errors."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_error = requests.RequestException("Unauthorized")
        mock_error.response = mock_response
        mock_post.side_effect = mock_error

        client = DysonClient(auth_token="expired_token")

        with pytest.raises(
            DysonAuthError, match="Authentication token expired or invalid"
        ):
            client.trigger_firmware_update("MOCK-TEST-SN12345")

        client.close()

    @patch("libdyson_rest.client.requests.Session.post")
    def test_trigger_firmware_update_404_error(self, mock_post: Mock) -> None:
        """Test firmware update trigger handles 404 device not found errors."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_error = requests.RequestException("Not Found")
        mock_error.response = mock_response
        mock_post.side_effect = mock_error

        client = DysonClient(auth_token="test_token")

        with pytest.raises(
            DysonAPIError,
            match=(
                "Device MOCK-TEST-SN12345 not found or no pending firmware update "
                "available"
            ),
        ):
            client.trigger_firmware_update("MOCK-TEST-SN12345")

        client.close()

    @patch("libdyson_rest.client.requests.Session.post")
    def test_trigger_firmware_update_connection_error(self, mock_post: Mock) -> None:
        """Test firmware update trigger handles connection errors."""
        mock_post.side_effect = requests.RequestException("Connection failed")

        client = DysonClient(auth_token="test_token")

        with pytest.raises(
            DysonConnectionError, match="Failed to trigger firmware update"
        ):
            client.trigger_firmware_update("MOCK-TEST-SN12345")

        client.close()

    @patch("libdyson_rest.client.requests.Session.post")
    def test_trigger_firmware_update_unexpected_status(self, mock_post: Mock) -> None:
        """Test firmware update trigger handles unexpected response status."""
        mock_response = Mock()
        mock_response.status_code = 200  # Unexpected, should be 204
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = DysonClient(auth_token="test_token")

        with pytest.raises(DysonAPIError, match="Unexpected response status: 200"):
            client.trigger_firmware_update("MOCK-TEST-SN12345")

        client.close()
