"""
Main client for interacting with the Dyson REST API.

This client implements the official Dyson App API as documented in the OpenAPI specification.
Authentication uses a two-step process with OTP codes.
"""

import base64
import json
import logging
from typing import Any, cast
from urllib.parse import urljoin

import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from .exceptions import DysonAPIError, DysonAuthError, DysonConnectionError
from .models import (
    Device,
    IoTData,
    LoginChallenge,
    LoginInformation,
    PendingRelease,
    UserStatus,
)
from .types import (
    DeviceResponseDict,
    IoTDataResponseDict,
    LoginChallengeResponseDict,
    LoginInformationResponseDict,
    PendingReleaseResponseDict,
    UserStatusResponseDict,
)

logger = logging.getLogger(__name__)

# Dyson API hostname - this is an allowed static value
DYSON_API_HOST = "https://appapi.cp.dyson.com"

# Default headers required by the API
DEFAULT_USER_AGENT = "android client"


class DysonClient:
    """
    Client for interacting with the Dyson REST API.

    This client handles the complete authentication flow, device discovery, and IoT credential
    retrieval for Dyson devices through their REST API according to the OpenAPI specification.

    Authentication Flow:
    1. provision() - Required initial call
    2. get_user_status() - Check user account status
    3. begin_login() - Start authentication process
    4. complete_login() - Complete authentication with OTP code
    5. API calls with Bearer token
    """

    def __init__(
        self,
        email: str | None = None,
        password: str | None = None,
        auth_token: str | None = None,
        country: str = "US",
        culture: str = "en-US",
        timeout: int = 30,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        """
        Initialize the Dyson client.

        Args:
            email: User email for authentication
            password: User password for authentication
            auth_token: Existing bearer token (skips authentication flow if provided)
            country: Country code for API endpoint (2-letter ISO 3166-1 alpha-2)
            culture: Locale/language code (IETF language code, e.g., 'en-US')
            timeout: Request timeout in seconds
            user_agent: User agent string for requests

        Raises:
            ValueError: If country or culture format is invalid
        """
        # Validate country format
        if not (country and len(country) == 2 and country.isupper()):
            raise ValueError(
                "Country must be a 2-character uppercase ISO 3166-1 alpha-2 code"
            )

        # Validate culture format
        if not (
            culture
            and len(culture) == 5
            and culture[2] == "-"
            and culture[:2].islower()
            and culture[3:].isupper()
        ):
            raise ValueError("Culture must be in format 'xx-YY' (e.g., 'en-US')")

        self.email = email
        self.password = password
        self.country = country
        self.culture = culture
        self.timeout = timeout
        self.user_agent = user_agent

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

        # Authentication state
        self._auth_token: str | None = auth_token
        self.account_id: str | None = None
        self._provisioned = False

        # If auth_token provided, set up session headers immediately
        if auth_token:
            self.session.headers.update({"Authorization": f"Bearer {auth_token}"})

    def provision(self) -> str:
        """
        Make the required provisioning call to the API.

        This call must be made before any other API calls. The server will ignore
        all other requests from clients which haven't made this request recently.

        Returns:
            Version string from the API

        Raises:
            DysonConnectionError: If connection fails
            DysonAPIError: If API request fails
        """
        url = urljoin(
            DYSON_API_HOST, "/v1/provisioningservice/application/Android/version"
        )

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as e:
            raise DysonConnectionError(f"Failed to provision API access: {e}") from e

        try:
            version_data = response.json()
            self._provisioned = True
            version = str(version_data) if version_data is not None else ""
            logger.info(f"API provisioned successfully, version: {version}")
            return version
        except json.JSONDecodeError as e:
            raise DysonAPIError(f"Invalid JSON response from provision: {e}") from e

    def get_user_status(self, email: str | None = None) -> UserStatus:
        """
        Get the status of a user account.

        Args:
            email: Email address to check. If None, uses client's email.

        Returns:
            UserStatus object with account status and authentication method

        Raises:
            DysonConnectionError: If connection fails
            DysonAPIError: If API request fails
        """
        if not self._provisioned:
            self.provision()

        target_email = email or self.email
        if not target_email:
            raise DysonAPIError("Email address is required")

        url = urljoin(DYSON_API_HOST, "/v3/userregistration/email/userstatus")
        params = {"country": self.country}
        payload = {"email": target_email}

        try:
            response = self.session.post(
                url, params=params, json=payload, timeout=self.timeout
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise DysonConnectionError(f"Failed to get user status: {e}") from e

        try:
            data = response.json()
            # Type safety: cast to UserStatusResponseDict
            typed_data = cast(UserStatusResponseDict, data)
            return UserStatus.from_dict(typed_data)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(f"Invalid user status response: {e}") from e

    def begin_login(self, email: str | None = None) -> LoginChallenge:
        """
        Begin the login process by requesting a challenge ID.

        Args:
            email: Email address for login. If None, uses client's email.

        Returns:
            LoginChallenge object with challenge ID for completing login

        Raises:
            DysonConnectionError: If connection fails
            DysonAPIError: If API request fails
        """
        if not self._provisioned:
            self.provision()

        target_email = email or self.email
        if not target_email:
            raise DysonAPIError("Email address is required")

        url = urljoin(DYSON_API_HOST, "/v3/userregistration/email/auth")
        params = {"country": self.country, "culture": self.culture}
        payload = {"email": target_email}

        try:
            response = self.session.post(
                url, params=params, json=payload, timeout=self.timeout
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise DysonConnectionError(f"Failed to begin login: {e}") from e

        try:
            data = response.json()
            # Type safety: cast to LoginChallengeResponseDict
            typed_data = cast(LoginChallengeResponseDict, data)
            return LoginChallenge.from_dict(typed_data)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(f"Invalid login challenge response: {e}") from e

    def complete_login(
        self,
        challenge_id: str,
        otp_code: str,
        email: str | None = None,
        password: str | None = None,
    ) -> LoginInformation:
        """
        Complete the login process with the challenge response.

        Args:
            challenge_id: Challenge ID from begin_login()
            otp_code: One-time password code (usually from email or SMS)
            email: Email address for login. If None, uses client's email.
            password: Password for login. If None, uses client's password.

        Returns:
            LoginInformation: Contains account and token information

        Raises:
            DysonAuthError: If authentication fails
            DysonConnectionError: If connection fails
            DysonAPIError: If API request fails
        """
        if not self._provisioned:
            self.provision()

        target_email = email or self.email
        target_password = password or self.password

        if not target_email or not target_password:
            raise DysonAuthError("Email and password are required for authentication")

        url = urljoin(DYSON_API_HOST, "/v3/userregistration/email/verify")
        params = {"country": self.country, "culture": self.culture}
        payload = {
            "challengeId": challenge_id,
            "email": target_email,
            "otpCode": otp_code,
            "password": target_password,
        }

        try:
            response = self.session.post(
                url, params=params, json=payload, timeout=self.timeout
            )
            response.raise_for_status()
        except requests.RequestException as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Invalid credentials or OTP code") from e
            raise DysonConnectionError(f"Failed to complete login: {e}") from e

        try:
            data = response.json()
            # Type safety: cast to LoginInformationResponseDict
            typed_data = cast(LoginInformationResponseDict, data)
            login_info = LoginInformation.from_dict(typed_data)

            # Store authentication details
            self._auth_token = login_info.token
            self.account_id = str(login_info.account)

            # Set authorization header for future requests
            self.session.headers.update({"Authorization": f"Bearer {self._auth_token}"})

            logger.info(f"Authentication successful for account: {self.account_id}")
            return login_info

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(f"Invalid login response: {e}") from e

    def authenticate(self, otp_code: str | None = None) -> bool:
        """
        Convenience method for complete authentication flow.

        This method handles the full authentication process:
        1. Provision API access
        2. Check user status
        3. Begin login process
        4. Complete login with OTP (if provided)

        Args:
            otp_code: One-time password code. If None, only completes up to begin_login()

        Returns:
            True if authentication successful (or if OTP required and not provided)

        Raises:
            DysonAuthError: If authentication fails
            DysonConnectionError: If connection fails
            DysonAPIError: If API request fails
        """
        if not self.email or not self.password:
            raise DysonAuthError("Email and password are required for authentication")

        # Provision API access
        self.provision()

        # Check user status
        user_status = self.get_user_status()
        logger.info(f"User status: {user_status.account_status.value}")

        # Begin login process
        challenge = self.begin_login()
        logger.info(f"Login challenge received: {challenge.challenge_id}")

        # If OTP code provided, complete the login
        if otp_code:
            self.complete_login(str(challenge.challenge_id), otp_code)
            return True

        # OTP code required - user needs to provide it via complete_login()
        logger.info("OTP code required to complete authentication")
        return True

    def get_devices(self) -> list[Device]:
        """
        Get list of devices associated with the authenticated account.

        Returns:
            List of Device objects

        Raises:
            DysonAuthError: If not authenticated
            DysonConnectionError: If connection fails
            DysonAPIError: If API request fails
        """
        if not self._auth_token:
            raise DysonAuthError("Must authenticate before getting devices")

        url = urljoin(DYSON_API_HOST, "/v3/manifest")

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to get devices: {e}") from e

        try:
            devices_data = response.json()
            if not isinstance(devices_data, list):
                raise DysonAPIError("Expected list of devices in response")

            # Type safety: cast each device data dict to DeviceResponseDict
            typed_devices = [
                cast(DeviceResponseDict, device) for device in devices_data
            ]
            return [Device.from_dict(device_data) for device_data in typed_devices]
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(f"Invalid devices response: {e}") from e

    def get_iot_credentials(self, serial_number: str) -> IoTData:
        """
        Get AWS IoT connection credentials for a specific device.

        Args:
            serial_number: Device serial number

        Returns:
            IoTData object with endpoint and credentials

        Raises:
            DysonAuthError: If not authenticated
            DysonConnectionError: If connection fails
            DysonAPIError: If API request fails
        """
        if not self._auth_token:
            raise DysonAuthError("Must authenticate before getting IoT credentials")

        url = urljoin(DYSON_API_HOST, "/v2/authorize/iot-credentials")
        payload = {"Serial": serial_number}

        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to get IoT credentials: {e}") from e

        try:
            data = response.json()
            # Type safety: cast to IoTDataResponseDict
            typed_data = cast(IoTDataResponseDict, data)
            return IoTData.from_dict(typed_data)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(f"Invalid IoT credentials response: {e}") from e

    def get_pending_release(self, serial_number: str) -> PendingRelease:
        """
        Get pending firmware release information for a specific device.

        Args:
            serial_number: Device serial number

        Returns:
            PendingRelease object with version and push status

        Raises:
            DysonAuthError: If not authenticated
            DysonConnectionError: If connection fails
            DysonAPIError: If API request fails
        """
        if not self._auth_token:
            raise DysonAuthError(
                "Must authenticate before getting pending release info"
            )

        url = urljoin(
            DYSON_API_HOST, f"/v1/assets/devices/{serial_number}/pendingrelease"
        )

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to get pending release: {e}") from e

        try:
            data = response.json()
            # Type safety: cast to PendingReleaseResponseDict
            typed_data = cast(PendingReleaseResponseDict, data)
            return PendingRelease.from_dict(typed_data)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(f"Invalid pending release response: {e}") from e

    def decrypt_local_credentials(
        self, encrypted_password: str, serial_number: str
    ) -> str:
        """
        Decrypt the local MQTT broker credentials for direct device connection.

        This method decrypts the MQTT password needed to connect to the device's
        local MQTT broker when on the same network.

        Args:
            encrypted_password: Base64 encoded encrypted password from
                device.connected_configuration.mqtt.local_broker_credentials
            serial_number: Device serial number used as decryption key

        Returns:
            Decrypted MQTT password for local broker connection

        Raises:
            DysonAPIError: If decryption fails
        """
        try:
            # Fixed AES key used by Dyson (from Go implementation)
            aes_key = bytes(
                [
                    1,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    11,
                    12,
                    13,
                    14,
                    15,
                    16,
                    17,
                    18,
                    19,
                    20,
                    21,
                    22,
                    23,
                    24,
                    25,
                    26,
                    27,
                    28,
                    29,
                    30,
                    31,
                    32,
                ]
            )

            # Zero-filled 16-byte IV
            iv = bytes(16)

            # Decode the base64 encrypted password
            encrypted_bytes = base64.b64decode(encrypted_password)

            # Create AES-CBC cipher
            cipher = Cipher(
                algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend()
            )
            decryptor = cipher.decryptor()

            # Decrypt the data
            decrypted_bytes = decryptor.update(encrypted_bytes) + decryptor.finalize()

            # Remove padding (trim backspace characters)
            decrypted_text = decrypted_bytes.decode("utf-8").rstrip("\b").rstrip("\x00")

            # Parse JSON to extract password
            password_data = json.loads(decrypted_text)
            return str(password_data["apPasswordHash"])

        except Exception as e:
            raise DysonAPIError(f"Failed to decrypt local credentials: {e}") from e

    def get_auth_token(self) -> str | None:
        """
        Get the current authentication token.

        Returns:
            The current bearer token if authenticated, None otherwise
        """
        return self._auth_token

    def set_auth_token(self, token: str) -> None:
        """
        Set the authentication token directly.

        This allows reusing an existing token without going through the full
        authentication flow. The token should be obtained from a previous
        authentication session.

        Args:
            token: Bearer token from previous authentication
        """
        self._auth_token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        logger.info("Authentication token set directly")

    @property
    def auth_token(self) -> str | None:
        """
        Get the current authentication token.

        Returns:
            The current bearer token if authenticated, None otherwise
        """
        return self._auth_token

    @auth_token.setter
    def auth_token(self, value: str | None) -> None:
        """
        Set the authentication token.

        Args:
            value: The bearer token to set, or None to clear authentication
        """
        self._auth_token = value
        if value:
            self.session.headers.update({"Authorization": f"Bearer {value}"})
        else:
            self.session.headers.pop("Authorization", None)

    def close(self) -> None:
        """Close the session and clear authentication state."""
        self.session.close()
        self._auth_token = None
        self.account_id = None
        self._provisioned = False

    def __enter__(self) -> "DysonClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
