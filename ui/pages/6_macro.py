"""
pages/6_macro.py - Makro-Dashboard

Zeigt:
- US Yield Curve (3M, 2Y, 5Y, 10Y, 30Y)
- Sektor-Performance Heatmap (YTD / 1M / 1W)
- Währungspaare (EUR/USD, GBP/USD, USD/JPY, ...)
- Rohstoffe (Gold, Öl, Kupfer, Gas)
- Markt-Angstindex VIX Verlauf
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

from data.openbb_client import get_client
from utils.formatters import fmt_price, fmt_pct, color_pct, trend_arrow

st.set_page_config(page_title="Makro", page_icon="🌍", layout="wide")

# ─────────────────────────────────────────────
client = get_client()

st.markdown("## 🌍 Makro Dashboard")
st.caption("Zinsen · Sektoren · Währungen · Rohstoffe · Angst-Index")

# ── Tabs ──────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Zinsen & Yield Curve",
    "🏭 Sektoren",
    "💱 Währungen & Rohstoffe",
    "😰 Angst-Indikatoren",
])

# ════════════════════════════════════════════
# TAB 1: ZINSEN & YIELD CURVE
# ════════════════════════════════════════════
with tab1:
    st.markdown("### 📈 US Treasury Yield Curve")

    TREASURIES = {
        "3M":  "^IRX",
        "2Y":  "^TwoYear",
        "5Y":  "^FVX",
        "10Y": "^TNX",
        "30Y": "^TYX",
    }

    # Aktuelle Yields holen
    yields_current = {}
    yields_prev    = {}

    with st.spinner("Lade Treasury-Daten..."):
        for label, symbol in TREASURIES.items():
            try:
                q = client.get_quote(symbol)
                yields_current[label] = q.get("price", 0)
                yields_prev[label]    = q.get("price", 0) - q.get("change", 0)
            except Exception:
                yields_current[label] = None
                yields_prev[label]    = None

    # KPI-Zeile
    cols = st.columns(len(TREASURIES))
    for col, (label, val) in zip(cols, yields_current.items()):
        prev = yields_prev.get(label)
        with col:
            if val and prev and prev != 0:
                change = val - prev
                color  = "#ef5350" if change > 0 else "#26a69a"  # Zinserhöhung = rot
                arrow  = "▲" if change > 0 else "▼"
                st.markdown(f"""
                <div style="background:#1e2329;border-radius:8px;padding:14px;text-align:center;">
                    <div style="color:#8b95a1;font-size:0.8rem;">US {label}</div>
                    <div style="font-size:1.4rem;font-weight:700;">{val:.2f}%</div>
                    <div style="color:{color};font-size:0.85rem;">{arrow} {change:+.3f}%</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.metric(f"US {label}", f"{val:.2f}%" if val else "N/A")

    st.divider()

    # Yield-Curve Chart
    valid_yields = {k: v for k, v in yields_current.items() if v}
    if len(valid_yields) >= 2:
        maturities = list(valid_yields.keys())
        values     = list(valid_yields.values())
        is_inverted = values[0] > values[-1] if len(values) >= 2 else False

        fig_yield = go.Figure()
        fig_yield.add_trace(go.Scatter(
            x=maturities, y=values,
            mode="lines+markers",
            line=dict(
                color="#ef5350" if is_inverted else "#26a69a",
                width=3
            ),
            marker=dict(size=10),
            fill="tozeroy",
            fillcolor="rgba(239,83,80,0.1)" if is_inverted else "rgba(38,166,154,0.1)",
        ))
        fig_yield.update_layout(
            title=f"US Yield Curve {'⚠️ INVERTIERT' if is_inverted else '(Normal)'}",
            template="plotly_dark",
            height=350,
            paper_bgcolor="#0e1117",
            plot_bgcolor="#0e1117",
            margin=dict(l=0, r=0, t=40, b=0),
            yaxis=dict(ticksuffix="%", gridcolor="#1e2329"),
            xaxis=dict(gridcolor="#1e2329"),
        )
        st.plotly_chart(fig_yield, use_container_width=True)

        if is_inverted:
            st.warning("⚠️ Die Yield Curve ist invertiert (kurzfristige Zinsen > langfristige). Historisch ein Rezessions-Signal.")
    else:
        st.info("Yield-Daten momentan nicht verfügbar.")

    # 10Y Verlauf
    st.divider()
    st.markdown("### 📉 10Y Treasury – 1-Jahres-Verlauf")
    try:
        df_10y = client.get_price_history("^TNX", "1y", "1d")
        if not df_10y.empty:
            fig_10y = go.Figure(go.Scatter(
                x=df_10y.index, y=df_10y["close"],
                mode="lines",
                line=dict(color="#5c6bc0", width=2),
                fill="tozeroy",
                fillcolor="rgba(92,107,192,0.1)",
            ))
            fig_10y.update_layout(
                template="plotly_dark", height=280,
                paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                margin=dict(l=0, r=0, t=10, b=0),
                yaxis=dict(ticksuffix="%", gridcolor="#1e2329"),
                xaxis=dict(gridcolor="#1e2329"),
            )
            st.plotly_chart(fig_10y, use_container_width=True)
    except Exception:
        st.info("10Y-Verlaufsdaten nicht verfügbar.")


