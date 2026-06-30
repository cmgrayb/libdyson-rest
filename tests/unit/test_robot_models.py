"""Unit tests for Vis Nav robot vacuum model classes."""

import base64
import struct
import zlib

import pytest

from libdyson_rest.models import (
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
    RecommendedCleanMap,
    ZoneDustBreakdown,
    ZoneMeta,
    ZonePrediction,
)

# ---------------------------------------------------------------------------
# PNG test helpers
# ---------------------------------------------------------------------------


def _make_rgba_png(pixels: list[list[tuple[int, int, int, int]]]) -> bytes:
    """Build a minimal RGBA PNG from a 2-D list of (R, G, B, A) tuples."""
    height = len(pixels)
    width = len(pixels[0]) if pixels else 0

    raw = bytearray()
    for row in pixels:
        raw.append(0)  # filter type: None
        for r, g, b, a in row:
            raw.extend([r, g, b, a])

    def chunk(name: bytes, data: bytes) -> bytes:
        payload = name + data
        crc = zlib.crc32(payload) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + payload + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(bytes(raw)))
        + chunk(b"IEND", b"")
    )


def _b64_png(pixels: list[list[tuple[int, int, int, int]]]) -> str:
    """Return a base64-encoded RGBA PNG string."""
    return base64.b64encode(_make_rgba_png(pixels)).decode()


def _make_1bit_greyscale_png(rows: list[list[int]]) -> bytes:
    """Build a minimal 1-bit greyscale PNG from a 2-D list of 0/1 values.

    Each inner list is one row; each value is 0 (black) or 1 (white).
    Rows need not be a multiple of 8 wide — the last byte is zero-padded.
    """
    height = len(rows)
    width = len(rows[0]) if rows else 0

    def chunk(name: bytes, data: bytes) -> bytes:
        payload = name + data
        crc = zlib.crc32(payload) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + payload + struct.pack(">I", crc)

    raw = bytearray()
    for row in rows:
        raw.append(0)  # filter type: None
        # Pack pixels MSB-first, 8 pixels per byte, zero-pad the last byte.
        byte = 0
        bit_pos = 7
        for px in row:
            if px:
                byte |= 1 << bit_pos
            bit_pos -= 1
            if bit_pos < 0:
                raw.append(byte)
                byte = 0
                bit_pos = 7
        if bit_pos < 7:  # flush any partial byte
            raw.append(byte)

    ihdr = struct.pack(
        ">IIBBBBB",
        width,
        height,
        1,
        0,
        0,
        0,
        0,  # bit_depth=1, color_type=0
    )
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(bytes(raw)))
        + chunk(b"IEND", b"")
    )


