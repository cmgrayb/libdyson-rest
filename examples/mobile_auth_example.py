"""
Example usage of mobile authentication with Dyson REST API.

This demonstrates the mobile authentication flow available on the China (CN) region
server. Mobile authentication uses SMS OTP codes instead of email OTP codes.

IMPORTANT: Mobile authentication is only available on the CN region server.
Mobile numbers must include the country code prefix (e.g., '+8613800000000').
"""

import logging
import os

from libdyson_rest import DysonClient
from libdyson_rest.exceptions import DysonAPIError, DysonAuthError, DysonConnectionError

# Configure logging to see authentication flow
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def main() -> None:
    """Demonstrate mobile authentication flow."""
    # Configuration - Get from environment variables for security
    mobile = os.getenv("DYSON_MOBILE")  # e.g., '+8613800000000'
    password = os.getenv("DYSON_PASSWORD")
    country = "CN"  # Mobile auth only works on CN server
    culture = "zh-CN"

    if not mobile or not password:
        logger.error("Please set DYSON_MOBILE and DYSON_PASSWORD environment variables")
        logger.info(
            "Example: DYSON_MOBILE='+8613800000000' DYSON_PASSWORD='your_password'"
        )
        return

    logger.info("=== Dyson Mobile Authentication Example ===")
    logger.info(f"Mobile: {mobile[:6]}****")  # Mask mobile number
    logger.info(f"Country: {country}")
    logger.info(f"Culture: {culture}")
    logger.info("")

    try:
        # Step 1: Initialize the client
        # Note: We still pass mobile in the email parameter for now, or use mobile
        # parameter in the specific methods
        logger.info("Step 1: Initializing Dyson client...")
        client = DysonClient(
            email=mobile,  # Can use email parameter for mobile
            password=password,
            country=country,
            culture=culture,
            debug=True,
        )
        logger.info("✓ Client initialized")
        logger.info("")

        # Step 2: Call provision endpoint (required before authentication)
        logger.info("Step 2: Calling provision endpoint...")
        client.provision()
        logger.info("✓ Provision successful")
        logger.info("")

        # Step 3: Check user status with mobile number
        logger.info("Step 3: Checking user status with mobile number...")
        user_status = client.get_user_status_mobile(mobile)
        logger.info(f"✓ User status retrieved: {user_status}")
        logger.info(f"  - Authentication method: {user_status.authentication_method}")
        logger.info(f"  - Account exists: {user_status.account_exists}")
        logger.info("")

        # Step 4: Begin login process (sends SMS OTP)
        logger.info("Step 4: Beginning login process (SMS OTP will be sent)...")
        challenge = client.begin_login_mobile(mobile)
        logger.info(f"✓ Login challenge created: {challenge.challenge_id}")
        logger.info(
            f"  - Challenge ID: "
            f"{challenge.challenge_id[:8]}...{challenge.challenge_id[-8:]}"
        )
        logger.info("")

        # Step 5: Wait for user to receive and enter OTP code
        logger.info("Step 5: Waiting for OTP code from SMS...")
        otp_code = input("Enter the OTP code received via SMS: ").strip()

        if not otp_code:
            logger.error("No OTP code provided")
            return

        logger.info("")

        # Step 6: Complete login with OTP code
        logger.info("Step 6: Completing login with OTP code...")
        login_info = client.complete_login_mobile(
            challenge_id=challenge.challenge_id,
            otp_code=otp_code,
            mobile=mobile,
        )
        logger.info("✓ Login successful!")
        logger.info(f"  - Account ID: {login_info.account}")
        logger.info(f"  - Token: {login_info.token[:20]}...")
        logger.info("")

        # Step 7: Get user's devices (requires authentication)
        logger.info("Step 7: Retrieving devices...")
        devices = client.get_devices()
        logger.info(f"✓ Found {len(devices)} device(s):")

        for i, device in enumerate(devices, 1):
            logger.info(f"  Device {i}:")
            logger.info(f"    - Name: {device.name}")
            logger.info(f"    - Serial: {device.serial}")
            logger.info(f"    - Product Type: {device.product_type}")
            logger.info(f"    - Version: {device.version}")
            logger.info("")

        # Step 8: Get IoT credentials for first device (if any)
        if devices:
            device = devices[0]
            logger.info(f"Step 8: Getting IoT credentials for device: {device.name}...")
            iot_data = client.get_iot_data(device.serial)
            logger.info("✓ IoT credentials retrieved:")
            logger.info(f"  - Connection ID: {iot_data.connection_id}")
            logger.info(f"  - MQTT Host: {iot_data.mqtt_host}")
            logger.info(f"  - MQTT Port: {iot_data.mqtt_port}")
            logger.info("")

        logger.info("=== Mobile Authentication Example Completed Successfully ===")

    except DysonAuthError as e:
        logger.error(f"Authentication error: {e}")
        logger.info("")
        logger.info("Common issues:")
        logger.info("  - Incorrect mobile number or password")
        logger.info("  - Invalid OTP code")
        logger.info("  - Mobile number not registered on CN server")
        logger.info(
            "  - Mobile number format must include country code "
            "(e.g., '+8613800000000')"
        )

    except DysonConnectionError as e:
        logger.error(f"Connection error: {e}")
        logger.info("")
        logger.info("Common issues:")
        logger.info("  - Network connectivity problems")
        logger.info("  - Dyson API server unavailable")
        logger.info("  - Firewall or proxy blocking connections")

    except DysonAPIError as e:
        logger.error(f"API error: {e}")
        logger.info("")
        logger.info("Common issues:")
        logger.info("  - Invalid API response format")
        logger.info("  - API endpoint changed")
        logger.info("  - Server-side error")

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.exception("Full traceback:")


if __name__ == "__main__":
    main()
