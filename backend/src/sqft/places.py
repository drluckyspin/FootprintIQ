"""Google Places API client. OWNED BY LANE A.

Used for chain retail / branded warehouses where the brand name + address yields a
much better lat/lon than the generic Geocoding API (which often lands in parking lots).

Wave 0 stub.
"""

from __future__ import annotations

import httpx

from sqft.schema import GeocodeResult, NormalizedAddress

PLACES_TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACES_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"


async def text_search(
    client: httpx.AsyncClient,
    api_key: str,
    address: NormalizedAddress,
) -> dict | None:
    """Call Places Text Search with `"{chain_token} {address}"` query.

    Lane A MUST:
      - Include `region=us` and `type=...` where applicable
      - Return raw response dict (or None if no results)
    """
    raise NotImplementedError("Lane A: implement text_search")


async def place_details(
    client: httpx.AsyncClient,
    api_key: str,
    place_id: str,
) -> dict:
    """Fetch Place Details for `place_id` to get precise geometry/location."""
    raise NotImplementedError("Lane A: implement place_details")


def to_geocode_result(
    address: NormalizedAddress,
    text_search_response: dict,
    details_response: dict | None,
) -> GeocodeResult:
    """Map raw Places JSON into a GeocodeResult."""
    raise NotImplementedError("Lane A: implement to_geocode_result")
