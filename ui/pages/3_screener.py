"""pages/3_screener.py - Stock Screener"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from services.screener_service import get_screener_service, UNIVERSES
from ui.components.tables import screener_result_table

st.set_page_config(page_title="Screener", page_icon="🔍", layout="wide")

st.sidebar.title("🔍 Stock Screener")
st.sidebar.caption("Filtere Aktien nach deinen Kriterien")

universe_labels = {
    "mega_cap_us": "🇺🇸 US Mega Cap (Top 10)",
    "tech_growth":  "💻 Tech Growth",
    "dividends":    "💰 Dividenden-Aktien",
    "dax_top10":    "🇩🇪 DAX Top 10",
    "custom":       "✏️ Eigene Liste",
}

selected_universe = st.sidebar.selectbox("Universum", options=list(universe_labels.keys()), format_func=lambda x: universe_labels[x])

if selected_universe == "custom":
    custom_input = st.sidebar.text_area("Ticker (komma-getrennt)", value="AAPL, MSFT, NVDA, GOOGL, AMZN", height=100)
    tickers = [t.strip().upper() for t in custom_input.split(",") if t.strip()]
else:
    tickers = UNIVERSES[selected_universe]
    st.sidebar.caption(f"**{len(tickers)} Aktien** im Universum")

st.sidebar.divider()
st.sidebar.markdown("### 📐 Fundamentale Filter")
pe_max       = st.sidebar.slider("Max. P/E Ratio", 0, 100, 50, 5)
pb_max       = st.sidebar.slider("Max. P/B Ratio", 0, 30, 15, 1)
roe_min_pct  = st.sidebar.slider("Min. ROE %", 0, 50, 0, 5)
margin_min   = st.sidebar.slider("Min. Net Margin %", 0, 30, 0, 2)
rev_growth_min = st.sidebar.slider("Min. Umsatz-Wachstum %", -20, 50, -20, 5)

st.sidebar.divider()
st.sidebar.markdown("### 📊 Technische Filter")
rsi_range    = st.sidebar.slider("RSI Bereich", 0, 100, (20, 80))
above_sma200 = st.sidebar.checkbox("Über SMA 200", value=False)

filters = {k:v for k,v in {
    "pe_max":          pe_max if pe_max < 100 else None,
    "pb_max":          pb_max if pb_max < 30 else None,
    "roe_min":         roe_min_pct/100 if roe_min_pct > 0 else None,
    "margin_min":      margin_min/100 if margin_min > 0 else None,
    "rev_growth_min":  rev_growth_min/100 if rev_growth_min > -20 else None,
    "rsi_min":         rsi_range[0] if rsi_range[0] > 0 else None,
    "rsi_max":         rsi_range[1] if rsi_range[1] < 100 else None,
    "above_sma200":    above_sma200,
}.items() if v is not None}

st.markdown("## 🔍 Stock Screener")
st.caption(f"Universum: **{universe_labels[selected_universe]}** · {len(tickers)} Aktien")

col_btn, col_info = st.columns([1,4])
with col_btn:
    run_screen = st.button("🚀 Screen starten", type="primary", use_container_width=True)
with col_info:
    active = [k for k,v in filters.items() if v]
    st.caption(f"✅ Aktive Filter: {', '.join(active)}" if active else "ℹ️ Keine Filter aktiv")

st.divider()

if run_screen or "screener_results" in st.session_state:
    if run_screen:
        progress_bar = st.progress(0, text="Screener wird gestartet...")
        status_text  = st.empty()
        svc = get_screener_service()
        rows = []
        for i, ticker in enumerate(tickers):
            status_text.caption(f"Lade {ticker} ({i+1}/{len(tickers)})...")
            progress_bar.progress((i+1)/len(tickers), text=f"Analysiere {ticker}...")
            try:
                row = svc._fetch_ticker_data(ticker)
                if row: rows.append(row)
            except Exception: pass
        progress_bar.empty()
        status_text.empty()

        if rows:
            df_raw = pd.DataFrame(rows)
            df_raw = svc._calculate_scores(df_raw)
            df_raw = svc._apply_filters(df_raw, filters)
            df_raw = df_raw.sort_values("score", ascending=False).reset_index(drop=True)
            st.session_state["screener_results"] = df_raw
        else:
            st.error("Keine Daten geladen.")
            st.stop()

    df_raw = st.session_state.get("screener_results", pd.DataFrame())
    if df_raw.empty:
        st.warning("⚠️ Keine Aktien entsprechen den Filterkriterien.")
    else:
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Gefunden", f"{len(df_raw)} Aktien")
        c2.metric("Ø P/E",    f"{df_raw['pe_ratio'].dropna().mean():.1f}x" if not df_raw['pe_ratio'].dropna().empty else "N/A")
        c3.metric("Ø ROE",    f"{df_raw['roe'].dropna().mean()*100:.1f}%" if not df_raw['roe'].dropna().empty else "N/A")
        c4.metric("Bester Score", f"{df_raw['score'].max():.0f}/100")
        st.divider()

        svc = get_screener_service()
        display_df = svc.get_display_df(df_raw)
        screener_result_table(display_df)

        st.divider()
        csv = df_raw.to_csv(index=False).encode("utf-8")
        st.download_button("📥 CSV Export", data=csv, file_name=f"screener_{selected_universe}.csv", mime="text/csv")
else:
    st.markdown("""
    ### 👆 So funktioniert der Screener:
    1. **Universum wählen** (Sidebar)
    2. **Filter einstellen** (Sidebar)
    3. **🚀 Screen starten** klicken
    4. Ergebnisse nach **Composite Score** sortiert
    """)
    st.caption(f"**Aktuelles Universum:** {', '.join(tickers)}")
