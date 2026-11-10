import logging
import time
import httpx
from typing import Optional, Dict, Set
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class NotificationService:
    """Actionable, zero-noise Telegram notification service with cooldown deduplication."""

    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        self._cooldowns: Dict[str, float] = {}
        self._reached_milestones: Set[float] = set()

    def _is_on_cooldown(self, key: str, cooldown_sec: int) -> bool:
        now = time.time()
        last_sent = self._cooldowns.get(key, 0.0)
        if (now - last_sent) < cooldown_sec:
            return True
        self._cooldowns[key] = now
        return False

    async def send_message(
        self,
        text: str,
        silent: bool = False,
        dedup_key: Optional[str] = None,
        cooldown_sec: Optional[int] = None,
    ):
        """Send an asynchronous message to Telegram with optional cooldown and MarkdownV2 fallback."""
        if not self.bot_token or not self.chat_id:
            logger.warning("NOTIFICATIONS | Telegram credentials missing. Skipping message.")
            return

        if dedup_key:
            cd = cooldown_sec if cooldown_sec is not None else settings.ALERT_COOLDOWN_SECONDS
            if self._is_on_cooldown(dedup_key, cd):
                logger.debug(f"NOTIFICATIONS | Suppressed duplicate alert '{dedup_key}' (on cooldown).")
                return

        proj_esc = self.escape_markdown(settings.PROJECT_NAME)
        full_text = f"\\[{proj_esc}\\]\n{text}"

        payload = {
            "chat_id": self.chat_id,
            "text": full_text,
            "parse_mode": "MarkdownV2",
            "disable_notification": silent,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.base_url, json=payload, timeout=10.0)
                if response.status_code == 400 and "can't parse entities" in response.text:
                    clean_text = f"[{settings.PROJECT_NAME}]\n" + text.replace("\\", "").replace("*", "").replace("`", "")
                    fallback_payload = {
                        "chat_id": self.chat_id,
                        "text": clean_text,
                        "disable_notification": silent,
                    }
                    response = await client.post(self.base_url, json=fallback_payload, timeout=10.0)
                if response.status_code != 200:
                    logger.error(f"NOTIFICATIONS | Telegram API Error: {response.text}")
                else:
                    logger.info("NOTIFICATIONS | Message sent successfully to Telegram.")
        except Exception as e:
            logger.error(f"NOTIFICATIONS | Failed to send Telegram message: {e}")

    async def notify_order(
        self,
        symbol: str,
        side: str,
        price: float,
        qty: float,
        rsi: Optional[float] = None,
        balance: Optional[float] = None,
        quote_asset: str = "USDC",
    ):
        """Format and send a BUY order execution notification with SL/TP targets."""
        emoji = "🚀" if side.upper() == "BUY" else "💰"
        notional = price * qty
        sl_price = price * (1 - settings.STOP_LOSS_PCT / 100.0)
        tp_price = price * (1 + settings.TAKE_PROFIT_PCT / 100.0)

        symbol_esc = self.escape_markdown(symbol)
        side_esc = self.escape_markdown(side.upper())
        price_esc = self.escape_markdown(f"{price:.4f}" if price < 10 else f"{price:.2f}")
        qty_esc = self.escape_markdown(f"{qty}")
        notional_esc = self.escape_markdown(f"{notional:.2f} {quote_asset}")
        sl_esc = self.escape_markdown(f"{sl_price:.4f}" if price < 10 else f"{sl_price:.2f}")
        tp_esc = self.escape_markdown(f"{tp_price:.4f}" if price < 10 else f"{tp_price:.2f}")
        rsi_str = f"\nRSI Entrada: `{self.escape_markdown(f'{rsi:.1f}')}`" if rsi is not None else ""
        bal_str = (
            f"\nSaldo Libre: `{self.escape_markdown(f'{balance:.2f} {quote_asset}')}`"
            if balance is not None
            else ""
        )

        if side.upper() == "BUY":
            msg = (
                f"{emoji} *COMPRA EJECUTADA \\| {symbol_esc}*\n"
                f"Precio: `{price_esc}` \\(`{notional_esc}`\\)\n"
                f"Cantidad: `{qty_esc}`\n"
                f"SL: `{sl_esc}` \\(\\-{self.escape_markdown(str(settings.STOP_LOSS_PCT))}%\\) \\| "
                f"TP: `{tp_esc}` \\(\\+{self.escape_markdown(str(settings.TAKE_PROFIT_PCT))}%\\)"
                f"{rsi_str}{bal_str}"
            )
        else:
            msg = (
                f"{emoji} *{symbol_esc}* {side_esc} ejecutada\n"
                f"Precio: `{price_esc}` \\| Cant: `{qty_esc}`{rsi_str}{bal_str}"
            )
        await self.send_message(msg)

    async def notify_trade_closed(
        self,
        signal: str,
        symbol: str,
        entry_price: float,
        exit_price: float,
        qty: float,
        pnl_pct: float,
        pnl_usd: float,
        daily_pnl: float,
        balance: Optional[float] = None,
        quote_asset: str = "USDC",
        fee_usd: Optional[float] = None,
    ):
        """Send a single unified notification when a position is closed (TP, SL, Trailing TP, Time Exit, or Strategy SELL)."""
        is_win = pnl_usd >= 0
        emoji = "✅" if is_win else "🛑"
        sign_str = "+" if is_win else ""

        symbol_esc = self.escape_markdown(symbol)
        signal_esc = self.escape_markdown(signal.replace("_", " "))
        entry_esc = self.escape_markdown(f"{entry_price:.4f}" if entry_price < 10 else f"{entry_price:.2f}")
        exit_esc = self.escape_markdown(f"{exit_price:.4f}" if exit_price < 10 else f"{exit_price:.2f}")
        pnl_usd_esc = self.escape_markdown(f"{sign_str}{pnl_usd:.2f} {quote_asset}")
        pnl_pct_esc = self.escape_markdown(f"{sign_str}{pnl_pct:.2f}%")
        daily_sign = "+" if daily_pnl >= 0 else ""
        daily_esc = self.escape_markdown(f"{daily_sign}{daily_pnl:.2f} {quote_asset}")

        fee_str = f" \\| Fee: `-${fee_usd:.3f}`" if (fee_usd is not None and fee_usd > 0) else ""

        progress_line = ""
        if balance is not None:
            target = settings.CAPITAL_TARGET_USDC
            pct_goal = min(100.0, (balance / target) * 100.0) if target > 0 else 0.0
            bal_esc = self.escape_markdown(f"{balance:.2f} / {target:.0f} {quote_asset} ({pct_goal:.1f}%)")
            progress_line = f"\nMeta Capital: `{bal_esc}`"

        msg = (
            f"{emoji} *POSICIÓN CERRADA \\| {symbol_esc}*\n"
            f"Motivo: `{signal_esc}`\n"
            f"Entrada: `{entry_esc}` ➔ Salida: `{exit_esc}`\n"
            f"Resultado Neto: *{pnl_usd_esc}* \\(`{pnl_pct_esc}`\\){fee_str}\n"
            f"PnL Hoy: `{daily_esc}`{progress_line}"
        )
        await self.send_message(msg)

        if balance is not None:
            await self.check_capital_milestone(balance, quote_asset=quote_asset)

    async def notify_risk(
        self,
        signal: str,
        symbol: str,
        price: float,
        pnl: float,
        balance: Optional[float] = None,
        quote_asset: str = "USDC",
    ):
        """Legacy wrapper for risk notifications."""
        emoji = "⚠️" if "LOSS" in signal.upper() else "✨"
        symbol_esc = self.escape_markdown(symbol)
        signal_esc = self.escape_markdown(signal.replace("_", " "))
        price_esc = self.escape_markdown(f"{price:.2f}")
        pnl_esc = self.escape_markdown(f"{pnl:.2f}")
        pipe_esc = self.escape_markdown(" | ")
        bal_str = (
            f"\nBalance: `{self.escape_markdown(f'{balance:.2f}')} {self.escape_markdown(quote_asset)}`"
            if balance is not None
            else ""
        )

        msg = f"{emoji} *RISK ALERT*{pipe_esc}{symbol_esc}\nSignal: `{signal_esc}`\nPrice: `{price_esc}`\nPNL: `{pnl_esc}%`{bal_str}"
        await self.send_message(msg)

    async def notify_critical_error(self, context: str, symbol: str, error_msg: str):
        """Send an actionable alert when human intervention is required (e.g., failed order, SL failure, API block)."""
        ctx_esc = self.escape_markdown(context)
        sym_esc = self.escape_markdown(symbol)
        err_esc = self.escape_markdown(str(error_msg)[:220])
        msg = (
            f"🚨 *ACCIÓN REQUERIDA \\| {ctx_esc}*\n"
            f"Par: `{sym_esc}`\n"
            f"Detalle: `{err_esc}`\n"
            f"Verifica tu saldo libre o estado de órdenes en Binance\\."
        )
        await self.send_message(msg, dedup_key=f"crit:{context}:{symbol}")

    async def check_capital_milestone(self, current_balance: float, quote_asset: str = "USDC"):
        """Alert the user once when free capital crosses a compounding milestone (82, 91, 100 USDC)."""
        try:
            milestones = [
                float(m.strip())
                for m in settings.CAPITAL_MILESTONES.split(",")
                if m.strip()
            ]
        except Exception:
            milestones = [82.0, 91.0, 100.0]

        for m in sorted(milestones):
            if current_balance >= m and m not in self._reached_milestones:
                self._reached_milestones.add(m)
                if m >= 100.0:
                    action = "¡Meta de 100 USDC alcanzada! Considera retirar ganancias o activar Etapa 4."
                elif m >= 91.0:
                    action = "Etapa 3 desbloqueada: puedes subir FIXED_ORDER_VALUE_USDT a 25.0 en .env.classic y .env.scalper."
                else:
                    action = "Etapa 2 desbloqueada: puedes subir FIXED_ORDER_VALUE_USDT a 22.0 en .env.classic y .env.scalper."

                m_esc = self.escape_markdown(f"{m:.0f} {quote_asset}")
                bal_esc = self.escape_markdown(f"{current_balance:.2f} {quote_asset}")
                act_esc = self.escape_markdown(action)
                msg = (
                    f"🏆 *HITO DE CAPITAL ALCANZADO: {m_esc}*\n"
                    f"Saldo Libre Actual: `{bal_esc}`\n"
                    f"Acción sugerida: {act_esc}"
                )
                await self.send_message(msg, dedup_key=f"milestone:{m}", cooldown_sec=86400)

    async def notify_status(self, status: str, silent: bool = False, dedup_key: Optional[str] = None):
        """Send a status update notification."""
        emoji = "🚨" if "CIRCUIT BREAKER" in status.upper() else ("🤖" if "ONLINE" in status.upper() else "📊")
        status_esc = self.escape_markdown(status)
        msg = f"{emoji} {status_esc}"
        await self.send_message(msg, silent=silent, dedup_key=dedup_key)

    def escape_markdown(self, text: str) -> str:
        """Helper to escape special characters for Telegram MarkdownV2."""
        escape_chars = r"_*[]()~`>#+-=|{}.!"
        return "".join(f"\\{c}" if c in escape_chars else c for c in text)


# Global instance
notification_service = NotificationService()
