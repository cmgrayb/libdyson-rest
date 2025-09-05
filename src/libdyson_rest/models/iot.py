"""
IoT model classes for libdyson-rest.

These models represent the IoT connection data structures from the Dyson API.
"""

from dataclasses import dataclass
from typing import Any, Dict, cast
from uuid import UUID

from ..types import IoTCredentialsResponseDict, IoTDataResponseDict
from ..validation import (
    JSONValidationError,
    safe_get_dict,
    safe_get_str,
    validate_json_response,
)


@dataclass
class IoTCredentials:
    """IoT credentials for AWS connection."""

    client_id: UUID
    custom_authorizer_name: str
    token_key: str
    token_signature: str
    token_value: UUID

    @classmethod
    def from_dict(cls, data: IoTCredentialsResponseDict) -> "IoTCredentials":
        """Create IoTCredentials instance from dictionary."""
        validated_data = validate_json_response(data, "IoTCredentials")

        try:
            client_id = UUID(safe_get_str(validated_data, "ClientId"))
        except ValueError as e:
            raise JSONValidationError(f"Invalid UUID format for ClientId: {e}") from e

        try:
            token_value = UUID(safe_get_str(validated_data, "TokenValue"))
        except ValueError as e:
            raise JSONValidationError(f"Invalid UUID format for TokenValue: {e}") from e

        return cls(
            client_id=client_id,
            custom_authorizer_name=safe_get_str(validated_data, "CustomAuthorizerName"),
            token_key=safe_get_str(validated_data, "TokenKey"),
            token_signature=safe_get_str(validated_data, "TokenSignature"),
            token_value=token_value,
        )

    def to_dict(self) -> Dict[str, str]:
        """Convert IoTCredentials instance to dictionary."""
        return {
            "ClientId": str(self.client_id),
            "CustomAuthorizerName": self.custom_authorizer_name,
            "TokenKey": self.token_key,
            "TokenSignature": self.token_signature,
            "TokenValue": str(self.token_value),
        }


@dataclass
class IoTData:
    """IoT connection information for a device."""

    endpoint: str
    iot_credentials: IoTCredentials

    @classmethod
    def from_dict(cls, data: IoTDataResponseDict) -> "IoTData":
        """Create IoTData instance from dictionary."""
        validated_data = validate_json_response(data, "IoTData")

        # Cast the nested dictionary to the correct type
        iot_creds_data = cast(
            IoTCredentialsResponseDict, safe_get_dict(validated_data, "IoTCredentials")
        )

        return cls(
            endpoint=safe_get_str(validated_data, "Endpoint"),
            iot_credentials=IoTCredentials.from_dict(iot_creds_data),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert IoTData instance to dictionary."""
        return {
            "Endpoint": self.endpoint,
            "IoTCredentials": self.iot_credentials.to_dict(),
        }
