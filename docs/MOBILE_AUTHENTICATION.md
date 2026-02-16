# Mobile Authentication for China Region

## Overview

As of version 0.12.0, libdyson-rest supports mobile phone authentication for users in the China (CN) region. This authentication method uses SMS OTP codes instead of email OTP codes and is available exclusively on the China API server (`appapi.cp.dyson.cn`).

## When to Use Mobile Authentication

**Use mobile authentication when:**
- Your users are in the China (CN) region
- Their Dyson accounts are registered with mobile phone numbers
- They prefer SMS-based verification over email

**Use email authentication when:**
- Your users are in any other region (US, UK, AU, etc.)
- Their accounts are registered with email addresses
- You need global compatibility

## Key Differences from Email Authentication

| Feature | Email Authentication | Mobile Authentication |
|---------|---------------------|----------------------|
| **Available Regions** | All regions | China (CN) only |
| **API Server** | `appapi.cp.dyson.com` | `appapi.cp.dyson.cn` |
| **OTP Delivery** | Email | SMS |
| **Identifier Format** | `user@example.com` | `+8613800000000` (with country code) |
| **API Endpoints** | `/v3/userregistration/email/*` | `/v3/userregistration/mobile/*` |
| **Methods** | `get_user_status()`, `begin_login()`, `complete_login()` | `get_user_status_mobile()`, `begin_login_mobile()`, `complete_login_mobile()` |

## Requirements

1. **Mobile Number Format**: Must include country code prefix (e.g., `+8613800000000`)
2. **Region Setting**: Client must be configured with `country="CN"`
3. **Account Registration**: User's Dyson account must be registered with a mobile phone number

## Usage Examples

### Synchronous Client

```python
from libdyson_rest import DysonClient

# Initialize client for CN region
client = DysonClient(
    email="+8613800000000",  # Mobile number with country code
    password="your_password",
    country="CN",
    culture="zh-CN"
)

try:
    # Step 1: Provision API access (required first call)
    client.provision()
    
    # Step 2: Check user status (optional)
    user_status = client.get_user_status_mobile("+8613800000000")
    print(f"Account Status: {user_status.account_status.value}")
    
    # Step 3: Begin login - triggers SMS OTP
    challenge = client.begin_login_mobile("+8613800000000")
    print(f"SMS sent! Challenge ID: {challenge.challenge_id}")
    
    # Step 4: Get OTP code from user
    otp_code = input("Enter the OTP code from SMS: ")
    
    # Step 5: Complete login with OTP
    login_info = client.complete_login_mobile(
        challenge_id=challenge.challenge_id,
        otp_code=otp_code,
        mobile="+8613800000000"
    )
    
    print(f"✓ Authenticated! Account: {login_info.account}")
    print(f"✓ Token: {login_info.token[:20]}...")
    
    # Now you can use authenticated API calls
    devices = client.get_devices()
    for device in devices:
        print(f"Device: {device.name} ({device.serial})")
        
finally:
    client.close()
```

### Asynchronous Client

```python
import asyncio
from libdyson_rest import AsyncDysonClient

async def authenticate_mobile():
    """Example async mobile authentication."""
    async with AsyncDysonClient(
        email="+8613800000000",
        password="your_password",
        country="CN",
        culture="zh-CN"
    ) as client:
        # Provision
        await client.provision()
        
        # Check user status
        user_status = await client.get_user_status_mobile("+8613800000000")
        print(f"Account Status: {user_status.account_status.value}")
        
        # Begin login - SMS sent
        challenge = await client.begin_login_mobile("+8613800000000")
        print(f"Challenge ID: {challenge.challenge_id}")
        
        # Get OTP from user (in real async app, use async input method)
        otp_code = input("Enter OTP from SMS: ")
        
        # Complete login
        login_info = await client.complete_login_mobile(
            challenge_id=challenge.challenge_id,
            otp_code=otp_code,
            mobile="+8613800000000"
        )
        
        print(f"✓ Authenticated! Token: {login_info.token[:20]}...")
        
        # Use authenticated client
        devices = await client.get_devices()
        for device in devices:
            print(f"Device: {device.name}")

# Run the async function
asyncio.run(authenticate_mobile())
```

### Using Environment Variables

```python
import os
from libdyson_rest import DysonClient

# Set environment variables
# export DYSON_MOBILE='+8613800000000'
# export DYSON_PASSWORD='your_password'

mobile = os.getenv("DYSON_MOBILE")
password = os.getenv("DYSON_PASSWORD")

client = DysonClient(
    email=mobile,
    password=password,
    country="CN",
    culture="zh-CN"
)
```

## API Methods

### `get_user_status_mobile(mobile: str | None = None) -> UserStatus`

Check the status of a user account using mobile number.

**Parameters:**
- `mobile` (str, optional): Mobile number with country code (e.g., `+8613800000000`). If None, uses instance email.

**Returns:**
- `UserStatus`: Object containing account status and authentication method

**Raises:**
- `DysonAPIError`: If no mobile number is available
- `DysonConnectionError`: If connection fails
- `DysonAPIError`: If API response is invalid

### `begin_login_mobile(mobile: str | None = None) -> LoginChallenge`

Begin the login process by requesting an OTP challenge via SMS.

**Parameters:**
- `mobile` (str, optional): Mobile number with country code. If None, uses instance email.

**Returns:**
- `LoginChallenge`: Object containing challenge ID for completing login

**Raises:**
- `DysonAPIError`: If no mobile number is available
- `DysonAuthError`: If mobile number is invalid or not authorized (401)
- `DysonAuthError`: If bad request format (400)
- `DysonConnectionError`: If connection fails

