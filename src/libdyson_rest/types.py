"""
TypedDict definitions for Dyson API responses.

These definitions provide compile-time type safety for JSON API responses
and enable better IDE support and error detection.
"""

from typing import List, TypedDict

from typing_extensions import NotRequired, Required


class UserStatusResponseDict(TypedDict):
    """Type definition for user status API response."""

    accountStatus: Required[str]
    authenticationMethod: Required[str]


class LoginChallengeResponseDict(TypedDict):
    """Type definition for login challenge API response."""

    challengeId: Required[str]


class LoginInformationResponseDict(TypedDict):
    """Type definition for login information API response."""

    account: Required[str]
    token: Required[str]
    tokenType: Required[str]


class FirmwareResponseDict(TypedDict):
    """Type definition for firmware information in API response."""

    autoUpdateEnabled: Required[bool]
    newVersionAvailable: Required[bool]
    version: Required[str]
    capabilities: NotRequired[List[str]]
    minimumAppVersion: NotRequired[str]


class MQTTResponseDict(TypedDict):
    """Type definition for MQTT information in API response."""

    localBrokerCredentials: Required[str]
    mqttRootTopicLevel: Required[str]
    remoteBrokerType: Required[str]


class ConnectedConfigurationResponseDict(TypedDict):
    """Type definition for connected configuration in API response."""

    firmware: Required[FirmwareResponseDict]
    mqtt: Required[MQTTResponseDict]


class DeviceResponseDict(TypedDict):
    """Type definition for device information in API response."""

    serialNumber: Required[str]
    name: str | None  # Can be null in API responses
    model: Required[str]
    type: Required[str]
    category: Required[str]
    connectionCategory: Required[str]
    variant: NotRequired[str]
    connectedConfiguration: NotRequired[ConnectedConfigurationResponseDict]


class IoTCredentialsResponseDict(TypedDict):
    """Type definition for IoT credentials in API response."""

    ClientId: Required[str]
    CustomAuthorizerName: Required[str]
    TokenKey: Required[str]
    TokenSignature: Required[str]
    TokenValue: Required[str]


class PendingReleaseResponseDict(TypedDict):
    """Type definition for pending firmware release API response."""

    version: Required[str]
    pushed: Required[bool]


class IoTDataResponseDict(TypedDict):
    """Type definition for IoT data API response."""

    Endpoint: Required[str]
    IoTCredentials: Required[IoTCredentialsResponseDict]
