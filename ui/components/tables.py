"""
ui/components/tables.py - Tabellen & Visualisierung
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

def financial_statement_table(df: pd.DataFrame, title: str):
    """
    Rendert eine Finanz-Tabelle UND einen interaktiven Chart für die ausgewählte Metrik.
    """
    if df is None or df.empty:
        st.caption(f"Keine Daten für {title}.")
        return

    # Container für sauberen Look
    with st.container():
        st.subheader(title)

        # 1. VISUALISIERUNG
        # Wir holen uns die Zeilennamen (Index) als Auswahlmöglichkeiten
        metrics = df.index.tolist()
        
        # Wenn Daten da sind, zeigen wir Selector und Chart
        if metrics:
            col_sel, col_chart = st.columns([1, 3])
            
            with col_sel:
                # Selectbox erlaubt das "Auswählen" einer Zeile
                selected_metric = st.selectbox(
                    "Metrik analysieren:", 
                    options=metrics, 
                    index=0, # Erstes Element standardmäßig
                    key=f"sel_{title}_{len(df)}" # Unique Key
                )
                st.caption("Wähle eine Kennzahl, um den Verlauf im Chart zu sehen.")

            with col_chart:
                # Daten für die gewählte Zeile holen
                if selected_metric in df.index:
                    row_data = df.loc[selected_metric]
                    
                    # Sicherstellen, dass es Zahlen sind (manchmal sind es Objekte)
                    try:
                        row_data = pd.to_numeric(row_data, errors='coerce').fillna(0)
                    except:
                        pass

                    # Farben: Grün für Positiv, Rot für Negativ
                    colors = ['#00C805' if v >= 0 else '#FF3B30' for v in row_data.values]

                    fig = go.Figure(data=[
                        go.Bar(
                            x=row_data.index, # Die Jahre (Spalten)
                            y=row_data.values,
                            marker_color=colors,
                            text=row_data.values,
                            texttemplate='%{y:.2s}', # Smart Format (1.5B, 20M...)
                            textposition='auto',
                            name=selected_metric
                        )
                    ])

                    fig.update_layout(
                        title=dict(text=f"Verlauf: {selected_metric}", font=dict(size=14, color="#d1d4dc")),
                        height=250, # Kompakt halten
                        template="plotly_dark",
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=0, r=0, t=30, b=0),
                        yaxis=dict(gridcolor="#333", showgrid=True),
                        xaxis=dict(gridcolor="#333", showgrid=False)
                    )
                    st.plotly_chart(fig, use_container_width=True)

        # 2. DIE TABELLE (Expandable, damit sie nicht zu viel Platz wegnimmt)
        with st.expander(f"Details: {title}", expanded=True):
            # Wir formatieren große Zahlen für bessere Lesbarkeit, falls möglich
            st.dataframe(
                df,
                use_container_width=True,
                height=400
            )