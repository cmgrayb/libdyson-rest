# Dyson REST API Client Documentation

This document prov    async with AsyncDysonClient("user@example.com", "your_password") as client:
        if not await client.authenticate():
            otp = input("Enter OTP from email: ")
            await client.complete_authentication(otp)
        devices = await client.get_devices()

asyncio.run(main())
```omprehensive documentation for both the synchronous and asynchronous Dyson REST API clients.

## Table of Contents

- [Quick Start](#quick-start)
- [Client Overview](#client-overview)
- [Synchronous Client (DysonClient)](#synchronous-client-dysonclient)
- [Asynchronous Client (AsyncDysonClient)](#asynchronous-client-asyncdysonclient)
- [Method Comparison Table](#method-comparison-table)
- [Authentication Flow](#authentication-flow)
- [Error Handling](#error-handling)
- [Data Models](#data-models)

## Quick Start

### Synchronous Usage
```python
from libdyson_rest import DysonClient

# Two-step authentication (recommended)
client = DysonClient("user@example.com", "your_password")
if not client.authenticate():  # Returns False - OTP needed
    otp = input("Enter OTP from email: ")
    client.complete_authentication(otp)

devices = client.get_devices()
for device in devices:
    print(f"Device: {device.name} ({device.serial})")

# Context manager usage
with DysonClient("user@example.com", "your_password") as client:
    if not client.authenticate():
        otp = input("Enter OTP from email: ")
        client.complete_authentication(otp)
    devices = client.get_devices()
```

### Asynchronous Usage
```python
import asyncio
from libdyson_rest import AsyncDysonClient

async def main():
    # Two-step authentication (recommended)
    client = AsyncDysonClient("user@example.com", "your_password")
    if not await client.authenticate():  # Returns False - OTP needed
        otp = input("Enter OTP from email: ")
        await client.complete_authentication(otp)
        
    devices = await client.get_devices()
    for device in devices:
        print(f"Device: {device.name} ({device.serial})")
    await client.close()

    # Context manager usage
    async with AsyncDysonClient("user@example.com", "your_password") as client:
        if await client.authenticate("123456"):
            devices = await client.get_devices()

asyncio.run(main())
```

## Client Overview

The library provides two client implementations:

- **`DysonClient`**: Synchronous client using `requests` library
- **`AsyncDysonClient`**: Asynchronous client using `httpx` library

Both clients provide identical APIs except for the async/await syntax and context manager protocols.

## Synchronous Client (DysonClient)

### Constructor

```python
class DysonClient:
    def __init__(
        self,
        email: str | None = None,
        auth_token: str | None = None,
        request_timeout: int = 30,
        user_agent: str = "android client"
    ) -> None
```

**Parameters:**
- `email` (str | None): User's email address for authentication
- `auth_token` (str | None): Pre-existing authentication token
- `request_timeout` (int): Request timeout in seconds (default: 30)
- `user_agent` (str): User agent string for requests (default: "android client")

### Authentication Methods

#### `provision() -> str`
Generates a unique device provision key for registration.

```python
provision_key = client.provision()
print(f"Provision key: {provision_key}")
```

**Returns:** String containing the provision key

#### `get_user_status(email: str | None = None) -> UserStatus`
Retrieves user account status information.

```python
status = client.get_user_status()
print(f"Status: {status.authentication_state}")
```

**Parameters:**
- `email` (str | None): Email address (uses instance email if None)

**Returns:** `UserStatus` object with account information

#### `begin_login(email: str | None = None) -> LoginChallenge`
Initiates the login process and requests OTP code.

```python
challenge = client.begin_login()
print(f"Challenge ID: {challenge.challenge_id}")
# User will receive OTP code via email/SMS
```

**Parameters:**
- `email` (str | None): Email address (uses instance email if None)

**Returns:** `LoginChallenge` object with challenge details

#### `complete_login(otp_code: str, challenge_id: str | None = None, mobile: str | None = None) -> LoginInformation`
Completes the login process with OTP code.

```python
login_info = client.complete_login("123456")
print(f"Auth token: {login_info.token}")
```

**Parameters:**
- `otp_code` (str): 6-digit OTP code from email/SMS
- `challenge_id` (str | None): Challenge ID from `begin_login()` (auto-retrieved if None)
- `mobile` (str | None): Mobile number for SMS delivery

**Returns:** `LoginInformation` object with authentication token

#### `authenticate(otp_code: str | None = None) -> bool`
High-level authentication method that handles the complete flow.

```python
# Two-step authentication (recommended)
if not client.authenticate():  # Returns False if OTP needed
    otp = input("Enter OTP code from email: ")
    client.complete_authentication(otp)
    print("Authentication successful!")

