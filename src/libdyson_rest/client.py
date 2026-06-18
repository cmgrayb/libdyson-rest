"""
Main client for interacting with the Dyson REST API.

This client implements the official Dyson App API as documented in the OpenAPI
specification.
Authentication uses a two-step process with OTP codes.
"""

import base64
import json
import logging
from typing import Any, cast
from urllib.parse import urljoin

import httpx
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from .exceptions import DysonAPIError, DysonAuthError, DysonConnectionError
from .models import (
    CleaningStrategy,
    CleanRecord,
    DailyAirQualityData,
    Device,
    IoTData,
    LoginChallenge,
    LoginInformation,
    OutdoorAirQualityData,
    PendingRelease,
    PersistentMap,
    PersistentMapMeta,
    RecommendedCleanMap,
    ScheduledEventsData,
    UserStatus,
)
from .types import (
    CleanRecordDict,
    DailyEnvironmentDataDict,
    DeviceResponseDict,
    IoTDataResponseDict,
    LoginChallengeResponseDict,
    LoginInformationResponseDict,
    OutdoorEnvironmentDataDict,
    PendingReleaseResponseDict,
    PersistentMapDict,
    PersistentMapMetaDict,
    RecommendedCleanMapDict,
    ScheduledEventsDataDict,
    UserStatusResponseDict,
)
from .utils import get_api_hostname

logger = logging.getLogger(__name__)

# Default headers required by the API
# Noted from recent traces: DysonLink/205298 CFNetwork/3826.600.41 Darwin/24.6.0
# Where 205298 is the app build for Dyson Link on iOS, CFNetwork is CloudFlare's
# added header, and Darwin is the iOS version as of 18.6.2
DEFAULT_USER_AGENT = "android client"


