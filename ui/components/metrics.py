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
    # FIX: Richtiger Variablenzugriff
    price = quote_data.get("price", 0)
    change = quote_data.get("change", 0)
    pct = quote_data.get("change_pct", 0) # Erwartet Dezimalwert (z.B. 0.015)
    
    color = color_pct(pct)
    arrow = trend_arrow(pct)
    
    st.markdown(f"""
    <div style="background:#1e2329; border-radius:12px; padding:20px 24px; margin-bottom:20px;">
        <div style="display:flex; align-items:baseline; gap:20px;">
            <h1 style="margin:0; font-size:2.5rem; font-weight:800;">{ticker}</h1>
            <div style="font-size:2rem; font-weight:700;">{fmt_price(price)}</div>
            <div style="color:{color}; font-size:1.3rem; font-weight:600;">
                {arrow} {fmt_price(change)} ({fmt_pct(pct)})
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def kpi_row(metrics: List[Dict[str, str]], columns: Optional[int] = None):
    if not metrics: return
    num_cols = columns or len(metrics)
    cols = st.columns(num_cols)
    for i, metric in enumerate(metrics):
        with cols[i % num_cols]:
            st.markdown(f"""
            <div style="background:#1e2329; border-radius:8px; padding:14px; text-align:center;">
                <div style="color:#8b95a1; font-size:0.8rem; margin-bottom:6px;">{metric.get("label", "")}</div>
                <div style="font-size:1.4rem; font-weight:700;">{metric.get("value", "N/A")}</div>
            </div>
            """, unsafe_allow_html=True)

def format_large_number(value: Any) -> str:
    return fmt_large(value)