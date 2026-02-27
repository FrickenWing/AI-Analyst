"""
data/openbb_client.py - Fix für Prozentwerte und API
"""
import time
import hashlib
import json
import requests
import pandas as pd
import streamlit as st
from functools import wraps
from loguru import logger

# Der Cache-Speicher muss global zugänglich sein
_cache_store: dict = {}

def cached(ttl_seconds: int = 300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key_parts = [func.__name__, str(args), str(kwargs)]
            key = hashlib.md5(json.dumps(key_parts, sort_keys=True, default=str).encode()).hexdigest()
            if key in _cache_store:
                val, exp = _cache_store[key]
                if time.time() < exp: return val
            res = func(*args, **kwargs)
            _cache_store[key] = (res, time.time() + ttl_seconds)
            return res
        return wrapper
    return decorator

class OpenBBClient:
    def __init__(self):
        self.fmp_key = st.secrets.get("FMP_API_KEY", "")
        self._obb = None
        try:
            from openbb import obb
            if self.fmp_key: obb.user.credentials.fmp_api_key = self.fmp_key
            self._obb = obb
        except: pass

    def clear_cache(self):
        """Leert den internen Cache komplett."""
        global _cache_store
        _cache_store.clear()
        st.cache_data.clear() # Sicherheitshalber auch Streamlit Cache

    @cached(ttl_seconds=3600)
    def search_ticker(self, query: str) -> list:
        if not query: return []
        results = []
        # FMP
        if self.fmp_key:
            try:
                url = f"https://financialmodelingprep.com/api/v3/search?query={query}&limit=10&apikey={self.fmp_key}"
                data = requests.get(url, timeout=3).json()
                for item in data: results.append({"ticker": item['symbol'], "name": item['name'], "exchange": item.get('exchangeShortName','N/A')})
                return results
            except: pass
        # Yahoo Fallback
        try:
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=5"
            data = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=3).json()
            for item in data.get('quotes', []):
                if item.get('quoteType') in ['EQUITY', 'ETF']:
                    results.append({"ticker": item['symbol'], "name": item.get('shortname') or item.get('longname'), "exchange": item.get('exchDisp','N/A')})
        except: pass
        return results

    @cached(ttl_seconds=300)
    def get_price_history(self, ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        if self.fmp_key and self._obb:
            try:
                # Mehr Daten laden für glatte Charts
                start_date = (pd.Timestamp.now() - pd.Timedelta(days=730 if period=='5y' else 365)).strftime("%Y-%m-%d")
                df = self._obb.equity.price.historical(symbol=ticker, start_date=start_date, interval=interval, provider="fmp").to_df()
                df.index.name = "date"
                return df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].dropna()
            except: pass
        
        # Yahoo Fallback
        import yfinance as yf
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        if df.empty: return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df.columns = [c.lower() for c in df.columns]
        if "adj close" in df.columns: df = df.rename(columns={"adj close": "close"})
        return df[["open", "high", "low", "close", "volume"]].dropna()

    @cached(ttl_seconds=60)
    def get_quote(self, ticker: str) -> dict:
        # 1. Versuch: FMP
        if self.fmp_key:
            try:
                url = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={self.fmp_key}"
                d = requests.get(url, timeout=3).json()[0]
                return {
                    "price": d.get("price"),
                    "change": d.get("change"),
                    "change_pct": d.get("changesPercentage", 0) / 100.0,
                    "volume": d.get("volume"),
                    "market_cap": d.get("marketCap"),
                    "pe_ratio": d.get("pe"),
                    "week_52_high": d.get("yearHigh"),
                    "week_52_low": d.get("yearLow"),
                }
            except: pass

        # 2. Versuch: Yahoo
        import yfinance as yf
        try:
            i = yf.Ticker(ticker).info
            price = i.get("currentPrice") or i.get("regularMarketPrice", 0)
            prev = i.get("regularMarketPreviousClose", price)
            change = price - prev
            change_pct = (change / prev) if prev else 0
            
            return {
                "price": price,
                "change": change,
                "change_pct": change_pct,
                "volume": i.get("volume"),
                "market_cap": i.get("marketCap"),
                "pe_ratio": i.get("trailingPE"),
                "week_52_high": i.get("fiftyTwoWeekHigh"),
                "week_52_low": i.get("fiftyTwoWeekLow"),
            }
        except:
            return {"price": 0, "change": 0, "change_pct": 0}

    # Dummy methods needed for other services
    def get_company_info(self, t): return {"name": t}
    def get_financials(self, t, type_): return pd.DataFrame()

_client = None
def get_client():
    global _client
    if not _client: _client = OpenBBClient()
    return _client