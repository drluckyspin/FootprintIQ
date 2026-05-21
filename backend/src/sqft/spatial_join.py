"""Point-in-polygon / nearest-building spatial join. OWNED BY LANE B."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pandas as pd
from pyproj import Transformer
from shapely import wkb
from shapely.geometry import Point
from shapely.ops import transform

from sqft.area import polygon_area_sqft
from sqft.config import SpatialConfig
from sqft.geocode import has_usable_coordinates
from sqft.parcels import ParcelProvider
from sqft.schema import BuildingMatch, CandidateBuilding, GeocodeResult, MatchMethod

_COMMERCIAL_CLASSES = frozenset({"commercial", "industrial", "retail"})


def _optional_str(val: object) -> str | None:
    """Coerce parquet nulls (NaN) to None for Pydantic string fields."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    return str(val)


@lru_cache(maxsize=1)
def _to_5070() -> Transformer:
    return Transformer.from_crs("EPSG:4326", "EPSG:5070", always_xy=True)


@dataclass(frozen=True)
class _FootprintRow:
    id: str
    geometry: object
    area_sqft: float
    overture_class: str | None
    overture_subtype: str | None


def _distance_m(point: Point, geometry: object) -> float:
    pt_5070 = transform(_to_5070().transform, point)
    geom_5070 = transform(_to_5070().transform, geometry)
    if geom_5070.contains(pt_5070):
        return 0.0
    return float(pt_5070.distance(geom_5070))


def _load_footprints(footprints_parquet: Path) -> list[_FootprintRow]:
    table = pd.read_parquet(footprints_parquet)
    rows: list[_FootprintRow] = []
    for rec in table.to_dict(orient="records"):
        geom = wkb.loads(rec["geometry_wkb"])
        rows.append(
            _FootprintRow(
                id=rec["id"],
                geometry=geom,
                area_sqft=polygon_area_sqft(geom),
                overture_class=_optional_str(rec.get("overture_class")),
                overture_subtype=_optional_str(rec.get("overture_subtype")),
            )
        )
    return rows


def _candidate(
    fp: _FootprintRow,
    distance_m: float,
    *,
    is_chosen: bool,
) -> CandidateBuilding:
    return CandidateBuilding(
        building_id=fp.id,
        area_sqft=fp.area_sqft,
        distance_m=distance_m,
        overture_class=fp.overture_class,
        overture_subtype=fp.overture_subtype,
        is_chosen=is_chosen,
    )


def _pick_largest(candidates: list[_FootprintRow]) -> _FootprintRow:
    return max(candidates, key=lambda fp: fp.area_sqft)


def _filter_by_location_type(
    fps: list[_FootprintRow],
    location_type: str | None,
) -> list[_FootprintRow]:
    if location_type not in {"retail", "warehouse"}:
        return fps
    filtered = [fp for fp in fps if (fp.overture_class or "").lower() in _COMMERCIAL_CLASSES]
    return filtered if filtered else fps


def _buildings_within_point(
    footprints: list[_FootprintRow],
    point: Point,
) -> list[_FootprintRow]:
    return [fp for fp in footprints if fp.geometry.contains(point)]


def _buildings_within_geometry(
    footprints: list[_FootprintRow],
    geometry: object,
) -> list[_FootprintRow]:
    return [
        fp
        for fp in footprints
        if fp.geometry.intersects(geometry) and geometry.contains(fp.geometry.centroid)
    ]


def _nearest_within_buffer(
    footprints: list[_FootprintRow],
    point: Point,
    buffer_m: float,
    nearest_k: int,
    location_type: str | None,
) -> list[tuple[_FootprintRow, float]]:
    scored: list[tuple[_FootprintRow, float]] = []
    for fp in footprints:
        dist = _distance_m(point, fp.geometry)
        if dist <= buffer_m:
            scored.append((fp, dist))
    scored.sort(key=lambda item: item[1])
    allowed_ids = {fp.id for fp in _filter_by_location_type([fp for fp, _ in scored], location_type)}
    if allowed_ids != {fp.id for fp, _ in scored}:
        scored = [(fp, dist) for fp, dist in scored if fp.id in allowed_ids]
    return scored[:nearest_k]


def _apply_multi_building_rule(
    hits: list[_FootprintRow],
    rule: str,
) -> _FootprintRow:
    if rule in {"largest", "largest_within_parcel", "sum_within_radius"}:
        return _pick_largest(hits)
    return _pick_largest(hits)


