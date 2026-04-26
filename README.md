# CAC 40 Portfolio Analyser

End-to-end institutional portfolio analytics pipeline for a French equity investor: data ingestion, QC validation, lookthrough consolidation, risk metrics, ESG scoring, and automated HTML report generation.

**Result:** Portfolio +20.87% vs CAC 40 +1.58% = +19.29% alpha over 1 year, driven by a concentrated High Conviction sleeve (STM +117%, Legrand +62%, GTT +50%).

**[Live report →](https://yodablocks.github.io/cac40-portfolio-analyser/)**

## Pipeline

| Stage | Module | Description |
|---|---|---|
| Ingest | `pipeline/ingest.py` | 1-year daily adjusted close prices via `yfinance` for all holdings + `^FCHI` benchmark |
| Validate | `pipeline/validate.py` | Weight integrity, data gaps, minimum history, negative prices, single-issuer concentration |
| Consolidate | `pipeline/consolidate.py` | Lookthrough aggregation across 4 sleeves; detects cross-sleeve issuer overlap |
| Metrics | `pipeline/metrics.py` | Full risk analytics suite + ESG scoring |
| Report | `report/` | Jinja2 HTML report with 8 interactive Plotly charts |

## Portfolio Structure

| Sleeve | Tickers | Sleeve Weight |
|---|---|---|
| Growth | MC.PA, AIR.PA, SU.PA, SAF.PA, KER.PA | 25% |
| Defensive | SAN.PA, OR.PA, EL.PA, AI.PA, SW.PA | 25% |
| Financial & Energy | BNP.PA, TTE.PA, CS.PA, ACA.PA, MC.PA | 25% |
| High Conviction | STMPA.PA, LR.PA, GTT.PA | 25% |

MC.PA appears in Growth and Financial & Energy — intentional overlap for lookthrough demonstration. 17 unique issuers after consolidation.

## Metrics

| Category | Metrics |
|---|---|
| Performance | Annualised Return, Annualised Volatility, Sharpe Ratio (RF = 3% OAT) |
| Benchmark | Beta vs CAC 40, Tracking Error, Information Ratio, Calmar Ratio |
| Risk | 1-Day Historical VaR (95%), Max Drawdown, HHI Concentration |
| ESG | Weighted MSCI score, letter grade, delta vs CAC 40 average (5.8) |

## QC Checks

| Check | Severity |
|---|---|
| Weight sum ≠ 100% (tolerance ±0.1%) | Error |
| Price gaps > 5 consecutive trading days | Warning |
| History shorter than 252 days | Warning |
| Negative or zero closing prices | Error |
| Single-issuer weight > 30% (HHI breach) | Warning |

## Report

| Chart | Type |
|---|---|
| Cumulative return vs CAC 40 | Line |
| Drawdown | Filled area |
| Rolling 30-day beta vs CAC 40 | Line |
| Rolling 30-day volatility by sleeve | Multi-line |
| Sector over/underweight vs CAC 40 | Diverging bar |
| Pairwise correlation matrix | Heatmap |
| Portfolio weights by issuer and sector | Treemap |
| ESG score by issuer vs CAC 40 benchmark | Horizontal bar |

The report also includes sleeve performance cards, validation flags, cross-sleeve overlap table, and ESG KPI cards (score, grade, vs benchmark delta).

## Installation

Requires Python 3.9+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python generate_report.py          # fetch live data (~8s)
python generate_report.py --cache  # reuse cached prices (~0.4s)
open output/report.html
```

The `--cache` flag pickles price data to `output/prices.pkl` on first run and reuses it on subsequent runs.

A pre-generated sample report is available at `output/report.html` — viewable without running anything.

## Stack

| Library | Role |
|---|---|
| `yfinance` | Market data ingestion |
| `pandas` / `numpy` | Data manipulation and analytics |
| `plotly` | Interactive charts (Plotly 6, `go.*` API) |
| `jinja2` | HTML report templating |
