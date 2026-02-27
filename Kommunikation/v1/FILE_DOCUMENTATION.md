# 📚 File Documentation - OpenBB Terminal Pro

**Zweck:** Detaillierte Dokumentation jeder Datei im Projekt  
**Für wen:** Entwickler die verstehen wollen was wo ist  
**Update:** Nach jeder neuen Datei aktualisieren

---

## 📁 Root-Level Dateien

### 📄 app.py
**Status:** ⏳ Noch nicht erstellt  
**Pfad:** `/openbb_terminal_pro/app.py`  
**Typ:** Streamlit Multi-Page App (Main Entry Point)

**Zweck:**
- Haupteinstiegspunkt der Applikation
- Navigation zwischen verschiedenen Seiten
- Sidebar mit Watchlists & Settings
- Session State Management

**Dependencies:**
- streamlit
- config.py (Settings laden)
- ui/components/sidebar.py (Sidebar Komponenten)

**Wichtige Funktionen:**
```python
def main():
    """Hauptfunktion - startet die App"""
    
def render_sidebar():
    """Rendert die Sidebar mit Navigation"""
    
def load_session_state():
    """Lädt Session State für User-Einstellungen"""
```

**Wie starten:**
```bash
streamlit run app.py
```

**Wichtig zu wissen:**
- Nutzt Streamlit's Multi-Page Feature
- Pages sind in ui/pages/ organisiert
- Session State wird hier initialisiert
- Sidebar ist auf allen Pages sichtbar

---

### 📄 config.py
**Status:** ⏳ Noch nicht erstellt  
**Pfad:** `/openbb_terminal_pro/config.py`  
**Typ:** Configuration Module

**Zweck:**
- Zentrale Konfiguration für alle Module
- Feature Flags (Features ein/ausschalten)
- Constants & Defaults
- Provider-Settings

**Beinhaltet:**
```python
class AppConfig:
    """Haupt-Konfiguration"""
    
    # App Settings
    APP_NAME = "OpenBB Terminal Pro"
    VERSION = "0.1.0"
    
    # Feature Flags
    ENABLE_AI_ANALYST = True
    ENABLE_OPTIONS = True
    
    # Data Settings
    DEFAULT_TIMEFRAME = "1y"
    CACHE_TTL = 300  # 5 Minuten
    
    # UI Settings
    THEME = "dark"
    CHART_HEIGHT = 600
    
    # Provider Priority
    PROVIDER_PRIORITY = ["yfinance", "fmp", "polygon"]

class Timeframes:
    """Verfügbare Timeframes"""
    OPTIONS = {
        "1D": "1d",
        "1W": "5d",
        "1M": "1mo",
        "3M": "3mo",
        "6M": "6mo",
        "1Y": "1y",
        "5Y": "5y",
        "Max": "max"
    }

class Watchlists:
    """Vordefinierte Watchlists"""
    TECH_GIANTS = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
    DAX_TOP10 = ["SAP.DE", "SIE.DE", "ALV.DE", ...]
    ...
```

**Wie nutzen:**
```python
from config import AppConfig, Timeframes

cache_ttl = AppConfig.CACHE_TTL
timeframes = Timeframes.OPTIONS
```

---

### 📄 requirements.txt
**Status:** ⏳ Noch nicht erstellt  
**Pfad:** `/openbb_terminal_pro/requirements.txt`  
**Typ:** Python Dependencies

**Zweck:**
- Liste aller Python-Packages
- Versions-Management
- Reproduzierbare Umgebung

**Inhalt:**
```txt
# Core
openbb>=4.0.0
streamlit>=1.30.0
pandas>=2.1.0
numpy>=1.24.0

# Charting
plotly>=5.18.0
matplotlib>=3.8.0

# Technical Analysis
pandas-ta>=0.3.14b
ta-lib>=0.4.28  # Optional

# Data Validation
pydantic>=2.5.0

# AI/ML
google-generativeai>=0.3.0  # Optional
anthropic>=0.8.0  # Optional

# Utilities
python-dotenv>=1.0.0
loguru>=0.7.0
```

**Wie installieren:**
```bash
pip install -r requirements.txt
```

---

## 📂 core/ - Domain Layer

### 📄 core/models.py
**Status:** ⏳ Noch nicht erstellt  
**Zweck:** Pydantic Data Models für Type Safety

