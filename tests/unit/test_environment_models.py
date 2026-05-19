"""Unit tests for EC air purifier model classes."""

import pytest

from libdyson_rest.models import (
    DailyAirQualityData,
    OutdoorAirQualityData,
    ScheduledEvent,
    ScheduledEventsData,
)

# ---------------------------------------------------------------------------
# DailyAirQualityData
# ---------------------------------------------------------------------------


class TestDailyAirQualityData:
    def test_from_dict_full(self) -> None:
        data = DailyAirQualityData.from_dict(
            {
                "start_time": "2024-01-01T00:00:00Z",
                "resolution": 15,
                "aqlm": [1.0, 2.0, 3.0],
            }
        )
        assert data.start_time == "2024-01-01T00:00:00Z"
        assert data.resolution_minutes == 15
        assert data.samples == [1.0, 2.0, 3.0]

    def test_from_dict_with_none_samples(self) -> None:
        data = DailyAirQualityData.from_dict({"aqlm": [1.0, None, 3.0]})
        assert data.samples == [1.0, None, 3.0]

    def test_from_dict_with_non_numeric_samples_become_none(self) -> None:
        data = DailyAirQualityData.from_dict({"aqlm": [1.0, "bad", 3.0]})
        assert data.samples[1] is None

    def test_from_dict_defaults(self) -> None:
        data = DailyAirQualityData.from_dict({})
        assert data.start_time is None
        assert data.resolution_minutes == 15  # default
        assert data.samples == []

    def test_from_dict_resolution_non_int_defaults_to_15(self) -> None:
        data = DailyAirQualityData.from_dict({"resolution": "hourly"})
        assert data.resolution_minutes == 15

    def test_latest_sample_last_non_null(self) -> None:
        data = DailyAirQualityData.from_dict({"aqlm": [1.0, 2.0, None]})
        assert data.latest_sample == pytest.approx(2.0)

    def test_latest_sample_all_none(self) -> None:
        data = DailyAirQualityData.from_dict({"aqlm": [None, None]})
        assert data.latest_sample is None

    def test_latest_sample_empty(self) -> None:
        data = DailyAirQualityData.from_dict({})
        assert data.latest_sample is None

    def test_min_sample(self) -> None:
        data = DailyAirQualityData.from_dict({"aqlm": [5.0, None, 2.0, 8.0]})
        assert data.min_sample == pytest.approx(2.0)

    def test_min_sample_all_none(self) -> None:
        data = DailyAirQualityData.from_dict({"aqlm": [None]})
        assert data.min_sample is None

    def test_max_sample(self) -> None:
        data = DailyAirQualityData.from_dict({"aqlm": [5.0, None, 2.0, 8.0]})
        assert data.max_sample == pytest.approx(8.0)

    def test_max_sample_all_none(self) -> None:
        data = DailyAirQualityData.from_dict({"aqlm": [None]})
        assert data.max_sample is None

    def test_integer_samples_converted_to_float(self) -> None:
        data = DailyAirQualityData.from_dict({"aqlm": [1, 2, 3]})
        assert all(isinstance(s, float) for s in data.samples if s is not None)


# ---------------------------------------------------------------------------
# ScheduledEvent
# ---------------------------------------------------------------------------


class TestScheduledEvent:
    def test_from_dict_full(self) -> None:
        event = ScheduledEvent.from_dict(
            {
                "enabled": True,
                "days": ["Monday", "Wednesday", "Friday"],
                "startTime": "07:30",
                "extra_field": "preserved",
            }
        )
        assert event.enabled is True
        assert event.days == ["Monday", "Wednesday", "Friday"]
        assert event.start_time == "07:30"
        assert event.raw["extra_field"] == "preserved"

    def test_from_dict_disabled(self) -> None:
        event = ScheduledEvent.from_dict({"enabled": False})
        assert event.enabled is False

    def test_from_dict_defaults(self) -> None:
        event = ScheduledEvent.from_dict({})
        assert event.enabled is False
        assert event.days == []
        assert event.start_time is None

    def test_days_coerced_to_str(self) -> None:
        event = ScheduledEvent.from_dict({"days": [0, 1, 2]})
        assert event.days == ["0", "1", "2"]


