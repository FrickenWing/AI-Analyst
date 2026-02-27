"""pages/1_charts.py - Professionelle Chart-Analyse"""
import sys, os
from datetime import datetime
import streamlit as st
from streamlit_searchbox import st_searchbox # type: ignore

# Pfad-Setup
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.openbb_client import get_client
from services.market_service import get_market_service
from indicators.technical import TechnicalIndicators
from ui.components.charts import create_main_chart
from ui.components.metrics import price_header, kpi_row, format_large_number

# ─────────────────────────────────────────────
# SEITEN-KONFIGURATION
# ─────────────────────────────────────────────
st.set_page_config(page_title="Charts", page_icon="📈", layout="wide")

st.markdown("""
<style>
    div[data-testid="stHorizontalBlock"] button {
        border-radius: 20px;
        padding: 4px 15px;
        border: 1px solid #4b5563;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 1. SUCHFUNKTION & REFRESH
# ─────────────────────────────────────────────
client = get_client()

def search_yfinance(search_term: str) -> list:
    if not search_term: return []
    results = client.search_ticker(search_term)
    return [(f"{r['ticker']} | {r['name']} ({r['exchange']})", r['ticker']) for r in results]

current_ticker = st.session_state.get("current_ticker", "AAPL")

# Layout: Suche (Links) | Refresh Button (Rechts)
col_search, col_refresh = st.columns([3, 1])

with col_search:
    st.markdown("### 🔍 Aktie suchen")
    selected_ticker = st_searchbox(
        search_yfinance,
        default=current_ticker,
        key="chart_search",
        placeholder="z.B. Apple, Nvidia, SAP..."
    )

with col_refresh:
    st.markdown("### &nbsp;") # Platzhalter für Alignment
    if st.button("🔄 Daten aktualisieren", use_container_width=True):
        with st.spinner("Lösche Cache und lade neu..."):
            client.clear_cache()
            st.rerun()

if selected_ticker and selected_ticker != current_ticker:
    st.session_state["current_ticker"] = selected_ticker
    current_ticker = selected_ticker
    st.rerun()

# ─────────────────────────────────────────────
# 2. ZEITRAUM-AUSWAHL
# ─────────────────────────────────────────────
TIMEFRAME_MAP = {
    "1T":   ("1d", "5m"),
    "5T":   ("5d", "15m"),
    "1M":   ("1mo", "60m"),
    "6M":   ("6mo", "1d"),
    "YTD":  ("ytd", "1d"),
    "1J":   ("1y", "1d"),
    "5J":   ("5y", "1wk"),
    "Max":  ("max", "1mo"),
}

st.write("") 
tf_cols = st.columns(len(TIMEFRAME_MAP))
selected_tf_label = st.session_state.get("selected_tf", "1J")

for i, label in enumerate(TIMEFRAME_MAP.keys()):
    with tf_cols[i]:
        if st.button(label, use_container_width=True, type="primary" if label == selected_tf_label else "secondary"):
            st.session_state["selected_tf"] = label
            st.rerun()

period, interval = TIMEFRAME_MAP[selected_tf_label]

# ─────────────────────────────────────────────
# 3. DATEN LADEN
# ─────────────────────────────────────────────
market_svc = get_market_service()

with st.spinner(f"Lade Chart für {current_ticker} ({selected_tf_label})..."):
    quote = client.get_quote(current_ticker)
    df = client.get_price_history(current_ticker, period, interval)
    analyst_info = market_svc.get_analyst_info(current_ticker)

if df.empty:
    st.error(f"❌ Keine Daten für **{current_ticker}** im Zeitraum {selected_tf_label}.")
    st.stop()

# ─────────────────────────────────────────────
# 4. HEADER & KPIs
# ─────────────────────────────────────────────
price_header(current_ticker, quote)

rating = analyst_info.get("recommendation", "N/A")
if isinstance(rating, str): rating = rating.title()

kpi_row([
    {"label": "Marktkapitalisierung", "value": format_large_number(quote.get("market_cap"))},
    {"label": "KGV (P/E)", "value": f"{quote.get('pe_ratio', 0):.2f}" if quote.get("pe_ratio") else "N/A"},
    {"label": "52W Hoch", "value": f"${quote.get('week_52_high', 0):,.2f}"},
    {"label": "Volumen", "value": format_large_number(quote.get("volume"))},
    {"label": "Analysten", "value": rating},
])

st.divider()

# ─────────────────────────────────────────────
# 5. CHART & INDIKATOREN
# ─────────────────────────────────────────────
with st.expander("⚙️ Technische Indikatoren konfigurieren", expanded=False):
    ind_cols = st.columns(4)
    with ind_cols[0]:
        show_sma = st.checkbox("SMA (20, 50, 200)", value=True)
        show_ema = st.checkbox("EMA (9)", value=False)
    with ind_cols[1]:
        show_bb = st.checkbox("Bollinger Bands", value=False)
        show_vol = st.checkbox("Volumen", value=True)
    with ind_cols[2]:
        show_rsi = st.checkbox("RSI (14)", value=True)
    with ind_cols[3]:
        show_macd = st.checkbox("MACD", value=True)

ti = TechnicalIndicators(df)
try:
    if show_sma: ti.add_sma([20, 50, 200])
    if show_ema: ti.add_ema([9])
    if show_bb:  ti.add_bollinger_bands()
    if show_rsi: ti.add_rsi()
    if show_macd: ti.add_macd()
    if show_vol: ti.add_volume_ma()
    df_chart = ti.df
except Exception as e:
    st.warning(f"Fehler bei Indikatoren: {e}")
    df_chart = df

indicators_dict = {
    "sma_20": show_sma, "sma_50": show_sma, "sma_200": show_sma,
    "ema_9": show_ema, "bb": show_bb,
    "rsi": show_rsi, "macd": show_macd, "volume": show_vol
}

fig = create_main_chart(df_chart, current_ticker, indicators_dict)
st.plotly_chart(fig, use_container_width=True)