# ════════════════════════════════════════════
# TAB 2: SEKTOREN
# ════════════════════════════════════════════
with tab2:
    st.markdown("### 🏭 Sektor-Performance")

    SECTOR_ETFS = {
        "Technology":             "XLK",
        "Healthcare":             "XLV",
        "Financials":             "XLF",
        "Consumer Discret.":      "XLY",
        "Consumer Staples":       "XLP",
        "Energy":                 "XLE",
        "Industrials":            "XLI",
        "Materials":              "XLB",
        "Real Estate":            "XLRE",
        "Utilities":              "XLU",
        "Communication":          "XLC",
    }

    period_choice = st.radio("Zeitraum", ["1W", "1M", "3M", "YTD", "1J"], horizontal=True, index=2)
    period_map = {"1W": "5d", "1M": "1mo", "3M": "3mo", "YTD": "ytd", "1J": "1y"}
    period = period_map[period_choice]

    sector_perf = {}
    with st.spinner("Lade Sektor-Daten..."):
        for sector, etf in SECTOR_ETFS.items():
            try:
                df_s = client.get_price_history(etf, period, "1d")
                if not df_s.empty and len(df_s) >= 2:
                    change = (df_s["close"].iloc[-1] / df_s["close"].iloc[0] - 1)
                    sector_perf[sector] = float(change)
            except Exception:
                pass

    if sector_perf:
        sorted_sectors = sorted(sector_perf.items(), key=lambda x: x[1], reverse=True)
        names  = [s[0] for s in sorted_sectors]
        values = [s[1] * 100 for s in sorted_sectors]
        colors = ["#26a69a" if v >= 0 else "#ef5350" for v in values]

        fig_sector = go.Figure(go.Bar(
            x=values, y=names,
            orientation="h",
            marker_color=colors,
            text=[f"{v:+.1f}%" for v in values],
            textposition="outside",
        ))
        fig_sector.update_layout(
            title=f"Sektor-Performance ({period_choice})",
            template="plotly_dark",
            height=420,
            paper_bgcolor="#0e1117",
            plot_bgcolor="#0e1117",
            margin=dict(l=0, r=60, t=40, b=0),
            xaxis=dict(ticksuffix="%", gridcolor="#1e2329"),
        )
        st.plotly_chart(fig_sector, use_container_width=True)

        # Heatmap-ähnliche Tabelle
        st.divider()
        st.markdown("**Performance-Übersicht**")
        df_display = pd.DataFrame([
            {"Sektor": s, "ETF": SECTOR_ETFS.get(s,""), "Performance": f"{v/100*100:+.2f}%"}
            for s, v in sorted_sectors
        ])
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("Sektor-Daten momentan nicht verfügbar.")


