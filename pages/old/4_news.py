"""pages/4_news.py - News Feed"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from datetime import datetime
from data.openbb_client import get_client
from ui.components.sidebar import render_ticker_input
from utils.formatters import fmt_date

# Beispiel für den Anfang deiner pages/1_charts.py Datei:

# Hole den aktuell ausgewählten Ticker aus dem globalen Speicher. 
# Falls noch nichts gesucht wurde, nimm "AAPL" als Standardwert.
current_ticker = st.session_state.get("current_ticker", "AAPL")

# (Optional) Lass den Nutzer den Ticker in der Sidebar der Unterseite trotzdem noch manuell anpassen
ticker = st.sidebar.text_input("Ticker Symbol", current_ticker).upper()

# Falls der Nutzer es in der Sidebar ändert, aktualisiere den State!
if ticker != current_ticker:
    st.session_state["current_ticker"] = ticker

st.set_page_config(page_title="News", page_icon="📰", layout="wide")

st.sidebar.title("📰 News & Sentiment")
ticker      = render_ticker_input()
news_count  = st.sidebar.slider("Anzahl News", 5, 30, 15)

client = get_client()

st.markdown(f"## 📰 News: {ticker}")

tab1, tab2 = st.tabs(["🎯 Ticker News", "🌍 Watchlist News"])

with tab1:
    with st.spinner(f"Lade News für {ticker}..."):
        news = client.get_news(ticker, limit=news_count)
    if not news:
        st.info(f"Keine aktuellen News für **{ticker}** gefunden.")
    else:
        st.caption(f"{len(news)} News gefunden")
        st.divider()
        for item in news:
            title     = item.get("title","Kein Titel")
            url       = item.get("url","#")
            source    = item.get("source","")
            published = item.get("published")
            summary   = item.get("summary","")
            col_text, col_meta = st.columns([4,1])
            with col_text:
                st.markdown(f"#### [{title}]({url})")
                if summary:
                    st.markdown(f"<p style='color:#8b95a1;font-size:0.9rem;'>{summary[:200]}{'...' if len(summary)>200 else ''}</p>", unsafe_allow_html=True)
            with col_meta:
                if source: st.markdown(f"<p style='color:#8b95a1;font-size:0.8rem;'><b>{source}</b></p>", unsafe_allow_html=True)
                if published:
                    try:
                        dt = datetime.fromtimestamp(published) if isinstance(published,(int,float)) else published
                        st.caption(fmt_date(dt, "%d.%m.%Y"))
                    except: pass
            st.divider()

with tab2:
    watchlist = st.session_state.get("watchlist", ["AAPL","MSFT","NVDA","GOOGL"])
    st.caption(f"Aggregierte News für: {', '.join(watchlist)}")
    if st.button("🔄 Watchlist News laden", type="primary"):
        all_news = []
        prog = st.progress(0)
        for i, wl_ticker in enumerate(watchlist):
            prog.progress((i+1)/len(watchlist), text=f"Lade {wl_ticker}...")
            items = client.get_news(wl_ticker, limit=3)
            for item in items:
                item["_ticker"] = wl_ticker
                all_news.append(item)
        prog.empty()
        all_news.sort(key=lambda x: x.get("published",0) or 0, reverse=True)
        st.session_state["watchlist_news"] = all_news

    wl_news = st.session_state.get("watchlist_news",[])
    if wl_news:
        for item in wl_news[:30]:
            c1, c2 = st.columns([5,1])
            with c1: st.markdown(f"**[{item.get('title','')}]({item.get('url','#')})**")
            with c2: st.markdown(f"`{item.get('_ticker','')}` · {item.get('source','')}")
            st.divider()
    else:
        st.info("Klicke auf 'Watchlist News laden' um News für alle Watchlist-Aktien zu sehen.")
