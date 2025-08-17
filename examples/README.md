# Examples

This directory contains example scripts demonstrating how to use the `libdyson-rest` library.

## Example Scripts

### 1. `usage_example.py`
**Purpose**: Basic usage demonstration showing authentication and device listing.

**What it demonstrates**:
- Complete authentication flow with OTP
- Getting user account information
- Listing devices and their properties
- Basic error handling

**Usage**:
```bash
cd examples
python usage_example.py
```

### 2. `example_token_usage.py`
**Purpose**: Shows how to use token-based authentication for stateless operations.

**What it demonstrates**:
- Saving and reusing bearer tokens
- Stateless API calls without re-authentication
- Token management best practices

**Usage**:
```bash
cd examples
python example_token_usage.py
```

### 3. `test_real_auth.py`
**Purpose**: Development script for testing authentication with real Dyson accounts.

**What it demonstrates**:
- Interactive authentication testing
- Device enumeration and details
- IoT credential retrieval
- MQTT connection parameters

**Usage**:
```bash
cd examples
python test_real_auth.py
```

**Note**: This script requires real Dyson account credentials.

### 4. `analyze_mqtt_info.py`
**Purpose**: Utility for analyzing MQTT connection information from devices.

**What it demonstrates**:
- MQTT credential decryption
- Connection parameter extraction
- Local vs cloud MQTT setup
- AES decryption implementation

**Usage**:
```bash
cd examples
python analyze_mqtt_info.py [path_to_mqtt_info.json]
```

## Prerequisites

Before running these examples:

1. **Install the package**:
   ```bash
   pip install libdyson-rest
   ```

   Or in development mode:
   ```bash
   pip install -e .
   ```

2. **Have a Dyson account** ready with:
   - Email address
   - Password
   - At least one registered Dyson device

## Common Usage Pattern

Most examples follow this pattern:

```python
from libdyson_rest import DysonClient

# Initialize client
client = DysonClient(
    email="your.email@example.com",
    password="your_password"
)

try:
    # Authenticate
    challenge = client.begin_login()
    otp_code = input("Enter OTP from email: ")
    login_info = client.complete_login(
        str(challenge.challenge_id),
        otp_code
    )

    # Use authenticated client
    devices = client.get_devices()
    # ... do something with devices

finally:
    client.close()
```

## Environment Variables

Some examples support environment variables for convenience:

- `DYSON_EMAIL`: Your Dyson account email
- `DYSON_PASSWORD`: Your Dyson account password

Set these to avoid entering credentials repeatedly during development.

## Notes

- These scripts are for **development and testing** only
- They are **not included** in the PyPI package distribution
- Real credentials are required for most examples
- Some scripts may create temporary files (e.g., token storage)

## Troubleshooting

1. **Import errors**: Make sure you've installed the package or are running from the project root
2. **Authentication failures**: Check your email/password and ensure OTP codes are entered quickly
3. **No devices found**: Ensure you have registered Dyson devices in your account
4. **MQTT connection issues**: Check that your devices are online and connected to WiFi

## ⚠️ Security Note

**Never commit sensitive data to version control!**

- Device-specific files (e.g., `mqtt_info_*.json`) are automatically ignored by `.gitignore`
- Credential files and authentication tokens are excluded from the repository
- Use environment variables for credentials when possible
- These example scripts may create temporary files - review before committing changes