class DysonClient:
    """
    Client for interacting with the Dyson REST API.

    This client handles the complete authentication flow, device discovery, and IoT
    credential retrieval for Dyson devices through their REST API according to the
    OpenAPI specification.

    Authentication Flow (Email - Global/CN):
    1. provision() - Required initial call
    2. get_user_status() - Check user account status
    3. begin_login() - Start authentication process
    4. complete_login() - Complete authentication with OTP code
    5. API calls with Bearer token

    Authentication Flow (Mobile - CN Region Only):
    1. provision() - Required initial call
    2. get_user_status_mobile() - Check user account status with mobile number
    3. begin_login_mobile() - Start authentication process with mobile number
    4. complete_login_mobile() - Complete authentication with OTP SMS code
    5. API calls with Bearer token

    Note: Mobile authentication requires mobile number with country code
    (e.g., '+8613800000000') and is only available on the China (CN)
    region server.
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
        debug: bool = False,
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
            debug: Enable detailed debug logging (includes HTTP requests/responses)

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
        self.debug = debug

        self.session = httpx.Client(headers={"User-Agent": user_agent})

        # Configure debug logging if enabled
        if debug:
            self._configure_debug_logging()

        # Authentication state
        self._auth_token: str | None = auth_token
        self.account_id: str | None = None
        self._provisioned = False
        self._current_challenge_id: str | None = None

        # If auth_token provided, set up session headers immediately
        if auth_token:
            self.session.headers.update({"Authorization": f"Bearer {auth_token}"})

    def _configure_debug_logging(self) -> None:
        """Configure detailed HTTP debug logging."""
        # Enable debug logging for httpx
        logging.getLogger("httpx").setLevel(logging.DEBUG)

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
            get_api_hostname(self.country),
            "/v1/provisioningservice/application/Android/version",
        )

        logger.debug(f"Provisioning API access for country {self.country} at {url}")

        try:
            response = self.session.get(url, timeout=self.timeout)

            # Enhanced debug logging when debug mode is enabled
            if self.debug:
                logger.debug(f"🌐 Country: {self.country}")
                logger.debug(f"📡 Request URL: {url}")
                logger.debug(f"⏱️  Timeout: {self.timeout}s")
                logger.debug(f"🔤 User-Agent: {self.user_agent}")
                logger.debug(f"📥 Response Status: {response.status_code}")
                logger.debug(f"📥 Response Headers: {dict(response.headers)}")

            response.raise_for_status()
        except httpx.HTTPError as e:
            if self.debug:
                logger.error(f"❌ Provisioning failed: {e}")
                logger.error(f"❌ Request URL: {url}")
                if hasattr(e, "response") and e.response is not None:
                    logger.error(f"❌ Response status: {e.response.status_code}")
                    logger.error(f"❌ Response text: {e.response.text[:500]}")
            else:
                logger.error(f"Failed to provision API access: {e}")
            raise DysonConnectionError(f"Failed to provision API access: {e}") from e

        try:
            version_data = response.json()
            if self.debug:
                logger.debug(f"📋 Response data: {version_data}")
            self._provisioned = True
            version = str(version_data) if version_data is not None else ""
            logger.debug(f"API provisioned successfully, version: {version}")
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

        url = urljoin(
            get_api_hostname(self.country), "/v3/userregistration/email/userstatus"
        )
        params = {"country": self.country}
        payload = {"email": target_email}

        try:
            response = self.session.post(
                url, params=params, json=payload, timeout=self.timeout
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
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

        url = urljoin(get_api_hostname(self.country), "/v3/userregistration/email/auth")
        params = {"country": self.country, "culture": self.culture}
        payload = {"email": target_email}

        try:
            response = self.session.post(
                url, params=params, json=payload, timeout=self.timeout
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise DysonConnectionError(f"Failed to begin login: {e}") from e

        try:
            data = response.json()
            # Type safety: cast to LoginChallengeResponseDict
            typed_data = cast(LoginChallengeResponseDict, data)
            return LoginChallenge.from_dict(typed_data)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(f"Invalid login challenge response: {e}") from e

    def complete_login(  # noqa: C901
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

        url = urljoin(
            get_api_hostname(self.country), "/v3/userregistration/email/verify"
        )
        params = {"country": self.country, "culture": self.culture}
        payload = {
            "challengeId": challenge_id,
            "email": target_email,
            "otpCode": otp_code,
            "password": target_password,
        }

        # Debug logging for troubleshooting
        logger.debug(f"complete_login - URL: {url}")
        logger.debug(f"complete_login - Params: {params}")
        logger.debug(f"complete_login - Payload keys: {list(payload.keys())}")
        logger.debug(f"complete_login - Challenge ID: {challenge_id}")
        logger.debug(f"complete_login - OTP Code: {otp_code}")

        try:
            response = self.session.post(
                url, params=params, json=payload, timeout=self.timeout
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Invalid credentials or OTP code") from e
            elif (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 400
            ):
                # Enhanced error details for 400 Bad Request
                try:
                    error_body = e.response.text
                    logger.error(f"400 Bad Request - Response body: {error_body}")
                    logger.error(f"400 Bad Request - Request URL: {e.response.url}")
                    if hasattr(e, "request") and e.request is not None:
                        logger.error(
                            f"400 Bad Request - Request headers: "
                            f"{dict(e.request.headers)}"
                        )
                except (AttributeError, ValueError, TypeError) as log_error:
                    # Only catch specific exceptions that might occur during logging
                    logger.debug(
                        f"Could not extract detailed error information: {log_error}"
                    )
                raise DysonAuthError(
                    f"Bad request to Dyson API (400): {e}. Check API parameters."
                ) from e
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
        except Exception as e:
            # Catch any other errors from model validation
            raise DysonAPIError(f"Invalid login response: {e}") from e

    def get_user_status_mobile(self, mobile: str | None = None) -> UserStatus:
        """
        Get the status of a user account using mobile number.

        Available on China region (CN) server. Mobile number must include country code.

        Args:
            mobile: Mobile number with country code (e.g., '+8613800000000').

        Returns:
            UserStatus object with account status and authentication method

        Raises:
            DysonConnectionError: If connection fails
            DysonAPIError: If API request fails
        """
        if not self._provisioned:
            self.provision()

        target_mobile = mobile
        if not target_mobile:
            raise DysonAPIError("Mobile number is required")

        url = urljoin(
            get_api_hostname(self.country), "/v3/userregistration/mobile/userstatus"
        )
        params = {"country": self.country}
        payload = {"mobile": target_mobile}

        try:
            response = self.session.post(
                url, params=params, json=payload, timeout=self.timeout
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise DysonConnectionError(f"Failed to get user status: {e}") from e

        try:
            data = response.json()
            # Type safety: cast to UserStatusResponseDict
            typed_data = cast(UserStatusResponseDict, data)
            return UserStatus.from_dict(typed_data)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(f"Invalid user status response: {e}") from e

    def begin_login_mobile(self, mobile: str | None = None) -> LoginChallenge:
        """
        Begin the login process by requesting a challenge ID using mobile number.

        Available on China region (CN) server. Mobile number must include country code.

        Args:
            mobile: Mobile number with country code (e.g., '+8613800000000').

        Returns:
            LoginChallenge object with challenge ID for completing login

        Raises:
            DysonConnectionError: If connection fails
            DysonAPIError: If API request fails
        """
        if not self._provisioned:
            self.provision()

        target_mobile = mobile
        if not target_mobile:
            raise DysonAPIError("Mobile number is required")

        url = urljoin(
            get_api_hostname(self.country), "/v3/userregistration/mobile/auth"
        )
        params = {"country": self.country, "culture": self.culture}
        payload = {"mobile": target_mobile}

        try:
            response = self.session.post(
                url, params=params, json=payload, timeout=self.timeout
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response is not None:
                if e.response.status_code == 401:
                    raise DysonAuthError(
                        "Invalid mobile number or not authorized"
                    ) from e
                elif e.response.status_code == 400:
                    # Enhanced error details for 400 Bad Request
                    try:
                        error_body = e.response.text
                        logger.error(f"400 Bad Request - Response body: {error_body}")
                        logger.error(f"400 Bad Request - Request URL: {e.response.url}")
                    except (AttributeError, ValueError, TypeError) as log_error:
                        logger.debug(
                            f"Could not extract detailed error information: {log_error}"
                        )
                    raise DysonAuthError(
                        f"Bad request to Dyson API (400): {e}. Check mobile format."
                    ) from e
            raise DysonConnectionError(f"Failed to begin login: {e}") from e
        except httpx.HTTPError as e:
            raise DysonConnectionError(f"Failed to begin login: {e}") from e

        try:
            data = response.json()
            # Type safety: cast to LoginChallengeResponseDict
            typed_data = cast(LoginChallengeResponseDict, data)
            return LoginChallenge.from_dict(typed_data)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(f"Invalid login challenge response: {e}") from e

    def complete_login_mobile(  # noqa: C901
        self,
        challenge_id: str,
        otp_code: str,
        mobile: str | None = None,
    ) -> LoginInformation:
        """
        Complete the login process with the challenge response using mobile number.

        Available on China region (CN) server. Mobile number must include country code.

        Args:
            challenge_id: Challenge ID from begin_login_mobile()
            otp_code: One-time password code received via SMS
            mobile: Mobile number with country code (e.g., '+8613800000000').

        Returns:
            LoginInformation: Contains account and token information

        Raises:
            DysonAuthError: If mobile number is missing or OTP is invalid
            DysonConnectionError: If connection fails
            DysonAPIError: If API request fails
        """
        if not self._provisioned:
            self.provision()

        target_mobile = mobile

        if not target_mobile:
            raise DysonAuthError("Mobile number is required for authentication")

        url = urljoin(
            get_api_hostname(self.country), "/v3/userregistration/mobile/verify"
        )
        params = {"country": self.country, "culture": self.culture}
        payload = {
            "challengeId": challenge_id,
            "mobile": target_mobile,
            "otpCode": otp_code,
        }

        # Debug logging for troubleshooting
        logger.debug(f"complete_login_mobile - URL: {url}")
        logger.debug(f"complete_login_mobile - Params: {params}")
        logger.debug(f"complete_login_mobile - Payload keys: {list(payload.keys())}")
        logger.debug(f"complete_login_mobile - Challenge ID: {challenge_id}")
        logger.debug(f"complete_login_mobile - OTP Code: {otp_code}")

        try:
            response = self.session.post(
                url, params=params, json=payload, timeout=self.timeout
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Invalid credentials or OTP code") from e
            elif (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 400
            ):
                # Enhanced error details for 400 Bad Request
                try:
                    error_body = e.response.text
                    logger.error(f"400 Bad Request - Response body: {error_body}")
                    logger.error(f"400 Bad Request - Request URL: {e.response.url}")
                    if hasattr(e, "request") and e.request is not None:
                        logger.error(
                            f"400 Bad Request - Request headers: "
                            f"{dict(e.request.headers)}"
                        )
                except (AttributeError, ValueError, TypeError) as log_error:
                    # Only catch specific exceptions that might occur during logging
                    logger.debug(
                        f"Could not extract detailed error information: {log_error}"
                    )
                raise DysonAuthError(
                    f"Bad request to Dyson API (400): {e}. Check API parameters."
                ) from e
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
        except Exception as e:
            # Catch any other errors from model validation
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
            otp_code: One-time password code. If None, only completes up to
                begin_login()

        Returns:
            True if authentication completed successfully, False if OTP code still
            needed

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
        self._current_challenge_id = str(challenge.challenge_id)
        logger.info(f"Login challenge received: {challenge.challenge_id}")

        # If OTP code provided, complete the login
        if otp_code:
            self.complete_login(self._current_challenge_id, otp_code)
            return True

        # OTP code required - user needs to provide it via complete_authentication()
        logger.info("OTP code required to complete authentication")
        return False

    def complete_authentication(self, otp_code: str) -> bool:
        """
        Complete authentication using the stored challenge ID from authenticate().

        This method should be called after authenticate() returns False, once you have
        received the OTP code from email.

        Args:
            otp_code: OTP code received via email

        Returns:
            True if authentication completed successfully

        Raises:
            DysonAuthError: If no pending challenge or authentication fails
            DysonConnectionError: If connection fails
            DysonAPIError: If API request fails
        """
        if not self._current_challenge_id:
            raise DysonAuthError(
                "No pending authentication challenge. Call authenticate() first."
            )

        self.complete_login(self._current_challenge_id, otp_code)
        self._current_challenge_id = None  # Clear challenge after use
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

        url = urljoin(get_api_hostname(self.country), "/v3/manifest")

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
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

        url = urljoin(get_api_hostname(self.country), "/v2/authorize/iot-credentials")
        payload = {"Serial": serial_number}

        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
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
            get_api_hostname(self.country),
            f"/v1/assets/devices/{serial_number}/pendingrelease",
        )

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
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

    def trigger_firmware_update(self, serial_number: str) -> bool:
        """
        Trigger a firmware update for a specific device.

        This method initiates a firmware update process for the device. The device
        must have a pending firmware release available for the update to succeed.

        Args:
            serial_number: Device serial number

        Returns:
            True if firmware update was successfully triggered

        Raises:
            DysonAuthError: If not authenticated
            DysonConnectionError: If connection fails
            DysonAPIError: If API request fails
        """
        if not self._auth_token:
            raise DysonAuthError("Must authenticate before triggering firmware update")

        url = urljoin(
            get_api_hostname(self.country),
            f"/v1/assets/devices/{serial_number}/pendingrelease",
        )

        # Add headers that match the API specification
        headers = {
            "cache-control": "no-cache",
            "content-length": "0",
        }

        try:
            response = self.session.post(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            elif (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 404
            ):
                raise DysonAPIError(
                    f"Device {serial_number} not found or no pending firmware "
                    f"update available"
                ) from e
            raise DysonConnectionError(f"Failed to trigger firmware update: {e}") from e

        # API returns 204 No Content on success
        if response.status_code == 204:
            logger.info(
                f"Firmware update triggered successfully for device {serial_number}"
            )
            return True
        else:
            raise DysonAPIError(f"Unexpected response status: {response.status_code}")

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
            ValueError: If encrypted_password is empty/None (device has no MQTT)
        """
        if not encrypted_password:
            raise ValueError(
                "Device has no MQTT credentials (likely LEC_ONLY or NON_CONNECTED)"
            )

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
            cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
            decryptor = cipher.decryptor()

            # Decrypt the data
            decrypted_bytes = decryptor.update(encrypted_bytes) + decryptor.finalize()

            # Remove padding (trim backspace characters)
            decrypted_text = decrypted_bytes.decode("utf-8").rstrip("\b").rstrip("\x00")

            # Debug logging for troubleshooting robot vacuum credentials
            logger.debug(
                f"Decrypted credentials for device {serial_number}: "
                f"length={len(decrypted_text)} chars"
            )
            logger.debug(f"Decrypted text: {decrypted_text}")
            logger.debug(
                f"Decrypted text (hex, first 200 bytes): {decrypted_bytes[:200].hex()}"
            )

            # Parse JSON to extract password
            # Use raw_decode to handle robot vacuum devices that have multiple JSON
            # objects or extra data after the first JSON (lecAndWifi devices)
            try:
                decoder = json.JSONDecoder()
                password_data, end_pos = decoder.raw_decode(decrypted_text)
                logger.debug(
                    f"Successfully parsed JSON, ended at position {end_pos} "
                    f"of {len(decrypted_text)} total chars"
                )
                if end_pos < len(decrypted_text):
                    remaining = decrypted_text[end_pos:]
                    logger.debug(f"Extra data after JSON: {remaining}")
                return str(password_data["apPasswordHash"])
            except json.JSONDecodeError as json_err:
                logger.error(
                    f"JSON parsing failed for device {serial_number}: {json_err}"
                )
                logger.error(f"Full decrypted text: {decrypted_text}")
                raise

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

    # ------------------------------------------------------------------
    # Robot / Vis Nav cloud endpoints
    # ------------------------------------------------------------------

    def get_clean_maps(
        self, serial_number: str, include_dust_map: bool = True
    ) -> list[CleanRecord]:
        """Get recent cleaning runs for a Vis Nav robot vacuum.

        Args:
            serial_number: Device serial number.
            include_dust_map: When True (default), requests the aggregated
                dust-density map blob for each run (``dustMap=total``).

        Returns:
            List of CleanRecord objects, newest first.

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError("Must authenticate before calling get_clean_maps")

        url = urljoin(get_api_hostname(self.country), f"/v2/{serial_number}/clean-maps")
        params: dict[str, str] = {}
        if include_dust_map:
            params["dustMap"] = "total"

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to get clean maps: {e}") from e

        try:
            data = response.json()
            if isinstance(data, dict) and "data" in data:
                data = data["data"]
            if not isinstance(data, list):
                raise DysonAPIError(
                    "Expected list in clean-maps response",
                    raw=response.text,
                )
            return [
                CleanRecord.from_dict(cast(CleanRecordDict, item))
                for item in data
                if isinstance(item, dict)
            ]
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(
                f"Invalid clean-maps response: {e}",
                raw=response.text,
            ) from e

    def get_persistent_map_metadata(
        self, serial_number: str
    ) -> list[PersistentMapMeta]:
        """Get persistent map metadata (zone names, IDs, areas) for a Vis Nav.

        Args:
            serial_number: Device serial number.

        Returns:
            List of PersistentMapMeta objects (one per stored map).

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError(
                "Must authenticate before calling get_persistent_map_metadata"
            )

        url = urljoin(
            get_api_hostname(self.country),
            f"/v2/app/{serial_number}/persistent-map-metadata",
        )

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(
                f"Failed to get persistent map metadata: {e}"
            ) from e

        try:
            data = response.json()
            if not isinstance(data, list):
                raise DysonAPIError(
                    "Expected list in persistent-map-metadata response",
                    raw=response.text,
                )
            return [
                PersistentMapMeta.from_dict(cast(PersistentMapMetaDict, item))
                for item in data
                if isinstance(item, dict)
            ]
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(
                f"Invalid persistent-map-metadata response: {e}",
                raw=response.text,
            ) from e

    def get_persistent_map(self, serial_number: str, map_id: str) -> PersistentMap:
        """Get the full persistent map record including the floor-plan PNG.

        Args:
            serial_number: Device serial number.
            map_id: Persistent map ID (from get_persistent_map_metadata).

        Returns:
            PersistentMap with presentation image, orientation, offset, and zones.

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError("Must authenticate before calling get_persistent_map")

        url = urljoin(
            get_api_hostname(self.country),
            f"/v2/app/{serial_number}/persistent-maps/{map_id}",
        )

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to get persistent map: {e}") from e

        try:
            data = response.json()
            if not isinstance(data, dict):
                raise DysonAPIError("Expected object in persistent-map response")
            return PersistentMap.from_dict(cast(PersistentMapDict, data))
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(f"Invalid persistent-map response: {e}") from e

    def get_recommended_cleans(self, serial_number: str) -> list[RecommendedCleanMap]:
        """Get Dyson's zone-clean recommendations for a Vis Nav.

        Recommendations are ranked by accumulated dust load. Each entry
        contains per-zone dust predictions broken down by particle class.

        Args:
            serial_number: Device serial number.

        Returns:
            List of RecommendedCleanMap objects (one per persistent map).

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError(
                "Must authenticate before calling get_recommended_cleans"
            )

        url = urljoin(
            get_api_hostname(self.country),
            f"/v1/app/{serial_number}/recommended-cleans",
        )

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to get recommended cleans: {e}") from e

        try:
            data = response.json()
            if not isinstance(data, list):
                raise DysonAPIError(
                    "Expected list in recommended-cleans response",
                    raw=response.text,
                )
            return [
                RecommendedCleanMap.from_dict(cast(RecommendedCleanMapDict, item))
                for item in data
                if isinstance(item, dict)
            ]
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(
                f"Invalid recommended-cleans response: {e}",
                raw=response.text,
            ) from e

    def set_zone_behaviour(
        self,
        serial_number: str,
        map_id: str,
        zone_id: str,
        strategy: CleaningStrategy | str,
    ) -> None:
        """Set the per-zone cleaning strategy for a Vis Nav zone.

        This persists the override to the Dyson cloud; the device picks it
        up on the next clean — equivalent to changing the zone's behaviour
        in the MyDyson app.

        Note: the real API path is ``/v1/app/{serial}/{mapId}/zones/{zoneId}/
        zone-behaviours`` (without a ``persistent-maps/`` segment).

        Args:
            serial_number: Device serial number.
            map_id: Persistent map ID.
            zone_id: Zone ID to update.
            strategy: One of the CleaningStrategy enum values
                (``auto``, ``quick``, ``quiet``, ``boost``).

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError("Must authenticate before calling set_zone_behaviour")

        strategy_value = (
            strategy.value if isinstance(strategy, CleaningStrategy) else str(strategy)
        )
        url = urljoin(
            get_api_hostname(self.country),
            f"/v1/app/{serial_number}/{map_id}/zones/{zone_id}/zone-behaviours",
        )

        try:
            response = self.session.put(
                url,
                json={"cleaningStrategy": strategy_value},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to set zone behaviour: {e}") from e

    # ------------------------------------------------------------------
    # EC (air purifier) cloud endpoints
    # ------------------------------------------------------------------

    def get_daily_environment_data(
        self, serial_number: str, language: str = "en"
    ) -> DailyAirQualityData:
        """Get indoor air-quality history at 15-minute resolution for today.

        Args:
            serial_number: Device serial number.
            language: Language code for localised field values (default ``en``).

        Returns:
            DailyAirQualityData with sample series and resolution metadata.

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError(
                "Must authenticate before calling get_daily_environment_data"
            )

        url = urljoin(
            get_api_hostname(self.country),
            f"/v1/messageprocessor/devices/{serial_number}/environmentdata/daily",
        )

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(
                f"Failed to get daily environment data: {e}"
            ) from e

        try:
            data = response.json()
            if not isinstance(data, dict):
                raise DysonAPIError("Expected object in environmentdata/daily response")
            return DailyAirQualityData.from_dict(cast(DailyEnvironmentDataDict, data))
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(f"Invalid environmentdata/daily response: {e}") from e

    def get_scheduled_events(
        self, serial_number: str, product_type: str | None = None
    ) -> ScheduledEventsData:
        """Get MyDyson-app scheduled automation events for a device.

        Args:
            serial_number: Device serial number.
            product_type: Device product-type code (e.g. ``438K``). Required
                by the server to return the correct schedule schema; omit if
                the product type is unknown.

        Returns:
            ScheduledEventsData containing the schedule enabled flag and events.

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError(
                "Must authenticate before calling get_scheduled_events"
            )

        url = urljoin(
            get_api_hostname(self.country),
            f"/v1/unifiedscheduler/{serial_number}/events",
        )
        params: dict[str, str] = {}
        if product_type:
            params["productType"] = product_type

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to get scheduled events: {e}") from e

        try:
            data = response.json()
            if not isinstance(data, dict):
                raise DysonAPIError("Expected object in scheduled-events response")
            return ScheduledEventsData.from_dict(cast(ScheduledEventsDataDict, data))
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(f"Invalid scheduled-events response: {e}") from e

    def get_outdoor_environment_data(
        self, serial_number: str, language: str = "en"
    ) -> OutdoorAirQualityData:
        """Get outdoor air quality and weather data for a device's location.

        Args:
            serial_number: Device serial number.
            language: Language code for localised field values (default ``en``).

        Returns:
            OutdoorAirQualityData with AQI, pollutant, weather, and pollen fields.

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError(
                "Must authenticate before calling get_outdoor_environment_data"
            )

        url = urljoin(
            get_api_hostname(self.country),
            f"/v1/environment/devices/{serial_number}/data",
        )
        params: dict[str, str] = {"language": language}

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(
                f"Failed to get outdoor environment data: {e}"
            ) from e

        try:
            data = response.json()
            if not isinstance(data, dict):
                raise DysonAPIError(
                    "Expected object in outdoor environment data response"
                )
            return OutdoorAirQualityData.from_dict(
                cast(OutdoorEnvironmentDataDict, data)
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(
                f"Invalid outdoor environment data response: {e}"
            ) from e

    # ------------------------------------------------------------------
    # Robot vacuum v2 additional endpoints
    # ------------------------------------------------------------------

    def get_clean_map_data(self, serial_number: str, clean_id: str) -> dict[str, Any]:
        """Get detailed data for a single cleaning session.

        Args:
            serial_number: Device serial number.
            clean_id: Cleaning session ID (from get_clean_maps).

        Returns:
            Raw dict with detailed clean session data.

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError("Must authenticate before calling get_clean_map_data")

        url = urljoin(
            get_api_hostname(self.country),
            f"/v2/{serial_number}/clean-maps-data/{clean_id}",
        )

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to get clean map data: {e}") from e

        try:
            data = response.json()
            if not isinstance(data, dict):
                raise DysonAPIError("Expected object in clean-map-data response")
            return data
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(f"Invalid clean-map-data response: {e}") from e

    def update_persistent_map(
        self, serial_number: str, map_id: str, name: str | None = None
    ) -> None:
        """Update an existing persistent map (rename, etc.).

        Args:
            serial_number: Device serial number.
            map_id: Persistent map ID.
            name: New name for the map.

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError(
                "Must authenticate before calling update_persistent_map"
            )

        url = urljoin(
            get_api_hostname(self.country),
            f"/v2/app/{serial_number}/persistent-maps/{map_id}",
        )
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name

        try:
            response = self.session.put(url, json=body, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to update persistent map: {e}") from e

    def delete_persistent_map(self, serial_number: str, map_id: str) -> None:
        """Delete a persistent map from the device.

        Args:
            serial_number: Device serial number.
            map_id: Persistent map ID to delete.

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError(
                "Must authenticate before calling delete_persistent_map"
            )

        url = urljoin(
            get_api_hostname(self.country),
            f"/v2/app/{serial_number}/persistent-maps/{map_id}",
        )

        try:
            response = self.session.delete(url, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to delete persistent map: {e}") from e

    def update_map_metadata(
        self,
        serial_number: str,
        map_id: str,
        name: str | None = None,
    ) -> None:
        """Update persistent map metadata (e.g. map name) for a Vis Nav.

        Args:
            serial_number: Device serial number.
            map_id: Persistent map ID.
            name: New name for the map.

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError("Must authenticate before calling update_map_metadata")

        url = urljoin(
            get_api_hostname(self.country),
            f"/v2/app/{serial_number}/persistent-map-metadata/{map_id}",
        )
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name

        try:
            response = self.session.put(url, json=body, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to update map metadata: {e}") from e

    def get_clean_estimation(
        self,
        serial_number: str,
        map_id: str,
        zone_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Request a cleaning estimation for a set of zones.

        Args:
            serial_number: Device serial number.
            map_id: Persistent map ID.
            zone_ids: List of zone IDs to estimate. If None, estimates all zones.

        Returns:
            Raw dict with estimated cleaning duration and coverage.

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError(
                "Must authenticate before calling get_clean_estimation"
            )

        url = urljoin(
            get_api_hostname(self.country),
            f"/v2/app/{serial_number}/persistent-maps/{map_id}/clean-estimation",
        )
        body: dict[str, Any] = {}
        if zone_ids is not None:
            body["zoneIds"] = zone_ids

        try:
            response = self.session.post(url, json=body, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to get clean estimation: {e}") from e

        try:
            data = response.json()
            if not isinstance(data, dict):
                raise DysonAPIError("Expected object in clean-estimation response")
            return data
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(f"Invalid clean-estimation response: {e}") from e

    def get_restrictions(self, serial_number: str, map_id: str) -> dict[str, Any]:
        """Get no-go and restricted-area definitions for a persistent map.

        Args:
            serial_number: Device serial number.
            map_id: Persistent map ID.

        Returns:
            Raw dict with restriction definitions (no-go zones, keep-out areas).

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError("Must authenticate before calling get_restrictions")

        url = urljoin(
            get_api_hostname(self.country),
            f"/v2/app/{serial_number}/restrictions-definitions/{map_id}",
        )

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to get restrictions: {e}") from e

        try:
            data = response.json()
            if not isinstance(data, dict):
                raise DysonAPIError(
                    "Expected object in restrictions-definitions response"
                )
            return data
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(
                f"Invalid restrictions-definitions response: {e}"
            ) from e

    def update_restrictions(
        self, serial_number: str, map_id: str, body: dict[str, Any]
    ) -> None:
        """Update no-go and restricted-area definitions for a persistent map.

        Args:
            serial_number: Device serial number.
            map_id: Persistent map ID.
            body: Restriction definitions payload.

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError("Must authenticate before calling update_restrictions")

        url = urljoin(
            get_api_hostname(self.country),
            f"/v2/app/{serial_number}/restrictions-definitions/{map_id}",
        )

        try:
            response = self.session.put(url, json=body, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to update restrictions: {e}") from e

    def divide_zone(
        self, serial_number: str, map_id: str, body: dict[str, Any]
    ) -> None:
        """Divide a zone into two sub-zones on a persistent map.

        Args:
            serial_number: Device serial number.
            map_id: Persistent map ID.
            body: Division specification payload (zone IDs, dividing line, etc.).

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError("Must authenticate before calling divide_zone")

        url = urljoin(
            get_api_hostname(self.country),
            f"/v2/app/{serial_number}/zones-definitions/{map_id}/divide-zone",
        )

        try:
            response = self.session.put(url, json=body, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to divide zone: {e}") from e

    def merge_zones(
        self, serial_number: str, map_id: str, body: dict[str, Any]
    ) -> None:
        """Merge two or more zones into one on a persistent map.

        Args:
            serial_number: Device serial number.
            map_id: Persistent map ID.
            body: Merge specification payload (zone IDs to merge, resulting name, etc.).

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError("Must authenticate before calling merge_zones")

        url = urljoin(
            get_api_hostname(self.country),
            f"/v2/app/{serial_number}/zones-definitions/{map_id}/merge-zones",
        )

        try:
            response = self.session.put(url, json=body, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to merge zones: {e}") from e

    def get_live_map_cleaning(self, serial_number: str) -> dict[str, Any]:
        """Get the current live map during a cleaning run.

        Returns the robot's real-time position and cleaned footprint during
        an active cleaning session.

        Args:
            serial_number: Device serial number.

        Returns:
            Raw dict with live map data including robot position and footprint.

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError(
                "Must authenticate before calling get_live_map_cleaning"
            )

        url = urljoin(
            get_api_hostname(self.country),
            f"/v1/app/{serial_number}/live-maps/cleaning",
        )

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to get live map (cleaning): {e}") from e

        try:
            data = response.json()
            if not isinstance(data, dict):
                raise DysonAPIError("Expected object in live-maps/cleaning response")
            return data
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(f"Invalid live-maps/cleaning response: {e}") from e

    def get_live_map_mapping(self, serial_number: str) -> dict[str, Any]:
        """Get the current live map during a mapping run.

        Returns the robot's real-time position and discovered floor plan
        during an active mapping session.

        Args:
            serial_number: Device serial number.

        Returns:
            Raw dict with live map data including robot position and discovered area.

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError(
                "Must authenticate before calling get_live_map_mapping"
            )

        url = urljoin(
            get_api_hostname(self.country),
            f"/v1/app/{serial_number}/live-maps/mapping",
        )

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to get live map (mapping): {e}") from e

        try:
            data = response.json()
            if not isinstance(data, dict):
                raise DysonAPIError("Expected object in live-maps/mapping response")
            return data
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(f"Invalid live-maps/mapping response: {e}") from e

    def set_scheduled_events(
        self,
        serial_number: str,
        enabled: bool,
        events: list[dict[str, Any]],
        product_type: str | None = None,
    ) -> None:
        """Update the scheduled automation events for a device.

        Args:
            serial_number: Device serial number.
            enabled: Whether the overall schedule should be active.
            events: List of event dicts matching the ScheduledEvent schema
                (keys: ``enabled``, ``days``, ``startTime``, ``settings``).
            product_type: Device product-type code (e.g. ``438K``).

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError(
                "Must authenticate before calling set_scheduled_events"
            )

        url = urljoin(
            get_api_hostname(self.country),
            f"/v1/unifiedscheduler/{serial_number}/events",
        )
        params: dict[str, str] = {}
        if product_type:
            params["productType"] = product_type

        body: dict[str, Any] = {"enabled": enabled, "events": events}

        try:
            response = self.session.put(
                url, json=body, params=params, timeout=self.timeout
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to set scheduled events: {e}") from e

    def get_schedule_binary(self, serial_number: str) -> bytes:
        """Download the device schedule as a binary blob.

        The binary schedule is intended for direct device programming via BLE.

        Args:
            serial_number: Device serial number.

        Returns:
            Raw bytes of the schedule binary.

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError("Must authenticate before calling get_schedule_binary")

        url = urljoin(
            get_api_hostname(self.country),
            f"/v1/unifiedscheduler/{serial_number}/app/schedule.bin",
        )

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to get schedule binary: {e}") from e

        return response.content

    def get_map_image(self, serial_number: str, map_id: str) -> bytes:
        """Fetch a server-rendered map image from the Dyson Map Visualizer API.

        Uses the ``/v1/mapvisualizer/devices/{serial}/map/{mapId}`` endpoint
        (discovered from ``assets/config/default/machine/robotEndpointsConfig.json``
        in the MyDyson APK).  The ``map_id`` can be either a clean session UUID
        (from ``CleanRecord.clean_id``) or a persistent map ID integer string
        (from ``CleanRecord.persistent_map_id``).

        For the RB05 (product type 804A) this is the correct path for floor-plan
        imagery — the ``/v1/app/{serial}/persistent-maps/{id}`` endpoint returns
        null data for that device.

        Args:
            serial_number: Device serial number.
            map_id: Clean session UUID (e.g. from ``CleanRecord.clean_id``) or
                persistent map ID string (e.g. ``"1780280259"``).

        Returns:
            Raw image bytes (PNG or JPEG).

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError("Must authenticate before calling get_map_image")

        url = urljoin(
            get_api_hostname(self.country),
            f"/v1/mapvisualizer/devices/{serial_number}/map/{map_id}",
        )

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to get map image: {e}") from e

        return response.content

    # ------------------------------------------------------------------
    # Device management additional endpoints
    # ------------------------------------------------------------------

    def get_timezone(self, serial_number: str) -> str | None:
        """Get the timezone configured for a device.

        Args:
            serial_number: Device serial number.

        Returns:
            IANA timezone name (e.g. ``"Europe/London"``), or None if not set.

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError("Must authenticate before calling get_timezone")

        url = urljoin(
            get_api_hostname(self.country),
            f"/v1/machine/{serial_number}/timezone",
        )

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to get timezone: {e}") from e

        try:
            data = response.json()
            if not isinstance(data, dict):
                raise DysonAPIError("Expected object in timezone response")
            return data.get("timezone") or data.get("timeZone") or data.get("tz")
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(f"Invalid timezone response: {e}") from e

    def set_timezone(self, serial_number: str, timezone: str) -> None:
        """Set the timezone for a device.

        Args:
            serial_number: Device serial number.
            timezone: IANA timezone name (e.g. ``"Europe/London"``).

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError("Must authenticate before calling set_timezone")

        url = urljoin(
            get_api_hostname(self.country),
            f"/v1/machine/{serial_number}/timezone",
        )

        try:
            response = self.session.put(
                url, json={"timezone": timezone}, timeout=self.timeout
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to set timezone: {e}") from e

    def get_ota_info(self, serial_number: str) -> dict[str, Any]:
        """Get over-the-air firmware update information for a device.

        Args:
            serial_number: Device serial number.

        Returns:
            Raw dict with OTA firmware info.

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError("Must authenticate before calling get_ota_info")

        url = urljoin(
            get_api_hostname(self.country),
            f"/v1/assets/devices/{serial_number}/ota",
        )

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to get OTA info: {e}") from e

        try:
            data = response.json()
            if not isinstance(data, dict):
                raise DysonAPIError("Expected object in OTA info response")
            return data
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(f"Invalid OTA info response: {e}") from e

    def is_banned_machine(self, serial_number: str) -> bool:
        """Check whether a device serial number is on the banned machine list.

        A banned machine cannot connect to Dyson cloud services.

        Args:
            serial_number: Device serial number.

        Returns:
            True if the device is banned, False otherwise.

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError("Must authenticate before calling is_banned_machine")

        url = urljoin(
            get_api_hostname(self.country),
            f"/v1/bannedmachine/{serial_number}",
        )

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to check banned machine: {e}") from e

        try:
            data = response.json()
            if isinstance(data, dict):
                return bool(data.get("banned", False) or data.get("isBanned", False))
            if isinstance(data, bool):
                return data
            return False
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(f"Invalid banned machine response: {e}") from e

    def get_feature_support(self) -> dict[str, Any]:
        """Get the global feature-support configuration from the Dyson API.

        Returns a server-controlled feature-flags object used by the MyDyson
        app to enable or disable app features at runtime.

        Returns:
            Raw dict with feature support flags.

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError("Must authenticate before calling get_feature_support")

        url = urljoin(get_api_hostname(self.country), "/v1/featuresupport")

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to get feature support: {e}") from e

        try:
            data = response.json()
            if not isinstance(data, dict):
                raise DysonAPIError("Expected object in feature support response")
            return data
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(f"Invalid feature support response: {e}") from e

    def get_voice_languages(self, serial_number: str) -> list[str]:
        """Get available voice-command language codes for a device.

        Args:
            serial_number: Device serial number.

        Returns:
            List of IETF language tag strings (e.g. ``["en-GB", "fr-FR"]``).

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError("Must authenticate before calling get_voice_languages")

        url = urljoin(
            get_api_hostname(self.country),
            f"/v1/package/voice/{serial_number}/languages",
        )

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to get voice languages: {e}") from e

        try:
            data = response.json()
            if isinstance(data, list):
                return [str(item) for item in data]
            if isinstance(data, dict):
                langs = data.get("languages") or data.get("Languages")
                if isinstance(langs, list):
                    return [str(item) for item in langs]
            raise DysonAPIError("Unexpected format in voice languages response")
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(f"Invalid voice languages response: {e}") from e

    # ------------------------------------------------------------------
    # EC (air purifier) additional endpoints
    # ------------------------------------------------------------------

    def get_environment_history(self, serial_number: str) -> dict[str, Any]:
        """Get the multi-day indoor air-quality history for a device.

        Unlike ``get_daily_environment_data`` (today at 15-minute resolution),
        this endpoint returns a longer historical dataset across multiple days.

        Args:
            serial_number: Device serial number.

        Returns:
            Raw dict with historical air-quality data.

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError(
                "Must authenticate before calling get_environment_history"
            )

        url = urljoin(
            get_api_hostname(self.country),
            f"/v1/messageprocessor/devices/{serial_number}/environmentdailyhistory",
        )

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to get environment history: {e}") from e

        try:
            data = response.json()
            if not isinstance(data, dict):
                raise DysonAPIError(
                    "Expected object in environmentdailyhistory response"
                )
            return data
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(f"Invalid environmentdailyhistory response: {e}") from e

    def get_energy_insights(
        self,
        serial_number: str,
        year: int | None = None,
        month: int | None = None,
    ) -> dict[str, Any]:
        """Get monthly energy consumption insights for a device.

        Args:
            serial_number: Device serial number.
            year: Year (default: current year on the server).
            month: Month, 1-12 (default: current month on the server).

        Returns:
            Raw dict with monthly energy/EC usage data.

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError("Must authenticate before calling get_energy_insights")

        url = urljoin(
            get_api_hostname(self.country),
            f"/v1/insights/ec/{serial_number}/monthly",
        )
        params: dict[str, str] = {}
        if year is not None:
            params["year"] = str(year)
        if month is not None:
            params["month"] = str(month)

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to get energy insights: {e}") from e

        try:
            data = response.json()
            if not isinstance(data, dict):
                raise DysonAPIError("Expected object in energy insights response")
            return data
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(f"Invalid energy insights response: {e}") from e

    # ------------------------------------------------------------------
    # Product support endpoints
    # ------------------------------------------------------------------

    def get_product_faults(self, serial_number: str) -> dict[str, Any]:
        """Get known product faults and remedies for a device.

        Args:
            serial_number: Device serial number.

        Returns:
            Raw dict with product fault information.

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError("Must authenticate before calling get_product_faults")

        url = urljoin(
            get_api_hostname(self.country),
            f"/v1/support/product-faults/{serial_number}",
        )

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to get product faults: {e}") from e

        try:
            data = response.json()
            if not isinstance(data, dict):
                raise DysonAPIError("Expected object in product faults response")
            return data
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(f"Invalid product faults response: {e}") from e

    def get_product_guide(self, serial_number: str) -> dict[str, Any]:
        """Get the product user guide content for a device.

        Args:
            serial_number: Device serial number.

        Returns:
            Raw dict with product guide content.

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError("Must authenticate before calling get_product_guide")

        url = urljoin(
            get_api_hostname(self.country),
            f"/v1/support/product-guide/{serial_number}",
        )

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to get product guide: {e}") from e

        try:
            data = response.json()
            if not isinstance(data, dict):
                raise DysonAPIError("Expected object in product guide response")
            return data
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(f"Invalid product guide response: {e}") from e

    def get_product_voice_commands(self, serial_number: str) -> dict[str, Any]:
        """Get voice command reference content for a device.

        Args:
            serial_number: Device serial number.

        Returns:
            Raw dict with voice command reference data.

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError(
                "Must authenticate before calling get_product_voice_commands"
            )

        url = urljoin(
            get_api_hostname(self.country),
            f"/v1/support/product-voice-commands/{serial_number}",
        )

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(
                f"Failed to get product voice commands: {e}"
            ) from e

        try:
            data = response.json()
            if not isinstance(data, dict):
                raise DysonAPIError(
                    "Expected object in product voice commands response"
                )
            return data
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(f"Invalid product voice commands response: {e}") from e

    # ------------------------------------------------------------------
    # Push notification endpoints
    # ------------------------------------------------------------------

    def register_push_token(
        self,
        application_id: str,
        token: str,
        platform: str,
        serial_numbers: list[str] | None = None,
    ) -> dict[str, Any]:
        """Register a push notification token with the Dyson API.

        Args:
            application_id: The application or notification token identifier.
            token: The platform push notification token (APNs or FCM).
            platform: The platform type (``"ios"`` or ``"android"``).
            serial_numbers: Optional list of device serial numbers to associate.

        Returns:
            Raw dict with registration confirmation.

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError("Must authenticate before calling register_push_token")

        url = urljoin(get_api_hostname(self.country), "/v1/notifier/applications")
        body: dict[str, Any] = {
            "applicationId": application_id,
            "token": token,
            "platform": platform,
        }
        if serial_numbers is not None:
            body["serialNumbers"] = serial_numbers

        try:
            response = self.session.post(url, json=body, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to register push token: {e}") from e

        try:
            data = response.json()
            if not isinstance(data, dict):
                raise DysonAPIError(
                    "Expected object in push token registration response"
                )
            return data
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(f"Invalid push token registration response: {e}") from e

    def get_notification_permissions(
        self, application_id: str, serial_number: str
    ) -> dict[str, Any]:
        """Get notification permissions for a device and application.

        Args:
            application_id: The application or notification token identifier.
            serial_number: The device serial number.

        Returns:
            Raw dict with per-device notification permission settings.

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError(
                "Must authenticate before calling get_notification_permissions"
            )

        url = urljoin(
            get_api_hostname(self.country),
            f"/v2/notifier/applications/{application_id}/permissions/{serial_number}",
        )

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(
                f"Failed to get notification permissions: {e}"
            ) from e

        try:
            data = response.json()
            if not isinstance(data, dict):
                raise DysonAPIError(
                    "Expected object in notification permissions response"
                )
            return data
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(
                f"Invalid notification permissions response: {e}"
            ) from e

    def update_notification_permissions(
        self,
        application_id: str,
        serial_number: str,
        permissions: dict[str, Any],
    ) -> None:
        """Update notification permissions for a device and application.

        Args:
            application_id: The application or notification token identifier.
            serial_number: The device serial number.
            permissions: Permission settings payload.

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError(
                "Must authenticate before calling update_notification_permissions"
            )

        url = urljoin(
            get_api_hostname(self.country),
            f"/v2/notifier/applications/{application_id}/permissions",
        )
        body: dict[str, Any] = {"serialNumber": serial_number, **permissions}

        try:
            response = self.session.put(url, json=body, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(
                f"Failed to update notification permissions: {e}"
            ) from e

    # ------------------------------------------------------------------
    # Smart home (NCP/NSP) endpoints
    # ------------------------------------------------------------------

    def get_registered_products(self) -> dict[str, Any]:
        """Get smart-home products registered with Dyson's NCP platform.

        Returns:
            Raw dict with registered smart-home product data.

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError(
                "Must authenticate before calling get_registered_products"
            )

        url = urljoin(get_api_hostname(self.country), "/v1/ncp/product/registered")

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to get registered products: {e}") from e

        try:
            data = response.json()
            if not isinstance(data, dict):
                raise DysonAPIError("Expected object in registered products response")
            return data
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise DysonAPIError(f"Invalid registered products response: {e}") from e

    def register_ncp(self, body: dict[str, Any]) -> None:
        """Register a device with Dyson's NCP smart-home platform.

        Args:
            body: Registration payload.

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError("Must authenticate before calling register_ncp")

        url = urljoin(get_api_hostname(self.country), "/v1/ncp/register")

        try:
            response = self.session.put(url, json=body, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to register NCP device: {e}") from e

    def register_nsp(self, body: dict[str, Any]) -> None:
        """Register a device with Dyson's NSP smart-home platform.

        Args:
            body: Registration payload.

        Raises:
            DysonAuthError: If not authenticated.
            DysonConnectionError: If connection fails.
            DysonAPIError: If API request fails.
        """
        if not self._auth_token:
            raise DysonAuthError("Must authenticate before calling register_nsp")

        url = urljoin(get_api_hostname(self.country), "/v1/nsp/register")

        try:
            response = self.session.put(url, json=body, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 401
            ):
                raise DysonAuthError("Authentication token expired or invalid") from e
            raise DysonConnectionError(f"Failed to register NSP device: {e}") from e
