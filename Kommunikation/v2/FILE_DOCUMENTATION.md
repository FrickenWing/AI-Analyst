# 📚 FILE_DOCUMENTATION.md - OpenBB Terminal Pro

**Zweck:** Jede Datei des Projekts detailliert erklärt  
**Aktualisiert:** 25. Februar 2026 - nach Foundation-Phase  
**Nutzen:** Wenn du nicht weißt was eine Datei macht → hier nachschlagen

---

## 🗂️ Übersicht

| Status | Bedeutung |
|--------|-----------|
| ✅     | Fertig & funktioniert |
| ⏳     | Noch nicht implementiert (Stub) |
| 🔄     | In Arbeit |

---

## 📄 Root-Dateien

### `app.py` ✅
**Zweck:** Entry-Point der gesamten Anwendung  
**Starten mit:** `streamlit run app.py`

**Was es tut:**
- Streamlit Multi-Page App Setup (Page Config, Custom CSS)
- Globale Sidebar mit Navigation
- Market Overview Dashboard:
  - 5 Markt-Indizes live (S&P 500, NASDAQ, Dow, VIX, DAX)
  - Watchlist mit Live-Preisen
  - Projekt-Fortschritts-Anzeige

**Dependencies:** `config.py`, `data/openbb_client.py`, `config.COLORS`

**Wichtig:** `set_page_config()` muss als ERSTER Streamlit-Aufruf stehen!

---

### `config.py` ✅
**Zweck:** Zentrale Konfiguration – alle Settings an einem Ort

**Enthält:**
- `OPENBB_PAT`, `FMP_API_KEY` – API Keys aus Secrets/Env
- `TIMEFRAMES` – Dict mit allen verfügbaren Zeitrahmen & Labels
- `INDICATOR_DEFAULTS` – Standard-Werte für alle Indikatoren
- `COLORS` – Farb-Schema (Dark Theme)
- `CHART_TEMPLATE`, `CHART_HEIGHT` – Chart-Einstellungen
- `DEFAULT_WATCHLIST` – Start-Watchlist
- `FEATURES` – Feature Flags (ein/aus schalten)
- `CACHE_TTL` – Cache-Dauer je Datentyp

**Verwendung:**
```python
from config import COLORS, TIMEFRAMES, DEFAULT_TICKER
```

---

### `requirements.txt` ✅
**Zweck:** Alle Python-Dependencies

**Installieren:**
```bash
pip install -r requirements.txt
```

**Wichtigste Packages:**
- `openbb` – Datenprovider-Framework
- `streamlit` – Web UI
- `plotly` – Interaktive Charts
- `pandas-ta` – Technische Indikatoren (200+)
- `pydantic` – Data Validation
- `yfinance` – Yahoo Finance (kein API Key nötig)
- `loguru` – Logging

---

## 📂 core/ - Domain Layer

### `core/models.py` ✅
**Zweck:** Pydantic-Datenmodelle für alle Datenstrukturen

**Enthaltene Models:**

| Model | Felder | Eigenschaften |
|-------|--------|---------------|
| `OHLCVData` | timestamp, open/high/low/close, volume | validator: high >= low |
| `StockQuote` | ticker, price, change, change_pct, volume | `is_positive` property |
| `CompanyProfile` | ticker, name, sector, industry, country, ... | - |
| `IncomeStatement` | revenue, net_income, eps, ebitda, ... | `gross_margin`, `net_margin` |
| `KeyMetrics` | pe, pb, ps, ev_ebitda, roe, roa, ... | - |
| `ScreenerFilter` | pe_min/max, roe_min, rsi_min/max, ... | - |
| `ScreenerResult` | ticker, price, metrics, score | - |
| `Position` | ticker, quantity, avg_price | `market_value`, `pnl`, `pnl_pct` |
| `Portfolio` | positions, cash | `total_value`, `total_pnl` |
| `NewsItem` | title, url, source, published, sentiment | - |

**Verwendung:**
```python
from core.models import StockQuote
quote = StockQuote(ticker="AAPL", price=185.0, change=1.5, change_pct=0.82, volume=50000000)
print(quote.is_positive)  # True
```

---

### `core/constants.py` ✅
**Zweck:** Typisierte Enumerationen und unveränderliche Konstanten

**Enthaltene Enums:**
- `Timeframe` – "1m", "5m", "15m", "1h", "4h", "1d", "1wk", "1mo"
- `Period` – "7d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"
- `AssetClass` – equity, etf, crypto, forex, futures, options, bond
- `DataProvider` – yfinance, fmp, alpha_vantage, openbb
- `Sector` – Alle 11 S&P 500 Sektoren
- `SignalType` – strong_buy, buy, neutral, sell, strong_sell

