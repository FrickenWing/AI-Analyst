"""
ui/pages/4_📰_news.py - News & Sentiment Feed

Features:
- News für beliebige Ticker
- Markt-News Übersicht
- Sentiment-Anzeige
- Watchlist News aggregiert
"""

import streamlit as st
from datetime import datetime

from data.openbb_client import get_client
from ui.components.sidebar import render_ticker_input
from utils.formatters import fmt_date

# ─────────────────────────────────────────────
st.set_page_config(page_title="News", page_icon="📰", layout="wide")

# ── Sidebar ───────────────────────────────────
st.sidebar.title("📰 News & Sentiment")
ticker = render_ticker_input()

news_count = st.sidebar.slider("Anzahl News", 5, 30, 15)

watchlist_news = st.sidebar.checkbox("Watchlist News aggregieren", value=False)

# ── Daten laden ───────────────────────────────
client = get_client()

# ── Haupt-Bereich ─────────────────────────────
st.markdown(f"## 📰 News: {ticker}")

tab1, tab2 = st.tabs(["🎯 Ticker News", "🌍 Watchlist News"])

# ── TAB 1: Ticker-spezifische News ────────────
with tab1:
    with st.spinner(f"Lade News für {ticker}..."):
        news = client.get_news(ticker, limit=news_count)

    if not news:
        st.info(f"Keine aktuellen News für **{ticker}** gefunden.")
    else:
        st.caption(f"{len(news)} News gefunden")
        st.divider()

        for item in news:
            title     = item.get("title", "Kein Titel")
            url       = item.get("url", "#")
            source    = item.get("source", "Unbekannt")
            published = item.get("published")
            summary   = item.get("summary", "")

            with st.container():
                col_text, col_meta = st.columns([4, 1])

                with col_text:
                    st.markdown(f"#### [{title}]({url})")
                    if summary:
                        st.markdown(f"<p style='color:#8b95a1; font-size:0.9rem;'>{summary[:200]}{'...' if len(summary) > 200 else ''}</p>",
                                    unsafe_allow_html=True)

                with col_meta:
                    st.markdown(f"<p style='color:#8b95a1; font-size:0.8rem;'><b>{source}</b></p>",
                                unsafe_allow_html=True)
                    if published:
                        try:
                            dt = datetime.fromtimestamp(published) if isinstance(published, (int, float)) else published
                            st.caption(fmt_date(dt, "%d.%m.%Y %H:%M"))
                        except Exception:
                            pass

                st.divider()

# ── TAB 2: Watchlist News ────────────────────
with tab2:
    watchlist = st.session_state.get("watchlist", ["AAPL", "MSFT", "NVDA", "GOOGL"])
    st.caption(f"Aggregierte News für: {', '.join(watchlist)}")

    if st.button("🔄 Watchlist News laden", type="primary"):
        all_news = []
        progress = st.progress(0)

        for i, wl_ticker in enumerate(watchlist):
            progress.progress((i + 1) / len(watchlist), text=f"Lade {wl_ticker}...")
            items = client.get_news(wl_ticker, limit=3)
            for item in items:
                item["_ticker"] = wl_ticker
                all_news.append(item)

        progress.empty()

        # Nach Datum sortieren
        all_news.sort(key=lambda x: x.get("published", 0) or 0, reverse=True)
        st.session_state["watchlist_news"] = all_news

    wl_news = st.session_state.get("watchlist_news", [])
    if wl_news:
        for item in wl_news[:30]:
            wl_ticker = item.get("_ticker", "")
            title     = item.get("title", "")
            url       = item.get("url", "#")
            source    = item.get("source", "")
            published = item.get("published")

            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"**[{title}]({url})**")
            with col2:
                st.markdown(f"`{wl_ticker}` · {source}")
            st.divider()
    else:
        st.info("Klicke auf 'Watchlist News laden' um News für alle Watchlist-Aktien zu sehen.")
