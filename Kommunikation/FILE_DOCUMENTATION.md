# 📚 FILE_DOCUMENTATION.md - OpenBB Terminal Pro

**Aktualisiert:** 26. Februar 2026 – nach Phase 3
**Nutzen:** Datei unbekannt? → Hier nachschlagen.

---

## Status-Legende
| Symbol | Bedeutung |
|--------|-----------|
| ✅ | Fertig & funktioniert |
| ⏳ | Noch nicht implementiert |
| 🔄 | In Arbeit |

---

## 📄 Root-Dateien

### `app.py` ✅
**Start:** `streamlit run app.py` (aus `A:\OpenBB\` heraus!)
**Wichtig:** Kein `st.page_link()` – Streamlit zeigt Pages in `pages\` automatisch in der Sidebar.
**Dependencies:** `config.py`, `data/openbb_client.py`

### `config.py` ✅
Alle Settings zentral. **Wichtige Ergänzungen (Phase 3):**
`MARKET_INDICES`, `SECTOR_ETFS`, `FOREX_PAIRS`, `COMMODITIES`, `RISK_FREE_RATE`, `TRADING_DAYS_PER_YEAR`

---

## 📂 data/

### `data/openbb_client.py` ✅
**Singleton via `get_client()`**

| Methode | Returns | Cache TTL |
|---------|---------|-----------|
| `get_price_history(ticker, period, interval)` | DataFrame OHLCV | 5 Min |
| `get_quote(ticker)` | dict | 1 Min |
| `get_company_info(ticker)` | dict | 1 Std |
| `get_financials(ticker, type)` | DataFrame | 1 Std |
| `get_news(ticker, limit)` | list[dict] | 10 Min |
| `clear_cache()` | – | – |

### `data/cache_manager.py` ✅ NEU Phase 3
**Persistentes Disk-Caching** – überlebt Streamlit-Neustarts.

```python
from data.cache_manager import get_cache, cached, TTL

# Direkte Nutzung:
cache = get_cache()
cache.set("key", data, ttl=300)
data = cache.get("key")
cache.clear()
stats = cache.stats()  # {"type":"disk","entries":42,"size_mb":2.3}

# Als Decorator:
@cached(ttl=TTL["fundamentals"], prefix="market")
def get_expensive_data(ticker: str) -> dict:
    ...
```

**TTL-Konstanten:**
```python
TTL = {
    "quote": 60, "price_history": 300, "fundamentals": 3600,
    "news": 900, "screener": 600, "macro": 3600, "company_info": 86400
}
```

**Fallback:** Wenn `diskcache` fehlt → automatisch InMemoryCache.

---

## 📂 indicators/

### `indicators/technical.py` ✅
**Fluent Interface:** `TechnicalIndicators(df).add_sma([20,50]).add_rsi().add_macd().df`

| Methode | Neue Spalten |
|---------|-------------|
| `add_sma([20,50,200])` | `sma_20`, `sma_50`, `sma_200` |
| `add_ema([9,21])` | `ema_9`, `ema_21` |
| `add_rsi(14)` | `rsi` (0–100) |
| `add_macd(12,26,9)` | `macd`, `macd_signal`, `macd_hist` |
| `add_bollinger_bands(20,2)` | `bb_upper`, `bb_middle`, `bb_lower` |
| `add_atr(14)` | `atr` |
| `add_obv()` | `obv` |
| `add_volume_ma(20)` | `volume_ma` |
| `add_vwap()` | `vwap` |

**Wichtig:** pandas-ta ist optional. Alle Indikatoren haben numpy/pandas Fallbacks.

---

## 📂 services/

### `services/market_service.py` ✅
**Singleton via `get_market_service()`**

| Methode | Returns |
|---------|---------|
| `get_stock_overview(ticker)` | dict mit fmt_price, fmt_pe, fmt_market_cap, ... |
| `get_key_metrics(ticker)` | list[dict] für kpi_row() |
| `get_financial_statements(ticker)` | {"income": df, "balance": df, "cashflow": df} |
| `get_growth_metrics(ticker)` | list[dict] |
| `get_analyst_info(ticker)` | dict mit recommendation, target_mean, fmt_upside |

### `services/screener_service.py` ✅
**Singleton via `get_screener_service()`**

Score 0–100: Bewertung (30) + Wachstum (25) + Profitabilität (25) + Momentum (20)

```python
svc = get_screener_service()
df  = svc.run_screen(UNIVERSES["mega_cap_us"], filters={"pe_max": 30, "rsi_min": 40})
display = svc.get_display_df(df)
```

### `services/portfolio_service.py` ✅ NEU Phase 3
**Singleton via `get_portfolio_service()`**

```python
svc = get_portfolio_service()
analytics = svc.get_full_analytics(positions)
# analytics enthält:
# - metrics:      {sharpe_ratio, max_drawdown, var_95, volatility, total_return, ...}
# - benchmark:    {port_return, bench_return, alpha, beta, correlation}
# - correlation:  pd.DataFrame (Korrelations-Matrix)
# - sector_alloc: list[{sector, value, weight}]
# - cum_returns:  pd.Series (kumulierte Returns Portfolio)
# - cum_benchmark:pd.Series (kumulierte Returns S&P 500)
# - daily_returns:pd.Series (tägliche Returns)
```

**Kennzahlen-Formeln:**
- **Sharpe Ratio:** `(ann_return - risk_free_rate) / volatility`
- **Max Drawdown:** `min((cumulative - rolling_max) / rolling_max)`
- **VaR 95%:** `np.percentile(daily_returns, 5)`
- **Beta:** `cov(portfolio, sp500) / var(sp500)`
- **Alpha:** `portfolio_return - benchmark_return`

---

## 📂 ui/components/

### `ui/components/charts.py` ✅
`create_main_chart(df, ticker, show_indicators)` → Plotly Figure

### `ui/components/metrics.py` ✅
`price_header(ticker, overview)`, `kpi_row(metrics_list)`, `format_large_number()`

### `ui/components/sidebar.py` ✅
`render_ticker_input()` → str, `render_timeframe_selector()` → (interval, period), `render_indicator_settings()` → dict

### `ui/components/tables.py` ✅
`styled_dataframe()`, `financial_statement_table()`, `screener_result_table()`, `news_table()`, `plotly_bar_chart()`

---

## 📂 pages/ (Streamlit Pages)

### `pages/1_charts.py` ✅
Candlestick + alle Indikatoren. Sidebar: Ticker, Timeframe, Indikatoren on/off.

### `pages/2_fundamentals.py` ✅
5 Tabs: Übersicht · GuV/Bilanz/Cashflow · 12 Kennzahlen · Analysten · News

### `pages/3_screener.py` ✅
4 Universen + eigene Liste. Filter-Slider. Score-Tabelle. CSV Export.

### `pages/4_news.py` ✅
Ticker News + Watchlist-aggregierter Feed.

### `pages/5_portfolio.py` ✅ Phase 3 erweitert
**4 Tabs:**
- Übersicht: Pie Chart, P&L Balken, Positions-Tabelle
- Performance: Kumulierter Chart vs. S&P 500, Alpha/Beta
- Risiko: Sharpe, Max Drawdown, VaR, Volatilität, Drawdown-Chart
- Korrelation & Sektoren: Heatmap + Sektor-Pie

Analytics werden per Button gestartet und in `st.session_state["analytics_cache"]` gecacht.

### `pages/6_macro.py` ✅ NEU Phase 3
**4 Tabs:**
- Zinsen: US Yield Curve (3M→30Y) + Invertierungs-Warnung + 10Y Verlauf
- Sektoren: Performance-Balken (XLK, XLV, ...) mit Zeitraum-Auswahl
- Währungen & Rohstoffe: 6 Forex-Paare + 6 Rohstoffe + Gold-Chart
- Angst: VIX-Gauge (5 Zonen) + Risk-On/Off + VIX Verlauf

**Datenquellen (alle via yfinance, kein API Key):**
```
Treasuries: ^IRX, ^FVX, ^TNX, ^TYX
Sektoren:   XLK, XLV, XLF, XLY, XLP, XLE, XLI, XLB, XLRE, XLU, XLC
Forex:      EURUSD=X, GBPUSD=X, USDJPY=X, USDCHF=X, AUDUSD=X
Rohstoffe:  GC=F, SI=F, CL=F, BZ=F, NG=F, HG=F
VIX:        ^VIX
```

### `pages/7_ai_analyst.py` ⏳ Phase 3
KI-gestützte Aktienanalyse mit Claude API.

---

## 📂 utils/

### `utils/formatters.py` ✅
`fmt_large()`, `fmt_pct()`, `fmt_price()`, `fmt_ratio()`, `fmt_volume()`, `fmt_date()`, `color_pct()`, `trend_arrow()`

---

## 🗝️ Konfigurationsdateien

### `.streamlit/config.toml` ✅
Dark Theme: `primaryColor = "#26a69a"`, `backgroundColor = "#0e1117"`

### `.streamlit/secrets.toml` ⚠️ LOKAL ERSTELLEN (NICHT committen!)
```toml
OPENBB_PAT        = "pat_..."   # optional
ANTHROPIC_API_KEY = "sk-ant-..." # für AI-Analyst (Phase 3)
```

---

## 💡 Wichtige Architektur-Hinweise

**Page-Pfade:** Streamlit 1.54+ erkennt `pages\` automatisch. Kein `st.page_link()` nötig.

**sys.path Fix:** Jede Page beginnt mit:
```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```
Damit werden `config`, `data`, `services` etc. gefunden.

**Analytics-Caching:** Portfolio Analytics dauert ~20s → `st.session_state["analytics_cache"]` verhindert Neuberechnung.

**pandas-ta:** Optional. Alle Indikatoren haben manuelle Fallbacks via numpy/pandas.

---

**Letzte Aktualisierung:** 26. Februar 2026 – Phase 3 (75%) abgeschlossen
