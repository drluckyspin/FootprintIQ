"""Lane A — address ingestion. Tests skip until Lane A implements the stubs.

Lane A MUST flip `pytestmark` from `skip` to `lane_a` once implementations land.
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.lane_a, pytest.mark.skip(reason="Lane A not yet implemented")]


def test_normalize_addresses_matches_fixture() -> None:
    """normalize_addresses(read_input_csv(sample_addresses.csv)) ==
    pq.read_table(tests/fixtures/normalized.parquet) modulo ordering."""
    raise NotImplementedError("Lane A: implement this test")


def test_dedup_groups_by_address_key() -> None:
    """build_address_key_index groups location_ids that share an address_key."""
    raise NotImplementedError("Lane A: implement this test")


@pytest.mark.asyncio
async def test_geocode_batch_uses_cache(tmp_path) -> None:
    """geocode_batch must consult GeocodeCache before issuing HTTP requests.

    Use respx to mock httpx; assert: 1st call -> 1 HTTP hit; 2nd call -> 0 HTTP hits.
    """
    raise NotImplementedError("Lane A: implement this test")


def test_places_used_when_chain_token_present() -> None:
    """Addresses with chain_token go through Places, others through Geocoding."""
    raise NotImplementedError("Lane A: implement this test")


def test_estimate_cost_reports_breakdown() -> None:
    """estimate_cost_usd returns places_calls, geocoding_calls, and total_usd."""
    raise NotImplementedError("Lane A: implement this test")
