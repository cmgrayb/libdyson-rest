"""
TypedDict definitions for Dyson API responses.

These definitions provide compile-time type safety for JSON API responses
and enable better IDE support and error detection.
"""

from typing import TypedDict

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
    capabilities: NotRequired[list[str]]
    minimumAppVersion: NotRequired[str]


class MQTTResponseDict(TypedDict):
    """Type definition for MQTT information in API response."""

    localBrokerCredentials: Required[str]
    mqttRootTopicLevel: Required[str]
    remoteBrokerType: Required[str]


class ConnectedConfigurationResponseDict(TypedDict):
    """Type definition for connected configuration in API response."""

    firmware: Required[FirmwareResponseDict]
    mqtt: NotRequired[MQTTResponseDict]  # Optional for non-WiFi devices


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


# ---------------------------------------------------------------------------
# Robot / Vis Nav cloud endpoints
# ---------------------------------------------------------------------------


class CleanTimelineEventDict(TypedDict):
    """One event in a cleaning run timeline."""

    time: NotRequired[str]
    eventName: NotRequired[str]
    faultLocation: NotRequired[str | None]


class DustDataEntryDict(TypedDict):
    """A single dust-density blob (base64-encoded, zlib-compressed)."""

    scaleFactor: NotRequired[int]
    data: Required[str]


class DustMapDict(TypedDict):
    """Aggregated dust-density map for one cleaning run."""

    width: Required[int]
    height: Required[int]
    resolution: NotRequired[int]
    dustData: Required[list[DustDataEntryDict]]


class CleanedFootprintDict(TypedDict):
    """Cleaned-area footprint for one cleaning run."""

    data: NotRequired[str]
    area: NotRequired[float]


class CleanMapPositionDict(TypedDict):
    """World-coordinate origin of a dust-map crop (mm)."""

    x: Required[float]
    y: Required[float]


class PersistentMapRefDict(TypedDict):
    """Persistent-map reference embedded in a clean record."""

    id: NotRequired[str]
    cleanMapPosition: NotRequired[CleanMapPositionDict]


class CleaningProgrammeDict(TypedDict):
    """Zone-clean programme embedded in a clean record."""

    persistentMapId: NotRequired[str]
    orderedZones: NotRequired[list[str]]
    unorderedZones: NotRequired[list[str]]
    zonesDefinitionLastUpdatedDate: NotRequired[str]


class CleanRecordDict(TypedDict):
    """One entry from GET /v1/{serial}/clean-maps."""

    cleanId: NotRequired[str]
    sequenceNumber: NotRequired[int]
    cleanTimeline: NotRequired[list[CleanTimelineEventDict]]
    cleanedFootprint: NotRequired[CleanedFootprintDict | None]
    cleaningProgramme: NotRequired[CleaningProgrammeDict | None]
    persistentMap: NotRequired[PersistentMapRefDict | None]
    dustMap: NotRequired[DustMapDict | None]


class ZoneMetaDict(TypedDict):
    """One zone entry from persistent-map metadata."""

    id: Required[str]
    name: NotRequired[str]
    icon: NotRequired[str]
    area: NotRequired[float]


class PersistentMapMetaDict(TypedDict):
    """One entry from GET /v1/app/{serial}/persistent-map-metadata."""

    id: Required[str]
    name: NotRequired[str]
    zonesDefinitionLastUpdatedDate: NotRequired[str]
    zones: NotRequired[list[ZoneMetaDict]]


class PresentationMapDict(TypedDict):
    """Presentation map PNG blob (base64-encoded)."""

    data: Required[str]


class ZonesDefinitionDict(TypedDict):
    """Zones definition including display orientation."""

    persistentMapDisplayOrientation: NotRequired[int]


class MapOffsetDict(TypedDict):
    """World-coordinate offset of the presentation map origin (mm)."""

    x: Required[float]
    y: Required[float]


class PersistentMapDict(TypedDict):
    """Full persistent map from GET /v1/app/{serial}/persistent-maps/{id}."""

    id: Required[str]
    name: NotRequired[str]
    offset: NotRequired[MapOffsetDict]
    presentationMap: NotRequired[PresentationMapDict]
    zonesDefinition: NotRequired[ZonesDefinitionDict]
    zones: NotRequired[list[ZoneMetaDict]]


class ZoneDustMilligramsEntryDict(TypedDict):
    """One particle-class dust entry (e.g. fine, total) in mg."""

    name: Required[str]
    weight: Required[float]


class ZonePredictionDict(TypedDict):
    """Dust prediction for one zone."""

    zoneId: Required[str]
    zoneDustMilligrams: NotRequired[list[ZoneDustMilligramsEntryDict]]


class RecommendedCleanMapDict(TypedDict):
    """One entry from GET /v1/app/{serial}/recommended-cleans."""

    persistentMapId: Required[str]
    zonePredictions: NotRequired[list[ZonePredictionDict]]


# ---------------------------------------------------------------------------
# EC (air purifier) cloud endpoints
# ---------------------------------------------------------------------------


class DailyEnvironmentDataDict(TypedDict):
    """Response from GET /v1/messageprocessor/devices/{serial}/environmentdata/daily."""

    start_time: NotRequired[str]
    resolution: NotRequired[int]
    aqlm: NotRequired[list[float | None]]


class ScheduledEventDict(TypedDict):
    """One scheduled event from GET /v1/unifiedscheduler/{serial}/events."""

    enabled: NotRequired[bool]
    days: NotRequired[list[str]]
    startTime: NotRequired[str]


class ScheduledEventsDataDict(TypedDict):
    """Response from GET /v1/unifiedscheduler/{serial}/events."""

    enabled: NotRequired[bool]
    events: NotRequired[list[ScheduledEventDict]]
