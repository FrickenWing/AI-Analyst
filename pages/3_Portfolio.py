"""
pages/5_portfolio.py - Portfolio Tracking + Analytics (Phase 3)

Features:
- Positionen verwalten (hinzufügen, löschen)
- P&L Übersicht
- Pie Chart + P&L Balken
- NEU: Performance vs. S&P 500 Chart
- NEU: Sharpe Ratio, Max Drawdown, VaR
- NEU: Korrelations-Matrix
- NEU: Sektor-Allokation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff
from datetime import datetime

from data.openbb_client import get_client
from services.portfolio_service import get_portfolio_service
from utils.formatters import fmt_price, fmt_pct, fmt_large, color_pct, trend_arrow

# Beispiel für den Anfang deiner pages/1_charts.py Datei:

# Hole den aktuell ausgewählten Ticker aus dem globalen Speicher. 
# Falls noch nichts gesucht wurde, nimm "AAPL" als Standardwert.
current_ticker = st.session_state.get("current_ticker", "AAPL")

# (Optional) Lass den Nutzer den Ticker in der Sidebar der Unterseite trotzdem noch manuell anpassen
ticker = st.sidebar.text_input("Ticker Symbol", current_ticker).upper()

# Falls der Nutzer es in der Sidebar ändert, aktualisiere den State!
if ticker != current_ticker:
    st.session_state["current_ticker"] = ticker

st.set_page_config(page_title="Portfolio", page_icon="💼", layout="wide")

# ─────────────────────────────────────────────
def get_positions(): return st.session_state.get("portfolio_positions", [])
def save_positions(p): st.session_state["portfolio_positions"] = p

# ── Sidebar ───────────────────────────────────
st.sidebar.title("💼 Portfolio")

with st.sidebar.expander("➕ Position hinzufügen", expanded=True):
    pos_ticker = st.text_input("Ticker", placeholder="AAPL").upper()
    pos_qty    = st.number_input("Anzahl Stück", min_value=0.01, value=10.0, step=1.0)
    pos_price  = st.number_input("Kaufpreis ($)", min_value=0.01, value=100.0, step=0.01)
    pos_date   = st.date_input("Kaufdatum", value=datetime.today())

    if st.button("✅ Hinzufügen", use_container_width=True) and pos_ticker:
        positions = get_positions()
        existing  = next((p for p in positions if p["ticker"] == pos_ticker), None)
        if existing:
            total = existing["qty"] + pos_qty
            avg   = (existing["qty"] * existing["buy_price"] + pos_qty * pos_price) / total
            existing["qty"], existing["buy_price"] = total, round(avg, 2)
        else:
            positions.append({"ticker": pos_ticker, "qty": pos_qty,
                               "buy_price": pos_price, "date": str(pos_date)})
        save_positions(positions)
        st.success(f"✅ {pos_ticker} hinzugefügt!")
        st.rerun()

if st.sidebar.button("📋 Demo-Portfolio laden"):
    save_positions([
        {"ticker": "AAPL",  "qty": 10, "buy_price": 150.00, "date": "2024-01-15"},
        {"ticker": "MSFT",  "qty": 5,  "buy_price": 380.00, "date": "2024-02-01"},
        {"ticker": "NVDA",  "qty": 3,  "buy_price": 500.00, "date": "2024-03-10"},
        {"ticker": "GOOGL", "qty": 8,  "buy_price": 140.00, "date": "2024-01-20"},
        {"ticker": "AMZN",  "qty": 6,  "buy_price": 175.00, "date": "2024-04-05"},
    ])
    st.rerun()

if st.sidebar.button("🗑️ Portfolio leeren"):
    save_positions([])
    if "analytics_cache" in st.session_state:
        del st.session_state["analytics_cache"]
    st.rerun()

# ─────────────────────────────────────────────
st.markdown("## 💼 Portfolio Analytics")

positions = get_positions()
if not positions:
    st.info("**Noch keine Positionen.**\n\nFüge Positionen über die Sidebar hinzu oder lade das **Demo-Portfolio**.")
    st.stop()

# ── Aktuelle Kurse laden ──────────────────────
client = get_client()

with st.spinner("Lade aktuelle Kurse..."):
    enriched = []
    for pos in positions:
        quote     = client.get_quote(pos["ticker"])
        cur_price = quote.get("price", pos["buy_price"])
        cost      = pos["qty"] * pos["buy_price"]
        mv        = pos["qty"] * cur_price
        pnl       = mv - cost
        pnl_pct   = (cur_price - pos["buy_price"]) / pos["buy_price"]
        enriched.append({
            "Ticker":        pos["ticker"],
            "Stück":         pos["qty"],
            "Kaufkurs":      fmt_price(pos["buy_price"]),
            "Aktuell":       fmt_price(cur_price),
            "Marktwert":     fmt_large(mv),
            "P&L":           fmt_large(pnl),
            "P&L %":         fmt_pct(pnl_pct),
            "_market_value": mv,
            "_cost_basis":   cost,
            "_pnl":          pnl,
            "_pnl_pct":      pnl_pct,
        })

df_p = pd.DataFrame(enriched)
total_value = df_p["_market_value"].sum()
total_cost  = df_p["_cost_basis"].sum()
total_pnl   = df_p["_pnl"].sum()
total_pct   = (total_value - total_cost) / total_cost if total_cost else 0
pnl_color   = color_pct(total_pnl)

# ── Portfolio-Übersicht ───────────────────────
st.markdown(f"""
<div style="background:#1e2329;border-radius:12px;padding:22px;margin-bottom:20px;
            display:flex;gap:40px;align-items:center;flex-wrap:wrap;">
    <div><div style="color:#8b95a1;font-size:0.82rem;">Gesamtwert</div>
         <div style="font-size:2rem;font-weight:800;">{fmt_large(total_value)}</div></div>
    <div><div style="color:#8b95a1;font-size:0.82rem;">Investiert</div>
         <div style="font-size:1.4rem;font-weight:600;">{fmt_large(total_cost)}</div></div>
    <div><div style="color:#8b95a1;font-size:0.82rem;">Unrealisierter P&L</div>
         <div style="font-size:1.4rem;font-weight:700;color:{pnl_color};">
           {trend_arrow(total_pnl)} {fmt_large(abs(total_pnl))} ({fmt_pct(total_pct)})</div></div>
    <div><div style="color:#8b95a1;font-size:0.82rem;">Positionen</div>
         <div style="font-size:1.4rem;font-weight:600;">{len(positions)}</div></div>
