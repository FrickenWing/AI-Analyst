import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import requests
from services.technical_analysis_service import get_technical_analysis_service
from services.market_service import get_market_service
from data.openbb_client import get_client

# --- CONFIG ---
st.set_page_config(
    page_title="AI Analyst",
    page_icon="🤖",
    layout="wide"
)

# CSS
st.markdown("""
<style>
    .ai-recommendation {
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        margin: 20px 0;
    }
    .rec-buy { background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 100%); border: 2px solid #4caf50; }
    .rec-sell { background: linear-gradient(135deg, #b71c1c 0%, #c62828 100%); border: 2px solid #ef5350; }
    .rec-hold { background: linear-gradient(135deg, #37474f 0%, #455a64 100%); border: 2px solid #78909c; }
    .rec-badge {
        font-size: 2.5rem;
        font-weight: bold;
        padding: 15px 30px;
        border-radius: 10px;
        display: inline-block;
    }
    .badge-buy { background: #4caf50; color: white; }
    .badge-sell { background: #ef5350; color: white; }
    .badge-hold { background: #78909c; color: white; }
    .metric-card {
        background: #1e2329;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    .section-header {
        background: linear-gradient(90deg, #2962FF, #00C805);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
        font-size: 1.3rem;
    }
    .confidence-bar {
        height: 20px;
        border-radius: 10px;
        background: #2a2e39;
        overflow: hidden;
    }
    .confidence-fill {
        height: 100%;
        border-radius: 10px;
        transition: width 0.5s ease;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.title("🤖 AI Analyst")
ticker = st.sidebar.text_input("Ticker", value="NVDA").upper()

# API Keys
api_key = st.sidebar.text_input("🔑 Gemini API Key", type="password", help="https://aistudio.google.com/app/apikey")

st.sidebar.markdown("---")
st.sidebar.info("""
**Was wird analysiert:**
- Technische Indikatoren
- Fundamentaldaten
- Analysten-Meinungen
- News & Stimmung
- Preisvorhersagen
""")

# --- LOAD DATA ---
client = get_client()
market_svc = get_market_service()
tech_svc = get_technical_analysis_service()

# Fetch all data in parallel
with st.spinner(f"Lade Daten für {ticker}..."):
    # Quote data
    quote = client.get_quote(ticker)

    # Technical analysis
    df = tech_svc.get_price_data(ticker, period="3mo")
    tech_analysis = tech_svc.analyze_indicators(df) if not df.empty else {}

    # Analyst data
    analyst = market_svc.get_analyst_info(ticker)

    # News
    news = client.get_news(ticker, limit=5)

    # Key stats
    stats = client.get_key_stats(ticker)

if not quote:
    st.error(f"Keine Daten für {ticker} gefunden.")
    st.stop()

# Extract data
price = quote.get('price', 0)
change = quote.get('change', 0)
change_pct = quote.get('change_pct', 0)

# --- HEADER ---
col_title, col_price = st.columns([3, 1])

with col_title:
    st.title(f"🤖 AI Analyst: {ticker}")
    st.markdown(f"### {quote.get('name', ticker)}")

with col_price:
    color = "#00C805" if change >= 0 else "#FF3B30"
    st.markdown(f"""
    <div style="text-align: right; padding: 20px;">
        <div style="font-size: 2.5rem; font-weight: bold;">${price:.2f}</div>
        <div style="font-size: 1.2rem; color: {color};">{change:+.2f} ({change_pct:+.2%})</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- AI RECOMMENDATION SECTION ---
st.markdown("## 🎯 KI Empfehlung")

# Generate AI recommendation if API key provided
ai_recommendation = None
ai_confidence = 0
ai_analysis = None

if api_key and tech_analysis:
    try:
        prompt = f"""Analysiere {ticker} umfassend und gib eine klare Kaufempfehlung.

## TECHNISCHE ANALYSE:
- Aktueller Preis: ${price:.2f}
- RSI: {tech_analysis.get('latest_data', {}).get('rsi', 'N/A')}
- Technischer Score: {tech_analysis.get('score', 'N/A')} (von -100 bis +100)
- Buy-Signale: {tech_analysis.get('buy_signals', 0)}
- Sell-Signale: {tech_analysis.get('sell_signals', 0)}

## FUNDAMENTALDaten:
- Marktkapitalisierung: ${quote.get('market_cap', 'N/A'):,.0f}
- P/E Ratio: {quote.get('pe_ratio', 'N/A')}
- 52W Hoch: ${quote.get('week_52_high', 'N/A'):.2f}
- 52W Tief: ${quote.get('week_52_low', 'N/A'):.2f}
- Sektor: {quote.get('sector', 'N/A')}

## ANALYSTEN:
- Empfehlung: {analyst.get('recommendation', 'N/A')}
- Kursziel: ${analyst.get('target_mean', 'N/A')}
- Upside: {analyst.get('fmt_upside', 'N/A')}

AUFGABE:
1. Gib eine KLARE Empfehlung: BUY, SELL oder HOLD
2. Gib eine Confidence (0-100%) an
3. Erkläre in 2-3 Sätzen warum
4. Nenne Einstiegspunkt, Stop-Loss und Kursziel

Antworte im JSON Format:
{{"recommendation": "BUY/SELL/HOLD", "confidence": 85, "summary": "...", "entry": 150, "stop_loss": 140, "target": 180}}
"""

        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        with st.spinner("🤖 KI analysiert..."):
            response = requests.post(f"{url}?key={api_key}", headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            result = response.json()
            ai_text = result['candidates'][0]['content']['parts'][0]['text']

            # Try to parse JSON from response
            import json
            import re
            json_match = re.search(r'\{[^{}]*\}', ai_text.replace('\n', ''))
            if json_match:
                ai_recommendation = json.loads(json_match.group())
    except Exception as e:
        st.warning(f"KI-Analyse fehlgeschlagen: {e}")

# Display recommendation
if ai_recommendation:
    rec = ai_recommendation.get('recommendation', 'HOLD').upper()
    conf = ai_recommendation.get('confidence', 50)
    summary = ai_recommendation.get('summary', '')
    entry = ai_recommendation.get('entry', price)
    stop = ai_recommendation.get('stop_loss', price * 0.95)
    target = ai_recommendation.get('target', price * 1.2)

    rec_class = "rec-buy" if rec == "BUY" else "rec-sell" if rec == "SELL" else "rec-hold"
    badge_class = "badge-buy" if rec == "BUY" else "badge-sell" if rec == "SELL" else "badge-hold"

    col_rec, col_conf = st.columns([2, 1])

    with col_rec:
        st.markdown(f"""
        <div class="ai-recommendation {rec_class}">
            <div style="color: #aaa; margin-bottom: 10px;">EMPFEHLUNG</div>
            <div class="rec-badge {badge_class}">{rec}</div>
            <p style="margin-top: 20px; font-size: 1.1rem;">{summary}</p>
        </div>
        """, unsafe_allow_html=True)

    with col_conf:
        st.markdown("### Konfidenz")
        st.markdown(f"## {conf}%")
        st.markdown(f"""
        <div class="confidence-bar">
            <div class="confidence-fill" style="width: {conf}%; background: {'#4caf50' if conf > 70 else '#ffa726' if conf > 40 else '#ef5350'};"></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### Trading Plan")
        st.metric("Einstieg", f"${entry:.2f}")
        st.metric("Stop-Loss", f"${stop:.2f}", delta=f"{(stop/entry-1)*100:.1f}%")
        st.metric("Kursziel", f"${target:.2f}", delta=f"{(target/entry-1)*100:.1f}%")

else:
    # Fallback: rule-based recommendation
    if tech_analysis:
        score = tech_analysis.get('score', 0)
        if score > 30:
            rec = "BUY"
            rec_class = "rec-buy"
        elif score < -30:
            rec = "SELL"
            rec_class = "rec-sell"
        else:
            rec = "HOLD"
            rec_class = "rec-hold"

        st.markdown(f"""
        <div class="ai-recommendation {rec_class}">
            <div style="color: #aaa;">TECHNISCHE EMPFEHLUNG</div>
            <div class="rec-badge badge-{rec.lower()}">{rec}</div>
            <p style="margin-top: 15px;">Score: {score}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Keine technische Analyse verfügbar.")

# --- DATA SECTIONS ---
st.markdown("---")

col_tech, col_fund = st.columns(2)

# TECHNICAL
with col_tech:
    st.markdown("### 📊 Technische Analyse")

    if tech_analysis:
        data = tech_analysis.get('latest_data', {})

        c1, c2, c3 = st.columns(3)
        c1.metric("RSI (14)", f"{data.get('rsi', 0):.1f}")
        c2.metric("ATR", f"{data.get('atr', 0):.2f}")
        c3.metric("Score", f"{tech_analysis.get('score', 0):.0f}")

        st.markdown("#### Signale")
        signals_df = pd.DataFrame([
            {"Indikator": k.upper(), "Signal": v['signal'], "Grund": v['reason']}
            for k, v in tech_analysis.get('signals', {}).items()
        ])
        st.dataframe(signals_df, hide_index=True, use_container_width=True)
    else:
        st.warning("Keine technischen Daten verfügbar.")

# FUNDAMENTALS
with col_fund:
    st.markdown("### 📈 Fundamentaldaten")

    c1, c2 = st.columns(2)
    c1.metric("Marktkap", f"${quote.get('market_cap', 0)/1e9:.1f}B" if quote.get('market_cap') else "N/A")
    c2.metric("P/E", f"{quote.get('pe_ratio', 'N/A')}")

    c3, c4 = st.columns(2)
    c3.metric("52W Hoch", f"${quote.get('week_52_high', 0):.2f}")
    c4.metric("52W Tief", f"${quote.get('week_52_low', 0):.2f}")

    st.markdown("**Sektor:** " + (quote.get('sector', 'N/A') or 'N/A'))

# ANALYSTS
st.markdown("---")
st.markdown("### 👔 Analysten Meinungen")

if analyst:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rating", analyst.get('recommendation', 'N/A'))
    c2.metric("Kursziel", f"${analyst.get('target_mean', 'N/A')}" if analyst.get('target_mean') else "N/A")
    c3.metric("High", f"${analyst.get('target_high', 'N/A')}" if analyst.get('target_high') else "N/A")
    c4.metric("Low", f"${analyst.get('target_low', 'N/A')}" if analyst.get('target_low') else "N/A")

    if analyst.get('fmt_upside'):
        st.progress(min(float(analyst.get('fmt_upside', '0%').replace('%', '')) / 100, 1.0))
        st.caption(f"Upside zum Kursziel: {analyst.get('fmt_upside')}")
else:
    st.info("Keine Analysten-Daten verfügbar.")

# NEWS
st.markdown("---")
st.markdown("### 📰 Neueste Nachrichten")

if news:
    for item in news[:5]:
        st.markdown(f"""
        <div style="margin-bottom: 10px; padding: 10px; background: #1e2329; border-radius: 8px;">
            <a href="{item.get('url')}" target="_blank" style="color: #2962FF; font-weight: bold;">{item.get('title')}</a>
            <div style="color: #78909c; font-size: 0.8rem;">{item.get('source')} • {item.get('published', '')[:16]}</div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("Keine News verfügbar.")

# KEY STATS EXPANDER
with st.expander("📋 Alle Key Statistics"):
    if stats:
        for section, items in stats.items():
            st.markdown(f"**{section}**")
            cols = st.columns(4)
            for i, (k, v) in enumerate(items.items()):
                cols[i % 4].metric(k, str(v))
