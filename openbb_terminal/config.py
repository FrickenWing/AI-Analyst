"""
config.py - Zentrale Konfiguration für OpenBB Terminal Pro

Alle Settings, Konstanten und Feature-Flags an einem Ort.
Wird von allen anderen Modulen importiert.
"""

import os
import streamlit as st
from pathlib import Path

# ─────────────────────────────────────────────
# PROJEKT-PFADE
# ─────────────────────────────────────────────
ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data"
CACHE_DIR = ROOT_DIR / ".cache"
CACHE_DIR.mkdir(exist_ok=True)

# ─────────────────────────────────────────────
# API KEYS (aus Streamlit Secrets oder .env)
# ─────────────────────────────────────────────
def get_secret(key: str, default: str = "") -> str:
    """Holt Secret aus st.secrets oder Environment Variable."""
    try:
        return st.secrets.get(key, os.getenv(key, default))
    except Exception:
        return os.getenv(key, default)

OPENBB_PAT = get_secret("OPENBB_PAT")         # OpenBB Personal Access Token
FMP_API_KEY = get_secret("FMP_API_KEY")         # Financial Modeling Prep (optional)
ALPHA_VANTAGE_KEY = get_secret("ALPHA_VANTAGE_KEY")  # Alpha Vantage (optional)

# ─────────────────────────────────────────────
# DATEN-EINSTELLUNGEN
# ─────────────────────────────────────────────

# Standard-Ticker & Timeframe
DEFAULT_TICKER = "AAPL"
DEFAULT_TIMEFRAME = "1d"
DEFAULT_PERIOD = "1y"

# Verfügbare Timeframes
TIMEFRAMES = {
    "1m":  {"label": "1 Minute",   "interval": "1m",  "period": "7d"},
    "5m":  {"label": "5 Minuten",  "interval": "5m",  "period": "60d"},
    "15m": {"label": "15 Minuten", "interval": "15m", "period": "60d"},
    "1h":  {"label": "1 Stunde",   "interval": "1h",  "period": "2y"},
    "4h":  {"label": "4 Stunden",  "interval": "4h",  "period": "2y"},
    "1d":  {"label": "Täglich",    "interval": "1d",  "period": "5y"},
    "1wk": {"label": "Wöchentlich","interval": "1wk", "period": "10y"},
    "1mo": {"label": "Monatlich",  "interval": "1mo", "period": "20y"},
}

# Provider Priorität (erster verfügbarer wird genutzt)
PROVIDER_PRIORITY = ["yfinance", "fmp", "alpha_vantage"]

# Cache-Dauer in Sekunden
CACHE_TTL = {
    "price_data":    300,    # 5 Min - Kursdaten
    "fundamentals":  3600,   # 1 Std - Fundamentaldaten
    "news":          900,    # 15 Min - News
    "screener":      600,    # 10 Min - Screener
    "macro":         3600,   # 1 Std - Makrodaten
}

# ─────────────────────────────────────────────
# TECHNISCHE INDIKATOREN - DEFAULTS
# ─────────────────────────────────────────────
INDICATOR_DEFAULTS = {
    # Moving Averages
    "sma_fast":    20,
    "sma_slow":    50,
    "sma_200":     200,
    "ema_fast":    12,
    "ema_slow":    26,

    # Momentum
    "rsi_period":  14,
    "rsi_ob":      70,   # Overbought
    "rsi_os":      30,   # Oversold
    "macd_fast":   12,
    "macd_slow":   26,
    "macd_signal": 9,

    # Volatilität
    "bb_period":   20,
    "bb_std":      2.0,
    "atr_period":  14,

    # Volumen
    "vwap_enabled": True,
    "obv_enabled":  True,
}

# ─────────────────────────────────────────────
# UI EINSTELLUNGEN
# ─────────────────────────────────────────────
APP_TITLE = "OpenBB Terminal Pro"
APP_ICON = "📈"
APP_LAYOUT = "wide"

# Chart Farben (Dark Theme)
COLORS = {
    "bullish":      "#26a69a",   # Grün (Kerze oben)
    "bearish":      "#ef5350",   # Rot (Kerze unten)
    "volume":       "#5c6bc0",   # Lila (Volumen)
    "sma_fast":     "#ff9800",   # Orange
    "sma_slow":     "#2196f3",   # Blau
    "sma_200":      "#9c27b0",   # Lila
    "ema":          "#00bcd4",   # Cyan
    "bb_upper":     "#78909c",   # Grau
    "bb_lower":     "#78909c",   # Grau
    "rsi":          "#ab47bc",   # Lila
    "macd":         "#42a5f5",   # Hellblau
    "signal":       "#ef5350",   # Rot
    "background":   "#0e1117",   # Dark BG
    "grid":         "#1e2329",   # Grid
    "text":         "#fafafa",   # Weißer Text
}

CHART_TEMPLATE = "plotly_dark"
CHART_HEIGHT = 600
VOLUME_HEIGHT = 150

# ─────────────────────────────────────────────
# SCREENER EINSTELLUNGEN
# ─────────────────────────────────────────────
SCREENER_UNIVERSES = {
    "sp500":     "S&P 500",
    "nasdaq100": "NASDAQ 100",
    "dax":       "DAX 40",
    "custom":    "Eigene Watchlist",
}

# Standard Watchlist
DEFAULT_WATCHLIST = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "META", "TSLA", "NFLX", "AMD", "INTC",
]

# ─────────────────────────────────────────────
# PORTFOLIO EINSTELLUNGEN
# ─────────────────────────────────────────────
RISK_FREE_RATE = 0.05          # 5% - für Sharpe Ratio
TRADING_DAYS_PER_YEAR = 252

# ─────────────────────────────────────────────
# FEATURE FLAGS (Ein/Ausschalten von Features)
# ─────────────────────────────────────────────
FEATURES = {
    "ai_analyst":       bool(get_secret("GEMINI_API_KEY") or get_secret("ANTHROPIC_API_KEY")),
    "options_data":     bool(FMP_API_KEY),
    "real_time_data":   False,   # Noch nicht implementiert
    "backtesting":      False,   # Phase 3
    "paper_trading":    False,   # Phase 4
    "export_pdf":       True,
    "export_csv":       True,
}
