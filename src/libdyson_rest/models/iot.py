"""
IoT model classes for libdyson-rest.

These models represent the IoT connection data structures from the Dyson API.
"""

from dataclasses import dataclass
from typing import Any, Dict
from uuid import UUID


@dataclass
class IoTCredentials:
    """IoT credentials for AWS connection."""

    client_id: UUID
    custom_authorizer_name: str
    token_key: str
    token_signature: str
    token_value: UUID

    @classmethod
    def from_dict(cls, data: Dict) -> "IoTCredentials":
        """Create IoTCredentials instance from dictionary."""
        return cls(
            client_id=UUID(data["ClientId"]),
            custom_authorizer_name=data["CustomAuthorizerName"],
            token_key=data["TokenKey"],
            token_signature=data["TokenSignature"],
            token_value=UUID(data["TokenValue"]),
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
    def from_dict(cls, data: Dict) -> "IoTData":
        """Create IoTData instance from dictionary."""
        return cls(
            endpoint=data["Endpoint"],
            iot_credentials=IoTCredentials.from_dict(data["IoTCredentials"]),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert IoTData instance to dictionary."""
        return {
            "Endpoint": self.endpoint,
            "IoTCredentials": self.iot_credentials.to_dict(),
        }
