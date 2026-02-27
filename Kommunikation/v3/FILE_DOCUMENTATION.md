# 📚 FILE_DOCUMENTATION.md - OpenBB Terminal Pro

**Aktualisiert:** 25. Februar 2026 – nach Phase 2  
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
**Start:** `streamlit run app.py`  
**Zweck:** Entry-Point. Zeigt Market Overview Dashboard + Navigation zu allen 5 Seiten.  
**Navigation enthält:** Charts, Fundamentals, Screener, News, Portfolio  
**Dependencies:** `config.py`, `data/openbb_client.py`

---

### `config.py` ✅
**Zweck:** Alle Settings zentral. Wird von jedem Modul importiert.

| Konstante | Inhalt |
|-----------|--------|
| `OPENBB_PAT`, `FMP_API_KEY` | API Keys aus Secrets/Env |
| `TIMEFRAMES` | Dict: Intervall → Label, Period |
| `INDICATOR_DEFAULTS` | Standard-Werte SMA/RSI/MACD/BB |
| `COLORS` | Farb-Schema (Dark Theme) |
| `CACHE_TTL` | Cache-Dauer je Datentyp |
| `DEFAULT_WATCHLIST` | Start-Watchlist |
| `FEATURES` | Feature-Flags |

```python
from config import COLORS, TIMEFRAMES, DEFAULT_TICKER
```

---

## 📂 core/

### `core/models.py` ✅
Pydantic-Datenmodelle für Type Safety und Validierung.

| Model | Felder | Properties |
|-------|--------|-----------|
| `StockQuote` | ticker, price, change, change_pct, volume | `is_positive` |
| `CompanyProfile` | ticker, name, sector, industry, country | – |
| `IncomeStatement` | revenue, net_income, eps, ebitda | `gross_margin`, `net_margin` |
| `KeyMetrics` | pe, pb, ps, ev_ebitda, roe, roa, ... | – |
| `ScreenerFilter` | pe_min/max, roe_min, rsi_min/max, ... | – |
| `Position` | ticker, quantity, avg_price | `market_value`, `pnl`, `pnl_pct` |
| `Portfolio` | positions, cash | `total_value`, `total_pnl` |
| `NewsItem` | title, url, source, published, sentiment | – |

### `core/constants.py` ✅
Enums: `Timeframe`, `Period`, `AssetClass`, `DataProvider`, `Sector`, `SignalType`  
Konstanten: `SECTOR_ETFS`, `MARKET_INDICES`, `SIGNAL_COLORS`

### `core/exceptions.py` ✅
`DataFetchError(ticker)`, `InvalidTickerError(ticker)`, `ProviderError(providers)`, `InsufficientDataError(required, available)`

---

## 📂 data/

### `data/openbb_client.py` ✅
**Singleton via `get_client()`** – nutze immer diesen Zugang.

| Methode | Returns | Cache |
|---------|---------|-------|
| `get_price_history(ticker, period, interval)` | `pd.DataFrame` (OHLCV) | 5 Min |
| `get_quote(ticker)` | `dict` | 1 Min |
| `get_company_info(ticker)` | `dict` | 1 Std |
| `get_financials(ticker, "income"/"balance"/"cashflow")` | `pd.DataFrame` | 1 Std |
| `get_news(ticker, limit)` | `list[dict]` | 10 Min |
| `get_market_overview()` | `dict` | 2 Min |
| `clear_cache()` | – | – |

```python
from data.openbb_client import get_client
client = get_client()
df = client.get_price_history("AAPL", "1y", "1d")
```

**Fallback-Kette:** OpenBB Platform PAT → yfinance direkt

**Testen:** `python data/openbb_client.py`

---

## 📂 indicators/

### `indicators/technical.py` ✅
**Fluent Interface** – Methoden geben `self` zurück, können gekettet werden.

```python
from indicators.technical import TechnicalIndicators
df = TechnicalIndicators(df).add_sma([20,50]).add_rsi().add_macd().df
```