# ---------------------------------------------------------------------------
# ScheduledEventsData
# ---------------------------------------------------------------------------


EVENTS_DATA_RAW: dict = {
    "enabled": True,
    "events": [
        {
            "enabled": True,
            "days": ["Monday"],
            "startTime": "08:00",
        },
        {
            "enabled": False,
            "days": ["Saturday"],
            "startTime": "10:00",
        },
    ],
}


class TestScheduledEventsData:
    def test_from_dict_full(self) -> None:
        data = ScheduledEventsData.from_dict(EVENTS_DATA_RAW)
        assert data.schedule_enabled is True
        assert len(data.events) == 2

    def test_active_events(self) -> None:
        data = ScheduledEventsData.from_dict(EVENTS_DATA_RAW)
        active = data.active_events
        assert len(active) == 1
        assert active[0].days == ["Monday"]

    def test_from_dict_empty_events(self) -> None:
        data = ScheduledEventsData.from_dict({"enabled": False})
        assert data.schedule_enabled is False
        assert data.events == []
        assert data.active_events == []

    def test_from_dict_non_dict_events_are_skipped(self) -> None:
        data = ScheduledEventsData.from_dict(
            {"enabled": True, "events": [None, "bad", {"enabled": True}]}
        )
        assert len(data.events) == 1

    def test_from_dict_schedule_disabled(self) -> None:
        data = ScheduledEventsData.from_dict({})
        assert data.schedule_enabled is False


# ---------------------------------------------------------------------------
# OutdoorAirQualityData
# ---------------------------------------------------------------------------

OUTDOOR_RAW = {
    "DateTime": "2024-06-01T12:00:00Z",
    "AqiState": 4,
    "AqiValue": None,
    "Pm25Value": None,
    "Pm10Value": None,
    "No2Value": None,
    "WeatherState": 2,
    "Humidity": None,
    "Temperature": None,
    "LocationName": "London",
    "AqiName": "Poor",
    "AqiDescription": "Air quality is poor",
    "PollenState": 3,
    "DominantPollen": None,
    "Pollens": None,
}


class TestOutdoorAirQualityData:
    def test_from_dict_full(self) -> None:
        data = OutdoorAirQualityData.from_dict(OUTDOOR_RAW)
        assert data.aqi_state == 4
        assert data.weather_state == 2
        assert data.pollen_state == 3
        assert data.date_time == "2024-06-01T12:00:00Z"
        assert data.location_name == "London"
        assert data.aqi_name == "Poor"
        assert data.aqi_description == "Air quality is poor"

    def test_from_dict_nullable_fields_are_none(self) -> None:
        data = OutdoorAirQualityData.from_dict(OUTDOOR_RAW)
        assert data.aqi_value is None
        assert data.pm25_value is None
        assert data.pm10_value is None
        assert data.no2_value is None
        assert data.humidity is None
        assert data.temperature is None
        assert data.dominant_pollen is None
        assert data.pollens is None

    def test_from_dict_empty(self) -> None:
        data = OutdoorAirQualityData.from_dict({})
        assert data.aqi_state is None
        assert data.weather_state is None
        assert data.pollen_state is None
        assert data.date_time is None
        assert data.location_name is None
        assert data.aqi_name is None

    def test_from_dict_float_state_coerced_to_int(self) -> None:
        data = OutdoorAirQualityData.from_dict({"AqiState": 3.9})
        assert data.aqi_state == 3
        assert isinstance(data.aqi_state, int)

    def test_from_dict_non_numeric_state_is_none(self) -> None:
        data = OutdoorAirQualityData.from_dict({"AqiState": "bad"})
        assert data.aqi_state is None

    def test_raw_preserves_all_fields(self) -> None:
        data = OutdoorAirQualityData.from_dict(OUTDOOR_RAW)
        assert data.raw["LocationName"] == "London"
        assert data.raw["AqiState"] == 4