# ════════════════════════════════════════════
# TAB 3: WÄHRUNGEN & ROHSTOFFE
# ════════════════════════════════════════════
with tab3:
    col_forex, col_comm = st.columns(2)

    # ── Währungen ────────────────────────────
    with col_forex:
        st.markdown("### 💱 Währungspaare")

        FOREX = {
            "EUR/USD": "EURUSD=X",
            "GBP/USD": "GBPUSD=X",
            "USD/JPY": "USDJPY=X",
            "USD/CHF": "USDCHF=X",
            "AUD/USD": "AUDUSD=X",
            "USD/CNY": "USDCNY=X",
        }

        for pair, symbol in FOREX.items():
            try:
                q = client.get_quote(symbol)
                price  = q.get("price", 0)
                change = q.get("change_pct", 0)
                color  = color_pct(change)
                arrow  = trend_arrow(change)
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;
                            padding:10px 14px;background:#1e2329;border-radius:6px;margin-bottom:6px;">
                    <span style="font-weight:600;">{pair}</span>
                    <span style="font-size:1.1rem;">{price:.4f}</span>
                    <span style="color:{color};">{arrow} {fmt_pct(change)}</span>
                </div>
                """, unsafe_allow_html=True)
            except Exception:
                st.markdown(f"**{pair}** – N/A")

    # ── Rohstoffe ────────────────────────────
    with col_comm:
        st.markdown("### 🪨 Rohstoffe")

        COMMODITIES = {
            "Gold":        ("GC=F",  "🥇"),
            "Silber":      ("SI=F",  "🥈"),
            "Öl (WTI)":   ("CL=F",  "🛢️"),
            "Öl (Brent)": ("BZ=F",  "🛢️"),
            "Erdgas":      ("NG=F",  "🔥"),
            "Kupfer":      ("HG=F",  "🔶"),
        }

        for name, (symbol, icon) in COMMODITIES.items():
            try:
                q = client.get_quote(symbol)
                price  = q.get("price", 0)
                change = q.get("change_pct", 0)
                color  = color_pct(change)
                arrow  = trend_arrow(change)
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;
                            padding:10px 14px;background:#1e2329;border-radius:6px;margin-bottom:6px;">
                    <span style="font-weight:600;">{icon} {name}</span>
                    <span style="font-size:1.1rem;">${price:,.2f}</span>
                    <span style="color:{color};">{arrow} {fmt_pct(change)}</span>
                </div>
                """, unsafe_allow_html=True)
            except Exception:
                st.markdown(f"**{icon} {name}** – N/A")

    # ── Gold-Chart ────────────────────────────
    st.divider()
    st.markdown("### 📊 Gold – 1-Jahres-Verlauf")
    try:
        df_gold = client.get_price_history("GC=F", "1y", "1d")
        if not df_gold.empty:
            fig_gold = go.Figure(go.Scatter(
                x=df_gold.index, y=df_gold["close"],
                mode="lines",
                line=dict(color="#f59e0b", width=2),
                fill="tozeroy",
                fillcolor="rgba(245,158,11,0.08)",
            ))
            fig_gold.update_layout(
                template="plotly_dark", height=280,
                paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                margin=dict(l=0, r=0, t=10, b=0),
                yaxis=dict(tickprefix="$", gridcolor="#1e2329"),
                xaxis=dict(gridcolor="#1e2329"),
            )
            st.plotly_chart(fig_gold, use_container_width=True)
    except Exception:
        st.info("Gold-Verlaufsdaten nicht verfügbar.")


