# Dyson Account Troubleshooting Guide

## Overview

The `troubleshoot_account.py` script is a comprehensive diagnostic tool for Dyson account connections. It authenticates with your real Dyson account and outputs all available API information for troubleshooting connection issues.

## Features

This script combines functionality from multiple example scripts to provide:

- ✅ **Complete Authentication Flow**: Tests the full OTP-based authentication process
- 🔍 **Device Discovery**: Lists all devices associated with your account  
- 🔐 **MQTT Password Decryption**: Decrypts local MQTT broker credentials
- ☁️ **IoT Credentials Analysis**: Retrieves and displays AWS IoT connection details
- 📨 **MQTT Topic Mapping**: Shows all relevant MQTT topics for each device
- 🌐 **Connection Parameters**: Provides both local and cloud MQTT configuration
- 📊 **Comprehensive Summary**: Outputs troubleshooting statistics and exports detailed JSON data

## Usage

### Basic Usage

```bash
cd examples
python troubleshoot_account.py
```

The script will prompt you for:
1. Dyson account email
2. Dyson account password  
3. Country code (default: US)
4. Locale (default: en-US)
5. OTP code (sent to your email)

### Example Output

```
🔧 Dyson Account Troubleshooting Tool
==================================================
This tool will authenticate with your Dyson account and output
comprehensive API information for troubleshooting connection issues.

Enter your Dyson account email: your-email@example.com
Enter your Dyson account password: 
Enter your country code (default: US): 
Enter your locale (default: en-US): 

🚀 Starting comprehensive account analysis...

📡 Step 1: Provisioning API access...
✅ API provisioned successfully! Version: 5.0.21061

👤 Step 2: Checking account status...
✅ Account status: ACTIVE

🔐 Step 3: Beginning login process...
✅ Login challenge received!

📧 Step 4: OTP sent to your-email@example.com
Enter the OTP code from your email: 123456
✅ Authentication completed successfully!

============================================================
📊 AUTHENTICATION INFORMATION
============================================================
   Account ID: bc8f2680-1f98-4c4d-8733-efb5003919d2
   Email: your-email@example.com
   Country: US
   Locale: en-US
   Account Status: ACTIVE
   Auth Method: EMAIL_PWD_2FA
   Token Type: Bearer
   Bearer Token: 657EE842F50B6A90DE6D...

============================================================
📊 DEVICE ANALYSIS
============================================================
Found 1 device(s) on account

🔍 Device: Theater Fan
----------------------------------------
   📱 Basic Information:
      Name: Theater Fan
      Serial Number: 9RJ-US-UAA8845A
      Type: 438
      Model: TP11
      Category: ec
      Connection: lecAndWifi

   🌐 Connected Configuration:
      MQTT Root Topic: 438M
      Remote Broker Type: wss
      Encrypted Local Credentials: zVGln87HAMt8wVbgjk...
      ✅ Decrypted Local Password: Q0T3OiiA0/eb6gynNPYzv+1ov...

   ☁️  AWS IoT Credentials:
      AWS IoT Endpoint: a1u2wvl3e2lrc4-ats.iot.eu-west-1.amazonaws.com
      Client ID: f91a40c3-44ed-4e2d-a8aa-18dbd4d644e5
      Custom Authorizer: cld-iot-credentials-lambda-authorizer

   📨 MQTT Topics:
      Base Topic: 438/9RJ-US-UAA8845A
      Status Topics:
         - 438/9RJ-US-UAA8845A/status/current
         - 438/9RJ-US-UAA8845A/status/faults
         - 438/9RJ-US-UAA8845A/status/software
         - 438/9RJ-US-UAA8845A/status/summary
         - 438/9RJ-US-UAA8845A/status/sensor
         - 438/9RJ-US-UAA8845A/status/environmental
      Command Topics:
         - 438/9RJ-US-UAA8845A/command

   🏠 Local MQTT Connection Parameters:
      Host: Theater Fan.local (or device IP)
      MQTT Port: 1883
      MQTT+TLS Port: 8883
      Username: 9RJ-US-UAA8845A
      Password: Q0T3OiiA0/eb6gynNPYzv+1ovQMLkbx...
      Protocol: MQTT (plain or TLS)
      Root Topic: 438M

   🌐 Cloud MQTT Connection Parameters:
      Host: a1u2wvl3e2lrc4-ats.iot.eu-west-1.amazonaws.com
      Port: 443
      Protocol: MQTT over WebSockets with TLS
      Client ID: f91a40c3-44ed-4e2d-a8aa-18dbd4d644e5
      Auth Type: AWS IoT Custom Authorizer

============================================================
📊 TROUBLESHOOTING SUMMARY
============================================================
   Authentication: ✅ SUCCESS
   Total Devices: 1
   Connected Devices: 1
   Devices with Local Config: 1
   Devices with IoT Credentials: 1

💾 Detailed troubleshooting data exported to: dyson_troubleshooting_20250819_105651.json

🎉 Troubleshooting analysis complete!
```

