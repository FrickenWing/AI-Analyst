"""
ui/components/sidebar.py - Sidebar-Komponenten

Wiederverwendbare Sidebar-Elemente:
- Ticker-Input
- Timeframe-Selektor
- Indikator-Einstellungen
"""

import streamlit as st
from typing import Tuple, Dict
from config import TIMEFRAMES, DEFAULT_TICKER, DEFAULT_TIMEFRAME


def render_ticker_input(default: str = DEFAULT_TICKER, label: str = "Ticker-Symbol") -> str:
    """
    Ticker-Eingabefeld
    
    Args:
        default: Standard-Ticker
        label: Label-Text
    
    Returns:
        Ticker-Symbol (uppercase)
    """
    ticker = st.sidebar.text_input(
        label,
        value=default,
        max_chars=10,
        help="Gib ein Ticker-Symbol ein (z.B. AAPL, MSFT, TSLA)"
    ).strip().upper()
    
    return ticker if ticker else default


def render_timeframe_selector() -> Tuple[str, str]:
    """
    Timeframe-Auswahl (Interval + Period)
    
    Returns:
        Tuple (interval, period)
        z.B. ("1d", "1y")
    """
    timeframe_key = st.sidebar.selectbox(
        "Zeitrahmen",
        options=list(TIMEFRAMES.keys()),
        index=list(TIMEFRAMES.keys()).index(DEFAULT_TIMEFRAME),
        format_func=lambda x: TIMEFRAMES[x]["label"],
        help="Wähle den gewünschten Zeitrahmen"
    )
    
    tf = TIMEFRAMES[timeframe_key]
    return tf["interval"], tf["period"]


def render_indicator_settings() -> Dict[str, bool]:
    """
    Indikator-Einstellungen
    
    Returns:
        Dict mit aktivierten Indikatoren
        z.B. {"sma_20": True, "rsi": False, ...}
    """
    st.sidebar.markdown("### 📊 Indikatoren")
    
    indicators = {}
    
    # ─────────────────────────────────────────────
    # Trend Indicators
    # ─────────────────────────────────────────────
    with st.sidebar.expander("📈 Trend", expanded=True):
        indicators["sma_20"] = st.checkbox("SMA 20", value=True, key="ind_sma20")
        indicators["sma_50"] = st.checkbox("SMA 50", value=True, key="ind_sma50")
        indicators["sma_200"] = st.checkbox("SMA 200", value=False, key="ind_sma200")
        indicators["ema_9"] = st.checkbox("EMA 9", value=False, key="ind_ema9")
    
    # ─────────────────────────────────────────────
    # Volatility
    # ─────────────────────────────────────────────
    with st.sidebar.expander("📊 Volatilität"):
        indicators["bb"] = st.checkbox("Bollinger Bands", value=False, key="ind_bb")
        indicators["atr"] = st.checkbox("ATR", value=False, key="ind_atr")
    
    # ─────────────────────────────────────────────
    # Momentum
    # ─────────────────────────────────────────────
    with st.sidebar.expander("⚡ Momentum"):
        indicators["rsi"] = st.checkbox("RSI", value=True, key="ind_rsi")
        indicators["macd"] = st.checkbox("MACD", value=True, key="ind_macd")
        indicators["stoch"] = st.checkbox("Stochastic", value=False, key="ind_stoch")
    
    # ─────────────────────────────────────────────
    # Volume
    # ─────────────────────────────────────────────
    with st.sidebar.expander("📊 Volumen"):
        indicators["volume"] = st.checkbox("Volume Bars", value=True, key="ind_volume")
        indicators["obv"] = st.checkbox("OBV", value=False, key="ind_obv")
        indicators["vwap"] = st.checkbox("VWAP", value=False, key="ind_vwap")
    
    return indicators


def render_watchlist_selector() -> str:
    """
    Watchlist-Auswahl
    
    Returns:
        Ausgewählter Ticker aus Watchlist
    """
    watchlist = st.session_state.get("watchlist", [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"
    ])
    
    if not watchlist:
        st.sidebar.info("Watchlist ist leer")
        return ""
    
    selected = st.sidebar.selectbox(
        "Watchlist",
        options=watchlist,
        help="Wähle Ticker aus deiner Watchlist"
    )
    
    return selected


def render_chart_settings():
    """
    Chart-Einstellungen (Theme, Höhe, etc.)
    
    Returns:
        Dict mit Chart-Settings
    """
    st.sidebar.markdown("### ⚙️ Chart-Einstellungen")
    
    settings = {}
    
    settings["height"] = st.sidebar.slider(
        "Chart-Höhe",
        min_value=400,
        max_value=1000,
        value=600,
        step=50,
        help="Höhe des Charts in Pixeln"
    )
    
    settings["show_volume"] = st.sidebar.checkbox(
        "Volume anzeigen",
        value=True,
        help="Zeigt Volumen-Balken unter dem Chart"
    )
    
    settings["show_grid"] = st.sidebar.checkbox(
        "Grid anzeigen",
        value=True,
        help="Zeigt Grid-Linien im Chart"
    )
    
    return settings


def render_refresh_button():
    """
    Refresh-Button für Daten-Aktualisierung
    """
    if st.sidebar.button("🔄 Daten aktualisieren", use_container_width=True):
        # Cache clearen
        st.cache_data.clear()
        st.rerun()


def render_export_options(ticker: str):
    """
    Export-Optionen
    
    Args:
        ticker: Ticker-Symbol für Dateinamen
    """
    st.sidebar.markdown("### 📥 Export")
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("CSV", use_container_width=True, help="Exportiere Daten als CSV"):
            st.info("CSV-Export wird implementiert...")
    
    with col2:
        if st.button("PDF", use_container_width=True, help="Exportiere Chart als PDF"):
            st.info("PDF-Export wird implementiert...")


def render_info_section(title: str, content: str):
    """
    Info-Sektion in Sidebar
    
    Args:
        title: Titel
        content: Markdown-Content
    """
    with st.sidebar.expander(f"ℹ️ {title}"):
        st.markdown(content)


def render_connection_status():
    """
    Zeigt OpenBB Connection Status
    """
    from data.openbb_client import get_client
    
    try:
        client = get_client()
        st.sidebar.success("✅ OpenBB verbunden")
    except Exception as e:
        st.sidebar.error(f"❌ OpenBB Fehler: {str(e)[:50]}")
