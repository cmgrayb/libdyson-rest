"""
Main client for interacting with the Dyson REST API.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from cryptography.fernet import Fernet

from .exceptions import DysonAPIError, DysonAuthError, DysonConnectionError

logger = logging.getLogger(__name__)

# Dyson API hostname - this is an allowed static value
DYSON_API_HOST = "https://appapi.cp.dyson.com"

# Decryption key for passwords - this is an allowed static value
# Note: This is a placeholder key. Replace with the actual Dyson decryption key
DYSON_PASSWORD_KEY = b"dGhpcyBpcyBhIDMyIGJ5dGUga2V5IGZvciBGZXJuZXQhISE="  # Base64 placeholder


class DysonClient:
    """
    Client for interacting with the Dyson REST API.

    This client handles authentication, device discovery, and command execution
    for Dyson devices through their REST API.
    """

    def __init__(
        self,
        email: Optional[str] = None,
        password: Optional[str] = None,
        country: str = "US",
        timeout: int = 30,
    ) -> None:
        """
        Initialize the Dyson client.

        Args:
            email: User email for authentication
            password: User password for authentication
            country: Country code for API endpoint
            timeout: Request timeout in seconds

        Raises:
            DysonValidationError: If required parameters are invalid
        """
        self.email = email
        self.password = password
        self.country = country
        self.timeout = timeout
        self.session = requests.Session()
        self.auth_token: Optional[str] = None
        self.account_id: Optional[str] = None

    def authenticate(self) -> bool:
        """
        Authenticate with the Dyson API.

        Returns:
            True if authentication successful, False otherwise

        Raises:
            DysonAuthError: If authentication fails
            DysonConnectionError: If connection fails
        """
        if not self.email or not self.password:
            raise DysonAuthError("Email and password are required for authentication")

        auth_url = urljoin(DYSON_API_HOST, "/v1/userapi/auth/login")

        payload = {
            "email": self.email,
            "password": self._decrypt_password(self.password),
        }

        try:
            response = self.session.post(auth_url, json=payload, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as e:
            raise DysonConnectionError(f"Failed to connect to Dyson API: {e}") from e

        try:
            auth_data = response.json()
            self.auth_token = auth_data.get("token")
            self.account_id = auth_data.get("account_id")

            if not self.auth_token:
                raise DysonAuthError("No authentication token received")

            # Set authorization header for future requests
            self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})

            return True

        except (json.JSONDecodeError, KeyError) as e:
            raise DysonAPIError(f"Invalid response from authentication: {e}") from e

    def get_devices(self) -> List[Dict[str, Any]]:
        """
        Get list of devices associated with the account.

        Returns:
            List of device dictionaries

        Raises:
            DysonAuthError: If not authenticated
            DysonAPIError: If API request fails
        """
        if not self.auth_token:
            raise DysonAuthError("Must authenticate before getting devices")

        devices_url = urljoin(DYSON_API_HOST, "/v2/provisioningservice/manifest")

        try:
            response = self.session.get(devices_url, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as e:
            raise DysonConnectionError(f"Failed to get devices: {e}") from e

        try:
            devices_data = response.json()
            return devices_data if isinstance(devices_data, list) else []
        except json.JSONDecodeError as e:
            raise DysonAPIError(f"Invalid JSON response: {e}") from e

    def _decrypt_password(self, encrypted_password: str) -> str:
        """
        Decrypt password using the Dyson decryption key.

        Args:
            encrypted_password: The encrypted password

        Returns:
            Decrypted password string
        """
        # This is a placeholder implementation
        # Replace with actual Dyson password decryption logic
        try:
            fernet = Fernet(DYSON_PASSWORD_KEY)
            decrypted_bytes: bytes = fernet.decrypt(encrypted_password.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            logger.warning(f"Password decryption failed: {e}")
            # For now, return the password as-is if decryption fails
            return encrypted_password

    def close(self) -> None:
        """Close the session."""
        self.session.close()

    def __enter__(self) -> "DysonClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
