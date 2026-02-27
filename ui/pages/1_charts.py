"""pages/1_charts.py - Chart-Analyse Seite"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from data.openbb_client import get_client
from indicators.technical import TechnicalIndicators
from ui.components.charts import create_main_chart
from ui.components.metrics import price_header, kpi_row, format_large_number
from ui.components.sidebar import render_ticker_input, render_timeframe_selector, render_indicator_settings

st.set_page_config(page_title="Charts", page_icon="📈", layout="wide")

st.sidebar.title("📈 Chart Einstellungen")
ticker             = render_ticker_input()
interval, period   = render_timeframe_selector()
indicators         = render_indicator_settings()

client = get_client()

with st.spinner(f"Lade {ticker}..."):
    quote = client.get_quote(ticker)
    df    = client.get_price_history(ticker, period, interval)

if df.empty:
    st.error(f"❌ Keine Daten für **{ticker}**. Bitte prüfe das Ticker-Symbol.")
    st.stop()

price_header(ticker, quote)

kpi_row([
    {"label": "Market Cap",  "value": format_large_number(quote.get("market_cap"))},
    {"label": "P/E Ratio",   "value": f"{quote.get('pe_ratio', 0):.1f}x" if quote.get("pe_ratio") else "N/A"},
    {"label": "52W High",    "value": f"${quote.get('week_52_high', 0):,.2f}"},
    {"label": "52W Low",     "value": f"${quote.get('week_52_low', 0):,.2f}"},
    {"label": "Volumen",     "value": format_large_number(quote.get("volume"))},
])

st.divider()

try:
    ti = TechnicalIndicators(df)
    periods = [p for p, key in [(20,"sma_20"),(50,"sma_50"),(200,"sma_200")] if indicators.get(key)]
    if periods: ti.add_sma(periods)
    if indicators.get("ema_9"): ti.add_ema([9])
    if indicators.get("bb"):    ti.add_bollinger_bands()
    if indicators.get("rsi"):   ti.add_rsi()
    if indicators.get("macd"):  ti.add_macd()
    ti.add_volume_ma()
    df_ind = ti.df
except Exception as e:
    st.warning(f"Indikator-Fehler: {e}")
    df_ind = df

fig = create_main_chart(df_ind, ticker, indicators)
st.plotly_chart(fig, use_container_width=True)

with st.expander("📋 Rohdaten"):
    st.dataframe(df_ind.tail(50).sort_index(ascending=False), use_container_width=True)