def _b64_1bit_png(rows: list[list[int]]) -> str:
    """Return a base64-encoded 1-bit greyscale PNG string."""
    return base64.b64encode(_make_1bit_greyscale_png(rows)).decode()


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

    # --- compute_area_m2 ------------------------------------------------

    def test_compute_area_m2_no_data(self) -> None:
        fp = CleanedFootprint(data=None, area=None)
        assert fp.compute_area_m2() is None

    def test_compute_area_m2_invalid_base64_returns_none(self) -> None:
        fp = CleanedFootprint(data="not-valid-base64!!!", area=None)
        assert fp.compute_area_m2() is None

    def test_compute_area_m2_not_a_png_returns_none(self) -> None:
        fp = CleanedFootprint(
            data=base64.b64encode(b"this is not a png").decode(), area=None
        )
        assert fp.compute_area_m2() is None

    def test_compute_area_m2_all_transparent(self) -> None:
        # 2×2 image where all pixels are fully transparent
        png_b64 = _b64_png(
            [
                [(0, 0, 0, 0), (0, 0, 0, 0)],
                [(0, 0, 0, 0), (0, 0, 0, 0)],
            ]
        )
        fp = CleanedFootprint(data=png_b64, area=None)
        assert fp.compute_area_m2() == pytest.approx(0.0)

    def test_compute_area_m2_fully_opaque(self) -> None:
        # 3×2 image, all 6 pixels opaque → 6 × (0.02 m)² = 0.0024 m²
        png_b64 = _b64_png(
            [
                [(255, 0, 0, 255), (255, 0, 0, 255), (255, 0, 0, 255)],
                [(255, 0, 0, 255), (255, 0, 0, 255), (255, 0, 0, 255)],
            ]
        )
        fp = CleanedFootprint(data=png_b64, area=None)
        assert fp.compute_area_m2() == pytest.approx(6 * 0.02 * 0.02)

    def test_compute_area_m2_partial_coverage(self) -> None:
        # 2×2 image: 3 opaque + 1 transparent → 3 × 0.0004 m²
        png_b64 = _b64_png(
            [
                [(255, 255, 255, 255), (0, 0, 0, 0)],
                [(255, 0, 0, 255), (0, 255, 0, 255)],
            ]
        )
        fp = CleanedFootprint(data=png_b64, area=None)
        assert fp.compute_area_m2() == pytest.approx(3 * 0.0004)

    def test_compute_area_m2_custom_resolution(self) -> None:
        # 1×1 opaque pixel at 10 mm/px → 0.01 × 0.01 = 0.0001 m²
        png_b64 = _b64_png([[(100, 100, 100, 200)]])
        fp = CleanedFootprint(data=png_b64, area=None)
        assert fp.compute_area_m2(tile_resolution_mm=10.0) == pytest.approx(0.0001)

    def test_compute_area_m2_default_resolution_is_20mm(self) -> None:
        # 1×1 opaque → 0.02 × 0.02 = 0.0004 m²
        png_b64 = _b64_png([[(50, 50, 50, 128)]])
        fp = CleanedFootprint(data=png_b64, area=None)
        assert fp.compute_area_m2() == pytest.approx(0.0004)

    # --- 1-bit greyscale PNG (Vis Nav cloud masks) --------------------------

    def test_compute_area_m2_1bit_png_all_set(self) -> None:
        # 8×2 1-bit greyscale: all pixels set → 16 × (0.02)² = 0.0064 m²
        png_b64 = _b64_1bit_png([[1] * 8, [1] * 8])
        fp = CleanedFootprint(data=png_b64, area=None)
        assert fp.compute_area_m2() == pytest.approx(16 * 0.02 * 0.02)

    def test_compute_area_m2_1bit_png_all_clear(self) -> None:
        # 8×2 1-bit greyscale: no pixels set → 0.0 m²
        png_b64 = _b64_1bit_png([[0] * 8, [0] * 8])
        fp = CleanedFootprint(data=png_b64, area=None)
        assert fp.compute_area_m2() == pytest.approx(0.0)

    def test_compute_area_m2_1bit_png_partial(self) -> None:
        # 8×2: top row all set (8), bottom row all clear (0) → 8 pixels
        png_b64 = _b64_1bit_png([[1] * 8, [0] * 8])
        fp = CleanedFootprint(data=png_b64, area=None)
        assert fp.compute_area_m2() == pytest.approx(8 * 0.02 * 0.02)

    def test_compute_area_m2_1bit_png_non_multiple_of_8_width(self) -> None:
        # 5-pixel wide, 1-bit greyscale: 3 set + 2 clear per row, 2 rows → 6
        png_b64 = _b64_1bit_png([[1, 1, 1, 0, 0], [1, 1, 1, 0, 0]])
        fp = CleanedFootprint(data=png_b64, area=None)
        assert fp.compute_area_m2() == pytest.approx(6 * 0.02 * 0.02)

    # --- backward-compat resolution_mm kwarg --------------------------------

    def test_compute_area_m2_resolution_mm_compat(self) -> None:
        # resolution_mm=10 → tile_m = 0.01 → 1 pixel = 0.01 × 0.01 = 0.0001 m²
        png_b64 = _b64_png([[(100, 100, 100, 200)]])
        fp = CleanedFootprint(data=png_b64, area=None)
        assert fp.compute_area_m2(resolution_mm=10.0) == pytest.approx(0.0001)


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

    def test_clean_type_zone_configured(self) -> None:
        record = CleanRecord.from_dict(CLEAN_RECORD_FULL)
        assert record.clean_type == "zoneConfigured"

    def test_clean_type_global_no_programme(self) -> None:
        record = CleanRecord.from_dict({})
        assert record.clean_type == "global"

    def test_clean_type_global_programme_no_zones(self) -> None:
        data = dict(CLEAN_RECORD_FULL)
        data["cleaningProgramme"] = {
            "persistentMapId": "map-001",
            "orderedZones": [],
            "unorderedZones": [],
        }
        record = CleanRecord.from_dict(data)
        assert record.clean_type == "global"


