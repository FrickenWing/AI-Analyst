# 🚀 Getting Started - Schneller Wiedereinstieg

**Letzte Aktualisierung:** 25. Februar 2026 – Phase 2 abgeschlossen

---

## ⚡ Quick Status (30 Sekunden)

```
Phase 1: Foundation     [████████░░] 85% ✅
Phase 2: Core Features  [████████░░] 80% ✅
Phase 3: Advanced       [░░░░░░░░░░]  0% ← JETZT
Phase 4: Polish         [░░░░░░░░░░]  0%
```

### Was läuft bereits?
✅ `streamlit run app.py` → Market Dashboard + 5 Seiten  
✅ 📈 Chart-Analyse mit Indikatoren  
✅ 📊 Fundamentals (5 Tabs: Übersicht, Financials, Kennzahlen, Analysten, News)  
✅ 🔍 Screener mit Composite Score + CSV Export  
✅ 📰 News Feed (Ticker + Watchlist)  
✅ 💼 Portfolio Tracking (P&L, Charts, Tabelle)  

### Nächster Schritt:
**→ Phase 3: Macro Dashboard (`ui/pages/6_🌍_macro.py`)**

---

## 🚀 Sofort starten

```bash
cd openbb_terminal_pro
pip install -r requirements.txt   # einmalig
streamlit run app.py
```

Alle 5 Seiten sind in der Sidebar navigierbar.

---

## 📚 Die 4 wichtigen Dateien

| Datei | Wann lesen |
|-------|-----------|
| `ROADMAP.md` | Vor jeder Session (5 Min) – Wo stehen wir? |
| `DAILY_LOG.md` | Start + Ende jeder Session – Was war / was kommt? |
| `FILE_DOCUMENTATION.md` | Bei Fragen zu einer Datei |
| `GETTING_STARTED.md` | Diese Datei – Quick Start & Fehlerbehebung |

---

## 🎯 Session-Start Routine

```bash
# 1. Projekt öffnen
cd A:/OpenBB/openbb_terminal_pro

# 2. Status prüfen
git status && git log --oneline -3

# 3. App testen
streamlit run app.py

# 4. Nächsten Task aus ROADMAP.md holen
#    → Aktuell: ui/pages/6_🌍_macro.py

# 5. Arbeiten!
# 6. Am Ende: DAILY_LOG.md + ROADMAP.md updaten + git commit
```

---

## 💡 Code-Patterns (Copy-Paste für neue Seiten)

### Neue Page-Datei starten:
```python
import streamlit as st
from data.openbb_client import get_client
from services.market_service import get_market_service
from ui.components.sidebar import render_ticker_input
from utils.formatters import fmt_price, fmt_pct, fmt_large

st.set_page_config(page_title="Meine Seite", page_icon="🎯", layout="wide")
st.sidebar.title("🎯 Meine Seite")
ticker  = render_ticker_input()
client  = get_client()
svc     = get_market_service()

overview = svc.get_stock_overview(ticker)
df       = client.get_price_history(ticker, "1y", "1d")
```

### Indikatoren berechnen:
```python
from indicators.technical import TechnicalIndicators
df = TechnicalIndicators(df).add_sma([20, 50]).add_rsi().add_macd().df
```

### Screener nutzen:
```python
from services.screener_service import get_screener_service, UNIVERSES
svc = get_screener_service()
df_results = svc.run_screen(UNIVERSES["mega_cap_us"], filters={"pe_max": 30})
display_df = svc.get_display_df(df_results)
```

### Chart anzeigen:
```python
from ui.components.charts import create_main_chart
fig = create_main_chart(df, ticker, {"sma_20": True, "rsi": True})
st.plotly_chart(fig, use_container_width=True)
```

---

## 🚨 Häufige Probleme

| Problem | Lösung |
|---------|--------|
| `ModuleNotFoundError` | `pip install -r requirements.txt` |
| `pandas-ta` Fehler | `pip install pandas-ta==0.3.14b0` |
| Keine Daten für Ticker | Ticker auf Yahoo Finance prüfen (Ticker korrekt?) |
| Screener sehr langsam | Normal bei yfinance (~1-2s/Ticker) – Phase 3 bringt Disk-Cache |
| Streamlit zeigt alten Stand | `Ctrl+Shift+R` im Browser oder App-Cache leeren |
| `secrets.toml` Fehler | Datei erstellen: `.streamlit/secrets.toml` (Vorlage: `.toml.example`) |

---

## 🎯 Phase 3 Tasks (JETZT)

### 1. Macro Dashboard (3-4 Std)
```python
# ui/pages/6_🌍_macro.py
# Datenquellen via yfinance (kein API Key!):
# Treasuries: "^TNX", "^FVX", "^IRX"
# Währungen:  "EURUSD=X", "USDJPY=X", "GBPUSD=X"
# Rohstoffe:  "GC=F" (Gold), "CL=F" (Öl), "HG=F" (Kupfer)
# Sektoren:   "XLK", "XLV", "XLF", "XLE", ...
```

### 2. Portfolio Analytics (3 Std)
```python
# services/portfolio_service.py
# - Sharpe Ratio: (Return - Risk Free Rate) / StdDev
# - Max Drawdown: max((max - current) / max)
# - VaR 95%: numpy percentile
# - Korrelations-Matrix: df.corr()
```

### 3. Disk-Caching (1 Std)
```python
# data/cache_manager.py mit diskcache
# Screener-Ergebnisse 10 Min cachen → 10x schneller
```

---

## ✅ Pre-Session Checklist

- [ ] ROADMAP.md gelesen (5 Min)
- [ ] DAILY_LOG.md gelesen (2 Min)
- [ ] `streamlit run app.py` → App läuft?
- [ ] Nächsten Task klar (Macro Dashboard)
- [ ] Kaffee geholt ☕

**Los geht's!** 🚀

---

**App starten:** `streamlit run app.py`  
**Nächster Fokus:** Phase 3 – Macro Dashboard + Portfolio Analytics
