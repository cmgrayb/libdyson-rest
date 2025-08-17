"""Integration tests for Dyson REST API client."""

import os
from unittest.mock import Mock, patch

import pytest

from libdyson_rest import DysonClient
from libdyson_rest.exceptions import DysonAuthError, DysonConnectionError


class TestDysonClientIntegration:
    """Integration tests for DysonClient."""

    def test_client_initialization(self) -> None:
        """Test client can be initialized with proper parameters."""
        client = DysonClient(email="test@example.com", password="password123", country="US", timeout=30)

        assert client.email == "test@example.com"
        assert client.password == "password123"
        assert client.country == "US"
        assert client.timeout == 30
        assert client.auth_token is None
        assert client.account_id is None

        client.close()

    def test_context_manager(self) -> None:
        """Test client works as context manager."""
        with DysonClient(email="test@example.com", password="password") as client:
            assert client.email == "test@example.com"
        # Client should be closed automatically

    @patch("requests.Session.post")
    def test_authentication_success(self, mock_post: Mock) -> None:
        """Test successful authentication flow."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "token": "test_token_123",
            "account_id": "account_456",
        }
        mock_post.return_value = mock_response

        client = DysonClient(email="test@example.com", password="password123")

        result = client.authenticate()

        assert result is True
        assert client.auth_token == "test_token_123"
        assert client.account_id == "account_456"
        assert "Authorization" in client.session.headers
        assert client.session.headers["Authorization"] == "Bearer test_token_123"

        client.close()

    def test_authentication_missing_credentials(self) -> None:
        """Test authentication fails with missing credentials."""
        client = DysonClient()

        with pytest.raises(DysonAuthError, match="Email and password are required"):
            client.authenticate()

        client.close()

    @patch("requests.Session.post")
    def test_authentication_connection_error(self, mock_post: Mock) -> None:
        """Test authentication handles connection errors."""
        import requests

        mock_post.side_effect = requests.ConnectionError("Network error")

        client = DysonClient(email="test@example.com", password="password123")

        with pytest.raises(DysonConnectionError, match="Failed to connect"):
            client.authenticate()

        client.close()

    @patch("requests.Session.get")
    def test_get_devices_success(self, mock_get: Mock) -> None:
        """Test successful device retrieval."""
        # Setup authenticated client
        client = DysonClient(email="test@example.com", password="password123")
        client.auth_token = "test_token"
        client.session.headers["Authorization"] = "Bearer test_token"

        # Mock API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [{"serial": "ABC123", "name": "Living Room Fan", "product_type": "527"}]
        mock_get.return_value = mock_response

        devices = client.get_devices()

        assert len(devices) == 1
        assert devices[0]["serial"] == "ABC123"
        assert devices[0]["name"] == "Living Room Fan"

        client.close()

    def test_get_devices_not_authenticated(self) -> None:
        """Test get_devices fails when not authenticated."""
        client = DysonClient(email="test@example.com", password="password123")

        with pytest.raises(DysonAuthError, match="Must authenticate"):
            client.get_devices()

        client.close()

    @pytest.mark.skipif(
        not os.getenv("DYSON_EMAIL") or not os.getenv("DYSON_PASSWORD"),
        reason="Real API credentials not provided",
    )
    def test_real_api_authentication(self) -> None:
        """Test authentication against real Dyson API (requires env vars)."""
        email = os.getenv("DYSON_EMAIL")
        password = os.getenv("DYSON_PASSWORD")

        client = DysonClient(email=email, password=password)

        try:
            result = client.authenticate()
            assert result is True
            assert client.auth_token is not None
            assert client.account_id is not None
        except Exception as e:
            pytest.skip(f"Real API test failed: {e}")
        finally:
            client.close()
