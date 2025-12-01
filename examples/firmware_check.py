#!/usr/bin/env python3
"""
Example: Check firmware version and pending updates for Dyson devices.

This example demonstrates how to:
1. Authenticate with the Dyson API
2. Get list of devices
3. Check current firmware information
4. Check for pending firmware releases

Usage:
    python firmware_check.py
"""

import logging

from libdyson_rest import DysonClient
from libdyson_rest.exceptions import DysonAPIError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_firmware_info(client: DysonClient, serial_number: str) -> None:
    """Check and display firmware information for a device."""
    try:
        # Get pending release information
        pending_release = client.get_pending_release(serial_number)

        print(f"\n📋 Pending Release Info for {serial_number}:")
        print(f"  Pending Version: {pending_release.version}")
        print(f"  Update Pushed: {'Yes' if pending_release.pushed else 'No'}")

        if pending_release.pushed:
            print("  ✅ Firmware update is available and has been pushed to the device")
        else:
            print("  ⏳ Firmware update is available but not yet pushed")

    except DysonAPIError as e:
        print(f"  ❌ Failed to get pending release info: {e}")


def main() -> None:
    """Main example function."""
    # NOTE: Replace with your actual credentials
    email = input("Enter your Dyson account email: ").strip()
    password = input("Enter your password: ").strip()

    client = DysonClient(email=email, password=password)

    try:
        # Authenticate
        print("🔐 Starting authentication...")
        challenge = client.begin_login()

        otp_code = input("Enter the OTP code from your email: ").strip()
        login_info = client.complete_login(str(challenge.challenge_id), otp_code)

        print(f"✅ Authentication successful! Account: {login_info.account}")

        # Get devices
        print("\n📱 Getting devices...")
        devices = client.get_devices()

        if not devices:
            print("❌ No devices found in your account")
            return

        print(f"✅ Found {len(devices)} device(s)")

        for device in devices:
            print(f"\n🔧 Device: {device.name}")
            print(f"  Serial: {device.serial_number}")
            print(f"  Model: {device.model}")
            print(f"  Type: {device.type}")
            print(f"  Category: {device.category.value}")

            # Check current firmware info
            if (
                device.connected_configuration
                and device.connected_configuration.firmware
            ):
                firmware = device.connected_configuration.firmware
                print(f"  Current Firmware: {firmware.version}")
                print(
                    f"  Auto-update: "
                    f"{'Enabled' if firmware.auto_update_enabled else 'Disabled'}"
                )
                print(
                    f"  New Version Available: "
                    f"{'Yes' if firmware.new_version_available else 'No'}"
                )

                if firmware.minimum_app_version:
                    print(f"  Min App Version: {firmware.minimum_app_version}")

                if firmware.capabilities:
                    print(
                        f"  Capabilities: "
                        f"{', '.join(cap.value for cap in firmware.capabilities)}"
                    )

            # Check pending releases
            check_firmware_info(client, device.serial_number)

    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