## Output Files

The script generates a timestamped JSON file containing all collected data:

- **Filename Format**: `dyson_troubleshooting_YYYYMMDD_HHMMSS.json`
- **Contents**: Complete structured data including authentication details, device information, MQTT configurations, and IoT credentials
- **Use Case**: Detailed analysis, sharing with support, or integration with other tools

### JSON Structure

```json
{
  "timestamp": "2024-08-19T10:56:51.123456",
  "authentication": {
    "account_id": "bc8f2680-1f98-4c4d-8733-efb5003919d2",
    "email": "your-email@example.com",
    "country": "US",
    "culture": "en-US",
    "account_status": "ACTIVE",
    "authentication_method": "EMAIL_PWD_2FA",
    "token_type": "Bearer",
    "bearer_token": "full-token-here",
    "bearer_token_preview": "657EE842F50B6A90DE6D..."
  },
  "devices": [
    {
      "basic_info": {
        "name": "Theater Fan",
        "serial_number": "9RJ-US-UAA8845A",
        "type": "438",
        "model": "TP11",
        "category": "ec",
        "connection_category": "lecAndWifi",
        "variant": "M"
      },
      "connected_configuration": {
        "mqtt": {
          "local_broker_credentials_encrypted": "zVGln87HAMt8wVbgjk...",
          "mqtt_root_topic_level": "438M",
          "remote_broker_type": "wss",
          "local_broker_credentials_decrypted": "Q0T3OiiA0/eb6gynNPYzv..."
        },
        "firmware": {
          "version": "438MPF.00.01.003.0011",
          "auto_update_enabled": false,
          "new_version_available": false,
          "capabilities": ["AdvanceOscillationDay1", "Scheduling", "EnvironmentalData"]
        }
      },
      "iot_credentials": {
        "endpoint": "a1u2wvl3e2lrc4-ats.iot.eu-west-1.amazonaws.com",
        "credentials": {
          "client_id": "f91a40c3-44ed-4e2d-a8aa-18dbd4d644e5",
          "custom_authorizer_name": "cld-iot-credentials-lambda-authorizer",
          "token_key": "token",
          "token_value": "f91a40c3-44ed-4e2d-a8aa-18dbd4d644e5",
          "token_signature": "fODnWKQOrZ/v8YIPhHhel1oemv..."
        }
      },
      "mqtt_analysis": {
        "local_mqtt": {
          "host": "Theater Fan.local",
          "ports": {"mqtt": 1883, "mqtt_tls": 8883},
          "username": "9RJ-US-UAA8845A",
          "password": "Q0T3OiiA0/eb6gynNPYzv...",
          "protocol": "MQTT (plain or TLS)",
          "root_topic": "438M"
        },
        "cloud_mqtt": null,
        "topics": null
      }
    }
  ],
  "summary": {
    "total_devices": 1,
    "connected_devices": 1,
    "devices_with_local_config": 1,
    "devices_with_iot_credentials": 1,
    "authentication_successful": true
  }
}
```

## Troubleshooting Common Issues

### Authentication Failures

**Problem**: Authentication fails with "Invalid credentials"
- ✅ **Solution**: Verify email and password are correct
- ✅ **Solution**: Ensure account is active (not suspended)
- ✅ **Solution**: Check if 2FA is properly configured

