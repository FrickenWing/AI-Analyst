# 🚀 Getting Started - Schneller Wiedereinstieg

**Letzte Aktualisierung:** 26. Februar 2026 – Phase 3 (75%)

---

## ⚡ Quick Status (30 Sekunden)

```
Phase 1: Foundation     [████████░░]  85% ✅
Phase 2: Core Features  [██████████] 100% ✅
Phase 3: Advanced       [███████░░░]  75% 🔄 ← HIER
Phase 4: Polish/Deploy  [░░░░░░░░░░]   0% ⏳
```

### Was läuft bereits?
✅ 6 vollständige Seiten in der Streamlit-Sidebar
✅ 📈 Charts mit Indikatoren
✅ 📊 Fundamentals (GuV, Bilanz, Analysten)
✅ 🔍 Screener mit Composite Score
✅ 📰 News Feed
✅ 💼 Portfolio (P&L + Sharpe + VaR + Korrelation) ← Phase 3
✅ 🌍 Makro Dashboard (Zinsen, Sektoren, Währungen, VIX) ← Phase 3
✅ 💾 Disk-Caching ← Phase 3

### Nächster Schritt:
**→ `pages/7_ai_analyst.py` – KI-Analyst mit Claude API**

---

## 🚀 App starten

```
cd A:\OpenBB
streamlit run app.py
```

Alle 6 Seiten erscheinen automatisch in der linken Sidebar.

---

## ⚠️ Bekannte Probleme & Fixes

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: config` | Du bist im falschen Ordner! `cd A:\OpenBB` dann nochmal |
| `pandas-ta` Fehler | `pip install git+https://github.com/twopirllc/pandas-ta.git@development` |
| `plotly` fehlt | `pip install plotly>=5.15.0` |
| `KeyError: url_pathname` | Alte `app.py` → neue herunterladen (kein `st.page_link`) |
| Seiten erscheinen nicht | Files müssen in `A:\OpenBB\pages\` liegen (nicht `ui\pages\`) |
| Portfolio Analytics langsam | Normal (~20s) – einmal berechnen, dann gecacht |

---

## 📦 Installation (einmalig)

```
pip install streamlit yfinance pandas plotly pydantic loguru diskcache
pip install git+https://github.com/twopirllc/pandas-ta.git@development
```

---

## 💡 Code-Patterns

### Neue Page starten:
```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from data.openbb_client import get_client
from services.market_service import get_market_service
from utils.formatters import fmt_price, fmt_pct, fmt_large

st.set_page_config(page_title="Meine Seite", page_icon="🎯", layout="wide")
ticker = st.sidebar.text_input("Ticker", "AAPL").upper()
client = get_client()
svc    = get_market_service()
```

### Cache nutzen:
```python
from data.cache_manager import get_cache, TTL
cache = get_cache()
data = cache.get(f"mykey:{ticker}")
if data is None:
    data = expensive_api_call(ticker)
    cache.set(f"mykey:{ticker}", data, ttl=TTL["fundamentals"])
```

### Portfolio Analytics:
```python
from services.portfolio_service import get_portfolio_service
svc       = get_portfolio_service()
analytics = svc.get_full_analytics(positions)
sharpe    = analytics["metrics"]["sharpe_ratio"]
drawdown  = analytics["metrics"]["max_drawdown"]
alpha     = analytics["benchmark"]["alpha"]
```

---

## 🎯 Phase 3 Rest: AI-Analyst (nächster Task)

```python
# pages/7_ai_analyst.py – Grundgerüst:
import anthropic

client = anthropic.Anthropic(api_key=st.secrets.get("ANTHROPIC_API_KEY",""))
msg = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": f"""
        Analysiere die Aktie {ticker}.
        Aktueller Kurs: {price}
        P/E: {pe_ratio}
        RSI: {rsi}
        Gib eine kurze Einschätzung (bullish/bearish/neutral) mit Begründung.
        """
    }]
)
st.markdown(msg.content[0].text)
```

**Zeitaufwand:** ~2-3 Stunden

---

## ✅ Pre-Session Checklist

- [ ] ROADMAP.md gelesen (2 Min)
- [ ] `streamlit run app.py` → App läuft + alle 6 Seiten sichtbar?
- [ ] Nächster Task klar: `pages/7_ai_analyst.py`
- [ ] `ANTHROPIC_API_KEY` in `.streamlit/secrets.toml` vorhanden?

---

**App starten:** `cd A:\OpenBB && streamlit run app.py`
**Nächster Fokus:** Phase 3 Rest – AI-Analyst