**Wichtige Models:**
```python
class StockQuote(BaseModel):
    """Live Stock Quote"""
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int
    timestamp: datetime

class HistoricalData(BaseModel):
    """Historical OHLCV Data"""
    symbol: str
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

class CompanyProfile(BaseModel):
    """Company Information"""
    symbol: str
    name: str
    sector: str
    industry: str
    market_cap: float
    description: str
    website: str
    ceo: str

class FinancialMetrics(BaseModel):
    """Key Financial Metrics"""
    symbol: str
    pe_ratio: float
    pb_ratio: float
    roe: float
    debt_to_equity: float
    dividend_yield: float
```

**Wie nutzen:**
```python
from core.models import StockQuote

quote = StockQuote(
    symbol="AAPL",
    price=273.71,
    change=2.50,
    change_percent=0.92,
    volume=50000000,
    timestamp=datetime.now()
)
```

---

### 📄 core/constants.py
**Status:** ⏳ Noch nicht erstellt  
**Zweck:** Constants & Enums

**Inhalt:**
```python
from enum import Enum

class AssetType(Enum):
    """Asset Types"""
    STOCK = "stock"
    ETF = "etf"
    CRYPTO = "crypto"
    FOREX = "forex"
    INDEX = "index"

class Interval(Enum):
    """Chart Intervals"""
    MIN_1 = "1m"
    MIN_5 = "5m"
    MIN_15 = "15m"
    HOUR_1 = "1h"
    DAY_1 = "1d"
    WEEK_1 = "1wk"
    MONTH_1 = "1mo"

class IndicatorType(Enum):
    """Technical Indicator Categories"""
    TREND = "trend"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    VOLUME = "volume"

# Market Hours
MARKET_OPEN = time(9, 30)
MARKET_CLOSE = time(16, 0)

# Limits
MAX_SCREENER_RESULTS = 100
MAX_CHART_INDICATORS = 10
```

---

### 📄 core/exceptions.py
**Status:** ⏳ Noch nicht erstellt  
**Zweck:** Custom Exception Classes

**Exceptions:**
```python
class OpenBBTerminalException(Exception):
    """Base Exception"""
    pass

class DataNotFoundError(OpenBBTerminalException):
    """Data konnte nicht gefunden werden"""
    pass

class APIRateLimitError(OpenBBTerminalException):
    """API Rate Limit erreicht"""
    pass

class InvalidSymbolError(OpenBBTerminalException):
    """Symbol ist ungültig"""
    pass

class ProviderError(OpenBBTerminalException):
    """Provider-spezifischer Fehler"""
    pass
```

**Wie nutzen:**
```python
from core.exceptions import DataNotFoundError

def get_data(symbol):
    if not data_exists(symbol):
        raise DataNotFoundError(f"No data for {symbol}")
```

---

## 📂 data/ - Infrastructure Layer

### 📄 data/openbb_client.py
**Status:** ✅ FERTIG!  
**Zweck:** OpenBB API Wrapper mit Caching & Fallback

**Siehe separate Datei für Details - bereits erstellt und funktioniert!**

**Hauptfunktionen:**
- `get_historical_data()` - Historische Preise
- `get_company_profile()` - Firmeninformationen
- `get_financials()` - Financial Statements
- `get_key_metrics()` - Key Metrics
- `get_company_news()` - News
- `get_options_chains()` - Options Data
- `get_treasury_yields()` - Macro Data
- Und 20+ weitere...

**Multi-Provider Fallback:**
- Versucht Provider in Reihenfolge
- Automatischer Fallback bei Fehler
- Logging für Debugging

---

### 📄 data/cache_manager.py
**Status:** ⏳ Noch nicht erstellt  
**Zweck:** Intelligentes Caching-System

**Features:**
- Multi-Level Caching (Memory + Disk)
- TTL-basiertes Expiry
- Cache Invalidation
- Cache Statistics

**Wichtige Funktionen:**
```python
class CacheManager:
    def get(self, key: str) -> Any:
        """Holt Wert aus Cache"""
        
    def set(self, key: str, value: Any, ttl: int):
        """Speichert Wert in Cache"""
        
    def invalidate(self, key: str):
        """Invalidiert Cache-Eintrag"""
        
    def clear_all(self):
        """Löscht kompletten Cache"""
        
    def get_stats(self) -> Dict:
        """Gibt Cache-Statistiken"""
```

