"""Parcel-polygon provider. INTERFACE ONLY IN V1. OWNED BY LANE B.

v1 ships `NullParcelProvider` (always returns None). A real RegridParcelProvider
or CountyGISParcelProvider can be added later without touching spatial_join.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from shapely.geometry.base import BaseGeometry


@dataclass(frozen=True)
class ParcelPolygon:
    """A single parcel polygon in EPSG:4326."""

    parcel_id: str
    geometry: BaseGeometry  # shapely polygon in EPSG:4326
    source: str  # e.g. "regrid", "king_county_gis"


@runtime_checkable
class ParcelProvider(Protocol):
    """Lookup a parcel polygon containing the given point."""

    def get(self, lat: float, lon: float) -> ParcelPolygon | None: ...


class NullParcelProvider:
    """v1 default — always returns None. Spatial join falls back to k-NN with class filter."""

    def get(self, lat: float, lon: float) -> ParcelPolygon | None:
        return None


# Future: RegridParcelProvider(Path(...)).get(...), CountyGISParcelProvider, etc.
