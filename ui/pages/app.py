"""
app.py - Haupt-Entry-Point für OpenBB Terminal Pro

Streamlit Multi-Page App.
Start: streamlit run app.py
"""

import streamlit as st
from data.openbb_client import get_client
from config import APP_TITLE, APP_ICON, MARKET_INDICES, COLORS

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stMetric { background: #1e2329; padding: 12px; border-radius: 8px; }
    .ticker-card {
        background: #1e2329; padding: 12px 16px;
        border-radius: 8px; border: 1px solid #2d3748; text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────
with st.sidebar:
    st.title(f"{APP_ICON} {APP_TITLE}")
    st.caption("Powered by OpenBB Platform")
    st.divider()

    st.markdown("### 🧭 Navigation")
    st.page_link("app.py",                          label="🏠 Dashboard")
    st.page_link("ui/pages/1_📈_charts.py",         label="📈 Chart Analyse")
    st.page_link("ui/pages/2_📊_fundamentals.py",   label="📊 Fundamentals")
    st.page_link("ui/pages/3_🔍_screener.py",       label="🔍 Screener")
    st.page_link("ui/pages/4_📰_news.py",           label="📰 News")
    st.page_link("ui/pages/5_💼_portfolio.py",      label="💼 Portfolio")

    st.divider()
    if st.button("🔄 Daten refreshen"):
        get_client().clear_cache()
        st.rerun()

# ── Market Overview ───────────────────────────
st.markdown("## 🌍 Market Overview")
st.caption("Live Marktdaten via OpenBB Platform")

client = get_client()

index_tickers = {
    "^GSPC":  "S&P 500",
    "^IXIC":  "NASDAQ",
    "^DJI":   "Dow Jones",
    "^VIX":   "VIX",
    "^GDAXI": "DAX",
}

cols = st.columns(len(index_tickers))
for col, (symbol, name) in zip(cols, index_tickers.items()):
    with col:
        quote      = client.get_quote(symbol)
        price      = quote.get("price", 0)
        change_pct = quote.get("change_pct", 0)
        color      = COLORS["bullish"] if change_pct >= 0 else COLORS["bearish"]
        arrow      = "▲" if change_pct >= 0 else "▼"
        st.markdown(f"""
        <div class="ticker-card">
            <div style="font-size:0.8rem; color:#8b95a1;">{name}</div>
            <div style="font-size:1.3rem; font-weight:700;">{price:,.2f}</div>
            <div style="color:{color}; font-size:0.9rem;">{arrow} {change_pct:+.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ── Watchlist ─────────────────────────────────
st.markdown("### ⭐ Watchlist")
watchlist = st.session_state.get("watchlist", ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN"])

for i in range(0, len(watchlist), 5):
    chunk    = watchlist[i:i+5]
    wl_cols  = st.columns(len(chunk))
    for col, ticker in zip(wl_cols, chunk):
        with col:
            quote      = client.get_quote(ticker)
            price      = quote.get("price", 0)
            change_pct = quote.get("change_pct", 0)
            color      = COLORS["bullish"] if change_pct >= 0 else COLORS["bearish"]
            arrow      = "▲" if change_pct >= 0 else "▼"
            st.markdown(f"""
            <div class="ticker-card">
                <div style="font-weight:700;">{ticker}</div>
                <div>${price:,.2f}</div>
                <div style="color:{color}; font-size:0.85rem;">{arrow} {change_pct:+.2f}%</div>
            </div>
            """, unsafe_allow_html=True)

st.divider()

# ── Module-Übersicht ──────────────────────────
st.markdown("### 🗺️ Verfügbare Module")
mc1, mc2, mc3, mc4, mc5 = st.columns(5)
mc1.markdown("**📈 Charts**\nTechnische Analyse\nIndikatoren & Signale")
mc2.markdown("**📊 Fundamentals**\nGuV · Bilanz · Cashflow\nAnalysten · KPIs")
mc3.markdown("**🔍 Screener**\nMulti-Filter\nComposite Score")
mc4.markdown("**📰 News**\nTicker News\nWatchlist Feed")
mc5.markdown("**💼 Portfolio**\nP&L Tracking\nPortfolio Analytics")

st.divider()

# ── Projekt-Status ────────────────────────────
st.markdown("### 🗺️ Projekt Status")
c1, c2, c3, c4 = st.columns(4)
c1.progress(0.85, text="Phase 1: Foundation 85%")
c2.progress(0.80, text="Phase 2: Core Features 80%")
c3.progress(0.00, text="Phase 3: Advanced 0%")
c4.progress(0.00, text="Phase 4: Polish 0%")
st.caption("📍 Aktuell: Phase 2 fast fertig – Phase 3 (Portfolio Analytics, Macro) als nächstes")
