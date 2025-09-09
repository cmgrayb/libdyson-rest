#!/usr/bin/env python3
"""
Dyson API Device Scanner

A streamlined script to authenticate with the Dyson API and scan all devices
on the account, outputting key device information for analysis.
"""

import logging
from getpass import getpass
from typing import Any, List, Optional, Tuple

from libdyson_rest import (
    DysonAPIError,
    DysonAuthError,
    DysonClient,
    DysonConnectionError,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_user_credentials() -> Tuple[Optional[str], Optional[str], str, str]:
    """Get user credentials for API authentication."""
    print("🔍 Dyson API Device Scanner")
    print("=" * 40)
    print("This tool will scan all devices on your Dyson account\n")

    email = input("Enter your Dyson account email: ").strip()
    if not email:
        print("❌ Email is required")
        return None, None, "US", "en-US"

    password = getpass("Enter your Dyson account password: ").strip()
    if not password:
        print("❌ Password is required")
        return None, None, "US", "en-US"

    print()
    country = input("Enter your country code (default: US): ").strip().upper() or "US"
    culture = input("Enter your locale (default: en-US): ").strip() or "en-US"

    return email, password, country, culture


def authenticate_client(client: DysonClient, email: str) -> bool:
    """Authenticate the client using the two-part MFA process."""
    try:
        # Step 1: Provision API access
        print("📡 Provisioning API access...")
        version = client.provision()
        print(f"✅ API provisioned successfully! Version: {version}")

        # Step 2: Check account status
        print("👤 Checking account status...")
        user_status = client.get_user_status()
        print(f"✅ Account status: {user_status.account_status.value}")

        if user_status.account_status.value != "ACTIVE":
            print(f"❌ Account is not active: {user_status.account_status.value}")
            return False

        # Step 3: Begin login process
        print("🔐 Beginning login process...")
        challenge = client.begin_login()
        print("✅ Login challenge received!")

        # Step 4: Complete authentication with OTP
        print(f"📧 OTP sent to {email}")
        otp_code = input("Enter the OTP code from your email: ").strip()
        if not otp_code:
            print("❌ OTP code is required")
            return False

        client.complete_login(str(challenge.challenge_id), otp_code)
        print("✅ Authentication completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False


def get_mqtt_root_topic(device: Any) -> Optional[str]:
    """Extract MQTT root topic from device configuration."""
    if device.connected_configuration and device.connected_configuration.mqtt:
        return str(device.connected_configuration.mqtt.mqtt_root_topic_level)
    return None


def get_device_capabilities(device: Any) -> List[str]:
    """Extract device capabilities from firmware configuration."""
    if (
        device.connected_configuration
        and device.connected_configuration.firmware
        and device.connected_configuration.firmware.capabilities
    ):
        return [
            cap.value for cap in device.connected_configuration.firmware.capabilities
        ]
    return []


def scan_devices(client: DysonClient) -> None:
    """Scan and display information for all devices on the account."""
    print("\n🔍 Scanning devices...")
    print("=" * 60)

    try:
        devices = client.get_devices()

        if not devices:
            print("📱 No devices found on this account")
            return

        print(f"📱 Found {len(devices)} device(s) on account\n")

        # Display each device in block format
        for i, device in enumerate(devices, 1):
            device_type = device.type or "N/A"
            variant = device.variant or "N/A"
            model = device.model or "N/A"
            category = device.category.value if device.category else "N/A"
            connection_category = (
                device.connection_category.value
                if device.connection_category
                else "N/A"
            )
            mqtt_root_topic = get_mqtt_root_topic(device) or "N/A"
            capabilities = get_device_capabilities(device)
            device_name = device.name if hasattr(device, "name") else f"Device {i}"

            print(f"📱 Device #{i}: {device_name}")
            print("-" * 40)
            print(f"   Device Type:      {device_type}")
            print(f"   Variant:          {variant}")
            print(f"   Model:            {model}")
            print(f"   Category:         {category}")
            print(f"   Connection:       {connection_category}")
            print(f"   MQTT Root Topic:  {mqtt_root_topic}")
            print("   Capabilities:")
            if capabilities:
                for cap in capabilities:
                    print(f"      • {cap}")
            else:
                print("      • No capabilities available (device may not be connected)")

            if i < len(devices):
                print()  # Add blank line between devices except for the last one

        print("\n" + "=" * 60)
        print(f"✅ Device scan completed! Total devices: {len(devices)}")

    except Exception as e:
        print(f"❌ Error scanning devices: {e}")


def main() -> None:
    """Main entry point for the device scanner."""
    try:
        # Get credentials
        email, password, country, culture = get_user_credentials()
        if not email or not password:
            return

        print("\n🚀 Starting device scan...\n")

        # Initialize client and authenticate
        with DysonClient(
            email=email, password=password, country=country, culture=culture
        ) as client:
            if authenticate_client(client, email):
                scan_devices(client)
            else:
                print("❌ Authentication failed - cannot scan devices")

    except DysonAuthError as e:
        print(f"❌ Authentication error: {e}")
    except DysonConnectionError as e:
        print(f"❌ Connection error: {e}")
    except DysonAPIError as e:
        print(f"❌ API error: {e}")
    except KeyboardInterrupt:
        print("\n❌ Scan cancelled by user")
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
