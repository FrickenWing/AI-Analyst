import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from services.market_service import get_market_service
from data.openbb_client import get_client
from ui.components.metrics import kpi_row, price_header
from ui.components.tables import financial_statement_table, news_table, plotly_bar_chart
from ui.components.sidebar import render_ticker_input
from utils.formatters import fmt_price, fmt_pct, fmt_large

# --- Setup & Config ---
st.set_page_config(page_title="Fundamentals", page_icon="📊", layout="wide")

# Session State Management für Ticker
current_ticker = st.session_state.get("current_ticker", "AAPL")
st.sidebar.title("📊 Fundamentals")
ticker = st.sidebar.text_input("Ticker Symbol", current_ticker).upper()

if ticker != current_ticker:
    st.session_state["current_ticker"] = ticker
    st.rerun() # Seite neu laden bei Änderung

# Services initialisieren
svc = get_market_service()
client = get_client()

# --- Helper Funktionen für Charts ---
def plot_financial_trend(df: pd.DataFrame, title: str, metric_name: str, color: str = "#00C805"):
    """Erstellt einen Trend-Chart aus einem Financial DataFrame"""
    if df is None or df.empty:
        return None
    
    # Suche nach der Zeile (case insensitive)
    row = df[df.index.str.contains(metric_name, case=False, na=False)]
    if row.empty:
        return None
        
    # Daten extrahieren (die Spalten sind meist Jahre/Quartale)
    try:
        x_values = [str(c)[:4] for c in df.columns] # Nur Jahr nehmen
        y_values = [float(v) for v in row.iloc[0].values if pd.notnull(v)]
        
        # Sicherstellen, dass x und y gleich lang sind
        min_len = min(len(x_values), len(y_values))
        x_values = x_values[:min_len]
        y_values = y_values[:min_len]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=x_values, 
            y=y_values,
            name=metric_name,
            marker_color=color
        ))
        
        fig.update_layout(
            title=title,
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=300,
            margin=dict(t=40, b=20, l=20, r=20),
            yaxis=dict(showgrid=True, gridcolor="#333"),
        )
        return fig
    except Exception as e:
        print(f"Chart Error: {e}")
        return None

# --- Hauptlogik ---

# Daten laden
with st.spinner(f"Lade Fundamentaldaten für {ticker}..."):
    try:
        overview   = svc.get_stock_overview(ticker)
        # Fallback, falls Overview fehlschlägt
        if not overview or not overview.get("price"):
             # Versuch über Client direkt falls Service nichts liefert
            quote = client.get_quote(ticker)
            if quote: overview = overview or {}
            overview.update(quote)

        metrics    = svc.get_key_metrics(ticker)
        statements = svc.get_financial_statements(ticker)
        growth     = svc.get_growth_metrics(ticker)
        analyst    = svc.get_analyst_info(ticker)
        news       = client.get_news(ticker, limit=5)
    except Exception as e:
        st.error(f"Fehler beim Laden der Daten: {e}")
        st.stop()

if not overview:
    st.warning(f"Keine Daten für **{ticker}** gefunden. Bitte prüfe das Symbol.")
    st.stop()

# 1. Header Area
price_header(ticker, overview)

# Meta Informationen
col1, col2, col3, col4 = st.columns(4)
col1.caption(f"🏢 **Sektor:** {overview.get('sector','N/A')}")
col2.caption(f"🏭 **Industrie:** {overview.get('industry','N/A')}")
col3.caption(f"🌍 **Land:** {overview.get('country','N/A')}")
col4.caption(f"📊 **Börse:** {overview.get('exchange','N/A')}")

st.divider()

# 2. Tabs
tab_overview, tab_financials, tab_ratios, tab_analysis = st.tabs([
    "📈 Übersicht & Profil", 
    "💰 Finanzen (GuV/Bilanz)", 
    "📐 Kennzahlen", 
    "🎯 Analysten & News"
])

# --- TAB 1: ÜBERSICHT ---
with tab_overview:
    col_main, col_side = st.columns([2, 1])
    
    with col_main:
        st.subheader("Unternehmensprofil")
        desc = overview.get("description", "")
        if desc:
            st.info(desc[:1000] + "..." if len(desc) > 1000 else desc)
        else:
            st.write("Keine Beschreibung verfügbar.")
            
        st.subheader("Wachstum (YoY)")
        if growth:
            # FIX: Sicherstellen, dass growth eine Liste ist und keine Nones enthält
            cols = st.columns(3)
            for i, g in enumerate(growth[:6]): # Max 6 Wachstumsmetriken
                # Hier lag der Fehler: g.get("label") war None
                lbl = g.get("label")
                if not lbl: 
                    lbl = "N/A"
                
                cols[i % 3].metric(label=str(lbl), value=g.get("value"))
        else:
            st.text("Keine Wachstumsdaten verfügbar.")

    with col_side:
        st.subheader("Stammdaten")
        kpi_data = [
            {"label": "Marktkapitalisierung", "value": overview.get("fmt_market_cap", "N/A")},
            {"label": "KGV (P/E)", "value": overview.get("fmt_pe", "N/A")},
            {"label": "Volumen", "value": overview.get("fmt_volume", "N/A")},
            {"label": "52W Hoch", "value": overview.get("fmt_52h", "N/A")},
            {"label": "52W Tief", "value": overview.get("fmt_52l", "N/A")},
            {"label": "Beta", "value": str(overview.get("beta", "N/A"))},
        ]
        
        # Eigene kleine Tabelle für Stammdaten statt KPI Row für vertikale Ansicht
        df_meta = pd.DataFrame(kpi_data)
        st.dataframe(
            df_meta, 
            hide_index=True, 
            column_config={"label": "Metrik", "value": "Wert"},
            use_container_width=True
        )

        st.markdown("---")
        if overview.get("website"):
             st.markdown(f"🌐 **Webseite:** [{overview['website']}]({overview['website']})")
        if overview.get("ceo"):
             st.markdown(f"👤 **CEO:** {overview['ceo']}")

