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
            # Erstelle einen eindeutigen Key basierend auf Funktionsname und Argumenten
            key_parts = [func.__name__, str(args), str(kwargs)]
            key = hashlib.md5(json.dumps(key_parts, sort_keys=True, default=str).encode()).hexdigest()
            
            # Prüfe Cache
            if key in _cache_store:
                val, exp = _cache_store[key]
                if time.time() < exp:
                    return val
            
            # Führe Funktion aus
            try:
                res = func(*args, **kwargs)
                # Speichere im Cache nur wenn Ergebnis gültig (nicht None/Leer bei Fehlern)
                if res is not None:
                    _cache_store[key] = (res, time.time() + ttl_seconds)
                return res
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                return None # Oder leeres Ergebnis
        return wrapper
    return decorator

class OpenBBClient:
    def __init__(self):
        self.fmp_key = st.secrets.get("FMP_API_KEY", "")
        self._obb = None
        # Versuch OpenBB zu laden, falls installiert
        try:
            from openbb import obb
            if self.fmp_key:
                obb.user.credentials.fmp_api_key = self.fmp_key
            self._obb = obb
        except:
            pass

    def clear_cache(self):
        """Leert den internen Cache komplett."""
        global _cache_store
        _cache_store.clear()
        st.cache_data.clear()

    @cached(ttl_seconds=3600)
    def search_ticker(self, query: str) -> list:
        if not query: return []
        results = []
        
        # 1. FMP Search
        if self.fmp_key:
            try:
                url = f"https://financialmodelingprep.com/api/v3/search?query={query}&limit=10&apikey={self.fmp_key}"
                data = requests.get(url, timeout=3).json()
                for item in data:
                    results.append({
                        "ticker": item['symbol'], 
                        "name": item['name'], 
                        "exchange": item.get('exchangeShortName','N/A')
                    })
                return results
            except: pass
            
        # 2. Yahoo Fallback
        try:
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=5"
            headers = {'User-Agent': 'Mozilla/5.0'}
            data = requests.get(url, headers=headers, timeout=3).json()
            for item in data.get('quotes', []):
                if item.get('quoteType') in ['EQUITY', 'ETF']:
                    results.append({
                        "ticker": item['symbol'], 
                        "name": item.get('shortname') or item.get('longname'), 
                        "exchange": item.get('exchDisp','N/A')
                    })
        except: pass
        
        return results

    @cached(ttl_seconds=300)
    def get_price_history(self, ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        # FMP via OpenBB
        if self.fmp_key and self._obb:
            try:
                start_date = (pd.Timestamp.now() - pd.Timedelta(days=730 if period=='5y' else 365)).strftime("%Y-%m-%d")
                df = self._obb.equity.price.historical(symbol=ticker, start_date=start_date, interval=interval, provider="fmp").to_df()
                df.index.name = "date"
                return df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].dropna()
            except: pass
        
        # Yahoo Fallback
        import yfinance as yf
        try:
            df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
            if df.empty: return pd.DataFrame()
            # MultiIndex bereinigen falls nötig
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df.columns = [c.lower() for c in df.columns]
            if "adj close" in df.columns:
                df = df.rename(columns={"adj close": "close"})
            
            cols = [c for c in ["open", "high", "low", "close", "volume"] if c in df.columns]
            return df[cols].dropna()
        except:
            return pd.DataFrame()

    @cached(ttl_seconds=60)
    def get_quote(self, ticker: str) -> dict:
        # 1. FMP
        if self.fmp_key:
            try:
                url = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={self.fmp_key}"
                res = requests.get(url, timeout=3).json()
                if res:
                    d = res[0]
                    return {
                        "price": d.get("price"),
                        "change": d.get("change"),
                        "change_pct": d.get("changesPercentage", 0) / 100.0,
                        "volume": d.get("volume"),
                        "market_cap": d.get("marketCap"),
                        "pe_ratio": d.get("pe"),
                        "week_52_high": d.get("yearHigh"),
                        "week_52_low": d.get("yearLow"),
                        "name": d.get("name"),
                        "exchange": d.get("exchange"),
                    }
            except: pass

        # 2. Yahoo
        import yfinance as yf
        try:
            t = yf.Ticker(ticker)
            i = t.info
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
                "name": i.get("shortName"),
                "exchange": i.get("exchange"),
            }
        except:
            return {"price": 0, "change": 0, "change_pct": 0}

    @cached(ttl_seconds=3600)
    def get_news(self, ticker: str, limit: int = 5) -> list:
        """Hole Nachrichten zu einem Ticker (FMP oder Yahoo)"""
        news_items = []
        
        # 1. Versuch: FMP
        if self.fmp_key:
            try:
                url = f"https://financialmodelingprep.com/api/v3/stock_news?tickers={ticker}&limit={limit}&apikey={self.fmp_key}"
                data = requests.get(url, timeout=4).json()
                for item in data:
                    news_items.append({
                        "title": item.get("title"),
                        "url": item.get("url"),
                        "source": item.get("site"),
                        "published": item.get("publishedDate"), # Format: YYYY-MM-DD HH:MM:SS
                        "summary": item.get("text"),
                        "image": item.get("image")
                    })
                return news_items
            except Exception as e:
                logger.error(f"FMP News Error: {e}")

        # 2. Versuch: Yahoo Finance
        try:
            import yfinance as yf
            t = yf.Ticker(ticker)
            ynews = t.news
            for item in ynews[:limit]:
                # Yahoo liefert Zeitstempel oft als Epoch
                pub = item.get("providerPublishTime")
                news_items.append({
                    "title": item.get("title"),
                    "url": item.get("link"),
                    "source": item.get("publisher"),
                    "published": pub, 
                    "summary": "Mehr auf Yahoo Finance lesen...", # Yahoo liefert oft keine Summary im Free Tier
                    "image": None
                })
        except Exception as e:
             logger.error(f"Yahoo News Error: {e}")
             
        return news_items

    # Dummy methods für Kompatibilität
    def get_company_info(self, t): return {"name": t}
    def get_financials(self, t, type_): return pd.DataFrame()

_client = None
def get_client():
    global _client
    if not _client:
        _client = OpenBBClient()
    return _client