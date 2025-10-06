#!/usr/bin/env python3
"""
Test connectivity to different Dyson endpoints to verify which ones work.
"""

import asyncio
import logging
import sys

from libdyson_rest import AsyncDysonClient
from libdyson_rest.utils import get_api_hostname

# Setup debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

# Enable debug logging for our library
logging.getLogger("libdyson_rest").setLevel(logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.INFO)  # Reduce HTTP noise for this test


async def test_endpoint_connectivity() -> None:
    """Test connectivity to different Dyson API endpoints."""
    print("🌐 Testing Dyson API Endpoint Connectivity")
    print("=" * 60)

    test_endpoints = [
        ("US (Default)", "US", get_api_hostname("US")),
        ("Australia", "AU", get_api_hostname("AU")),
        ("New Zealand", "NZ", get_api_hostname("NZ")),
        ("China", "CN", get_api_hostname("CN")),
    ]

    results = []

    for name, country, endpoint in test_endpoints:
        print(f"\n🔍 Testing {name}: {endpoint}")

        try:
            async with AsyncDysonClient(
                email="test@example.com",
                password="fake_password",
                country=country,
                culture="en-US",
            ) as client:
                await client.provision()
                results.append((name, endpoint, "✅ Connected successfully"))
        except Exception as e:
            error_type = type(e).__name__
            if "ConnectError" in str(e) or "EndOfStream" in str(e):
                results.append((name, endpoint, f"❌ Connection failed: {error_type}"))
            elif "HTTPStatusError" in str(e) or "status" in str(e).lower():
                results.append(
                    (name, endpoint, f"🟡 Connected but HTTP error: {error_type}")
                )
            else:
                results.append((name, endpoint, f"❓ Other error: {error_type}"))

    print("\n" + "=" * 60)
    print("📊 CONNECTIVITY SUMMARY:")
    print("=" * 60)

    for name, endpoint, status in results:
        print(f"{name:15} | {endpoint:35} | {status}")

    print("\n💡 Recommendations:")
    print("   - ✅ = Endpoint is accessible and working")
    print("   - 🟡 = Endpoint is accessible but may have auth issues")
    print("   - ❌ = Endpoint is not accessible or doesn't exist")
    print("   - ❓ = Unexpected error occurred")


if __name__ == "__main__":
    asyncio.run(test_endpoint_connectivity())
