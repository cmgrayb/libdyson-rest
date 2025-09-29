#!/usr/bin/env python3
"""
Test the debug logging functionality with a simple example.
"""

import logging
import sys

from libdyson_rest import DysonClient
from libdyson_rest.exceptions import DysonAPIError, DysonConnectionError


def test_debug_logging():
    """Test debug logging with fake credentials."""
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )

    logging.getLogger("libdyson_rest").setLevel(logging.DEBUG)

    print("🔍 Testing debug logging with fake credentials...")
    print("🚫 This will fail authentication, but shows debug output")
    print()

    try:
        # Test with debug=True (detailed HTTP logging)
        print("=== With debug=True (detailed HTTP logging) ===")
        with DysonClient(
            email="fake@example.com",
            password="fake_password",
            country="US",
            debug=True,  # Enable detailed HTTP debug logging
        ) as client:
            version = client.provision()
            print(f"✅ API Version: {version}")

    except (DysonConnectionError, DysonAPIError) as e:
        print(f"Expected error (fake credentials): {e}")

    print()

    try:
        # Test with debug=False (minimal logging)
        print("=== With debug=False (minimal logging) ===")
        with DysonClient(
            email="fake@example.com",
            password="fake_password",
            country="CN",  # Test China endpoint
            debug=False,  # No detailed HTTP logging
        ) as client:
            version = client.provision()
            print(f"✅ API Version: {version}")

    except (DysonConnectionError, DysonAPIError) as e:
        print(f"Expected error (fake credentials): {e}")


if __name__ == "__main__":
    test_debug_logging()