**Side Effects:**
- Sends SMS OTP code to the mobile number

### `complete_login_mobile(challenge_id: str, otp_code: str, mobile: str | None = None) -> LoginInformation`

Complete the login process using the OTP code received via SMS.

**Parameters:**
- `challenge_id` (str): Challenge ID from `begin_login_mobile()`
- `otp_code` (str): OTP code received via SMS
- `mobile` (str, optional): Mobile number with country code. If None, uses instance email.

**Returns:**
- `LoginInformation`: Object containing authentication token and account details

**Raises:**
- `DysonAuthError`: If mobile number is missing or OTP is invalid
- `DysonAuthError`: If OTP code is invalid (401)
- `DysonAuthError`: If bad request parameters (400)
- `DysonConnectionError`: If connection fails

**Side Effects:**
- Sets authentication token in client
- Updates session headers with Bearer token
- Sets `account_id` on client instance

## Error Handling

```python
from libdyson_rest import DysonClient
from libdyson_rest.exceptions import (
    DysonAPIError,
    DysonAuthError,
    DysonConnectionError
)

client = DysonClient(
    email="+8613800000000",
    password="password",
    country="CN"
)

try:
    client.provision()
    challenge = client.begin_login_mobile("+8613800000000")
    otp = input("Enter OTP: ")
    login_info = client.complete_login_mobile(
        challenge.challenge_id,
        otp,
        "+8613800000000"
    )
    
except DysonAuthError as e:
    # Authentication errors: invalid credentials, wrong OTP, etc.
    print(f"Authentication failed: {e}")
    print("Common causes:")
    print("  - Incorrect mobile number")
    print("  - Invalid or expired OTP code")
    print("  - Mobile number not registered on CN server")
    print("  - Mobile number format missing country code")
    
except DysonConnectionError as e:
    # Network/connection errors
    print(f"Connection failed: {e}")
    print("Common causes:")
    print("  - Network connectivity issues")
    print("  - Dyson API server unavailable")
    print("  - Firewall blocking connections")
    
except DysonAPIError as e:
    # API-related errors
    print(f"API error: {e}")
    print("Common causes:")
    print("  - Invalid API response format")
    print("  - Missing required parameters")
    print("  - API endpoint changed")
    
finally:
    client.close()
```

## Common Issues and Solutions

### Issue: "Mobile number is required"
**Solution:** Ensure you're passing the mobile number with country code:
```python
# ✗ Wrong
client.begin_login_mobile()  # No mobile provided

# ✓ Correct
client.begin_login_mobile("+8613800000000")
```

### Issue: "Bad request to Dyson API (400): Check mobile format"
**Solution:** Mobile number must include country code with `+` prefix:
```python
# ✗ Wrong
client.begin_login_mobile("13800000000")  # Missing country code

# ✓ Correct
client.begin_login_mobile("+8613800000000")  # With +86 country code
```

### Issue: "Invalid mobile number or not authorized"
**Solution:** Verify:
1. Mobile number is registered with Dyson in CN region
2. Mobile number format is correct
3. Account exists and is active
4. Using CN server (`country="CN"`)

### Issue: "Invalid credentials or OTP code"
**Solution:**
1. Check OTP code was entered correctly (no spaces)
2. OTP codes expire quickly - request a new one if needed
3. Ensure you're using the latest OTP (not an old one)

## Migration from Email to Mobile Authentication (CN Users)

If you have existing code using email authentication for CN users, here's how to migrate:

**Before (Email):**
```python
client = DysonClient(email="user@example.com", password="pwd", country="CN")
client.provision()
challenge = client.begin_login()
login_info = client.complete_login(challenge.challenge_id, otp_code)
```

**After (Mobile):**
```python
client = DysonClient(email="+8613800000000", password="pwd", country="CN")
client.provision()
challenge = client.begin_login_mobile("+8613800000000")
login_info = client.complete_login_mobile(
    challenge.challenge_id, 
    otp_code, 
    "+8613800000000"
)
```

**Key Changes:**
1. Replace email with mobile number (with country code)
2. Use `*_mobile()` methods instead of regular methods
3. Pass mobile number to methods (or set as instance email)
4. OTP will arrive via SMS instead of email

## Testing

For testing and development, see:
- **Examples**: `examples/mobile_auth_example.py` (sync) and `examples/async_mobile_auth_example.py` (async)
- **Unit Tests**: `tests/unit/test_client.py::TestDysonClientMobileAuth`
- **Integration Tests**: Set `DYSON_MOBILE` and `DYSON_PASSWORD` environment variables

## API Compatibility

- **Minimum Version**: libdyson-rest 0.12.0
- **Python Version**: 3.10+
- **Required Dependencies**: No additional dependencies beyond standard libdyson-rest requirements

## Support

- **Full Documentation**: See `docs/API.md` for complete API reference
- **Examples**: See `examples/` directory for working code samples
- **Troubleshooting**: See `examples/TROUBLESHOOTING.md` for debugging tips
- **Issues**: Report issues at https://github.com/cmgrayb/libdyson-rest/issues

## Notes

- Mobile authentication is **only available on the China (CN) region server**
- Attempting to use mobile authentication methods on other regions will fail
- Mobile numbers **must include the country code** (e.g., `+86` for China)
- The authentication flow is identical to email auth, just using different endpoints
- Both sync (`DysonClient`) and async (`AsyncDysonClient`) clients are supported
- After successful authentication, all other API methods work identically to email auth
