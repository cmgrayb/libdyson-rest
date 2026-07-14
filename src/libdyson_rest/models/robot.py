"""
Robot vacuum (Vis Nav) model classes for libdyson-rest.

These models represent cloud data structures returned by the Dyson API for
robot vacuum devices (360 Vis Nav, 360 Heurist, 360 Eye).

Endpoints covered:
- GET /v2/{serial}/clean-maps                          → list[CleanRecord]
- GET /v1/app/{serial}/persistent-map-metadata         → list[PersistentMapMeta]
- GET /v1/app/{serial}/persistent-maps/{id}            → PersistentMap
- GET /v1/app/{serial}/recommended-cleans              → list[RecommendedCleanMap]
- GET /v1/mapvisualizer/devices/{serial}/map/{mapId}   → bytes (PNG/JPEG)
- PUT /v1/app/{serial}/{mapId}/zones/{zoneId}/zone-behaviours

Utilities:
- decode_dust_map(raw_bytes)  → ProtobufMapData  (zlib+protobuf S3 dust map)
"""

from __future__ import annotations

import base64 as _base64
import struct as _struct
import zlib as _zlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, cast

from ..types import (
    CleanFaultDict,
    CleanRecordDict,
    CleanZoneDict,
    CleanZoneSettingsDict,
    PersistentMapDict,
    PersistentMapMetaDict,
    RecommendedCleanMapDict,
    ZoneMetaDict,
)

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _png_count_opaque_pixels(png_bytes: bytes) -> int:
    """Count non-background pixels in a PNG byte string.

    Supports all five PNG filter types and color types 0 (Greyscale), 2 (RGB),
    3 (Indexed), 4 (Grey+Alpha), and 6 (RGBA), with bit depths 1, 2, 4, 8,
    and 16.  Non-interlaced only.

    For RGBA and Grey+Alpha images, "non-background" means alpha > 0.
    For all other color types, any pixel with at least one non-zero sample
    is counted as foreground.  For sub-byte depths (1, 2, 4) this means any
    sample whose value is non-zero (e.g. a set bit in a 1-bit mask).

    Raises:
        ValueError: If the bytes are not a valid PNG, use interlacing, or
            use an unsupported bit depth.
    """
    if png_bytes[:8] != _PNG_SIGNATURE:
        raise ValueError("Not a valid PNG: bad signature")

    # --- parse chunks -------------------------------------------------------
    idat_chunks: list[bytes] = []
    width = height = bit_depth = color_type = interlace = 0
    pos = 8
    while pos + 12 <= len(png_bytes):
        (length,) = _struct.unpack_from(">I", png_bytes, pos)
        chunk_type = png_bytes[pos + 4 : pos + 8]
        chunk_data = png_bytes[pos + 8 : pos + 8 + length]
        pos += 12 + length  # length + type(4) + data + crc(4)

        if chunk_type == b"IHDR":
            width, height = _struct.unpack_from(">II", chunk_data)
            bit_depth = chunk_data[8]
            color_type = chunk_data[9]
            interlace = chunk_data[12]
        elif chunk_type == b"IDAT":
            idat_chunks.append(chunk_data)
        elif chunk_type == b"IEND":
            break

    if interlace:
        raise ValueError("Interlaced PNG images are not supported")

    # --- determine stride and bytes-per-pixel for filter reconstruction -----
    # color_type: 0=Greyscale, 2=RGB, 3=Indexed, 4=Grey+Alpha, 6=RGBA
    if bit_depth >= 8:
        channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color_type, 1)
        bpp = (bit_depth // 8) * channels  # bytes per pixel
        stride = width * bpp  # bytes per row, excluding the filter byte
    elif bit_depth in (1, 2, 4):
        # Sub-byte packed format (valid for color types 0 and 3 in the PNG spec).
        # PNG filter reconstruction operates at byte granularity, so bpp = 1.
        bpp = 1
        stride = (width * bit_depth + 7) // 8
    else:
        raise ValueError(f"Unsupported bit depth: {bit_depth}")

    # --- decompress all IDAT chunks together --------------------------------
    raw = _zlib.decompress(b"".join(idat_chunks))

    # --- reconstruct scanlines and count non-background pixels --------------
    count = 0
    prev_row = bytearray(stride)

    for row_idx in range(height):
        base = row_idx * (stride + 1)
        filter_type = raw[base]
        row = bytearray(raw[base + 1 : base + 1 + stride])

        # Reconstruct the row according to the PNG filter type.
        if filter_type == 1:  # Sub
            for i in range(bpp, stride):
                row[i] = (row[i] + row[i - bpp]) & 0xFF
        elif filter_type == 2:  # Up
            for i in range(stride):
                row[i] = (row[i] + prev_row[i]) & 0xFF
        elif filter_type == 3:  # Average
            for i in range(stride):
                a = row[i - bpp] if i >= bpp else 0
                row[i] = (row[i] + (a + prev_row[i]) // 2) & 0xFF
        elif filter_type == 4:  # Paeth
            for i in range(stride):
                a = row[i - bpp] if i >= bpp else 0
                b = prev_row[i]
                c = prev_row[i - bpp] if i >= bpp else 0
                pa = abs(b - c)
                pb = abs(a - c)
                pc = abs(a + b - 2 * c)
                pr = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                row[i] = (row[i] + pr) & 0xFF
        # filter_type == 0 (None): row is already correct.

        # Count non-background pixels.
        if bit_depth < 8:
            # Packed sub-byte samples, stored MSB-first within each byte.
            mask = (1 << bit_depth) - 1
            pixels_per_byte = 8 // bit_depth
            pixel_num = 0
            for byte in row:
                for slot in range(pixels_per_byte - 1, -1, -1):
                    if pixel_num >= width:
                        break
                    if (byte >> (slot * bit_depth)) & mask:
                        count += 1
                    pixel_num += 1
        elif color_type == 6:  # RGBA: alpha channel is index 3
            for i in range(0, stride, bpp):
                if row[i + 3] > 0:
                    count += 1
        elif color_type == 4:  # Grey+Alpha: alpha channel is index 1
            for i in range(0, stride, bpp):
                if row[i + 1] > 0:
                    count += 1
        else:  # Greyscale, RGB, Indexed: any non-zero byte is foreground
            for i in range(0, stride, bpp):
                if any(row[i + j] for j in range(bpp)):
                    count += 1

        prev_row = row

    return count


class CleaningStrategy(str, Enum):
    """Per-zone cleaning strategy for the 360 Vis Nav."""

    AUTO = "auto"
    QUICK = "quick"
    QUIET = "quiet"
    BOOST = "boost"


@dataclass
class CleanTimelineEvent:
    """One event in a cleaning run's timeline."""

    time: str | None
    event_name: str | None
    fault_location: str | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CleanTimelineEvent:
        """Create a CleanTimelineEvent from a raw dict."""
        return cls(
            time=data.get("time"),
            event_name=data.get("eventName"),
            fault_location=data.get("faultLocation"),
        )


@dataclass
class CleanedFootprint:
    """Cleaned-area footprint associated with one cleaning run."""

    data: str | None
    """Base64-encoded PNG of the cleaned-area bitmap."""
    area: float | None
    """Cleaned area in square metres."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CleanedFootprint:
        """Create a CleanedFootprint from a raw dict."""
        raw_area = data.get("area") or data.get("cleanedArea")
        area: float | None = (
            float(raw_area) if isinstance(raw_area, int | float) else None
        )
        return cls(
            data=data.get("data"),
            area=area,
        )

    def compute_area_m2(
        self,
        tile_resolution_mm: float = 20.0,
        *,
        resolution_mm: float | None = None,
    ) -> float | None:
        """Compute the cleaned area in square metres from the footprint bitmap.

        Decodes the base64-encoded PNG stored in ``data`` and counts the
        non-background pixels.  Each pixel represents a
        ``tile_resolution_mm × tile_resolution_mm`` mm² cell on the floor.

        Args:
            tile_resolution_mm: Millimetres per pixel in the Vis Nav footprint
                bitmap (default: 20, which is the standard Dyson resolution).
            resolution_mm: Deprecated alias for ``tile_resolution_mm``.
                Provided for backward compatibility; prefer
                ``tile_resolution_mm``.

        Returns:
            Cleaned area in square metres, or ``None`` if ``data`` is absent
            or cannot be decoded.
        """
        if resolution_mm is not None:
            tile_resolution_mm = resolution_mm
        if not self.data:
            return None
        try:
            png_bytes = _base64.b64decode(self.data)
            pixel_count = _png_count_opaque_pixels(png_bytes)
            tile_m = tile_resolution_mm / 1000.0
            return pixel_count * tile_m * tile_m
        except Exception:
            return None


@dataclass
class DustMapData:
    """Aggregated dust-density map for one cleaning run.

    The ``dust_data`` list contains base64-encoded, zlib-compressed byte
    arrays; each byte encodes the dust level for one (resolution × resolution)
    mm² cell of the map at 0–scaleFactor scale.
    """

    width: int
    height: int
    resolution: int
    """Millimetres per pixel (typically 20 for the Vis Nav)."""
    dust_data: list[dict[str, Any]]
    """Raw dustData entries from the API response."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DustMapData:
        """Create a DustMapData from a raw dict."""
        return cls(
            width=int(data.get("width", 0)),
            height=int(data.get("height", 0)),
            resolution=int(data.get("resolution") or 20),
            dust_data=list(data.get("dustData") or []),
        )


@dataclass
class CleanMapPosition:
    """World-coordinate origin of a dust-map crop (mm)."""

    x: float
    y: float

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CleanMapPosition:
        """Create a CleanMapPosition from a raw dict."""
        return cls(x=float(data.get("x", 0)), y=float(data.get("y", 0)))


@dataclass
class CleanZoneSettings:
    """Per-zone cleaning settings from a v2 clean record."""

    cleaning_strategy: str | None
    clean_type: str | None
    water_level: str | None
    mop_passes: int | None
    dry_passes: int | None

    @classmethod
    def from_dict(cls, data: CleanZoneSettingsDict) -> CleanZoneSettings:
        """Create a CleanZoneSettings from a raw dict."""
        raw: dict[str, Any] = dict(data)
        return cls(
            cleaning_strategy=raw.get("cleaningStrategy"),
            clean_type=raw.get("cleanType"),
            water_level=raw.get("waterLevel"),
            mop_passes=raw.get("mopPasses"),
            dry_passes=raw.get("dryPasses"),
        )


@dataclass
class CleanZone:
    """One zone entry from a v2 clean record."""

    id: str
    name: str | None
    type: str | None
    is_selected: bool
    settings: CleanZoneSettings | None
    name_location: CleanMapPosition | None

    @classmethod
    def from_dict(cls, data: CleanZoneDict) -> CleanZone:
        """Create a CleanZone from a raw dict."""
        raw: dict[str, Any] = dict(data)
        settings_raw = raw.get("settings")
        settings = (
            CleanZoneSettings.from_dict(cast(CleanZoneSettingsDict, settings_raw))
            if isinstance(settings_raw, dict)
            else None
        )
        name_loc_raw = raw.get("nameLocation")
        name_location = (
            CleanMapPosition.from_dict(name_loc_raw)
            if isinstance(name_loc_raw, dict)
            else None
        )
        return cls(
            id=str(raw.get("id", "")),
            name=raw.get("name"),
            type=raw.get("type"),
            is_selected=bool(raw.get("isSelected", False)),
            settings=settings,
            name_location=name_location,
        )


@dataclass
class CleanFault:
    """A fault event reported during a v2 clean run."""

    type: str
    x: float
    y: float

    @classmethod
    def from_dict(cls, data: CleanFaultDict) -> CleanFault:
        """Create a CleanFault from a raw dict."""
        raw: dict[str, Any] = dict(data)
        return cls(
            type=str(raw.get("type", "")),
            x=float(raw.get("x", 0)),
            y=float(raw.get("y", 0)),
        )


@dataclass
class CleaningProgramme:
    """Zone-clean programme embedded in a clean record."""

    persistent_map_id: str | None
    ordered_zones: list[str]
    unordered_zones: list[str]
    zones_definition_last_updated_date: str | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CleaningProgramme:
        """Create a CleaningProgramme from a raw dict."""
        return cls(
            persistent_map_id=data.get("persistentMapId"),
            ordered_zones=[str(z) for z in (data.get("orderedZones") or [])],
            unordered_zones=[str(z) for z in (data.get("unorderedZones") or [])],
            zones_definition_last_updated_date=data.get(
                "zonesDefinitionLastUpdatedDate"
            ),
        )

    @property
    def is_zone_clean(self) -> bool:
        """Return True if this programme targets specific zones."""
        return bool(self.ordered_zones or self.unordered_zones)


@dataclass
class CleanRecord:
    """One entry from GET /v2/{serial}/clean-maps.

    Represents a single historical cleaning run returned by the Dyson cloud.
    The v2 API returns a ``{"data": [...]}`` envelope and a substantially
    different field set from the v1 schema — see field-level notes below.

    v1-only fields (``timeline``, ``cleaned_footprint``, ``cleaning_programme``,
    ``clean_map_position``, ``dust_map``) are ``None`` / empty for v2 responses.
    v2-only fields (``start_time_epoch``, ``end_time_epoch``, ``download_url``,
    ``zones``, ``faults``, etc.) are ``None`` / empty for v1 responses.
    """

    # --- fields present in both schema versions ---
    clean_id: str | None
    persistent_map_id: str | None
    """ID of the persistent map associated with this run (if any)."""

    # --- v1 fields (None / empty for v2 responses) ---
    sequence_number: int | None
    timeline: list[CleanTimelineEvent]
    cleaned_footprint: CleanedFootprint | None
    cleaning_programme: CleaningProgramme | None
    clean_map_position: CleanMapPosition | None
    """World-coordinate origin of the dust-map crop within the floor plan."""
    dust_map: DustMapData | None

    # --- v2 fields (None / empty for v1 responses) ---
    start_time_epoch: int | None = None
    """Unix epoch timestamp of the run start (v2 only)."""
    end_time_epoch: int | None = None
    """Unix epoch timestamp of the run end (v2 only)."""
    clean_duration: int | None = None
    """Duration of the run in seconds (v2 only)."""
    area_cleaned: float | None = None
    """Cleaned area in square metres (v2 only)."""
    download_url: str | None = None
    """Pre-signed S3 URL for detailed map data (v2 only, expires ~15 min).

    Note:
        This URL has a short TTL (``X-Amz-Expires=900`` seconds).  Do not
        cache it long-term.  Re-call ``get_clean_maps()`` to obtain a fresh
        URL before each map image fetch.
    """
    is_spot_clean: bool | None = None
    """True when the run was a spot-clean, False for full/zone runs (v2 only)."""
    orientation: int | None = None
    """Map orientation in degrees (v2 only)."""
    start_battery: float | None = None
    """Battery level at run start, as a percentage (v2 only)."""
    end_battery: float | None = None
    """Battery level at run end, as a percentage (v2 only)."""
    zones: list[CleanZone] = field(default_factory=list)
    """Per-zone settings for this run (v2 only)."""
    spot_zones: list[Any] = field(default_factory=list)
    """Spot-clean zone entries (v2 only, empty for full/zone runs)."""
    dock_location: Any | None = None
    """Dock location at time of run (v2 only, often None)."""
    faults: list[CleanFault] = field(default_factory=list)
    """Fault events recorded during the run (v2 only)."""
    firmware_version: str | None = None
    """Firmware version string at time of run (v2 only, often None)."""

    @classmethod
    def from_dict(cls, data: CleanRecordDict) -> CleanRecord:
        """Create a CleanRecord from an API response dict.

        Handles both v1 (bare-list) and v2 (``data``-wrapped) schemas
        transparently.  Fields absent from the received schema are left as
        ``None`` or an empty list.
        """
        raw: dict[str, Any] = dict(data)

        # --- v1 fields ---
        timeline = [
            CleanTimelineEvent.from_dict(e)
            for e in (raw.get("cleanTimeline") or [])
            if isinstance(e, dict)
        ]

        footprint_raw = raw.get("cleanedFootprint")
        footprint = (
            CleanedFootprint.from_dict(footprint_raw)
            if isinstance(footprint_raw, dict)
            else None
        )

        programme_raw = raw.get("cleaningProgramme")
        programme = (
            CleaningProgramme.from_dict(programme_raw)
            if isinstance(programme_raw, dict)
            else None
        )

        # persistent_map_id: v1 nests it inside persistentMap.id;
        # v2 exposes it as a top-level persistentMapId.
        persistent_map_raw = raw.get("persistentMap") or {}
        persistent_map_id: str | None = (
            persistent_map_raw.get("id")
            if isinstance(persistent_map_raw, dict)
            else None
        ) or raw.get("persistentMapId")

        position_raw = (
            persistent_map_raw.get("cleanMapPosition")
            if isinstance(persistent_map_raw, dict)
            else None
        )
        position = (
            CleanMapPosition.from_dict(position_raw)
            if isinstance(position_raw, dict)
            else None
        )

        dust_map_raw = raw.get("dustMap")
        dust_map = (
            DustMapData.from_dict(dust_map_raw)
            if isinstance(dust_map_raw, dict)
            else None
        )

        seq = raw.get("sequenceNumber")

        # --- v2 fields ---
        zones = [
            CleanZone.from_dict(cast(CleanZoneDict, z))
            for z in (raw.get("zones") or [])
            if isinstance(z, dict)
        ]
        spot_zones = list(raw.get("spotZones") or [])
        faults = [
            CleanFault.from_dict(cast(CleanFaultDict, f))
            for f in (raw.get("faults") or [])
            if isinstance(f, dict)
        ]

        start_time_raw = raw.get("startTime")
        end_time_raw = raw.get("endTime")
        clean_duration_raw = raw.get("cleanDuration")
        area_cleaned_raw = raw.get("areaCleaned")
        start_battery_raw = raw.get("startBattery")
        end_battery_raw = raw.get("endBattery")
        orientation_raw = raw.get("orientation")
        is_spot_clean_raw = raw.get("isSpotClean")

        return cls(
            clean_id=raw.get("cleanId"),
            persistent_map_id=persistent_map_id,
            sequence_number=int(seq) if seq is not None else None,
            timeline=timeline,
            cleaned_footprint=footprint,
            cleaning_programme=programme,
            clean_map_position=position,
            dust_map=dust_map,
            start_time_epoch=(
                int(start_time_raw) if start_time_raw is not None else None
            ),
            end_time_epoch=(int(end_time_raw) if end_time_raw is not None else None),
            clean_duration=(
                int(clean_duration_raw) if clean_duration_raw is not None else None
            ),
            area_cleaned=(
                float(area_cleaned_raw) if area_cleaned_raw is not None else None
            ),
            download_url=raw.get("downloadUrl"),
            is_spot_clean=(
                bool(is_spot_clean_raw) if is_spot_clean_raw is not None else None
            ),
            orientation=(int(orientation_raw) if orientation_raw is not None else None),
            start_battery=(
                float(start_battery_raw) if start_battery_raw is not None else None
            ),
            end_battery=(
                float(end_battery_raw) if end_battery_raw is not None else None
            ),
            zones=zones,
            spot_zones=spot_zones,
            dock_location=raw.get("dockLocation"),
            faults=faults,
            firmware_version=raw.get("firmwareVersion"),
        )

    @property
    def start_time(self) -> str | None:
        """Earliest timestamp from the v1 timeline, or None.

        For v2 responses use ``start_time_epoch`` instead.
        """
        times = [e.time for e in self.timeline if e.time]
        return min(times) if times else None

    @property
    def end_time(self) -> str | None:
        """Latest timestamp from the v1 timeline, or None.

        For v2 responses use ``end_time_epoch`` instead.
        """
        times = [e.time for e in self.timeline if e.time]
        return max(times) if times else None

    @property
    def is_zone_clean(self) -> bool:
        """Return True if this was a zone-targeted clean.

        Checks the v1 ``cleaning_programme`` and the v2 ``zones`` list.
        """
        # v1: cleaning programme with one or more zones
        if (
            self.cleaning_programme is not None
            and self.cleaning_programme.is_zone_clean
        ):
            return True
        # v2: zones list is populated and the run is not a spot clean
        return bool(self.zones and self.is_spot_clean is False)

    @property
    def clean_type(self) -> str:
        """Clean type string matching the Dyson API vocabulary.

        Returns ``"zoneConfigured"`` when a cleaning programme with one or
        more zones exists, ``"global"`` for a standard whole-home run.
        """
        if self.is_zone_clean:
            return "zoneConfigured"
        return "global"


@dataclass
class ZoneMeta:
    """Metadata for one zone within a persistent map."""

    id: str
    name: str | None
    icon: str | None
    area: float | None

    @classmethod
    def from_dict(cls, data: ZoneMetaDict) -> ZoneMeta:
        """Create a ZoneMeta from a raw dict."""
        raw: dict[str, Any] = dict(data)
        area_raw = raw.get("area")
        return cls(
            id=str(raw.get("id", "")),
            name=raw.get("name"),
            icon=raw.get("icon"),
            area=float(area_raw) if isinstance(area_raw, int | float) else None,
        )


@dataclass
class PersistentMapMeta:
    """One entry from GET /v1/app/{serial}/persistent-map-metadata.

    Contains map identification, zone list with human-readable names, the
    ``zones_definition_last_updated_date`` timestamp that must be included in
    zone-clean MQTT payloads so the device honours the request, and the
    ``last_visited`` timestamp of the map's most recent robot activity.
    """

    id: str
    name: str | None
    zones_definition_last_updated_date: str | None
    zones: list[ZoneMeta]
    is_current_map: bool = False
    last_visited: str | None = None

    @classmethod
    def from_dict(cls, data: PersistentMapMetaDict) -> PersistentMapMeta:
        """Create a PersistentMapMeta from an API response dict."""
        raw: dict[str, Any] = dict(data)
        zones = [
            ZoneMeta.from_dict(cast(ZoneMetaDict, z))
            for z in (raw.get("zones") or [])
            if isinstance(z, dict)
        ]
        return cls(
            id=str(raw.get("id", "")),
            name=raw.get("name"),
            zones_definition_last_updated_date=raw.get(
                "zonesDefinitionLastUpdatedDate"
            ),
            zones=zones,
            is_current_map=bool(raw.get("isCurrentMap", False)),
            last_visited=raw.get("lastVisited"),
        )

    def zone_by_id(self, zone_id: str) -> ZoneMeta | None:
        """Return the zone with the given ID, or None."""
        return next((z for z in self.zones if z.id == zone_id), None)

    def zone_by_name(self, name: str) -> ZoneMeta | None:
        """Return the zone matching ``name`` (case-insensitive), or None."""
        name_lower = name.lower()
        return next(
            (z for z in self.zones if (z.name or "").lower() == name_lower), None
        )


@dataclass
class PersistentMap:
    """Full persistent map from GET /v1/app/{serial}/persistent-maps/{id}.

    Includes the presentation-map PNG (base64-encoded), the zones definition
    with display orientation, and the world-coordinate offset used to align
    the dust-map crop correctly onto the floor plan.
    """

    id: str
    name: str | None
    offset_x: float | None
    """World-coordinate X origin of the presentation map (mm)."""
    offset_y: float | None
    """World-coordinate Y origin of the presentation map (mm)."""
    presentation_map_data: str | None
    """Base64-encoded PNG of the annotated floor plan."""
    display_orientation: int
    """Clockwise rotation in degrees to match the MyDyson app view."""
    zones: list[ZoneMeta]

    @classmethod
    def from_dict(cls, data: PersistentMapDict) -> PersistentMap:
        """Create a PersistentMap from an API response dict."""
        raw: dict[str, Any] = dict(data)

        offset_raw = raw.get("offset") or {}
        offset_x = (
            float(offset_raw["x"])
            if isinstance(offset_raw.get("x"), int | float)
            else None
        )
        offset_y = (
            float(offset_raw["y"])
            if isinstance(offset_raw.get("y"), int | float)
            else None
        )

        pres_map = raw.get("presentationMap") or {}
        pres_data = pres_map.get("data") if isinstance(pres_map, dict) else None

        zones_def = raw.get("zonesDefinition") or {}
        orientation_raw = (
            zones_def.get("persistentMapDisplayOrientation")
            if isinstance(zones_def, dict)
            else None
        )
        orientation = int(orientation_raw) if isinstance(orientation_raw, int) else 0

        zones = [
            ZoneMeta.from_dict(cast(ZoneMetaDict, z))
            for z in (raw.get("zones") or [])
            if isinstance(z, dict)
        ]

        return cls(
            id=str(raw.get("id", "")),
            name=raw.get("name"),
            offset_x=offset_x,
            offset_y=offset_y,
            presentation_map_data=pres_data,
            display_orientation=orientation,
            zones=zones,
        )


@dataclass
class ZoneDustBreakdown:
    """Dust mass (mg) broken down by particle class for one zone."""

    extra_fine: float
    fine: float
    medium: float
    large: float
    other: float
    total: float
    raw: dict[str, float] = field(default_factory=dict)

    @classmethod
    def from_list(cls, entries: list[dict[str, Any]]) -> ZoneDustBreakdown:
        """Build a breakdown from the ``zoneDustMilligrams`` entry list."""
        by_name = {
            e["name"]: float(e.get("weight", 0))
            for e in entries
            if isinstance(e, dict) and e.get("name")
        }
        return cls(
            extra_fine=by_name.get("extraFine", 0.0),
            fine=by_name.get("fine", 0.0),
            medium=by_name.get("medium", 0.0),
            large=by_name.get("large", 0.0),
            other=by_name.get("other", 0.0),
            total=by_name.get("total", 0.0),
            raw=by_name,
        )


@dataclass
class ZonePrediction:
    """Dust prediction for one zone within a recommended-cleans response."""

    zone_id: str
    dust: ZoneDustBreakdown

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ZonePrediction:
        """Create a ZonePrediction from a raw API dict."""
        return cls(
            zone_id=str(data.get("zoneId", "")),
            dust=ZoneDustBreakdown.from_list(data.get("zoneDustMilligrams") or []),
        )


@dataclass
class RecommendedCleanMap:
    """One entry from GET /v1/app/{serial}/recommended-cleans."""

    persistent_map_id: str
    zone_predictions: list[ZonePrediction]

    @classmethod
    def from_dict(cls, data: RecommendedCleanMapDict) -> RecommendedCleanMap:
        """Create a RecommendedCleanMap from an API response dict."""
        raw: dict[str, Any] = dict(data)
        predictions = [
            ZonePrediction.from_dict(p)
            for p in (raw.get("zonePredictions") or [])
            if isinstance(p, dict)
        ]
        return cls(
            persistent_map_id=str(raw.get("persistentMapId", "")),
            zone_predictions=predictions,
        )

    def sorted_by_dust(self) -> list[ZonePrediction]:
        """Return zone predictions sorted by total dust (dirtiest first)."""
        return sorted(self.zone_predictions, key=lambda p: p.dust.total, reverse=True)


# ---------------------------------------------------------------------------
# Minimal protobuf wire-format parser (no external dependency)
# ---------------------------------------------------------------------------


def _proto_read_varint(data: bytes, pos: int) -> tuple[int, int]:
    """Read a protobuf varint from *data* starting at *pos*.

    Returns ``(value, new_pos)``.

    Raises:
        ValueError: If the varint is truncated before the stop bit.
    """
    result = 0
    shift = 0
    while pos < len(data):
        byte = data[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            return result, pos
        shift += 7
    raise ValueError("Truncated varint in protobuf data")


def _proto_parse_fields(data: bytes) -> dict[int, list[Any]]:
    """Parse the top-level fields of a protobuf binary message.

    Handles wire types 0 (varint), 1 (64-bit), 2 (length-delimited), and
    5 (32-bit).  An unknown wire type terminates parsing.  Length-delimited
    values are returned as ``bytes``; varints and fixed-width integers as
    ``int``.

    Returns:
        Mapping of ``field_number -> [value, ...]`` (list to support repeated
        fields).
    """
    fields: dict[int, list[Any]] = {}
    pos = 0
    while pos < len(data):
        try:
            tag, pos = _proto_read_varint(data, pos)
        except ValueError:
            break
        field_number = tag >> 3
        wire_type = tag & 0x7

        try:
            value: Any
            if wire_type == 0:  # varint
                value, pos = _proto_read_varint(data, pos)
            elif wire_type == 1:  # 64-bit little-endian
                if pos + 8 > len(data):
                    break
                value = int.from_bytes(data[pos : pos + 8], "little")
                pos += 8
            elif wire_type == 2:  # length-delimited
                length, pos = _proto_read_varint(data, pos)
                if pos + length > len(data):
                    break
                value = data[pos : pos + length]
                pos += length
            elif wire_type == 5:  # 32-bit little-endian
                if pos + 4 > len(data):
                    break
                value = int.from_bytes(data[pos : pos + 4], "little")
                pos += 4
            else:
                break  # unknown wire type — cannot continue safely
        except ValueError:
            break

        fields.setdefault(field_number, []).append(value)

    return fields


@dataclass
class ProtobufMapData:
    """Decoded zlib+protobuf dust-map binary from the S3 ``downloadUrl``.

    Instances are created by :func:`decode_dust_map` after downloading the
    binary payload from ``CleanRecord.download_url`` (v2 ``clean-maps``
    endpoint).

    Observed on the Dyson Spot+Scrub (RB05-AA, product type ``804A``,
    firmware 34.x) where ``message_type == 21``.

    Attributes:
        message_type: Integer type discriminator from the outer protobuf
            envelope (field 1).  Value ``21`` identifies the RB05 session
            format.
        start_time: Unix timestamp of the session start (field 2.1), or
            ``None`` if not present in the binary.
        end_time: Unix timestamp of the session end (field 2.2), or ``None``
            if not present in the binary.
        session_id: Session UUID hex string from the inner ``SessionUUID``
            message (field 2.7.1), e.g. ``"fce99365-3756-5655-…"``, or
            ``None`` if not present.
        raw_payload: Full decompressed protobuf payload bytes, for advanced
            client-side decoding of robot path, coverage, and obstacle data.
    """

    message_type: int
    start_time: int | None
    end_time: int | None
    session_id: str | None
    raw_payload: bytes


def decode_dust_map(raw_bytes: bytes) -> ProtobufMapData:
    """Decode a zlib-compressed Protocol Buffer dust-map binary from S3.

    Download the binary from ``CleanRecord.download_url`` using any HTTP
    client, then pass the response body to this function.  The format is
    zlib default compression (magic bytes ``0x78 0x9C``) wrapping a protobuf
    message with the following top-level structure (reverse-engineered from
    the MyDyson APK v6.4 smali bytecode)::

        message CleanSession {
          field 1  (varint) = message_type       # 21 for RB05/804A
          field 2  (bytes)  = SessionHeader {
            field 1 (varint) = start_time_epoch
            field 2 (varint) = end_time_epoch
            field 7 (bytes)  = SessionUUID {
              field 1 (bytes) = session_uuid_hex_string
            }
          }
          // remaining bytes: robot path, coverage, obstacle data
        }

    Note:
        The protobuf ``.proto`` definition is not published by Dyson.  Fields
        beyond the header (robot path, coverage, obstacle data) are captured
        in ``ProtobufMapData.raw_payload`` for callers that perform their own
        further decoding.

    Args:
        raw_bytes: Raw bytes fetched from ``CleanRecord.download_url``.

    Returns:
        :class:`ProtobufMapData` with decoded header fields and the full
        decompressed payload.

    Raises:
        ValueError: If *raw_bytes* cannot be decompressed or does not contain
            a valid protobuf varint tag.
    """
    try:
        payload = _zlib.decompress(raw_bytes)
    except _zlib.error as exc:
        raise ValueError(f"Failed to decompress dust map: {exc}") from exc

    top = _proto_parse_fields(payload)

    # Field 1 (varint): message_type
    mt_vals = top.get(1, [])
    message_type = int(mt_vals[0]) if mt_vals else 0

    start_time: int | None = None
    end_time: int | None = None
    session_id: str | None = None

    # Field 2 (bytes): SessionHeader
    header_vals = top.get(2, [])
    if header_vals and isinstance(header_vals[0], bytes):
        header = _proto_parse_fields(header_vals[0])

        st_vals = header.get(1, [])
        if st_vals:
            start_time = int(st_vals[0])

        et_vals = header.get(2, [])
        if et_vals:
            end_time = int(et_vals[0])

        # Field 7 (bytes): SessionUUID → field 1 (bytes): uuid string
        uuid_vals = header.get(7, [])
        if uuid_vals and isinstance(uuid_vals[0], bytes):
            inner = _proto_parse_fields(uuid_vals[0])
            str_vals = inner.get(1, [])
            if str_vals and isinstance(str_vals[0], bytes):
                session_id = str_vals[0].decode("utf-8", errors="replace")

    return ProtobufMapData(
        message_type=message_type,
        start_time=start_time,
        end_time=end_time,
        session_id=session_id,
        raw_payload=payload,
    )
