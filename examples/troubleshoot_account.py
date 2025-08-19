#!/usr/bin/env python3
"""
Dyson Account Troubleshooting Script

This script performs comprehensive testing of a Dyson account connection
and outputs all available API information for troubleshooting purposes.
Combines authentication testing with detailed device and MQTT analysis.
"""

import json
import logging
from getpass import getpass
from typing import Any, Dict, Optional, Tuple

from libdyson_rest import (
    DysonAPIError,
    DysonAuthError,
    DysonClient,
    DysonConnectionError,
)

# Configure detailed logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def get_user_credentials() -> Tuple[Optional[str], Optional[str], str, str]:
    """Get user credentials for testing."""
    print("🔧 Dyson Account Troubleshooting Tool")
    print("=" * 50)
    print("This tool will authenticate with your Dyson account and output")
    print("comprehensive API information for troubleshooting connection issues.\n")

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


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"📊 {title}")
    print("=" * 60)


def print_subsection(title: str) -> None:
    """Print a formatted subsection header."""
    print(f"\n🔍 {title}")
    print("-" * 40)


def output_authentication_info(client: DysonClient, login_info: Any, user_status: Any) -> Dict[str, Any]:
    """Output comprehensive authentication information."""
    print_section("AUTHENTICATION INFORMATION")

    auth_info = {
        "account_id": str(login_info.account),
        "email": client.email,
        "country": client.country,
        "culture": client.culture,
        "account_status": user_status.account_status.value,
        "authentication_method": user_status.authentication_method.value,
        "token_type": login_info.token_type.value,
        "bearer_token": str(login_info.token),
        "bearer_token_preview": f"{str(login_info.token)[:20]}...",
    }

    print(f"   Account ID: {auth_info['account_id']}")
    print(f"   Email: {auth_info['email']}")
    print(f"   Country: {auth_info['country']}")
    print(f"   Locale: {auth_info['culture']}")
    print(f"   Account Status: {auth_info['account_status']}")
    print(f"   Auth Method: {auth_info['authentication_method']}")
    print(f"   Token Type: {auth_info['token_type']}")
    print(f"   Bearer Token: {auth_info['bearer_token_preview']}")

    return auth_info


def analyze_device_details(device: Any, client: DysonClient) -> Dict[str, Any]:
    """Analyze and output comprehensive device information."""
    device_info = _initialize_device_info(device)

    print_subsection(f"Device: {device.name}")
    _print_basic_device_info(device)

    # Analyze connected configuration
    if device.connected_configuration:
        config_info = _analyze_device_configuration(device, client)
        device_info["connected_configuration"] = config_info
    else:
        print("\n   ⚠️  No connected configuration available")

    # Analyze IoT credentials
    if device.connection_category.value != "nonConnected":
        iot_info = _analyze_iot_credentials(device, client)
        device_info["iot_credentials"] = iot_info

        if iot_info and not isinstance(iot_info, str) and device.connected_configuration:
            _analyze_mqtt_topics(device)
            _analyze_cloud_mqtt_config(iot_info)

    # Local MQTT Configuration
    if device.connected_configuration and device_info["connected_configuration"]:
        _analyze_local_mqtt_config(device, device_info)

    return device_info


def _initialize_device_info(device: Any) -> Dict[str, Any]:
    """Initialize device information structure."""
    return {
        "basic_info": {
            "name": device.name,
            "serial_number": device.serial_number,
            "type": device.type,
            "model": device.model,
            "category": device.category.value,
            "connection_category": device.connection_category.value,
            "variant": device.variant,
        },
        "connected_configuration": None,
        "iot_credentials": None,
        "mqtt_analysis": {
            "local_mqtt": None,
            "cloud_mqtt": None,
            "topics": None,
        },
    }


