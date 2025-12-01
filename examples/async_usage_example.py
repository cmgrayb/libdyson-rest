"""
Example usage of libdyson-rest async client library.

This example demonstrates how to use the async client to interact with Dyson devices.
This is particularly useful for Home Assistant integrations and other async
environments.

The Dyson API uses a two-step authentication process:
1. Begin login to get a challenge ID
2. Complete login with OTP code (usually sent via email)
"""

import asyncio
import logging
import os

from libdyson_rest import AsyncDysonClient, DysonAuthError, DysonConnectionError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def basic_async_example() -> None:
    """Basic asynchronous usage example with two-step authentication."""
    logger.info("🚀 Starting basic async example")

    # Get credentials from environment or use defaults for testing
    email = os.getenv("DYSON_EMAIL", "your@email.com")
    password = os.getenv("DYSON_PASSWORD", "your_password")
    country = os.getenv("DYSON_COUNTRY", "US")
    culture = os.getenv("DYSON_CULTURE", "en-US")

    async with AsyncDysonClient(
        email=email,
        password=password,
        country=country,
        culture=culture,
        timeout=30,
    ) as client:
        try:
            # Step 1: Provision the API (required first call)
            logger.info("📡 Provisioning API access...")
            version = await client.provision()
            logger.info(f"✅ API provisioned successfully, version: {version}")

            # Step 2: Check user status (optional)
            logger.info("👤 Checking user account status...")
            user_status = await client.get_user_status()
            logger.info(f"   Account Status: {user_status.account_status.value}")
            logger.info(f"   Auth Method: {user_status.authentication_method.value}")

            # Step 3: Begin login process
            logger.info("🔐 Beginning login process...")
            challenge = await client.begin_login()
            logger.info(f"   Challenge ID: {challenge.challenge_id}")
            logger.info("📧 Check your email for the OTP code!")

            # In a real scenario, you would wait for user input here
            # For this example, we'll show how to complete the process
            logger.info(
                "⏳ Waiting for OTP code (this example won't complete without real OTP)"
            )

            # Uncomment the following lines and provide real OTP when testing:
            # otp_code = input("Enter OTP code from email: ")
            # login_info = await client.complete_login(
            #     str(challenge.challenge_id), otp_code
            # )
            # logger.info(f"✅ Authentication successful!")
            # logger.info(f"   Account ID: {login_info.account}")
            # logger.info(f"   Token Type: {login_info.token_type.value}")

            # # Step 4: Get devices
            # logger.info("📱 Getting device list...")
            # devices = await client.get_devices()
            # logger.info(f"   Found {len(devices)} device(s)")

            # for device in devices:
            #     logger.info(f"   📱 Device: {device.name} ({device.serial_number})")
            #     logger.info(f"        Product Type: {device.product_type}")
            #     logger.info(f"        Connection: {device.connection_category.value}")
            #
            #     # Get IoT credentials for cloud MQTT connection
            #     try:
            #         iot_data = await client.get_iot_credentials(device.serial_number)
            #         logger.info(f"    ☁️  AWS IoT Endpoint: {iot_data.endpoint}")
            #     except Exception as e:
            #         logger.warning(f"    Could not get IoT credentials: {e}")

        except DysonAuthError as e:
            logger.error(f"❌ Authentication error: {e}")
        except DysonConnectionError as e:
            logger.error(f"❌ Connection error: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")


async def context_manager_async_example() -> None:
    """Example using async context manager for automatic cleanup."""
    logger.info("🔄 Starting async context manager example")

    async with AsyncDysonClient() as client:
        logger.info("✅ Client created and will be automatically closed")
        logger.info(f"   Country: {client.country}")
        logger.info(f"   Culture: {client.culture}")
        logger.info(f"   Timeout: {client.timeout}s")

    # Client is automatically closed here
    logger.info("🔒 Client automatically closed")


