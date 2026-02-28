"""
ui/components/metrics.py - Metric Display Components
"""
import streamlit as st
from typing import List, Dict, Optional, Any
from utils.formatters import fmt_price, fmt_pct, fmt_large, color_pct, trend_arrow

def price_header(ticker: str, quote_data: Dict[str, Any]):
    """
    Zeigt Preis-Header mit Ticker, Preis, Änderung
    """
    price = quote_data.get("price", 0)
    change = quote_data.get("change", 0)
    pct = quote_data.get("change_pct", 0)
    
    color = color_pct(pct)
    arrow = trend_arrow(pct)
    
    st.markdown(f"""
    <div style="background:#1e2329; border-radius:12px; padding:20px 24px; margin-bottom:20px; border: 1px solid #333;">
        <div style="display:flex; align-items:baseline; gap:20px;">
            <h1 style="margin:0; font-size:2.5rem; font-weight:800;">{ticker}</h1>
            <div style="font-size:2rem; font-weight:700;">{fmt_price(price)}</div>
            <div style="color:{color}; font-size:1.3rem; font-weight:600;">
                {arrow} {fmt_price(change)} ({fmt_pct(pct)})
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_kpi_card(label: str, value: str, help_text: Optional[str] = None):
    """
    Zeigt eine einzelne KPI Karte (für Header oder Grid)
    """
    tooltip = f'title="{help_text}"' if help_text else ''
    
    st.markdown(f"""
    <div {tooltip} style="background-color: #1e2329; padding: 15px; border-radius: 10px; border: 1px solid #333; text-align: center; height: 100%;">
        <div style="font-size: 0.8rem; color: #888; margin-bottom: 5px;">{label}</div>
        <div style="font-size: 1.2rem; font-weight: bold;">{value}</div>
    </div>
    """, unsafe_allow_html=True)

def kpi_row(metrics: List[Dict[str, str]], columns: Optional[int] = None):
    """
    Zeigt eine Reihe von KPIs
    """
    if not metrics: return
    num_cols = columns or len(metrics)
    cols = st.columns(num_cols)
    for i, metric in enumerate(metrics):
        with cols[i % num_cols]:
            render_kpi_card(metric.get("label", ""), metric.get("value", "N/A"))

def format_large_number(value: Any) -> str:
    return fmt_large(value)