**Wichtige Konstanten:**
- `SECTOR_ETFS` – Sektor → ETF-Ticker (XLK, XLV, XLF, ...)
- `MARKET_INDICES` – Symbol → Name (^GSPC → "S&P 500")
- `SIGNAL_COLORS` – SignalType → Farbe

---

### `core/exceptions.py` ✅
**Zweck:** Custom Exceptions für bessere Fehlerbehandlung

| Exception | Auslöser |
|-----------|----------|
| `OpenBBTerminalError` | Basis für alle App-Fehler |
| `DataFetchError(ticker, provider)` | Daten können nicht geladen werden |
| `InvalidTickerError(ticker)` | Ticker nicht gefunden |
| `ProviderError(providers)` | Alle Provider fehlgeschlagen |
| `InsufficientDataError(required, available)` | Zu wenig Datenpunkte für Berechnung |

---

## 📂 data/ - Infrastruktur-Layer

### `data/openbb_client.py` ✅
**Zweck:** Einheitlicher Zugang zu allen Marktdaten

**Die Hauptklasse: `OpenBBClient`**

| Methode | Beschreibung | Cache TTL |
|---------|-------------|-----------|
| `get_price_history(ticker, period, interval)` | OHLCV DataFrame | 5 Min |
| `get_quote(ticker)` | Aktueller Kurs + Metadaten | 1 Min |
| `get_company_info(ticker)` | Unternehmens-Profil | 1 Std |
| `get_financials(ticker, statement)` | GuV / Bilanz / Cashflow | 1 Std |
| `get_news(ticker, limit)` | Aktuelle News | 10 Min |
| `get_market_overview()` | Alle Indizes | 2 Min |
| `clear_cache()` | Cache leeren | - |

**Singleton-Zugang (empfohlen):**
```python
from data.openbb_client import get_client
client = get_client()
df = client.get_price_history("AAPL", "1y", "1d")
quote = client.get_quote("MSFT")
```

**Fallback-Kette:** OpenBB Platform → yfinance direkt

**Testen:**
```bash
python data/openbb_client.py
```

---

## 📂 indicators/ - Technical Analysis

### `indicators/technical.py` ✅
**Zweck:** Berechnung aller technischen Indikatoren

**Die Hauptklasse: `TechnicalIndicators`**

Fluent Interface – Methoden geben `self` zurück und können gekettet werden:

```python
from indicators.technical import TechnicalIndicators
ti = TechnicalIndicators(df)
df_with_indicators = ti.add_sma([20, 50]).add_rsi().add_macd().df
```

**Verfügbare Methoden:**

| Methode | Neue Spalten | Beschreibung |
|---------|-------------|-------------|
| `add_sma([20,50,200])` | `sma_20`, `sma_50`, `sma_200` | Simple Moving Average |
| `add_ema([9,21,50])` | `ema_9`, `ema_21`, `ema_50` | Exponential Moving Average |
| `add_vwap()` | `vwap` | Volume Weighted Average Price |
| `add_rsi(14)` | `rsi` | RSI 0-100 |
| `add_macd(12,26,9)` | `macd`, `macd_signal`, `macd_hist` | MACD |
| `add_stochastic(14,3)` | `stoch_k`, `stoch_d` | Stochastic |
| `add_bollinger_bands(20,2)` | `bb_upper`, `bb_middle`, `bb_lower` | Bollinger Bands |
| `add_atr(14)` | `atr` | Average True Range |
| `add_obv()` | `obv` | On-Balance Volume |
| `add_volume_ma(20)` | `volume_ma` | Volumen-Durchschnitt |
| `add_all()` | Alle oben | Alle Standard-Indikatoren |
| `add_chart_defaults()` | Subset | Für Chart-Seite optimiert |

**Fallback:** Wenn `pandas-ta` nicht installiert → manuelle numpy/pandas Berechnung

---

## 📂 ui/ - Presentation Layer

### `ui/components/charts.py` ✅
**Zweck:** Alle Plotly-Chart-Komponenten

**Funktionen:**

`create_main_chart(df, ticker, show_indicators)` – **Hauptfunktion**
- Parameter `show_indicators`: dict mit `{"sma_20": True, "rsi": True, ...}`
- Erstellt automatisch Sub-Charts für Volumen, RSI, MACD (wenn aktiviert)
- Dark Theme, keine Wochenenden, responsive

```python
from ui.components.charts import create_main_chart
fig = create_main_chart(df, "AAPL", {"sma_20": True, "rsi": True})
st.plotly_chart(fig, use_container_width=True)
```

`create_metric_sparkline(values, color)` – Kleines Sparkline für Cards

---

### `ui/components/metrics.py` ✅
**Zweck:** KPI-Cards und Formatierungs-Helfer