def _match_point(
    location_id: str,
    address_key: str,
    geocode: GeocodeResult,
    footprints: list[_FootprintRow],
    config: SpatialConfig,
    parcels: ParcelProvider,
    location_type: str | None,
) -> BuildingMatch:
    if not has_usable_coordinates(geocode):
        return BuildingMatch(
            location_id=location_id,
            address_key=address_key,
            match_method=MatchMethod.UNMATCHED,
            multi_building_count=0,
            candidates=[],
        )

    point = Point(geocode.lon, geocode.lat)
    parcel = parcels.get(geocode.lat, geocode.lon)
    if parcel is not None:
        within = _buildings_within_geometry(footprints, parcel.geometry)
        if within:
            chosen = _apply_multi_building_rule(within, config.multi_building_rule)
            candidates = [
                _candidate(fp, _distance_m(point, fp.geometry), is_chosen=fp.id == chosen.id)
                for fp in sorted(within, key=lambda fp: _distance_m(point, fp.geometry))
            ]
            return BuildingMatch(
                location_id=location_id,
                address_key=address_key,
                chosen_building_id=chosen.id,
                match_method=MatchMethod.WITHIN_PARCEL,
                multi_building_count=len(within),
                candidates=candidates,
            )

    within = _buildings_within_point(footprints, point)
    if len(within) == 1:
        fp = within[0]
        return BuildingMatch(
            location_id=location_id,
            address_key=address_key,
            chosen_building_id=fp.id,
            match_method=MatchMethod.WITHIN,
            multi_building_count=1,
            candidates=[_candidate(fp, 0.0, is_chosen=True)],
        )
    if len(within) > 1:
        chosen = _apply_multi_building_rule(within, config.multi_building_rule)
        candidates = [
            _candidate(fp, _distance_m(point, fp.geometry), is_chosen=fp.id == chosen.id)
            for fp in sorted(within, key=lambda fp: _distance_m(point, fp.geometry))
        ]
        return BuildingMatch(
            location_id=location_id,
            address_key=address_key,
            chosen_building_id=chosen.id,
            match_method=MatchMethod.WITHIN,
            multi_building_count=len(within),
            candidates=candidates,
        )

    nearest = _nearest_within_buffer(
        footprints,
        point,
        config.search_buffer_meters,
        config.nearest_k,
        location_type,
    )
    if nearest:
        if len(nearest) > 1 and config.multi_building_rule in {
            "largest",
            "largest_within_parcel",
        }:
            chosen_fp = _pick_largest([fp for fp, _ in nearest])
            chosen_dist = next(dist for fp, dist in nearest if fp.id == chosen_fp.id)
        else:
            chosen_fp, chosen_dist = nearest[0]
        candidates = [
            _candidate(fp, dist, is_chosen=fp.id == chosen_fp.id)
            for fp, dist in nearest
        ]
        return BuildingMatch(
            location_id=location_id,
            address_key=address_key,
            chosen_building_id=chosen_fp.id,
            match_method=MatchMethod.NEAREST_WITHIN_BUFFER,
            multi_building_count=len(nearest),
            candidates=candidates,
        )

    return BuildingMatch(
        location_id=location_id,
        address_key=address_key,
        match_method=MatchMethod.UNMATCHED,
        multi_building_count=0,
        candidates=[],
    )


def join_points_to_buildings(
    geocoded: list[GeocodeResult],
    footprints_parquet: Path,
    location_id_lookup: dict[str, list[str]],
    config: SpatialConfig,
    parcels: ParcelProvider,
    location_types: dict[str, str] | None = None,
) -> list[BuildingMatch]:
    """Match each geocoded point to a building."""
    footprints = _load_footprints(footprints_parquet)
    location_types = location_types or {}
    geocode_by_key = {g.address_key: g for g in geocoded}
    matches: list[BuildingMatch] = []

    for address_key, location_ids in location_id_lookup.items():
        geocode = geocode_by_key.get(address_key)
        if geocode is None:
            for location_id in location_ids:
                matches.append(
                    BuildingMatch(
                        location_id=location_id,
                        address_key=address_key,
                        match_method=MatchMethod.UNMATCHED,
                        multi_building_count=0,
                        candidates=[],
                    )
                )
            continue
        for location_id in location_ids:
            matches.append(
                _match_point(
                    location_id,
                    address_key,
                    geocode,
                    footprints,
                    config,
                    parcels,
                    location_types.get(location_id),
                )
            )
    return matches
