"""Address normalization. OWNED BY LANE A.

Inputs:  list[RawAddress] (or read from input CSV)
Outputs: list[NormalizedAddress]

Wave 0 stub — Lane A implements `normalize_addresses`.
"""

from __future__ import annotations

from sqft.schema import NormalizedAddress, RawAddress


def normalize_address(raw: RawAddress, chain_tokens: tuple[str, ...] = ()) -> NormalizedAddress:
    """Normalize a single address.

    Lane A MUST:
      - Use usaddress (or libpostal if installable) to parse address_line_1
      - Strip store-number suffixes like '#4521', dock/suite designators that hurt matching
      - Uppercase state, zero-pad zip5
      - Detect chain_token from input (membership in chain_tokens)
      - Emit NormalizedAddress with stable address_key = "{normalized_line_1}|{city}|{state2}|{zip5}"
      - Populate normalize_warnings with any heuristics applied (e.g. "dropped suite", "ambiguous zip")
    """
    raise NotImplementedError("Lane A: implement normalize_address")


def normalize_addresses(
    raws: list[RawAddress], chain_tokens: tuple[str, ...] = ()
) -> list[NormalizedAddress]:
    """Batch wrapper. Lane A may parallelize if profiling justifies it."""
    return [normalize_address(r, chain_tokens) for r in raws]
