"""
Data ingestion: download adjusted close prices via yfinance.
"""

import logging
from datetime import datetime, timedelta
from typing import List

import pandas as pd
import yfinance as yf

from config import BENCHMARK_TICKER, LOOKBACK_DAYS

logger = logging.getLogger(__name__)


def fetch_prices(tickers: List[str]) -> pd.DataFrame:
    """Download 1 year of daily adjusted close prices for all tickers plus benchmark.

    Args:
        tickers: List of ticker symbols (e.g. ['MC.PA', 'AIR.PA']).

    Returns:
        DataFrame indexed by date with one column per ticker, forward-filled
        and dropped if still missing after fill.
    """
    all_symbols = sorted(set(tickers + [BENCHMARK_TICKER]))
    end = datetime.today()
    start = end - timedelta(days=LOOKBACK_DAYS + 30)  # buffer for trading days

    logger.info("Downloading price data for %d symbols", len(all_symbols))

    raw: pd.DataFrame = yf.download(
        all_symbols,
        start=start.strftime("%Y-%m-%d"),
        end=end.strftime("%Y-%m-%d"),
        auto_adjust=True,
        progress=False,
    )

    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw["Close"]
    else:
        prices = raw[["Close"]]
        prices.columns = all_symbols

    prices = prices.ffill()
    prices = prices.dropna(how="all")

    missing_cols = [c for c in all_symbols if c not in prices.columns]
    if missing_cols:
        logger.warning("Tickers not returned by yfinance: %s", missing_cols)

    cols_with_data = [c for c in all_symbols if c in prices.columns]
    prices = prices[cols_with_data].dropna(subset=cols_with_data, how="all")

    logger.info(
        "Fetched %d trading days for %d symbols", len(prices), len(cols_with_data)
    )
    return prices
