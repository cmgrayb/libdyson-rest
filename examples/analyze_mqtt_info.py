#!/usr/bin/env python3
"""
MQTT Information Extractor for libdyson-rest.

This script extracts and displays all MQTT-related information available
from the Dyson API without creating actual MQTT connections.
"""

import json
import logging
from getpass import getpass
from typing import Any, Dict

from libdyson_rest import (
    DysonAPIError,
    DysonAuthError,
    DysonClient,
    DysonConnectionError,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def analyze_device_mqtt_info(device: Any, iot_data: Any, client: DysonClient) -> None:
    """Analyze and display MQTT information for a device."""
    print(f"\n📱 Device: {device.name}")
    print("=" * 50)

    # Basic device info
    print("🔧 Device Information:")
    print(f"   Serial Number: {device.serial_number}")
    print(f"   Type: {device.type}")
    print(f"   Model: {device.model}")
    print(f"   Category: {device.category.value}")
    print(f"   Connection: {device.connection_category.value}")
    if device.variant:
        print(f"   Variant: {device.variant}")

    # Connected configuration (MQTT broker info)
    decrypted_password = None
    config = None

    if device.connected_configuration:
        print("\n🌐 Connected Configuration:")
        config = device.connected_configuration

        print("   📡 MQTT Configuration:")
        encrypted_password = config.mqtt.local_broker_credentials
        print(f"      Local Broker Credentials (encrypted): {encrypted_password}")

        # Decrypt the local broker password
        try:
            decrypted_password = client.decrypt_local_credentials(encrypted_password, device.serial_number)
            print(f"      Local Broker Password (decrypted): {decrypted_password}")
        except Exception as e:
            print(f"      ⚠️  Failed to decrypt password: {e}")
            decrypted_password = None

        print(f"      MQTT Root Topic Level: {config.mqtt.mqtt_root_topic_level}")
        print(f"      Remote Broker Type: {config.mqtt.remote_broker_type.value}")

        print("   💾 Firmware Information:")
        print(f"      Version: {config.firmware.version}")
        print(f"      Auto Update Enabled: {config.firmware.auto_update_enabled}")
        print(f"      New Version Available: {config.firmware.new_version_available}")

        if config.firmware.capabilities:
            print("      Capabilities:")
            for cap in config.firmware.capabilities:
                print(f"         - {cap.value}")
    else:
        print("\n⚠️  No connected configuration available")

    # IoT Data (AWS IoT connection info)
    print("\n☁️  AWS IoT Configuration:")
    print(f"   Endpoint: {iot_data.endpoint}")
    print(f"   Client ID: {iot_data.iot_credentials.client_id}")
    print(f"   Custom Authorizer: {iot_data.iot_credentials.custom_authorizer_name}")
    print(f"   Token Key: {iot_data.iot_credentials.token_key}")
    print(f"   Token Value: {iot_data.iot_credentials.token_value}")
    print(f"   Token Signature: {iot_data.iot_credentials.token_signature}")

    # Inferred MQTT topics based on Dyson patterns
    print("\n📨 Expected MQTT Topics:")
    base_topic = f"{device.type}/{device.serial_number}"

    topics = {
        "Status Topics": [
            f"{base_topic}/status/current",
            f"{base_topic}/status/faults",
            f"{base_topic}/status/software",
            f"{base_topic}/status/summary",
        ],
        "Command Topics": [f"{base_topic}/command"],
        "Sensor Topics": [f"{base_topic}/status/sensor", f"{base_topic}/status/environmental"],
    }

    for category, topic_list in topics.items():
        print(f"   {category}:")
        for topic in topic_list:
            print(f"      - {topic}")

    # MQTT connection parameters for external client
    print("\n🔗 MQTT Connection Parameters (for external client):")

    print("   ☁️  AWS IoT (Remote Connection):")
    print(f"      Host: {iot_data.endpoint}")
    print("      Port: 443 (MQTT over WebSockets with TLS)")
    print(f"      Client ID: {iot_data.iot_credentials.client_id}")
    print("      Protocol: MQTT over WebSockets")
    print("      TLS: Required (AWS IoT)")
    print("      Authentication: Custom Authorizer")
    print(f"         Authorizer Name: {iot_data.iot_credentials.custom_authorizer_name}")
    print(f"         Token Key Header: {iot_data.iot_credentials.token_key}")
    print(f"         Token Value: {iot_data.iot_credentials.token_value}")
    print(f"         Token Signature: {iot_data.iot_credentials.token_signature}")

    # Local MQTT connection info
    if device.connected_configuration and decrypted_password and config:
        print("\n   🏠 Local MQTT Broker (Direct Device Connection):")
        print(f"      Host: {device.name}.local (or device IP address)")
        print("      Port: 1883 (MQTT) or 8883 (MQTT over TLS)")
        print(f"      Username: {device.serial_number}")
        print(f"      Password: {decrypted_password}")
        print("      Client ID: Any unique identifier")
        print("      Protocol: MQTT (plain or TLS)")
        print(f"      Root Topic: {config.mqtt.mqtt_root_topic_level}")


def main() -> None:  # noqa: C901
    print("🔍 Dyson MQTT Information Analyzer")
    print("=" * 50)
    print("This tool extracts MQTT connection information from the Dyson API")
    print("without creating actual MQTT connections.\n")

    # Get credentials (reuse from previous test if available)
    email = input("Enter your Dyson account email: ").strip()
    if not email:
        print("❌ Email is required")
        return

    password = getpass("Enter your Dyson account password: ").strip()
    if not password:
        print("❌ Password is required")
        return

    print("\n🚀 Connecting to Dyson API...")

    try:
        # Initialize and authenticate
        with DysonClient(email=email, password=password) as client:
            # Quick auth flow
            challenge = client.begin_login()
            print(f"📧 OTP sent to {email}")

            otp_code = input("Enter OTP code: ").strip()
            if not otp_code:
                print("❌ OTP required")
                return

            client.complete_login(str(challenge.challenge_id), otp_code)
            print("✅ Authentication successful!")

            # Get devices
            devices = client.get_devices()
            print(f"\n📱 Found {len(devices)} device(s)")

            # Analyze each device
            for device in devices:
                try:
                    # Get IoT credentials
                    iot_data = client.get_iot_credentials(device.serial_number)

                    # Analyze MQTT info
                    analyze_device_mqtt_info(device, iot_data, client)

                    # Export data for external use
                    mqtt_info = {
                        "device": {
                            "name": device.name,
                            "serial": device.serial_number,
                            "type": device.type,
                            "model": device.model,
                            "category": device.category.value,
                            "connection_category": device.connection_category.value,
                            "variant": device.variant,
                        },
                        "mqtt_connection": {
                            "endpoint": iot_data.endpoint,
                            "port": 443,
                            "protocol": "mqtt_over_websockets",
                            "tls_required": True,
                            "client_id": str(iot_data.iot_credentials.client_id),
                            "auth": {
                                "type": "custom_authorizer",
                                "authorizer_name": iot_data.iot_credentials.custom_authorizer_name,
                                "token_key": iot_data.iot_credentials.token_key,
                                "token_value": str(iot_data.iot_credentials.token_value),
                                "token_signature": iot_data.iot_credentials.token_signature,
                            },
                        },
                        "topics": {
                            "status": [
                                f"{device.type}/{device.serial_number}/status/current",
                                f"{device.type}/{device.serial_number}/status/faults",
                                f"{device.type}/{device.serial_number}/status/software",
                                f"{device.type}/{device.serial_number}/status/summary",
                            ],
                            "commands": [f"{device.type}/{device.serial_number}/command"],
                        },
                    }

                    # Add connected configuration if available
                    if device.connected_configuration:
                        mqtt_config: Dict[str, Any] = {
                            "local_broker_credentials_encrypted": (
                                device.connected_configuration.mqtt.local_broker_credentials
                            ),
                            "mqtt_root_topic_level": device.connected_configuration.mqtt.mqtt_root_topic_level,
                            "remote_broker_type": device.connected_configuration.mqtt.remote_broker_type.value,
                        }

                        # Try to decrypt local credentials
                        try:
                            decrypted_password = client.decrypt_local_credentials(
                                device.connected_configuration.mqtt.local_broker_credentials, device.serial_number
                            )
                            mqtt_config["local_mqtt_connection"] = {
                                "host": f"{device.name}.local",
                                "port": 1883,
                                "port_tls": 8883,
                                "username": device.serial_number,
                                "password": decrypted_password,
                                "protocol": "mqtt",
                                "tls_available": True,
                                "root_topic": device.connected_configuration.mqtt.mqtt_root_topic_level,
                            }
                        except Exception as e:
                            mqtt_config["local_mqtt_error"] = f"Failed to decrypt password: {e}"

                        mqtt_info["device_mqtt_config"] = mqtt_config

                    # Save to JSON file for external clients
                    filename = f"mqtt_info_{device.serial_number}.json"
                    with open(filename, "w") as f:
                        json.dump(mqtt_info, f, indent=2)

                    print(f"\n💾 MQTT info exported to: {filename}")

                except Exception as e:
                    print(f"❌ Error analyzing device {device.name}: {e}")

            print(f"\n✅ Analysis complete! Found MQTT information for {len(devices)} device(s)")
            print("\nThe JSON files contain all the connection parameters needed")
            print("for an external MQTT client to connect to your Dyson devices.")

    except (DysonAuthError, DysonConnectionError, DysonAPIError) as e:
        print(f"❌ API Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