# --- TAB 2: FINANCIALS ---
with tab_financials:
    st.caption("Daten basierend auf den letzten verfügbaren Jahresberichten.")
    
    income = statements.get("income", pd.DataFrame())
    balance = statements.get("balance", pd.DataFrame())
    cashflow = statements.get("cashflow", pd.DataFrame())

    t1, t2, t3 = st.tabs(["GuV (Income)", "Bilanz (Balance)", "Cashflow"])

    with t1:
        c1, c2 = st.columns([1, 1])
        with c1:
            # Chart für Umsatz
            fig_rev = plot_financial_trend(income, "Umsatzentwicklung", "Revenue", "#4CAF50")
            if fig_rev: st.plotly_chart(fig_rev, use_container_width=True)
        with c2:
            # Chart für Net Income
            fig_inc = plot_financial_trend(income, "Netto-Gewinn Entwicklung", "Net Income", "#2196F3")
            if fig_inc: st.plotly_chart(fig_inc, use_container_width=True)
            
        financial_statement_table(income, "Gewinn- und Verlustrechnung")

    with t2:
        c1, c2 = st.columns([1, 1])
        with c1:
             fig_assets = plot_financial_trend(balance, "Gesamtvermögen", "Total Assets", "#9C27B0")
             if fig_assets: st.plotly_chart(fig_assets, use_container_width=True)
        with c2:
             fig_liab = plot_financial_trend(balance, "Gesamtverbindlichkeiten", "Total Liab", "#FF5722")
             if fig_liab: st.plotly_chart(fig_liab, use_container_width=True)

        financial_statement_table(balance, "Bilanz")

    with t3:
        fig_cf = plot_financial_trend(cashflow, "Free Cash Flow", "Free Cash Flow", "#00BCD4")
        if fig_cf: st.plotly_chart(fig_cf, use_container_width=True)
        financial_statement_table(cashflow, "Cashflow Rechnung")

# --- TAB 3: KENNZAHLEN ---
with tab_ratios:
    st.markdown("### 📊 Detaillierte Kennzahlen")
    
    if metrics:
        # Split metrics in chunks of 4 for rows
        cols_per_row = 4
        for i in range(0, len(metrics), cols_per_row):
            cols = st.columns(cols_per_row)
            batch = metrics[i:i+cols_per_row]
            for col, m in zip(cols, batch):
                with col:
                    # FIX: Auch hier Robustheit erhöhen
                    lbl = m.get("label") or "N/A"
                    val = m.get("value")
                    st.metric(
                        label=str(lbl), 
                        value=val if val is not None else "N/A",
                        help=m.get("help")
                    )
            st.divider()
    else:
        st.info("Keine detaillierten Kennzahlen verfügbar.")

# --- TAB 4: ANALYSE & NEWS ---
with tab_analysis:
    col_analyst, col_news = st.columns([1, 1])
    
    with col_analyst:
        st.subheader("🎯 Analysten Meinung")
        if analyst:
            rec = analyst.get("recommendation", "N/A")
            target = analyst.get("fmt_target", "N/A")
            upside = analyst.get("fmt_upside", "N/A")
            
            # Farb-Logik für Empfehlung
            rec_color = "green" if "Buy" in rec else "red" if "Sell" in rec else "orange"
            
            st.markdown(f"""
            <div style="padding: 20px; border: 1px solid #333; border-radius: 10px; text-align: center;">
                <h2 style="color: {rec_color}; margin: 0;">{rec}</h2>
                <p style="color: #888;">Konsensus</p>
                <hr style="border-color: #333;">
                <div style="display: flex; justify-content: space-around;">
                    <div>
                        <div style="font-size: 1.2rem; font-weight: bold;">{target}</div>
                        <div style="font-size: 0.8rem; color: #888;">Kursziel Ø</div>
                    </div>
                    <div>
                        <div style="font-size: 1.2rem; font-weight: bold; color: {rec_color};">{upside}</div>
                        <div style="font-size: 0.8rem; color: #888;">Potenzial</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if analyst.get("target_high") and analyst.get("target_low"):
                st.write("")
                st.write(f"**Range:** {fmt_price(analyst['target_low'])} - {fmt_price(analyst['target_high'])}")
        else:
            st.info("Keine Analystendaten verfügbar.")

    with col_news:
        st.subheader(f"📰 Neueste Nachrichten zu {ticker}")
        news_table(news)