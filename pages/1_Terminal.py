import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import numpy as np
from streamlit_lightweight_charts import renderLightweightCharts
from streamlit_searchbox import st_searchbox  # <-- NEU: Für Autocomplete
from services.market_service import get_market_service
from data.openbb_client import get_client
from ui.components.metrics import price_header
from ui.components.tables import financial_statement_table
from ui.components.charts import render_target_price_chart, render_recommendation_gauge
from utils.formatters import fmt_large

# --- CONFIG ---
st.set_page_config(page_title="Terminal", page_icon="💻", layout="wide")

st.markdown("""
<style>
    /* TRADINGVIEW STYLE CSS */
    .block-container { 
        padding-top: 3rem; 
        padding-bottom: 2rem; 
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 100%;
    }
    
    /* Searchbox Styling anpassen */
    div[data-testid="stSearchbox"] > div {
        background-color: #1e222d;
        border: 1px solid #2a2e39;
        border-radius: 4px;
        color: white;
    }
    
    /* Toolbar Button Styling */
    div[data-testid="stHorizontalBlock"] button {
        border-radius: 4px;
        font-weight: 600;
        border: 1px solid #333;
        background-color: #131722;
        color: #d1d4dc;
        font-size: 0.75rem;
        padding: 0.25rem 0.5rem;
    }
    div[data-testid="stHorizontalBlock"] button:hover {
        border-color: #2962FF;
        color: #2962FF;
    }
    
    /* Right Sidebar Card Styling */
    .tv-card {
        background-color: #1e222d;
        border: 1px solid #2a2e39;
        border-radius: 4px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .tv-header {
        font-size: 0.8rem;
        font-weight: bold;
        color: #787b86;
        margin-bottom: 8px;
        text-transform: uppercase;
    }
    .tv-value {
        font-size: 0.9rem;
        color: #d1d4dc;
        display: flex;
        justify-content: space-between;
        border-bottom: 1px solid #2a2e39;
        padding: 4px 0;
    }
    .tv-value:last-child { border-bottom: none; }
    
    /* News Styling */
    .news-item {
        margin-bottom: 12px;
        border-bottom: 1px solid #2a2e39;
        padding-bottom: 8px;
    }
    .news-item a {
        color: #d1d4dc;
        text-decoration: none;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .news-item a:hover { color: #2962FF; }
    .news-meta {
        font-size: 0.7rem;
        color: #787b86;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# --- STATE ---
if "ticker" not in st.session_state: st.session_state.ticker = "AAPL"
if "selected_range" not in st.session_state: st.session_state.selected_range = "1Y"

client = get_client()

# --- SMART SEARCH LOGIC ---
def search_ticker_api(searchterm: str):
    """
    Diese Funktion wird von st_searchbox bei jedem Tippen aufgerufen.
    Sie gibt eine Liste von Tupeln zurück: (Anzeige-Name, Rückgabe-Wert)
    """
    if not searchterm: 
        return []
    
    # Suche via Client (Yahoo/FMP)
    results = client.search_ticker(searchterm)
    
    # Formatierung für das Dropdown: "NVDA | NVIDIA Corp (NASDAQ)" -> "NVDA"
    return [
        (f"{r['ticker']} | {r['name']} ({r.get('exchange', 'N/A')})", r['ticker']) 
        for r in results
    ]

# --- LAYOUT: SUCHE ---
with st.container():
    # Die Searchbox ersetzt das alte Text Input
    selected_value = st_searchbox(
        search_ticker_api,
        key="ticker_search_box",
        placeholder="🔍 Ticker oder Firma suchen (z.B. Nvidia)...",
        label=None,
        clear_on_submit=True, # Löscht Text nach Auswahl (sauberer Look)
    )

    # Wenn etwas ausgewählt wurde -> State Update
    if selected_value and selected_value != st.session_state.ticker:
        st.session_state.ticker = selected_value
        st.rerun()

# --- SMART CONFIG ---
SMART_RANGES = {
    "1D": {"label": "1D", "api_interval": "1m", "api_period": "5d", "bar_spacing": 2.5, "desc": "Intraday"},
    "1W": {"label": "1W", "api_interval": "15m", "api_period": "1mo", "bar_spacing": 5.5, "desc": "Week"},
    "1M": {"label": "1M", "api_interval": "1h", "api_period": "6mo", "bar_spacing": 6.0, "desc": "Month"},
    "3M": {"label": "3M", "api_interval": "1d", "api_period": "2y", "bar_spacing": 12.0, "desc": "Quarter"},
    "1Y": {"label": "1Y", "api_interval": "1d", "api_period": "5y", "bar_spacing": 3.2, "desc": "Year"},
    "5Y": {"label": "5Y", "api_interval": "1wk", "api_period": "max", "bar_spacing": 3.0, "desc": "5 Years"},
    "ALL": {"label": "ALL", "api_interval": "1mo", "api_period": "max", "bar_spacing": 2.0, "desc": "Max"}
}

# Fix für State Validierung
if "selected_range" not in st.session_state or st.session_state.selected_range not in SMART_RANGES:
    st.session_state.selected_range = "1Y"

# --- DATEN LADEN ---
ticker = st.session_state.ticker
svc = get_market_service()

try:
    overview = svc.get_stock_overview(ticker)
except: overview = {}

if not overview:
    st.error(f"Keine Daten für {ticker} gefunden.")
    st.stop()

# =========================================================
# TRADINGVIEW LAYOUT
# =========================================================

main_col, side_col = st.columns([3.5, 1.2])

with main_col:
    # 1. HEADER
    p = overview.get('price', 0)
    c = overview.get('change', 0)
    cp = overview.get('change_pct', 0)
    color = "#00C805" if c >= 0 else "#FF3B30"
    
    st.markdown(f"""
    <div style="display: flex; align-items: baseline; gap: 15px; margin-bottom: 10px;">
        <h1 style="margin: 0; font-size: 2rem;">{ticker}</h1>
        <span style="font-size: 1.5rem; font-weight: bold;">{p:.2f}</span>
        <span style="font-size: 1.2rem; color: {color};">{c:+.2f} ({cp:+.2%})</span>
        <span style="color: #787b86; font-size: 0.9rem; align-self: center;">{overview.get('name','')} • {overview.get('exchange','')}</span>
    </div>
    """, unsafe_allow_html=True)

    # 2. TOOLBAR
    t_cols = st.columns(len(SMART_RANGES) + 4)
    range_keys = list(SMART_RANGES.keys())
    for i, r_key in enumerate(range_keys):
        if t_cols[i].button(r_key, key=f"btn_{r_key}", use_container_width=True):
            st.session_state.selected_range = r_key
            st.rerun()

    # 3. CHART
    current_cfg = SMART_RANGES[st.session_state.selected_range]
    
    with st.spinner(f"Loading {ticker}..."):
        hist_df = client.get_price_history(ticker, period=current_cfg["api_period"], interval=current_cfg["api_interval"])

    if not hist_df.empty:
        df_chart = hist_df.reset_index().copy()
        df_chart.columns = [c.lower() for c in df_chart.columns]
        date_col = next((c for c in df_chart.columns if 'date' in c or 'time' in c), None)
        
        if date_col:
            if current_cfg["api_interval"] in ["1m", "5m", "15m", "30m", "1h", "90m"]:
                df_chart['time'] = pd.to_datetime(df_chart[date_col]).astype('int64') // 10**9
            else:
                df_chart['time'] = pd.to_datetime(df_chart[date_col]).dt.strftime('%Y-%m-%d')
            
            candles_data = df_chart[['time', 'open', 'high', 'low', 'close']].to_dict('records')
            vol_data = [{'time': r['time'], 'value': r['volume'], 'color': 'rgba(0, 200, 5, 0.5)' if r['close'] >= r['open'] else 'rgba(255, 59, 48, 0.5)'} for _, r in df_chart.iterrows()]

            chart_options = {
                "layout": {"background": {"type": 'solid', "color": '#131722'}, "textColor": '#d1d4dc'},
                "grid": {"vertLines": {"color": '#1e222d'}, "horzLines": {"color": '#1e222d'}},
                "timeScale": {"timeVisible": True, "secondsVisible": False, "barSpacing": current_cfg["bar_spacing"], "borderColor": "#2a2e39"},
                "rightPriceScale": {"borderColor": "#2a2e39"},
                "crosshair": {"mode": 1, "vertLine": {"color": "#758696", "style": 3}, "horzLine": {"color": "#758696", "style": 3}},
                "height": 600
            }
            
            renderLightweightCharts([
                {"chart": chart_options, "series": [{"type": 'Candlestick', "data": candles_data, "options": {"upColor": '#00C805', "downColor": '#FF3B30', "borderVisible": False, "wickUpColor": '#00C805', "wickDownColor": '#FF3B30'}}]},
                {"chart": {"height": 100, "layout": chart_options["layout"], "timeScale": chart_options["timeScale"]}, "series": [{"type": 'Histogram', "data": vol_data, "options": {"priceFormat": {"type": 'volume'}}}]}
            ], key=f"tv_{ticker}_{st.session_state.selected_range}")
    else:
        st.info("Chart Daten werden geladen oder sind nicht verfügbar...")

    # 4. BOTTOM PANEL
    st.write("")
    tab_overview, tab_fin, tab_analysis = st.tabs(["Company Profile", "Financials", "Analysis"])
    
    with tab_overview:
        st.markdown(f"**{overview.get('name')}**")
        st.caption(f"{overview.get('sector')} | {overview.get('industry')}")
        st.write(overview.get('description', 'No description.'))
        
    with tab_fin:
        statements = svc.get_financial_statements(ticker)
        inc = statements.get("income", pd.DataFrame())
        bal = statements.get("balance", pd.DataFrame())
        if not inc.empty: financial_statement_table(inc, "Income Statement")
        if not bal.empty: financial_statement_table(bal, "Balance Sheet")

    with tab_analysis:
        analyst = svc.get_analyst_info(ticker)
        if analyst and analyst.get("target_mean"):
             c1, c2 = st.columns([1,2])
             with c1: st.plotly_chart(render_recommendation_gauge(3.5), use_container_width=True)
             with c2: 
                 st.plotly_chart(render_target_price_chart(p, analyst['target_low'], analyst['target_mean'], analyst['target_high']), use_container_width=True)
        else: st.info("No analyst data.")

with side_col:
    # --- RECHTE SEITE ---
    
    # 1. KEY STATS
    st.markdown("### Key Statistics")
    stats = client.get_key_stats(ticker)
    
    if stats:
        with st.container():
            st.markdown('<div class="tv-card">', unsafe_allow_html=True)
            
            st.markdown('<div class="tv-header">Valuation</div>', unsafe_allow_html=True)
            for k, v in stats.get("Valuation", {}).items():
                val_str = fmt_large(v) if isinstance(v, (int, float)) and v > 1000 else str(v)
                st.markdown(f'<div class="tv-value"><span>{k}</span><span style="font-weight:bold;">{val_str}</span></div>', unsafe_allow_html=True)
            
            st.markdown('<div class="tv-header" style="margin-top:10px;">Profitability</div>', unsafe_allow_html=True)
            for k, v in stats.get("Profitability", {}).items():
                st.markdown(f'<div class="tv-value"><span>{k}</span><span style="font-weight:bold;">{v}</span></div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.caption("No details available.")

    # 2. NEWS
    st.markdown("### Headlines")
    news_items = client.get_news(ticker, limit=10)
    
    if news_items:
        st.markdown('<div class="tv-card">', unsafe_allow_html=True)
        for n in news_items:
            try:
                dt_str = " ".join(n['published'].split(" ")[1:3])
            except: dt_str = ""
            
            st.markdown(f"""
            <div class="news-item">
                <div style="display:flex; justify-content:space-between;">
                    <span style="color:#787b86; font-size:0.7rem;">{n.get('source')}</span>
                    <span style="color:#787b86; font-size:0.7rem;">{dt_str}</span>
                </div>
                <a href="{n.get('url')}" target="_blank">{n.get('title')}</a>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.caption("No news found.")