**Problem**: OTP code not received
- ✅ **Solution**: Check spam/junk folder
- ✅ **Solution**: Wait 30-60 seconds for delivery
- ✅ **Solution**: Restart authentication process if code expires

**Problem**: OTP code rejected
- ✅ **Solution**: Ensure you're entering the most recent code
- ✅ **Solution**: Check for typos in the 6-digit code
- ✅ **Solution**: Verify time synchronization on your device

### Device Connection Issues

**Problem**: No devices found
- ✅ **Solution**: Verify devices are registered to your account via the Dyson app
- ✅ **Solution**: Check if you're using the correct country/region
- ✅ **Solution**: Ensure devices have been set up and connected at least once

**Problem**: Device shows "nonConnected" status
- ✅ **Solution**: Device may not support cloud connectivity
- ✅ **Solution**: Check device model compatibility with Dyson cloud services
- ✅ **Solution**: Verify device firmware is up to date

**Problem**: Local MQTT password decryption fails
- ✅ **Solution**: Device may not have local credentials configured
- ✅ **Solution**: Try connecting device to local WiFi via Dyson app first
- ✅ **Solution**: Check if device has been factory reset recently

**Problem**: IoT credentials unavailable
- ✅ **Solution**: Device must be connected and configured for cloud access
- ✅ **Solution**: Try reconnecting device through Dyson app
- ✅ **Solution**: Check if device is online and reachable

### Network and Connectivity

**Problem**: API timeouts or connection errors
- ✅ **Solution**: Check internet connection stability
- ✅ **Solution**: Verify firewall/proxy settings allow HTTPS traffic
- ✅ **Solution**: Try different network (mobile hotspot) to isolate network issues

**Problem**: MQTT connection testing fails
- ✅ **Solution**: Use provided connection parameters with MQTT client (like MQTT Explorer)
- ✅ **Solution**: For local MQTT: ensure you're on same network as device
- ✅ **Solution**: For cloud MQTT: verify AWS IoT endpoint is reachable

## Integration with MQTT Clients

The script provides complete connection parameters for both local and cloud MQTT connections:

### Local MQTT Connection (Direct to Device)
- **Host**: `[Device Name].local` or device IP address
- **Ports**: 1883 (plain MQTT) or 8883 (MQTT+TLS)
- **Username**: Device serial number
- **Password**: Decrypted local broker credentials
- **Root Topic**: Device-specific root topic (e.g., "438M")

### Cloud MQTT Connection (via AWS IoT)
- **Host**: AWS IoT endpoint (e.g., `a1u2wvl3e2lrc4-ats.iot.eu-west-1.amazonaws.com`)
- **Port**: 443 (MQTT over WebSockets with TLS)
- **Client ID**: AWS IoT client ID
- **Authentication**: AWS IoT Custom Authorizer with token headers

## Security Considerations

⚠️ **Important Security Notes**:

1. **Credential Storage**: This script outputs decrypted passwords and tokens. Do not share the output files publicly.

2. **OTP Codes**: OTP codes are single-use and time-limited. Never share or reuse them.

3. **Bearer Tokens**: The exported JSON contains full bearer tokens that provide account access. Protect these files.

4. **Local Network**: Local MQTT credentials provide direct device access on your network.

5. **Data Export**: Consider the sensitivity of exported troubleshooting data before sharing with others.

## Related Scripts

This troubleshooting script combines and extends functionality from:

- **`test_real_auth.py`**: Basic authentication and device listing
- **`analyze_mqtt_info.py`**: MQTT credential analysis and decryption
- **`usage_example.py`**: API usage patterns and error handling

For specific use cases, you may prefer the individual scripts:

- Use `test_real_auth.py` for quick authentication testing
- Use `analyze_mqtt_info.py` when you only need MQTT analysis
- Use `usage_example.py` for API integration examples

## Support

If you encounter issues with this script:

1. Check the troubleshooting section above
2. Review the exported JSON for detailed error information  
3. Test with individual scripts (`test_real_auth.py`, `analyze_mqtt_info.py`) to isolate issues
4. Ensure you have the latest version of the `libdyson-rest` library
5. Check your network connectivity and firewall settings

The comprehensive output from this script provides most information needed for diagnosing account and device connectivity issues.
