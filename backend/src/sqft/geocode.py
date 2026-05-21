"""Geocoder orchestration. OWNED BY LANE A.

Routes each NormalizedAddress to:
  - Google Places API (Text Search + Place Details) if chain_token detected
  - Google Geocoding API otherwise
  - SQLite cache wraps both — key is address_key

Wave 0 stub.
"""

from __future__ import annotations

from pathlib import Path

from sqft.config import GeocoderConfig
from sqft.schema import GeocodeResult, NormalizedAddress


class GeocodeCache:
    """SQLite-backed cache keyed on address_key.

    Lane A MUST:
      - sqlite3 with WAL mode
      - Schema: (address_key TEXT PRIMARY KEY, provider TEXT, lat REAL, lon REAL,
                 precision TEXT, formatted_address TEXT, place_id TEXT,
                 raw_response_json TEXT, raw_response_hash TEXT, created_at_utc TEXT)
      - get(address_key) -> Optional[GeocodeResult]
      - put(address_key, GeocodeResult, raw_response_json: dict) -> None
    """

    def __init__(self, path: Path) -> None:
        self.path = path

    def get(self, address_key: str) -> GeocodeResult | None:
        raise NotImplementedError("Lane A: implement GeocodeCache.get")

    def put(
        self,
        address_key: str,
        result: GeocodeResult,
        raw_response: dict,
    ) -> None:
        raise NotImplementedError("Lane A: implement GeocodeCache.put")


async def geocode_batch(
    addresses: list[NormalizedAddress],
    config: GeocoderConfig,
    cache: GeocodeCache,
) -> list[GeocodeResult]:
    """Async-batch geocode addresses, respecting concurrency + rate limits.

    Lane A MUST:
      - Use httpx.AsyncClient with asyncio.Semaphore(config.concurrency)
      - Token-bucket rate limiter at config.rate_limit_qps
      - Retry with exponential backoff on 5xx and 429 (config.retry_attempts)
      - Skip cache hits; persist new results into the cache
      - Reject results worse than config.min_acceptable_precision -> status="low_precision"
      - Never raise on per-row failure: produce GeocodeResult with status="failed"
    """
    raise NotImplementedError("Lane A: implement geocode_batch")


def estimate_cost_usd(
    addresses: list[NormalizedAddress],
    config: GeocoderConfig,
    cache: GeocodeCache,
) -> dict[str, float]:
    """Pre-flight cost estimate. Returns dict with breakdown:
    { "places_calls": int, "geocoding_calls": int,
      "places_cost_usd": float, "geocoding_cost_usd": float, "total_usd": float }
    """
    raise NotImplementedError("Lane A: implement estimate_cost_usd")
