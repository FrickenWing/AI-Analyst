"""
ui/pages/5_💼_portfolio.py - Portfolio Analytics

Features:
- Positionen manuell eingeben oder aus Session laden
- P&L Übersicht (realisiert / unrealisiert)
- Portfolio-Zusammensetzung (Pie Chart)
- Performance vs. S&P 500
- Positions-Tabelle
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

from data.openbb_client import get_client
from utils.formatters import fmt_price, fmt_pct, fmt_large, color_pct, trend_arrow

# ─────────────────────────────────────────────
st.set_page_config(page_title="Portfolio", page_icon="💼", layout="wide")

# ── Helper: Portfolio aus Session State ───────
def get_portfolio() -> list[dict]:
    return st.session_state.get("portfolio_positions", [])

def save_portfolio(positions: list[dict]):
    st.session_state["portfolio_positions"] = positions

# ── Sidebar ───────────────────────────────────
st.sidebar.title("💼 Portfolio")

with st.sidebar.expander("➕ Position hinzufügen", expanded=True):
    pos_ticker = st.text_input("Ticker", placeholder="AAPL").upper()
    pos_qty    = st.number_input("Anzahl Stück", min_value=0.01, value=10.0, step=1.0)
    pos_price  = st.number_input("Kaufpreis ($)", min_value=0.01, value=100.0, step=0.01)
    pos_date   = st.date_input("Kaufdatum", value=datetime.today())

    if st.button("✅ Hinzufügen", use_container_width=True) and pos_ticker:
        positions = get_portfolio()
        # Prüfe ob Ticker schon vorhanden (dann average)
        existing = next((p for p in positions if p["ticker"] == pos_ticker), None)
        if existing:
            total_qty   = existing["qty"] + pos_qty
            avg_price   = (existing["qty"] * existing["buy_price"] + pos_qty * pos_price) / total_qty
            existing["qty"]       = total_qty
            existing["buy_price"] = round(avg_price, 2)
        else:
            positions.append({
                "ticker":    pos_ticker,
                "qty":       pos_qty,
                "buy_price": pos_price,
                "date":      str(pos_date),
            })
        save_portfolio(positions)
        st.success(f"✅ {pos_ticker} hinzugefügt!")
        st.rerun()

# Demo-Portfolio laden
if st.sidebar.button("📋 Demo-Portfolio laden"):
    demo = [
        {"ticker": "AAPL",  "qty": 10,  "buy_price": 150.00, "date": "2024-01-15"},
        {"ticker": "MSFT",  "qty": 5,   "buy_price": 380.00, "date": "2024-02-01"},
        {"ticker": "NVDA",  "qty": 3,   "buy_price": 500.00, "date": "2024-03-10"},
        {"ticker": "GOOGL", "qty": 8,   "buy_price": 140.00, "date": "2024-01-20"},
        {"ticker": "AMZN",  "qty": 6,   "buy_price": 175.00, "date": "2024-04-05"},
    ]
    save_portfolio(demo)
    st.rerun()

if st.sidebar.button("🗑️ Portfolio leeren"):
    save_portfolio([])
    st.rerun()

# ── Haupt-Bereich ─────────────────────────────
st.markdown("## 💼 Portfolio Analytics")

positions = get_portfolio()

if not positions:
    st.info("""
    **Noch keine Positionen.** 

    Füge Positionen über die Sidebar hinzu,
    oder lade das Demo-Portfolio zum Ausprobieren.
    """)
    st.stop()

# ── Aktuelle Kurse laden ──────────────────────
client = get_client()

with st.spinner("Lade aktuelle Kurse..."):
    enriched = []
    for pos in positions:
        ticker    = pos["ticker"]
        quote     = client.get_quote(ticker)
        cur_price = quote.get("price", pos["buy_price"])
        qty       = pos["qty"]
        buy_price = pos["buy_price"]

        cost_basis   = qty * buy_price
        market_value = qty * cur_price
        pnl          = market_value - cost_basis
        pnl_pct      = (cur_price - buy_price) / buy_price

        enriched.append({
            "Ticker":        ticker,
            "Stück":         qty,
            "Kaufkurs":      fmt_price(buy_price),
            "Aktuell":       fmt_price(cur_price),
            "Marktwert":     fmt_large(market_value),
            "P&L":           fmt_large(pnl),
            "P&L %":         fmt_pct(pnl_pct),
            # Raw für Berechnungen
            "_market_value": market_value,
            "_cost_basis":   cost_basis,
            "_pnl":          pnl,
            "_pnl_pct":      pnl_pct,
            "_cur_price":    cur_price,
        })

df_portfolio = pd.DataFrame(enriched)

# ── KPI-Zusammenfassung ───────────────────────
total_value   = df_portfolio["_market_value"].sum()
total_cost    = df_portfolio["_cost_basis"].sum()
total_pnl     = df_portfolio["_pnl"].sum()
total_pnl_pct = (total_value - total_cost) / total_cost if total_cost else 0
pnl_color     = color_pct(total_pnl)

st.markdown(f"""
<div style="background:#1e2329; border-radius:12px; padding:20px; margin-bottom:20px;
            display:flex; gap:40px; align-items:center;">
    <div>
        <div style="color:#8b95a1; font-size:0.85rem;">Gesamtwert</div>
        <div style="font-size:2rem; font-weight:700;">{fmt_large(total_value)}</div>
    </div>
    <div>
        <div style="color:#8b95a1; font-size:0.85rem;">Investiert</div>
        <div style="font-size:1.4rem; font-weight:600;">{fmt_large(total_cost)}</div>
    </div>
    <div>
        <div style="color:#8b95a1; font-size:0.85rem;">Unrealisierter Gewinn</div>
        <div style="font-size:1.4rem; font-weight:700; color:{pnl_color};">
            {trend_arrow(total_pnl)} {fmt_large(abs(total_pnl))} ({fmt_pct(total_pnl_pct)})
        </div>
    </div>
    <div>
        <div style="color:#8b95a1; font-size:0.85rem;">Positionen</div>
        <div style="font-size:1.4rem; font-weight:600;">{len(positions)}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Charts & Tabelle ──────────────────────────
