import logging
from typing import Dict, Any, List
from app.services.binance_client import binance_client

logger = logging.getLogger(__name__)

class AccountManager:
    async def get_account_info(self) -> Dict[str, Any]:
        """Fetch full account information (Task 5.1)."""
        return await binance_client.request("GET", "/v3/account", signed=True)

    async def get_asset_balance(self, asset: str) -> Dict[str, str]:
        """Get balance for a specific asset."""
        account_info = await self.get_account_info()
        balances = account_info.get("balances", [])
        for balance in balances:
            if balance["asset"] == asset:
                return balance
        return {"asset": asset, "free": "0.0", "locked": "0.0"}

account_manager = AccountManager()