def _print_basic_device_info(device: Any) -> None:
    """Print basic device information."""
    print("   📱 Basic Information:")
    print(f"      Name: {device.name}")
    print(f"      Serial Number: {device.serial_number}")
    print(f"      Type: {device.type}")
    print(f"      Model: {device.model}")
    print(f"      Category: {device.category.value}")
    print(f"      Connection: {device.connection_category.value}")
    if device.variant:
        print(f"      Variant: {device.variant}")


def _analyze_device_configuration(device: Any, client: DysonClient) -> Dict[str, Any]:
    """Analyze device connected configuration."""
    print("\n   🌐 Connected Configuration:")
    config = device.connected_configuration

    capabilities = []
    if config.firmware.capabilities:
        capabilities = [cap.value for cap in config.firmware.capabilities]

    config_info = {
        "mqtt": {
            "local_broker_credentials_encrypted": config.mqtt.local_broker_credentials,
            "mqtt_root_topic_level": config.mqtt.mqtt_root_topic_level,
            "remote_broker_type": config.mqtt.remote_broker_type.value,
            "local_broker_credentials_decrypted": None,
        },
        "firmware": {
            "version": config.firmware.version,
            "auto_update_enabled": config.firmware.auto_update_enabled,
            "new_version_available": config.firmware.new_version_available,
            "capabilities": capabilities,
        },
    }

    print(f"      MQTT Root Topic: {config_info['mqtt']['mqtt_root_topic_level']}")
    print(f"      Remote Broker Type: {config_info['mqtt']['remote_broker_type']}")
    encrypted_creds = config_info["mqtt"]["local_broker_credentials_encrypted"]
    print(f"      Encrypted Local Credentials: {encrypted_creds[:50]}...")

    # Try to decrypt local MQTT password
    try:
        decrypted_password = client.decrypt_local_credentials(
            config.mqtt.local_broker_credentials, device.serial_number
        )
        config_info["mqtt"]["local_broker_credentials_decrypted"] = decrypted_password
        print(f"      ✅ Decrypted Local Password: {decrypted_password}")
    except Exception as e:
        error_msg = f"Failed to decrypt: {e}"
        config_info["mqtt"]["local_broker_credentials_decrypted"] = f"ERROR: {error_msg}"
        print(f"      ❌ Local Password Decryption: {error_msg}")

    print("\n      💾 Firmware Information:")
    print(f"         Version: {config_info['firmware']['version']}")
    print(f"         Auto Update: {config_info['firmware']['auto_update_enabled']}")
    print(f"         New Version Available: {config_info['firmware']['new_version_available']}")
    if config_info["firmware"]["capabilities"]:
        capabilities_str = ", ".join(config_info["firmware"]["capabilities"])
        print(f"         Capabilities: {capabilities_str}")

    return config_info


def _analyze_iot_credentials(device: Any, client: DysonClient) -> Any:
    """Analyze IoT credentials for the device."""
    try:
        print("\n   ☁️  AWS IoT Credentials:")
        iot_data = client.get_iot_credentials(device.serial_number)

        iot_info = {
            "endpoint": iot_data.endpoint,
            "credentials": {
                "client_id": str(iot_data.iot_credentials.client_id),
                "custom_authorizer_name": iot_data.iot_credentials.custom_authorizer_name,
                "token_key": iot_data.iot_credentials.token_key,
                "token_value": str(iot_data.iot_credentials.token_value),
                "token_signature": iot_data.iot_credentials.token_signature,
            },
        }

        print(f"      AWS IoT Endpoint: {iot_info['endpoint']}")
        print(f"      Client ID: {iot_info['credentials']['client_id']}")
        print(f"      Custom Authorizer: {iot_info['credentials']['custom_authorizer_name']}")
        print(f"      Token Key: {iot_info['credentials']['token_key']}")
        print(f"      Token Value: {iot_info['credentials']['token_value']}")
        signature_preview = iot_info["credentials"]["token_signature"][:50]
        print(f"      Token Signature: {signature_preview}...")

        return iot_info

    except Exception as e:
        error_msg = f"Failed to get IoT credentials: {e}"
        print(f"      ❌ IoT Credentials Error: {error_msg}")
        return f"ERROR: {error_msg}"