---

## 📂 indicators/ - Technical Analysis

### 📄 indicators/technical.py
**Status:** ⏳ Noch nicht erstellt  
**Zweck:** Technische Indikatoren (pandas-ta Integration)

**Kategorien:**
```python
# Trend Indicators
def calculate_sma(df, period=20)
def calculate_ema(df, period=20)
def calculate_macd(df)
def calculate_supertrend(df)

# Momentum Indicators
def calculate_rsi(df, period=14)
def calculate_stochastic(df)
def calculate_cci(df)

# Volatility Indicators
def calculate_bollinger_bands(df)
def calculate_atr(df)
def calculate_keltner_channel(df)

# Volume Indicators
def calculate_obv(df)
def calculate_vwap(df)
def calculate_mfi(df)
```

**Wie nutzen:**
```python
from indicators.technical import calculate_rsi, calculate_macd

df = get_historical_data("AAPL")
df['rsi'] = calculate_rsi(df)
df['macd'], df['signal'] = calculate_macd(df)
```

---

### 📄 indicators/signals.py
**Status:** ⏳ Noch nicht erstellt  
**Zweck:** Trading Signal Generation

**Signal Types:**
```python
class SignalGenerator:
    def generate_rsi_signals(self, df) -> List[Signal]:
        """RSI Überkauft/Überverkauft"""
        
    def generate_macd_signals(self, df) -> List[Signal]:
        """MACD Crossovers"""
        
    def generate_bb_signals(self, df) -> List[Signal]:
        """Bollinger Band Bounces"""
        
    def generate_composite_signal(self, df) -> float:
        """Composite Score 0-100"""
```

**Signal Model:**
```python
class Signal(BaseModel):
    type: str  # "BUY", "SELL", "HOLD"
    strength: float  # 0-1
    indicator: str
    reason: str
    timestamp: datetime
```

---

### 📄 indicators/patterns.py
**Status:** ⏳ Noch nicht erstellt  
**Zweck:** Chart Pattern Detection

**Patterns:**
```python
def detect_hammer(df) -> List[Pattern]
def detect_doji(df) -> List[Pattern]
def detect_engulfing(df) -> List[Pattern]
def detect_morning_star(df) -> List[Pattern]
def detect_head_and_shoulders(df) -> List[Pattern]
def detect_double_top(df) -> List[Pattern]
```

---

## 📂 services/ - Application Layer

### 📄 services/market_service.py
**Status:** ⏳ Noch nicht erstellt  
**Zweck:** Market Data Service (Business Logic)

**Responsibilities:**
- Koordiniert OpenBB Client Calls
- Data Transformation
- Error Handling
- Caching Strategy

**Wichtige Funktionen:**
```python
class MarketService:
    def __init__(self, openbb_client, cache_manager):
        self.openbb = openbb_client
        self.cache = cache_manager
    
    def get_stock_data(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """Holt & cached Stock Data"""
        
    def get_multiple_stocks(self, symbols: List[str]) -> Dict:
        """Bulk Data Loading"""
        
    def get_market_overview(self) -> Dict:
        """Market Summary (Indices, VIX, etc.)"""
        
    def search_symbol(self, query: str) -> List[Dict]:
        """Symbol Search"""
```

---

### 📄 services/analysis_service.py
**Status:** ⏳ Noch nicht erstellt  
**Zweck:** Analysis Logic

**Features:**
- Kombiniert Indicators
- Generiert Insights
- Scoring System

```python
class AnalysisService:
    def analyze_stock(self, symbol: str) -> StockAnalysis:
        """Vollständige Aktien-Analyse"""
        
    def calculate_signal_score(self, df: pd.DataFrame) -> float:
        """Composite Signal Score"""
        
    def find_support_resistance(self, df: pd.DataFrame) -> Dict:
        """Support/Resistance Levels"""
```

---

### 📄 services/portfolio_service.py
**Status:** ⏳ Noch nicht erstellt  
**Zweck:** Portfolio Management & Analytics

