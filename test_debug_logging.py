#!/usr/bin/env python3
"""
Quick test script to verify debug logging is working.
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
logging.getLogger("httpx").setLevel(logging.DEBUG)
logging.getLogger("requests").setLevel(logging.DEBUG)


async def test_debug_logging() -> None:
    """Test that debug logging is working properly."""
    print("🔍 Testing Debug Logging")
    print("=" * 50)

    # Test regional endpoint resolution
    test_countries = ["US", "AU", "NZ", "CN", "GB"]
    print("\n🌐 Regional Endpoint Resolution:")
    for country in test_countries:
        endpoint = get_api_hostname(country)
        print(f"   {country}: {endpoint}")

    print("\n📡 Testing HTTP Debug Logging with API Call:")
    print("   (This will fail authentication but show HTTP debug info)")

    # Test with a client to see HTTP debug logging
    async with AsyncDysonClient(
        email="test@example.com",
        password="fake_password",
        country="AU",  # Test AU endpoint
        culture="en-AU",
    ) as client:
        try:
            print(f"\n🌐 Using endpoint: {get_api_hostname('AU')}")
            # This will show the HTTP request/response in debug logs
            await client.provision()
        except Exception as e:
            print(f"Expected error (no real credentials): {e}")
            print("✅ Debug logging test complete!")


if __name__ == "__main__":
    asyncio.run(test_debug_logging())
