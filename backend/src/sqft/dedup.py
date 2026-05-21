"""Address deduplication. OWNED BY LANE A.

Multiple input location_ids can share an address_key (chains often have duplicate addresses).
Geocoding then runs once per unique address_key; estimates re-fan-out to all location_ids later.

Wave 0 stub.
"""

from __future__ import annotations

from sqft.schema import NormalizedAddress


def build_address_key_index(
    normalized: list[NormalizedAddress],
) -> dict[str, list[str]]:
    """Return mapping `address_key -> [location_id, ...]`.

    Lane A MUST:
      - Group by address_key
      - Preserve location_id order within each group (CSV order)
    """
    raise NotImplementedError("Lane A: implement build_address_key_index")


def unique_addresses(normalized: list[NormalizedAddress]) -> list[NormalizedAddress]:
    """Return one NormalizedAddress per unique address_key (first occurrence wins).

    Used as input to the geocoder.
    """
    raise NotImplementedError("Lane A: implement unique_addresses")
