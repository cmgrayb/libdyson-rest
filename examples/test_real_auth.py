#!/usr/bin/env python3
"""
Test script for real Dyson API authentication.

This script tests the complete authentication flow with a real Dyson account,
including all steps from provisioning to device enumeration.
"""

import logging
import sys
from getpass import getpass
from typing import Optional, Tuple

from libdyson_rest import (
    DysonAPIError,
    DysonAuthError,
    DysonClient,
    DysonConnectionError,
)

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def get_user_credentials() -> Tuple[Optional[str], Optional[str], str, str]:
    """Get user credentials for testing."""
    email = input("Enter your Dyson account email: ").strip()
    if not email:
        print("❌ Email is required")
        return None, None, "US", "en-US"

    password = getpass("Enter your Dyson account password: ").strip()
    if not password:
        print("❌ Password is required")
        return None, None, "US", "en-US"

    # Optional: country and culture
    print()
    country = input("Enter your country code (default: US): ").strip().upper() or "US"
    culture = input("Enter your locale (default: en-US): ").strip() or "en-US"

    return email, password, country, culture


def test_devices(client: DysonClient) -> None:
    """Test device enumeration and IoT credentials."""
    print("\n📱 Testing device enumeration...")
    devices = client.get_devices()
    print(f"   ✅ Found {len(devices)} device(s)")

    for device in devices:
        print(f"\n   📱 Device: {device.name}")
        print(f"      Serial: {device.serial_number}")
        print(f"      Type: {device.type}")
        print(f"      Connection: {device.connection_category.value}")

        # Test IoT credentials for connected devices
        if device.connection_category.value != "nonConnected":
            try:
                print("     🌐 Getting IoT credentials...")
                iot_data = client.get_iot_credentials(device.serial_number)
                print(f"     ✅ IoT Endpoint: {iot_data.endpoint}")
                print(f"     ✅ Client ID: {iot_data.iot_credentials.client_id}")
            except Exception as e:
                print(f"     ⚠️  IoT credentials failed: {e}")
        else:
            print("     ℹ️  Device not connected - no IoT credentials available")

    if not devices:
        print("   ℹ️  No devices found on this account")


def run_auth_test() -> None:  # noqa: C901
    """Run the authentication test - complex for demonstration purposes."""
    print("🔧 libdyson-rest Authentication Test")
    print("=" * 50)
    print()
    print("This will test the complete authentication flow with a real Dyson account.")
    print("You'll need:")
    print("  ✅ A valid Dyson account email")
    print("  ✅ Your Dyson account password")
    print("  ✅ Access to your email for the OTP code")
    print()

    # Get credentials
    email, password, country, culture = get_user_credentials()
    if not email or not password:
        return

    print()
    print("🚀 Starting authentication test...")
    print()

    try:
        # Initialize client
        client = DysonClient(email=email, password=password, country=country, culture=culture)
        print(f"✅ Client initialized for {email} in {country} ({culture})")

        # Step 1: Provision
        print("\n📡 Step 1: Provisioning API access...")
        version = client.provision()
        print("✅ API provisioned successfully!")
        print(f"   API Version: {version}")

        # Step 2: Get user status
        print("\n👤 Step 2: Checking account status...")
        user_status = client.get_user_status()
        print("✅ Account status retrieved!")
        print(f"   Status: {user_status.account_status.value}")
        print(f"   Auth Method: {user_status.authentication_method.value}")

        if user_status.account_status.value != "ACTIVE":
            print(f"⚠️  Account is not active: {user_status.account_status.value}")
            return

        # Step 3: Begin login
        print("\n🔐 Step 3: Beginning login process...")
        challenge = client.begin_login()
        print("✅ Login challenge received!")
        print(f"   Challenge ID: {challenge.challenge_id}")

        # Step 4: Complete login
        print(f"\n📧 Step 4: OTP sent to {email}")
        print("   Check your email for the verification code...")

        otp_code = input("Enter the OTP code from your email: ").strip()
        if not otp_code:
            print("❌ OTP code is required")
            return

        login_info = client.complete_login(str(challenge.challenge_id), otp_code)
        print("✅ Authentication completed successfully!")
        print(f"   Account ID: {login_info.account}")
        print(f"   Token Type: {login_info.token_type.value}")
        print(f"   Token: {login_info.token[:20]}...")

        # Test device functionality
        test_devices(client)

        print("\n🎉 All tests completed successfully!")
        print(f"   Bearer Token: {client.get_auth_token()}")
        print("   You can now use this token for future API calls")

        # Always close the client
        client.close()
        print("\n🔒 Client session closed")

    except ValueError as e:
        print(f"❌ Invalid configuration: {e}")
    except DysonAuthError as e:
        print(f"❌ Authentication error: {e}")
    except DysonConnectionError as e:
        print(f"❌ Connection error: {e}")
    except DysonAPIError as e:
        print(f"❌ API error: {e}")
    except KeyboardInterrupt:
        print("\n❌ Test cancelled by user")
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")


def main() -> None:
    """Main entry point."""
    try:
        run_auth_test()
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
