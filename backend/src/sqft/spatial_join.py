"""Point-in-polygon / nearest-building spatial join. OWNED BY LANE B.

Decides the chosen building for each geocoded point.

Wave 0 stub.
"""

from __future__ import annotations

from pathlib import Path

from sqft.config import SpatialConfig
from sqft.parcels import ParcelProvider
from sqft.schema import BuildingMatch, GeocodeResult


def join_points_to_buildings(
    geocoded: list[GeocodeResult],
    footprints_parquet: Path,
    location_id_lookup: dict[str, list[str]],
    config: SpatialConfig,
    parcels: ParcelProvider,
    location_types: dict[str, str] | None = None,
) -> list[BuildingMatch]:
    """Match each geocoded point to a building.

    Lane B MUST follow this decision order:

    1. If `parcels.get(lat, lon)` returns a parcel:
         enumerate buildings `within` the parcel polygon
         -> apply config.multi_building_rule
         -> match_method = WITHIN_PARCEL

    2. Else try point `within` polygon (geopandas .sjoin or shapely .contains):
         if exactly one -> WITHIN
         if multiple -> apply multi_building_rule, multi_building_count = N

    3. Else nearest-K (config.nearest_k) within config.search_buffer_meters:
         filter by class in {commercial, industrial, retail} if location_type is informative
         else largest
         -> match_method = NEAREST_WITHIN_BUFFER, set flag_nearest_fallback later

    4. Else match_method = UNMATCHED

    Always populate `candidates` (sorted by distance, marking is_chosen=True on the winner).
    """
    raise NotImplementedError("Lane B: implement join_points_to_buildings")