**Features:**
```python
class PortfolioService:
    def calculate_returns(self, holdings: List[Holding]) -> Dict:
        """Portfolio Returns"""
        
    def calculate_risk_metrics(self, holdings) -> RiskMetrics:
        """Sharpe, Sortino, VaR"""
        
    def calculate_correlation_matrix(self, symbols) -> pd.DataFrame:
        """Korrelation zwischen Assets"""
        
    def optimize_portfolio(self, symbols, constraints) -> Dict:
        """Portfolio Optimization (Markowitz)"""
```

---

### 📄 services/screener_service.py
**Status:** ⏳ Noch nicht erstellt  
**Zweck:** Stock Screening Logic

**Strategies:**
```python
class ScreenerService:
    def screen_rsi_oversold(self, symbols) -> List[str]:
        """Findet überverkaufte Aktien"""
        
    def screen_macd_crossover(self, symbols) -> List[str]:
        """Findet MACD Crossovers"""
        
    def screen_volume_breakout(self, symbols) -> List[str]:
        """Findet Volume Breakouts"""
        
    def screen_custom(self, symbols, filters) -> List[str]:
        """Custom Filter"""
```

---

## 📂 ui/ - Presentation Layer

### 📄 ui/components/charts.py
**Status:** ⏳ Noch nicht erstellt  
**Zweck:** Reusable Chart Components

**Components:**
```python
def create_candlestick_chart(df, indicators=None) -> go.Figure:
    """Candlestick Chart mit Indikatoren"""
    
def create_line_chart(df, columns) -> go.Figure:
    """Line Chart"""
    
def create_volume_chart(df) -> go.Figure:
    """Volume Bar Chart"""
    
def create_indicator_subplot(df, indicator_name) -> go.Figure:
    """Indicator Subplot (RSI, MACD, etc.)"""
    
def create_heatmap(data, title) -> go.Figure:
    """Heatmap (z.B. Korrelation)"""
```

---

### 📄 ui/components/metrics.py
**Status:** ⏳ Noch nicht erstellt  
**Zweck:** Metric Display Components

**Components:**
```python
def display_metric_card(label, value, delta=None):
    """Metric Card mit Delta"""
    
def display_metric_grid(metrics: Dict):
    """Grid von Metrics"""
    
def display_progress_bar(value, max_value, label):
    """Progress Bar für Scores"""
```

---

### 📄 ui/components/tables.py
**Status:** ⏳ Noch nicht erstellt  
**Zweck:** Data Table Components

**Components:**
```python
def display_financial_table(df):
    """Financial Statements Table"""
    
def display_screener_results(results):
    """Screener Results Table"""
    
def display_options_chain(chain_data):
    """Options Chain Table"""
```

---

### 📄 ui/components/sidebar.py
**Status:** ⏳ Noch nicht erstellt  
**Zweck:** Sidebar Components

**Components:**
```python
def render_watchlist_selector():
    """Watchlist Dropdown"""
    
def render_settings_panel():
    """Settings Panel"""
    
def render_symbol_search():
    """Symbol Search Box"""
    
def render_connection_status():
    """OpenBB Connection Status"""
```

---

## 📂 ui/pages/ - Streamlit Pages

### 📄 ui/pages/1_📈_charts.py
**Status:** ⏳ Noch nicht erstellt  
**Zweck:** Chart Analysis Page

**Features:**
- Symbol Input
- Timeframe Selector
- Indicator Checkboxes
- Interactive Chart
- Live Indicators Grid
- Signal Score

**Layout:**
```
┌─────────────────────────────────────┐
│ Symbol: [AAPL▼] Timeframe: [1Y▼]  │
├─────────────────────────────────────┤
│ Indicators: [☑ SMA] [☑ RSI] [☑ BB]│
├─────────────────────────────────────┤
│                                     │
│        CANDLESTICK CHART            │
│                                     │
├─────────────────────────────────────┤
│  RSI: 45.2   MACD: +0.5  BB: Mid  │
├─────────────────────────────────────┤
│  Signal Score: 65/100  [BUY]       │
└─────────────────────────────────────┘
```

---

### 📄 ui/pages/2_📊_fundamentals.py
**Status:** ⏳ Noch nicht erstellt  
**Zweck:** Fundamental Analysis Page

**Features:**
- Company Profile
- Financial Statements (Income, Balance, Cash Flow)
- Key Metrics (P/E, ROE, etc.)
- Analyst Estimates
- Insider Trading
- Institutional Holdings

---

