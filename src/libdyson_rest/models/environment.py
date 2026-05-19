"""
Environmental sensor model classes for libdyson-rest.

These models represent cloud data structures returned by the Dyson API for
EC-category devices (air purifiers, heaters, fans with environmental sensing).

Endpoints covered:
- GET /v1/messageprocessor/devices/{serial}/environmentdata/daily
    → DailyAirQualityData
- GET /v1/unifiedscheduler/{serial}/events?productType={code}
    → ScheduledEventsData
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from ..types import (
    DailyEnvironmentDataDict,
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