| Methode | Neue Spalten |
|---------|-------------|
| `add_sma([20,50,200])` | `sma_20`, `sma_50`, `sma_200` |
| `add_ema([9,21])` | `ema_9`, `ema_21` |
| `add_vwap()` | `vwap` |
| `add_rsi(14)` | `rsi` (0–100) |
| `add_macd(12,26,9)` | `macd`, `macd_signal`, `macd_hist` |
| `add_bollinger_bands(20,2)` | `bb_upper`, `bb_middle`, `bb_lower` |
| `add_atr(14)` | `atr` |
| `add_obv()` | `obv` |
| `add_volume_ma(20)` | `volume_ma` |
| `add_all()` | Alle oben |

---

## 📂 services/

### `services/market_service.py` ✅
**Singleton via `get_market_service()`**  
Service-Layer zwischen Pages und Client.

| Methode | Returns |
|---------|---------|
| `get_stock_overview(ticker)` | dict mit Kurs, Sektor, formatierte Werte |
| `get_key_metrics(ticker)` | list[dict] → direkt für `kpi_row()` |
| `get_financial_statements(ticker)` | dict mit "income", "balance", "cashflow" DataFrames |
| `get_income_summary(ticker)` | Vereinfachtes GuV DataFrame |
| `get_growth_metrics(ticker)` | list[dict] mit Wachstumsraten |
| `get_analyst_info(ticker)` | dict mit Consensus, Kursziel, Upside |
| `get_market_summary()` | list[dict] für Dashboard-Header |

```python
from services.market_service import get_market_service
svc = get_market_service()
overview = svc.get_stock_overview("AAPL")
```

---

### `services/screener_service.py` ✅
**Singleton via `get_screener_service()`**

| Methode | Beschreibung |
|---------|-------------|
| `run_screen(tickers, filters, sort_by)` | Komplett-Screening → `pd.DataFrame` |
| `_fetch_ticker_data(ticker)` | Fundamentale + RSI + SMA200 für einen Ticker |
| `_calculate_scores(df)` | Composite Score 0–100 je Zeile |
| `_apply_filters(df, filters)` | Multi-Kriterien Filter |
| `get_display_df(df)` | Formatiertes DataFrame für st.dataframe() |

**Vordefinierte Universen:**
```python
UNIVERSES = {
    "mega_cap_us": ["AAPL", "MSFT", "NVDA", ...],
    "tech_growth":  ["NVDA", "AMD", "CRWD", ...],
    "dividends":    ["JNJ", "PG", "KO", ...],
    "dax_top10":    ["SAP", "SIE", "ALV", ...],
}
```

**Score-Zusammensetzung:**
- Bewertung (P/E, P/B, EV/EBITDA): 30 Punkte
- Wachstum (Revenue, EPS): 25 Punkte
- Profitabilität (ROE, Net Margin): 25 Punkte
- Momentum (RSI): 20 Punkte

---

## 📂 ui/components/

### `ui/components/charts.py` ✅
`create_main_chart(df, ticker, show_indicators)` – Hauptfunktion für Chart-Seite.

`show_indicators` dict: `{"sma_20": True, "rsi": True, "macd": False, "bb": False}`

Sub-Charts: Volumen (immer), RSI (wenn aktiviert), MACD (wenn aktiviert)

### `ui/components/metrics.py` ✅

| Funktion | Verwendung |
|----------|-----------|
| `price_header(ticker, quote)` | Großer Kurs-Header oben auf der Seite |
| `kpi_row(metrics_list)` | Mehrere st.metric() nebeneinander |
| `format_large_number(value)` | `$1.23B`, `$456.7M` |
| `format_pct(value)` | `+5.32%` |
| `format_ratio(value)` | `25.30x` |
| `signal_badge("strong_buy")` | HTML-Badge grün/rot |

### `ui/components/sidebar.py` ✅
`render_ticker_input()`, `render_timeframe_selector()`, `render_indicator_settings()`,  
`render_watchlist()`, `render_cache_controls()`

### `ui/components/tables.py` ✅

