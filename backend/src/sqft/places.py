"""Google Places API client. OWNED BY LANE A."""

from __future__ import annotations

from typing import Any

import httpx

from sqft.schema import GeocodeResult, GeocoderPrecision, GeocoderProvider, NormalizedAddress

PLACES_TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACES_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"


def _precision_from_types(types: list[str]) -> GeocoderPrecision:
    upper = {t.upper() for t in types}
    if "ROOFTOP" in upper:
        return GeocoderPrecision.ROOFTOP
    if "RANGE_INTERPOLATED" in upper:
        return GeocoderPrecision.RANGE_INTERPOLATED
    if "GEOMETRIC_CENTER" in upper:
        return GeocoderPrecision.GEOMETRIC_CENTER
    return GeocoderPrecision.APPROXIMATE


async def text_search(
    client: httpx.AsyncClient,
    api_key: str,
    address: NormalizedAddress,
) -> dict[str, Any] | None:
    query = address.address_input
    if address.chain_token:
        query = f"{address.chain_token} {query}"
    params = {"query": query, "key": api_key, "region": "us"}
    resp = await client.get(PLACES_TEXT_SEARCH_URL, params=params)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("results"):
        return None
    return data


async def place_details(
    client: httpx.AsyncClient,
    api_key: str,
    place_id: str,
) -> dict[str, Any]:
    params = {
        "place_id": place_id,
        "key": api_key,
        "fields": "geometry,formatted_address,types",
    }
    resp = await client.get(PLACES_DETAILS_URL, params=params)
    resp.raise_for_status()
    return resp.json()


def to_geocode_result(
    address: NormalizedAddress,
    text_search_response: dict[str, Any],
    details_response: dict[str, Any] | None,
) -> GeocodeResult:
    results = text_search_response.get("results") or []
    if not results:
        return GeocodeResult(
            address_key=address.address_key,
            provider=GeocoderProvider.GOOGLE_PLACES,
            status="failed",
            error="no places results",
        )

    result = results[0]
    place_id = result.get("place_id")
    loc = result.get("geometry", {}).get("location", {})
    lat = loc.get("lat")
    lon = loc.get("lng")
    formatted = result.get("formatted_address")
    precision = GeocoderPrecision.APPROXIMATE

    if details_response:
        detail = details_response.get("result") or {}
        formatted = detail.get("formatted_address") or formatted
        dloc = detail.get("geometry", {}).get("location", {})
        lat = dloc.get("lat", lat)
        lon = dloc.get("lng", lon)
        precision = _precision_from_types(detail.get("types") or [])

    return GeocodeResult(
        address_key=address.address_key,
        lat=lat,
        lon=lon,
        precision=precision,
        provider=GeocoderProvider.GOOGLE_PLACES,
        place_id=place_id,
        formatted_address=formatted,
        status="ok",
    )