col_chart, col_pie = st.columns([3, 2])

with col_pie:
    st.markdown("**Portfolio-Aufteilung**")
    labels = [r["Ticker"] for _, r in df_portfolio.iterrows()]
    values = [r["_market_value"] for _, r in df_portfolio.iterrows()]

    fig_pie = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        textinfo="label+percent",
        marker=dict(colors=px.colors.qualitative.Set2),
    ))
    fig_pie.update_layout(
        template="plotly_dark",
        height=300,
        paper_bgcolor="#0e1117",
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col_chart:
    st.markdown("**P&L je Position**")
    pnl_vals = [r["_pnl"] for _, r in df_portfolio.iterrows()]
    tickers  = [r["Ticker"] for _, r in df_portfolio.iterrows()]
    colors   = ["#26a69a" if v >= 0 else "#ef5350" for v in pnl_vals]

    fig_bar = go.Figure(go.Bar(
        x=tickers, y=pnl_vals,
        marker_color=colors,
        text=[fmt_large(v) for v in pnl_vals],
        textposition="outside",
    ))
    fig_bar.update_layout(
        template="plotly_dark",
        height=300,
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        margin=dict(l=0, r=0, t=10, b=0),
        yaxis=dict(showgrid=False, showticklabels=False),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# ── Positions-Tabelle ─────────────────────────
st.markdown("### 📋 Positions-Übersicht")

# Nur Anzeige-Spalten
display_cols = ["Ticker", "Stück", "Kaufkurs", "Aktuell", "Marktwert", "P&L", "P&L %"]
display_df   = df_portfolio[display_cols]

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    height=min(400, 60 + len(display_df) * 38),
)

# Export
csv = df_portfolio[display_cols].to_csv(index=False).encode("utf-8")
st.download_button(
    label="📥 Portfolio als CSV",
    data=csv,
    file_name="portfolio.csv",
    mime="text/csv",
)
