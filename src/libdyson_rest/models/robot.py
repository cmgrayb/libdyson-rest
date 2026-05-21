"""
Robot vacuum (Vis Nav) model classes for libdyson-rest.

These models represent cloud data structures returned by the Dyson API for
robot vacuum devices (360 Vis Nav, 360 Heurist, 360 Eye).

Endpoints covered:
- GET /v1/{serial}/clean-maps          → list[CleanRecord]
- GET /v1/app/{serial}/persistent-map-metadata → list[PersistentMapMeta]
- GET /v1/app/{serial}/persistent-maps/{id}    → PersistentMap
- GET /v1/app/{serial}/recommended-cleans      → list[RecommendedCleanMap]
- PUT /v1/app/{serial}/{mapId}/zones/{zoneId}/zone-behaviours
"""

from __future__ import annotations

import base64 as _base64
import struct as _struct
import zlib as _zlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, cast

from ..types import (
    CleanRecordDict,
    PersistentMapDict,
    PersistentMapMetaDict,
    RecommendedCleanMapDict,
    ZoneMetaDict,
)

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _png_count_opaque_pixels(png_bytes: bytes) -> int:
    """Count non-background pixels in a PNG byte string.

    Supports all five PNG filter types and color types 0 (Greyscale), 2 (RGB),
    3 (Indexed), 4 (Grey+Alpha), and 6 (RGBA), with bit depth ≥ 8.
    Non-interlaced only.

    For RGBA and Grey+Alpha images, "non-background" means alpha > 0.
    For all other color types, any pixel with at least one non-zero byte
    is counted as foreground.

    Raises:
        ValueError: If the bytes are not a valid PNG, use interlacing, or
            use a bit depth below 8.
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
    if bit_depth < 8:
        raise ValueError(f"Bit depth {bit_depth} < 8 is not supported")

    # --- determine bytes per pixel ------------------------------------------
    # color_type: 0=Greyscale, 2=RGB, 3=Indexed, 4=Grey+Alpha, 6=RGBA
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color_type, 1)
    bpp = (bit_depth // 8) * channels  # bytes per pixel

    # --- decompress all IDAT chunks together --------------------------------
    raw = _zlib.decompress(b"".join(idat_chunks))

    # --- reconstruct scanlines and count non-background pixels --------------
    stride = width * bpp  # bytes per row, excluding the leading filter byte
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
        if color_type == 6:  # RGBA: alpha channel is index 3
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

    def compute_area_m2(self, tile_resolution_mm: float = 20.0) -> float | None:
        """Compute the cleaned area in square metres from the footprint bitmap.

        Decodes the base64-encoded PNG stored in ``data`` and counts the
        non-background pixels.  Each pixel represents a
        ``tile_resolution_mm × tile_resolution_mm`` mm² cell on the floor.

        Args:
            tile_resolution_mm: Millimetres per pixel in the Vis Nav footprint
                bitmap (default: 20, which is the standard Dyson resolution).

        Returns:
            Cleaned area in square metres, or ``None`` if ``data`` is absent
            or cannot be decoded.
        """
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
    """One entry from GET /v1/{serial}/clean-maps.

    Represents a single historical cleaning run returned by the Dyson cloud.
    The ``dust_map`` field is only populated when the endpoint is called with
    ``dustMap=total``.
    """

    clean_id: str | None
    sequence_number: int | None
    timeline: list[CleanTimelineEvent]
    cleaned_footprint: CleanedFootprint | None
    cleaning_programme: CleaningProgramme | None
    persistent_map_id: str | None
    """ID of the persistent map associated with this run (if any)."""
    clean_map_position: CleanMapPosition | None
    """World-coordinate origin of the dust-map crop within the floor plan."""
    dust_map: DustMapData | None

    @classmethod
    def from_dict(cls, data: CleanRecordDict) -> CleanRecord:
        """Create a CleanRecord from an API response dict."""
        raw: dict[str, Any] = dict(data)

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

        persistent_map_raw = raw.get("persistentMap") or {}
        persistent_map_id = (
            persistent_map_raw.get("id")
            if isinstance(persistent_map_raw, dict)
            else None
        )
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
        return cls(
            clean_id=raw.get("cleanId"),
            sequence_number=int(seq) if seq is not None else None,
            timeline=timeline,
            cleaned_footprint=footprint,
            cleaning_programme=programme,
            persistent_map_id=persistent_map_id,
            clean_map_position=position,
            dust_map=dust_map,
        )

    @property
    def start_time(self) -> str | None:
        """Earliest timestamp from the timeline, or None."""
        times = [e.time for e in self.timeline if e.time]
        return min(times) if times else None

    @property
    def end_time(self) -> str | None:
        """Latest timestamp from the timeline, or None."""
        times = [e.time for e in self.timeline if e.time]
        return max(times) if times else None

    @property
    def is_zone_clean(self) -> bool:
        """Return True if this was a zone-targeted clean."""
        return (
            self.cleaning_programme is not None
            and self.cleaning_programme.is_zone_clean
        )

    @property
    def clean_type(self) -> str:
        """Human-readable clean type string.

        Returns ``"zone_configured"`` when a cleaning programme with one or
        more zones exists, ``"global"`` for a standard whole-home run.
        """
        if self.is_zone_clean:
            return "zone_configured"
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

    Contains map identification, zone list with human-readable names, and the
    ``zones_definition_last_updated_date`` timestamp that must be included in
    zone-clean MQTT payloads so the device honours the request.
    """

    id: str
    name: str | None
    zones_definition_last_updated_date: str | None
    zones: list[ZoneMeta]

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
