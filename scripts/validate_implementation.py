#!/usr/bin/env python3
"""
Validation script for libdyson-rest async implementation.

This script validates that both sync and async clients work correctly.
"""

import asyncio
import sys


def test_sync_client():
    """Test that the sync client imports and initializes correctly."""
    print("🔄 Testing sync client...")

    try:
        from libdyson_rest import DysonClient

        # Test basic initialization
        client = DysonClient()
        assert client.country == "US"
        assert client.culture == "en-US"
        assert client.timeout == 30
        assert client.auth_token is None

        # Test custom initialization
        client = DysonClient(
            email="test@example.com",
            password="test_password",
            country="UK",
            culture="en-GB",
            timeout=60,
        )
        assert client.email == "test@example.com"
        assert client.password == "test_password"
        assert client.country == "UK"
        assert client.culture == "en-GB"
        assert client.timeout == 60

        # Test context manager
        with DysonClient() as ctx_client:
            assert ctx_client is not None

        client.close()
        print("✅ Sync client tests passed")
        return True

    except Exception as e:
        print(f"❌ Sync client test failed: {e}")
        return False


async def test_async_client():
    """Test that the async client imports and works correctly."""
    print("🔄 Testing async client...")

    try:
        from libdyson_rest import AsyncDysonClient

        # Test basic initialization
        client = AsyncDysonClient()
        assert client.country == "US"
        assert client.culture == "en-US"
        assert client.timeout == 30
        assert client.auth_token is None

        # Test custom initialization
        client = AsyncDysonClient(
            email="test@example.com",
            password="test_password",
            country="UK",
            culture="en-GB",
            timeout=60,
        )
        assert client.email == "test@example.com"
        assert client.password == "test_password"
        assert client.country == "UK"
        assert client.culture == "en-GB"
        assert client.timeout == 60

        await client.close()

        # Test async context manager
        async with AsyncDysonClient() as ctx_client:
            assert ctx_client is not None

        print("✅ Async client tests passed")
        return True

    except ImportError as e:
        print(f"⚠️  Async client not available (missing httpx): {e}")
        return None  # Not a failure, just not available
    except Exception as e:
        print(f"❌ Async client test failed: {e}")
        return False


def test_exports():
    """Test that the expected exports are available."""
    print("🔄 Testing module exports...")

    try:
        import libdyson_rest as dyson

        # Test that sync client is always available
        assert hasattr(dyson, "DysonClient")
        assert hasattr(dyson, "DysonAPIError")
        assert hasattr(dyson, "DysonAuthError")
        assert hasattr(dyson, "DysonConnectionError")

        # Test __all__ contents
        all_exports = dyson.__all__
        assert "DysonClient" in all_exports
        assert (
            "AsyncDysonClient" in all_exports
        )  # Should be in __all__ even if not available
        assert "DysonAPIError" in all_exports

        print("✅ Export tests passed")
        return True

    except Exception as e:
        print(f"❌ Export test failed: {e}")
        return False


def test_error_handling():
    """Test that error handling works correctly."""
    print("🔄 Testing error handling...")

    try:
        from libdyson_rest import DysonAPIError, DysonAuthError, DysonClient

        # Test that errors are raised correctly
        client = DysonClient()

        try:
            client.get_devices()  # Should fail - not authenticated
            print("❌ Expected DysonAuthError was not raised")
            return False
        except DysonAuthError:
            pass  # Expected

        try:
            client.begin_login()  # Should fail - no email
            print("❌ Expected DysonAPIError was not raised")
            return False
        except DysonAPIError as e:
            # This is expected - the client needs an email to begin login
            if "Email address is required" in str(e):
                pass  # Expected
            else:
                print(f"❌ Unexpected error message: {e}")
                return False

        client.close()
        print("✅ Error handling tests passed")
        return True

    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


async def main():
    """Run all validation tests."""
    print("🌟 Starting libdyson-rest validation tests")
    print("=" * 50)

    tests = [
        ("Sync Client", test_sync_client, False),
        ("Async Client", test_async_client, True),
        ("Module Exports", test_exports, False),
        ("Error Handling", test_error_handling, False),
    ]

    results = []

    for name, test_func, is_async in tests:
        print(f"\n📋 Running: {name}")
        print("-" * 30)

        try:
            if is_async:
                result = await test_func()
            else:
                result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Test {name} crashed: {e}")
            results.append((name, False))

    print("\n📊 Results Summary")
    print("=" * 50)

    passed = 0
    failed = 0
    skipped = 0

    for name, result in results:
        if result is True:
            print(f"✅ {name}: PASSED")
            passed += 1
        elif result is False:
            print(f"❌ {name}: FAILED")
            failed += 1
        elif result is None:
            print(f"⚠️  {name}: SKIPPED (dependency missing)")
            skipped += 1

    print(f"\nTotals: {passed} passed, {failed} failed, {skipped} skipped")

    if failed > 0:
        print("❌ Some tests failed!")
        return 1
    else:
        print("🎉 All available tests passed!")
        return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