def _analyze_mqtt_topics(device: Any) -> None:
    """Analyze MQTT topics for the device."""
    print("\n   📨 MQTT Topics:")

    # Use the MQTT root topic from the device configuration
    # Note: This should always be available for connected devices
    root_topic = device.connected_configuration.mqtt.mqtt_root_topic_level
    base_topic = f"{root_topic}/{device.serial_number}"

    status_topics = [
        f"{base_topic}/status/current",
        f"{base_topic}/status/faults",
        f"{base_topic}/status/software",
        f"{base_topic}/status/summary",
        f"{base_topic}/status/sensor",
        f"{base_topic}/status/environmental",
    ]

    print(f"      Base Topic: {base_topic}")
    print("      Status Topics:")
    for topic in status_topics:
        print(f"         - {topic}")
    print("      Command Topics:")
    print(f"         - {base_topic}/command")


def _analyze_cloud_mqtt_config(iot_info: Dict[str, Any]) -> None:
    """Analyze cloud MQTT connection configuration."""
    print("\n   🌐 Cloud MQTT Connection Parameters:")
    print(f"      Host: {iot_info['endpoint']}")
    print("      Port: 443")
    print("      Protocol: MQTT over WebSockets with TLS")
    print(f"      Client ID: {iot_info['credentials']['client_id']}")
    print("      Auth Type: AWS IoT Custom Authorizer")
    print(f"      Authorizer: {iot_info['credentials']['custom_authorizer_name']}")


def _analyze_local_mqtt_config(device: Any, device_info: Dict[str, Any]) -> None:
    """Analyze local MQTT connection configuration."""
    print("\n   � Local MQTT Connection Parameters:")
    print(f"      Host: {device.name}.local (or device IP)")
    print("      MQTT Port: 1883")
    print("      MQTT+TLS Port: 8883")
    print(f"      Username: {device.serial_number}")

    password = device_info["connected_configuration"]["mqtt"]["local_broker_credentials_decrypted"]
    if isinstance(password, str) and not password.startswith("ERROR:"):
        print(f"      Password: {password}")
    else:
        print(f"      Password: {password}")

    print("      Protocol: MQTT (plain or TLS)")
    root_topic = device_info["connected_configuration"]["mqtt"]["mqtt_root_topic_level"]
    print(f"      Root Topic: {root_topic}")

    # Add to device_info
    local_mqtt_info = {
        "host": f"{device.name}.local",
        "host_alternatives": [f"{device.name}.local", "Device IP address on local network"],
        "ports": {"mqtt": 1883, "mqtt_tls": 8883},
        "username": device.serial_number,
        "password": password,
        "protocol": "MQTT (plain or TLS)",
        "root_topic": root_topic,
    }
    device_info["mqtt_analysis"]["local_mqtt"] = local_mqtt_info


def run_troubleshooting() -> None:
    """Run the complete troubleshooting analysis."""
    # Get credentials
    email, password, country, culture = get_user_credentials()
    if not email or not password:
        return

    print("\n🚀 Starting comprehensive account analysis...\n")

    troubleshooting_data = _initialize_troubleshooting_data()

    try:
        # Initialize client and authenticate
        with DysonClient(email=email, password=password, country=country, culture=culture) as client:

            # Authentication steps
            print("📡 Step 1: Provisioning API access...")
            version = client.provision()
            print(f"✅ API provisioned successfully! Version: {version}")

            user_status = _verify_account_status(client)
            if not user_status:
                return

            login_info = _complete_authentication(client, email)
            if not login_info:
                return

            troubleshooting_data["summary"]["authentication_successful"] = True

            # Output authentication information
            auth_info = output_authentication_info(client, login_info, user_status)
            troubleshooting_data["authentication"] = auth_info

            # Device analysis
            _analyze_all_devices(client, troubleshooting_data)

            # Output results
            _output_final_summary(troubleshooting_data)

    except DysonAuthError as e:
        print(f"❌ Authentication error: {e}")
    except DysonConnectionError as e:
        print(f"❌ Connection error: {e}")
    except DysonAPIError as e:
        print(f"❌ API error: {e}")
    except KeyboardInterrupt:
        print("\n❌ Analysis cancelled by user")
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()


