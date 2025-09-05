#!/usr/bin/env python3
"""
Example demonstrating token-based authentication with libdyson-rest.

This shows how to:
1. Authenticate once and get a token
2. Reuse the token for subsequent operations
"""

import logging
from getpass import getpass

from libdyson_rest import DysonAuthError, DysonClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def authenticate_and_get_token(email: str, password: str) -> str:
    """
    Authenticate with Dyson API and return the bearer token.

    Args:
        email: Dyson account email
        password: Dyson account password

    Returns:
        Bearer token for future API calls
    """
    print("🔐 Step 1: Authenticating with Dyson API...")

    # Create client for authentication
    with DysonClient(email=email, password=password) as client:
        # Perform full authentication flow
        client.provision()
        user_status = client.get_user_status()
        print(f"   User status: {user_status.account_status.value}")

        # Begin login and get OTP
        challenge = client.begin_login()
        print(f"   📧 OTP sent to {email}")

        # Get OTP from user
        otp_code = input("   Enter OTP code: ").strip()
        if not otp_code:
            raise ValueError("OTP code is required")

        # Complete login
        login_info = client.complete_login(str(challenge.challenge_id), otp_code)
        print("   ✅ Authentication successful!")

        return str(login_info.token)


def use_token_for_device_operations(token: str) -> None:
    """
    Use an existing token to perform device operations.

    Args:
        token: Bearer token from previous authentication
    """
    print("\n📱 Step 2: Using token for device operations...")

    # Create client with existing token (no email/password needed)
    with DysonClient(auth_token=token) as client:
        # Provision is still required for any API operations
        client.provision()

        # Get devices using the token
        devices = client.get_devices()
        print(f"   Found {len(devices)} device(s)")

        # Process each device
        for device in devices:
            print(f"\n   📱 Device: {device.name}")
            print(f"      Serial: {device.serial_number}")
            print(f"      Model: {device.model}")
            print(f"      Type: {device.type}")

            # Get IoT credentials for this device
            try:
                iot_data = client.get_iot_credentials(device.serial_number)
                print(f"      AWS IoT Endpoint: {iot_data.endpoint}")
                print(f"      Client ID: {iot_data.iot_credentials.client_id}")

                # If device has local MQTT config, decrypt password
                if device.connected_configuration:
                    try:
                        decrypted_password = client.decrypt_local_credentials(
                            device.connected_configuration.mqtt.local_broker_credentials,
                            device.serial_number,
                        )
                        print(f"      Local MQTT Password: {decrypted_password}")
                        print(
                            f"      Root Topic: {device.connected_configuration.mqtt.mqtt_root_topic_level}"
                        )
                    except Exception as e:
                        print(f"      ⚠️  Could not decrypt local password: {e}")

            except Exception as e:
                print(f"      ❌ Error getting IoT credentials: {e}")


def main() -> None:
    print("🔍 Dyson Token-Based Authentication Example")
    print("=" * 50)
    print("This demonstrates authenticating once and reusing the token.\n")

    # Get credentials
    email = input("Enter your Dyson account email: ").strip()
    if not email:
        print("❌ Email is required")
        return

    password = getpass("Enter your Dyson account password: ").strip()
    if not password:
        print("❌ Password is required")
        return

    try:
        # Step 1: Authenticate and get token
        token = authenticate_and_get_token(email, password)

        print(f"\n🎟️  Authentication token obtained: {token[:20]}...")
        print("   This token can be saved and reused for future API calls")
        print("   (until it expires - typically 24-48 hours)")

        # Step 2: Use token for device operations (simulating a separate session)
        use_token_for_device_operations(token)

        print("\n✅ Example complete!")
        print("\n📝 Usage Summary:")
        print("   1. Authenticate once with email/password/OTP to get token")
        print("   2. Store token securely (e.g., in config file, environment variable)")
        print(
            "   3. Create new DysonClient(auth_token=token) for subsequent operations"
        )
        print("   4. No need for email/password/OTP on subsequent uses")

    except (DysonAuthError, ValueError) as e:
        print(f"❌ Authentication error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
