"""pages/2_fundamentals.py - Fundamentalanalyse"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from services.market_service import get_market_service
from data.openbb_client import get_client
from ui.components.metrics import kpi_row, price_header, format_large_number
from ui.components.tables import financial_statement_table, news_table, plotly_bar_chart
from ui.components.sidebar import render_ticker_input
from utils.formatters import fmt_price, fmt_pct, fmt_large

st.set_page_config(page_title="Fundamentals", page_icon="📊", layout="wide")

st.sidebar.title("📊 Fundamentals")
ticker = render_ticker_input()

svc    = get_market_service()
client = get_client()

with st.spinner(f"Lade Fundamentaldaten für {ticker}..."):
    overview   = svc.get_stock_overview(ticker)
    metrics    = svc.get_key_metrics(ticker)
    statements = svc.get_financial_statements(ticker)
    growth     = svc.get_growth_metrics(ticker)
    analyst    = svc.get_analyst_info(ticker)
    news       = client.get_news(ticker, limit=8)

if not overview.get("name"):
    st.error(f"❌ Keine Daten für **{ticker}**.")
    st.stop()

price_header(ticker, overview)

col1, col2, col3, col4 = st.columns(4)
col1.caption(f"🏢 **Sektor:** {overview.get('sector','N/A')}")
col2.caption(f"🏭 **Industrie:** {overview.get('industry','N/A')}")
col3.caption(f"🌍 **Land:** {overview.get('country','N/A')}")
col4.caption(f"📊 **Börse:** {overview.get('exchange','N/A')}")

st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Übersicht", "💰 Financials", "📐 Kennzahlen", "🎯 Analysten", "📰 News"
])

with tab1:
    st.markdown("### 📊 Key Statistics")
    kpi_row([
        {"label": "Market Cap",  "value": overview.get("fmt_market_cap","N/A")},
        {"label": "P/E Ratio",   "value": overview.get("fmt_pe","N/A")},
        {"label": "52W High",    "value": overview.get("fmt_52h","N/A")},
        {"label": "52W Low",     "value": overview.get("fmt_52l","N/A")},
        {"label": "Volumen",     "value": overview.get("fmt_volume","N/A")},
    ])
    st.divider()
    if growth:
        st.markdown("### 📈 Wachstum")
        g_cols = st.columns(len(growth))
        for col, g in zip(g_cols, growth):
            col.metric(label=g["label"], value=g["value"])
    st.divider()
    st.markdown("### 🏢 Unternehmensprofil")
    col_info, col_meta = st.columns([3,1])
    with col_info:
        desc = overview.get("description","")
        st.markdown(desc[:800] + "..." if len(desc) > 800 else desc or "Keine Beschreibung.")
    with col_meta:
        if overview.get("ceo"):       st.caption(f"👤 CEO: {overview['ceo']}")
        if overview.get("employees"): st.caption(f"👥 {overview['employees']:,} Mitarbeiter")
        if overview.get("website"):   st.caption(f"🌐 [{overview['website']}]({overview['website']})")

with tab2:
    st.markdown("### 💰 Financial Statements")
    income   = statements.get("income")
    balance  = statements.get("balance")
    cashflow = statements.get("cashflow")
    fs1, fs2, fs3 = st.tabs(["📋 Gewinn & Verlust", "🏦 Bilanz", "💸 Cashflow"])
    with fs1:
        if income is not None and not income.empty:
            try:
                rev_row = income[income.index.str.contains("Total Revenue", case=False, na=False)]
                if not rev_row.empty:
                    cols_str = [str(c)[:4] for c in rev_row.columns]
                    rev_vals = [float(v) for v in rev_row.iloc[0].values if v and str(v) != "nan"]
                    if rev_vals:
                        st.plotly_chart(plotly_bar_chart(cols_str[:len(rev_vals)], rev_vals, "Umsatz", False), use_container_width=True)
            except Exception: pass
            financial_statement_table(income, "Gewinn & Verlustrechnung")
        else: st.info("Keine GuV-Daten verfügbar.")
    with fs2: financial_statement_table(balance, "Bilanz")
    with fs3: financial_statement_table(cashflow, "Cashflow Statement")

with tab3:
    st.markdown("### 📐 Kennzahlen")
    if metrics:
        col_a, col_b, col_c = st.columns(3)
        for i, m in enumerate(metrics):
            with [col_a, col_b, col_c][i % 3]:
                st.metric(label=m.get("label",""), value=m.get("value","N/A"), help=m.get("help"))
    else: st.info("Keine Kennzahlen verfügbar.")

with tab4:
    st.markdown("### 🎯 Analysten-Empfehlungen")
    if analyst:
        rec = analyst.get("recommendation","N/A")
        rec_colors = {"Strong Buy":"#00e676","Buy":"#69f0ae","Hold":"#ffab40","Sell":"#ff6e40","Strong Sell":"#ff1744"}
        color = rec_colors.get(rec,"#8b95a1")
        c1,c2,c3,c4 = st.columns(4)
        c1.markdown(f'<div style="text-align:center;padding:20px;background:#1e2329;border-radius:8px;"><div style="font-size:0.85rem;color:#8b95a1;">Consensus</div><div style="font-size:1.5rem;font-weight:700;color:{color};">{rec}</div><div style="font-size:0.8rem;color:#8b95a1;">{analyst.get("num_analysts",0)} Analysten</div></div>', unsafe_allow_html=True)
        c2.metric("Kursziel (Ø)",  analyst.get("fmt_target","N/A"))
        c3.metric("Kursziel Hoch", fmt_price(analyst.get("target_high")))
        c4.metric("Upside",        analyst.get("fmt_upside","N/A"))
    else: st.info("Keine Analysten-Daten verfügbar.")

with tab5:
    st.markdown(f"### 📰 Aktuelle News: {ticker}")
    news_table(news)
