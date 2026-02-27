"""
ui/components/charts.py - Chart-Komponenten

Erstellt interaktive Plotly Charts für:
- Candlestick Charts
- Technische Indikatoren als Overlays
- Volume Bars
- Sub-Charts (RSI, MACD, etc.)
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, Optional
from config import COLORS, CHART_TEMPLATE, CHART_HEIGHT, VOLUME_HEIGHT


def create_main_chart(
    df: pd.DataFrame,
    ticker: str,
    show_indicators: Dict[str, bool]
) -> go.Figure:
    """
    Erstellt Haupt-Chart mit Candlesticks und Indikatoren
    
    Args:
        df: DataFrame mit OHLCV + Indikatoren
        ticker: Ticker-Symbol
        show_indicators: Dict welche Indikatoren angezeigt werden sollen
    
    Returns:
        Plotly Figure
    """
    # Prüfe ob RSI oder MACD angezeigt werden sollen (benötigen Subplots)
    has_rsi = show_indicators.get("rsi", False) and 'rsi' in df.columns
    has_macd = show_indicators.get("macd", False) and 'macd' in df.columns
    
    # Anzahl Rows basierend auf Subplots
    num_rows = 1  # Haupt-Chart
    row_heights = [0.7]  # 70% für Haupt-Chart
    
    if has_rsi:
        num_rows += 1
        row_heights.append(0.15)  # 15% für RSI
    
    if has_macd:
        num_rows += 1
        row_heights.append(0.15)  # 15% für MACD
    
    # Subplot erstellen
    fig = make_subplots(
        rows=num_rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
        subplot_titles=([f"{ticker} Chart"] + 
                       (["RSI"] if has_rsi else []) +
                       (["MACD"] if has_macd else []))
    )
    
    # ═══════════════════════════════════════════
    # ROW 1: CANDLESTICK CHART
    # ═══════════════════════════════════════════
    
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name=ticker,
            increasing_line_color=COLORS['bullish'],
            decreasing_line_color=COLORS['bearish'],
        ),
        row=1, col=1
    )
    
    # ─────────────────────────────────────────────
    # MOVING AVERAGES
    # ─────────────────────────────────────────────
    
    if show_indicators.get("sma_20") and 'sma_20' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['sma_20'],
                mode='lines',
                name='SMA 20',
                line=dict(color=COLORS['sma_fast'], width=1.5),
            ),
            row=1, col=1
        )
    
    if show_indicators.get("sma_50") and 'sma_50' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['sma_50'],
                mode='lines',
                name='SMA 50',
                line=dict(color=COLORS['sma_slow'], width=1.5),
            ),
            row=1, col=1
        )
    
    if show_indicators.get("sma_200") and 'sma_200' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['sma_200'],
                mode='lines',
                name='SMA 200',
                line=dict(color=COLORS['sma_200'], width=2),
            ),
            row=1, col=1
        )
    
    if show_indicators.get("ema_9") and 'ema_9' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['ema_9'],
                mode='lines',
                name='EMA 9',
                line=dict(color=COLORS['ema'], width=1.5, dash='dash'),
            ),
            row=1, col=1
        )
    
    # ─────────────────────────────────────────────
    # BOLLINGER BANDS
    # ─────────────────────────────────────────────
    
    if show_indicators.get("bb") and all(col in df.columns for col in ['bb_upper', 'bb_middle', 'bb_lower']):
        # Upper Band
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['bb_upper'],
                mode='lines',
                name='BB Upper',
                line=dict(color=COLORS['bb_upper'], width=1, dash='dot'),
                showlegend=True,
            ),
            row=1, col=1
        )
        
        # Middle Band
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['bb_middle'],
                mode='lines',
                name='BB Middle',
                line=dict(color=COLORS['bb_upper'], width=1),
                showlegend=False,
            ),
            row=1, col=1
        )
        
        # Lower Band (mit Fill)
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['bb_lower'],
                mode='lines',
                name='BB Lower',
                line=dict(color=COLORS['bb_lower'], width=1, dash='dot'),
                fill='tonexty',
                fillcolor='rgba(120,144,156,0.1)',
                showlegend=True,
            ),
            row=1, col=1
        )
    
    # ─────────────────────────────────────────────
    # VOLUME BARS (am unteren Rand vom Haupt-Chart)
    # ─────────────────────────────────────────────
    
    if 'volume' in df.columns:
        # Farbe basierend auf Preis-Änderung
        volume_colors = [
            COLORS['bullish'] if df['close'].iloc[i] >= df['open'].iloc[i] 
            else COLORS['bearish']
            for i in range(len(df))
        ]
        
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df['volume'],
                name='Volume',
                marker_color=volume_colors,
                opacity=0.3,
                yaxis='y2',
                showlegend=False,
            ),
            row=1, col=1
        )
        
        # Volume MA
        if 'volume_ma' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['volume_ma'],
                    mode='lines',
                    name='Volume MA',
                    line=dict(color=COLORS['volume'], width=1),
                    yaxis='y2',
                    showlegend=False,
                ),
                row=1, col=1
            )
    
    # ═══════════════════════════════════════════
    # ROW 2: RSI (falls aktiviert)
    # ═══════════════════════════════════════════
    
    if has_rsi:
        current_row = 2
        
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['rsi'],
                mode='lines',
                name='RSI',
                line=dict(color=COLORS['rsi'], width=2),
            ),
            row=current_row, col=1
        )
        
        # Overbought / Oversold Linien
        fig.add_hline(
            y=70, line_dash="dash", line_color="rgba(239,83,80,0.5)",
            annotation_text="Overbought (70)",
            row=current_row, col=1
        )
        fig.add_hline(
            y=30, line_dash="dash", line_color="rgba(38,166,154,0.5)",
            annotation_text="Oversold (30)",
            row=current_row, col=1
        )
        
        # Y-Achse Range
        fig.update_yaxes(range=[0, 100], row=current_row, col=1)
    
    # ═══════════════════════════════════════════
    # ROW 3: MACD (falls aktiviert)
    # ═══════════════════════════════════════════
    
    if has_macd:
        current_row = 3 if has_rsi else 2
        
        # MACD Line
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['macd'],
                mode='lines',
                name='MACD',
                line=dict(color=COLORS['macd'], width=2),
            ),
            row=current_row, col=1
        )
        
        # Signal Line
        if 'macd_signal' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=df['macd_signal'],
                    mode='lines',
                    name='Signal',
                    line=dict(color=COLORS['signal'], width=1.5),
                ),
                row=current_row, col=1
            )
        
        # Histogram
        if 'macd_hist' in df.columns:
            hist_colors = [
                COLORS['bullish'] if val >= 0 else COLORS['bearish']
                for val in df['macd_hist']
            ]
            
            fig.add_trace(
                go.Bar(
                    x=df.index, y=df['macd_hist'],
                    name='Histogram',
                    marker_color=hist_colors,
                    opacity=0.5,
                ),
                row=current_row, col=1
            )
        
        # Zero Line
        fig.add_hline(
            y=0, line_dash="dot", line_color="rgba(250,250,250,0.3)",
            row=current_row, col=1
        )
    
    # ═══════════════════════════════════════════
    # LAYOUT
    # ═══════════════════════════════════════════
    
    fig.update_layout(
        template=CHART_TEMPLATE,
        height=CHART_HEIGHT + (VOLUME_HEIGHT * (num_rows - 1)),
        paper_bgcolor=COLORS['background'],
        plot_bgcolor=COLORS['background'],
        xaxis_rangeslider_visible=False,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=50, r=50, t=50, b=50),
    )
    
    # Grid-Styling für alle Subplots
    for i in range(1, num_rows + 1):
        fig.update_xaxes(
            gridcolor=COLORS['grid'],
            showgrid=True,
            row=i, col=1
        )
        fig.update_yaxes(
            gridcolor=COLORS['grid'],
            showgrid=True,
            row=i, col=1
        )
    
    # Volume Overlay (sekundäre Y-Achse)
    if 'volume' in df.columns:
        fig.update_layout(
            yaxis2=dict(
                overlaying='y',
                side='right',
                showgrid=False,
                showticklabels=False,
                range=[0, df['volume'].max() * 4]  # Volume nimmt nur unteren Bereich
            )
        )
    
    return fig


def create_indicator_chart(df: pd.DataFrame, indicator: str, title: str = None) -> go.Figure:
    """
    Erstellt eigenständiges Chart für einen Indikator
    
    Args:
        df: DataFrame mit Indikator-Spalte
        indicator: Name der Spalte (z.B. 'rsi')
        title: Chart-Titel
    
    Returns:
        Plotly Figure
    """
    if indicator not in df.columns:
        # Leeres Chart zurückgeben
        fig = go.Figure()
        fig.add_annotation(
            text=f"Indikator '{indicator}' nicht verfügbar",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
        )
        return fig
    
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df[indicator],
            mode='lines',
            name=indicator.upper(),
            line=dict(color=COLORS.get(indicator, '#42a5f5'), width=2),
        )
    )
    
    fig.update_layout(
        title=title or indicator.upper(),
        template=CHART_TEMPLATE,
        height=300,
        paper_bgcolor=COLORS['background'],
        plot_bgcolor=COLORS['background'],
        xaxis=dict(gridcolor=COLORS['grid']),
        yaxis=dict(gridcolor=COLORS['grid']),
        margin=dict(l=50, r=50, t=50, b=50),
    )
    
    return fig
"""
ui/components/charts.py - Chart-Komponenten (Fixed Layout)
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict
from config import COLORS, CHART_TEMPLATE, CHART_HEIGHT, VOLUME_HEIGHT

