"""
tests/test_openbb_client.py - Tests für OpenBB Client & Indikatoren

Führe aus mit: pytest tests/test_openbb_client.py -v
"""

import pytest
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.openbb_client import OpenBBClient
from indicators.technical import TechnicalIndicators


@pytest.fixture
def client():
    return OpenBBClient(pat="")


class TestPriceHistory:
    def test_returns_dataframe(self, client):
        df = client.get_price_history("AAPL", "1mo", "1d")
        assert isinstance(df, pd.DataFrame) and not df.empty

    def test_has_ohlcv_columns(self, client):
        df = client.get_price_history("AAPL", "1mo", "1d")
        for col in ["open", "high", "low", "close", "volume"]:
            assert col in df.columns

    def test_high_gte_low(self, client):
        df = client.get_price_history("AAPL", "1mo", "1d")
        assert (df["high"] >= df["low"]).all()

    def test_invalid_ticker(self, client):
        df = client.get_price_history("INVALID_XYZ_999", "1mo", "1d")
        assert isinstance(df, pd.DataFrame)


class TestQuote:
    def test_has_price(self, client):
        quote = client.get_quote("MSFT")
        assert quote.get("price", 0) > 0

    def test_required_fields(self, client):
        quote = client.get_quote("AAPL")
        for field in ["ticker", "price", "change", "change_pct", "volume"]:
            assert field in quote


class TestCaching:
    def test_second_call_consistent(self, client):
        q1 = client.get_quote("AAPL")
        q2 = client.get_quote("AAPL")
        assert q1["price"] == q2["price"]

    def test_clear_cache(self, client):
        client.clear_cache()  # kein Fehler


class TestIndicators:
    def test_sma(self, client):
        df = client.get_price_history("AAPL", "6mo", "1d")
        ti = TechnicalIndicators(df)
        ti.add_sma([20])
        assert "sma_20" in ti.df.columns

    def test_rsi_range(self, client):
        df = client.get_price_history("AAPL", "6mo", "1d")
        ti = TechnicalIndicators(df)
        ti.add_rsi()
        rsi = ti.df["rsi"].dropna()
        assert (rsi >= 0).all() and (rsi <= 100).all()

    def test_macd_columns(self, client):
        df = client.get_price_history("AAPL", "1y", "1d")
        ti = TechnicalIndicators(df)
        ti.add_macd()
        for col in ["macd", "macd_signal", "macd_hist"]:
            assert col in ti.df.columns

    def test_bollinger_bands(self, client):
        df = client.get_price_history("AAPL", "6mo", "1d")
        ti = TechnicalIndicators(df)
        ti.add_bollinger_bands()
        bb_upper = ti.df["bb_upper"].dropna()
        bb_lower = ti.df["bb_lower"].dropna()
        assert (bb_upper >= bb_lower).all()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
