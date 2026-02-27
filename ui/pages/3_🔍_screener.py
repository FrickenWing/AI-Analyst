"""
ui/pages/3_🔍_screener.py - Stock Screener Seite

Features:
- Vordefinierte Universen (Mega Cap, Tech, Dividenden, DAX)
- Eigene Watchlist screenen
- Fundamentale Filter (P/E, P/B, ROE, Margen)
- Technische Filter (RSI, über SMA 200)
- Composite Score Ranking
- CSV Export
"""

import streamlit as st
import pandas as pd
import time

from services.screener_service import get_screener_service, UNIVERSES
from ui.components.tables import screener_result_table
from ui.components.sidebar import render_ticker_input

# ─────────────────────────────────────────────
st.set_page_config(page_title="Screener", page_icon="🔍", layout="wide")

# ── Sidebar ───────────────────────────────────
st.sidebar.title("🔍 Stock Screener")
st.sidebar.caption("Filtere Aktien nach deinen Kriterien")

# Universum-Auswahl
universe_labels = {
    "mega_cap_us": "🇺🇸 US Mega Cap (Top 10)",
    "tech_growth":  "💻 Tech Growth",
    "dividends":    "💰 Dividenden-Aktien",
    "dax_top10":    "🇩🇪 DAX Top 10",
    "custom":       "✏️ Eigene Liste",
}

selected_universe = st.sidebar.selectbox(
    "Universum",
    options=list(universe_labels.keys()),
    format_func=lambda x: universe_labels[x],
)

# Eigene Ticker
if selected_universe == "custom":
    custom_input = st.sidebar.text_area(
        "Ticker (komma-getrennt)",
        value="AAPL, MSFT, NVDA, GOOGL, AMZN",
        height=100,
    )
    tickers = [t.strip().upper() for t in custom_input.split(",") if t.strip()]
else:
    tickers = UNIVERSES[selected_universe]
    st.sidebar.caption(f"**{len(tickers)} Aktien** im Universum")

st.sidebar.divider()

# ── Filter-Einstellungen ──────────────────────
st.sidebar.markdown("### 📐 Fundamentale Filter")

pe_max      = st.sidebar.slider("Max. P/E Ratio",      0, 100, 50, 5)
pb_max      = st.sidebar.slider("Max. P/B Ratio",      0, 30,  15, 1)
roe_min_pct = st.sidebar.slider("Min. ROE %",          0, 50,   0, 5)
margin_min  = st.sidebar.slider("Min. Net Margin %",   0, 30,   0, 2)
rev_growth_min_pct = st.sidebar.slider("Min. Umsatz-Wachstum %", -20, 50, -20, 5)

st.sidebar.divider()
st.sidebar.markdown("### 📊 Technische Filter")

rsi_range = st.sidebar.slider("RSI Bereich", 0, 100, (20, 80))
above_sma200 = st.sidebar.checkbox("Über SMA 200", value=False)

# Filter zusammenbauen
filters = {
    "pe_max":        pe_max       if pe_max < 100      else None,
    "pb_max":        pb_max       if pb_max < 30       else None,
    "roe_min":       roe_min_pct / 100 if roe_min_pct > 0 else None,
    "margin_min":    margin_min / 100  if margin_min > 0   else None,
    "rev_growth_min":rev_growth_min_pct / 100 if rev_growth_min_pct > -20 else None,
    "rsi_min":       rsi_range[0] if rsi_range[0] > 0   else None,
    "rsi_max":       rsi_range[1] if rsi_range[1] < 100 else None,
    "above_sma200":  above_sma200,
}
# None-Werte entfernen
filters = {k: v for k, v in filters.items() if v is not None}

# ── Haupt-Bereich ─────────────────────────────
st.markdown("## 🔍 Stock Screener")
st.caption(f"Universum: **{universe_labels[selected_universe]}** · {len(tickers)} Aktien")

# Screen-Button
col_btn, col_info = st.columns([1, 4])
with col_btn:
    run_screen = st.button("🚀 Screen starten", type="primary", use_container_width=True)

