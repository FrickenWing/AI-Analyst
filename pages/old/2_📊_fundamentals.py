"""
ui/pages/2_📊_fundamentals.py - Fundamentalanalyse Seite

Zeigt:
- Unternehmens-Profil & Kurs-Header
- Key Metrics (P/E, P/B, ROE, Margen, ...)
- Financial Statements (GuV, Bilanz, Cashflow)
- Wachstumskennzahlen
- Analysten-Schätzungen
- News
"""

import streamlit as st

from services.market_service import get_market_service
from data.openbb_client import get_client
from ui.components.metrics import kpi_row, price_header, format_large_number
from ui.components.tables import (
    financial_statement_table,
    news_table,
    plotly_bar_chart,
)
from ui.components.sidebar import render_ticker_input
from utils.formatters import fmt_price, fmt_pct, fmt_large, color_pct

# ─────────────────────────────────────────────
st.set_page_config(page_title="Fundamentals", page_icon="📊", layout="wide")

# ── Sidebar ───────────────────────────────────
st.sidebar.title("📊 Fundamentals")
ticker = render_ticker_input()

# ── Daten laden ───────────────────────────────
svc    = get_market_service()
client = get_client()

with st.spinner(f"Lade Fundamentaldaten für {ticker}..."):
    overview    = svc.get_stock_overview(ticker)
    metrics     = svc.get_key_metrics(ticker)
    statements  = svc.get_financial_statements(ticker)
    growth      = svc.get_growth_metrics(ticker)
    analyst     = svc.get_analyst_info(ticker)
    news        = client.get_news(ticker, limit=8)

# Fehlerbehandlung
if not overview.get("name"):
    st.error(f"❌ Keine Daten für **{ticker}**. Bitte prüfe das Ticker-Symbol.")
    st.stop()

# ── Preis-Header ──────────────────────────────
price_header(ticker, overview)

# Sektor / Industrie / Exchange Info
col1, col2, col3, col4 = st.columns(4)
col1.caption(f"🏢 **Sektor:** {overview.get('sector', 'N/A')}")
col2.caption(f"🏭 **Industrie:** {overview.get('industry', 'N/A')}")
col3.caption(f"🌍 **Land:** {overview.get('country', 'N/A')}")
col4.caption(f"📊 **Börse:** {overview.get('exchange', 'N/A')}")

st.divider()

# ── Tabs ──────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Übersicht",
    "💰 Financials",
    "📐 Kennzahlen",
    "🎯 Analysten",
    "📰 News",
])

# ════════════════════════════════════════════
# TAB 1: ÜBERSICHT
# ════════════════════════════════════════════
with tab1:
    # Quick Stats Row
    st.markdown("### 📊 Key Statistics")
    kpi_row([
        {"label": "Market Cap",   "value": overview.get("fmt_market_cap", "N/A")},
        {"label": "P/E Ratio",    "value": overview.get("fmt_pe", "N/A")},
        {"label": "52W High",     "value": overview.get("fmt_52h", "N/A")},
        {"label": "52W Low",      "value": overview.get("fmt_52l", "N/A")},
        {"label": "Volumen",      "value": overview.get("fmt_volume", "N/A")},
    ])

    st.divider()

    # Wachstum
    if growth:
        st.markdown("### 📈 Wachstum")
        g_cols = st.columns(len(growth))
        for col, g in zip(g_cols, growth):
            col.metric(label=g["label"], value=g["value"])

    st.divider()

    # Unternehmensbeschreibung
    st.markdown("### 🏢 Unternehmensprofil")
    col_info, col_meta = st.columns([3, 1])

    with col_info:
        desc = overview.get("description", "")
        if desc:
            st.markdown(desc[:800] + "..." if len(desc) > 800 else desc)
        else:
            st.info("Keine Beschreibung verfügbar.")

    with col_meta:
        st.markdown("**Details**")
        if overview.get("ceo"):
            st.caption(f"👤 CEO: {overview['ceo']}")
        if overview.get("employees"):
            st.caption(f"👥 Mitarbeiter: {overview['employees']:,}")
        if overview.get("website"):
            st.caption(f"🌐 [{overview['website']}]({overview['website']})")

