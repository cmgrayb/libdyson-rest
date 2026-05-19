# Dyson REST API Client Documentation

This document prov    # Dyson REST API Client Documentation

This document provides comprehensive documentation for both the synchronous and asynchronous Dyson REST API clients.

## Table of Contents

- [Quick Start](#quick-start)
- [Client Overview](#client-overview)
- [Synchronous Client (DysonClient)](#synchronous-client-dysonclient)
  - [Authentication Methods](#authentication-methods)
  - [Device Management Methods](#device-management-methods)
  - [Vis Nav Robot Vacuum Methods](#vis-nav-robot-vacuum-methods)
  - [EC Air Purifier Methods](#ec-air-purifier-methods)
- [Asynchronous Client (AsyncDysonClient)](#asynchronous-client-asyncdysonclient)
- [Method Comparison Table](#method-comparison-table)
- [Authentication Flow](#authentication-flow)
- [Error Handling](#error-handling)
- [Data Models](#data-models)
  - [Vis Nav Robot Vacuum Models](#vis-nav-robot-vacuum-models)
  - [EC Air Purifier Models](#ec-air-purifier-models)

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
        if not await client.authenticate():
            otp = input("Enter OTP from email: ")
            await client.complete_authentication(otp)
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
        password: str | None = None,
        auth_token: str | None = None,
        request_timeout: int = 30,
        user_agent: str = "android client"
    ) -> None
```

**Parameters:**
- `email` (str | None): User's email address for authentication
- `password` (str | None): User's password for authentication
- `auth_token` (str | None): Pre-existing authentication token
- `request_timeout` (int): Request timeout in seconds (default: 30)
- `user_agent` (str): User agent string for requests (default: "android client")

### Authentication Methods

#### `authenticate()`
```python
def authenticate(self) -> bool
```
Initiates the authentication process. Returns `True` if authentication completes without OTP, `False` if OTP is required.

**Returns:** `bool` - True if authenticated, False if OTP required

**Raises:**
- `DysonAuthError`: Authentication failed
- `DysonConnectionError`: Network/connection issues

#### `complete_authentication(otp_code: str)`
```python
def complete_authentication(self, otp_code: str) -> None
```
Completes authentication using the OTP code received via email.

**Parameters:**
- `otp_code` (str): One-time password from email

**Raises:**
- `DysonAuthError`: Invalid OTP or authentication failed
- `DysonConnectionError`: Network/connection issues

#### `login_challenge(email: str, password: str)`
```python
def login_challenge(self, email: str, password: str) -> LoginChallenge
```
Low-level method to initiate login challenge (used internally by `authenticate()`).

**Parameters:**
- `email` (str): User's email address
- `password` (str): User's password

**Returns:** `LoginChallenge` object containing challenge details

#### `complete_login(challenge_id: str, otp_code: str, email: str | None = None, password: str | None = None)`
```python
def complete_login(
    self,
    challenge_id: str,
    otp_code: str,
    email: str | None = None,
    password: str | None = None,
) -> LoginInformation
```
Low-level method to complete login with OTP (used internally by `complete_authentication()`).

**Parameters:**
- `challenge_id` (str): Challenge ID from login_challenge response
- `otp_code` (str): One-time password from email
- `email` (str | None): User's email (optional if set in constructor)
- `password` (str | None): User's password (optional if set in constructor)

**Returns:** `LoginInformation` object containing auth token and account details

### Device Management Methods

#### `get_devices()`
```python
def get_devices(self) -> list[DysonDevice]
```
Retrieves all Dyson devices associated with the account.

**Returns:** List of `DysonDevice` objects

**Raises:**
- `DysonAuthError`: Not authenticated or token expired
- `DysonAPIError`: API request failed
- `DysonConnectionError`: Network/connection issues

#### `get_device_by_serial(serial: str)`
```python
def get_device_by_serial(self, serial: str) -> DysonDevice | None
```
Retrieves a specific device by its serial number.

**Parameters:**
- `serial` (str): Device serial number

**Returns:** `DysonDevice` object if found, `None` otherwise

#### `get_device_credentials(device: DysonDevice)`
```python
def get_device_credentials(self, device: DysonDevice) -> dict[str, str]
```
Retrieves MQTT credentials for a specific device.

**Parameters:**
- `device` (DysonDevice): Device object

**Returns:** Dictionary containing MQTT credentials (`username`, `password`, `hostname`)

**Raises:**
- `DysonAuthError`: Not authenticated or token expired
- `DysonAPIError`: API request failed
- `DysonConnectionError`: Network/connection issues

### Vis Nav Robot Vacuum Methods

#### `get_clean_maps(serial_number: str, include_dust_map: bool = True)`
```python
def get_clean_maps(
    self, serial_number: str, include_dust_map: bool = True
) -> list[CleanRecord]
```
Retrieves recent cleaning run history for a Vis Nav robot vacuum.

**Parameters:**
- `serial_number` (str): Device serial number
- `include_dust_map` (bool): When True (default), fetches the aggregated dust-density map blob for each run

**Returns:** List of `CleanRecord` objects, newest first

**Raises:**
- `DysonAuthError`: Not authenticated or token expired
- `DysonAPIError`: API request failed
- `DysonConnectionError`: Network/connection issues

#### `get_persistent_map_metadata(serial_number: str)`
```python
def get_persistent_map_metadata(self, serial_number: str) -> list[PersistentMapMeta]
```
Retrieves the list of saved maps (zone names, IDs, and areas) for a Vis Nav.

**Parameters:**
- `serial_number` (str): Device serial number

**Returns:** List of `PersistentMapMeta` objects — one per stored map

**Raises:**
- `DysonAuthError`: Not authenticated or token expired
- `DysonAPIError`: API request failed
- `DysonConnectionError`: Network/connection issues

#### `get_persistent_map(serial_number: str, map_id: str)`
```python
def get_persistent_map(self, serial_number: str, map_id: str) -> PersistentMap
```
Retrieves the full map record for a single persistent map, including the floor-plan PNG.

**Parameters:**
- `serial_number` (str): Device serial number
- `map_id` (str): Persistent map ID (from `get_persistent_map_metadata`)

**Returns:** `PersistentMap` with presentation image, display orientation, world offset, and zone definitions

**Raises:**
- `DysonAuthError`: Not authenticated or token expired
- `DysonAPIError`: API request failed
- `DysonConnectionError`: Network/connection issues

#### `get_recommended_cleans(serial_number: str)`
```python
def get_recommended_cleans(self, serial_number: str) -> list[RecommendedCleanMap]
```
Retrieves Dyson's per-zone clean recommendations ranked by accumulated dust load.

**Parameters:**
- `serial_number` (str): Device serial number

**Returns:** List of `RecommendedCleanMap` objects (one per persistent map), each containing per-zone `ZonePrediction` entries with `ZoneDustBreakdown` data

**Raises:**
- `DysonAuthError`: Not authenticated or token expired
- `DysonAPIError`: API request failed
- `DysonConnectionError`: Network/connection issues

#### `set_zone_behaviour(serial_number, map_id, zone_id, strategy)`
```python
def set_zone_behaviour(
    self,
    serial_number: str,
    map_id: str,
    zone_id: str,
    strategy: CleaningStrategy | str,
) -> None
```
Sets the per-zone cleaning strategy. Equivalent to changing a zone's behaviour in the MyDyson app. The device applies the override on its next clean.

> **Note:** The API path is `/v1/app/{serial}/{mapId}/zones/{zoneId}/zone-behaviours` — there is no `persistent-maps/` segment in this path.

**Parameters:**
- `serial_number` (str): Device serial number
- `map_id` (str): Persistent map ID
- `zone_id` (str): Zone ID to update
- `strategy` (`CleaningStrategy` | str): Cleaning strategy — `AUTO`, `QUICK`, `QUIET`, or `BOOST`

**Raises:**
- `DysonAuthError`: Not authenticated or token expired
- `DysonAPIError`: API request failed
- `DysonConnectionError`: Network/connection issues

### EC Air Purifier Methods

#### `get_daily_environment_data(serial_number: str, language: str = "en")`
```python
def get_daily_environment_data(
    self, serial_number: str, language: str = "en"
) -> DailyAirQualityData
```
Retrieves today's indoor air-quality history at 15-minute resolution.

**Parameters:**
- `serial_number` (str): Device serial number
- `language` (str): Language code for localised field values (default: `"en"`)

**Returns:** `DailyAirQualityData` with sample series, `start_time`, and `resolution_minutes`

**Raises:**
- `DysonAuthError`: Not authenticated or token expired
- `DysonAPIError`: API request failed
- `DysonConnectionError`: Network/connection issues

#### `get_scheduled_events(serial_number: str, product_type: str | None = None)`
```python
def get_scheduled_events(
    self, serial_number: str, product_type: str | None = None
) -> ScheduledEventsData
```
Retrieves the MyDyson-app automation schedule for a device.

**Parameters:**
- `serial_number` (str): Device serial number
- `product_type` (str | None): Device product-type code (e.g. `"438K"`). Required by the server to return the correct schedule schema; omit only if the product type is unknown.

**Returns:** `ScheduledEventsData` with `schedule_enabled` flag and list of `ScheduledEvent` objects

**Raises:**
- `DysonAuthError`: Not authenticated or token expired
- `DysonAPIError`: API request failed
- `DysonConnectionError`: Network/connection issues

### Context Manager Support

```python
with DysonClient("user@example.com", "password") as client:
    if not client.authenticate():
        otp = input("Enter OTP: ")
        client.complete_authentication(otp)
    devices = client.get_devices()
# Client is automatically cleaned up
```

## Asynchronous Client (AsyncDysonClient)

### Constructor

```python
class AsyncDysonClient:
    def __init__(
        self,
        email: str | None = None,
        password: str | None = None,
        auth_token: str | None = None,
        request_timeout: int = 30,
        user_agent: str = "android client"
    ) -> None
```

**Parameters:** Same as `DysonClient`

### Authentication Methods

#### `authenticate()`
```python
async def authenticate(self) -> bool
```
Async version of authenticate method.

**Returns:** `bool` - True if authenticated, False if OTP required

#### `complete_authentication(otp_code: str)`
```python
async def complete_authentication(self, otp_code: str) -> None
```
Async version of complete_authentication method.

**Parameters:**
- `otp_code` (str): One-time password from email

#### `login_challenge(email: str, password: str)`
```python
async def login_challenge(self, email: str, password: str) -> LoginChallenge
```
Async version of login_challenge method.

#### `complete_login(challenge_id: str, otp_code: str, email: str | None = None, password: str | None = None)`
```python
async def complete_login(
    self,
    challenge_id: str,
    otp_code: str,
    email: str | None = None,
    password: str | None = None,
) -> LoginInformation
```
Async version of complete_login method.

### Device Management Methods

#### `get_devices()`
```python
async def get_devices(self) -> list[DysonDevice]
```
Async version of get_devices method.

#### `get_device_by_serial(serial: str)`
```python
async def get_device_by_serial(self, serial: str) -> DysonDevice | None
```
Async version of get_device_by_serial method.

#### `get_device_credentials(device: DysonDevice)`
```python
async def get_device_credentials(self, device: DysonDevice) -> dict[str, str]
```
Async version of get_device_credentials method.

### Vis Nav Robot Vacuum Methods

#### `get_clean_maps(serial_number: str, include_dust_map: bool = True)`
```python
async def get_clean_maps(
    self, serial_number: str, include_dust_map: bool = True
) -> list[CleanRecord]
```
Async version of `get_clean_maps`. See sync client for full parameter/return documentation.

#### `get_persistent_map_metadata(serial_number: str)`
```python
async def get_persistent_map_metadata(self, serial_number: str) -> list[PersistentMapMeta]
```
Async version of `get_persistent_map_metadata`.

#### `get_persistent_map(serial_number: str, map_id: str)`
```python
async def get_persistent_map(self, serial_number: str, map_id: str) -> PersistentMap
```
Async version of `get_persistent_map`.

#### `get_recommended_cleans(serial_number: str)`
```python
async def get_recommended_cleans(self, serial_number: str) -> list[RecommendedCleanMap]
```
Async version of `get_recommended_cleans`.

#### `set_zone_behaviour(serial_number, map_id, zone_id, strategy)`
```python
async def set_zone_behaviour(
    self,
    serial_number: str,
    map_id: str,
    zone_id: str,
    strategy: CleaningStrategy | str,
) -> None
```
Async version of `set_zone_behaviour`.

### EC Air Purifier Methods

#### `get_daily_environment_data(serial_number: str, language: str = "en")`
```python
async def get_daily_environment_data(
    self, serial_number: str, language: str = "en"
) -> DailyAirQualityData
```
Async version of `get_daily_environment_data`.

#### `get_scheduled_events(serial_number: str, product_type: str | None = None)`
```python
async def get_scheduled_events(
    self, serial_number: str, product_type: str | None = None
) -> ScheduledEventsData
```
Async version of `get_scheduled_events`.

### Resource Management

#### `close()`
```python
async def close(self) -> None
```
Properly closes the HTTP client session. Always call this when done with the client, or use async context manager.

### Async Context Manager Support

```python
async with AsyncDysonClient("user@example.com", "password") as client:
    if not await client.authenticate():
        otp = input("Enter OTP: ")
        await client.complete_authentication(otp)
    devices = await client.get_devices()
# Client is automatically closed
```

## Method Comparison Table

| Feature | Synchronous | Asynchronous | Notes |
|---------|-------------|--------------|-------|
| Constructor | `DysonClient()` | `AsyncDysonClient()` | Same parameters |
| Authentication | `authenticate()` | `await authenticate()` | Returns bool |
| Complete Auth | `complete_authentication()` | `await complete_authentication()` | Takes OTP code |
| Get Devices | `get_devices()` | `await get_devices()` | Returns device list |
| Get Device | `get_device_by_serial()` | `await get_device_by_serial()` | Find by serial |
| Get Credentials | `get_device_credentials()` | `await get_device_credentials()` | MQTT credentials |
| **Clean Maps** | `get_clean_maps()` | `await get_clean_maps()` | Vis Nav history |
| **Map Metadata** | `get_persistent_map_metadata()` | `await get_persistent_map_metadata()` | Zone names/IDs |
| **Full Map** | `get_persistent_map()` | `await get_persistent_map()` | Floor-plan PNG |
| **Recommended** | `get_recommended_cleans()` | `await get_recommended_cleans()` | Dust predictions |
| **Zone Strategy** | `set_zone_behaviour()` | `await set_zone_behaviour()` | Vis Nav zone config |
| **AQI History** | `get_daily_environment_data()` | `await get_daily_environment_data()` | EC purifier |
| **Schedule** | `get_scheduled_events()` | `await get_scheduled_events()` | Automation schedule |
| Context Manager | `with client:` | `async with client:` | Auto cleanup |
| Resource Cleanup | Automatic | `await client.close()` | Manual or context manager |

## Authentication Flow

The library uses a two-step authentication process:

1. **Initial Authentication**: Call `authenticate()` with email/password
   - If MFA is disabled: Returns `True`, authentication complete
   - If MFA is enabled: Returns `False`, OTP sent to email

2. **OTP Completion**: If `authenticate()` returns `False`, call `complete_authentication(otp)`
   - Provide the OTP code received via email
   - Authentication completes successfully

### Example Flow
```python
# Step 1: Initial authentication
client = DysonClient("user@example.com", "password")
if client.authenticate():
    print("Authentication complete!")
else:
    # Step 2: OTP required
    otp = input("Enter OTP from email: ")
    client.complete_authentication(otp)
    print("Authentication complete with OTP!")

# Now authenticated - can make API calls
devices = client.get_devices()
```

### Legacy Single-Step Authentication
```python
# Deprecated: Single-step with OTP (if known)
client = DysonClient("user@example.com", "password")
login_info = client.complete_login(challenge_id, "123456")
```

## Error Handling

The library defines custom exceptions for different error scenarios:

### Exception Hierarchy
```
DysonError (base)
├── DysonAuthError (authentication failures)
├── DysonAPIError (API response errors)
└── DysonConnectionError (network/connection issues)
```

### Exception Details

#### `DysonError`
Base exception class for all Dyson-related errors.

#### `DysonAuthError`
Raised when authentication fails:
- Invalid credentials
- Invalid OTP code
- Token expired
- Account locked

#### `DysonAPIError`
Raised when API requests fail:
- Invalid API response format
- Server errors (5xx)
- Rate limiting
- Invalid device serial

#### `DysonConnectionError`
Raised when network issues occur:
- Connection timeout
- DNS resolution failure
- SSL/TLS errors
- Network unreachable

### Error Handling Example
```python
from libdyson_rest import DysonClient, DysonAuthError, DysonAPIError, DysonConnectionError

try:
    client = DysonClient("user@example.com", "password")
    if not client.authenticate():
        otp = input("Enter OTP: ")
        client.complete_authentication(otp)
    
    devices = client.get_devices()
    
except DysonAuthError as e:
    print(f"Authentication failed: {e}")
except DysonAPIError as e:
    print(f"API error: {e}")
except DysonConnectionError as e:
    print(f"Connection error: {e}")
```

## Data Models

### DysonDevice

Represents a Dyson device with the following attributes:

```python
@dataclass
class DysonDevice:
    serial: str           # Device serial number
    name: str            # User-assigned device name
    product_type: str    # Product identifier (e.g., "520")
    version: str         # Firmware version
    auto_update: bool    # Auto-update enabled
    new_version_available: bool  # Firmware update available
    category: str        # Device category (e.g., "purifier")
    
    # Optional attributes (may be None)
    local_credentials: dict[str, str] | None  # Local MQTT credentials
    connection_type: str | None               # Connection type
    mqtt_server: str | None                   # MQTT server hostname
```

### LoginChallenge

Represents a login challenge response:

```python
@dataclass
class LoginChallenge:
    challenge_id: str    # Challenge identifier for OTP completion
    user_id: str        # User account identifier
```

### LoginInformation

Represents completed login information:

```python
@dataclass  
class LoginInformation:
    token: str          # Authentication token
    account: dict       # Account details
    challenge_id: str   # Challenge identifier used
```

### Usage Examples with Data Models

```python
# Working with devices
devices = client.get_devices()
for device in devices:
    print(f"Device: {device.name}")
    print(f"Serial: {device.serial}")
    print(f"Type: {device.product_type}")
    print(f"Category: {device.category}")
    
    if device.new_version_available:
        print("⚠️  Firmware update available")
    
    # Get MQTT credentials for device
    credentials = client.get_device_credentials(device)
    print(f"MQTT Host: {credentials['hostname']}")

# Find specific device
device = client.get_device_by_serial("ABC-DEF-123")
if device:
    print(f"Found: {device.name}")
else:
    print("Device not found")
```

### Vis Nav Robot Vacuum Models

#### `CleanRecord`
A single cleaning run, including timeline, dust map, and cleaning programme.

```python
@dataclass
class CleanRecord:
    start_time: datetime | None
    end_time: datetime | None
    timeline: list[CleanTimelineEvent]
    dust_map: DustMapData | None        # Aggregated dust-density grid
    clean_map_position: CleanMapPosition | None  # World origin of dust map
    cleaning_programme: CleaningProgramme | None # Zone-clean config used
    footprint: CleanedFootprint | None           # Cleaned area + floor-plan crop
    raw: dict                                    # Full raw API response

    @property
    def is_zone_clean(self) -> bool: ...
```

#### `CleaningStrategy` (Enum)
Per-zone cleaning intensity used with `set_zone_behaviour()`:

| Value | Description |
|-------|-------------|
| `AUTO` | Dyson-selected intensity |
| `QUICK` | Fast single pass |
| `QUIET` | Low-noise mode |
| `BOOST` | Intensive multi-pass |

#### `PersistentMapMeta`
Metadata about a stored floor map, including its zones.

```python
@dataclass
class PersistentMapMeta:
    id: str
    name: str | None
    zones: list[ZoneMeta]

    def zone_by_id(self, zone_id: str) -> ZoneMeta | None: ...
    def zone_by_name(self, name: str) -> ZoneMeta | None: ...
```

#### `ZoneMeta`
```python
@dataclass
class ZoneMeta:
    id: str
    name: str | None
    icon: str | None
    area: float | None   # Zone area in m²
```

#### `PersistentMap`
Full map record including presentation image and zone definitions.

```python
@dataclass
class PersistentMap:
    id: str
    offset_x: float | None     # World-mm X origin
    offset_y: float | None     # World-mm Y origin
    display_orientation: int   # Degrees rotation for display
    presentation_map_data: str | None  # Base64-encoded floor-plan PNG
    zones_definition: dict | None
    zones: list[ZoneMeta]
```

#### `RecommendedCleanMap`
```python
@dataclass
class RecommendedCleanMap:
    persistent_map_id: str
    zone_predictions: list[ZonePrediction]

    def sorted_by_dust(self) -> list[ZonePrediction]: ...
```

#### `ZonePrediction`
```python
@dataclass
class ZonePrediction:
    zone_id: str
    dust: ZoneDustBreakdown
```

#### `ZoneDustBreakdown`
Per-particle-class dust load (milligrams).

```python
@dataclass
class ZoneDustBreakdown:
    extra_fine: float
    fine: float
    medium: float
    large: float
    other: float
    total: float   # Sum of all classes
    raw: list      # Original API array
```

#### `DustMapData`
Aggregated dust-density grid returned with each clean record.

```python
@dataclass
class DustMapData:
    width: int
    height: int
    resolution: float              # mm per pixel
    dust_data: list[list[float]]   # 2-D grid, values 0–1 (divided by scaleFactor)
```

### EC Air Purifier Models

#### `DailyAirQualityData`
```python
@dataclass
class DailyAirQualityData:
    start_time: datetime | None
    resolution_minutes: int           # Typically 15
    samples: list[float | None]       # AQI values; None = no reading

    @property
    def latest_sample(self) -> float | None: ...
    @property
    def min_sample(self) -> float | None: ...
    @property
    def max_sample(self) -> float | None: ...
```

#### `ScheduledEventsData`
```python
@dataclass
class ScheduledEventsData:
    schedule_enabled: bool
    events: list[ScheduledEvent]

    @property
    def active_events(self) -> list[ScheduledEvent]: ...
```

#### `ScheduledEvent`
```python
@dataclass
class ScheduledEvent:
    enabled: bool
    days: list[int]       # 0 = Monday … 6 = Sunday
    start_time: str | None  # "HH:MM" local time
    raw: dict
```

## Migration from v0.6.x

If upgrading from version 0.6.x, note the following changes:

### Authentication Changes
- **Old (v0.6.x)**: Single `authenticate(otp)` method
- **New (v0.7.0)**: Two-step `authenticate()` → `complete_authentication(otp)`

```python
# Old v0.6.x approach
client = DysonClient("user@example.com", "password")
client.authenticate("123456")  # OTP required upfront

# New v0.7.0 approach
client = DysonClient("user@example.com", "password")
if not client.authenticate():  # Try without OTP first
    otp = input("Enter OTP: ")
    client.complete_authentication(otp)
```

### Async Client Changes
- **New in v0.7.0**: Full async support with `AsyncDysonClient`
- SSL blocking issues resolved with lazy HTTP client initialization
- Proper async context manager support

### API Endpoint Updates
- Updated to use latest Dyson API endpoints (/v3/manifest)
- Better error handling and validation
- Enhanced device metadata support

---

This documentation covers the complete API surface for both synchronous and asynchronous clients. For additional examples and troubleshooting guides, see the `examples/` directory in the repository.

asyncio.run(main())
