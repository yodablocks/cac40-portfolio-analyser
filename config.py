"""
Portfolio configuration: sleeve definitions, tickers, and benchmark data.
"""

from typing import Dict, List

SLEEVES: Dict[str, Dict[str, float]] = {
    "Growth": {
        "MC.PA": 0.25,
        "AIR.PA": 0.20,
        "SU.PA": 0.20,
        "SAF.PA": 0.20,
        "KER.PA": 0.15,
    },
    "Defensive": {
        "SAN.PA": 0.30,
        "OR.PA": 0.25,
        "EL.PA": 0.20,
        "AI.PA": 0.15,
        "SW.PA": 0.10,
    },
    "Financial & Energy": {
        "BNP.PA": 0.30,
        "TTE.PA": 0.25,
        "CS.PA": 0.20,   # AXA SA (yfinance ticker: CS.PA)
        "ACA.PA": 0.15,  # Crédit Agricole
        "MC.PA": 0.10,
    },
    "High Conviction": {
        "STMPA.PA": 0.50,  # STMicroelectronics — +117% 1Y
        "LR.PA": 0.30,     # Legrand — +62% 1Y
        "GTT.PA": 0.20,    # GTT (LNG tech) — +50% 1Y
    },
}

SLEEVE_WEIGHTS: Dict[str, float] = {
    "Growth": 0.25,
    "Defensive": 0.25,
    "Financial & Energy": 0.25,
    "High Conviction": 0.25,
}

BENCHMARK_TICKER: str = "^FCHI"

SECTOR_MAP: Dict[str, str] = {
    "MC.PA": "Consumer Discretionary",
    "AIR.PA": "Industrials",
    "SU.PA": "Utilities",
    "SAF.PA": "Industrials",
    "KER.PA": "Consumer Discretionary",
    "SAN.PA": "Health Care",
    "OR.PA": "Consumer Staples",
    "EL.PA": "Consumer Discretionary",
    "AI.PA": "Industrials",
    "SW.PA": "Industrials",
    "BNP.PA": "Financials",
    "TTE.PA": "Energy",
    "CS.PA": "Financials",              # AXA SA
    "ACA.PA": "Financials",             # Crédit Agricole
    "STMPA.PA": "Information Technology",  # STMicroelectronics
    "LR.PA": "Industrials",             # Legrand
    "GTT.PA": "Industrials",            # GTT
}

COUNTRY_MAP: Dict[str, str] = {ticker: "France" for ticker in SECTOR_MAP}


# CAC 40 approximate benchmark sector weights (source: Euronext / public data)
BENCHMARK_SECTOR_WEIGHTS: Dict[str, float] = {
    "Consumer Discretionary": 0.175,
    "Industrials": 0.165,
    "Financials": 0.145,
    "Health Care": 0.120,
    "Consumer Staples": 0.095,
    "Energy": 0.075,
    "Utilities": 0.065,
    "Materials": 0.060,
    "Information Technology": 0.055,
    "Real Estate": 0.025,
    "Communication Services": 0.020,
}

ESG_SCORES: Dict[str, Dict] = {
    "MC.PA":    {"grade": "AA",  "score": 7.2},
    "AIR.PA":   {"grade": "A",   "score": 6.1},
    "SU.PA":    {"grade": "AAA", "score": 8.4},
    "SAF.PA":   {"grade": "A",   "score": 6.3},
    "KER.PA":   {"grade": "BBB", "score": 4.8},
    "SAN.PA":   {"grade": "AA",  "score": 7.5},
    "OR.PA":    {"grade": "A",   "score": 6.0},
    "EL.PA":    {"grade": "A",   "score": 6.2},
    "AI.PA":    {"grade": "AA",  "score": 7.1},
    "SW.PA":    {"grade": "BBB", "score": 4.5},
    "BNP.PA":   {"grade": "A",   "score": 6.4},
    "TTE.PA":   {"grade": "BBB", "score": 4.2},
    "CS.PA":    {"grade": "A",   "score": 6.1},
    "ACA.PA":   {"grade": "A",   "score": 6.3},
    "STMPA.PA": {"grade": "BBB", "score": 4.9},
    "LR.PA":    {"grade": "AA",  "score": 7.0},
    "GTT.PA":   {"grade": "BBB", "score": 4.1},
}

CAC40_ESG_BENCHMARK: float = 5.8

ESG_GRADE_COLOURS: Dict[str, str] = {
    "AAA": "#00b894",
    "AA":  "#00cec9",
    "A":   "#0984e3",
    "BBB": "#fdcb6e",
    "BB":  "#e17055",
    "B":   "#d63031",
    "CCC": "#6c5ce7",
}

COMPANY_NAMES: Dict[str, str] = {
    "MC.PA":    "LVMH Moët Hennessy",
    "AIR.PA":   "Airbus Group",
    "SU.PA":    "Schneider Electric",
    "SAF.PA":   "Safran",
    "KER.PA":   "Kering",
    "SAN.PA":   "Sanofi",
    "OR.PA":    "L'Oréal",
    "EL.PA":    "EssilorLuxottica",
    "AI.PA":    "Air Liquide",
    "SW.PA":    "Sodexo",
    "BNP.PA":   "BNP Paribas",
    "TTE.PA":   "TotalEnergies",
    "CS.PA":    "AXA SA",
    "ACA.PA":   "Crédit Agricole",
    "STMPA.PA": "STMicroelectronics",
    "LR.PA":    "Legrand",
    "GTT.PA":   "GTT (Gaztransport & Technigaz)",
}

# Known volatility events within the 1-year lookback window (Apr 2025 – Apr 2026)
STRESS_PERIODS = [
    {"start": "2025-08-01", "end": "2025-08-15", "label": "Global sell-off (Aug 2025)"},
    {"start": "2025-10-01", "end": "2025-10-20", "label": "Rate anxiety (Oct 2025)"},
    {"start": "2026-01-13", "end": "2026-01-27", "label": "Trump tariff shock (Jan 2026)"},
]

RISK_FREE_RATE: float = 0.03  # French OAT proxy
PORTFOLIO_VALUE_EUR: float = 1_000_000.0
VAR_CONFIDENCE: float = 0.95
LOOKBACK_DAYS: int = 365
ROLLING_WINDOW: int = 30
MAX_CONSECUTIVE_GAP: int = 3
MIN_TRADING_DAYS: int = 200
MAX_SINGLE_ISSUER_WEIGHT: float = 0.15
WEIGHT_TOLERANCE: float = 0.0001

ALL_TICKERS: List[str] = sorted(
    {t for sleeve in SLEEVES.values() for t in sleeve}
)
