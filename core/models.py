"""
core/models.py - Pydantic Data Models

Alle Datenstrukturen des Projekts.
Type Safety, automatische Validierung, IDE Autocomplete.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator


# ─────────────────────────────────────────────
# MARKT-DATEN MODELS
# ─────────────────────────────────────────────

class OHLCVData(BaseModel):
    """OHLCV Kerzendaten für einen Zeitpunkt."""
    timestamp: datetime
    open:      float
    high:      float
    low:       float
    close:     float
    volume:    float
    vwap:      Optional[float] = None

    @validator("high")
    def high_must_be_max(cls, v, values):
        if "low" in values and v < values["low"]:
            raise ValueError("High muss >= Low sein")
        return v


class StockQuote(BaseModel):
    """Aktueller Kurs eines Wertpapiers."""
    ticker:         str
    price:          float
    change:         float        # Absolute Änderung
    change_pct:     float        # Prozentuale Änderung
    volume:         int
    avg_volume:     Optional[int] = None
    market_cap:     Optional[float] = None
    pe_ratio:       Optional[float] = None
    week_52_high:   Optional[float] = None
    week_52_low:    Optional[float] = None
    timestamp:      datetime = Field(default_factory=datetime.now)

    @property
    def is_positive(self) -> bool:
        return self.change >= 0


class CompanyProfile(BaseModel):
    """Unternehmensprofil."""
    ticker:         str
    name:           str
    sector:         Optional[str] = None
    industry:       Optional[str] = None
    country:        Optional[str] = None
    exchange:       Optional[str] = None
    currency:       str = "USD"
    description:    Optional[str] = None
    employees:      Optional[int] = None
    website:        Optional[str] = None
    ceo:            Optional[str] = None
    ipo_date:       Optional[str] = None


# ─────────────────────────────────────────────
# FUNDAMENTALDATEN MODELS
# ─────────────────────────────────────────────

class IncomeStatement(BaseModel):
    """Gewinn- und Verlustrechnung."""
    ticker:               str
    period:               str           # "annual" oder "quarterly"
    date:                 str
    revenue:              Optional[float] = None
    gross_profit:         Optional[float] = None
    operating_income:     Optional[float] = None
    net_income:           Optional[float] = None
    ebitda:               Optional[float] = None
    eps:                  Optional[float] = None
    eps_diluted:          Optional[float] = None

    @property
    def gross_margin(self) -> Optional[float]:
        if self.revenue and self.gross_profit:
            return self.gross_profit / self.revenue
        return None

    @property
    def net_margin(self) -> Optional[float]:
        if self.revenue and self.net_income:
            return self.net_income / self.revenue
        return None


class KeyMetrics(BaseModel):
    """Kennzahlen eines Unternehmens."""
    ticker:                str
    date:                  str
    market_cap:            Optional[float] = None
    pe_ratio:              Optional[float] = None
    pb_ratio:              Optional[float] = None
    ps_ratio:              Optional[float] = None
    ev_ebitda:             Optional[float] = None
    debt_to_equity:        Optional[float] = None
    current_ratio:         Optional[float] = None
    roe:                   Optional[float] = None
    roa:                   Optional[float] = None
    revenue_growth:        Optional[float] = None
    earnings_growth:       Optional[float] = None
    dividend_yield:        Optional[float] = None
    payout_ratio:          Optional[float] = None


# ─────────────────────────────────────────────
# SCREENER MODELS
# ─────────────────────────────────────────────

class ScreenerFilter(BaseModel):
    """Filter-Kriterien für den Screener."""
    # Bewertung
    pe_min:         Optional[float] = None
    pe_max:         Optional[float] = None
    pb_min:         Optional[float] = None
    pb_max:         Optional[float] = None
    # Wachstum
    rev_growth_min: Optional[float] = None
    eps_growth_min: Optional[float] = None
    # Profitabilität
    roe_min:        Optional[float] = None
    margin_min:     Optional[float] = None
    # Technisch
    rsi_min:        Optional[float] = None
    rsi_max:        Optional[float] = None
    above_sma200:   Optional[bool] = None
    # Volumen
    min_volume:     Optional[int] = None
    # Sektor
    sectors:        Optional[list[str]] = None


class ScreenerResult(BaseModel):
    """Einzelnes Screening-Ergebnis."""
    ticker:         str
    name:           str
    sector:         Optional[str] = None
    price:          float
    change_pct:     float
    market_cap:     Optional[float] = None
    pe_ratio:       Optional[float] = None
    rsi:            Optional[float] = None
    score:          Optional[float] = None   # Composite Score 0-100


# ─────────────────────────────────────────────
# PORTFOLIO MODELS
# ─────────────────────────────────────────────

class Position(BaseModel):
    """Eine Portfolio-Position."""
    ticker:         str
    name:           Optional[str] = None
    quantity:       float
    avg_price:      float
    current_price:  Optional[float] = None
    purchase_date:  Optional[str] = None

    @property
    def market_value(self) -> Optional[float]:
        if self.current_price:
            return self.quantity * self.current_price
        return None

    @property
    def pnl(self) -> Optional[float]:
        if self.current_price:
            return (self.current_price - self.avg_price) * self.quantity
        return None

    @property
    def pnl_pct(self) -> Optional[float]:
        if self.current_price:
            return (self.current_price - self.avg_price) / self.avg_price
        return None


class Portfolio(BaseModel):
    """Komplettes Portfolio."""
    name:       str = "Mein Portfolio"
    positions:  list[Position] = []
    cash:       float = 0.0

    @property
    def total_value(self) -> float:
        values = [p.market_value or 0 for p in self.positions]
        return sum(values) + self.cash

    @property
    def total_pnl(self) -> float:
        return sum(p.pnl or 0 for p in self.positions)


# ─────────────────────────────────────────────
# NEWS MODEL
# ─────────────────────────────────────────────

class NewsItem(BaseModel):
    """Eine News-Meldung."""
    title:      str
    url:        str
    source:     Optional[str] = None
    published:  Optional[datetime] = None
    summary:    Optional[str] = None
    tickers:    Optional[list[str]] = None
    sentiment:  Optional[str] = None   # "positive", "negative", "neutral"
