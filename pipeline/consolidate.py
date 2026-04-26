"""
Lookthrough consolidation: aggregate sleeve holdings into a single portfolio.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from config import COUNTRY_MAP, SECTOR_MAP, SLEEVE_WEIGHTS, SLEEVES


@dataclass
class ConsolidatedPortfolio:
    """Result of lookthrough consolidation across all sleeves."""

    net_weights: Dict[str, float]
    sector_weights: Dict[str, float]
    country_weights: Dict[str, float]
    overlapping_issuers: List[Tuple[str, List[str]]]
    sleeve_weights: Dict[str, float] = field(default_factory=dict)


def consolidate() -> ConsolidatedPortfolio:
    """Aggregate sleeve holdings into a single consolidated portfolio.

    Equal sleeve weighting (1/3 each) is applied. Overlapping issuers
    (present in more than one sleeve) are detected and reported.

    Returns:
        ConsolidatedPortfolio with net issuer weights, sector/country breakdowns,
        and overlap information.
    """
    net_weights: Dict[str, float] = {}

    for sleeve_name, holdings in SLEEVES.items():
        sleeve_w = SLEEVE_WEIGHTS[sleeve_name]
        for ticker, weight in holdings.items():
            net_weights[ticker] = net_weights.get(ticker, 0.0) + sleeve_w * weight

    overlapping_issuers = _find_overlaps()

    sector_weights = _aggregate_by_key(net_weights, SECTOR_MAP)
    country_weights = _aggregate_by_key(net_weights, COUNTRY_MAP)

    return ConsolidatedPortfolio(
        net_weights=net_weights,
        sector_weights=sector_weights,
        country_weights=country_weights,
        overlapping_issuers=overlapping_issuers,
        sleeve_weights=SLEEVE_WEIGHTS,
    )


def _find_overlaps() -> List[Tuple[str, List[str]]]:
    """Return list of (ticker, [sleeve_names]) for issuers in multiple sleeves."""
    issuer_sleeves: Dict[str, List[str]] = {}
    for sleeve_name, holdings in SLEEVES.items():
        for ticker in holdings:
            issuer_sleeves.setdefault(ticker, []).append(sleeve_name)

    return [
        (ticker, sleeves)
        for ticker, sleeves in sorted(issuer_sleeves.items())
        if len(sleeves) > 1
    ]


def _aggregate_by_key(
    net_weights: Dict[str, float], mapping: Dict[str, str]
) -> Dict[str, float]:
    """Sum net weights by the dimension defined in mapping (sector or country)."""
    result: Dict[str, float] = {}
    for ticker, weight in net_weights.items():
        key = mapping.get(ticker, "Unknown")
        result[key] = result.get(key, 0.0) + weight
    return result
