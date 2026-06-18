"""
Data models for libdyson-rest.

This module contains all data model classes for the Dyson REST API.
"""

from .auth import (
    AuthenticationMethod,
    LoginChallenge,
    LoginInformation,
    TokenType,
    UserStatus,
)
from .device import (
    MQTT,
    ConnectedConfiguration,
    ConnectionCategory,
    Device,
    DeviceCategory,
    Firmware,
    PendingRelease,
    RemoteBrokerType,
)
from .environment import (
    DailyAirQualityData,
    OutdoorAirQualityData,
    ScheduledEvent,
    ScheduledEventsData,
)
from .iot import IoTCredentials, IoTData
from .robot import (
    CleanedFootprint,
    CleanFault,
    CleaningProgramme,
    CleaningStrategy,
    CleanMapPosition,
    CleanRecord,
    CleanTimelineEvent,
    CleanZone,
    CleanZoneSettings,
    DustMapData,
    PersistentMap,
    PersistentMapMeta,
    ProtobufMapData,
    RecommendedCleanMap,
    ZoneDustBreakdown,
    ZoneMeta,
    ZonePrediction,
    decode_dust_map,
)

__all__ = [
    # Auth models
    "AuthenticationMethod",
    "LoginChallenge",
    "LoginInformation",
    "TokenType",
    "UserStatus",
    # Device models
    "ConnectedConfiguration",
    "ConnectionCategory",
    "Device",
    "DeviceCategory",
    "Firmware",
    "MQTT",
    "PendingRelease",
    "RemoteBrokerType",
    # IoT models
    "IoTCredentials",
    "IoTData",
    # Robot / Vis Nav models
    "CleanedFootprint",
    "CleanFault",
    "CleaningProgramme",
    "CleaningStrategy",
    "CleanMapPosition",
    "CleanRecord",
    "CleanTimelineEvent",
    "CleanZone",
    "CleanZoneSettings",
    "DustMapData",
    "PersistentMap",
    "PersistentMapMeta",
    "ProtobufMapData",
    "RecommendedCleanMap",
    "ZoneDustBreakdown",
    "ZoneMeta",
    "ZonePrediction",
    "decode_dust_map",
    # Environment / EC purifier models
    "DailyAirQualityData",
    "OutdoorAirQualityData",
    "ScheduledEvent",
    "ScheduledEventsData",
]
