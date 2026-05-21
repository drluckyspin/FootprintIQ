"""Address normalization. OWNED BY LANE A."""

from __future__ import annotations

import re

from sqft.schema import NormalizedAddress, RawAddress

_LOCATION_PREFIX_CHAIN: dict[str, str] = {
    "WMART": "walmart",
    "AMZN": "amazon",
    "TGT": "target",
    "BBY": "best buy",
    "HD": "home depot",
    "LOWE": "lowe's",
    "COSTCO": "costco",
}


def _detect_chain_token(
    location_id: str,
    text: str,
    chain_tokens: tuple[str, ...],
) -> str | None:
    for prefix, chain in _LOCATION_PREFIX_CHAIN.items():
        if location_id.startswith(prefix):
            return chain
    lower = text.lower()
    for token in sorted(chain_tokens, key=len, reverse=True):
        if token.lower() in lower:
            return token.lower()
    return None


def normalize_address(raw: RawAddress, chain_tokens: tuple[str, ...] = ()) -> NormalizedAddress:
    """Normalize a single address row (matches tests/fixtures/normalized.parquet conventions)."""
    address_input = f"{raw.address_line_1}, {raw.city}, {raw.state} {raw.postal_code}".strip(
        ", "
    ).strip()

    normalized_line_1 = raw.address_line_1.lower().strip()
    normalized_city = raw.city.lower().strip()
    normalized_state = raw.state.lower().strip()[:2]
    zip_digits = re.sub(r"\D", "", raw.postal_code or "")
    normalized_zip5 = zip_digits[:5] if zip_digits else ""

    address_key = f"{normalized_line_1}|{normalized_city}|{normalized_state}|{normalized_zip5}"

    chain_token = _detect_chain_token(
        raw.location_id,
        f"{raw.address_line_1} {raw.city}",
        chain_tokens,
    )

    return NormalizedAddress(
        location_id=raw.location_id,
        address_input=address_input,
        normalized_line_1=normalized_line_1,
        normalized_city=normalized_city,
        normalized_state=normalized_state,
        normalized_zip5=normalized_zip5,
        address_key=address_key,
        chain_token=chain_token,
        normalize_warnings=[],
    )


def normalize_addresses(
    raws: list[RawAddress],
    chain_tokens: tuple[str, ...] = (),
) -> list[NormalizedAddress]:
    return [normalize_address(r, chain_tokens) for r in raws]