**Funktionen:**

| Funktion | Output | Beispiel |
|----------|--------|---------|
| `metric_card(label, value, delta)` | Streamlit metric | - |
| `price_header(ticker, quote)` | Großer Preis-Header | AAPL $185.23 ▲ +1.5% |
| `kpi_row(metrics_list)` | Mehrere Cards in Reihe | - |
| `format_large_number(1234567890)` | `"$1.23B"` | Milliarden/Millionen |
| `format_pct(0.0532)` | `"+5.32%"` | Mit Vorzeichen |
| `format_ratio(25.3)` | `"25.30x"` | Für P/E, P/B |
| `signal_badge("strong_buy")` | HTML-Badge grün | - |

---

### `ui/components/sidebar.py` ✅
**Zweck:** Globale Sidebar-Elemente

**Funktionen:**
- `render_ticker_input()` → gibt Ticker-String zurück
- `render_timeframe_selector()` → gibt `(interval, period)` zurück
- `render_indicator_settings()` → gibt `dict` mit True/False je Indikator
- `render_watchlist()` → gibt `(watchlist, selected_ticker)` zurück
- `render_cache_controls()` → Cache-Leeren Button

---

### `ui/pages/1_📈_charts.py` ✅
**Zweck:** Chart-Analyse Seite (Page 1)

**Was es zeigt:**
- Ticker-Eingabe + Timeframe-Selector (Sidebar)
- Großer Preis-Header mit aktuellem Kurs
- KPI-Leiste (Market Cap, P/E, 52W High/Low, Volumen)
- Candlestick Chart mit aktivierten Indikatoren
- Sub-Charts: Volumen, RSI, MACD (wenn aktiviert)
- Aufklappbare Rohdaten-Tabelle

**Aufrufen:** Direkt via Streamlit Navigation oder `streamlit run ui/pages/1_📈_charts.py`

---

## 📂 services/ - Application Layer (Phase 2)

### `services/market_service.py` ⏳
**Geplant für:** Phase 2, Tag 2  
**Zweck:** Service-Layer zwischen Pages und OpenBB Client  
**Wird enthalten:** Daten-Aggregation, Business Logic, Fehlerbehandlung auf hohem Level

### `services/screener_service.py` ⏳
**Geplant für:** Phase 2, Tag 4  
**Zweck:** Stock-Screening Logik  
**Wird enthalten:** Filter-Anwendung auf Universum, Signal-Berechnung, Ranking

---

## 📂 strategies/ - Trading Strategies (Phase 3)
Alle Dateien hier sind für Phase 3 geplant.

---

## 📂 ai/ - AI Components (Phase 3)

### `ai/analyst.py` ⏳
**Geplant für:** Phase 3  
**Zweck:** KI-gestützte Analyse mit Gemini/Claude API

---

## 📂 utils/ - Utilities (Phase 2)

### `utils/formatters.py` ⏳
**Geplant für:** Phase 2  
**Wird enthalten:** Zahlen-, Datum-, Prozent-Formatierung

---

## 📂 tests/ - Testing (Phase 2)

### `tests/test_openbb_client.py` ⏳
**Geplant für:** Phase 2  
**Was wird getestet:** get_price_history, get_quote, Caching, Fallback-Verhalten

---

## 🗝️ Konfigurationsdateien

### `.streamlit/config.toml` ✅
Streamlit Dark Theme + Server-Einstellungen.  
Farben: Background `#0e1117`, Primary `#26a69a`.

### `.streamlit/secrets.toml` ⚠️ LOKAL ERSTELLEN
```toml
OPENBB_PAT = "pat_..."        # von my.openbb.co
FMP_API_KEY = "..."            # optional
```
**NIEMALS in Git committen!** Bereits in `.gitignore`.

### `.gitignore` ✅
Schützt: `secrets.toml`, `.env`, `__pycache__/`, `.cache/`

---

## 💡 Architektur-Entscheidungen

**Warum Singleton für OpenBBClient?**  
Streamlit erstellt pro Seite neue Python-Instanzen. Ein Singleton verhindert,  
dass der OpenBB-Client zig Mal initialisiert wird und Caches verloren gehen.

**Warum Fluent Interface bei TechnicalIndicators?**  
Ermöglicht lesbares Chaining: `ti.add_rsi().add_macd().add_bb().df`  
statt 3 separate Aufrufe.

**Warum Pydantic Models?**  
Type Safety verhindert zur Laufzeit Bugs.  
IDE-Autocomplete funktioniert zuverlässig.  
Automatische Validierung (z.B. High >= Low).

---

**Letzte Aktualisierung:** 25. Februar 2026 - Foundation Complete  
**Alle Phase-1-Module:** ✅ Dokumentiert und implementiert
