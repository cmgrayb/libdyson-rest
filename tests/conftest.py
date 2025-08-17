"""Pytest configuration and shared fixtures."""

from unittest.mock import Mock

import pytest

from libdyson_rest import DysonClient


@pytest.fixture
def mock_dyson_client() -> DysonClient:
    """Create a mock Dyson client for testing."""
    client = DysonClient(email="test@example.com", password="test_password", country="US")
    return client


@pytest.fixture
def authenticated_client() -> DysonClient:
    """Create an authenticated mock client."""
    client = DysonClient(email="test@example.com", password="test_password")
    client.auth_token = "mock_token_123"
    client.account_id = "mock_account_456"
    client.session.headers["Authorization"] = "Bearer mock_token_123"
    return client


@pytest.fixture
def mock_api_response() -> Mock:
    """Create a mock API response object."""
    response = Mock()
    response.raise_for_status.return_value = None
    response.status_code = 200
    return response
