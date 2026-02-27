"""
ui/pages/1_📈_charts.py - Chart-Analyse Seite

Technische Chart-Analyse mit:
- Candlestick Charts
- Technische Indikatoren
- RSI, MACD, Bollinger Bands
- Multi-Timeframe Support
"""

import streamlit as st
import pandas as pd

from data.openbb_client import get_client
from indicators.technical import TechnicalIndicators
from ui.components.charts import create_main_chart
from ui.components.metrics import price_header, kpi_row, format_large_number, format_pct
from ui.components.sidebar import (
    render_ticker_input,
    render_timeframe_selector,
    render_indicator_settings,
)

# In 1_📈_charts.py:
from indicators.technical import TechnicalIndicators  # ❌ FEHLT!
from ui.components.charts import create_main_chart     # ❌ FEHLT!
from services.market_service import get_market_service # ❌ FEHLT!

# ─────────────────────────────────────────────
st.set_page_config(page_title="Charts", page_icon="📈", layout="wide")

# ── Sidebar ───────────────────────────────────
st.sidebar.title("📈 Chart Einstellungen")
ticker     = render_ticker_input()
interval, period = render_timeframe_selector()
indicators = render_indicator_settings()

# ── Hauptbereich ──────────────────────────────
client = get_client()

# Lade Quote
with st.spinner(f"Lade {ticker}..."):
    quote = client.get_quote(ticker)
    df    = client.get_price_history(ticker, period, interval)

if df.empty:
    st.error(f"❌ Keine Daten für **{ticker}** gefunden. Bitte prüfe das Ticker-Symbol.")
    st.stop()

# ── Header ────────────────────────────────────
price_header(ticker, quote)

# KPI-Leiste
kpi_row([
    {"label": "Market Cap",   "value": format_large_number(quote.get("market_cap"))},
    {"label": "P/E Ratio",    "value": f"{quote.get('pe_ratio', 'N/A'):.1f}x" if quote.get("pe_ratio") else "N/A"},
    {"label": "52W High",     "value": f"${quote.get('week_52_high', 0):,.2f}"},
    {"label": "52W Low",      "value": f"${quote.get('week_52_low', 0):,.2f}"},
    {"label": "Volumen",      "value": format_large_number(quote.get("volume"))},
])

st.divider()

# ── Indikatoren berechnen ─────────────────────
try:
    ti = TechnicalIndicators(df)
    if indicators.get("sma_20") or indicators.get("sma_50") or indicators.get("sma_200"):
        periods = []
        if indicators.get("sma_20"):  periods.append(20)
        if indicators.get("sma_50"):  periods.append(50)
        if indicators.get("sma_200"): periods.append(200)
        ti.add_sma(periods)
    if indicators.get("ema_9"):
        ti.add_ema([9])
    if indicators.get("bb"):
        ti.add_bollinger_bands()
    if indicators.get("rsi"):
        ti.add_rsi()
    if indicators.get("macd"):
        ti.add_macd()
    ti.add_volume_ma()
    df_with_indicators = ti.df
except Exception as e:
    st.warning(f"Indikator-Fehler: {e}")
    df_with_indicators = df

# ── Chart ─────────────────────────────────────
fig = create_main_chart(df_with_indicators, ticker, indicators)
st.plotly_chart(fig, use_container_width=True)

# ── Data Table (Optional) ─────────────────────
with st.expander("📋 Rohdaten"):
    st.dataframe(
        df_with_indicators.tail(50).sort_index(ascending=False),
        use_container_width=True,
    )
