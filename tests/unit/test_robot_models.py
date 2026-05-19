"""Unit tests for Vis Nav robot vacuum model classes."""

import pytest

from libdyson_rest.models import (
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

# ---------------------------------------------------------------------------
# CleaningStrategy
# ---------------------------------------------------------------------------


class TestCleaningStrategy:
    def test_values(self) -> None:
        assert CleaningStrategy.AUTO.value == "auto"
        assert CleaningStrategy.QUICK.value == "quick"
        assert CleaningStrategy.QUIET.value == "quiet"
        assert CleaningStrategy.BOOST.value == "boost"

    def test_is_str_subclass(self) -> None:
        assert isinstance(CleaningStrategy.AUTO, str)

    def test_from_value(self) -> None:
        assert CleaningStrategy("auto") is CleaningStrategy.AUTO
        assert CleaningStrategy("boost") is CleaningStrategy.BOOST


# ---------------------------------------------------------------------------
# CleanTimelineEvent
# ---------------------------------------------------------------------------


class TestCleanTimelineEvent:
    def test_from_dict_full(self) -> None:
        event = CleanTimelineEvent.from_dict(
            {
                "time": "2024-01-01T10:00:00Z",
                "eventName": "START",
                "faultLocation": None,
            }  # noqa: E501
        )
        assert event.time == "2024-01-01T10:00:00Z"
        assert event.event_name == "START"
        assert event.fault_location is None

    def test_from_dict_partial(self) -> None:
        event = CleanTimelineEvent.from_dict({})
        assert event.time is None
        assert event.event_name is None
        assert event.fault_location is None

    def test_from_dict_with_fault(self) -> None:
        event = CleanTimelineEvent.from_dict({"faultLocation": "left_brush"})
        assert event.fault_location == "left_brush"


# ---------------------------------------------------------------------------
# CleanedFootprint
# ---------------------------------------------------------------------------


class TestCleanedFootprint:
    def test_from_dict_with_area(self) -> None:
        fp = CleanedFootprint.from_dict({"data": "base64==", "area": 12.5})
        assert fp.data == "base64=="
        assert fp.area == pytest.approx(12.5)

    def test_from_dict_with_cleaned_area_fallback(self) -> None:
        fp = CleanedFootprint.from_dict({"cleanedArea": 7.3})
        assert fp.area == pytest.approx(7.3)

    def test_from_dict_no_area(self) -> None:
        fp = CleanedFootprint.from_dict({"data": "x"})
        assert fp.area is None

    def test_from_dict_non_numeric_area(self) -> None:
        fp = CleanedFootprint.from_dict({"area": "unknown"})
        assert fp.area is None


# ---------------------------------------------------------------------------
# DustMapData
# ---------------------------------------------------------------------------


class TestDustMapData:
    def test_from_dict_full(self) -> None:
        dm = DustMapData.from_dict(
            {"width": 100, "height": 80, "resolution": 20, "dustData": [{"x": 0}]}
        )
        assert dm.width == 100
        assert dm.height == 80
        assert dm.resolution == 20
        assert dm.dust_data == [{"x": 0}]

    def test_from_dict_defaults(self) -> None:
        dm = DustMapData.from_dict({})
        assert dm.width == 0
        assert dm.height == 0
        assert dm.resolution == 20  # default
        assert dm.dust_data == []

    def test_from_dict_no_dust_data(self) -> None:
        dm = DustMapData.from_dict({"width": 50})
        assert dm.dust_data == []


# ---------------------------------------------------------------------------
# CleanMapPosition
# ---------------------------------------------------------------------------


class TestCleanMapPosition:
    def test_from_dict(self) -> None:
        pos = CleanMapPosition.from_dict({"x": 1500.0, "y": -300.0})
        assert pos.x == pytest.approx(1500.0)
        assert pos.y == pytest.approx(-300.0)

    def test_from_dict_defaults(self) -> None:
        pos = CleanMapPosition.from_dict({})
        assert pos.x == 0.0
        assert pos.y == 0.0


# ---------------------------------------------------------------------------
# CleaningProgramme
# ---------------------------------------------------------------------------


class TestCleaningProgramme:
    def test_from_dict_whole_house(self) -> None:
        prog = CleaningProgramme.from_dict(
            {
                "persistentMapId": "map-001",
                "orderedZones": [],
                "unorderedZones": [],
                "zonesDefinitionLastUpdatedDate": "2024-01-01T00:00:00Z",
            }
        )
        assert prog.persistent_map_id == "map-001"
        assert prog.ordered_zones == []
        assert prog.unordered_zones == []
        assert prog.is_zone_clean is False

    def test_from_dict_zone_clean(self) -> None:
        prog = CleaningProgramme.from_dict(
            {
                "persistentMapId": "map-001",
                "orderedZones": ["zone-A", "zone-B"],
                "unorderedZones": [],
                "zonesDefinitionLastUpdatedDate": "2024-01-01T00:00:00Z",
            }
        )
        assert prog.is_zone_clean is True
        assert prog.ordered_zones == ["zone-A", "zone-B"]

    def test_from_dict_unordered_zones(self) -> None:
        prog = CleaningProgramme.from_dict({"unorderedZones": ["zone-C"]})
        assert prog.is_zone_clean is True

    def test_from_dict_empty(self) -> None:
        prog = CleaningProgramme.from_dict({})
        assert prog.persistent_map_id is None
        assert prog.is_zone_clean is False


# ---------------------------------------------------------------------------
# CleanRecord
# ---------------------------------------------------------------------------

CLEAN_RECORD_FULL: dict = {
    "cleanId": "cr-001",
    "sequenceNumber": 42,
    "cleanTimeline": [
        {"time": "2024-01-01T09:00:00Z", "eventName": "START"},
        {"time": "2024-01-01T09:30:00Z", "eventName": "STOP"},
    ],
    "cleanedFootprint": {"data": "base64==", "area": 10.0},
    "cleaningProgramme": {
        "persistentMapId": "map-001",
        "orderedZones": ["zone-A"],
        "unorderedZones": [],
        "zonesDefinitionLastUpdatedDate": "2024-01-01T00:00:00Z",
    },
    "persistentMap": {
        "id": "map-001",
        "cleanMapPosition": {"x": 100.0, "y": 200.0},
    },
    "dustMap": {"width": 50, "height": 40, "resolution": 20, "dustData": []},
}


class TestCleanRecord:
    def test_from_dict_full(self) -> None:
        record = CleanRecord.from_dict(CLEAN_RECORD_FULL)
        assert record.clean_id == "cr-001"
        assert record.sequence_number == 42
        assert len(record.timeline) == 2
        assert record.cleaned_footprint is not None
        assert record.cleaned_footprint.area == pytest.approx(10.0)
        assert record.cleaning_programme is not None
        assert record.persistent_map_id == "map-001"
        assert record.clean_map_position is not None
        assert record.clean_map_position.x == pytest.approx(100.0)
        assert record.dust_map is not None
        assert record.dust_map.width == 50

    def test_from_dict_minimal(self) -> None:
        record = CleanRecord.from_dict({})
        assert record.clean_id is None
        assert record.sequence_number is None
        assert record.timeline == []
        assert record.cleaned_footprint is None
        assert record.cleaning_programme is None
        assert record.persistent_map_id is None
        assert record.clean_map_position is None
        assert record.dust_map is None

    def test_start_time_end_time(self) -> None:
        record = CleanRecord.from_dict(CLEAN_RECORD_FULL)
        assert record.start_time == "2024-01-01T09:00:00Z"
        assert record.end_time == "2024-01-01T09:30:00Z"

    def test_start_end_time_empty_timeline(self) -> None:
        record = CleanRecord.from_dict({})
        assert record.start_time is None
        assert record.end_time is None

    def test_is_zone_clean_true(self) -> None:
        record = CleanRecord.from_dict(CLEAN_RECORD_FULL)
        assert record.is_zone_clean is True

    def test_is_zone_clean_false(self) -> None:
        data = dict(CLEAN_RECORD_FULL)
        data["cleaningProgramme"] = {
            "persistentMapId": "map-001",
            "orderedZones": [],
            "unorderedZones": [],
        }
        record = CleanRecord.from_dict(data)
        assert record.is_zone_clean is False

    def test_is_zone_clean_no_programme(self) -> None:
        record = CleanRecord.from_dict({})
        assert record.is_zone_clean is False


# ---------------------------------------------------------------------------
# ZoneMeta
# ---------------------------------------------------------------------------


class TestZoneMeta:
    def test_from_dict_full(self) -> None:
        zm = ZoneMeta.from_dict(
            {"id": "z1", "name": "Kitchen", "icon": "🍳", "area": 8.2}
        )
        assert zm.id == "z1"
        assert zm.name == "Kitchen"
        assert zm.icon == "🍳"
        assert zm.area == pytest.approx(8.2)

    def test_from_dict_no_area(self) -> None:
        zm = ZoneMeta.from_dict({"id": "z2"})
        assert zm.area is None

    def test_from_dict_string_area_ignored(self) -> None:
        zm = ZoneMeta.from_dict({"id": "z3", "area": "unknown"})
        assert zm.area is None


# ---------------------------------------------------------------------------
# PersistentMapMeta
# ---------------------------------------------------------------------------

MAP_META_RAW: dict = {
    "id": "pm-001",
    "name": "Ground Floor",
    "zonesDefinitionLastUpdatedDate": "2024-06-01T00:00:00Z",
    "zones": [
        {"id": "z1", "name": "Kitchen", "area": 8.0},
        {"id": "z2", "name": "Living Room", "area": 20.0},
    ],
}


class TestPersistentMapMeta:
    def test_from_dict_full(self) -> None:
        meta = PersistentMapMeta.from_dict(MAP_META_RAW)
        assert meta.id == "pm-001"
        assert meta.name == "Ground Floor"
        assert meta.zones_definition_last_updated_date == "2024-06-01T00:00:00Z"
        assert len(meta.zones) == 2

    def test_zone_by_id_found(self) -> None:
        meta = PersistentMapMeta.from_dict(MAP_META_RAW)
        zone = meta.zone_by_id("z1")
        assert zone is not None
        assert zone.name == "Kitchen"

    def test_zone_by_id_not_found(self) -> None:
        meta = PersistentMapMeta.from_dict(MAP_META_RAW)
        assert meta.zone_by_id("z99") is None

    def test_zone_by_name_found(self) -> None:
        meta = PersistentMapMeta.from_dict(MAP_META_RAW)
        zone = meta.zone_by_name("living room")  # case-insensitive
        assert zone is not None
        assert zone.id == "z2"

    def test_zone_by_name_not_found(self) -> None:
        meta = PersistentMapMeta.from_dict(MAP_META_RAW)
        assert meta.zone_by_name("Garage") is None

    def test_from_dict_no_zones(self) -> None:
        meta = PersistentMapMeta.from_dict({"id": "pm-002"})
        assert meta.zones == []
        assert meta.zones_definition_last_updated_date is None


# ---------------------------------------------------------------------------
# PersistentMap
# ---------------------------------------------------------------------------

PERSISTENT_MAP_RAW: dict = {
    "id": "pm-001",
    "name": "Ground Floor",
    "offset": {"x": 500.0, "y": -200.0},
    "presentationMap": {"data": "base64pngdata=="},
    "zonesDefinition": {"persistentMapDisplayOrientation": 90},
    "zones": [{"id": "z1", "name": "Kitchen"}],
}


class TestPersistentMap:
    def test_from_dict_full(self) -> None:
        pm = PersistentMap.from_dict(PERSISTENT_MAP_RAW)
        assert pm.id == "pm-001"
        assert pm.name == "Ground Floor"
        assert pm.offset_x == pytest.approx(500.0)
        assert pm.offset_y == pytest.approx(-200.0)
        assert pm.presentation_map_data == "base64pngdata=="
        assert pm.display_orientation == 90
        assert len(pm.zones) == 1

    def test_from_dict_minimal(self) -> None:
        pm = PersistentMap.from_dict({})
        assert pm.id == ""
        assert pm.offset_x is None
        assert pm.offset_y is None
        assert pm.presentation_map_data is None
        assert pm.display_orientation == 0
        assert pm.zones == []

    def test_from_dict_no_offset_values(self) -> None:
        pm = PersistentMap.from_dict({"offset": {}})
        assert pm.offset_x is None
        assert pm.offset_y is None

    def test_from_dict_non_int_orientation_defaults_to_zero(self) -> None:
        pm = PersistentMap.from_dict(
            {"zonesDefinition": {"persistentMapDisplayOrientation": "90"}}
        )
        assert pm.display_orientation == 0


# ---------------------------------------------------------------------------
# ZoneDustBreakdown
# ---------------------------------------------------------------------------

DUST_ENTRIES = [
    {"name": "extraFine", "weight": 0.5},
    {"name": "fine", "weight": 1.2},
    {"name": "medium", "weight": 0.3},
    {"name": "large", "weight": 0.1},
    {"name": "other", "weight": 0.0},
    {"name": "total", "weight": 2.1},
]


class TestZoneDustBreakdown:
    def test_from_list_full(self) -> None:
        bd = ZoneDustBreakdown.from_list(DUST_ENTRIES)
        assert bd.extra_fine == pytest.approx(0.5)
        assert bd.fine == pytest.approx(1.2)
        assert bd.medium == pytest.approx(0.3)
        assert bd.large == pytest.approx(0.1)
        assert bd.other == pytest.approx(0.0)
        assert bd.total == pytest.approx(2.1)

    def test_from_list_missing_classes_default_to_zero(self) -> None:
        bd = ZoneDustBreakdown.from_list([])
        assert bd.extra_fine == 0.0
        assert bd.total == 0.0

    def test_from_list_skips_invalid_entries(self) -> None:
        bd = ZoneDustBreakdown.from_list([None, "bad", {"weight": 1.0}])  # type: ignore[list-item]
        assert bd.extra_fine == 0.0


# ---------------------------------------------------------------------------
# ZonePrediction
# ---------------------------------------------------------------------------


class TestZonePrediction:
    def test_from_dict(self) -> None:
        pred = ZonePrediction.from_dict(
            {"zoneId": "z1", "zoneDustMilligrams": DUST_ENTRIES}
        )
        assert pred.zone_id == "z1"
        assert pred.dust.total == pytest.approx(2.1)

    def test_from_dict_no_zone_id(self) -> None:
        pred = ZonePrediction.from_dict({})
        assert pred.zone_id == ""


# ---------------------------------------------------------------------------
# RecommendedCleanMap
# ---------------------------------------------------------------------------

RECOMMENDED_RAW: dict = {
    "persistentMapId": "pm-001",
    "zonePredictions": [
        {
            "zoneId": "z1",
            "zoneDustMilligrams": [
                {"name": "total", "weight": 3.0},
            ],
        },
        {
            "zoneId": "z2",
            "zoneDustMilligrams": [
                {"name": "total", "weight": 1.5},
            ],
        },
        {
            "zoneId": "z3",
            "zoneDustMilligrams": [
                {"name": "total", "weight": 5.0},
            ],
        },
    ],
}


class TestRecommendedCleanMap:
    def test_from_dict(self) -> None:
        rcm = RecommendedCleanMap.from_dict(RECOMMENDED_RAW)
        assert rcm.persistent_map_id == "pm-001"
        assert len(rcm.zone_predictions) == 3

    def test_sorted_by_dust(self) -> None:
        rcm = RecommendedCleanMap.from_dict(RECOMMENDED_RAW)
        sorted_preds = rcm.sorted_by_dust()
        totals = [p.dust.total for p in sorted_preds]
        assert totals == sorted(totals, reverse=True)
        assert sorted_preds[0].zone_id == "z3"

    def test_from_dict_empty_predictions(self) -> None:
        rcm = RecommendedCleanMap.from_dict({"persistentMapId": "pm-002"})
        assert rcm.zone_predictions == []
        assert rcm.sorted_by_dust() == []
