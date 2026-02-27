"""
services/market_service.py - Logik für Fundamentaldaten und Metriken
"""
from data.openbb_client import get_client

class MarketService:
    def __init__(self):
        self.client = get_client()

    def get_stock_overview(self, ticker: str) -> dict:
        """Kombiniert Company Info und aktuelles Quote-Objekt."""
        info = self.client.get_company_info(ticker)
        quote = self.client.get_quote(ticker)
        # Werte zusammenführen
        overview = {**info, **quote}
        return overview

    def get_key_metrics(self, ticker: str) -> list[dict]:
        """Liefert KPIs für die Metrik-Reihe auf der Fundamentals-Seite."""
        quote = self.client.get_quote(ticker)
        
        return [
            {"label": "Marktkapitalisierung", "value": f"${quote.get('market_cap', 0):,.0f}" if quote.get('market_cap') else "N/A"},
            {"label": "KGV (P/E)", "value": f"{quote.get('pe_ratio', 0):.2f}" if quote.get('pe_ratio') else "N/A"},
            {"label": "52W High", "value": f"${quote.get('week_52_high', 0):.2f}" if quote.get('week_52_high') else "N/A"},
            {"label": "52W Low", "value": f"${quote.get('week_52_low', 0):.2f}" if quote.get('week_52_low') else "N/A"},
        ]

    def get_financial_statements(self, ticker: str) -> dict:
        """Lädt Bilanz, GuV und Cashflow."""
        return {
            "income": self.client.get_financials(ticker, "income"),
            "balance": self.client.get_financials(ticker, "balance"),
            "cashflow": self.client.get_financials(ticker, "cashflow")
        }

    def get_growth_metrics(self, ticker: str) -> list[dict]:
        return [{"metric": "Umsatzwachstum", "value": "Daten via API laden..."}]

    def get_analyst_info(self, ticker: str) -> dict:
        return {"recommendation": "Hold", "target_mean": 0.0, "fmt_upside": "N/A"}

# --- SINGLETON PATTERN ---
_market_service_instance = None

def get_market_service() -> MarketService:
    global _market_service_instance
    if _market_service_instance is None:
        _market_service_instance = MarketService()
    return _market_service_instance