# ════════════════════════════════════════════
# TAB 4: ANGST-INDIKATOREN
# ════════════════════════════════════════════
with tab4:
    st.markdown("### 😰 Markt-Sentiment & Angst-Indikatoren")

    # VIX
    try:
        q_vix = client.get_quote("^VIX")
        vix   = q_vix.get("price", 0)
        vix_change = q_vix.get("change_pct", 0)

        if vix < 15:
            vix_zone, vix_color, vix_emoji = "Extreme Gier", "#26a69a", "😄"
        elif vix < 20:
            vix_zone, vix_color, vix_emoji = "Ruhig / Bullish", "#69f0ae", "😊"
        elif vix < 25:
            vix_zone, vix_color, vix_emoji = "Moderat", "#ffab40", "😐"
        elif vix < 35:
            vix_zone, vix_color, vix_emoji = "Erhöhte Angst", "#ff6e40", "😟"
        else:
            vix_zone, vix_color, vix_emoji = "Extreme Angst / Panik", "#ff1744", "😱"

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div style="background:#1e2329;border-radius:12px;padding:24px;text-align:center;">
                <div style="font-size:3rem;">{vix_emoji}</div>
                <div style="font-size:0.8rem;color:#8b95a1;margin-top:8px;">VIX (Angst-Index)</div>
                <div style="font-size:2.5rem;font-weight:800;color:{vix_color};">{vix:.2f}</div>
                <div style="color:{vix_color};font-weight:600;">{vix_zone}</div>
                <div style="color:#8b95a1;font-size:0.8rem;margin-top:4px;">{fmt_pct(vix_change)} heute</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            **VIX Interpretation:**

            | VIX | Marktlage |
            |-----|-----------|
            | < 15 | Sehr ruhig – Selbstgefälligkeit |
            | 15–20 | Normal / Bullish |
            | 20–25 | Leicht erhöht |
            | 25–35 | Ängstlich – Vorsicht |
            | > 35 | Panik / Crash-Modus |
            """)

        with col3:
            # Put/Call Ratio Proxy: Verhältnis von Tech / Defensive
            try:
                q_qqq  = client.get_quote("QQQ")
                q_xlp  = client.get_quote("XLP")
                qqq_ch = q_qqq.get("change_pct", 0)
                xlp_ch = q_xlp.get("change_pct", 0)
                risk_on = qqq_ch > xlp_ch
                st.markdown(f"""
                <div style="background:#1e2329;border-radius:12px;padding:24px;text-align:center;">
                    <div style="font-size:2rem;">{'🚀' if risk_on else '🛡️'}</div>
                    <div style="font-size:0.8rem;color:#8b95a1;margin-top:8px;">Risk-On / Risk-Off</div>
                    <div style="font-size:1.5rem;font-weight:700;color:{'#26a69a' if risk_on else '#ef5350'};">
                        {'RISK ON' if risk_on else 'RISK OFF'}
                    </div>
                    <div style="color:#8b95a1;font-size:0.8rem;margin-top:8px;">
                        QQQ: {fmt_pct(qqq_ch)} vs XLP: {fmt_pct(xlp_ch)}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            except Exception:
                st.info("Risk-On/Off Daten nicht verfügbar.")

    except Exception:
        st.info("VIX-Daten nicht verfügbar.")

    # VIX Verlauf
    st.divider()
    st.markdown("### 📉 VIX – 1-Jahres-Verlauf")
    try:
        df_vix = client.get_price_history("^VIX", "1y", "1d")
        if not df_vix.empty:
            vix_vals = df_vix["close"]
            vix_colors = ["#ef5350" if v > 25 else "#ffab40" if v > 20 else "#26a69a"
                          for v in vix_vals]
            fig_vix = go.Figure()
            fig_vix.add_trace(go.Scatter(
                x=df_vix.index, y=vix_vals,
                mode="lines",
                line=dict(color="#ab47bc", width=2),
                fill="tozeroy",
                fillcolor="rgba(171,71,188,0.08)",
                name="VIX",
            ))
            # Gefahren-Linie bei 25
            fig_vix.add_hline(y=25, line_dash="dash", line_color="#ff6e40",
                               annotation_text="25 – Erhöhte Angst")
            fig_vix.add_hline(y=20, line_dash="dot", line_color="#ffab40",
                               annotation_text="20 – Normal")
            fig_vix.update_layout(
                template="plotly_dark", height=300,
                paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                margin=dict(l=0, r=0, t=10, b=0),
                yaxis=dict(gridcolor="#1e2329"),
                xaxis=dict(gridcolor="#1e2329"),
            )
            st.plotly_chart(fig_vix, use_container_width=True)
    except Exception:
        st.info("VIX-Verlaufsdaten nicht verfügbar.")

    # S&P 500 vs. VIX Korrelation
    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**S&P 500 – 3 Monate**")
        try:
            df_sp = client.get_price_history("^GSPC", "3mo", "1d")
            if not df_sp.empty:
                fig_sp = go.Figure(go.Scatter(
                    x=df_sp.index, y=df_sp["close"],
                    mode="lines", line=dict(color="#42a5f5", width=2),
                ))
                fig_sp.update_layout(template="plotly_dark", height=200,
                                     paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                                     margin=dict(l=0,r=0,t=0,b=0),
                                     yaxis=dict(gridcolor="#1e2329"),
                                     xaxis=dict(gridcolor="#1e2329"))
                st.plotly_chart(fig_sp, use_container_width=True)
        except Exception: pass

    with col_b:
        st.markdown("**NASDAQ – 3 Monate**")
        try:
            df_nq = client.get_price_history("^IXIC", "3mo", "1d")
            if not df_nq.empty:
                fig_nq = go.Figure(go.Scatter(
                    x=df_nq.index, y=df_nq["close"],
                    mode="lines", line=dict(color="#26a69a", width=2),
                ))
                fig_nq.update_layout(template="plotly_dark", height=200,
                                     paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                                     margin=dict(l=0,r=0,t=0,b=0),
                                     yaxis=dict(gridcolor="#1e2329"),
                                     xaxis=dict(gridcolor="#1e2329"))
                st.plotly_chart(fig_nq, use_container_width=True)
        except Exception: pass
