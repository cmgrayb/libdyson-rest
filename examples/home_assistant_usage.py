#!/usr/bin/env python3
"""
Example of how to use libdyson-rest in a Home Assistant integration.

This demonstrates proper logging configuration and debug control
patterns that align with Home Assistant best practices.
"""

import logging

from libdyson_rest import AsyncDysonClient, DysonClient
from libdyson_rest.exceptions import DysonAPIError, DysonConnectionError

# This is how Home Assistant integrations typically set up their logger
_LOGGER = logging.getLogger(__name__)


class DysonDeviceManager:
    """
    Example device manager that might be used in a Home Assistant integration.

    Shows how to properly use the debug parameter and logging levels.
    """

    def __init__(
        self, email: str, password: str, country: str = "US", debug: bool = False
    ):
        """Initialize the device manager."""
        self.email = email
        self.password = password
        self.country = country
        self.debug = debug

        # In Home Assistant, debug mode can be controlled via configuration.yaml:
        # logger:
        #   logs:
        #     custom_components.dyson: debug
        #     libdyson_rest: debug

    async def async_setup(self) -> bool:
        """
        Set up the Dyson integration.

        In Home Assistant, this would be called during integration setup.
        """
        try:
            # Use debug=True only when Home Assistant debug logging is enabled
            # In a real integration, this would check the logger level:
            # debug_enabled = _LOGGER.isEnabledFor(logging.DEBUG)

            async with AsyncDysonClient(
                email=self.email,
                password=self.password,
                country=self.country,
                debug=self.debug,  # Enable detailed HTTP logging when debugging
            ) as client:

                _LOGGER.info(
                    "Setting up Dyson integration for country: %s", self.country
                )

                # Provision API access
                version = await client.provision()
                _LOGGER.debug("Dyson API version: %s", version)

                # Check user status
                user_status = await client.get_user_status()
                _LOGGER.debug("User authentication method: %s", user_status.auth_mode)

                # Begin authentication
                challenge_id = await client.begin_login()
                _LOGGER.info("Authentication challenge started: %s", challenge_id)

                return True

        except DysonConnectionError as e:
            _LOGGER.error("Failed to connect to Dyson API: %s", e)
            return False
        except DysonAPIError as e:
            _LOGGER.error("Dyson API error: %s", e)
            return False
        except Exception as e:
            _LOGGER.exception("Unexpected error during Dyson setup: %s", e)
            return False

    def sync_setup(self) -> bool:
        """
        Synchronous setup example.

        Shows how to use the sync client with proper logging.
        """
        try:
            with DysonClient(
                email=self.email,
                password=self.password,
                country=self.country,
                debug=self.debug,
            ) as client:

                _LOGGER.info(
                    "Setting up Dyson integration (sync) for country: %s", self.country
                )

                version = client.provision()
                _LOGGER.debug("Dyson API version: %s", version)

                return True

        except (DysonConnectionError, DysonAPIError) as e:
            _LOGGER.error("Dyson setup failed: %s", e)
            return False


def main() -> None:
    """
    Example of how this would be used in Home Assistant.

    In Home Assistant, debug logging can be enabled via configuration.yaml:

    logger:
      default: info
      logs:
        custom_components.dyson: debug
        libdyson_rest: debug
    """
    # Configure logging similar to Home Assistant
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    # Enable debug logging for our library (this would be done by HA config)
    logging.getLogger("libdyson_rest").setLevel(logging.DEBUG)

    # Example: Debug mode controlled by environment or configuration
    import os

    debug_mode = os.getenv("DYSON_DEBUG", "false").lower() == "true"

    manager = DysonDeviceManager(
        email="user@example.com",
        password="password123",
        country="US",
        debug=debug_mode,  # Only enable detailed HTTP logging when needed
    )

    # In Home Assistant, this would be called during integration setup
    success = manager.sync_setup()
    if success:
        _LOGGER.info("Dyson integration setup completed successfully")
    else:
        _LOGGER.error("Dyson integration setup failed")


if __name__ == "__main__":
    print("🏠 Home Assistant Integration Example")
    print("🔧 This example shows proper logging patterns for HA integrations")
    print("📝 See comments in the code for configuration details")
    print()

    # Don't actually run the setup without real credentials
    print("💡 To enable debug logging in Home Assistant:")
    print("   Add this to your configuration.yaml:")
    print()
    print("   logger:")
    print("     logs:")
    print("       custom_components.dyson: debug")
    print("       libdyson_rest: debug")
    print()
    print("🔍 When debug logging is enabled, set debug=True in client constructors")
    print("   for detailed HTTP request/response logging")
