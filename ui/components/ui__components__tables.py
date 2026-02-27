"""
ui/components/tables.py - Tabellen-Komponenten

Formatierte Tabellen für:
- Financial Statements
- Screener-Ergebnisse
- News
- Generische Daten-Tabellen
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import List, Dict, Optional, Any
from utils.formatters import fmt_price, fmt_pct, fmt_large, fmt_date, color_pct
from datetime import datetime


def styled_dataframe(df: pd.DataFrame, **kwargs):
    """
    Zeigt DataFrame mit Styling
    
    Args:
        df: DataFrame
        **kwargs: Zusätzliche st.dataframe() Parameter
    """
    if df.empty:
        st.info("Keine Daten verfügbar")
        return
    
    defaults = {
        "use_container_width": True,
        "hide_index": False,
        "height": min(600, 60 + len(df) * 38),
    }
    defaults.update(kwargs)
    
    st.dataframe(df, **defaults)


def financial_statement_table(df: pd.DataFrame, title: str = "Financial Statement"):
    """
    Zeigt Financial Statement Tabelle
    
    Args:
        df: DataFrame mit Financial Data
        title: Tabellen-Titel
    """
    if df is None or df.empty:
        st.info(f"{title}: Keine Daten verfügbar")
        return
    
    st.markdown(f"**{title}**")
    
    # Transpose für bessere Lesbarkeit (Jahre als Spalten)
    if len(df.columns) > 1:
        display_df = df.copy()
        
        # Formatiere Index (Metrik-Namen)
        display_df.index = display_df.index.str.replace("_", " ").str.title()
        
        # Limitiere auf letzte 5 Jahre wenn mehr vorhanden
        if len(display_df.columns) > 5:
            display_df = display_df.iloc[:, -5:]
        
        # Formatiere Spalten-Namen (Datum)
        display_df.columns = [str(col)[:4] if isinstance(col, (int, str)) else col 
                             for col in display_df.columns]
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=min(500, 60 + len(display_df) * 38),
        )
    else:
        st.dataframe(df, use_container_width=True)


def screener_result_table(df: pd.DataFrame):
    """
    Zeigt Screener-Ergebnisse formatiert
    
    Args:
        df: DataFrame mit Screener-Ergebnissen
    """
    if df.empty:
        st.warning("Keine Ergebnisse gefunden")
        return
    
    # Sortiere nach Score (falls vorhanden)
    if "Score" in df.columns:
        df = df.sort_values("Score", ascending=False).reset_index(drop=True)
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=min(600, 60 + len(df) * 38),
        column_config={
            "Score": st.column_config.ProgressColumn(
                "Score",
                format="%d/100",
                min_value=0,
                max_value=100,
            ),
        }
    )


def news_table(news_items: List[Dict[str, Any]]):
    """
    Zeigt News-Liste formatiert
    
    Args:
        news_items: Liste von News-Dicts
    """
    if not news_items:
        st.info("Keine News verfügbar")
        return
    
    for item in news_items:
        title = item.get("title", "Kein Titel")
        url = item.get("url", "#")
        source = item.get("source", "Unbekannt")
        published = item.get("published")
        summary = item.get("summary", "")
        
        with st.container():
            col_text, col_meta = st.columns([4, 1])
            
            with col_text:
                st.markdown(f"**[{title}]({url})**")
                if summary:
                    summary_short = summary[:200] + "..." if len(summary) > 200 else summary
                    st.caption(summary_short)
            
            with col_meta:
                st.caption(f"**{source}**")
                if published:
                    try:
                        if isinstance(published, (int, float)):
                            dt = datetime.fromtimestamp(published)
                        else:
                            dt = published
                        st.caption(fmt_date(dt, "%d.%m.%Y"))
                    except:
                        pass
            
            st.divider()


def plotly_bar_chart(labels: List[str], values: List[float], 
                    title: str = "", color_positive: bool = True) -> go.Figure:
    """
    Erstellt Plotly Bar Chart
    
    Args:
        labels: X-Achsen Labels
        values: Y-Achsen Werte
        title: Chart-Titel
        color_positive: Ob positive Werte grün, negative rot gefärbt werden
    
    Returns:
        Plotly Figure
    """
    if color_positive:
        colors = ["#26a69a" if v >= 0 else "#ef5350" for v in values]
    else:
        colors = "#5c6bc0"  # Einheitliche Farbe
    
    fig = go.Figure(go.Bar(
        x=labels,
        y=values,
        marker_color=colors,
        text=[fmt_large(v) for v in values],
        textposition="outside",
    ))
    
    fig.update_layout(
        title=title,
        template="plotly_dark",
        height=300,
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        margin=dict(l=0, r=0, t=40, b=0),
        yaxis=dict(showgrid=False, gridcolor="#1e2329"),
        xaxis=dict(gridcolor="#1e2329"),
    )
    
    return fig


def comparison_table(data: List[Dict[str, Any]], columns: List[str], 
                    highlight_col: Optional[str] = None):
    """
    Erstellt Vergleichstabelle
    
    Args:
        data: Liste von Dicts
        columns: Spalten zum Anzeigen
        highlight_col: Spalte die hervorgehoben werden soll
    """
    if not data:
        st.info("Keine Daten für Vergleich verfügbar")
        return
    
    df = pd.DataFrame(data)
    
    # Nur gewünschte Spalten
    available_cols = [col for col in columns if col in df.columns]
    if available_cols:
        df = df[available_cols]
    
    # Highlight-Config
    column_config = {}
    if highlight_col and highlight_col in df.columns:
        column_config[highlight_col] = st.column_config.NumberColumn(
            highlight_col,
            format="%.2f",
        )
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config=column_config if column_config else None,
    )


def pivot_table(df: pd.DataFrame, index_col: str, columns_col: str, 
               values_col: str, aggfunc: str = "sum"):
    """
    Erstellt Pivot-Tabelle
    
    Args:
        df: DataFrame
        index_col: Index-Spalte
        columns_col: Spalten-Spalte
        values_col: Werte-Spalte
        aggfunc: Aggregations-Funktion
    """
    if df.empty:
        st.info("Keine Daten für Pivot verfügbar")
        return
    
    try:
        pivot = pd.pivot_table(
            df,
            index=index_col,
            columns=columns_col,
            values=values_col,
            aggfunc=aggfunc,
        )
        
        st.dataframe(pivot, use_container_width=True)
    except Exception as e:
        st.error(f"Fehler beim Erstellen der Pivot-Tabelle: {e}")


def metrics_table(metrics: List[Dict[str, Any]]):
    """
    Zeigt Metriken als formatierte Tabelle
    
    Args:
        metrics: Liste von {"label": ..., "value": ..., "change": ...}
    """
    if not metrics:
        st.info("Keine Metriken verfügbar")
        return
    
    for metric in metrics:
        label = metric.get("label", "")
        value = metric.get("value", "N/A")
        change = metric.get("change")
        help_text = metric.get("help", "")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            help_icon = f" ({help_text})" if help_text else ""
            st.markdown(f"**{label}**{help_icon}")
        
        with col2:
            st.markdown(f"`{value}`")
        
        with col3:
            if change is not None:
                color = color_pct(change)
                st.markdown(f"<span style='color:{color};'>{fmt_pct(change)}</span>", 
                           unsafe_allow_html=True)


def key_value_table(data: Dict[str, Any]):
    """
    Zeigt Key-Value Paare als Tabelle
    
    Args:
        data: Dict mit Key-Value Paaren
    """
    if not data:
        st.info("Keine Daten verfügbar")
        return
    
    df = pd.DataFrame([
        {"Metrik": key, "Wert": value}
        for key, value in data.items()
    ])
    
    st.dataframe(df, use_container_width=True, hide_index=True)