# Single-step authentication (if you already have OTP)
if client.authenticate("123456"):
    print("Authentication completed in one step!")
```

**Parameters:**
- `otp_code` (str | None): 6-digit OTP code from email (optional)

**Returns:** `bool` - True if authentication completed, False if OTP code still needed

#### `complete_authentication(otp_code: str) -> bool`
Complete authentication using the stored challenge ID from a previous `authenticate()` call.

```python
# This method is called after authenticate() returns False
success = client.complete_authentication("123456")
if success:
    print("Authentication completed!")
```

**Parameters:**
- `otp_code` (str): 6-digit OTP code from email

**Returns:** `bool` indicating authentication success

### Device Methods

#### `get_devices() -> list[Device]`
Retrieves all devices associated with the authenticated account.

```python
devices = client.get_devices()
for device in devices:
    print(f"{device.name}: {device.product_type} ({device.serial})")
```

**Returns:** List of `Device` objects

**Requires:** Authentication token

#### `get_iot_credentials(serial_number: str) -> IoTData`
Retrieves IoT/MQTT credentials for a specific device.

```python
iot_data = client.get_iot_credentials("DEVICE-SERIAL-123")
print(f"MQTT Host: {iot_data.host}")
print(f"Username: {iot_data.username}")
```

**Parameters:**
- `serial_number` (str): Device serial number

**Returns:** `IoTData` object with MQTT connection details

**Requires:** Authentication token

#### `get_pending_release(serial_number: str) -> PendingRelease`
Checks for pending firmware updates for a device.

```python
release = client.get_pending_release("DEVICE-SERIAL-123")
if release.update_available:
    print(f"Update available: {release.version}")
```

**Parameters:**
- `serial_number` (str): Device serial number

**Returns:** `PendingRelease` object with update information

**Requires:** Authentication token

### Utility Methods

#### `decrypt_local_credentials(encrypted_password: str, serial_number: str) -> tuple[str, str]`
Decrypts local device credentials for direct Wi-Fi connection.

```python
username, password = client.decrypt_local_credentials(
    encrypted_password="encrypted_data_here",
    serial_number="DEVICE-SERIAL-123"
)
print(f"Local credentials: {username}:{password}")
```

**Parameters:**
- `encrypted_password` (str): Base64-encoded encrypted password from device
- `serial_number` (str): Device serial number (used as decryption key)

**Returns:** Tuple of (username, password) for local device access

#### `get_auth_token() -> str | None`
Retrieves the current authentication token.

```python
token = client.get_auth_token()
if token:
    print(f"Current token: {token[:20]}...")
```

**Returns:** Authentication token string or None

#### `set_auth_token(token: str) -> None`
Sets the authentication token manually.

```python
client.set_auth_token("your_token_here")
```

**Parameters:**
- `token` (str): Authentication token to set

### Context Manager Methods

#### `close() -> None`
Closes the HTTP session and releases resources.

```python
client.close()
```

#### Context Manager Support
```python
with DysonClient("user@example.com") as client:
    # Client automatically closed when exiting context
    pass
```

### Property: `auth_token`
Get or set the authentication token as a property.

```python
# Get token
current_token = client.auth_token

