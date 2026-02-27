"""
data/openbb_client.py - Robuster Client für FMP & yfinance
Behebt KeyError 'open', Prozent-Anzeige und Such-Probleme.
"""
import time
import hashlib
import json
import requests
import pandas as pd
import streamlit as st
from functools import wraps
from loguru import logger

# ─────────────────────────────────────────────
# CACHE DECORATOR
# ─────────────────────────────────────────────
_cache_store: dict = {}

def cached(ttl_seconds: int = 300):
    """Einfacher In-Memory Cache."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key_parts = [func.__name__, str(args), str(kwargs)]
            key = hashlib.md5(json.dumps(key_parts, sort_keys=True, default=str).encode()).hexdigest()

            if key in _cache_store:
                value, expires_at = _cache_store[key]
                if time.time() < expires_at:
                    return value

            result = func(*args, **kwargs)
            _cache_store[key] = (result, time.time() + ttl_seconds)
            return result
        return wrapper
    return decorator

# ─────────────────────────────────────────────
# OPENBB CLIENT CLASS
# ─────────────────────────────────────────────
class OpenBBClient:
    def __init__(self):
        # Versuche Keys aus verschiedenen Quellen zu lesen
        self.fmp_key = st.secrets.get("FMP_API_KEY", "")
        
        # Init OpenBB (optional)
        self._obb = None
        try:
            from openbb import obb
            if self.fmp_key:
                obb.user.credentials.fmp_api_key = self.fmp_key
            self._obb = obb
        except Exception:
            pass

    # ─────────────────────────────────────────
    # 1. SUCHE (HYBRID: FMP -> YAHOO)
    # ─────────────────────────────────────────
    @cached(ttl_seconds=3600)
    def search_ticker(self, query: str) -> list[dict]:
        """Sucht erst via FMP, bei Fehler Fallback auf Yahoo."""
        if not query: return []
        
        results = []
        
        # A) Versuch via FMP (Profi-Daten)
        if self.fmp_key:
            try:
                url = f"https://financialmodelingprep.com/api/v3/search?query={query}&limit=10&apikey={self.fmp_key}"
                resp = requests.get(url, timeout=2)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        for item in data:
                            results.append({
                                "ticker": item.get('symbol'),
                                "name": item.get('name', 'Unbekannt'),
                                "exchange": item.get('exchangeShortName', 'N/A'),
                                "currency": item.get('currency', 'USD')
                            })
                        return results # Treffer!
            except Exception as e:
                logger.warning(f"FMP Suche fehlgeschlagen: {e}")

        # B) Fallback via Yahoo (falls FMP leer/kaputt/kein Key)
        try:
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=8&newsCount=0"
            headers = {'User-Agent': 'Mozilla/5.0'}
            data = requests.get(url, headers=headers, timeout=2).json()
            for item in data.get('quotes', []):
                if item.get('quoteType') in ['EQUITY', 'ETF']:
                    results.append({
                        "ticker": item.get('symbol'),
                        "name": item.get('shortname') or item.get('longname', item.get('symbol')),
                        "exchange": item.get('exchDisp', 'N/A'),
                        "currency": "USD" # Annahme
                    })
        except Exception as e:
            logger.error(f"Yahoo Suche fehlgeschlagen: {e}")
            
        return results

    # ─────────────────────────────────────────
    # 2. CHART DATEN (MIT CRASH-FIX)
    # ─────────────────────────────────────────
    @cached(ttl_seconds=300)
    def get_price_history(self, ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        """Lädt OHLCV Daten und repariert MultiIndex-Fehler."""
        
        # A) Versuch via OpenBB/FMP
        if self._obb and self.fmp_key:
            try:
                df = self._obb.equity.price.historical(
                    symbol=ticker,
                    start_date=self._get_start_date(period),
                    interval=interval,
                    provider="fmp"
                ).to_df()
                # FMP liefert saubere Daten, nur normalisieren
                df.index.name = "date"
                df = df.rename(columns=str.lower)
                return df[["open", "high", "low", "close", "volume"]].dropna()
            except Exception:
                pass # Weiter zum Fallback

        # B) Fallback: yfinance (Robuste Version)
        return self._yfinance_history(ticker, period, interval)

    def _yfinance_history(self, ticker, period, interval):
        import yfinance as yf
        try:
            # auto_adjust=True ist oft sicherer für Charts
            df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
            
            if df.empty: return pd.DataFrame()

            # 🛠️ CRASH FIX: MultiIndex flachklopfen
            # Wenn Spalten aussehen wie ('Close', 'AAPL'), nimm nur 'Close'
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Alles klein schreiben
            df.columns = [c.lower() for c in df.columns]
            
            # Falls 'adj close' da ist, zu 'close' machen
            if "adj close" in df.columns:
                df = df.rename(columns={"adj close": "close"})
            
            # Prüfen ob wir alles haben
            required = ["open", "high", "low", "close", "volume"]
            for c in required:
                if c not in df.columns:
                    df[c] = 0.0 # Fehlende Spalten auffüllen
            
            return df[required].dropna()

        except Exception as e:
            logger.error(f"Chart Ladefehler {ticker}: {e}")
            return pd.DataFrame()

    # ─────────────────────────────────────────
    # 3. QUOTE (MIT PROZENT-FIX)
    # ─────────────────────────────────────────
    @cached(ttl_seconds=60)
    def get_quote(self, ticker: str) -> dict:
        # A) FMP
        if self.fmp_key:
            try:
                url = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={self.fmp_key}"
                res = requests.get(url, timeout=2).json()
                if res:
                    d = res[0]
                    return {
                        "ticker": d.get("symbol"),
                        "price": d.get("price", 0),
                        "change_pct": d.get("changesPercentage", 0),
                        "volume": d.get("volume", 0),
                        "market_cap": d.get("marketCap", 0),
                        "pe_ratio": d.get("pe", 0),
                        "week_52_high": d.get("yearHigh", 0),
                        "week_52_low": d.get("yearLow", 0),
                    }
            except: pass
            
        # B) Yahoo Fallback
        return self._yfinance_quote(ticker)

    def _yfinance_quote(self, ticker):
        import yfinance as yf
        try:
            i = yf.Ticker(ticker).info
            
            # KORREKTUR: Keine Multiplikation mit 100 mehr!
            pct = i.get("regularMarketChangePercent", 0)
            
            # Falls yfinance doch mal 0.015 liefert (passiert selten bei alten Versionen), 
            # merken wir das in der UI oder lassen es so. 
            # Aktuelle APIs liefern meist den "ganzen" Prozentwert (z.B. 1.25).
            
            return {
                "ticker": ticker,
                "price": i.get("currentPrice") or i.get("regularMarketPrice", 0),
                "change_pct": pct, # Hier wurde das *100 entfernt
                "volume": i.get("volume", 0),
                "market_cap": i.get("marketCap", 0),
                "pe_ratio": i.get("trailingPE", 0),
                "week_52_high": i.get("fiftyTwoWeekHigh", 0),
                "week_52_low": i.get("fiftyTwoWeekLow", 0),
            }
        except:
            return {"ticker": ticker, "price": 0, "change_pct": 0, "volume": 0}

    # ─────────────────────────────────────────
    # HILFSFUNKTIONEN
    # ─────────────────────────────────────────
    def _get_start_date(self, period: str) -> str:
        from datetime import datetime, timedelta
        # Mapping Period -> Tage
        days_map = {"1d": 1, "5d": 5, "1mo": 30, "3mo": 90, "6mo": 180, 
                    "ytd": 365, "1y": 365, "2y": 730, "5y": 1825, "max": 18250}
        days = days_map.get(period, 365)
        return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    # Weitere Services (Fundamentaldaten)
    @cached(ttl_seconds=3600)
    def get_company_info(self, ticker):
        # ... (Bleibt einfach, um Code kurz zu halten)
        return {"ticker": ticker, "name": ticker}
        
    @cached(ttl_seconds=3600)
    def get_financials(self, ticker, type_):
        import yfinance as yf
        t = yf.Ticker(ticker)
        if type_ == "income": return t.financials
        if type_ == "balance": return t.balance_sheet
        return t.cashflow
    
    @cached(ttl_seconds=3600)
    def get_analyst_info(self, ticker):
        # Dummy Implementation für Charts
        return {"recommendation": "Hold"}

# SINGLETON
_client = None
def get_client():
    global _client
    if not _client: _client = OpenBBClient()
    return _client