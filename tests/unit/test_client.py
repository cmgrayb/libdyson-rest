"""Unit tests for Dyson REST API client."""

from unittest.mock import Mock, patch

import pytest

from libdyson_rest.client import DysonClient
from libdyson_rest.exceptions import DysonAuthError


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
        """Test successful authentication."""
        # Setup mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "token": "test_token",
            "account_id": "test_account",
        }
        mock_post.return_value = mock_response

        client = DysonClient(email="test@example.com", password="password")
        result = client.authenticate()

        assert result is True
        assert client.auth_token == "test_token"
        assert client.account_id == "test_account"

        # Check authorization header was set
        auth_header = client.session.headers.get("Authorization")
        assert auth_header == "Bearer test_token"

        client.close()

    def test_decrypt_password_fallback(self) -> None:
        """Test password decryption falls back to plain text."""
        client = DysonClient()

        # Test with plain text password (should return as-is)
        result = client._decrypt_password("plain_password")
        assert result == "plain_password"

        client.close()

    def test_context_manager(self) -> None:
        """Test client works as context manager."""
        with DysonClient(email="test@example.com") as client:
            assert client.email == "test@example.com"
            # Client session should be active
            assert client.session is not None

        # After exiting context, client should be closed
        # (In real implementation, session would be closed)