async def step_by_step_async_auth_example() -> None:
    """Demonstrates the complete step-by-step async authentication process."""
    logger.info("📋 Starting step-by-step async authentication example")

    email = os.getenv("DYSON_EMAIL")
    password = os.getenv("DYSON_PASSWORD")

    if not email or not password:
        logger.warning(
            "⚠️  Set DYSON_EMAIL and DYSON_PASSWORD environment variables to test "
            "authentication"
        )
        return

    async with AsyncDysonClient(email=email, password=password) as client:
        try:
            # Step 1: Provision
            logger.info("1️⃣  Provisioning API...")
            await client.provision()

            # Step 2: Begin login
            logger.info("2️⃣  Starting login process...")
            challenge = await client.begin_login()

            # Step 3: Wait for OTP (in real usage)
            logger.info("3️⃣  OTP code sent to email")
            logger.info(f"   Challenge ID: {challenge.challenge_id}")

            # In a real application, you would prompt for OTP here
            logger.info("   💡 In real usage, prompt user for OTP code here")

            # Example of how to complete (commented out):
            # otp_code = await get_otp_from_user()  # Your async input method
            # login_info = await client.complete_login(
            #     str(challenge.challenge_id), otp_code
            # )
            # logger.info("4️⃣  Authentication completed!")

        except Exception as e:
            logger.error(f"❌ Error in authentication flow: {e}")


async def concurrent_operations_example() -> None:
    """Example showing concurrent async operations."""
    logger.info("⚡ Starting concurrent operations example")

    # Create multiple clients concurrently
    async def create_client_task(client_id: int) -> str:
        async with AsyncDysonClient(timeout=10):
            await asyncio.sleep(0.1)  # Simulate some work
            return f"Client {client_id} completed"

    # Run multiple tasks concurrently
    tasks = [create_client_task(i) for i in range(3)]
    results = await asyncio.gather(*tasks)

    for result in results:
        logger.info(f"   ✅ {result}")


async def token_reuse_example() -> None:
    """Example of reusing authentication tokens between sessions."""
    logger.info("🔑 Starting token reuse example")

    # Simulate getting a token from a previous session
    saved_token = os.getenv("DYSON_SAVED_TOKEN")

    if saved_token:
        async with AsyncDysonClient(auth_token=saved_token) as client:
            logger.info("✅ Using saved authentication token")

            try:
                # Try to use the saved token
                devices = await client.get_devices()
                logger.info(f"   🎉 Token is valid! Found {len(devices)} devices")

            except DysonAuthError:
                logger.warning("   ⚠️  Saved token is invalid or expired")
                logger.info("   💡 Would need to re-authenticate in real usage")
    else:
        logger.info(
            "   💡 No saved token found. Set DYSON_SAVED_TOKEN environment "
            "variable to test"
        )


async def error_handling_example() -> None:
    """Example of proper async error handling."""
    logger.info("🛡️  Starting error handling example")

    async with AsyncDysonClient() as client:
        # Test various error conditions
        try:
            await client.get_devices()  # Should fail - not authenticated
        except DysonAuthError as e:
            logger.info(f"   ✅ Caught expected auth error: {e}")

        try:
            await client.begin_login()  # Should fail - no email
        except DysonAuthError as e:
            logger.info(f"   ✅ Caught expected auth error: {e}")

        try:
            await client.get_iot_credentials(
                "invalid_serial"
            )  # Should fail - not authenticated
        except DysonAuthError as e:
            logger.info(f"   ✅ Caught expected auth error: {e}")


async def main() -> None:
    """Main async function to run examples."""
    logger.info("🌟 Starting Dyson Async Client Examples")
    logger.info("=" * 50)

    examples = [
        ("Basic Async Usage", basic_async_example),
        ("Context Manager", context_manager_async_example),
        ("Step-by-Step Auth", step_by_step_async_auth_example),
        ("Concurrent Operations", concurrent_operations_example),
        ("Token Reuse", token_reuse_example),
        ("Error Handling", error_handling_example),
    ]

    for name, example_func in examples:
        logger.info(f"\n📖 Running: {name}")
        logger.info("-" * 30)
        try:
            await example_func()
        except Exception as e:
            logger.error(f"❌ Example failed: {e}")
        logger.info("✅ Example completed")

    logger.info("\n🎉 All async examples completed!")
    logger.info("=" * 50)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
