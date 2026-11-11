from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseBrokerAdapter(ABC):
    """
    Abstract interface defining standard brokerage operations.
    Enables VinBot to seamlessly trade on Binance Spot, Alpaca Markets (Equities/Crypto),
    or any future exchange without altering trading strategies or risk engines.
    """

    @property
    @abstractmethod
    def broker_name(self) -> str:
        """Return the lowercase name of the broker (e.g. 'binance', 'alpaca')."""
        pass

    @abstractmethod
    async def get_account(self) -> Dict[str, Any]:
        """
        Fetch normalized account overview.
        Returns:
            {
                "equity_usd": float,
                "cash_usd": float,
                "buying_power_usd": float,
                "currency": str,
                "is_paper": bool,
                "status": str
            }
        """
        pass

    @abstractmethod
    async def get_wallet_balances(self) -> List[Dict[str, Any]]:
        """
        Fetch normalized list of assets held.
        Returns:
            [
                {
                    "asset": str,
                    "free": float,
                    "locked": float,
                    "total": float,
                    "price_usd": float,
                    "usd_value": float,
                    "is_stable": bool
                }
            ]
        """
        pass

    @abstractmethod
    async def get_positions(self) -> List[Dict[str, Any]]:
        """
        Fetch list of currently open positions.
        Returns:
            [
                {
                    "symbol": str,
                    "qty": float,
                    "entry_price": float,
                    "current_price": float,
                    "unrealized_pnl_usd": float,
                    "unrealized_pnl_pct": float,
                    "market_value_usd": float,
                    "side": str
                }
            ]
        """
        pass

    @abstractmethod
    async def get_historical_bars(self, symbol: str, interval: str = "1h", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch normalized OHLCV bars for technical indicators and ML models.
        Returns:
            [
                {
                    "time": int (epoch ms),
                    "open": float,
                    "high": float,
                    "low": float,
                    "close": float,
                    "volume": float
                }
            ]
        """
        pass

    @abstractmethod
    async def get_latest_price(self, symbol: str) -> float:
        """Fetch current market price for symbol."""
        pass

    @abstractmethod
    async def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "MARKET",
        time_in_force: str = "gtc",
        take_profit_price: Optional[float] = None,
        stop_loss_price: Optional[float] = None,
        limit_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Place an order. If take_profit_price and stop_loss_price are supplied on brokers
        supporting bracket orders (like Alpaca), submits a native server-side bracket order.
        """
        pass

    @abstractmethod
    async def cancel_order(self, order_id: Any, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Cancel an active order."""
        pass

    @abstractmethod
    async def close(self):
        """Clean up underlying network clients and connections."""
        pass

