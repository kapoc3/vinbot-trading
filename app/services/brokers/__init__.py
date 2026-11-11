from typing import Optional
from app.services.brokers.base import BaseBrokerAdapter
from app.services.brokers.binance_adapter import BinanceAdapter
from app.services.brokers.alpaca_adapter import AlpacaAdapter
from app.core.config import get_settings

settings = get_settings()

_adapters = {}


def get_broker_adapter(broker_name: Optional[str] = None) -> BaseBrokerAdapter:
    """
    Factory function returning the singleton instance of the requested or configured broker adapter.
    Options: 'binance' | 'alpaca'
    """
    name = (broker_name or getattr(settings, "BROKER_BACKEND", "binance")).lower()
    if name == "alpaca":
        if "alpaca" not in _adapters:
            _adapters["alpaca"] = AlpacaAdapter()
        return _adapters["alpaca"]
    else:
        if "binance" not in _adapters:
            _adapters["binance"] = BinanceAdapter()
        return _adapters["binance"]


def get_broker_adapter_for_symbol(symbol: str) -> BaseBrokerAdapter:
    """
    Determine and return the appropriate broker adapter for a given trading symbol.
    Supports single broker mode ('binance' | 'alpaca') as well as 'dual'/'hybrid' mode.
    """
    backend = getattr(settings, "BROKER_BACKEND", "binance").lower()
    if backend in ("dual", "hybrid", "both"):
        alpaca_syms = [s.strip().upper() for s in getattr(settings, "ALPACA_TRADING_SYMBOLS", "").split(",") if s.strip()]
        clean_sym = symbol.strip().upper()
        # Route to Alpaca if symbol is in ALPACA_TRADING_SYMBOLS, contains slash (e.g. BTC/USD),
        # or has standard stock ticker format (<= 5 chars without stablecoin suffix)
        if (clean_sym in alpaca_syms or 
            "/" in clean_sym or 
            (len(clean_sym) <= 5 and not clean_sym.endswith(("USDT", "USDC", "BUSD", "FDUSD")))):
            return get_broker_adapter("alpaca")
        return get_broker_adapter("binance")

    return get_broker_adapter(backend)


__all__ = ["BaseBrokerAdapter", "BinanceAdapter", "AlpacaAdapter", "get_broker_adapter", "get_broker_adapter_for_symbol"]

