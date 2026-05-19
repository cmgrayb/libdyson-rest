"""
Environmental sensor model classes for libdyson-rest.

These models represent cloud data structures returned by the Dyson API for
EC-category devices (air purifiers, heaters, fans with environmental sensing).

Endpoints covered:
- GET /v1/messageprocessor/devices/{serial}/environmentdata/daily
    → DailyAirQualityData
- GET /v1/unifiedscheduler/{serial}/events?productType={code}
    → ScheduledEventsData
- GET /v1/environment/devices/{serial}/data
    → OutdoorAirQualityData
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from ..types import (
    DailyEnvironmentDataDict,
    OutdoorEnvironmentDataDict,
    ScheduledEventDict,
    ScheduledEventsDataDict,
)


@dataclass
class DailyAirQualityData:
    """Indoor air-quality history for one device at 15-minute resolution.

    Source: GET /v1/messageprocessor/devices/{serial}/environmentdata/daily

    The ``samples`` list contains one AQI value per 15-minute slot for the
    current day (up to 96 entries); ``None`` entries indicate no reading for
    that slot.  The ``latest_sample`` property returns the most recent
    non-null value.
    """

    start_time: str | None
    """ISO-8601 timestamp of the first sample in the series."""
    resolution_minutes: int
    """Sample interval in minutes (typically 15)."""
    samples: list[float | None]
    """AQI samples, oldest first; ``None`` = no reading for that slot."""

    @classmethod
    def from_dict(cls, data: DailyEnvironmentDataDict) -> DailyAirQualityData:
        """Create a DailyAirQualityData from an API response dict."""
        raw: dict[str, Any] = dict(data)
        raw_samples = raw.get("aqlm") or []
        samples: list[float | None] = [
            float(v) if isinstance(v, int | float) else None for v in raw_samples
        ]
        resolution_raw = raw.get("resolution")
        return cls(
            start_time=raw.get("start_time"),
            resolution_minutes=int(resolution_raw)
            if isinstance(resolution_raw, int)
            else 15,
            samples=samples,
        )

    @property
    def latest_sample(self) -> float | None:
        """The most recent non-null AQI sample, or None."""
        for value in reversed(self.samples):
            if value is not None:
                return value
        return None

    @property
    def min_sample(self) -> float | None:
        """Minimum non-null AQI value in the series, or None."""
        valid = [v for v in self.samples if v is not None]
        return min(valid) if valid else None

    @property
    def max_sample(self) -> float | None:
        """Maximum non-null AQI value in the series, or None."""
        valid = [v for v in self.samples if v is not None]
        return max(valid) if valid else None


@dataclass
class ScheduledEvent:
    """One scheduled automation event for a Dyson device.

    Source: an entry in the ``events`` list from
    GET /v1/unifiedscheduler/{serial}/events.
    """

    enabled: bool
    days: list[str]
    """Days of the week this event fires (e.g. ``["Monday", "Wednesday"]``)."""
    start_time: str | None
    """Local time in ``HH:MM`` format."""
    raw: dict[str, Any]
    """Full raw event dict for accessing any extra fields."""

    @classmethod
    def from_dict(cls, data: ScheduledEventDict) -> ScheduledEvent:
        """Create a ScheduledEvent from a raw dict."""
        raw: dict[str, Any] = dict(data)
        return cls(
            enabled=bool(raw.get("enabled", False)),
            days=[str(d) for d in (raw.get("days") or [])],
            start_time=raw.get("startTime"),
            raw=raw,
        )


@dataclass
class ScheduledEventsData:
    """Scheduled automation events for a device.

    Source: GET /v1/unifiedscheduler/{serial}/events?productType={code}
    """

    schedule_enabled: bool
    """Whether the overall schedule is active for this device."""
    events: list[ScheduledEvent]

    @classmethod
    def from_dict(cls, data: ScheduledEventsDataDict) -> ScheduledEventsData:
        """Create ScheduledEventsData from an API response dict."""
        raw: dict[str, Any] = dict(data)
        events = [
            ScheduledEvent.from_dict(cast(ScheduledEventDict, e))
            for e in (raw.get("events") or [])
            if isinstance(e, dict)
        ]
        return cls(
            schedule_enabled=bool(raw.get("enabled", False)),
            events=events,
        )

    @property
    def active_events(self) -> list[ScheduledEvent]:
        """Return only the enabled events."""
        return [e for e in self.events if e.enabled]


@dataclass
class OutdoorAirQualityData:
    """Outdoor air quality and weather data for a device's location.

    Source: GET /v1/environment/devices/{serial}/data

    Fields come from a third-party outdoor AQI service and may be ``None``
    when data is unavailable for the device's registered location.
    """

    aqi_state: int | None
    """Numeric AQI state code (e.g. 4 = poor)."""
    weather_state: int | None
    """Numeric weather state code."""
    pollen_state: int | None
    """Numeric pollen state code."""
    date_time: str | None
    """ISO-8601 timestamp of the reading, or ``None``."""
    aqi_value: Any | None
    """Raw AQI value as returned by the API, or ``None``."""
    pm25_value: Any | None
    """PM2.5 concentration value, or ``None``."""
    pm10_value: Any | None
    """PM10 concentration value, or ``None``."""
    no2_value: Any | None
    """NO₂ concentration value, or ``None``."""
    humidity: Any | None
    """Outdoor humidity value, or ``None``."""
    temperature: Any | None
    """Outdoor temperature value, or ``None``."""
    location_name: str | None
    """Human-readable location name, or ``None``."""
    aqi_name: str | None
    """Localised AQI category label (e.g. ``"Poor"``), or ``None``."""
    aqi_description: str | None
    """Localised AQI description, or ``None``."""
    dominant_pollen: Any | None
    """Dominant pollen type, or ``None``."""
    pollens: Any | None
    """Full pollen detail object, or ``None``."""
    raw: dict[str, Any]
    """Full raw response dict for accessing any extra fields."""

    @classmethod
    def from_dict(cls, data: OutdoorEnvironmentDataDict) -> OutdoorAirQualityData:
        """Create an OutdoorAirQualityData from an API response dict."""
        raw: dict[str, Any] = dict(data)
        aqi_state_raw = raw.get("AqiState")
        weather_state_raw = raw.get("WeatherState")
        pollen_state_raw = raw.get("PollenState")
        return cls(
            aqi_state=int(aqi_state_raw)
            if isinstance(aqi_state_raw, int | float)
            else None,
            weather_state=int(weather_state_raw)
            if isinstance(weather_state_raw, int | float)
            else None,
            pollen_state=int(pollen_state_raw)
            if isinstance(pollen_state_raw, int | float)
            else None,
            date_time=raw.get("DateTime"),
            aqi_value=raw.get("AqiValue"),
            pm25_value=raw.get("Pm25Value"),
            pm10_value=raw.get("Pm10Value"),
            no2_value=raw.get("No2Value"),
            humidity=raw.get("Humidity"),
            temperature=raw.get("Temperature"),
            location_name=raw.get("LocationName"),
            aqi_name=raw.get("AqiName"),
            aqi_description=raw.get("AqiDescription"),
            dominant_pollen=raw.get("DominantPollen"),
            pollens=raw.get("Pollens"),
            raw=raw,
        )
