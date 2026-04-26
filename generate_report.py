"""
Entry point: orchestrate the full pipeline and render the HTML report.

Usage:
    python generate_report.py          # fetch live data
    python generate_report.py --cache  # reuse cached prices (fast iteration)
"""

import argparse
import logging
import pickle
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from config import ALL_TICKERS, ESG_GRADE_COLOURS, SECTOR_MAP, SLEEVES
from pipeline.consolidate import consolidate
from pipeline.ingest import fetch_prices
from pipeline.metrics import compute_metrics
from pipeline.validate import validate
from report.charts import (
    build_beta_chart,
    build_corr_heatmap,
    build_cumulative_return_chart,
    build_drawdown_chart,
    build_esg_chart,
    build_rolling_vol_chart,
    build_sector_chart,
    build_treemap,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("output")
REPORT_PATH = OUTPUT_DIR / "report.html"
CACHE_PATH = OUTPUT_DIR / "prices.pkl"
TEMPLATE_DIR = Path("report")
PLOTLY_CDN = '<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>'


def load_prices(use_cache: bool):
    """Return price DataFrame, from cache if requested and available."""
    if use_cache and CACHE_PATH.exists():
        logger.info("Loading prices from cache (%s)", CACHE_PATH)
        with open(CACHE_PATH, "rb") as f:
            return pickle.load(f)
    prices = fetch_prices(ALL_TICKERS)
    with open(CACHE_PATH, "wb") as f:
        pickle.dump(prices, f)
    logger.info("Prices cached to %s", CACHE_PATH)
    return prices


def main() -> None:
    """Run the full pipeline and generate the HTML report."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", action="store_true", help="Reuse cached price data")
    args = parser.parse_args()

    logger.info("=== CAC 40 Portfolio Analyser ===")
    OUTPUT_DIR.mkdir(exist_ok=True)

    logger.info("Step 1/4: Ingesting price data")
    prices = load_prices(args.cache)

    logger.info("Step 2/4: Consolidating portfolio")
    portfolio = consolidate()

    logger.info("Step 3/4: Validating data and portfolio")
    flags = validate(prices, portfolio.net_weights)

    logger.info("Step 4/4: Computing metrics")
    metrics = compute_metrics(prices, portfolio)

    logger.info("Rendering report")
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("template.html")

    html = template.render(
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        metrics=metrics,
        portfolio=portfolio,
        flags=flags,
        sleeves=SLEEVES,
        sleeve_names=list(SLEEVES.keys()),
        plotly_js=PLOTLY_CDN,
        chart_cumulative=build_cumulative_return_chart(metrics.portfolio_returns, metrics.benchmark_returns),
        chart_drawdown=build_drawdown_chart(metrics.drawdown_series),
        chart_beta=build_beta_chart(metrics.rolling_beta),
        chart_rolling_vol=build_rolling_vol_chart(metrics.rolling_vol),
        chart_sector=build_sector_chart(metrics.sector_over_under),
        chart_corr=build_corr_heatmap(metrics.correlation_matrix),
        chart_treemap=build_treemap(portfolio.net_weights, SECTOR_MAP),
        chart_esg=build_esg_chart(portfolio.net_weights),
        esg_grade_colours=ESG_GRADE_COLOURS,
    )

    REPORT_PATH.write_text(html, encoding="utf-8")
    logger.info("Report written to %s", REPORT_PATH)
    print(f"\nReport ready: {REPORT_PATH.resolve()}")


if __name__ == "__main__":
    main()
