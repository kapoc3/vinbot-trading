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


__all__ = ["BaseBrokerAdapter", "BinanceAdapter", "AlpacaAdapter", "get_broker_adapter"]
