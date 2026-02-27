"""
ui/components/charts.py - Polished Chart Design
"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict

def create_main_chart(df: pd.DataFrame, ticker: str, show_indicators: dict) -> go.Figure:
    # Subplots Setup
    has_rsi = show_indicators.get("rsi", False) and 'rsi' in df.columns
    has_macd = show_indicators.get("macd", False) and 'macd' in df.columns
    
    rows = 1
    row_heights = [0.6] 
    specs = [[{"secondary_y": True}]]
    
    if has_rsi:
        rows += 1
        row_heights.append(0.2)
        specs.append([{"secondary_y": False}])
    if has_macd:
        rows += 1
        row_heights.append(0.2)
        specs.append([{"secondary_y": False}])

    total = sum(row_heights)
    row_heights = [h/total for h in row_heights]

    fig = make_subplots(
        rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.03,
        row_heights=row_heights, specs=specs
    )

    # 1. Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'],
        name=ticker, increasing_line_color='#00C805', decreasing_line_color='#FF3B30',
        showlegend=False
    ), row=1, col=1)

    # 2. Volume
    if 'volume' in df.columns:
        colors = ['rgba(0, 200, 5, 0.3)' if c >= o else 'rgba(255, 59, 48, 0.3)' 
                  for c, o in zip(df['close'], df['open'])]
        fig.add_trace(go.Bar(
            x=df.index, y=df['volume'], marker_color=colors, showlegend=False, name="Volume"
        ), row=1, col=1, secondary_y=True)

    # Indikatoren
    for ind, color in [('sma_20', '#2962FF'), ('sma_50', '#FF6D00'), ('sma_200', '#E040FB')]:
        if show_indicators.get(ind) and ind in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df[ind], mode='lines', line=dict(width=1.5, color=color), name=ind.upper().replace('_', ' ')), row=1, col=1)

    if show_indicators.get("bb") and 'bb_upper' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['bb_upper'], line=dict(width=1, color='gray', dash='dot'), showlegend=False), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['bb_lower'], line=dict(width=1, color='gray', dash='dot'), fill='tonexty', fillcolor='rgba(128,128,128,0.1)', name="Bollinger", showlegend=True), row=1, col=1)

    curr_row = 2
    if has_rsi:
        fig.add_trace(go.Scatter(x=df.index, y=df['rsi'], line=dict(color='#E040FB', width=2), name="RSI"), row=curr_row, col=1)
        fig.add_hline(y=70, line_dash="dot", row=curr_row, col=1, line_color="gray"); fig.add_hline(y=30, line_dash="dot", row=curr_row, col=1, line_color="gray")
        curr_row += 1

    if has_macd:
        fig.add_trace(go.Bar(x=df.index, y=df['macd_hist'], marker_color=['#00C805' if v>0 else '#FF3B30' for v in df['macd_hist']], name="Hist"), row=curr_row, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['macd'], line=dict(color='#2962FF'), name="MACD"), row=curr_row, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['macd_signal'], line=dict(color='#FF6D00'), name="Signal"), row=curr_row, col=1)

    fig.update_layout(
        template="plotly_dark", 
        height=800 if rows > 1 else 600,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", y=1, x=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    # ---------------------------------------------------------
    # DYNAMISCHE LÜCKEN-ERKENNUNG (SMART RANGEBREAKS)
    # ---------------------------------------------------------
    rangebreaks = []
    if not df.empty and len(df) > 1:
        # Wochenenden immer ausblenden (außer Krypto)
        has_weekend_data = df.index.dayofweek.isin([5, 6]).any()
        if not has_weekend_data:
            rangebreaks.append(dict(bounds=["sat", "mon"]))

        # Intraday-Prüfung
        time_diff = df.index[1] - df.index[0]
        is_intraday = time_diff < pd.Timedelta(days=1)

        # Wenn Intraday UND kein Krypto -> Nacht ausblenden
        if is_intraday and not has_weekend_data:
            # Wir ermitteln die Handelszeiten direkt aus den Daten!
            # z.B. Max Stunde = 15 (15:30 close) -> Hide ab 16
            # z.B. Min Stunde = 9 (09:30 open) -> Hide bis 9
            
            last_trade_hour = df.index.hour.max()
            first_trade_hour = df.index.hour.min()
            
            # Puffer: Wir blenden ab der nächsten vollen Stunde nach Handelsschluss aus
            # bis zur Stunde des Handelsbeginns.
            # Beispiel US: Max=15 (Ende 16:00), Min=9. Break: [16, 9] (bedeutet 16:00 bis 09:00)
            
            # Sicherheitscheck: Nur wenn logische Werte
            if last_trade_hour >= first_trade_hour:
                break_start = last_trade_hour + 1 # Stunde nach letzter Kerze
                break_end = first_trade_hour      # Stunde vor erster Kerze
                
                # Wenn wir z.B. 16 Uhr Schluss haben und 9 Uhr Open, breaken wir [17, 9]? 
                # Nein, Plotly pattern="hour" nimmt Start und Ende.
                # US (16:00 Close) -> Daten bis 15:59. Max hour ist 15.
                # Wir wollen ab 16:00 (16) ausblenden.
                # US (09:30 Open) -> Daten ab 09:30. Min hour ist 9.
                # Wir wollen bis 09:30 ausblenden. Plotly Bounds sind float.
                # Versuchen wir den Standard [16, 9.5] wenn es nach US aussieht, sonst dynamisch.
                
                # DYNAMISCH:
                rangebreaks.append(dict(
                    bounds=[break_start, break_end], 
                    pattern="hour"
                ))

    if rangebreaks:
        fig.update_xaxes(rangebreaks=rangebreaks)
    
    if 'volume' in df.columns:
         fig.update_yaxes(range=[0, df['volume'].max() * 4], showticklabels=False, secondary_y=True, row=1, col=1)

    return fig