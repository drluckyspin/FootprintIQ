"""Address deduplication. OWNED BY LANE A."""

from __future__ import annotations

from sqft.schema import NormalizedAddress


def build_address_key_index(
    normalized: list[NormalizedAddress],
) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for row in normalized:
        index.setdefault(row.address_key, []).append(row.location_id)
    return index


def unique_addresses(normalized: list[NormalizedAddress]) -> list[NormalizedAddress]:
    seen: set[str] = set()
    out: list[NormalizedAddress] = []
    for row in normalized:
        if row.address_key in seen:
            continue
        seen.add(row.address_key)
        out.append(row)
    return out
