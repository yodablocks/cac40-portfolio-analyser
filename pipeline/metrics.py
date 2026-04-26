"""
Risk analytics: return, volatility, Sharpe, VaR, HHI, rolling vol, correlations, beta.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from config import (
    BENCHMARK_SECTOR_WEIGHTS,
    BENCHMARK_TICKER,
    CAC40_ESG_BENCHMARK,
    ESG_SCORES,
    PORTFOLIO_VALUE_EUR,
    RISK_FREE_RATE,
    ROLLING_WINDOW,
    SLEEVES,
    SLEEVE_WEIGHTS,
    VAR_CONFIDENCE,
)
from pipeline.consolidate import ConsolidatedPortfolio

TRADING_DAYS = 252


@dataclass
class PortfolioMetrics:
    """All computed risk and return metrics for the consolidated portfolio."""

    annualised_return: float
    annualised_volatility: float
    sharpe_ratio: float
    hhi: float
    hhi_label: str
    var_pct: float
    var_eur: float
    max_drawdown: float
    drawdown_series: pd.Series
    beta: float
    rolling_beta: pd.Series
    calmar_ratio: float
    tracking_error: float
    information_ratio: float
    portfolio_returns: pd.Series
    benchmark_returns: pd.Series
    rolling_vol: pd.DataFrame
    sector_over_under: Dict[str, float]
    correlation_matrix: pd.DataFrame
    sleeve_returns: Dict[str, float] = field(default_factory=dict)
    sleeve_vols: Dict[str, float] = field(default_factory=dict)
    sleeve_cumulative_returns: pd.DataFrame = field(default_factory=pd.DataFrame)
    esg_scores: Dict[str, float] = field(default_factory=dict)
    portfolio_esg_score: float = 0.0
    portfolio_esg_grade: str = ""
    esg_vs_benchmark: float = 0.0


def compute_metrics(
    prices: pd.DataFrame,
    portfolio: ConsolidatedPortfolio,
) -> PortfolioMetrics:
    """Compute all portfolio risk analytics.

    Args:
        prices: Adjusted close prices indexed by date.
        portfolio: Consolidated portfolio from consolidate.py.

    Returns:
        PortfolioMetrics dataclass with all computed values.
    """
    returns = prices.pct_change().dropna()
    portfolio_returns = _portfolio_daily_returns(returns, portfolio.net_weights)
    benchmark_returns = returns[BENCHMARK_TICKER] if BENCHMARK_TICKER in returns.columns else pd.Series(dtype=float)

    ann_ret = _annualised_return(portfolio_returns)
    ann_vol = _annualised_volatility(portfolio_returns)
    sharpe = _sharpe_ratio(ann_ret, ann_vol)
    hhi, hhi_label = _hhi(portfolio.net_weights)
    var_pct, var_eur = _historical_var(portfolio_returns)
    max_dd, drawdown_series = _max_drawdown(portfolio_returns)
    beta, rolling_beta = _beta(portfolio_returns, returns)
    calmar = _calmar_ratio(ann_ret, max_dd)
    te = _tracking_error(portfolio_returns, benchmark_returns)
    ir = _information_ratio(portfolio_returns, benchmark_returns)
    rolling_vol = _rolling_sleeve_volatility(returns)
    sector_over_under = _sector_over_under(portfolio.sector_weights)
    corr_matrix = _correlation_matrix(returns, portfolio.net_weights)

    sleeve_returns, sleeve_vols, sleeve_cum = _sleeve_stats(returns)
    esg_scores, portfolio_esg_score, portfolio_esg_grade, esg_vs_benchmark = _esg_metrics(portfolio.net_weights)

    return PortfolioMetrics(
        annualised_return=ann_ret,
        annualised_volatility=ann_vol,
        sharpe_ratio=sharpe,
        hhi=hhi,
        hhi_label=hhi_label,
        var_pct=var_pct,
        var_eur=var_eur,
        max_drawdown=max_dd,
        drawdown_series=drawdown_series,
        beta=beta,
        rolling_beta=rolling_beta,
        calmar_ratio=calmar,
        tracking_error=te,
        information_ratio=ir,
        portfolio_returns=portfolio_returns,
        benchmark_returns=benchmark_returns,
        rolling_vol=rolling_vol,
        sector_over_under=sector_over_under,
        correlation_matrix=corr_matrix,
        sleeve_returns=sleeve_returns,
        sleeve_vols=sleeve_vols,
        sleeve_cumulative_returns=sleeve_cum,
        esg_scores=esg_scores,
        portfolio_esg_score=portfolio_esg_score,
        portfolio_esg_grade=portfolio_esg_grade,
        esg_vs_benchmark=esg_vs_benchmark,
    )


def _portfolio_daily_returns(
    returns: pd.DataFrame, weights: Dict[str, float]
) -> pd.Series:
    """Compute daily portfolio return series from individual returns and weights."""
    available = {t: w for t, w in weights.items() if t in returns.columns}
    total_w = sum(available.values())
    norm_weights = {t: w / total_w for t, w in available.items()}
    weight_series = pd.Series(norm_weights)
    return returns[weight_series.index] @ weight_series


def _annualised_return(daily_returns: pd.Series) -> float:
    """Annualise mean daily return."""
    return float(daily_returns.mean() * TRADING_DAYS)


def _annualised_volatility(daily_returns: pd.Series) -> float:
    """Annualise daily return standard deviation."""
    return float(daily_returns.std() * np.sqrt(TRADING_DAYS))


def _sharpe_ratio(ann_return: float, ann_vol: float) -> float:
    """Compute Sharpe ratio using the configured risk-free rate."""
    if ann_vol == 0:
        return 0.0
    return (ann_return - RISK_FREE_RATE) / ann_vol


def _hhi(weights: Dict[str, float]) -> Tuple[float, str]:
    """Compute Herfindahl-Hirschman Index and assign concentration label."""
    total = sum(weights.values())
    hhi = sum((w / total) ** 2 for w in weights.values())
    if hhi < 0.10:
        label = "Low"
    elif hhi < 0.18:
        label = "Moderate"
    else:
        label = "High"
    return hhi, label


def _historical_var(daily_returns: pd.Series) -> Tuple[float, float]:
    """Compute 1-day historical VaR at 95% confidence.

    Returns:
        Tuple of (var_pct as positive decimal, var_eur).
    """
    clean = daily_returns.dropna()
    if len(clean) == 0:
        return 0.0, 0.0
    var_pct = float(-np.percentile(clean, (1 - VAR_CONFIDENCE) * 100))
    var_eur = var_pct * PORTFOLIO_VALUE_EUR
    return var_pct, var_eur


def _beta(
    portfolio_returns: pd.Series, returns: pd.DataFrame
) -> Tuple[float, pd.Series]:
    """Compute portfolio beta vs CAC 40 benchmark (full period + 60-day rolling).

    Returns:
        Tuple of (full-period beta, rolling_beta Series).
    """
    if BENCHMARK_TICKER not in returns.columns:
        return 0.0, pd.Series(dtype=float)

    bm = returns[BENCHMARK_TICKER]
    aligned = pd.concat([portfolio_returns, bm], axis=1).dropna()
    aligned.columns = ["portfolio", "benchmark"]

    cov = aligned["portfolio"].cov(aligned["benchmark"])
    var_bm = aligned["benchmark"].var()
    full_beta = float(cov / var_bm) if var_bm != 0 else 0.0

    roll_cov = aligned["portfolio"].rolling(ROLLING_WINDOW).cov(aligned["benchmark"])
    roll_var = aligned["benchmark"].rolling(ROLLING_WINDOW).var()
    rolling_beta = (roll_cov / roll_var).dropna()

    return full_beta, rolling_beta


def _information_ratio(portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """Annualised active return divided by tracking error."""
    if benchmark_returns.empty:
        return 0.0
    aligned = pd.concat([portfolio_returns, benchmark_returns], axis=1).dropna()
    active = aligned.iloc[:, 0] - aligned.iloc[:, 1]
    te = active.std() * np.sqrt(TRADING_DAYS)
    return float((active.mean() * TRADING_DAYS) / te) if te != 0 else 0.0


def _calmar_ratio(ann_return: float, max_dd: float) -> float:
    """Annualised return divided by absolute max drawdown."""
    return ann_return / abs(max_dd) if max_dd != 0 else 0.0


def _tracking_error(portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """Annualised std dev of active returns (portfolio minus benchmark)."""
    if benchmark_returns.empty:
        return 0.0
    aligned = pd.concat([portfolio_returns, benchmark_returns], axis=1).dropna()
    active = aligned.iloc[:, 0] - aligned.iloc[:, 1]
    return float(active.std() * np.sqrt(TRADING_DAYS))


def _max_drawdown(daily_returns: pd.Series) -> Tuple[float, pd.Series]:
    """Compute maximum drawdown and the full drawdown time series.

    Returns:
        Tuple of (max_drawdown as negative decimal, drawdown_series in %).
    """
    cum = (1 + daily_returns).cumprod()
    rolling_peak = cum.cummax()
    drawdown = (cum - rolling_peak) / rolling_peak
    return float(drawdown.min()), drawdown * 100


def _rolling_sleeve_volatility(returns: pd.DataFrame) -> pd.DataFrame:
    """Compute 30-day rolling annualised volatility for each sleeve's equal-weight portfolio."""
    result = {}
    for sleeve_name, holdings in SLEEVES.items():
        available = [t for t in holdings if t in returns.columns]
        if not available:
            continue
        sleeve_ret = returns[available].mean(axis=1)
        result[sleeve_name] = (
            sleeve_ret.rolling(ROLLING_WINDOW).std() * np.sqrt(TRADING_DAYS)
        )
    return pd.DataFrame(result).dropna()


