"""
ui/components/sidebar.py - Nur noch für Navigation & Globale Tools
"""
import streamlit as st

# Die Funktionen hier werden ggf. noch von anderen Seiten (Screener etc.) genutzt.
# Für die Charts-Seite brauchen wir sie nicht mehr zwingend, lassen sie aber 
# als Fallback drin, falls du sie woanders einbaust.

def render_ticker_input():
    """Veraltet für Charts-Seite, aber evtl. nützlich für andere Tools."""
    return st.sidebar.text_input("Ticker", st.session_state.get("current_ticker", "AAPL"))

def render_timeframe_selector():
    """Dummy-Funktion, damit alte Importe nicht abstürzen."""
    return "1d", "1y"

def render_indicator_settings():
    """Dummy-Funktion."""
    return {}