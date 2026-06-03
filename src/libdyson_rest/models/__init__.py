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
    CleaningProgramme,
    CleaningStrategy,
    CleanMapPosition,
    CleanRecord,
    CleanTimelineEvent,
    DustMapData,
    PersistentMap,
    PersistentMapMeta,
    RecommendedCleanMap,
    ZoneDustBreakdown,
    ZoneMeta,
    ZonePrediction,
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
    "CleaningProgramme",
    "CleaningStrategy",
    "CleanMapPosition",
    "CleanRecord",
    "CleanTimelineEvent",
    "DustMapData",
    "PersistentMap",
    "PersistentMapMeta",
    "RecommendedCleanMap",
    "ZoneDustBreakdown",
    "ZoneMeta",
    "ZonePrediction",
    # Environment / EC purifier models
    "DailyAirQualityData",
    "OutdoorAirQualityData",
    "ScheduledEvent",
    "ScheduledEventsData",
]