def _sector_over_under(portfolio_sector_weights: Dict[str, float]) -> Dict[str, float]:
    """Compute sector over/underweight versus CAC 40 benchmark."""
    all_sectors = set(portfolio_sector_weights) | set(BENCHMARK_SECTOR_WEIGHTS)
    return {
        sector: portfolio_sector_weights.get(sector, 0.0)
        - BENCHMARK_SECTOR_WEIGHTS.get(sector, 0.0)
        for sector in sorted(all_sectors)
    }


def _correlation_matrix(
    returns: pd.DataFrame, weights: Dict[str, float]
) -> pd.DataFrame:
    """Return pairwise correlation matrix for all holdings with available data."""
    tickers = [t for t in weights if t in returns.columns]
    return returns[tickers].corr()


def _esg_metrics(
    net_weights: Dict[str, float],
) -> Tuple[Dict[str, float], float, str, float]:
    """Compute ESG metrics from net portfolio weights and MSCI scores."""
    weighted: Dict[str, float] = {}
    total_w = 0.0
    weighted_sum = 0.0
    for ticker, weight in net_weights.items():
        if ticker in ESG_SCORES:
            score = ESG_SCORES[ticker]["score"]
            weighted[ticker] = weight * score
            weighted_sum += weight * score
            total_w += weight

    portfolio_score = weighted_sum / total_w if total_w > 0 else 0.0

    if portfolio_score >= 7.5:
        grade = "AAA"
    elif portfolio_score >= 6.5:
        grade = "AA"
    elif portfolio_score >= 5.5:
        grade = "A"
    elif portfolio_score >= 4.5:
        grade = "BBB"
    elif portfolio_score >= 3.5:
        grade = "BB"
    elif portfolio_score >= 2.5:
        grade = "B"
    else:
        grade = "CCC"

    return weighted, portfolio_score, grade, portfolio_score - CAC40_ESG_BENCHMARK


def _sleeve_stats(
    returns: pd.DataFrame,
) -> Tuple[Dict[str, float], Dict[str, float], pd.DataFrame]:
    """Compute annualised return, vol, and cumulative return series for each sleeve."""
    sleeve_returns: Dict[str, float] = {}
    sleeve_vols: Dict[str, float] = {}
    cum_series: Dict[str, pd.Series] = {}
    for sleeve_name, holdings in SLEEVES.items():
        available = [t for t in holdings if t in returns.columns]
        if not available:
            continue
        ret = returns[available].mean(axis=1)
        sleeve_returns[sleeve_name] = float(ret.mean() * TRADING_DAYS)
        sleeve_vols[sleeve_name] = float(ret.std() * np.sqrt(TRADING_DAYS))
        cum_series[sleeve_name] = (1 + ret).cumprod() * 100
    return sleeve_returns, sleeve_vols, pd.DataFrame(cum_series).dropna()
