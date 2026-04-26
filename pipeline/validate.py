"""
QC validation checks on portfolio configuration and price data.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd

from config import (
    MAX_CONSECUTIVE_GAP,
    MAX_SINGLE_ISSUER_WEIGHT,
    MIN_TRADING_DAYS,
    SLEEVES,
    WEIGHT_TOLERANCE,
)

logger = logging.getLogger(__name__)


@dataclass
class Flag:
    """A single validation flag."""

    severity: str  # "WARNING" or "ERROR"
    check: str
    detail: str

    def __str__(self) -> str:
        return f"[{self.severity}] {self.check}: {self.detail}"


def validate(prices: pd.DataFrame, consolidated_weights: Dict[str, float]) -> List[Flag]:
    """Run all QC checks and return a list of structured flags.

    Args:
        prices: DataFrame of adjusted close prices indexed by date.
        consolidated_weights: Net issuer weights in the consolidated portfolio.

    Returns:
        List of Flag objects; empty list means all checks passed.
    """
    flags: List[Flag] = []

    flags.extend(_check_sleeve_weights())
    flags.extend(_check_issuer_concentration(consolidated_weights))
    flags.extend(_check_data_gaps(prices))
    flags.extend(_check_min_trading_days(prices))
    flags.extend(_check_no_negative_prices(prices))

    for flag in flags:
        logger.warning(flag)

    return flags


def _check_sleeve_weights() -> List[Flag]:
    """Verify each sleeve's weights sum to 100% within tolerance."""
    flags: List[Flag] = []
    for sleeve_name, holdings in SLEEVES.items():
        total = sum(holdings.values())
        if abs(total - 1.0) > WEIGHT_TOLERANCE:
            flags.append(
                Flag(
                    severity="ERROR",
                    check="sleeve_weight_sum",
                    detail=f"{sleeve_name} weights sum to {total:.6f}, expected 1.0",
                )
            )
    return flags


def _check_issuer_concentration(consolidated_weights: Dict[str, float]) -> List[Flag]:
    """Flag any issuer exceeding the single-name concentration limit."""
    flags: List[Flag] = []
    for ticker, weight in consolidated_weights.items():
        if weight > MAX_SINGLE_ISSUER_WEIGHT:
            flags.append(
                Flag(
                    severity="WARNING",
                    check="issuer_concentration",
                    detail=(
                        f"{ticker} consolidated weight {weight:.2%} exceeds "
                        f"limit of {MAX_SINGLE_ISSUER_WEIGHT:.0%}"
                    ),
                )
            )
    return flags


def _check_data_gaps(prices: pd.DataFrame) -> List[Flag]:
    """Detect any ticker with > MAX_CONSECUTIVE_GAP missing trading days."""
    flags: List[Flag] = []
    for ticker in prices.columns:
        series = prices[ticker]
        null_mask = series.isna()
        if not null_mask.any():
            continue
        max_gap = _max_consecutive_trues(null_mask)
        if max_gap > MAX_CONSECUTIVE_GAP:
            flags.append(
                Flag(
                    severity="WARNING",
                    check="data_gaps",
                    detail=f"{ticker} has {max_gap} consecutive missing days (limit {MAX_CONSECUTIVE_GAP})",
                )
            )
    return flags


def _check_min_trading_days(prices: pd.DataFrame) -> List[Flag]:
    """Ensure each ticker has at least MIN_TRADING_DAYS of valid data."""
    flags: List[Flag] = []
    for ticker in prices.columns:
        count = prices[ticker].notna().sum()
        if count < MIN_TRADING_DAYS:
            flags.append(
                Flag(
                    severity="ERROR",
                    check="min_trading_days",
                    detail=f"{ticker} has only {count} valid days (minimum {MIN_TRADING_DAYS})",
                )
            )
    return flags


def _check_no_negative_prices(prices: pd.DataFrame) -> List[Flag]:
    """Flag any ticker with zero or negative prices."""
    flags: List[Flag] = []
    for ticker in prices.columns:
        neg_count = (prices[ticker] <= 0).sum()
        if neg_count > 0:
            flags.append(
                Flag(
                    severity="ERROR",
                    check="negative_prices",
                    detail=f"{ticker} has {neg_count} non-positive price observations",
                )
            )
    return flags


def _max_consecutive_trues(mask: pd.Series) -> int:
    """Return the maximum run length of True values in a boolean series."""
    max_run = 0
    current = 0
    for val in mask:
        if val:
            current += 1
            max_run = max(max_run, current)
        else:
            current = 0
    return max_run
