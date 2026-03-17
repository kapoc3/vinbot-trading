import logging
import httpx
from typing import Optional
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class NotificationService:
    """Task 1.2: Centralized service for Telegram notifications."""
    
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    async def send_message(self, text: str):
        """Send an asynchronous message to Telegram."""
        if not self.bot_token or not self.chat_id:
            logger.warning("NOTIFICATIONS | Telegram credentials missing. Skipping message.")
            return

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "MarkdownV2"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.base_url, json=payload, timeout=10.0)
                if response.status_code != 200:
                    logger.error(f"NOTIFICATIONS | Telegram API Error: {response.text}")
                else:
                    logger.info("NOTIFICATIONS | Message sent successfully to Telegram.")
        except Exception as e:
            logger.error(f"NOTIFICATIONS | Failed to send Telegram message: {e}")

    async def notify_order(self, symbol: str, side: str, price: float, qty: float, rsi: Optional[float] = None):
        """Format and send an order execution notification."""
        emoji = "🚀" if side.upper() == "BUY" else "💰"
        symbol_esc = self.escape_markdown(symbol)
        side_esc = self.escape_markdown(side.upper())
        price_esc = self.escape_markdown(f"{price:.2f}")
        qty_esc = self.escape_markdown(f"{qty}")
        rsi_str = f" | RSI: `{rsi:.2f}`" if rsi is not None else ""
        
        msg = f"{emoji} *{symbol_esc}* {side_esc} executed\nPrice: `{price_esc}`\nQty: `{qty_esc}`{rsi_str}"
        await self.send_message(msg)

    async def notify_risk(self, signal: str, symbol: str, price: float, pnl: float):
        """Format and send a risk management alert."""
        emoji = "⚠️" if "LOSS" in signal.upper() else "✨"
        symbol_esc = self.escape_markdown(symbol)
        signal_esc = self.escape_markdown(signal.replace("_", " "))
        price_esc = self.escape_markdown(f"{price:.2f}")
        pnl_esc = self.escape_markdown(f"{pnl:.2f}")
        
        msg = f"{emoji} *RISK ALERT* | {symbol_esc}\nSignal: `{signal_esc}`\nPrice: `{price_esc}`\nPNL: `{pnl_esc}%`"
        await self.send_message(msg)

    async def notify_status(self, status: str):
        """Send a status update notification."""
        emoji = "🤖" if "ONLINE" in status.upper() else "🔌"
        status_esc = self.escape_markdown(status)
        msg = f"{emoji} *VinBot* status: {status_esc}"
        await self.send_message(msg)

    def escape_markdown(self, text: str) -> str:
        """Helper to escape special characters for Telegram MarkdownV2."""
        # Characters to escape: _ * [ ] ( ) ~ ` > # + - = | { } . !
        escape_chars = r"_*[]()~`>#+-=|{}.!"
        return "".join(f"\\{c}" if c in escape_chars else c for c in text)

# Global instance
notification_service = NotificationService()