</div>
""", unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Übersicht",
    "📈 Performance vs. Benchmark",
    "📐 Risiko-Metriken",
    "🔗 Korrelation & Sektoren",
])

# ════════════════════════════════════════════
# TAB 1: ÜBERSICHT
# ════════════════════════════════════════════
with tab1:
    col_chart, col_pie = st.columns([3, 2])

    with col_pie:
        st.markdown("**Portfolio-Aufteilung**")
        fig_pie = go.Figure(go.Pie(
            labels=df_p["Ticker"], values=df_p["_market_value"],
            hole=0.4, textinfo="label+percent",
            marker=dict(colors=px.colors.qualitative.Set2),
        ))
        fig_pie.update_layout(template="plotly_dark", height=280,
                               paper_bgcolor="#0e1117", margin=dict(l=0,r=0,t=0,b=0),
                               showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_chart:
        st.markdown("**P&L je Position**")
        pnl_vals = df_p["_pnl"].tolist()
        colors   = ["#26a69a" if v >= 0 else "#ef5350" for v in pnl_vals]
        fig_bar  = go.Figure(go.Bar(
            x=df_p["Ticker"], y=pnl_vals, marker_color=colors,
            text=[fmt_large(v) for v in pnl_vals], textposition="outside",
        ))
        fig_bar.update_layout(template="plotly_dark", height=280,
                               paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                               margin=dict(l=0,r=0,t=10,b=0),
                               yaxis=dict(showgrid=False, showticklabels=False))
        st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()
    st.markdown("### 📋 Positions-Übersicht")
    display_cols = ["Ticker","Stück","Kaufkurs","Aktuell","Marktwert","P&L","P&L %"]
    st.dataframe(df_p[display_cols], use_container_width=True, hide_index=True)
    csv = df_p[display_cols].to_csv(index=False).encode("utf-8")
    st.download_button("📥 Portfolio als CSV", data=csv, file_name="portfolio.csv", mime="text/csv")

# ════════════════════════════════════════════
# TAB 2: PERFORMANCE
# ════════════════════════════════════════════
with tab2:
    st.markdown("### 📈 Performance vs. S&P 500")

    if st.button("🔄 Analytics berechnen", type="primary"):
        with st.spinner("Berechne Portfolio-Performance (dauert ~20 Sekunden)..."):
            svc       = get_portfolio_service()
            analytics = svc.get_full_analytics(positions)
            st.session_state["analytics_cache"] = analytics

    analytics = st.session_state.get("analytics_cache", {})

    if not analytics:
        st.info("Klicke auf **'Analytics berechnen'** um Performance-Charts zu laden.\n\n*(Lädt 1 Jahr historische Daten für alle Positionen + S&P 500)*")
    else:
        cum_port  = analytics.get("cum_returns", pd.Series())
        cum_bench = analytics.get("cum_benchmark", pd.Series())
        bench_inf = analytics.get("benchmark", {})

        if not cum_port.empty:
            fig_perf = go.Figure()
            fig_perf.add_trace(go.Scatter(
                x=cum_port.index, y=cum_port.values * 100,
                mode="lines", name="Mein Portfolio",
                line=dict(color="#26a69a", width=2.5),
            ))
            if not cum_bench.empty:
                # Auf gleichen Zeitraum bringen
                common = cum_port.index.intersection(cum_bench.index)
                if len(common) > 0:
                    fig_perf.add_trace(go.Scatter(
                        x=common, y=cum_bench.loc[common].values * 100,
                        mode="lines", name="S&P 500",
                        line=dict(color="#5c6bc0", width=2, dash="dash"),
                    ))
            fig_perf.add_hline(y=0, line_dash="dot", line_color="#4b5563")
            fig_perf.update_layout(
                template="plotly_dark", height=380,
                paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                margin=dict(l=0, r=0, t=10, b=0),
                yaxis=dict(ticksuffix="%", gridcolor="#1e2329"),
                xaxis=dict(gridcolor="#1e2329"),
                legend=dict(x=0.01, y=0.99),
            )
            st.plotly_chart(fig_perf, use_container_width=True)

        # Benchmark-Vergleich Metriken
        if bench_inf:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Portfolio Return",
                      fmt_pct(bench_inf.get("port_return")))
            c2.metric("S&P 500 Return",
                      fmt_pct(bench_inf.get("bench_return")))
            c3.metric("Alpha",
                      fmt_pct(bench_inf.get("alpha")),
                      delta=fmt_pct(bench_inf.get("alpha")))
            c4.metric("Beta",
                      f"{bench_inf.get('beta', 0):.2f}",
                      help="< 1 = defensiver als S&P 500")

# ════════════════════════════════════════════
# TAB 3: RISIKO-METRIKEN
# ════════════════════════════════════════════
with tab3:
    st.markdown("### 📐 Risiko-Kennzahlen")

    analytics = st.session_state.get("analytics_cache", {})
    if not analytics:
        st.info("Zuerst **'Analytics berechnen'** im Tab 'Performance' klicken.")
    else:
        metrics = analytics.get("metrics", {})
        if not metrics:
            st.warning("Keine Metriken verfügbar.")
        else:
            c1, c2, c3, c4 = st.columns(4)
            sharpe = metrics.get("sharpe_ratio", 0)
            sharpe_color = "#26a69a" if sharpe > 1 else "#ffab40" if sharpe > 0 else "#ef5350"

            c1.markdown(f"""
            <div style="background:#1e2329;border-radius:8px;padding:16px;text-align:center;">
                <div style="color:#8b95a1;font-size:0.8rem;">Sharpe Ratio</div>
                <div style="font-size:2rem;font-weight:800;color:{sharpe_color};">{sharpe:.2f}</div>
                <div style="color:#8b95a1;font-size:0.75rem;">{"Gut" if sharpe > 1 else "OK" if sharpe > 0 else "Schlecht"} (> 1 = gut)</div>
            </div>
            """, unsafe_allow_html=True)

            dd = metrics.get("max_drawdown", 0)
            c2.markdown(f"""
            <div style="background:#1e2329;border-radius:8px;padding:16px;text-align:center;">
                <div style="color:#8b95a1;font-size:0.8rem;">Max. Drawdown</div>
                <div style="font-size:2rem;font-weight:800;color:#ef5350;">{dd*100:.1f}%</div>
                <div style="color:#8b95a1;font-size:0.75rem;">Größter Rückgang</div>
            </div>
            """, unsafe_allow_html=True)

            var = metrics.get("var_95", 0)
            c3.markdown(f"""
            <div style="background:#1e2329;border-radius:8px;padding:16px;text-align:center;">
                <div style="color:#8b95a1;font-size:0.8rem;">VaR (95%, 1 Tag)</div>
                <div style="font-size:2rem;font-weight:800;color:#ff6e40;">{var*100:.2f}%</div>
                <div style="color:#8b95a1;font-size:0.75rem;">Tagesverlust-Risiko</div>
            </div>
            """, unsafe_allow_html=True)

            vol = metrics.get("volatility", 0)
            c4.markdown(f"""
            <div style="background:#1e2329;border-radius:8px;padding:16px;text-align:center;">
                <div style="color:#8b95a1;font-size:0.8rem;">Volatilität (ann.)</div>
                <div style="font-size:2rem;font-weight:800;">{vol*100:.1f}%</div>
                <div style="color:#8b95a1;font-size:0.75rem;">Jahres-Standardabw.</div>
            </div>
            """, unsafe_allow_html=True)

            st.divider()
            c5, c6, c7, c8 = st.columns(4)
            c5.metric("Gesamtrendite",    fmt_pct(metrics.get("total_return")))
            c6.metric("Ann. Rendite",     fmt_pct(metrics.get("ann_return")))
            c7.metric("Win-Rate",         f"{metrics.get('win_rate',0)*100:.0f}%")
            c8.metric("Calmar Ratio",     f"{metrics.get('calmar_ratio',0):.2f}")

            st.divider()
            col_best, col_worst = st.columns(2)
            col_best.metric("Bester Tag",  fmt_pct(metrics.get("best_day")))
            col_worst.metric("Schlechtester Tag", fmt_pct(metrics.get("worst_day")))

        # Drawdown-Chart
        daily_returns = analytics.get("daily_returns", pd.Series())
        if not daily_returns.empty:
            st.divider()
            st.markdown("**Drawdown-Verlauf**")
            cum = (1 + daily_returns).cumprod()
            rolling_max = cum.expanding().max()
            drawdown = (cum - rolling_max) / rolling_max

            fig_dd = go.Figure(go.Scatter(
                x=drawdown.index, y=drawdown.values * 100,
                mode="lines", fill="tozeroy",
                line=dict(color="#ef5350", width=1.5),
                fillcolor="rgba(239,83,80,0.15)",
            ))
            fig_dd.update_layout(
                template="plotly_dark", height=220,
                paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                margin=dict(l=0, r=0, t=10, b=0),
                yaxis=dict(ticksuffix="%", gridcolor="#1e2329"),
                xaxis=dict(gridcolor="#1e2329"),
            )
            st.plotly_chart(fig_dd, use_container_width=True)

# ════════════════════════════════════════════
# TAB 4: KORRELATION & SEKTOREN
# ════════════════════════════════════════════
with tab4:
    analytics = st.session_state.get("analytics_cache", {})
    if not analytics:
        st.info("Zuerst **'Analytics berechnen'** im Tab 'Performance' klicken.")
    else:
        col_corr, col_sect = st.columns(2)

        with col_corr:
            st.markdown("### 🔗 Korrelations-Matrix")
            corr = analytics.get("correlation")
            if corr is not None and not corr.empty:
                fig_corr = go.Figure(go.Heatmap(
                    z=corr.values,
                    x=corr.columns.tolist(),
                    y=corr.index.tolist(),
                    colorscale="RdYlGn",
                    zmin=-1, zmax=1,
                    text=corr.round(2).values,
                    texttemplate="%{text}",
                    showscale=True,
                ))
                fig_corr.update_layout(
                    template="plotly_dark", height=320,
                    paper_bgcolor="#0e1117",
                    margin=dict(l=0, r=0, t=0, b=0),
                )
                st.plotly_chart(fig_corr, use_container_width=True)
                st.caption("1.0 = perfekte Korrelation, 0 = kein Zusammenhang, -1 = gegenläufig")
            else:
                st.info("Mind. 2 Positionen für Korrelations-Matrix nötig.")

        with col_sect:
            st.markdown("### 🏭 Sektor-Allokation")
            sector_alloc = analytics.get("sector_alloc", [])
            if sector_alloc:
                labels = [s["sector"] for s in sector_alloc]
                values = [s["value"] for s in sector_alloc]
                fig_sect = go.Figure(go.Pie(
                    labels=labels, values=values, hole=0.35,
                    textinfo="label+percent",
                    marker=dict(colors=px.colors.qualitative.Pastel),
                ))
                fig_sect.update_layout(
                    template="plotly_dark", height=320,
                    paper_bgcolor="#0e1117",
                    margin=dict(l=0, r=0, t=0, b=0),
                    showlegend=False,
                )
                st.plotly_chart(fig_sect, use_container_width=True)
            else:
                st.info("Sektor-Daten werden geladen...")
