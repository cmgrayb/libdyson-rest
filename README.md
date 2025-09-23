# libdyson-rest

[![PyPI version](https://badge.fury.io/py/libdyson-rest.svg)](https://badge.fury.io/py/libdyson-rest)
[![Python](https://img.shields.io/pypi/pyversions/libdyson-rest.svg)](https://pypi.org/project/libdyson-rest/)
[![License](https://img.shields.io/pypi/l/libdyson-rest.svg)](https://github.com/cmgrayb/libdyson-rest/blob/main/LICENSE)

A Python library for interacting with Dyson devices through their official REST API.

## Features

- **Official API Compliance**: Implements the complete Dyson App API as documented in their OpenAPI specification
- **Two-Step Authentication**: Secure login process with OTP codes
- **Complete Device Management**: List devices, get device details, and retrieve IoT credentials
- **MQTT Connection Support**: Extract both cloud (AWS IoT) and local MQTT connection parameters
- **Password Decryption**: Decrypt local MQTT broker credentials for direct device communication
- **Token-Based Authentication**: Store and reuse authentication tokens for repeated API calls
- **Type-Safe Models**: Comprehensive data models with proper type hints
- **Error Handling**: Detailed exception hierarchy for robust error handling
- **Context Manager Support**: Automatic resource cleanup
- **Async/Await Support**: Full asynchronous client for Home Assistant and other async environments

## Installation

Install from PyPI:

```bash
pip install libdyson-rest
```

Or install from source:

```bash
git clone https://github.com/cmgrayb/libdyson-rest.git
cd libdyson-rest
pip install -e .
```

## Documentation

For comprehensive API documentation, see:

- **[API Reference](docs/API.md)** - Complete method documentation for both sync and async clients
- **[Examples](examples/)** - Practical usage examples and troubleshooting tools
- **[Type Checking Guide](docs/STRICT_TYPE_CHECKING.md)** - Advanced type checking configuration
- **[Modern Type Hints](docs/MODERN_TYPE_HINTS.md)** - Type hint patterns and best practices

### Quick Reference

| Client Type | Import | Context Manager | Best For |
|------------|--------|-----------------|----------|
| **Synchronous** | `from libdyson_rest import DysonClient` | `with DysonClient() as client:` | Scripts, simple applications |
| **Asynchronous** | `from libdyson_rest import AsyncDysonClient` | `async with AsyncDysonClient() as client:` | Home Assistant, web servers, concurrent apps |

## Quick Start

### Synchronous Usage

```python
from libdyson_rest import DysonClient

# Initialize the client
client = DysonClient(email="your@email.com")

# High-level authentication (recommended)
if client.authenticate("123456"):  # OTP code from email
    devices = client.get_devices()
    for device in devices:
        print(f"Device: {device.name} ({device.serial})")
        
client.close()
```

### Asynchronous Usage (Recommended for Home Assistant)

```python
import asyncio
from libdyson_rest import AsyncDysonClient

async def main():
    async with AsyncDysonClient(email="your@email.com") as client:
        if await client.authenticate("123456"):  # OTP code from email
            devices = await client.get_devices()
            for device in devices:
                print(f"Device: {device.name} ({device.serial})")

asyncio.run(main())
```

### Manual Authentication Flow

```python
from libdyson_rest import DysonClient

# Initialize the client
client = DysonClient(
    email="your@email.com",
    password="your_password",
    country="US",        # ISO 3166-1 alpha-2 country code
    culture="en-US"      # IETF language code
)

# Two-step authentication process
try:
    # Step 1: Begin login process
    challenge = client.begin_login()
    print(f"Challenge ID: {challenge.challenge_id}")
    print("Check your email for an OTP code")

    # Step 2: Complete login with OTP code
    otp_code = input("Enter OTP code: ")
    login_info = client.complete_login(str(challenge.challenge_id), otp_code)
    print(f"Logged in! Account: {login_info.account}")

    # Get devices
    devices = client.get_devices()
    for device in devices:
        print(f"Device: {device.name} ({device.serial_number})")
        print(f"  Type: {device.type}")
        print(f"  Category: {device.category.value}")

        # Get IoT credentials for connected devices
        if device.connection_category.value != "nonConnected":
            iot_data = client.get_iot_credentials(device.serial_number)
            print(f"  IoT Endpoint: {iot_data.endpoint}")

        # Check for firmware updates
        try:
            pending_release = client.get_pending_release(device.serial_number)
            print(f"  Pending Firmware: {pending_release.version}")
            print(f"  Update Pushed: {pending_release.pushed}")
        except Exception as e:
            print(f"  No pending firmware info available")

finally:
    client.close()
```

### Async/Await Usage (Recommended for Home Assistant)

```python
import asyncio
from libdyson_rest import AsyncDysonClient

async def main():
    # Use async context manager for automatic cleanup
    async with AsyncDysonClient(
        email="your@email.com",
        password="your_password",
        country="US",
        culture="en-US"
    ) as client:
        # Two-step authentication process
        challenge = await client.begin_login()
        print(f"Challenge ID: {challenge.challenge_id}")
        print("Check your email for an OTP code")

        otp_code = input("Enter OTP code: ")
        login_info = await client.complete_login(str(challenge.challenge_id), otp_code)
        print(f"Logged in! Account: {login_info.account}")

        # Get devices
        devices = await client.get_devices()
        for device in devices:
            print(f"Device: {device.name} ({device.serial_number})")

            # Get IoT credentials for connected devices
            if device.connection_category.value != "nonConnected":
                iot_data = await client.get_iot_credentials(device.serial_number)
                print(f"  IoT Endpoint: {iot_data.endpoint}")

# Run the async function
asyncio.run(main())
```

## Authentication Flow

The Dyson API uses a secure two-step authentication process:

### 1. API Provisioning (Automatic)
```python
version = client.provision()  # Called automatically
```

### 2. User Status Check (Optional)
```python
user_status = client.get_user_status()
print(f"Account status: {user_status.account_status.value}")
```

### 3. Begin Login Process
```python
challenge = client.begin_login()
# This triggers an OTP code to be sent to your email
```

### 4. Complete Login with OTP
```python
login_info = client.complete_login(
    challenge_id=str(challenge.challenge_id),
    otp_code="123456"  # From your email
)
```

### 5. Authenticated API Calls
```python
devices = client.get_devices()
iot_data = client.get_iot_credentials("device_serial")
```

## API Reference

### DysonClient

#### Constructor
```python
DysonClient(
    email: Optional[str] = None,
    password: Optional[str] = None,
    country: str = "US",
    culture: str = "en-US",
    timeout: int = 30,
    user_agent: str = "android client"
)
```

#### Core Methods

##### Authentication
- `provision() -> str`: Required initial API call
- `get_user_status(email=None) -> UserStatus`: Check account status
- `begin_login(email=None) -> LoginChallenge`: Start login process
- `complete_login(challenge_id, otp_code, email=None, password=None) -> LoginInformation`: Complete authentication
- `authenticate(otp_code=None) -> bool`: Convenience method for full auth flow

##### Device Management
- `get_devices() -> List[Device]`: List all account devices
- `get_iot_credentials(serial_number) -> IoTData`: Get AWS IoT connection info
- `get_pending_release(serial_number) -> PendingRelease`: Get pending firmware release info

##### Session Management
- `close() -> None`: Close session and clear state
- `__enter__()` and `__exit__()`: Context manager support

### AsyncDysonClient

The async client provides the same functionality as `DysonClient` but with async/await support for better performance in async environments like Home Assistant.

#### Constructor
```python
AsyncDysonClient(
    email: Optional[str] = None,
    password: Optional[str] = None,
    country: str = "US",
    culture: str = "en-US",
    timeout: int = 30,
    user_agent: str = "android client"
)
```

#### Core Methods (All Async)

##### Authentication
- `await provision() -> str`: Required initial API call
- `await get_user_status(email=None) -> UserStatus`: Check account status
- `await begin_login(email=None) -> LoginChallenge`: Start login process
- `await complete_login(challenge_id, otp_code, email=None, password=None) -> LoginInformation`: Complete authentication
- `await authenticate(otp_code=None) -> bool`: Convenience method for full auth flow

##### Device Management
- `await get_devices() -> List[Device]`: List all account devices
- `await get_iot_credentials(serial_number) -> IoTData`: Get AWS IoT connection info
- `await get_pending_release(serial_number) -> PendingRelease`: Get pending firmware release info

##### Session Management
- `await close() -> None`: Close async session and clear state
- `async with AsyncDysonClient() as client:`: Async context manager support

**Note**: All methods except `decrypt_local_credentials()`, `get_auth_token()`, and `set_auth_token()` are async and must be awaited.

### Data Models

#### Device
```python
@dataclass
class Device:
    category: DeviceCategory          # ec, flrc, hc, light, robot, wearable
    connection_category: ConnectionCategory  # lecAndWifi, lecOnly, nonConnected, wifiOnly
    model: str
    name: str
    serial_number: str
    type: str
    variant: Optional[str] = None
    connected_configuration: Optional[ConnectedConfiguration] = None
```

#### DeviceCategory (Enum)
- `ENVIRONMENT_CLEANER = "ec"` - Air filters, purifiers
- `FLOOR_CLEANER = "flrc"` - Vacuum cleaners
- `HAIR_CARE = "hc"` - Hair dryers, stylers
- `LIGHT = "light"` - Lighting products
- `ROBOT = "robot"` - Robot vacuums
- `WEARABLE = "wearable"` - Wearable devices

#### ConnectionCategory (Enum)
- `LEC_AND_WIFI = "lecAndWifi"` - Bluetooth and Wi-Fi
- `LEC_ONLY = "lecOnly"` - Bluetooth only
- `NON_CONNECTED = "nonConnected"` - No connectivity
- `WIFI_ONLY = "wifiOnly"` - Wi-Fi only

#### LoginInformation
```python
@dataclass
class LoginInformation:
    account: UUID      # Account ID
    token: str         # Bearer token for API calls
    token_type: TokenType  # Always "Bearer"
```

#### IoTData
```python
@dataclass
class IoTData:
    endpoint: str              # AWS IoT endpoint
    iot_credentials: IoTCredentials  # Connection credentials
```

#### PendingRelease
```python
@dataclass
class PendingRelease:
    version: str     # Pending firmware version
    pushed: bool     # Whether update has been pushed to device
```

### Exception Hierarchy

```
DysonAPIError (base)
├── DysonConnectionError    # Network/connection issues
├── DysonAuthError         # Authentication failures
├── DysonDeviceError       # Device operation failures
└── DysonValidationError   # Input validation errors
```

## Advanced Usage

### Using Context Manager
```python
with DysonClient(email="your@email.com", password="password") as client:
    # Authentication
    challenge = client.begin_login()
    otp = input("Enter OTP: ")
    client.complete_login(str(challenge.challenge_id), otp)

    # API calls
    devices = client.get_devices()
    # Client automatically closed on exit
```

### Error Handling
```python
from libdyson_rest import DysonAuthError, DysonConnectionError, DysonAPIError

try:
    client = DysonClient(email="user@example.com", password="pass")
    challenge = client.begin_login()

except DysonAuthError as e:
    print(f"Authentication failed: {e}")
except DysonConnectionError as e:
    print(f"Network error: {e}")
except DysonAPIError as e:
    print(f"API error: {e}")
```

### Manual Authentication Steps
```python
client = DysonClient(email="user@example.com", password="password")

# Step 1: Provision (required)
version = client.provision()
print(f"API version: {version}")

# Step 2: Check user status
user_status = client.get_user_status()
print(f"Account active: {user_status.account_status.value == 'ACTIVE'}")

# Step 3: Begin login
challenge = client.begin_login()
print("Check email for OTP")

# Step 4: Complete login
otp = input("OTP: ")
login_info = client.complete_login(str(challenge.challenge_id), otp)
print(f"Bearer token: {login_info.token[:10]}...")

# Step 5: Use authenticated endpoints
devices = client.get_devices()
```

## Configuration

### Environment Variables
- `DYSON_EMAIL`: Default email address
- `DYSON_PASSWORD`: Default password
- `DYSON_COUNTRY`: Default country code (default: "US")
- `DYSON_CULTURE`: Default culture/locale (default: "en-US")
- `DYSON_TIMEOUT`: Request timeout in seconds (default: "30")

### Country and Culture Codes
- **Country**: 2-letter uppercase ISO 3166-1 alpha-2 codes (e.g., "US", "GB", "DE")
- **Culture**: 5-character IETF language codes (e.g., "en-US", "en-GB", "de-DE")

### Regional API Endpoints

The library automatically selects the appropriate Dyson API endpoint based on your country code:

| Country Code | Region | API Endpoint |
|--------------|--------|--------------|
| `CN` | China | `https://appapi.cp.dyson.cn` |
| All others | Default | `https://appapi.cp.dyson.com` |

**Examples:**
```python
# Chinese users
client = DysonClient(country="CN")  # Uses appapi.cp.dyson.cn

# All other users (US, UK, AU, NZ, etc.)
client = DysonClient(country="US")  # Uses appapi.cp.dyson.com (default)
client = DysonClient(country="GB")  # Uses appapi.cp.dyson.com (default)
```

**Note**: Regional endpoint selection is automatic and requires no code changes. Simply specify the correct country code for your region, and the library will route requests to the appropriate API server.

## API Compliance

This library implements the complete Dyson App API as documented in their OpenAPI specification:
- Authentication endpoints (`/v3/userregistration/email/*`)
- Device management (`/v3/manifest`)
- IoT credentials (`/v2/authorize/iot-credentials`)
- Provisioning (`/v1/provisioningservice/application/Android/version`)

## Requirements

- Python 3.10+
- `requests` - HTTP client library
- `dataclasses` - Data model support (Python 3.10+)

## Contributing

Contributions are welcome! Please ensure all changes maintain compatibility with the official Dyson OpenAPI specification.

## Versioning & Releases

This project follows **PEP 440** versioning (not semantic versioning). Here's how versions are distributed:

### Version Patterns

| Pattern | Example | Distribution | Purpose |
|---------|---------|--------------|---------|
| **Alpha** | `0.3.0a1`, `0.3.0alpha1` | TestPyPI | Internal testing only |
| **Dev** | `0.3.0.dev1` | TestPyPI | Development builds |
| **Beta** | `0.3.0b1`, `0.3.0beta1` | **PyPI** | Public beta testing |
| **RC** | `0.3.0rc1` | **PyPI** | Release candidates |
| **Stable** | `0.3.0` | **PyPI** | Production releases |
| **Patch** | `0.3.0.post1` | **PyPI** | Post-release patches |

### Installation

```bash
# Install stable release
pip install libdyson-rest

# Install latest beta (includes rc, beta versions)
pip install --pre libdyson-rest

# Install specific version
pip install libdyson-rest==0.7.0b1

# Install from TestPyPI (alpha/dev versions)
pip install -i https://test.pypi.org/simple/ libdyson-rest==0.7.0a1
```

### For Beta Testers

Want to help test new features? Install pre-release versions:

```bash
pip install --pre libdyson-rest
```

This will install the latest beta or release candidate, giving you access to new features before stable release.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This is an unofficial library. Dyson is a trademark of Dyson Ltd. This library is not affiliated with, endorsed by, or sponsored by Dyson Ltd.

## OpenAPI Specification

This library is based on the community-documented Dyson App API OpenAPI specification. The specification can be found at:
https://raw.githubusercontent.com/libdyson-wg/appapi/refs/heads/main/openapi.yaml

This project is created to further the efforts of others in the community in interacting with the
Dyson devices they have purchased to better integrate them into their smart homes.

At this time, this library is PURELY EXPERIMENTAL and should not be used without carefully examining
the code before doing so. **USE AT YOUR OWN RISK**

## Features

- Clean, intuitive API for Dyson device interaction
- Full type hints support
- Comprehensive error handling
- Async/sync support
- Built-in authentication handling
- Extensive test coverage

## Installation

### From Source (Development)

```bash
# Clone the repository
git clone https://github.com/cmgrayb/libdyson-rest.git
cd libdyson-rest

# Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate

# Install development dependencies
pip install -r requirements-dev.txt
```

## Quick Start

```python
from libdyson_rest import DysonClient

# Initialize the client
client = DysonClient(
    email="your_email@example.com",
    password="your_password",
    country="US"
)

# Authenticate with Dyson API
client.authenticate()

# Get your devices
devices = client.get_devices()
for device in devices:
    print(f"Device: {device['name']} ({device['serial']})")

# Always close the client when done
client.close()

# Or use as context manager
with DysonClient(email="email@example.com", password="password") as client:
    client.authenticate()
    devices = client.get_devices()
    # Client is automatically closed
```

## Development

This project uses several tools to maintain code quality:

- **Black**: Code formatting (120 character line length)
- **Flake8**: Linting and style checking
- **isort**: Import sorting
- **MyPy**: Type checking
- **Pytest**: Testing framework
- **Pre-commit**: Git hooks

### Setting up Development Environment

1. **Create virtual environment and install dependencies:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements-dev.txt
   ```

2. **Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```

### VSCode Tasks

This project includes VSCode tasks for common development operations:

- **Setup Dev Environment**: Create venv and install dependencies
- **Format Code**: Run Black formatter
- **Lint Code**: Run Flake8 linter
- **Sort Imports**: Run isort
- **Type Check**: Run MyPy type checker
- **Run Tests**: Execute pytest with coverage
- **Check All**: Run all quality checks in sequence

Access these via `Ctrl+Shift+P` → "Tasks: Run Task"

### Code Quality Commands

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .

# Type check
mypy src/libdyson_rest

# Run tests
pytest

# Run all checks
black . && isort . && flake8 . && mypy src/libdyson_rest && pytest
```

### Testing

Run tests with coverage:

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# With coverage report
pytest --cov=src/libdyson_rest --cov-report=html
```

## Project Structure

```
libdyson-rest/
├── src/
│   └── libdyson_rest/          # Main library code
│       ├── __init__.py
│       ├── client.py           # Main API client
│       ├── exceptions.py       # Custom exceptions
│       ├── models/             # Data models
│       └── utils/              # Utility functions
├── tests/
│   ├── unit/                   # Unit tests
│   └── integration/            # Integration tests
├── .vscode/
│   └── tasks.json             # VSCode tasks
├── requirements.txt           # Production dependencies
├── requirements-dev.txt       # Development dependencies
├── pyproject.toml            # Project configuration
├── .flake8                   # Flake8 configuration
├── .pre-commit-config.yaml   # Pre-commit hooks
└── README.md
```

## Configuration Files

- **pyproject.toml**: Main project configuration (Black, isort, pytest, mypy)
- **.flake8**: Flake8 linting configuration
- **.pre-commit-config.yaml**: Git pre-commit hooks
- **requirements.txt**: Production dependencies
- **requirements-dev.txt**: Development dependencies

## Publishing to PyPI

This package is automatically published to PyPI using GitHub Actions. For detailed publishing instructions, see [PUBLISHING.md](PUBLISHING.md).

### Quick Publishing

- **Test Release**: GitHub Actions → Run workflow → TestPyPI
- **Production Release**: Create a GitHub release with version tag (e.g., `v0.2.0`)
- **Local Build**: `python .github/scripts/publish_to_pypi.py --check`

The package is available on PyPI as `libdyson-rest`.

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes following the coding standards
4. Run all quality checks: ensure Black, Flake8, isort, MyPy, and tests pass
5. Commit your changes: `git commit -am 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Create a Pull Request

All PRs must pass the full test suite and code quality checks.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Security

- No hardcoded credentials or sensitive data
- Use environment variables for configuration
- All user inputs are validated
- API responses are sanitized

## Home Assistant Integration

This library is designed to work seamlessly with Home Assistant and other async Python environments. Use the `AsyncDysonClient` for optimal performance:

```python
import asyncio
from libdyson_rest import AsyncDysonClient

class DysonDeviceCoordinator:
    """Example Home Assistant coordinator pattern."""
    
    def __init__(self, hass, email, password, auth_token=None):
        self.hass = hass
        self.client = AsyncDysonClient(
            email=email,
            password=password,
            auth_token=auth_token
        )
    
    async def async_update_data(self):
        """Update device data."""
        try:
            devices = await self.client.get_devices()
            return {device.serial_number: device for device in devices}
        except Exception as err:
            _LOGGER.error("Error updating Dyson devices: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}")
    
    async def async_get_iot_credentials(self, serial_number):
        """Get IoT credentials for MQTT connection."""
        return await self.client.get_iot_credentials(serial_number)
    
    async def async_close(self):
        """Close the client session."""
        await self.client.close()
```

### Performance Benefits

- **Non-blocking I/O**: All HTTP requests are non-blocking
- **Concurrent Operations**: Multiple device operations can run simultaneously
- **Resource Efficient**: Proper async session management
- **Home Assistant Ready**: Follows HA async patterns and best practices

## Roadmap

- [x] Complete API endpoint coverage
- [x] Asynchronous client support
- [ ] WebSocket real-time updates
- [ ] Command-line interface
- [ ] Docker container support