# v2 fixture — matches the real RB05-AA (product type 804A) response shape
CLEAN_RECORD_V2: dict = {
    "persistentMapId": "1780280259",
    "cleanId": "fce99365-3756-5655-5356-444130343735",
    "isSpotClean": False,
    "orientation": 0,
    "startTime": 1780779744,
    "endTime": 1780784253,
    "cleanDuration": 76,
    "areaCleaned": 37.76,
    "downloadUrl": "https://example.s3.eu-west-1.amazonaws.com/map.bin?X-Amz-Expires=900",
    "zones": [
        {
            "id": "10",
            "name": "Living room",
            "type": "livingRoom",
            "isSelected": True,
            "settings": {
                "cleaningStrategy": "auto",
                "cleanType": "vacuum",
                "waterLevel": "low",
                "mopPasses": 1,
                "dryPasses": 1,
            },
            "nameLocation": {"x": 1.825, "y": -1.725},
        }
    ],
    "spotZones": [],
    "dockLocation": None,
    "startBattery": 100.0,
    "endBattery": 56.0,
    "faults": [{"type": "2108", "x": -0.449, "y": 0.003}],
    "firmwareVersion": None,
}


# ---------------------------------------------------------------------------
# CleanZoneSettings
# ---------------------------------------------------------------------------


class TestCleanZoneSettings:
    def test_from_dict_full(self) -> None:
        settings = CleanZoneSettings.from_dict(
            {
                "cleaningStrategy": "auto",
                "cleanType": "vacuum",
                "waterLevel": "low",
                "mopPasses": 1,
                "dryPasses": 2,
            }
        )
        assert settings.cleaning_strategy == "auto"
        assert settings.clean_type == "vacuum"
        assert settings.water_level == "low"
        assert settings.mop_passes == 1
        assert settings.dry_passes == 2

    def test_from_dict_empty(self) -> None:
        settings = CleanZoneSettings.from_dict({})
        assert settings.cleaning_strategy is None
        assert settings.clean_type is None
        assert settings.water_level is None
        assert settings.mop_passes is None
        assert settings.dry_passes is None


# ---------------------------------------------------------------------------
# CleanZone
# ---------------------------------------------------------------------------


class TestCleanZone:
    def test_from_dict_full(self) -> None:
        zone = CleanZone.from_dict(CLEAN_RECORD_V2["zones"][0])
        assert zone.id == "10"
        assert zone.name == "Living room"
        assert zone.type == "livingRoom"
        assert zone.is_selected is True
        assert zone.settings is not None
        assert zone.settings.cleaning_strategy == "auto"
        assert zone.name_location is not None
        assert zone.name_location.x == pytest.approx(1.825)
        assert zone.name_location.y == pytest.approx(-1.725)

    def test_from_dict_no_settings(self) -> None:
        zone = CleanZone.from_dict({"id": "z1"})
        assert zone.id == "z1"
        assert zone.name is None
        assert zone.type is None
        assert zone.is_selected is False
        assert zone.settings is None
        assert zone.name_location is None

    def test_from_dict_settings_none_when_not_dict(self) -> None:
        zone = CleanZone.from_dict({"id": "z1", "settings": None})
        assert zone.settings is None


# ---------------------------------------------------------------------------
# CleanFault
# ---------------------------------------------------------------------------


class TestCleanFault:
    def test_from_dict_full(self) -> None:
        fault = CleanFault.from_dict({"type": "2108", "x": -0.449, "y": 0.003})
        assert fault.type == "2108"
        assert fault.x == pytest.approx(-0.449)
        assert fault.y == pytest.approx(0.003)

    def test_from_dict_defaults(self) -> None:
        fault = CleanFault.from_dict({})
        assert fault.type == ""
        assert fault.x == pytest.approx(0.0)
        assert fault.y == pytest.approx(0.0)

    def test_type_coerced_to_str(self) -> None:
        fault = CleanFault.from_dict({"type": 2108})
        assert fault.type == "2108"


