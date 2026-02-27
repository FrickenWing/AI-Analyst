"""
ui/components/metrics.py - Metric Display Components

Wiederverwendbare Komponenten für:
- Preis-Header
- KPI-Zeilen
- Metriken-Cards
- Formatierungs-Helpers
"""

import streamlit as st
from typing import List, Dict, Optional, Any
from utils.formatters import fmt_price, fmt_pct, fmt_large, color_pct, trend_arrow


def price_header(ticker: str, quote_data: Dict[str, Any]):
    """
    Zeigt Preis-Header mit Ticker, Preis, Änderung
    
    Args:
        ticker: Ticker-Symbol
        quote_data: Dict mit price, change, change_pct
    """
    price = quote_data.get("price", 0)
    change = quote_data.get("change", 0)
    change_pct = quote_data.get("change_pct", 0)
    
    color = color_pct(change_pct)
    arrow = trend_arrow(change_pct)
    
    st.markdown(f"""
    <div style="background:#1e2329; border-radius:12px; padding:20px 24px; margin-bottom:20px;">
        <div style="display:flex; align-items:baseline; gap:20px;">
            <h1 style="margin:0; font-size:2.5rem; font-weight:800;">{ticker}</h1>
            <div style="font-size:2rem; font-weight:700;">{fmt_price(price)}</div>
            <div style="color:{color}; font-size:1.3rem; font-weight:600;">
                {arrow} {fmt_price(change)} ({fmt_pct(change_pct)})
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def kpi_row(metrics: List[Dict[str, str]], columns: Optional[int] = None):
    """
    Zeigt KPI-Zeile mit mehreren Metriken
    
    Args:
        metrics: Liste von Dicts mit {"label": "...", "value": "...", "help": "..."}
        columns: Anzahl Spalten (default: auto basierend auf Anzahl Metriken)
    """
    if not metrics:
        return
    
    num_cols = columns or len(metrics)
    cols = st.columns(num_cols)
    
    for i, metric in enumerate(metrics):
        col_idx = i % num_cols
        with cols[col_idx]:
            st.markdown(f"""
            <div style="background:#1e2329; border-radius:8px; padding:14px; text-align:center;">
                <div style="color:#8b95a1; font-size:0.8rem; margin-bottom:6px;">
                    {metric.get("label", "")}
                </div>
                <div style="font-size:1.4rem; font-weight:700;">
                    {metric.get("value", "N/A")}
                </div>
            </div>
            """, unsafe_allow_html=True)


def metric_card(label: str, value: Any, delta: Optional[float] = None, 
                delta_color: bool = True, help_text: Optional[str] = None):
    """
    Einzelne Metrik-Card
    
    Args:
        label: Label-Text
        value: Wert
        delta: Optional: Änderung (als Dezimal, z.B. 0.05 für +5%)
        delta_color: Ob Delta farbig dargestellt werden soll
        help_text: Tooltip-Text
    """
    if delta is not None:
        delta_formatted = fmt_pct(delta)
        delta_color_val = color_pct(delta) if delta_color else "#8b95a1"
        delta_arrow = trend_arrow(delta)
        delta_html = f'<div style="color:{delta_color_val}; font-size:0.9rem; margin-top:4px;">{delta_arrow} {delta_formatted}</div>'
    else:
        delta_html = ""
    
    help_icon = f' <span title="{help_text}" style="color:#8b95a1; font-size:0.8rem; cursor:help;">ℹ️</span>' if help_text else ""
    
    st.markdown(f"""
    <div style="background:#1e2329; border-radius:8px; padding:16px;">
        <div style="color:#8b95a1; font-size:0.85rem; margin-bottom:8px;">
            {label}{help_icon}
        </div>
        <div style="font-size:1.6rem; font-weight:700;">
            {value}
        </div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def format_large_number(value: Any, decimals: int = 2) -> str:
    """
    Formatiert große Zahlen (wrapper für fmt_large)
    
    Args:
        value: Zahl
        decimals: Dezimalstellen
    
    Returns:
        Formatierter String
    """
    return fmt_large(value, decimals)


def format_pct(value: Any, decimals: int = 2) -> str:
    """Formatiert Prozent (wrapper für fmt_pct)"""
    return fmt_pct(value, decimals)


def format_price(value: Any, decimals: int = 2) -> str:
    """Formatiert Preis (wrapper für fmt_price)"""
    return fmt_price(value, decimals)


def status_badge(status: str, label: Optional[str] = None) -> str:
    """
    Erstellt Status-Badge HTML
    
    Args:
        status: "success", "warning", "danger", "info"
        label: Badge-Text
    
    Returns:
        HTML String
    """
    colors = {
        "success": "#26a69a",
        "warning": "#ffab40",
        "danger": "#ef5350",
        "info": "#42a5f5",
        "neutral": "#8b95a1",
    }
    
    color = colors.get(status, colors["neutral"])
    text = label or status.upper()
    
    return f"""
    <span style="background:{color}; color:#fff; padding:4px 12px; 
                 border-radius:12px; font-size:0.75rem; font-weight:600;">
        {text}
    </span>
    """


def progress_bar(value: float, max_value: float = 100, label: Optional[str] = None,
                 color: str = "#26a69a") -> str:
    """
    Erstellt Fortschrittsbalken HTML
    
    Args:
        value: Aktueller Wert
        max_value: Maximum (default: 100)
        label: Label-Text
        color: Balken-Farbe
    
    Returns:
        HTML String
    """
    percentage = min((value / max_value) * 100, 100)
    label_text = f"<div style='margin-bottom:4px; color:#8b95a1; font-size:0.85rem;'>{label}</div>" if label else ""
    
    return f"""
    <div>
        {label_text}
        <div style="background:#2d3748; border-radius:8px; overflow:hidden; height:20px;">
            <div style="background:{color}; height:100%; width:{percentage}%; 
                       transition:width 0.3s ease; display:flex; align-items:center; 
                       justify-content:center; color:#fff; font-size:0.75rem; font-weight:600;">
                {percentage:.1f}%
            </div>
        </div>
    </div>
    """


def comparison_table(data: List[Dict[str, Any]], columns: List[str]):
    """
    Erstellt Vergleichstabelle
    
    Args:
        data: Liste von Dicts mit Daten
        columns: Spalten-Namen
    """
    import pandas as pd
    
    if not data:
        st.info("Keine Daten verfügbar")
        return
    
    df = pd.DataFrame(data)
    
    # Nur gewünschte Spalten
    if columns:
        available_cols = [col for col in columns if col in df.columns]
        df = df[available_cols]
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )


def highlight_change(value: float, threshold_positive: float = 0, 
                     threshold_negative: float = 0) -> str:
    """
    Gibt Farbe für Wert basierend auf Schwellwerten
    
    Args:
        value: Wert
        threshold_positive: Ab diesem Wert = grün
        threshold_negative: Unter diesem Wert = rot
    
    Returns:
        Hex Farbe
    """
    if value > threshold_positive:
        return "#26a69a"  # Grün
    elif value < threshold_negative:
        return "#ef5350"  # Rot
    else:
        return "#8b95a1"  # Grau
