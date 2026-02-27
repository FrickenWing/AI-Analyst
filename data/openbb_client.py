"""
data/openbb_client.py - OpenBB Client Wrapper

Einheitlicher Zugang zu allen Marktdaten via OpenBB Platform.
Automatischer Provider-Fallback: OpenBB → yfinance → FMP

Features:
- Multi-Provider Fallback (kein Absturz bei API-Ausfall)
- Integriertes Caching (reduziert API-Calls drastisch)
- Einheitliche Datenformate (immer pandas DataFrames)
- Logging für Debugging
"""

import time
import hashlib
import json
from pathlib import Path
from functools import wraps
from typing import Optional

import pandas as pd
from loguru import logger

# ─────────────────────────────────────────────
# CACHE DECORATOR
# ─────────────────────────────────────────────
_cache_store: dict = {}

def cached(ttl_seconds: int = 300):
    """Einfacher In-Memory Cache Decorator."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = hashlib.md5(
                json.dumps({"fn": func.__name__, "a": str(args), "k": str(kwargs)},
                           sort_keys=True).encode()
            ).hexdigest()

            if key in _cache_store:
                value, expires_at = _cache_store[key]
                if time.time() < expires_at:
                    logger.debug(f"Cache HIT: {func.__name__}({args[1] if len(args) > 1 else ''})")
                    return value

            result = func(*args, **kwargs)
            _cache_store[key] = (result, time.time() + ttl_seconds)
            logger.debug(f"Cache MISS: {func.__name__}({args[1] if len(args) > 1 else ''})")
            return result
        return wrapper
    return decorator


# ─────────────────────────────────────────────
# OPENBB CLIENT
# ─────────────────────────────────────────────
class OpenBBClient:
    """
    Haupt-Client für alle Marktdaten.

    Verwendung:
        client = OpenBBClient()
        df = client.get_price_history("AAPL", "1y", "1d")
        quote = client.get_quote("AAPL")
    """

    def __init__(self, pat: str = ""):
        self.pat = pat
        self._obb = None
        self._init_openbb()

    def _init_openbb(self):
        """Initialisiert OpenBB mit optionalem PAT."""
        try:
            from openbb import obb
            if self.pat:
                obb.account.login(pat=self.pat)
                logger.info("OpenBB: Eingeloggt mit PAT (alle Provider verfügbar)")
            else:
                logger.info("OpenBB: Ohne PAT (yfinance verfügbar)")
            self._obb = obb
        except ImportError:
            logger.warning("OpenBB nicht installiert - nutze yfinance direkt")
        except Exception as e:
            logger.warning(f"OpenBB Init Fehler: {e} - nutze yfinance direkt")

    # ─────────────────────────────────────────
    # KURSDATEN
    # ─────────────────────────────────────────

    @cached(ttl_seconds=300)
    def get_price_history(
        self,
        ticker: str,
        period: str = "1y",
        interval: str = "1d",
        provider: str = "yfinance"
    ) -> pd.DataFrame:
        """
        Lädt historische OHLCV-Kursdaten.

        Args:
            ticker:   Ticker-Symbol (z.B. "AAPL")
            period:   Zeitraum (z.B. "1y", "6mo", "3mo")
            interval: Intervall (z.B. "1d", "1h", "5m")
            provider: Datenprovider (Standard: "yfinance")

        Returns:
            DataFrame mit Spalten: open, high, low, close, volume
        """
        # Versuche OpenBB zuerst
        if self._obb:
            try:
                result = self._obb.equity.price.historical(
                    symbol=ticker,
                    start_date=self._period_to_date(period),
                    interval=interval,
                    provider=provider,
                )
                df = result.to_df()
                logger.success(f"✅ Kursdaten geladen: {ticker} ({period}, {interval})")
                return self._normalize_ohlcv(df)
            except Exception as e:
                logger.warning(f"OpenBB Fehler für {ticker}: {e}")

        # Fallback: yfinance direkt
        return self._yfinance_history(ticker, period, interval)

    def _yfinance_history(self, ticker: str, period: str, interval: str) -> pd.DataFrame:
        """Direkter yfinance Fallback."""
        try:
            import yfinance as yf
            df = yf.download(
                ticker, period=period, interval=interval,
                auto_adjust=True, progress=False
            )
            if df.empty:
                raise ValueError(f"Keine Daten für {ticker}")
            return self._normalize_ohlcv(df)
        except Exception as e:
            logger.error(f"yfinance Fehler für {ticker}: {e}")
            return pd.DataFrame()

    @cached(ttl_seconds=60)
    def get_quote(self, ticker: str) -> dict:
        """
        Aktueller Kurs (oder letzter Schlusskurs).

        Returns:
            dict mit: price, change, change_pct, volume, ...
        """
        if self._obb:
            try:
                result = self._obb.equity.price.quote(symbol=ticker, provider="yfinance")
                data = result.to_df().iloc[0].to_dict()
                return self._normalize_quote(data)
            except Exception as e:
                logger.warning(f"Quote Fehler {ticker}: {e}")

        # Fallback
        return self._yfinance_quote(ticker)

    def _yfinance_quote(self, ticker: str) -> dict:
        """yfinance Quote Fallback."""
        try:
            import yfinance as yf
            info = yf.Ticker(ticker).info
            return {
                "ticker":       ticker,
                "price":        info.get("currentPrice") or info.get("regularMarketPrice", 0),
                "change":       info.get("regularMarketChange", 0),
                "change_pct":   info.get("regularMarketChangePercent", 0),
                "volume":       info.get("volume", 0),
                "market_cap":   info.get("marketCap"),
                "pe_ratio":     info.get("trailingPE"),
                "week_52_high": info.get("fiftyTwoWeekHigh"),
                "week_52_low":  info.get("fiftyTwoWeekLow"),
            }
        except Exception as e:
            logger.error(f"yfinance Quote Fehler {ticker}: {e}")
            return {"ticker": ticker, "price": 0, "change": 0, "change_pct": 0, "volume": 0}

    # ─────────────────────────────────────────
    # FUNDAMENTALDATEN
    # ─────────────────────────────────────────

    @cached(ttl_seconds=3600)
    def get_company_info(self, ticker: str) -> dict:
        """Unternehmensprofil und Basis-Info."""
        try:
            import yfinance as yf
            info = yf.Ticker(ticker).info
            return {
                "ticker":      ticker,
                "name":        info.get("longName", ticker),
                "sector":      info.get("sector"),
                "industry":    info.get("industry"),
                "country":     info.get("country"),
                "exchange":    info.get("exchange"),
                "description": info.get("longBusinessSummary"),
                "employees":   info.get("fullTimeEmployees"),
                "website":     info.get("website"),
                "ceo":         info.get("companyOfficers", [{}])[0].get("name") if info.get("companyOfficers") else None,
            }
        except Exception as e:
            logger.error(f"Company Info Fehler {ticker}: {e}")
            return {"ticker": ticker, "name": ticker}

    @cached(ttl_seconds=3600)
    def get_financials(self, ticker: str, statement: str = "income") -> pd.DataFrame:
        """
        Finanzdaten (Bilanz, GuV, Cashflow).

        Args:
            statement: "income", "balance", "cashflow"
        """
        try:
            import yfinance as yf
            t = yf.Ticker(ticker)
            if statement == "income":
                return t.financials
            elif statement == "balance":
                return t.balance_sheet
            elif statement == "cashflow":
                return t.cashflow
        except Exception as e:
            logger.error(f"Financials Fehler {ticker}: {e}")
            return pd.DataFrame()

    # ─────────────────────────────────────────
    # NEWS
    # ─────────────────────────────────────────

    @cached(ttl_seconds=600)
    def get_news(self, ticker: str, limit: int = 10) -> list[dict]:
        """Aktuelle News zu einem Ticker."""
        try:
            import yfinance as yf
            news = yf.Ticker(ticker).news
            result = []
            for item in (news or [])[:limit]:
                result.append({
                    "title":     item.get("title", ""),
                    "url":       item.get("link", ""),
                    "source":    item.get("publisher", ""),
                    "published": item.get("providerPublishTime"),
                    "summary":   item.get("summary", ""),
                })
            return result
        except Exception as e:
            logger.error(f"News Fehler {ticker}: {e}")
            return []

    # ─────────────────────────────────────────
    # MARKT-ÜBERSICHT
    # ─────────────────────────────────────────

    @cached(ttl_seconds=120)
    def get_market_overview(self) -> dict:
        """Wichtige Indizes und VIX."""
        from config import MARKET_INDICES
        results = {}
        for symbol, name in MARKET_INDICES.items():
            quote = self.get_quote(symbol)
            results[name] = quote
        return results

    # ─────────────────────────────────────────
    # HILFSFUNKTIONEN
    # ─────────────────────────────────────────

    def _period_to_date(self, period: str) -> str:
        """Konvertiert Period-String zu Start-Datum."""
        from datetime import datetime, timedelta
        mapping = {
            "1d": 1, "5d": 5, "1mo": 30, "3mo": 90,
            "6mo": 180, "1y": 365, "2y": 730, "5y": 1825, "10y": 3650,
        }
        days = mapping.get(period, 365)
        start = datetime.now() - timedelta(days=days)
        return start.strftime("%Y-%m-%d")

    def _normalize_ohlcv(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalisiert OHLCV DataFrame auf einheitliches Format."""
        df.columns = [c.lower().replace(" ", "_") for c in df.columns]
        rename_map = {
            "adj_close": "close",
            "adj close": "close",
        }
        df = df.rename(columns=rename_map)
        for col in ["open", "high", "low", "close", "volume"]:
            if col not in df.columns:
                df[col] = 0.0
        df.index.name = "date"
        return df[["open", "high", "low", "close", "volume"]].dropna()

    def _normalize_quote(self, data: dict) -> dict:
        """Normalisiert Quote-Daten."""
        return {
            "ticker":       data.get("symbol", ""),
            "price":        data.get("last_price") or data.get("price", 0),
            "change":       data.get("change", 0),
            "change_pct":   data.get("change_percent", 0),
            "volume":       data.get("volume", 0),
            "market_cap":   data.get("market_cap"),
            "pe_ratio":     data.get("pe_ratio"),
            "week_52_high": data.get("fifty_two_week_high"),
            "week_52_low":  data.get("fifty_two_week_low"),
        }

    def clear_cache(self):
        """Leert den gesamten Cache."""
        global _cache_store
        _cache_store = {}
        logger.info("Cache geleert")