# ---------------------------------------------------------------------------
# CleanRecord — v2 schema tests
# ---------------------------------------------------------------------------


class TestCleanRecordV2:
    def test_from_dict_v2_full(self) -> None:
        record = CleanRecord.from_dict(CLEAN_RECORD_V2)
        assert record.clean_id == "fce99365-3756-5655-5356-444130343735"
        assert record.persistent_map_id == "1780280259"
        assert record.start_time_epoch == 1780779744
        assert record.end_time_epoch == 1780784253
        assert record.clean_duration == 76
        assert record.area_cleaned == pytest.approx(37.76)
        assert (
            record.download_url
            == "https://example.s3.eu-west-1.amazonaws.com/map.bin?X-Amz-Expires=900"
        )
        assert record.is_spot_clean is False
        assert record.orientation == 0
        assert record.start_battery == pytest.approx(100.0)
        assert record.end_battery == pytest.approx(56.0)
        assert record.dock_location is None
        assert record.firmware_version is None

    def test_from_dict_v2_zones(self) -> None:
        record = CleanRecord.from_dict(CLEAN_RECORD_V2)
        assert len(record.zones) == 1
        zone = record.zones[0]
        assert zone.id == "10"
        assert zone.name == "Living room"
        assert zone.is_selected is True
        assert zone.settings is not None
        assert zone.settings.clean_type == "vacuum"
        assert zone.settings.water_level == "low"
        assert zone.settings.mop_passes == 1

    def test_from_dict_v2_faults(self) -> None:
        record = CleanRecord.from_dict(CLEAN_RECORD_V2)
        assert len(record.faults) == 1
        fault = record.faults[0]
        assert fault.type == "2108"
        assert fault.x == pytest.approx(-0.449)
        assert fault.y == pytest.approx(0.003)

    def test_from_dict_v2_spot_zones_empty(self) -> None:
        record = CleanRecord.from_dict(CLEAN_RECORD_V2)
        assert record.spot_zones == []

    def test_v2_v1_fields_are_empty(self) -> None:
        """v1-only fields should be None/empty when parsing a v2 record."""
        record = CleanRecord.from_dict(CLEAN_RECORD_V2)
        assert record.sequence_number is None
        assert record.timeline == []
        assert record.cleaned_footprint is None
        assert record.cleaning_programme is None
        assert record.clean_map_position is None
        assert record.dust_map is None

    def test_v2_start_time_end_time_properties_return_none(self) -> None:
        """The v1 timeline-based properties return None for v2-only records."""
        record = CleanRecord.from_dict(CLEAN_RECORD_V2)
        assert record.start_time is None
        assert record.end_time is None

    def test_v2_is_zone_clean_true_when_zones_non_empty(self) -> None:
        record = CleanRecord.from_dict(CLEAN_RECORD_V2)
        assert record.is_zone_clean is True
        assert record.clean_type == "zoneConfigured"

    def test_v2_is_zone_clean_false_for_spot_clean(self) -> None:
        data = dict(CLEAN_RECORD_V2)
        data["isSpotClean"] = True
        record = CleanRecord.from_dict(data)
        assert record.is_zone_clean is False

    def test_v2_is_zone_clean_false_when_no_zones(self) -> None:
        data = dict(CLEAN_RECORD_V2)
        data["zones"] = []
        record = CleanRecord.from_dict(data)
        assert record.is_zone_clean is False

    def test_v2_persistent_map_id_from_top_level(self) -> None:
        """v2 exposes persistentMapId at the top level (not nested)."""
        record = CleanRecord.from_dict({"persistentMapId": "pm-42"})
        assert record.persistent_map_id == "pm-42"

    def test_v2_minimal_record_defaults(self) -> None:
        """All v2 optional fields default to None / empty list."""
        record = CleanRecord.from_dict({})
        assert record.start_time_epoch is None
        assert record.end_time_epoch is None
        assert record.clean_duration is None
        assert record.area_cleaned is None
        assert record.download_url is None
        assert record.is_spot_clean is None
        assert record.orientation is None
        assert record.start_battery is None
        assert record.end_battery is None
        assert record.zones == []
        assert record.spot_zones == []
        assert record.faults == []
        assert record.firmware_version is None


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
