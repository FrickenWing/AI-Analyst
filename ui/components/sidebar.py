"""
ui/components/sidebar.py - Navigation & Suche
"""
import streamlit as st

def render_search_sidebar(client):
    """
    Rendert die Suchleiste.
    Gibt NICHTS mehr zurück, da die Chart-Steuerung jetzt im Terminal liegt.
    """
    st.sidebar.title("💻 Terminal")
    
    # 1. Aktueller Status
    current_ticker = st.session_state.get("ticker", "AAPL")
    
    st.sidebar.caption("Aktuell ausgewählt:")
    col1, col2 = st.sidebar.columns([3, 1])
    col1.markdown(f"## **{current_ticker}**")
    
    if col2.button("🔄", help="Aktualisieren"):
        st.rerun()

    st.sidebar.markdown("---")

    # 2. Die Suche
    st.sidebar.subheader("🔍 Suche")
    
    search_query = st.sidebar.text_input(
        "Firma oder Ticker:", 
        placeholder="Apple, TSLA...",
        label_visibility="collapsed",
        key="sidebar_search"
    )

    if search_query:
        with st.sidebar.status("Suche läuft...", expanded=True) as status:
            results = client.search_ticker(search_query)
            
            if not results:
                status.update(label="Keine Ergebnisse", state="error")
                st.sidebar.warning("Nichts gefunden.")
            else:
                status.update(label="Treffer!", state="complete")
                
                options_map = {
                    f"{r['ticker']} | {r['name']} ({r.get('exchange', 'N/A')})": r['ticker'] 
                    for r in results
                }
                
                selection = st.sidebar.selectbox(
                    "Ergebnisse:",
                    options=list(options_map.keys()),
                    index=None,
                    placeholder="Wählen..."
                )
                
                if selection:
                    new_ticker = options_map[selection]
                    if new_ticker != current_ticker:
                        st.session_state.ticker = new_ticker
                        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.info(
        "💡 **Tipp:**\n"
        "Steuere den Chart-Zeitraum jetzt direkt im Terminal über dem Graphen."
    )
    
    # Keine Rückgabewerte mehr nötig
    return