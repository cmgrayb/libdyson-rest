"""
Example usage of libdyson-rest library.

This example demonstrates how to use the library to interact with Dyson devices.
Note: This is for demonstration purposes only and requires proper API credentials.
"""

import logging
import os

from libdyson_rest import DysonAuthError, DysonClient, DysonConnectionError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def basic_example() -> None:
    """Basic synchronous usage example."""
    # Initialize client with credentials
    client = DysonClient(
        email=os.getenv("DYSON_EMAIL", "your_email@example.com"),
        password=os.getenv("DYSON_PASSWORD", "your_password"),
        country="US",
        timeout=30,
    )

    try:
        # Authenticate with Dyson API
        logger.info("Authenticating with Dyson API...")
        success = client.authenticate()

        if not success:
            logger.error("Authentication failed")
            return

        logger.info("Authentication successful!")

        # Get list of devices
        logger.info("Retrieving device list...")
        devices = client.get_devices()

        logger.info(f"Found {len(devices)} devices:")
        for device in devices:
            name = device.get("name", "Unknown")
            serial = device.get("serial", "No serial")
            logger.info(f"  - {name}: {serial}")

    except DysonAuthError as e:
        logger.error(f"Authentication error: {e}")
    except DysonConnectionError as e:
        logger.error(f"Connection error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        # Always close the client
        client.close()


def context_manager_example() -> None:
    """Example using context manager for automatic cleanup."""
    email = os.getenv("DYSON_EMAIL")
    password = os.getenv("DYSON_PASSWORD")

    if not email or not password:
        logger.warning("DYSON_EMAIL and DYSON_PASSWORD environment variables not set")
        logger.info("Using demo mode with mock data")
        return

    try:
        with DysonClient(email=email, password=password) as client:
            # Client is automatically closed when exiting the context
            client.authenticate()

            devices = client.get_devices()
            logger.info(f"Found {len(devices)} devices using context manager")

    except Exception as e:
        logger.error(f"Error in context manager example: {e}")


def advanced_example() -> None:
    """Advanced usage example with error handling and device details."""
    client = DysonClient(
        email=os.getenv("DYSON_EMAIL", "demo@example.com"),
        password=os.getenv("DYSON_PASSWORD", "demo_password"),
        country=os.getenv("DYSON_COUNTRY", "US"),
        timeout=int(os.getenv("DYSON_TIMEOUT", "30")),
    )

    try:
        # Authenticate
        if not client.authenticate():
            raise DysonAuthError("Failed to authenticate")

        # Get devices with detailed processing
        devices = client.get_devices()

        if not devices:
            logger.info("No devices found for this account")
            return

        # Process each device
        for i, device_data in enumerate(devices, 1):
            logger.info(f"\\nDevice {i}:")
            logger.info(f"  Serial: {device_data.get('serial', 'Unknown')}")
            logger.info(f"  Name: {device_data.get('name', 'Unnamed Device')}")
            logger.info(f"  Product Type: {device_data.get('product_type', 'Unknown')}")
            logger.info(f"  Version: {device_data.get('version', 'Unknown')}")
            logger.info(f"  Auto Update: {device_data.get('auto_update', False)}")

            # Additional processing could go here
            # For example: device configuration, state queries, commands, etc.

    except DysonAuthError:
        logger.error("Authentication failed. Please check your credentials.")
    except DysonConnectionError:
        logger.error("Connection failed. Please check your internet connection.")
    except Exception as e:
        logger.error(f"Unexpected error: {type(e).__name__}: {e}")
    finally:
        client.close()


def main() -> None:
    """Main function to run examples."""
    logger.info("=== libdyson-rest Example Usage ===")

    logger.info("\\n1. Basic Example:")
    basic_example()

    logger.info("\\n2. Context Manager Example:")
    context_manager_example()

    logger.info("\\n3. Advanced Example:")
    advanced_example()

    logger.info("\\n=== Examples Complete ===")


if __name__ == "__main__":
    main()