| Funktion | Verwendung |
|----------|-----------|
| `styled_dataframe(df, color_columns)` | DataFrame mit Grün/Rot-Highlighting |
| `financial_statement_table(df, title)` | GuV/Bilanz/Cashflow formatiert |
| `screener_result_table(df)` | Mit Score-Fortschrittsbalken |
| `news_table(news)` | Klickbare News-Liste |
| `plotly_bar_chart(cats, vals, title)` | Jahresvergleich Balken |

---

## 📂 ui/pages/

### `ui/pages/1_📈_charts.py` ✅
Candlestick + Indikatoren + RSI + MACD. Sidebar: Ticker, Timeframe, Indikatoren.

### `ui/pages/2_📊_fundamentals.py` ✅
5 Tabs: **Übersicht** (Profil, KPIs, Wachstum) | **Financials** (GuV, Bilanz, Cashflow mit Charts) | **Kennzahlen** (12 Metriken + Erklärung) | **Analysten** (Consensus, Kursziel) | **News**

### `ui/pages/3_🔍_screener.py` ✅
Sidebar: Universum-Auswahl + Filter-Slider. Haupt: Fortschrittsbalken, 3 Ansichts-Tabs, CSV Export.

### `ui/pages/4_📰_news.py` ✅
Tab 1: Ticker-News. Tab 2: Aggregierte Watchlist-News.

### `ui/pages/5_💼_portfolio.py` ✅
Positionen eingeben/löschen. KPI-Summary. Pie Chart + P&L Balken. Positions-Tabelle. CSV Export.

### `ui/pages/6_🌍_macro.py` ⏳ – Phase 3
Makro-Dashboard: Yield Curve, Zinsen, Sektoren, Währungen, Rohstoffe.

### `ui/pages/7_🤖_ai_analyst.py` ⏳ – Phase 3
KI-gestützte Aktien-Analyse.

---

## 📂 utils/

### `utils/formatters.py` ✅

| Funktion | Beispiel |
|----------|---------|
| `fmt_large(1_234_567_890)` | `"$1.23B"` |
| `fmt_pct(0.0532)` | `"+5.32%"` |
| `fmt_price(185.5)` | `"$185.50"` |
| `fmt_ratio(25.3)` | `"25.30x"` |
| `fmt_volume(50_000_000)` | `"50.0M"` |
| `fmt_date(timestamp)` | `"25.02.2026"` |
| `color_pct(value)` | `"#26a69a"` oder `"#ef5350"` |
| `trend_arrow(value)` | `"▲"` oder `"▼"` |

---

## 📂 tests/

### `tests/test_openbb_client.py` ✅
**12 Tests** in 4 Klassen: `TestPriceHistory`, `TestQuote`, `TestCaching`, `TestIndicators`

```bash
pytest tests/test_openbb_client.py -v
```

---

## 🗝️ Konfigurationsdateien

### `.streamlit/config.toml` ✅
Dark Theme. Primary Color `#26a69a`. Background `#0e1117`.

### `.streamlit/secrets.toml` ⚠️ LOKAL ERSTELLEN
```toml
OPENBB_PAT = "pat_..."    # my.openbb.co
FMP_API_KEY = "..."       # optional
```
**NIEMALS committen!** Bereits in `.gitignore`.

---

## 💡 Architektur-Entscheidungen

**Warum Services?**  
Pages sind schlank – nur UI-Logik. Business-Logik ist in Services testbar und wiederverwendbar.

**Warum Singleton-Pattern?**  
`get_client()`, `get_market_service()`, `get_screener_service()` – verhindert mehrfache Initialisierung, Caches bleiben erhalten.

**Warum Fluent Interface bei TechnicalIndicators?**  
`ti.add_rsi().add_macd().add_bb().df` ist lesbarer als 3 separate Aufrufe.

---

**Letzte Aktualisierung:** 25. Februar 2026 – Phase 2 abgeschlossen  
**Alle Phase-1 und Phase-2-Module:** ✅ Dokumentiert und implementiert