# ════════════════════════════════════════════
# TAB 2: FINANCIAL STATEMENTS
# ════════════════════════════════════════════
with tab2:
    st.markdown("### 💰 Financial Statements")

    income   = statements.get("income")
    balance  = statements.get("balance")
    cashflow = statements.get("cashflow")

    fs_tab1, fs_tab2, fs_tab3 = st.tabs([
        "📋 Gewinn & Verlust",
        "🏦 Bilanz",
        "💸 Cashflow"
    ])

    with fs_tab1:
        if income is not None and not income.empty:
            # Balken-Charts für Revenue & Net Income
            try:
                rev_row = income[income.index.str.contains("Total Revenue", case=False, na=False)]
                ni_row  = income[income.index.str.contains("Net Income", case=False, na=False)]

                if not rev_row.empty:
                    cols_str = [str(c)[:4] for c in rev_row.columns]
                    rev_vals = [float(v) for v in rev_row.iloc[0].values if v]
                    if rev_vals:
                        st.plotly_chart(
                            plotly_bar_chart(cols_str[:len(rev_vals)], rev_vals, "Umsatz (jährlich)", color_positive=False),
                            use_container_width=True
                        )
            except Exception:
                pass

            financial_statement_table(income, "Gewinn & Verlustrechnung")
        else:
            st.info("Keine GuV-Daten verfügbar.")

    with fs_tab2:
        financial_statement_table(balance, "Bilanz")

    with fs_tab3:
        if cashflow is not None and not cashflow.empty:
            try:
                fcf_row = cashflow[cashflow.index.str.contains("Free Cash", case=False, na=False)]
                if not fcf_row.empty:
                    cols_str = [str(c)[:4] for c in fcf_row.columns]
                    fcf_vals = [float(v) if v else 0 for v in fcf_row.iloc[0].values]
                    if fcf_vals:
                        st.plotly_chart(
                            plotly_bar_chart(cols_str[:len(fcf_vals)], fcf_vals, "Free Cashflow"),
                            use_container_width=True
                        )
            except Exception:
                pass
            financial_statement_table(cashflow, "Cashflow Statement")
        else:
            st.info("Keine Cashflow-Daten verfügbar.")

# ════════════════════════════════════════════
# TAB 3: KENNZAHLEN-ÜBERSICHT
# ════════════════════════════════════════════
with tab3:
    st.markdown("### 📐 Bewertungs- & Qualitätskennzahlen")

    if metrics:
        # In 3 Spalten anordnen
        col_a, col_b, col_c = st.columns(3)
        for i, m in enumerate(metrics):
            col = [col_a, col_b, col_c][i % 3]
            with col:
                st.metric(
                    label=m.get("label", ""),
                    value=m.get("value", "N/A"),
                    help=m.get("help"),
                )
    else:
        st.info("Keine Kennzahlen verfügbar.")

    st.divider()

    # Kennzahlen-Erklärungen
    with st.expander("📚 Kennzahlen erklärt"):
        st.markdown("""
        | Kennzahl | Bedeutung | Gut wenn |
        |----------|-----------|----------|
        | **P/E (TTM)** | Kurs / Jahresgewinn | < Branchendurchschnitt |
        | **P/E (Fwd)** | Kurs / erwarteter Gewinn | Zeigt Zukunftserwartung |
        | **P/B** | Kurs / Buchwert | < 1 = unter Substanzwert |
        | **P/S** | Kurs / Umsatz | Für unprofitable Firmen |
        | **EV/EBITDA** | Unternehmenswert / EBITDA | < 10 = günstig |
        | **ROE** | Eigenkapitalrendite | > 15% = gut |
        | **ROA** | Gesamtkapitalrendite | > 5% = gut |
        | **Net Margin** | Netto-Gewinnmarge | Je höher desto besser |
        | **Beta** | Markt-Sensitivität | < 1 = defensiv |
        """)

# ════════════════════════════════════════════
# TAB 4: ANALYSTEN
# ════════════════════════════════════════════
with tab4:
    st.markdown("### 🎯 Analysten-Empfehlungen")

    if analyst:
        rec = analyst.get("recommendation", "N/A")
        rec_colors = {
            "Strong Buy": "#00e676", "Buy": "#69f0ae",
            "Hold": "#ffab40", "Sell": "#ff6e40", "Strong Sell": "#ff1744",
        }
        rec_color = rec_colors.get(rec, "#8b95a1")

        col1, col2, col3, col4 = st.columns(4)

        col1.markdown(f"""
        <div style="text-align:center; padding:20px; background:#1e2329; border-radius:8px;">
            <div style="font-size:0.85rem; color:#8b95a1; margin-bottom:8px;">Consensus</div>
            <div style="font-size:1.5rem; font-weight:700; color:{rec_color};">{rec}</div>
            <div style="font-size:0.8rem; color:#8b95a1;">{analyst.get('num_analysts', 0)} Analysten</div>
        </div>
        """, unsafe_allow_html=True)

        col2.metric("Kursziel (Ø)",  analyst.get("fmt_target", "N/A"))
        col3.metric("Kursziel Hoch", fmt_price(analyst.get("target_high")))
        col4.metric("Upside Potenzial", analyst.get("fmt_upside", "N/A"))
    else:
        st.info("Keine Analysten-Daten verfügbar.")

# ════════════════════════════════════════════
# TAB 5: NEWS
# ════════════════════════════════════════════
with tab5:
    st.markdown(f"### 📰 Aktuelle News: {ticker}")
    news_table(news)
