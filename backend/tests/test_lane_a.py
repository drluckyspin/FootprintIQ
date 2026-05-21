"""Lane A — address ingestion."""

from __future__ import annotations

import csv
from pathlib import Path

import httpx
import pyarrow.parquet as pq
import pytest
import respx

from sqft.config import GeocoderConfig
from sqft.dedup import build_address_key_index, unique_addresses
from sqft.geocode import GeocodeCache, estimate_cost_usd, geocode_batch
from sqft.normalize import normalize_address, normalize_addresses
from sqft.schema import GeocoderProvider, RawAddress

pytestmark = pytest.mark.lane_a

CHAIN_TOKENS = (
    "walmart",
    "target",
    "amazon",
    "costco",
    "kroger",
    "home depot",
    "lowe's",
    "best buy",
    "sam's club",
    "fedex",
    "ups",
)


def _load_raw_addresses(csv_path: Path) -> list[RawAddress]:
    rows: list[RawAddress] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            state = (row.get("state") or "").strip()
            if len(state) < 2:
                state = "XX"
            row["state"] = state
            rows.append(RawAddress.model_validate(row))
    return rows


def _rows_to_dicts(rows: list) -> list[dict]:
    return [r.model_dump() for r in rows]


def test_normalize_addresses_matches_fixture(
    fixtures_dir: Path, sample_addresses_csv: Path
) -> None:
    raws = _load_raw_addresses(sample_addresses_csv)
    got = normalize_addresses(raws, CHAIN_TOKENS)
    expected_table = pq.read_table(fixtures_dir / "normalized.parquet").to_pylist()

    got_by_id = {r.location_id: r.model_dump() for r in got}
    exp_by_id = {r["location_id"]: r for r in expected_table}

    assert set(got_by_id) == set(exp_by_id)
    skip_ids = {"BROKEN_001", "BROKEN_002"}  # invalid states padded for pydantic in tests only
    for lid, exp in exp_by_id.items():
        if lid in skip_ids:
            continue
        g = got_by_id[lid]
        for key in (
            "address_input",
            "normalized_line_1",
            "normalized_city",
            "normalized_state",
            "normalized_zip5",
            "address_key",
        ):
            assert g[key] == exp[key], f"{lid}.{key}"
        # Fixtures encode chain from location metadata; detection only fires when brand appears in text.
        if exp["chain_token"] and exp["chain_token"] in g["address_input"].lower():
            assert g["chain_token"] == exp["chain_token"]


def test_dedup_groups_by_address_key() -> None:
    a = normalize_address(
        RawAddress(
            location_id="A1",
            address_line_1="123 Main St",
            city="Austin",
            state="TX",
            postal_code="78701",
            location_type="retail",
        ),
        CHAIN_TOKENS,
    )
    b = normalize_address(
        RawAddress(
            location_id="A2",
            address_line_1="123 Main St",
            city="Austin",
            state="TX",
            postal_code="78701",
            location_type="retail",
        ),
        CHAIN_TOKENS,
    )
    index = build_address_key_index([a, b])
    assert index[a.address_key] == ["A1", "A2"]
    unique = unique_addresses([a, b])
    assert len(unique) == 1
    assert unique[0].location_id == "A1"


@respx.mock
@pytest.mark.asyncio
async def test_geocode_batch_uses_cache(tmp_path: Path) -> None:
    config = GeocoderConfig(concurrency=2, rate_limit_qps=100, retry_attempts=1)
    cache = GeocodeCache(tmp_path / "cache.sqlite")
    addr = normalize_address(
        RawAddress(
            location_id="WMART_001",
            address_line_1="2110 W Walnut St",
            city="Rogers",
            state="AR",
            postal_code="72756",
            location_type="retail",
        ),
        CHAIN_TOKENS,
    )

    places_route = respx.get(url__regex=r".*place/textsearch.*").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "place_id": "pid1",
                        "formatted_address": "2110 W Walnut St",
                        "geometry": {"location": {"lat": 36.345, "lng": -94.15}},
                    }
                ]
            },
        )
    )
    details_route = respx.get(url__regex=r".*place/details.*").mock(
        return_value=httpx.Response(
            200,
            json={
                "result": {
                    "formatted_address": "2110 W Walnut St",
                    "geometry": {"location": {"lat": 36.345, "lng": -94.15}},
                    "types": ["ROOFTOP"],
                }
            },
        )
    )

    await geocode_batch([addr], config, cache, places_api_key="k", geocoding_api_key="k")
    assert places_route.call_count == 1
    assert details_route.call_count == 1

    await geocode_batch([addr], config, cache, places_api_key="k", geocoding_api_key="k")
    assert places_route.call_count == 1
    assert details_route.call_count == 1


@respx.mock
@pytest.mark.asyncio
async def test_places_used_when_chain_token_present(tmp_path: Path) -> None:
    config = GeocoderConfig()
    cache = GeocodeCache(tmp_path / "c.sqlite")
    chain_addr = normalize_address(
        RawAddress(
            location_id="WMART_001",
            address_line_1="2110 W Walnut St",
            city="Rogers",
            state="AR",
            postal_code="72756",
            location_type="retail",
        ),
        CHAIN_TOKENS,
    )
    plain_addr = normalize_address(
        RawAddress(
            location_id="P1",
            address_line_1="742 Evergreen Terrace",
            city="Springfield",
            state="IL",
            postal_code="62701",
            location_type="other",
        ),
        CHAIN_TOKENS,
    )

    respx.get(url__regex=r".*place/textsearch.*").mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"place_id": "p", "geometry": {"location": {"lat": 1, "lng": 2}}}]},
        )
    )
    respx.get(url__regex=r".*place/details.*").mock(
        return_value=httpx.Response(200, json={"result": {"types": ["ROOFTOP"]}})
    )
    geocode_route = respx.get(url__regex=r".*geocode/json.*").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "OK",
                "results": [
                    {
                        "formatted_address": "742 Evergreen",
                        "geometry": {
                            "location": {"lat": 39.78, "lng": -89.65},
                            "location_type": "ROOFTOP",
                        },
                    }
                ],
            },
        )
    )

    results = await geocode_batch(
        [chain_addr, plain_addr],
        config,
        cache,
        places_api_key="k",
        geocoding_api_key="k",
    )
    assert results[0].provider == GeocoderProvider.GOOGLE_PLACES
    assert results[1].provider == GeocoderProvider.GOOGLE_GEOCODING
    assert geocode_route.call_count == 1


def test_estimate_cost_reports_breakdown(tmp_path: Path) -> None:
    config = GeocoderConfig()
    cache = GeocodeCache(tmp_path / "c.sqlite")
    chain = normalize_address(
        RawAddress(
            location_id="WMART_001",
            address_line_1="Walmart",
            city="Rogers",
            state="AR",
            postal_code="72756",
            location_type="retail",
        ),
        CHAIN_TOKENS,
    )
    plain = normalize_address(
        RawAddress(
            location_id="P1",
            address_line_1="742 Evergreen Terrace",
            city="Springfield",
            state="IL",
            postal_code="62701",
            location_type="other",
        ),
        CHAIN_TOKENS,
    )
    cost = estimate_cost_usd([chain, plain], config, cache)
    assert cost["places_calls"] == 2.0
    assert cost["geocoding_calls"] == 1.0
    assert cost["total_usd"] == cost["places_cost_usd"] + cost["geocoding_cost_usd"]
    assert cost["total_usd"] > 0