# Set token
client.auth_token = "new_token_here"
```

## Asynchronous Client (AsyncDysonClient)

The `AsyncDysonClient` provides the same API as `DysonClient` but with async/await syntax.

### Constructor

```python
class AsyncDysonClient:
    def __init__(
        self,
        email: str | None = None,
        auth_token: str | None = None,
        request_timeout: int = 30,
        user_agent: str = "android client"
    ) -> None
```

Parameters are identical to `DysonClient`.

### Async Authentication Methods

#### `async def provision() -> str`
```python
provision_key = await client.provision()
```

#### `async def get_user_status(email: str | None = None) -> UserStatus`
```python
status = await client.get_user_status()
```

#### `async def begin_login(email: str | None = None) -> LoginChallenge`
```python
challenge = await client.begin_login()
```

#### `async def complete_login(otp_code: str, challenge_id: str | None = None, mobile: str | None = None) -> LoginInformation`
```python
login_info = await client.complete_login("123456")
```

#### `async def authenticate(otp_code: str | None = None) -> bool`
```python
# Two-step authentication (recommended)
if not await client.authenticate():  # Returns False if OTP needed
    otp = input("Enter OTP code from email: ")
    await client.complete_authentication(otp)
    print("Authentication successful!")

# Single-step authentication (if you already have OTP)
if await client.authenticate("123456"):
    print("Authentication completed in one step!")
```

#### `async def complete_authentication(otp_code: str) -> bool`
Complete authentication using the stored challenge ID from a previous `authenticate()` call.

```python
# This method is called after authenticate() returns False
success = await client.complete_authentication("123456")
if success:
    print("Authentication completed!")
```

### Async Device Methods

#### `async def get_devices() -> list[Device]`
```python
devices = await client.get_devices()
```

#### `async def get_iot_credentials(serial_number: str) -> IoTData`
```python
iot_data = await client.get_iot_credentials("DEVICE-SERIAL-123")
```

#### `async def get_pending_release(serial_number: str) -> PendingRelease`
```python
release = await client.get_pending_release("DEVICE-SERIAL-123")
```

### Async Context Manager

#### `async def close() -> None`
```python
await client.close()
```

#### Async Context Manager Support
```python
async with AsyncDysonClient("user@example.com") as client:
    # Client automatically closed when exiting context
    pass
```

### Utility Methods (Synchronous)

The following utility methods are synchronous in both clients:

- `decrypt_local_credentials()` - Cryptographic operation, no I/O
- `get_auth_token()` - Property access, no I/O
- `set_auth_token()` - Property access, no I/O
- `auth_token` property - Property access, no I/O

## Method Comparison Table

| Operation | Synchronous Client | Asynchronous Client |
|-----------|-------------------|---------------------|
| **Constructor** | `DysonClient(email, ...)` | `AsyncDysonClient(email, ...)` |
| **Provision** | `client.provision()` | `await client.provision()` |
| **User Status** | `client.get_user_status()` | `await client.get_user_status()` |
| **Begin Login** | `client.begin_login()` | `await client.begin_login()` |
| **Complete Login** | `client.complete_login(otp)` | `await client.complete_login(otp)` |
| **Authenticate** | `client.authenticate(otp)` | `await client.authenticate(otp)` |
| **Get Devices** | `client.get_devices()` | `await client.get_devices()` |
| **IoT Credentials** | `client.get_iot_credentials(serial)` | `await client.get_iot_credentials(serial)` |
| **Pending Release** | `client.get_pending_release(serial)` | `await client.get_pending_release(serial)` |
| **Decrypt Credentials** | `client.decrypt_local_credentials(...)` | `client.decrypt_local_credentials(...)` |
| **Get Token** | `client.get_auth_token()` | `client.get_auth_token()` |
| **Set Token** | `client.set_auth_token(token)` | `client.set_auth_token(token)` |
| **Token Property** | `client.auth_token` | `client.auth_token` |
| **Close** | `client.close()` | `await client.close()` |
| **Context Manager** | `with client:` | `async with client:` |

## Authentication Flow

### Two-Step Authentication (Recommended)

The new authentication flow properly handles the OTP process by returning `False` when an OTP code is needed:

#### Synchronous Client
```python
from libdyson_rest import DysonClient

