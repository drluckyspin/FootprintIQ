"""Floor count resolution. OWNED BY LANE B.

Resolution order:
  1. Overture num_floors (if present)         -> FloorsSource.OVERTURE_NUM_FLOORS
  2. Overture height -> floors (with subtype) -> FloorsSource.OVERTURE_HEIGHT
  3. Subtype default                          -> FloorsSource.SUBTYPE_DEFAULT
  4. Global default (1)                       -> FloorsSource.DEFAULT

Wave 0 stub.
"""

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

# Subtypes that are tall single-story regardless of height (warehouses can be 12m tall and 1 floor).
SINGLE_STORY_SUBTYPES: frozenset[str] = frozenset(
    {"warehouse", "industrial", "logistics", "manufacturing", "supermarket", "shopping_centre"}
)


def resolve_floors(
    num_floors: int | None,
    height_m: float | None,
    subtype: str | None,
    config: FloorsConfig,
) -> tuple[int, FloorsSource]:
    """Return (floors_used, FloorsSource).

    Lane B MUST:
      - Respect config.prefer ordering
      - If subtype in SINGLE_STORY_SUBTYPES -> ignore height; cap at 1 floor
      - If using height: floors = max(1, round(height / config.height_per_floor_meters))
      - Cap at config.max_floors_cap (default 50) — anything higher is a parse artifact
      - If height > config.max_height_meters_for_inference -> ignore height, fall through
    """
    raise NotImplementedError("Lane B: implement resolve_floors")
