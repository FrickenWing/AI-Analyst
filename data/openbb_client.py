import time
import hashlib
import json
import requests
import pandas as pd
import streamlit as st
import yfinance as yf
import xml.etree.ElementTree as ET
from functools import wraps
from loguru import logger

# Cache Speicher
_cache_store: dict = {}

def cached(ttl_seconds: int = 300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key_parts = [func.__name__, str(args), str(kwargs)]
            key = hashlib.md5(json.dumps(key_parts, sort_keys=True, default=str).encode()).hexdigest()
            
            if key in _cache_store:
                val, exp = _cache_store[key]
                if time.time() < exp:
                    return val
            
            try:
                res = func(*args, **kwargs)
                if res is not None:
                    _cache_store[key] = (res, time.time() + ttl_seconds)
                return res
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                return None
        return wrapper
    return decorator

class OpenBBClient:
    def __init__(self):
        self.fmp_key = st.secrets.get("FMP_API_KEY", "")
        # Standard Header um wie ein Browser auszusehen (verhindert 403 Errors)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def clear_cache(self):
        global _cache_store
        _cache_store.clear()
        st.cache_data.clear()

    @cached(ttl_seconds=3600)
    def search_ticker(self, query: str) -> list:
        if not query: return []
        results = []
        try:
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=10"
            data = requests.get(url, headers=self.headers, timeout=4).json()
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
        try:
            df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True, multi_level_index=False)
            if df.empty: return pd.DataFrame()
            df.columns = [c.lower() for c in df.columns]
            return df[["open", "high", "low", "close", "volume"]].dropna()
        except:
            return pd.DataFrame()

    @cached(ttl_seconds=60)
    def get_quote(self, ticker: str) -> dict:
        try:
            t = yf.Ticker(ticker)
            fi = t.fast_info
            i = t.info
            price = fi.last_price if fi.last_price else i.get("currentPrice", 0)
            prev = fi.previous_close if fi.previous_close else i.get("regularMarketPreviousClose", price)
            change = price - prev
            pct = (change / prev) if prev else 0
            
            return {
                "price": price,
                "change": change,
                "change_pct": pct,
                "volume": i.get("volume"),
                "market_cap": i.get("marketCap"),
                "pe_ratio": i.get("trailingPE"),
                "beta": i.get("beta"),
                "week_52_high": i.get("fiftyTwoWeekHigh"),
                "week_52_low": i.get("fiftyTwoWeekLow"),
                "name": i.get("shortName"),
                "exchange": i.get("exchange"),
                "sector": i.get("sector"),
                "industry": i.get("industry"),
                "description": i.get("longBusinessSummary"),
                "website": i.get("website"),
                "currency": i.get("currency", "USD"),
            }
        except: return {}

    @cached(ttl_seconds=3600)
    def get_news(self, ticker: str, limit: int = 10) -> list:
        """
        Holt News via RSS (US-Englisch) mit Fallback auf yfinance API
        """
        news_items = []
        
        # 1. Versuch: Yahoo RSS (Erzwingt Englisch via URL-Parameter)
        try:
            # WICHTIG: User-Agent Header mitsenden, sonst blockt Yahoo!
            url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
            resp = requests.get(url, headers=self.headers, timeout=5)
            
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                for item in root.findall('./channel/item')[:limit]:
                    news_items.append({
                        "title": item.find('title').text,
                        "url": item.find('link').text,
                        "source": "Yahoo Finance", 
                        "published": item.find('pubDate').text, 
                        "image": None
                    })
        except Exception as e:
            logger.error(f"RSS News Error: {e}")

        # 2. Versuch: yfinance Fallback (Falls RSS leer oder Fehler)
        if not news_items:
            try:
                t = yf.Ticker(ticker)
                # yfinance news ist robuster, aber manchmal lokalisiert
                for item in t.news[:limit]:
                    news_items.append({
                        "title": item.get("title"),
                        "url": item.get("link"),
                        "source": item.get("publisher"),
                        "published": str(pd.to_datetime(item.get("providerPublishTime"), unit='s')),
                        "image": None
                    })
            except Exception as e:
                logger.error(f"YF News Fallback Error: {e}")
            
        return news_items

    @cached(ttl_seconds=3600*12)
    def get_financials(self, ticker: str) -> dict:
        # FMP Bevorzugt
        if self.fmp_key:
            try:
                out = {}
                res = requests.get(f"https://financialmodelingprep.com/api/v3/income-statement/{ticker}?limit=5&apikey={self.fmp_key}").json()
                if isinstance(res, list):
                    df = pd.DataFrame(res).set_index("calendarYear")
                    out["income"] = df[["revenue","netIncome","operatingIncome","eps"]].T
                
                res = requests.get(f"https://financialmodelingprep.com/api/v3/balance-sheet-statement/{ticker}?limit=5&apikey={self.fmp_key}").json()
                if isinstance(res, list):
                    df = pd.DataFrame(res).set_index("calendarYear")
                    out["balance"] = df[["totalAssets","totalLiabilities","totalStockholdersEquity","cashAndCashEquivalents"]].T

                if out: return out
            except: pass

        # Yahoo Fallback
        try:
            t = yf.Ticker(ticker)
            def clean(df):
                if df is None or df.empty: return pd.DataFrame()
                df.columns = [str(c)[:4] for c in df.columns] 
                return df

            return {
                "income": clean(t.income_stmt),
                "balance": clean(t.balance_sheet),
                "cashflow": clean(t.cashflow)
            }
        except:
            return {"income": pd.DataFrame(), "balance": pd.DataFrame(), "cashflow": pd.DataFrame()}

    @cached(ttl_seconds=3600*12)
    def get_analyst_info(self, ticker: str) -> dict:
        try:
            t = yf.Ticker(ticker)
            i = t.info
            current = i.get("currentPrice", 1)
            target = i.get("targetMeanPrice")
            return {
                "recommendation": i.get("recommendationKey", "Hold").replace("_", " ").title(),
                "target_mean": target,
                "target_high": i.get("targetHighPrice"),
                "target_low": i.get("targetLowPrice"),
                "fmt_target": f"{target} {i.get('currency','USD')}" if target else "N/A",
                "fmt_upside": f"{((target/current)-1):.1%}" if target and current else "N/A"
            }
        except: return {}

    @cached(ttl_seconds=3600)
    def get_key_stats(self, ticker: str) -> dict:
        try:
            t = yf.Ticker(ticker)
            i = t.info
            
            def fmt(val, is_pct=False):
                if val is None: return "-"
                if is_pct: return f"{val:.2%}" if val < 5 else f"{val * 100:.2f}%"
                return f"{val:.2f}"

            return {
                "Valuation": {
                    "Market Cap": i.get("marketCap"),
                    "Enterprise Value": i.get("enterpriseValue"),
                    "Trailing P/E": fmt(i.get("trailingPE")),
                    "Forward P/E": fmt(i.get("forwardPE")),
                    "PEG Ratio": fmt(i.get("pegRatio")),
                    "Price/Sales": fmt(i.get("priceToSalesTrailing12Months")),
                    "Price/Book": fmt(i.get("priceToBook")),
                },
                "Profitability": {
                    "Profit Margin": fmt(i.get("profitMargins"), True),
                    "Operating Margin": fmt(i.get("operatingMargins"), True),
                    "Return on Assets": fmt(i.get("returnOnAssets"), True),
                    "Return on Equity": fmt(i.get("returnOnEquity"), True),
                    "Revenue (ttm)": i.get("totalRevenue"),
                    "Gross Profit": i.get("grossProfits"),
                },
                "Balance Sheet": {
                    "Total Cash": i.get("totalCash"),
                    "Total Debt": i.get("totalDebt"),
                    "Current Ratio": fmt(i.get("currentRatio")),
                    "Quick Ratio": fmt(i.get("quickRatio")),
                    "Book Value": fmt(i.get("bookValue")),
                },
                "Trading Info": {
                    "Beta": fmt(i.get("beta")),
                    "Short Ratio": fmt(i.get("shortRatio")),
                    "Shares Out": i.get("sharesOutstanding"),
                    "Float": i.get("floatShares"),
                    "Insiders": fmt(i.get("heldPercentInsiders"), True),
                    "Institutions": fmt(i.get("heldPercentInstitutions"), True),
                }
            }
        except Exception as e:
            logger.error(f"Stats Error: {e}")
            return {}

_client = None
def get_client():
    global _client
    if not _client:
        _client = OpenBBClient()
    return _client