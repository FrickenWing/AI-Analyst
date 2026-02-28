import streamlit as st
import pandas as pd
import plotly.express as px
from data.openbb_client import get_client
from ui.components.metrics import render_kpi_card  # Falls du das ausgelagert hast, sonst nutzen wir st.metric

# --- CONFIG ---
st.set_page_config(
    page_title="AI Analyst Dashboard", 
    page_icon="🚀", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS für Dashboard-Cards
st.markdown("""
<style>
    /* Karten-Look für Indizes */
    div[data-testid="stMetric"] {
        background-color: #1e2329;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #333;
    }
    /* Hover Effekt für Buttons */
    button[kind="secondary"]:hover {
        border-color: #00C805 !important;
        color: #00C805 !important;
    }
</style>
""", unsafe_allow_html=True)

# Client init
client = get_client()

# --- HEADER ---
st.title("🚀 Market Dashboard")
st.markdown("Willkommen zurück! Hier ist dein Marktüberblick für heute.")

st.divider()

# --- 1. MARKET INDICES (Die "Big Picture" View) ---
st.subheader("🌍 Markt Stimmung")

# Wir simulieren Indizes durch ETFs (da wir Realtime-Daten brauchen)
indices = [
    {"symbol": "SPY", "name": "S&P 500"},
    {"symbol": "QQQ", "name": "Nasdaq 100"},
    {"symbol": "DIA", "name": "Dow Jones"},
    {"symbol": "BTC-USD", "name": "Bitcoin"},
]

cols = st.columns(len(indices))

# Daten laden und anzeigen
for col, idx in zip(cols, indices):
    with col:
        q = client.get_quote(idx["symbol"])
        if q:
            st.metric(
                label=idx["name"],
                value=f"{q.get('price', 0):.2f}",
                delta=f"{q.get('change_pct', 0):.2%}"
            )
        else:
            st.metric(label=idx["name"], value="Lade...", delta=None)

st.write("") # Spacer

# --- 2. TRENDING & WATCHLIST ---
col_trend, col_nav = st.columns([2, 1])

with col_trend:
    st.subheader("🔥 Markt Pulse (Tech & AI)")
    
    # Eine feste Watchlist für den schnellen Blick (könnte man später dynamisch machen)
    watchlist_tickers = ["NVDA", "AAPL", "MSFT", "TSLA", "AMD", "GOOGL", "AMZN"]
    
    watchlist_data = []
    # Progress Bar für das Laden der Watchlist, damit es nicht "hängt"
    progress_text = "Lade Kurse..."
    my_bar = st.progress(0, text=progress_text)
    
    for i, t in enumerate(watchlist_tickers):
        q = client.get_quote(t)
        if q:
            watchlist_data.append({
                "Symbol": t,
                "Preis": q.get("price"),
                "Änderung %": q.get("change_pct"), # Rohdaten für Farbe
                "Volumen": q.get("volume")
            })
        my_bar.progress((i + 1) / len(watchlist_tickers), text=progress_text)
    
    my_bar.empty() # Balken entfernen wenn fertig

    if watchlist_data:
        df_watch = pd.DataFrame(watchlist_data)
        
        # Formatierung für die Anzeige
        st.dataframe(
            df_watch,
            column_config={
                "Symbol": st.column_config.TextColumn("Ticker", width="medium"),
                "Preis": st.column_config.NumberColumn("Preis ($)", format="$%.2f"),
                "Änderung %": st.column_config.NumberColumn(
                    "24h %",
                    format="%.2f %%",
                ),
                "Volumen": st.column_config.NumberColumn("Volumen", format="%d"),
            },
            hide_index=True,
            use_container_width=True,
            height=300
        )
    else:
        st.info("Konnte Watchlist nicht laden.")

with col_nav:
    st.subheader("⚡ Quick Actions")
    
    with st.container():
        st.markdown("""
        <div style="background-color: #262730; padding: 20px; border-radius: 10px;">
            <h4>Was möchtest du tun?</h4>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        
        # Navigation ist in Streamlit via Sidebar gelöst, aber wir können 
        # hier Hinweise geben oder Session State setzen.
        st.info("👈 Nutze die Sidebar, um zum **Terminal** zu wechseln.")
        
        st.markdown("### 💡 Neuigkeiten")
        st.caption("Das neue **Terminal** ist jetzt live! Alle Charts & Finanzen an einem Ort.")
        
        # Platz für zukünftige Features (z.B. "Zuletzt angesehen")
        if "ticker" in st.session_state:
            st.write(f"Zuletzt analysiert: **{st.session_state.ticker}**")

# --- FOOTER ---
st.divider()
st.caption("AI Analyst v2.0 - Powered by OpenBB & Streamlit")