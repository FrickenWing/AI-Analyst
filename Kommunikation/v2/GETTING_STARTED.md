# 🚀 Getting Started - Schneller Wiedereinstieg

**Zweck:** Quick Start nach Pause oder für neue Sessions  
**Lesezeit:** 3 Minuten  
**Letzte Aktualisierung:** 25. Februar 2026 - Foundation Complete

---

## ⚡ Quick Status Check (30 Sekunden)

### Wo stehen wir?
```
Phase 1: Foundation     [████████░░] 85% ✅ FAST FERTIG
Phase 2: Core Features  [░░░░░░░░░░]  0% ← NÄCHSTES ZIEL
Phase 3: Advanced       [░░░░░░░░░░]  0%
Phase 4: Polish         [░░░░░░░░░░]  0%
```

### Was ist fertig?
✅ OpenBB Client Wrapper (`data/openbb_client.py`)  
✅ Alle Core Models & Konstanten (`core/`)  
✅ Technische Indikatoren (`indicators/technical.py`)  
✅ Chart-Komponenten (`ui/components/charts.py`)  
✅ Chart-Analyse-Seite (`ui/pages/1_📈_charts.py`)  
✅ Haupt-Dashboard (`app.py`)  
✅ Zentrale Konfiguration (`config.py`)  
✅ Requirements, README, .gitignore  

### Nächster Schritt?
**→ Fundamentals-Page (`ui/pages/2_📊_fundamentals.py`) erstellen**

### App sofort starten:
```bash
cd openbb_terminal_pro
streamlit run app.py
```

---

## 📚 Die 4 wichtigen Dateien

### 1️⃣ ROADMAP.md ← IMMER ZUERST LESEN
Gesamtübersicht, was fertig ist, nächste Schritte.

### 2️⃣ FILE_DOCUMENTATION.md ← Bei Fragen zu Dateien
Jede Datei detailliert erklärt: Zweck, API, Code-Beispiele.

### 3️⃣ DAILY_LOG.md ← Start & Ende jeder Session
Was wurde gemacht, was kommt als nächstes.

### 4️⃣ GETTING_STARTED.md ← Diese Datei
Quick Start, Commands, Fehlerbehebung.

---

## 🎯 Session-Start Routine (5 Min)

```bash
# 1. Zum Projektordner
cd A:/OpenBB/openbb_terminal_pro

# 2. Git Status
git status
git log --oneline -5

# 3. App testen - läuft alles?
streamlit run app.py

# 4. Nächsten Task aus ROADMAP.md holen
# → aktuell: ui/pages/2_📊_fundamentals.py

# 5. Loslegen!
```

---

## 🔧 Wichtige Commands

```bash
# App starten
streamlit run app.py

# Dependencies installieren
pip install -r requirements.txt

# OpenBB Client testen
python data/openbb_client.py

# Tests ausführen
pytest tests/

# Git Commit
git add .
git commit -m "feat: Fundamentals-Page hinzugefügt"
```

---

## 📂 Projektstruktur (Quick Reference)

```
openbb_terminal_pro/
├── app.py                  ✅ Dashboard - Entry Point
├── config.py               ✅ Alle Settings
├── requirements.txt        ✅ Dependencies
│
├── core/                   ✅ Models, Constants, Exceptions
├── data/
│   └── openbb_client.py    ✅ OpenBB Wrapper
├── indicators/
│   └── technical.py        ✅ SMA/EMA/RSI/MACD/BB/ATR/OBV
│
├── ui/
│   ├── components/
│   │   ├── charts.py       ✅ Plotly Charts
│   │   ├── metrics.py      ✅ KPI Cards
│   │   └── sidebar.py      ✅ Sidebar
│   └── pages/
│       ├── 1_📈_charts.py  ✅ Chart-Analyse (FERTIG)
│       ├── 2_📊_fundamentals.py  ⏳ NÄCHSTER SCHRITT
│       ├── 3_🔍_screener.py      ⏳ Phase 2
│       └── ...
│
├── services/               ⏳ Phase 2
├── strategies/             ⏳ Phase 3
└── tests/                  ⏳ Phase 2
```

---

## 🚨 Häufige Probleme & Lösungen

### Problem: "Module not found"
```bash
pip install -r requirements.txt
# oder spezifisch:
pip install openbb streamlit pandas plotly pandas-ta pydantic loguru
```

### Problem: "pandas-ta not found"
```bash
pip install pandas-ta
# Falls Fehler: pip install pandas-ta==0.3.14b0
```

### Problem: "No secrets found" / API-Fehler
→ Das ist OK! yfinance funktioniert OHNE API Key.  
Wenn du mehr Provider willst:
```bash
# .streamlit/secrets.toml erstellen:
OPENBB_PAT = "pat_dein_token"  # von my.openbb.co
```

### Problem: "Ich weiß nicht was als nächstes kommt"
```bash
# Öffne ROADMAP.md → "Nächster konkreter Schritt"
# Aktuell: Fundamentals-Page (Phase 2, Tag 2)
```

### Problem: Charts laden nicht
```bash
# Teste OpenBB Client direkt:
python data/openbb_client.py
# → Wenn OK: ✅ Test 1/2/3 abgeschlossen
```

### Problem: Streamlit zeigt alten Stand
```bash
# Cache im Browser leeren (Ctrl+Shift+R)
# Oder in der App: Sidebar → "🔄 Daten refreshen"
```

---

## 💡 Code-Patterns (Copy-Paste)

### Daten laden in einer neuen Page:
```python
from data.openbb_client import get_client
from ui.components.sidebar import render_ticker_input

client = get_client()
ticker = render_ticker_input()

df = client.get_price_history(ticker, "1y", "1d")
quote = client.get_quote(ticker)
info = client.get_company_info(ticker)
```

### Indikatoren berechnen:
```python
from indicators.technical import TechnicalIndicators
ti = TechnicalIndicators(df)
df = ti.add_sma([20, 50]).add_rsi().add_macd().df
```

### Chart anzeigen:
```python
from ui.components.charts import create_main_chart
fig = create_main_chart(df, ticker, {"sma_20": True, "rsi": True})
st.plotly_chart(fig, use_container_width=True)
```

### Metrik-Karten anzeigen:
```python
from ui.components.metrics import kpi_row, format_large_number
kpi_row([
    {"label": "Market Cap", "value": format_large_number(1234567890)},
    {"label": "P/E Ratio",  "value": "25.3x"},
])
```

---

## 🎯 Nächste Tasks (nach Priorität)

### JETZT (Phase 2, Tag 2):
**Fundamentals-Page** - `ui/pages/2_📊_fundamentals.py`
- Company Header mit Profil
- Key Metrics Row
- Financial Statements (Income / Balance / Cashflow Tabs)
- Geschätzte Zeit: 3-4 Stunden

### Danach (Phase 2, Tag 4):
**Screener-Page** - `ui/pages/3_🔍_screener.py`

### Danach (Phase 2, Tag 6):
**News-Feed** in Seiten integrieren

---

## ✅ Pre-Session Checklist

- [ ] ROADMAP.md gelesen (5 Min)
- [ ] DAILY_LOG.md gelesen (2 Min)
- [ ] `streamlit run app.py` → App läuft?
- [ ] Nächster Task klar (Fundamentals-Page)
- [ ] Kaffee geholt ☕

**Los geht's!** 🚀

---

**Letzte Aktualisierung:** 25. Februar 2026 - Foundation Complete  
**App Status:** ✅ Lauffähig - `streamlit run app.py`  
**Nächster Fokus:** Fundamentals-Page (Phase 2)
