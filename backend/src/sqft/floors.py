"""Floor count resolution. OWNED BY LANE B."""

from __future__ import annotations

from sqft.config import FloorsConfig
from sqft.schema import FloorsSource

DEFAULT_FLOORS_BY_SUBTYPE: dict[str, int] = {
    "warehouse": 1,
    "industrial": 1,
    "logistics": 1,
    "manufacturing": 1,
    "retail": 1,
    "supermarket": 1,
    "shopping_centre": 1,
    "office": 3,
    "commercial": 2,
}

SINGLE_STORY_SUBTYPES: frozenset[str] = frozenset(
    {"warehouse", "industrial", "logistics", "manufacturing", "supermarket", "shopping_centre"}
)


def _subtype_default(subtype: str | None, config: FloorsConfig) -> tuple[int, FloorsSource]:
    if subtype and subtype in DEFAULT_FLOORS_BY_SUBTYPE:
        return DEFAULT_FLOORS_BY_SUBTYPE[subtype], FloorsSource.SUBTYPE_DEFAULT
    return config.default, FloorsSource.DEFAULT


def _from_height(
    height_m: float,
    subtype: str | None,
    config: FloorsConfig,
) -> tuple[int, FloorsSource] | None:
    if subtype in SINGLE_STORY_SUBTYPES:
        return 1, FloorsSource.SUBTYPE_DEFAULT
    if height_m > config.max_height_meters_for_inference:
        # Treat very large heights as parse artifacts — still cap at max_floors rather than ignoring.
        return config.max_floors_cap, FloorsSource.OVERTURE_HEIGHT
    floors = max(1, round(height_m / config.height_per_floor_meters))
    floors = min(floors, config.max_floors_cap)
    return floors, FloorsSource.OVERTURE_HEIGHT


def _from_num_floors(num_floors: int, config: FloorsConfig) -> tuple[int, FloorsSource]:
    floors = min(max(1, num_floors), config.max_floors_cap)
    return floors, FloorsSource.OVERTURE_NUM_FLOORS


def resolve_floors(
    num_floors: int | None,
    height_m: float | None,
    subtype: str | None,
    config: FloorsConfig,
) -> tuple[int, FloorsSource]:
    """Return (floors_used, FloorsSource)."""
    for source in config.prefer:
        if source == "num_floors" and num_floors is not None:
            return _from_num_floors(num_floors, config)
        if source == "height" and height_m is not None:
            height_result = _from_height(height_m, subtype, config)
            if height_result is not None:
                return height_result
    return _subtype_default(subtype, config)
