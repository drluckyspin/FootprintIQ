"""Geocoder orchestration. OWNED BY LANE A."""

from __future__ import annotations

import asyncio
import hashlib
import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx

from sqft.config import GeocoderConfig
from sqft.places import place_details, text_search, to_geocode_result
from sqft.schema import (
    GeocodeResult,
    GeocoderPrecision,
    GeocoderProvider,
    NormalizedAddress,
)

GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"

_PRECISION_RANK = {
    GeocoderPrecision.ROOFTOP: 0,
    GeocoderPrecision.RANGE_INTERPOLATED: 1,
    GeocoderPrecision.GEOMETRIC_CENTER: 2,
    GeocoderPrecision.APPROXIMATE: 3,
    GeocoderPrecision.UNKNOWN: 4,
}

PLACES_COST_PER_1K = 32.0
GEOCODING_COST_PER_1K = 5.0


class GeocodeCache:
    """SQLite-backed cache keyed on address_key."""

    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS geocode_cache (
                address_key TEXT PRIMARY KEY,
                provider TEXT NOT NULL,
                lat REAL,
                lon REAL,
                precision TEXT,
                formatted_address TEXT,
                place_id TEXT,
                raw_response_json TEXT,
                raw_response_hash TEXT,
                status TEXT NOT NULL,
                error TEXT,
                created_at_utc TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def get(self, address_key: str) -> GeocodeResult | None:
        row = self._conn.execute(
            "SELECT provider, lat, lon, precision, formatted_address, place_id, "
            "raw_response_hash, status, error FROM geocode_cache WHERE address_key = ?",
            (address_key,),
        ).fetchone()
        if row is None:
            return None
        provider, lat, lon, precision, formatted, place_id, rhash, status, error = row
        return GeocodeResult(
            address_key=address_key,
            lat=lat,
            lon=lon,
            precision=GeocoderPrecision(precision) if precision else GeocoderPrecision.UNKNOWN,
            provider=GeocoderProvider(provider),
            place_id=place_id,
            formatted_address=formatted,
            raw_response_hash=rhash,
            status=status,
            error=error,
        )

    def put(
        self,
        address_key: str,
        result: GeocodeResult,
        raw_response: dict[str, Any],
    ) -> None:
        raw_json = json.dumps(raw_response, sort_keys=True)
        rhash = hashlib.sha256(raw_json.encode()).hexdigest()
        self._conn.execute(
            """
            INSERT OR REPLACE INTO geocode_cache
            (address_key, provider, lat, lon, precision, formatted_address, place_id,
             raw_response_json, raw_response_hash, status, error, created_at_utc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                address_key,
                result.provider.value,
                result.lat,
                result.lon,
                result.precision.value,
                result.formatted_address,
                result.place_id,
                raw_json,
                rhash,
                result.status,
                result.error,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self._conn.commit()

    def has(self, address_key: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM geocode_cache WHERE address_key = ?",
            (address_key,),
        ).fetchone()
        return row is not None


class _RateLimiter:
    def __init__(self, qps: int) -> None:
        self._interval = 1.0 / max(qps, 1)
        self._lock = asyncio.Lock()
        self._last = 0.0

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            wait = self._interval - (now - self._last)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last = time.monotonic()


def _min_precision(config: GeocoderConfig) -> GeocoderPrecision:
    return GeocoderPrecision(config.min_acceptable_precision)


def _meets_precision(result: GeocodeResult, config: GeocoderConfig) -> bool:
    minimum = _min_precision(config)
    return _PRECISION_RANK[result.precision] <= _PRECISION_RANK[minimum]


def _geocoding_precision(location_type: str) -> GeocoderPrecision:
    mapping = {
        "ROOFTOP": GeocoderPrecision.ROOFTOP,
        "RANGE_INTERPOLATED": GeocoderPrecision.RANGE_INTERPOLATED,
        "GEOMETRIC_CENTER": GeocoderPrecision.GEOMETRIC_CENTER,
        "APPROXIMATE": GeocoderPrecision.APPROXIMATE,
    }
    return mapping.get(location_type.upper(), GeocoderPrecision.UNKNOWN)


async def _geocode_google(
    client: httpx.AsyncClient,
    api_key: str,
    address: NormalizedAddress,
) -> tuple[GeocodeResult, dict[str, Any]]:
    params = {"address": address.address_input, "key": api_key, "region": "us"}
    url = f"{GEOCODING_URL}?{urlencode(params)}"
    resp = await client.get(url)
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != "OK" or not data.get("results"):
        return (
            GeocodeResult(
                address_key=address.address_key,
                provider=GeocoderProvider.GOOGLE_GEOCODING,
                status="failed",
                error=data.get("status", "ZERO_RESULTS"),
            ),
            data,
        )
    top = data["results"][0]
    loc = top["geometry"]["location"]
    precision = _geocoding_precision(top["geometry"].get("location_type", "APPROXIMATE"))
    return (
        GeocodeResult(
            address_key=address.address_key,
            lat=loc["lat"],
            lon=loc["lng"],
            precision=precision,
            provider=GeocoderProvider.GOOGLE_GEOCODING,
            formatted_address=top.get("formatted_address"),
            status="ok",
        ),
        data,
    )


async def _geocode_one(
    client: httpx.AsyncClient,
    address: NormalizedAddress,
    config: GeocoderConfig,
    cache: GeocodeCache,
    limiter: _RateLimiter,
    places_key: str,
    geocode_key: str,
) -> GeocodeResult:
    cached = cache.get(address.address_key)
    if cached is not None:
        cached.provider = GeocoderProvider.CACHE
        return cached

    last_error: Exception | None = None
    for attempt in range(config.retry_attempts):
        try:
            await limiter.acquire()
            raw_payload: dict[str, Any]
            if address.chain_token:
                ts = await text_search(client, places_key, address)
                if ts is None:
                    result = GeocodeResult(
                        address_key=address.address_key,
                        provider=GeocoderProvider.GOOGLE_PLACES,
                        status="failed",
                        error="no places results",
                    )
                    cache.put(address.address_key, result, {"results": []})
                    return result
                place_id = ts["results"][0]["place_id"]
                await limiter.acquire()
                details = await place_details(client, places_key, place_id)
                result = to_geocode_result(address, ts, details)
                raw_payload = {"text_search": ts, "details": details}
            else:
                result, raw_payload = await _geocode_google(client, geocode_key, address)

            if not _meets_precision(result, config) and result.status == "ok":
                result.status = "low_precision"

            cache.put(address.address_key, result, raw_payload)
            return result
        except (httpx.HTTPStatusError, httpx.TransportError) as exc:
            last_error = exc
            if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code not in (
                429,
                500,
                502,
                503,
                504,
            ):
                break
            await asyncio.sleep(2**attempt)

    result = GeocodeResult(
        address_key=address.address_key,
        provider=GeocoderProvider.GOOGLE_GEOCODING,
        status="failed",
        error=str(last_error) if last_error else "unknown error",
    )
    cache.put(address.address_key, result, {"error": result.error})
    return result


async def geocode_batch(
    addresses: list[NormalizedAddress],
    config: GeocoderConfig,
    cache: GeocodeCache,
    *,
    places_api_key: str | None = None,
    geocoding_api_key: str | None = None,
) -> list[GeocodeResult]:
    import os

    places_key = places_api_key or os.environ.get(config.places_api_key_env, "")
    geocode_key = geocoding_api_key or os.environ.get(config.api_key_env, "")
    limiter = _RateLimiter(config.rate_limit_qps)
    sem = asyncio.Semaphore(config.concurrency)

    async def _run(addr: NormalizedAddress) -> GeocodeResult:
        async with sem:
            async with httpx.AsyncClient(timeout=30.0) as client:
                return await _geocode_one(
                    client, addr, config, cache, limiter, places_key, geocode_key
                )

    return list(await asyncio.gather(*[_run(a) for a in addresses]))


def estimate_cost_usd(
    addresses: list[NormalizedAddress],
    config: GeocoderConfig,
    cache: GeocodeCache,
) -> dict[str, float]:
    places_calls = 0
    geocoding_calls = 0
    for addr in addresses:
        if cache.has(addr.address_key):
            continue
        if addr.chain_token:
            places_calls += 2  # text search + details
        else:
            geocoding_calls += 1

    places_cost = (places_calls / 1000.0) * PLACES_COST_PER_1K
    geocoding_cost = (geocoding_calls / 1000.0) * GEOCODING_COST_PER_1K
    total = places_cost + geocoding_cost
    return {
        "places_calls": float(places_calls),
        "geocoding_calls": float(geocoding_calls),
        "places_cost_usd": places_cost,
        "geocoding_cost_usd": geocoding_cost,
        "total_usd": total,
    }