client = DysonClient("user@example.com", "your_password")

try:
    # Step 1: Start authentication (triggers OTP email)
    if not client.authenticate():  # Returns False - OTP needed
        print("Check your email for OTP code")
        otp_code = input("Enter OTP code: ")
        
        # Step 2: Complete authentication with OTP
        if client.complete_authentication(otp_code):
            print("Authentication successful!")
            devices = client.get_devices()
            print(f"Found {len(devices)} devices")
    else:
        print("Authentication completed immediately") 
        
finally:
    client.close()
```

#### Asynchronous Client  
```python
import asyncio
from libdyson_rest import AsyncDysonClient

async def authenticate():
    client = AsyncDysonClient("user@example.com", "your_password")
    
    try:
        # Step 1: Start authentication (triggers OTP email)
        if not await client.authenticate():  # Returns False - OTP needed
            print("Check your email for OTP code")
            otp_code = input("Enter OTP code: ")
            
            # Step 2: Complete authentication with OTP
            if await client.complete_authentication(otp_code):
                print("Authentication successful!")
                devices = await client.get_devices()
                print(f"Found {len(devices)} devices")
        else:
            print("Authentication completed immediately")
            
    finally:
        await client.close()

asyncio.run(authenticate())
```

### Single-Step Authentication (If You Have OTP)

If you already have the OTP code, you can complete authentication in one call:

```python
# Sync
if client.authenticate("123456"):  # OTP code
    devices = client.get_devices()

# Async  
if await client.authenticate("123456"):  # OTP code
    devices = await client.get_devices()
```

### Manual Authentication Steps

For advanced use cases, you can use the lower-level methods:

```python
from libdyson_rest import DysonClient

client = DysonClient("user@example.com", "your_password")

try:
    # Step-by-step authentication
    challenge = client.begin_login()
    print(f"Check your email/SMS for OTP (Challenge: {challenge.challenge_id})")
    
    otp_code = input("Enter OTP code: ")
    login_info = client.complete_login(challenge.challenge_id, otp_code)
    
    # Token is automatically set, can now use authenticated methods
    devices = client.get_devices()
    
    # Save token for later use
    saved_token = client.auth_token
    
finally:
    client.close()
```
        
        # Save token for later use
        saved_token = client.auth_token
        
    finally:
        await client.close()

asyncio.run(authenticate_and_get_devices())
```

### Token Reuse Example

```python
# Save token after first authentication
client = DysonClient("user@example.com")
if client.authenticate("123456"):
    saved_token = client.auth_token
    
# Later session - reuse token
client = DysonClient(auth_token=saved_token)
devices = client.get_devices()  # No re-authentication needed
```

## Error Handling

The library provides specific exception types for different error conditions:

### Exception Hierarchy

```python
from libdyson_rest.exceptions import (
    DysonAPIError,        # Base exception
    DysonAuthError,       # Authentication failures
    DysonConnectionError  # Network/connection issues
)
```

### Error Handling Examples

```python
from libdyson_rest import DysonClient
from libdyson_rest.exceptions import DysonAuthError, DysonConnectionError, DysonAPIError

client = DysonClient("user@example.com")

try:
    if client.authenticate("123456"):
        devices = client.get_devices()
        
except DysonAuthError as e:
    print(f"Authentication failed: {e}")
    # Invalid credentials, expired token, etc.
    
except DysonConnectionError as e:
    print(f"Connection problem: {e}")
    # Network issues, timeouts, DNS problems
    
except DysonAPIError as e:
    print(f"API error: {e}")
    # Server errors, invalid responses, rate limiting
    
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Async Error Handling

```python
import asyncio
from libdyson_rest import AsyncDysonClient
from libdyson_rest.exceptions import DysonAuthError, DysonConnectionError

