import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import requests
import json
from services.technical_analysis_service import get_technical_analysis_service

# --- CONFIG ---
st.set_page_config(
    page_title="Technische Analyse + AI",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
    .score-card {
        background: linear-gradient(135deg, #1e2329 0%, #2a2e39 100%);
        border-radius: 15px;
        padding: 30px;
        text-align: center;
        margin: 20px 0;
    }
    .score-value {
        font-size: 4rem;
        font-weight: bold;
    }
    .score-buy { color: #26a69a; }
    .score-sell { color: #ef5350; }
    .score-neutral { color: #ffa726; }
    .signal-badges {
        display: flex;
        gap: 10px;
        justify-content: center;
        margin: 15px 0;
    }
    .signal-badge {
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: bold;
    }
    .badge-buy { background: #26a69a; color: white; }
    .badge-sell { background: #ef5350; color: white; }
    .badge-neutral { background: #546e7a; color: white; }
    .indicator-card {
        background: #1e2329;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #2962FF;
    }
    .ai-box {
        background: linear-gradient(135deg, #1a237e 0%, #283593 100%);
        border-radius: 15px;
        padding: 20px;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# --- TITLE ---
st.title("📊 Technische Analyse + AI")
st.markdown("Hole dir eine KI-gestützte technische Analyse mit Scoring")

# --- SIDEBAR ---
st.sidebar.header("⚙️ Einstellungen")

# Ticker input
ticker = st.sidebar.text_input("Ticker", value="NVDA").upper()

# Time period
period = st.sidebar.selectbox(
    "Zeitraum",
    options=["1mo", "3mo", "6mo", "1y", "2y"],
    index=1,
    format_func=lambda x: {"1mo": "1 Monat", "3mo": "3 Monate", "6mo": "6 Monate", "1y": "1 Jahr", "2y": "2 Jahre"}[x]
)

# Gemini API Key
api_key = st.sidebar.text_input(
    "🔑 Gemini API Key",
    type="password",
    help="Erstelle einen Key unter https://aistudio.google.com/app/apikey"
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Hinweis:** Ohne API Key wird nur die technische Analyse ohne KI-Zusammenfassung angezeigt.")

# --- MAIN LOGIC ---
svc = get_technical_analysis_service()

with st.spinner(f"Lade Daten für {ticker}..."):
    # Get price data with indicators
    df = svc.get_price_data(ticker, period=period, interval="1d")

if df.empty:
    st.error(f"Keine Daten für {ticker} gefunden.")
    st.stop()

# Analyze indicators
analysis = svc.analyze_indicators(df)

if not analysis:
    st.error("Konnte Indikatoren nicht berechnen.")
    st.stop()

# Extract data
data = analysis['latest_data']
score = analysis['score']
signals = analysis['signals']

# --- SCORE DISPLAY ---
st.markdown("### 🎯 Technischer Score")

# Determine color and label
if score > 20:
    score_color = "score-buy"
    score_label = "BULLISH"
elif score < -20:
    score_color = "score-sell"
    score_label = "BEARISH"
else:
    score_color = "score-neutral"
    score_label = "NEUTRAL"

col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.markdown(f"""
    <div class="score-card">
        <div style="font-size: 1.2rem; color: #789b86;">GESAMTSCORE</div>
        <div class="score-value {score_color}">{score}</div>
        <div class="signal-badges">
            <span class="signal-badge badge-buy">▲ {analysis['buy_signals']} BUY</span>
            <span class="signal-badge badge-sell">▼ {analysis['sell_signals']} SELL</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    # Progress bar visualization
    import plotly.graph_objects as go

    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': score_label},
        gauge = {
            'axis': {'range': [-100, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': "#2962FF"},
            'bgcolor': "#1e2329",
            'borderwidth': 2,
            'bordercolor': "#2a2e39",
            'steps': [
                {'range': [-100, -20], 'color': "#ef5350"},
                {'range': [-20, 20], 'color': "#546e7a"},
                {'range': [20, 100], 'color': "#26a69a"},
            ],
        }
    ))

    fig.update_layout(
        paper_bgcolor="transparent",
        font={'color': "white"},
        height=200,
        margin=dict(l=20, r=20, t=50, b=20)
    )

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

with col3:
    st.markdown("### 📈 Preis")
    st.metric("Aktuell", f"${data['price']:.2f}")
    st.metric("RSI (14)", f"{data['rsi']:.1f}")
    st.metric("ATR", f"{data['atr']:.2f}")

# --- SIGNALS TABLE ---
st.markdown("### 📊 Indikator Signale")

signal_data = []
for name, sig in signals.items():
    signal_data.append({
        "Indikator": name.upper(),
        "Signal": sig['signal'],
        "Wert": str(sig['value']),
        "Begründung": sig['reason']
    })

signal_df = pd.DataFrame(signal_data)

# Color the signal column
def color_signal(val):
    if val == 'BUY':
        return 'color: #26a69a; font-weight: bold'
    elif val == 'SELL':
        return 'color: #ef5350; font-weight: bold'
    else:
        return 'color: #ffa726; font-weight: bold'

st.dataframe(
    signal_df.style.applymap(color_signal, subset=['Signal']),
    use_container_width=True,
    hide_index=True
)

# --- GEMINI AI ANALYSIS ---
st.markdown("---")

if api_key:
    st.markdown("### 🤖 KI Analyse (Gemini)")

    # Gemini API via REST
    try:
        prompt = svc.prepare_gemini_prompt(ticker, analysis)

        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }

        with st.spinner("Generiere KI-Analyse..."):
            response = requests.post(
                f"{url}?key={api_key}",
                headers=headers,
                json=payload,
                timeout=30
            )

        if response.status_code == 200:
            result = response.json()
            ai_text = result['candidates'][0]['content']['parts'][0]['text']

            st.markdown(f"""
            <div class="ai-box">
                {ai_text}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error(f"API Fehler: {response.status_code}")
            st.write(response.text)

    except Exception as e:
        st.error(f"Fehler bei Gemini: {str(e)}")
        st.info("Bitte überprüfe deinen API Key.")

else:
    st.info("🔑 Gib einen Gemini API Key in der Sidebar ein, um die KI-Analyse zu aktivieren.")

# --- RAW DATA EXPANDER ---
with st.expander("📋 Rohdaten anzeigen"):
    st.dataframe(df.tail(20), use_container_width=True)