with col_info:
    active_filters = [k for k, v in filters.items() if v]
    if active_filters:
        st.caption(f"✅ Aktive Filter: {', '.join(active_filters)}")
    else:
        st.caption("ℹ️ Keine Filter aktiv – alle Aktien werden angezeigt")

st.divider()

# ── Screening ausführen ───────────────────────
if run_screen or "screener_results" in st.session_state:

    if run_screen:
        # Fortschritts-Anzeige
        progress_bar = st.progress(0, text="Screener wird gestartet...")
        status_text  = st.empty()

        svc = get_screener_service()

        # Chunk-weise Verarbeitung für bessere UX
        results_rows = []
        total = len(tickers)

        for i, ticker in enumerate(tickers):
            status_text.caption(f"Lade {ticker} ({i+1}/{total})...")
            progress_bar.progress((i + 1) / total, text=f"Analysiere {ticker}...")

            try:
                row = svc._fetch_ticker_data(ticker)
                if row:
                    results_rows.append(row)
            except Exception:
                pass

        progress_bar.empty()
        status_text.empty()

        if results_rows:
            import pandas as pd
            df_raw = pd.DataFrame(results_rows)
            df_raw = svc._calculate_scores(df_raw)
            df_raw = svc._apply_filters(df_raw, filters)
            df_raw = df_raw.sort_values("score", ascending=False).reset_index(drop=True)
            st.session_state["screener_results"] = df_raw
        else:
            st.error("Keine Daten geladen. Bitte prüfe deine Internetverbindung.")
            st.stop()

    # Ergebnisse anzeigen
    df_raw = st.session_state.get("screener_results", pd.DataFrame())

    if df_raw.empty:
        st.warning("⚠️ Keine Aktien entsprechen den Filterkriterien. Bitte Filter lockern.")
    else:
        # Zusammenfassung
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Gefunden",           f"{len(df_raw)} Aktien")
        col2.metric("Ø P/E",              f"{df_raw['pe_ratio'].dropna().mean():.1f}x" if not df_raw['pe_ratio'].dropna().empty else "N/A")
        col3.metric("Ø ROE",              f"{df_raw['roe'].dropna().mean()*100:.1f}%" if not df_raw['roe'].dropna().empty else "N/A")
        col4.metric("Bester Score",       f"{df_raw['score'].max():.0f}/100" if not df_raw.empty else "N/A")

        st.divider()

        # Tabs für verschiedene Ansichten
        view_tab1, view_tab2, view_tab3 = st.tabs([
            "📋 Alle Ergebnisse",
            "💰 Bewertung",
            "📈 Wachstum & Qualität",
        ])

        svc = get_screener_service()
        display_df = svc.get_display_df(df_raw)

        with view_tab1:
            screener_result_table(display_df)

        with view_tab2:
            val_cols = ["Ticker", "Name", "Kurs", "Δ %", "Market Cap", "P/E", "P/B", "Score"]
            available = [c for c in val_cols if c in display_df.columns]
            screener_result_table(display_df[available])

        with view_tab3:
            growth_cols = ["Ticker", "Name", "Kurs", "ROE", "Net Margin", "Rev. Growth", "RSI", "Score"]
            available = [c for c in growth_cols if c in display_df.columns]
            screener_result_table(display_df[available])

        # Export
        st.divider()
        col_exp1, col_exp2 = st.columns([1, 4])
        with col_exp1:
            csv = df_raw.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 CSV Export",
                data=csv,
                file_name=f"screener_{selected_universe}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with col_exp2:
            st.caption("Exportiert alle Rohdaten als CSV-Datei.")

else:
    # Noch kein Screen gestartet
    st.markdown("""
    ### 👆 So funktioniert der Screener:

    1. **Universum wählen** (Sidebar) – z.B. US Mega Cap oder eigene Liste
    2. **Filter einstellen** (Sidebar) – P/E, ROE, RSI etc.
    3. **🚀 Screen starten** klicken
    4. Ergebnisse werden nach **Composite Score** sortiert

    > Der **Score (0-100)** bewertet jede Aktie nach Bewertung, Wachstum,
    > Profitabilität und technischem Momentum.
    """)

    # Universum-Vorschau
    st.markdown(f"**Aktuelles Universum:** {len(tickers)} Ticker")
    st.caption(", ".join(tickers))
