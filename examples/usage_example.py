"""
Example usage of libdyson-rest library.

This example demonstrates how to use the library to interact with Dyson devices.
Note: This is for demonstration purposes only and requires proper API credentials.

The Dyson API uses a two-step authentication process:
1. Begin login to get a challenge ID
2. Complete login with OTP code (usually sent via email)
"""

import logging
import os

from libdyson_rest import DysonAuthError, DysonClient, DysonConnectionError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def basic_example() -> None:
    """Basic synchronous usage example with two-step authentication."""
    # Initialize client with credentials
    client = DysonClient(
        email=os.getenv("DYSON_EMAIL", "your_email@example.com"),
        password=os.getenv("DYSON_PASSWORD", "your_password"),
        country="US",  # 2-letter ISO country code
        culture="en-US",  # Language/locale code
        timeout=30,
    )

    try:
        # Step 1: Authenticate (this will start the login process and require OTP)
        logger.info("Starting authentication process...")
        success = client.authenticate()  # This will prompt for OTP code via logs

        if not success:
            logger.error("Authentication failed")
            return

        # If OTP is required (which it will be), complete the authentication manually
        # In a real application, you would prompt the user for the OTP code
        otp_code = input("Enter OTP code from your email: ")

        # Begin the login process to get a challenge
        challenge = client.begin_login()
        logger.info(f"Challenge ID received: {challenge.challenge_id}")

        # Complete authentication with OTP code
        login_info = client.complete_login(str(challenge.challenge_id), otp_code)
        logger.info(f"Authentication successful! Account: {login_info.account}")

        # Get list of devices
        logger.info("Retrieving device list...")
        devices = client.get_devices()

        logger.info(f"Found {len(devices)} devices:")
        for device in devices:
            logger.info(f"  - {device.name} ({device.serial_number})")
            logger.info(f"    Type: {device.type}, Model: {device.model}")
            logger.info(f"    Category: {device.category.value}")
            logger.info(f"    Connection: {device.connection_category.value}")

            # Get IoT credentials for this device (if connected)
            if device.connection_category.value != "nonConnected":
                try:
                    iot_data = client.get_iot_credentials(device.serial_number)
                    logger.info(f"    IoT Endpoint: {iot_data.endpoint}")
                except Exception as e:
                    logger.warning(f"    Could not get IoT credentials: {e}")

    except DysonAuthError as e:
        logger.error(f"Authentication error: {e}")
    except DysonConnectionError as e:
        logger.error(f"Connection error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        # Always close the client
        client.close()


def context_manager_example() -> None:
    """Example using context manager for automatic cleanup."""
    email = os.getenv("DYSON_EMAIL")
    password = os.getenv("DYSON_PASSWORD")

    if not email or not password:
        logger.warning("DYSON_EMAIL and DYSON_PASSWORD environment variables not set")
        logger.info("Using demo mode with mock data")
        return

    try:
        with DysonClient(email=email, password=password) as client:
            # Client is automatically closed when exiting the context

            # Provision API access (this is required first)
            version = client.provision()
            logger.info(f"API provisioned, version: {version}")

            # Check user status
            user_status = client.get_user_status()
            logger.info(f"Account status: {user_status.account_status.value}")
            logger.info(f"Auth method: {user_status.authentication_method.value}")

            # Begin login process
            challenge = client.begin_login()
            logger.info(f"Login challenge ID: {challenge.challenge_id}")

            # In a real application, you would get the OTP from user input
            logger.info("OTP code would be required to complete authentication")

    except Exception as e:
        logger.error(f"Error in context manager example: {e}")


def step_by_step_auth_example() -> None:
    """Demonstrates the complete step-by-step authentication process."""
    client = DysonClient(
        email=os.getenv("DYSON_EMAIL", "demo@example.com"),
        password=os.getenv("DYSON_PASSWORD", "demo_password"),
        country=os.getenv("DYSON_COUNTRY", "US"),
        culture=os.getenv("DYSON_CULTURE", "en-US"),
        timeout=int(os.getenv("DYSON_TIMEOUT", "30")),
    )

    try:
        logger.info("=== Step-by-Step Authentication Demo ===")

        # Step 1: Provision API access (required)
        logger.info("Step 1: Provisioning API access...")
        version = client.provision()
        logger.info(f"✓ API provisioned successfully, version: {version}")

        # Step 2: Check user account status
        logger.info("\\nStep 2: Checking user account status...")
        user_status = client.get_user_status()
        logger.info(f"✓ Account Status: {user_status.account_status.value}")
        logger.info(f"✓ Authentication Method: {user_status.authentication_method.value}")

        # Step 3: Begin login process
        logger.info("\\nStep 3: Beginning login process...")
        challenge = client.begin_login()
        logger.info(f"✓ Challenge ID received: {challenge.challenge_id}")
        logger.info("📧 OTP code should now be sent to your email")

        # Step 4: Complete login with OTP (in real use, get from user input)
        logger.info("\\nStep 4: Complete login with OTP code")
        logger.info("In a real application, you would:")
        logger.info("1. Prompt user for OTP code from their email")
        logger.info("2. Call client.complete_login(challenge_id, otp_code)")
        logger.info("3. Receive bearer token for API calls")
        logger.info("4. Make authenticated API calls (get_devices, get_iot_credentials)")

        # For demo purposes, show what the login completion would look like
        demo_otp = "123456"  # This would come from user input
        logger.info(f"\\nDemo: client.complete_login('{challenge.challenge_id}', '{demo_otp}')")
        logger.info("This would complete authentication and return login information")

    except DysonAuthError:
        logger.error("Authentication failed. Please check your credentials.")
    except DysonConnectionError:
        logger.error("Connection failed. Please check your internet connection.")
    except Exception as e:
        logger.error(f"Unexpected error: {type(e).__name__}: {e}")
    finally:
        client.close()


def main() -> None:
    """Main function to run examples."""
    logger.info("=== libdyson-rest Example Usage ===")
    logger.info("Updated to use the official Dyson API OpenAPI specification")

    logger.info("\\n1. Basic Example (Interactive):")
    # Uncomment the line below for interactive authentication
    # basic_example()
    logger.info("(Commented out - requires user input for OTP)")

    logger.info("\\n2. Context Manager Example:")
    context_manager_example()

    logger.info("\\n3. Step-by-Step Authentication Demo:")
    step_by_step_auth_example()

    logger.info("\\n=== Examples Complete ===")
    logger.info("\\nNOTE: The Dyson API requires two-step authentication:")
    logger.info("1. Call begin_login() to get a challenge ID")
    logger.info("2. Check your email for an OTP code")
    logger.info("3. Call complete_login() with the challenge ID and OTP code")
    logger.info("4. Use the returned bearer token for subsequent API calls")


if __name__ == "__main__":
    main()
