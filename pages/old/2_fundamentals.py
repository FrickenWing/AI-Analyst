import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from services.market_service import get_market_service
from data.openbb_client import get_client
from ui.components.metrics import price_header
from ui.components.tables import financial_statement_table, news_table
from utils.formatters import fmt_price, fmt_pct, fmt_large

# --- Setup & Config ---
st.set_page_config(page_title="Fundamentals", page_icon="📊", layout="wide")

# Custom CSS für saubereres Layout
st.markdown("""
    <style>
    .kpi-card {
        background-color: #1e2329;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #333;
        text-align: center;
    }
    .kpi-label { font-size: 0.8rem; color: #888; }
    .kpi-value { font-size: 1.2rem; font-weight: bold; margin-top: 5px; }
    </style>
""", unsafe_allow_html=True)

# Session State Management
current_ticker = st.session_state.get("current_ticker", "AAPL")
st.sidebar.title("📊 Fundamentals")
ticker = st.sidebar.text_input("Ticker Symbol", current_ticker).upper()

if ticker != current_ticker:
    st.session_state["current_ticker"] = ticker
    st.rerun()

# Services
svc = get_market_service()
client = get_client()

# --- Helper: KPI Card ---
def render_kpi_card(label, value, help_text=None):
    st.markdown(f"""
    <div class="kpi-card" title="{help_text if help_text else ''}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

# --- Helper: Financial Trend Chart ---
def plot_financial_trend(df: pd.DataFrame, title: str, metric_name: str, color: str = "#00C805"):
    if df is None or df.empty: return None
    row = df[df.index.str.contains(metric_name, case=False, na=False)]
    if row.empty: return None
    
    try:
        x_values = [str(c)[:4] for c in df.columns]
        y_values = [float(v) for v in row.iloc[0].values if pd.notnull(v)]
        min_len = min(len(x_values), len(y_values))
        
        fig = go.Figure(go.Bar(
            x=x_values[:min_len], 
            y=y_values[:min_len],
            marker_color=color,
            name=metric_name
        ))
        fig.update_layout(
            title=dict(text=title, font=dict(size=14)),
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=250,
            margin=dict(t=30, b=0, l=0, r=0),
            yaxis=dict(showgrid=True, gridcolor="#333"),
            showlegend=False
        )
        return fig
    except: return None

# --- Daten laden ---
with st.spinner(f"Lade Daten für {ticker}..."):
    try:
        overview = svc.get_stock_overview(ticker)
        if not overview or not overview.get("price"):
            quote = client.get_quote(ticker)
            if quote: overview = overview or {}; overview.update(quote)
            
        metrics = svc.get_key_metrics(ticker)
        statements = svc.get_financial_statements(ticker)
        growth = svc.get_growth_metrics(ticker)
        analyst = svc.get_analyst_info(ticker)
        news = client.get_news(ticker, limit=5)
    except Exception as e:
        st.error(f"Fehler: {e}")
        st.stop()

if not overview:
    st.warning("Keine Daten gefunden.")
    st.stop()

# ==========================================
# 1. HEADER SECTION (Price + Key Stats)
# ==========================================

# Links: Preis Header
col_head_left, col_head_right = st.columns([1.5, 2.5])
with col_head_left:
    price_header(ticker, overview)

# Rechts: Die wichtigsten KPIs sofort sichtbar (ohne Tab)
with col_head_right:
    st.write("") # Spacer für vertikale Ausrichtung
    cols = st.columns(4)
    with cols[0]: render_kpi_card("Marktkapitalisierung", overview.get("fmt_market_cap", "N/A"))
    with cols[1]: render_kpi_card("KGV (P/E)", overview.get("fmt_pe", "N/A"))
    with cols[2]: render_kpi_card("52W Hoch", overview.get("fmt_52h", "N/A"))
    with cols[3]: render_kpi_card("Beta", str(overview.get("beta", "N/A")))

st.divider()

# ==========================================
# 2. MAIN CONTENT (Split View)
# ==========================================

# Layout: 70% Links (Deep Dive), 30% Rechts (Kontext/News)
main_col, side_col = st.columns([2.2, 1])

# --- RECHTE SPALTE (Der "Kontext") ---
with side_col:
    # A. Analysten Rating (Prominent oben)
    st.subheader("🎯 Analysten Konsensus")
    if analyst:
        rec = analyst.get("recommendation", "N/A")
        target = analyst.get("fmt_target", "N/A")
        upside = analyst.get("fmt_upside", "N/A")
        rec_color = "#00C805" if "Buy" in rec else "#FF3B30" if "Sell" in rec else "#FF9500"
        
        st.markdown(f"""
        <div style="border: 1px solid #444; border-radius: 8px; padding: 15px; margin-bottom: 20px;">
            <div style="text-align: center; font-size: 1.5rem; font-weight: bold; color: {rec_color}; margin-bottom: 10px;">
                {rec}
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 0.9rem;">
                <div>Kursziel Ø: <b>{target}</b></div>
                <div style="color: {rec_color};">Upside: <b>{upside}</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Keine Analystendaten.")

    # B. Profil
    with st.expander("🏢 Unternehmensprofil", expanded=True):
        st.caption(f"**Sektor:** {overview.get('sector','N/A')}")
        st.caption(f"**Industrie:** {overview.get('industry','N/A')}")
        desc = overview.get("description", "")
        if desc: st.write(desc[:400] + "..." if len(desc) > 400 else desc)
        if overview.get("website"): st.markdown(f"[Zur Webseite]({overview['website']})")

    # C. News (Immer sichtbar!)
    st.subheader("📰 Aktuelle News")
    # Wir nutzen hier eine kompakte Version der News Table
    if news:
        for n in news[:5]:
            st.markdown(f"""
            <div style="margin-bottom: 12px; font-size: 0.9rem;">
                <a href="{n.get('url')}" target="_blank" style="text-decoration: none; color: #4da6ff; font-weight: bold;">
                    {n.get('title')}
                </a>
                <div style="color: #888; font-size: 0.75rem; margin-top: 2px;">
                    {n.get('source')} • {str(n.get('published'))[:10]}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("Keine aktuellen Nachrichten.")

# --- LINKE SPALTE (Der "Deep Dive") ---
with main_col:
    # Tabs für verschiedene Detail-Ebenen
    tab_financials, tab_ratios, tab_growth = st.tabs([
        "💰 Finanzen & Charts", 
        "📐 Kennzahlen Matrix", 
        "📈 Wachstumsanalyse"
    ])

    # 1. Finanzen Tab
    with tab_financials:
        # Sub-Tabs für Income, Balance, Cashflow
        sub_t1, sub_t2, sub_t3 = st.tabs(["GuV (Income)", "Bilanz", "Cashflow"])
        
        income = statements.get("income", pd.DataFrame())
        balance = statements.get("balance", pd.DataFrame())
        cashflow = statements.get("cashflow", pd.DataFrame())

        with sub_t1:
            if not income.empty:
                c1, c2 = st.columns(2)
                with c1: st.plotly_chart(plot_financial_trend(income, "Umsatz (Revenue)", "Revenue"), use_container_width=True)
                with c2: st.plotly_chart(plot_financial_trend(income, "Gewinn (Net Income)", "Net Income", "#2962FF"), use_container_width=True)
                with st.expander("Detaillierte Tabelle ansehen"):
                    financial_statement_table(income, "GuV")
            else: st.info("Keine GuV Daten.")

        with sub_t2:
            if not balance.empty:
                c1, c2 = st.columns(2)
                with c1: st.plotly_chart(plot_financial_trend(balance, "Vermögen (Assets)", "Total Assets", "#9C27B0"), use_container_width=True)
                with c2: st.plotly_chart(plot_financial_trend(balance, "Verbindlichkeiten (Liab)", "Total Liab", "#FF5722"), use_container_width=True)
                with st.expander("Detaillierte Tabelle ansehen"):
                    financial_statement_table(balance, "Bilanz")
            else: st.info("Keine Bilanz Daten.")

        with sub_t3:
            if not cashflow.empty:
                st.plotly_chart(plot_financial_trend(cashflow, "Free Cash Flow", "Free Cash Flow", "#00BCD4"), use_container_width=True)
                with st.expander("Detaillierte Tabelle ansehen"):
                    financial_statement_table(cashflow, "Cashflow")
            else: st.info("Keine Cashflow Daten.")

    # 2. Kennzahlen Tab (Matrix)
    with tab_ratios:
        st.markdown("##### Bewertungs- & Profitabilitätskennzahlen")
        if metrics:
            # Wir bauen ein Grid
            cols = st.columns(3)
            for i, m in enumerate(metrics):
                lbl = m.get("label") or "N/A"
                val = m.get("value")
                cols[i % 3].markdown(f"**{lbl}**")
                cols[i % 3].caption(str(val) if val is not None else "N/A")
                if (i + 1) % 3 == 0: st.write("") # Zeilenumbruch
        else:
            st.info("Keine detaillierten Kennzahlen verfügbar.")

    # 3. Wachstum Tab
    with tab_growth:
        st.markdown("##### Wachstum im Vergleich (YoY)")
        if growth:
            g_cols = st.columns(3)
            for i, g in enumerate(growth[:9]):
                val = g.get("value")
                lbl = g.get("label") or "N/A"
                # Farbe für Wachstum: Grün wenn positiv
                color = "green" if val and isinstance(val, str) and not "-" in val else "red"
                
                with g_cols[i % 3]:
                    st.metric(label=lbl, value=val)
        else:
            st.info("Keine Wachstumsdaten verfügbar.")