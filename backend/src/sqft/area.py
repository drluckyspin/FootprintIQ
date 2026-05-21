"""Polygon area computation in EPSG:5070 (CONUS Albers Equal Area). OWNED BY LANE B.

CRITICAL: never compute .area in EPSG:4326 — it returns square degrees.

Wave 0 stub.
"""

from __future__ import annotations

from shapely.geometry.base import BaseGeometry

SQM_PER_SQFT = 10.7639


def polygon_area_sqft(polygon_4326: BaseGeometry) -> float:
    """Compute the area of `polygon_4326` (shapely, EPSG:4326) in square feet via EPSG:5070.

    Lane B MUST:
      - Reproject the geometry to EPSG:5070 (pyproj.Transformer + shapely.ops.transform,
        or geopandas .to_crs if working in a GeoDataFrame)
      - Compute .area (square meters)
      - Convert to square feet using SQM_PER_SQFT
      - Unit test against a hand-verified polygon (see tests/fixtures/expected_areas.json)
    """
    raise NotImplementedError("Lane B: implement polygon_area_sqft")