async def handle_errors():
    client = AsyncDysonClient("user@example.com")
    
    try:
        if await client.authenticate("123456"):
            devices = await client.get_devices()
            
    except DysonAuthError as e:
        print(f"Authentication failed: {e}")
        
    except DysonConnectionError as e:
        print(f"Connection problem: {e}")
        
    finally:
        await client.close()

asyncio.run(handle_errors())
```

## Data Models

The library provides structured data models for API responses:

### Device Model

```python
@dataclass
class Device:
    serial: str                    # Device serial number
    name: str                      # User-assigned device name
    version: str                   # Firmware version
    credentials: str               # Encrypted local credentials
    auto_update: bool              # Auto-update enabled
    new_version_available: bool    # Update available
    product_type: str              # Device model/type
    connection_type: str           # Connection method
    local_credentials: tuple[str, str] | None  # Decrypted credentials
```

### IoTData Model

```python
@dataclass
class IoTData:
    host: str          # MQTT broker hostname
    port: int          # MQTT broker port
    username: str      # MQTT username
    password: str      # MQTT password
    topic: str         # MQTT topic prefix
```

### UserStatus Model

```python
@dataclass
class UserStatus:
    authentication_state: str  # Current auth state
    # Additional status fields...
```

### LoginChallenge Model

```python
@dataclass
class LoginChallenge:
    challenge_id: str  # Unique challenge identifier
    # Additional challenge fields...
```

### LoginInformation Model

```python
@dataclass
class LoginInformation:
    token: str         # Authentication token
    account: dict      # Account information
    # Additional login fields...
```

### PendingRelease Model

```python
@dataclass
class PendingRelease:
    update_available: bool  # Whether update is available
    version: str           # Available version
    # Additional release fields...
```

## Best Practices

### 1. Use Context Managers

Always use context managers to ensure proper resource cleanup:

```python
# Synchronous
with DysonClient("user@example.com") as client:
    # Your code here
    pass

# Asynchronous
async with AsyncDysonClient("user@example.com") as client:
    # Your code here
    pass
```

### 2. Token Persistence

Save authentication tokens to avoid repeated login:

```python
# First authentication
client = DysonClient("user@example.com")
if client.authenticate("123456"):
    token = client.auth_token
    # Save token to file/database
    
# Subsequent uses
client = DysonClient(auth_token=saved_token)
```

### 3. Error Handling

Always handle specific exceptions:

```python
try:
    devices = client.get_devices()
except DysonAuthError:
    # Re-authenticate
    pass
except DysonConnectionError:
    # Retry or fail gracefully
    pass
```

### 4. Choose the Right Client

- Use `DysonClient` for simple scripts and synchronous applications
- Use `AsyncDysonClient` for web servers, concurrent applications, or when integrating with async frameworks like Home Assistant

### 5. Timeout Configuration

Adjust timeouts based on your network conditions:

```python
# Longer timeout for slow networks
client = DysonClient("user@example.com", request_timeout=60)
```

## Examples

See the `examples/` directory for more comprehensive usage examples:

- `usage_example.py` - Basic synchronous usage
- `example_token_usage.py` - Token persistence examples
- `test_real_auth.py` - Real authentication testing
- `troubleshoot_account.py` - Account troubleshooting utilities

## Migration from Sync to Async

Converting from synchronous to asynchronous usage:

```python
# Before (Sync)
from libdyson_rest import DysonClient

client = DysonClient("user@example.com")
if client.authenticate("123456"):
    devices = client.get_devices()
client.close()

# After (Async)
import asyncio
from libdyson_rest import AsyncDysonClient

async def main():
    client = AsyncDysonClient("user@example.com")
    if await client.authenticate("123456"):
        devices = await client.get_devices()
    await client.close()

asyncio.run(main())
```

The key changes:
1. Import `AsyncDysonClient` instead of `DysonClient`
2. Make your function `async`
3. Use `await` before client method calls
4. Use `await client.close()` instead of `client.close()`
5. Run with `asyncio.run()` or integrate with existing async event loop