def _initialize_troubleshooting_data() -> Dict[str, Any]:
    """Initialize the troubleshooting data structure."""
    return {
        "timestamp": None,
        "authentication": None,
        "devices": [],
        "summary": {
            "total_devices": 0,
            "connected_devices": 0,
            "devices_with_local_config": 0,
            "devices_with_iot_credentials": 0,
            "authentication_successful": False,
        },
    }


def _verify_account_status(client: DysonClient) -> Any:
    """Verify account status and return user status if active."""
    print("\n👤 Step 2: Checking account status...")
    user_status = client.get_user_status()
    print(f"✅ Account status: {user_status.account_status.value}")

    if user_status.account_status.value != "ACTIVE":
        print(f"❌ Account is not active: {user_status.account_status.value}")
        return None

    return user_status


def _complete_authentication(client: DysonClient, email: str) -> Any:
    """Complete the authentication process with OTP."""
    print("\n🔐 Step 3: Beginning login process...")
    challenge = client.begin_login()
    print("✅ Login challenge received!")

    print(f"\n📧 Step 4: OTP sent to {email}")
    otp_code = input("Enter the OTP code from your email: ").strip()
    if not otp_code:
        print("❌ OTP code is required")
        return None

    login_info = client.complete_login(str(challenge.challenge_id), otp_code)
    print("✅ Authentication completed successfully!")
    return login_info


def _analyze_all_devices(client: DysonClient, troubleshooting_data: Dict[str, Any]) -> None:
    """Analyze all devices on the account."""
    print_section("DEVICE ANALYSIS")
    devices = client.get_devices()
    print(f"Found {len(devices)} device(s) on account\n")

    troubleshooting_data["summary"]["total_devices"] = len(devices)

    for i, device in enumerate(devices, 1):
        print(f"\n{'─' * 60}")
        print(f"Device {i} of {len(devices)}")
        print("─" * 60)

        device_info = analyze_device_details(device, client)
        troubleshooting_data["devices"].append(device_info)

        # Update summary counters
        _update_device_summary(device, device_info, troubleshooting_data["summary"])


def _update_device_summary(device: Any, device_info: Dict[str, Any], summary: Dict[str, Any]) -> None:
    """Update device summary counters."""
    if device.connection_category.value != "nonConnected":
        summary["connected_devices"] += 1
    if device.connected_configuration:
        summary["devices_with_local_config"] += 1
    if device_info["iot_credentials"] and not isinstance(device_info["iot_credentials"], str):
        summary["devices_with_iot_credentials"] += 1


def _output_final_summary(troubleshooting_data: Dict[str, Any]) -> None:
    """Output the final troubleshooting summary and export data."""
    print_section("TROUBLESHOOTING SUMMARY")
    summary = troubleshooting_data["summary"]
    print(f"   Authentication: {'✅ SUCCESS' if summary['authentication_successful'] else '❌ FAILED'}")
    print(f"   Total Devices: {summary['total_devices']}")
    print(f"   Connected Devices: {summary['connected_devices']}")
    print(f"   Devices with Local Config: {summary['devices_with_local_config']}")
    print(f"   Devices with IoT Credentials: {summary['devices_with_iot_credentials']}")

    # Export detailed data
    import datetime

    troubleshooting_data["timestamp"] = datetime.datetime.now().isoformat()

    filename = f"dyson_troubleshooting_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w") as f:
        json.dump(troubleshooting_data, f, indent=2, default=str)

    print(f"\n💾 Detailed troubleshooting data exported to: {filename}")
    print("\n🎉 Troubleshooting analysis complete!")


def main() -> None:
    """Main entry point."""
    try:
        run_troubleshooting()
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")


if __name__ == "__main__":
    main()