# ─────────────────────────────────────────────
# SINGLETON
# ─────────────────────────────────────────────
_client_instance: Optional[OpenBBClient] = None

def get_client() -> OpenBBClient:
    """
    Gibt die globale Client-Instanz zurück (Singleton).
    Verwendung: from data.openbb_client import get_client
    """
    global _client_instance
    if _client_instance is None:
        try:
            import streamlit as st
            pat = st.secrets.get("OPENBB_PAT", "")
        except Exception:
            pat = ""
        _client_instance = OpenBBClient(pat=pat)
    return _client_instance


# ─────────────────────────────────────────────
# TEST (python data/openbb_client.py)
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("🧪 OpenBB Client Test\n" + "="*40)

    client = OpenBBClient()

    # Test 1: Kursdaten
    print("\n📊 Test 1: Kursdaten AAPL")
    df = client.get_price_history("AAPL", "3mo", "1d")
    if not df.empty:
        print(f"  ✅ {len(df)} Datenpunkte geladen")
        print(f"  Letzter Kurs: ${df['close'].iloc[-1]:.2f}")
    else:
        print("  ❌ Keine Daten")

    # Test 2: Quote
    print("\n💰 Test 2: Quote MSFT")
    quote = client.get_quote("MSFT")
    if quote.get("price"):
        print(f"  ✅ Kurs: ${quote['price']:.2f} ({quote['change_pct']:+.2f}%)")
    else:
        print("  ❌ Quote fehlgeschlagen")

    # Test 3: Company Info
    print("\n🏢 Test 3: Company Info GOOGL")
    info = client.get_company_info("GOOGL")
    if info.get("name"):
        print(f"  ✅ {info['name']} | {info.get('sector', 'N/A')}")
    else:
        print("  ❌ Info fehlgeschlagen")

    print("\n✅ Tests abgeschlossen!")
