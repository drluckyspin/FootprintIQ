"""Polygon area computation in EPSG:5070 (CONUS Albers Equal Area). OWNED BY LANE B.

CRITICAL: never compute .area in EPSG:4326 — it returns square degrees.
"""

from __future__ import annotations

from functools import lru_cache

from pyproj import Transformer
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform

SQM_PER_SQFT = 10.7639


@lru_cache(maxsize=1)
def _to_5070() -> Transformer:
    return Transformer.from_crs("EPSG:4326", "EPSG:5070", always_xy=True)


def polygon_area_sqft(polygon_4326: BaseGeometry) -> float:
    """Compute the area of `polygon_4326` (shapely, EPSG:4326) in square feet via EPSG:5070."""
    projected = transform(_to_5070().transform, polygon_4326)
    return float(projected.area * SQM_PER_SQFT)
