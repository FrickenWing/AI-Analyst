"""
indicators/technical.py - Technische Indikatoren via Pandas/Numpy
"""
import pandas as pd
import numpy as np

class TechnicalIndicators:
    def __init__(self, df: pd.DataFrame):
        # Wir arbeiten auf einer Kopie, um Warnungen zu vermeiden
        self._df = df.copy()

    @property
    def df(self) -> pd.DataFrame:
        """Gibt das modifizierte DataFrame zurück."""
        return self._df

    def add_sma(self, periods: list = [20, 50, 200]):
        """Simple Moving Average (SMA)"""
        for p in periods:
            self._df[f'sma_{p}'] = self._df['close'].rolling(window=p).mean()
        return self

    def add_ema(self, periods: list = [9, 21]):
        """Exponential Moving Average (EMA)"""
        for p in periods:
            self._df[f'ema_{p}'] = self._df['close'].ewm(span=p, adjust=False).mean()
        return self

    def add_rsi(self, period: int = 14):
        """Relative Strength Index (RSI)"""
        delta = self._df['close'].diff()
        gain = delta.clip(lower=0).ewm(alpha=1/period, adjust=False).mean()
        loss = (-delta.clip(upper=0)).ewm(alpha=1/period, adjust=False).mean()
        rs = gain / loss
        self._df['rsi'] = 100 - (100 / (1 + rs))
        return self

    def add_macd(self, fast: int = 12, slow: int = 26, signal: int = 9):
        """Moving Average Convergence Divergence (MACD)"""
        ema_fast = self._df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = self._df['close'].ewm(span=slow, adjust=False).mean()
        self._df['macd'] = ema_fast - ema_slow
        self._df['macd_signal'] = self._df['macd'].ewm(span=signal, adjust=False).mean()
        self._df['macd_hist'] = self._df['macd'] - self._df['macd_signal']
        return self

    def add_bollinger_bands(self, period: int = 20, std: int = 2):
        """Bollinger Bands"""
        sma = self._df['close'].rolling(window=period).mean()
        std_dev = self._df['close'].rolling(window=period).std()
        self._df['bb_middle'] = sma
        self._df['bb_upper'] = sma + (std_dev * std)
        self._df['bb_lower'] = sma - (std_dev * std)
        return self

    def add_atr(self, period: int = 14):
        """Average True Range (ATR)"""
        high_low = self._df['high'] - self._df['low']
        high_close = np.abs(self._df['high'] - self._df['close'].shift())
        low_close = np.abs(self._df['low'] - self._df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        self._df['atr'] = tr.rolling(window=period).mean()
        return self

    def add_obv(self):
        """On-Balance Volume (OBV)"""
        obv = (np.sign(self._df['close'].diff()) * self._df['volume']).fillna(0).cumsum()
        self._df['obv'] = obv
        return self

    def add_volume_ma(self, period: int = 20):
        """Volume Moving Average"""
        self._df['volume_ma'] = self._df['volume'].rolling(window=period).mean()
        return self

    def add_vwap(self):
        """Volume Weighted Average Price (VWAP)"""
        tp = (self._df['high'] + self._df['low'] + self._df['close']) / 3
        self._df['vwap'] = (tp * self._df['volume']).cumsum() / self._df['volume'].cumsum()
        return self