def create_main_chart(
    df: pd.DataFrame,
    ticker: str,
    show_indicators: Dict[str, bool]
) -> go.Figure:
    """
    Erstellt Haupt-Chart mit Candlesticks, Volume-Overlay und Subplots (RSI/MACD).
    Behebt den Axis-Clash zwischen Volume und Indikatoren.
    """
    # 1. Welche Subplots brauchen wir?
    has_rsi = show_indicators.get("rsi", False) and 'rsi' in df.columns
    has_macd = show_indicators.get("macd", False) and 'macd' in df.columns
    
    # Layout-Definition
    rows = 1
    row_heights = [0.7] # Start mit 70% für Price/Vol
    specs = [[{"secondary_y": True}]] # Zeile 1 hat zwei Y-Achsen (Preis links, Vol rechts)
    
    if has_rsi:
        rows += 1
        row_heights.append(0.15)
        specs.append([{"secondary_y": False}])
        
    if has_macd:
        rows += 1
        row_heights.append(0.15)
        specs.append([{"secondary_y": False}])

    # Normalisierung der row_heights, damit Summe = 1.0 (Wichtig für Plotly)
    total_height = sum(row_heights)
    row_heights = [h/total_height for h in row_heights]

    # Chart erstellen
    fig = make_subplots(
        rows=rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=row_heights,
        specs=specs,
        subplot_titles=[f"{ticker} Chart"] + (["RSI"] if has_rsi else []) + (["MACD"] if has_macd else [])
    )

    # ─────────────────────────────────────────────
    # ROW 1: CANDLESTICK & VOLUME
    # ─────────────────────────────────────────────
    
    # Candlestick (Linke Achse)
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['open'], high=df['high'], low=df['low'], close=df['close'],
            name=ticker,
            increasing_line_color=COLORS['bullish'],
            decreasing_line_color=COLORS['bearish'],
            showlegend=False
        ),
        row=1, col=1, secondary_y=False
    )
    
    # Volume (Rechte Achse - Overlay)
    if 'volume' in df.columns:
        colors = [COLORS['bullish'] if c >= o else COLORS['bearish'] 
                  for c, o in zip(df['close'], df['open'])]
        
        fig.add_trace(
            go.Bar(
                x=df.index, y=df['volume'],
                name='Volume',
                marker_color=colors,
                opacity=0.3,
                showlegend=False
            ),
            row=1, col=1, secondary_y=True
        )
        
        # Volume MA
        if show_indicators.get("volume", False) and 'volume_ma' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=df['volume_ma'],
                    mode='lines', name='Vol MA',
                    line=dict(color=COLORS['volume'], width=1),
                    showlegend=False
                ),
                row=1, col=1, secondary_y=True
            )

    # Indikatoren im Hauptchart (SMA, EMA, BB)
    if show_indicators.get("sma_20") and 'sma_20' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['sma_20'], mode='lines', name='SMA 20', line=dict(color=COLORS['sma_fast'], width=1)), row=1, col=1, secondary_y=False)
    
    if show_indicators.get("sma_50") and 'sma_50' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['sma_50'], mode='lines', name='SMA 50', line=dict(color=COLORS['sma_slow'], width=1)), row=1, col=1, secondary_y=False)
        
    if show_indicators.get("bb") and 'bb_upper' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['bb_upper'], mode='lines', line=dict(color=COLORS['bb_upper'], width=1, dash='dot'), showlegend=False), row=1, col=1, secondary_y=False)
        fig.add_trace(go.Scatter(x=df.index, y=df['bb_lower'], mode='lines', line=dict(color=COLORS['bb_lower'], width=1, dash='dot'), fill='tonexty', fillcolor='rgba(120,144,156,0.1)', name='Bollinger', showlegend=True), row=1, col=1, secondary_y=False)

    # ─────────────────────────────────────────────
    # ROW 2 & 3: RSI / MACD
    # ─────────────────────────────────────────────
    current_row = 2
    
    if has_rsi:
        fig.add_trace(go.Scatter(x=df.index, y=df['rsi'], mode='lines', name='RSI', line=dict(color=COLORS['rsi'])), row=current_row, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=current_row, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=current_row, col=1)
        fig.update_yaxes(range=[0, 100], row=current_row, col=1)
        current_row += 1
        
    if has_macd:
        fig.add_trace(go.Scatter(x=df.index, y=df['macd'], mode='lines', name='MACD', line=dict(color=COLORS['macd'])), row=current_row, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['macd_signal'], mode='lines', name='Signal', line=dict(color=COLORS['signal'])), row=current_row, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df['macd_hist'], name='Hist', marker_color=[COLORS['bullish'] if v>=0 else COLORS['bearish'] for v in df['macd_hist']]), row=current_row, col=1)

    # ─────────────────────────────────────────────
    # STYLING
    # ─────────────────────────────────────────────
    fig.update_layout(
        template=CHART_TEMPLATE,
        height=CHART_HEIGHT + (150 * (rows - 1)),
        margin=dict(l=10, r=10, t=30, b=10),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_rangeslider_visible=False
    )
    
    # Volume Skalierung (damit Balken unten bleiben)
    if 'volume' in df.columns:
        max_vol = df['volume'].max()
        fig.update_yaxes(range=[0, max_vol * 4], showticklabels=False, row=1, col=1, secondary_y=True)

    return fig

def create_indicator_chart(df, indicator, title=None):
    """Fallback Funktion"""
    return go.Figure()