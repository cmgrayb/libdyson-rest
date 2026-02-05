# Mobile Authentication Quick Reference

## TL;DR

Mobile authentication is available for **China (CN) region only**. Use SMS OTP instead of email OTP.

```python
from libdyson_rest import DysonClient

# Setup
client = DysonClient(
    email="+8613800000000",  # Mobile with country code
    password="your_password",
    country="CN"
)

# Authenticate
client.provision()
challenge = client.begin_login_mobile("+8613800000000")
otp = input("Enter SMS OTP: ")
login = client.complete_login_mobile(challenge.challenge_id, otp, "+8613800000000")

# Use API
devices = client.get_devices()
```

## Key Points

| Aspect | Details |
|--------|---------|
| **Region** | China (CN) only |
| **Format** | `+8613800000000` (must include country code) |
| **OTP** | Delivered via SMS |
| **Server** | `appapi.cp.dyson.cn` |
| **Methods** | `get_user_status_mobile()`, `begin_login_mobile()`, `complete_login_mobile()` |

## Quick Comparison

### Email Auth (All Regions)
```python
client = DysonClient(email="user@example.com", password="pwd")
client.provision()
challenge = client.begin_login()
login = client.complete_login(challenge.challenge_id, email_otp)
```

### Mobile Auth (CN Only)
```python
client = DysonClient(email="+8613800000000", password="pwd", country="CN")
client.provision()
challenge = client.begin_login_mobile("+8613800000000")
login = client.complete_login_mobile(challenge.challenge_id, sms_otp, "+8613800000000")
```

## Common Errors

```python
# ✗ Missing country code
begin_login_mobile("13800000000")  # Error!

# ✓ With country code
begin_login_mobile("+8613800000000")  # Works!

# ✗ Wrong region
DysonClient(country="US").begin_login_mobile(...)  # Error!

# ✓ CN region
DysonClient(country="CN").begin_login_mobile(...)  # Works!
```

## Full Documentation

See [MOBILE_AUTHENTICATION.md](MOBILE_AUTHENTICATION.md) for complete details, error handling, and async examples.