### 📄 ui/pages/3_🔍_screener.py
**Status:** ⏳ Noch nicht erstellt  
**Zweck:** Stock Screener Page

**Features:**
- Strategy Selection
- Custom Filters
- Watchlist Selection
- Results Table
- Export to CSV

---

### 📄 ui/pages/4_💼_portfolio.py
**Status:** ⏳ Noch nicht erstellt  
**Zweck:** Portfolio Analytics Page

**Features:**
- Portfolio Input (Holdings)
- Returns Chart
- Risk Metrics
- Correlation Matrix
- Efficient Frontier

---

### 📄 ui/pages/5_🌍_macro.py
**Status:** ⏳ Noch nicht erstellt  
**Zweck:** Macro Dashboard

**Features:**
- Global Indices
- Treasury Yields Curve
- VIX Chart
- Economic Calendar
- Sector Rotation

---

### 📄 ui/pages/6_🎰_options.py
**Status:** ⏳ Noch nicht erstellt  
**Zweck:** Options Analysis

**Features:**
- Options Chain
- Greeks Calculator
- IV Surface
- Max Pain Chart
- Put/Call Ratio

---

### 📄 ui/pages/7_🤖_ai_analyst.py
**Status:** ⏳ Noch nicht erstellt  
**Zweck:** AI-powered Analysis

**Features:**
- Natural Language Input
- 4D Analysis (Technical, Fundamental, Macro, Sentiment)
- Buy/Sell Recommendations
- Executive Summary

---

## 📂 utils/ - Utilities

### 📄 utils/formatters.py
**Status:** ⏳ Noch nicht erstellt  
**Zweck:** Data Formatting Functions

```python
def format_currency(value: float) -> str:
    """$1,234.56"""
    
def format_percentage(value: float) -> str:
    """12.34%"""
    
def format_large_number(value: float) -> str:
    """1.2M, 3.5B"""
    
def format_date(date: datetime) -> str:
    """Feb 25, 2026"""
```

---

### 📄 utils/validators.py
**Status:** ⏳ Noch nicht erstellt  
**Zweck:** Input Validation

```python
def validate_symbol(symbol: str) -> bool:
    """Validiert Stock Symbol"""
    
def validate_date_range(start, end) -> bool:
    """Validiert Date Range"""
    
def validate_portfolio_input(holdings) -> bool:
    """Validiert Portfolio Input"""
```

---

### 📄 utils/helpers.py
**Status:** ⏳ Noch nicht erstellt  
**Zweck:** Helper Functions

```python
def is_market_open() -> bool:
    """Prüft ob Markt offen"""
    
def get_market_status() -> str:
    """Market Status String"""
    
def calculate_date_range(timeframe: str) -> Tuple:
    """Berechnet Start/End Date"""
```

---

## 📂 tests/ - Testing

### 📄 tests/test_openbb_client.py
**Status:** ⏳ Noch nicht erstellt  
**Zweck:** Tests für OpenBB Client

```python
def test_get_historical_data():
    """Test historische Daten"""
    
def test_multi_provider_fallback():
    """Test Fallback-Mechanismus"""
    
def test_caching():
    """Test Caching"""
    
def test_error_handling():
    """Test Error Cases"""
```

---

## 🔄 Wie man diese Datei nutzt

### Als Entwickler:
1. **Neue Datei erstellen?** → Hier dokumentieren mit Status ⏳
2. **Datei fertig?** → Status auf ✅ ändern + Beschreibung updaten
3. **Funktion nicht klar?** → Hier nachlesen was Datei tut
4. **Dependency unklar?** → Hier steht was Datei braucht

### Als neuer Team-Member:
1. Lese diese Datei komplett durch (30 Min)
2. Du verstehst dann die komplette Architektur
3. Finde die Datei die du ändern willst
4. Checke Dependencies und Zweck

### Für Fortsetzung nach Pause:
1. Öffne ROADMAP.md (wo stehen wir?)
2. Öffne FILE_DOCUMENTATION.md (was macht was?)
3. Öffne DAILY_LOG.md (was wurde zuletzt gemacht?)
4. Nimm nächsten Task

---

**Letzte Aktualisierung:** 25. Februar 2026  
**Status:** Initial Documentation  
**Dateien dokumentiert:** 30+ geplante Dateien  
**Dateien fertig:** 1 (openbb_client.py)
