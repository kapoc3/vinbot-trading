import logging
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.core.config import get_settings
from app.services.risk_manager import risk_manager
from app.services.statistics import statistics_service
from app.services.regime_service import regime_service
from app.services.binance_client import binance_client
from app.core.database import db

logger = logging.getLogger(__name__)
settings = get_settings()


class AIChatService:
    """
    Intelligent Trading & Risk Advisor running on local LLMs (Ollama / Qwen 2.5 / GTX 1060).
    Injects real-time VinBot account state, FIFO closed cycles, OBI pressure, and market regimes.
    """

    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
        self.active_base_url: Optional[str] = None

    def _get_client(self) -> httpx.AsyncClient:
        if self.client is None or self.client.is_closed:
            self.client = httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT_SECONDS)
        return self.client

    async def _resolve_base_url(self) -> str:
        """Find working Ollama URL among configured URL, host LAN IP, host.docker.internal, and localhost."""
        if self.active_base_url:
            return self.active_base_url

        client = self._get_client()
        candidates = []
        if settings.OLLAMA_BASE_URL:
            candidates.append(settings.OLLAMA_BASE_URL.rstrip("/"))

        for fallback in [
            "http://192.168.2.70:11434",
            "http://host.docker.internal:11434",
            "http://172.18.0.1:11434",
            "http://localhost:11434",
        ]:
            if fallback not in candidates:
                candidates.append(fallback)

        for candidate in candidates:
            try:
                res = await client.get(f"{candidate}/api/tags", timeout=1.5)
                if res.status_code == 200:
                    self.active_base_url = candidate
                    return candidate
            except Exception:
                continue

        return settings.OLLAMA_BASE_URL.rstrip("/")

    async def check_ollama_status(self) -> Dict[str, Any]:
        """Check if local Ollama daemon is reachable and whether the target model is installed."""
        client = self._get_client()
        base_url = await self._resolve_base_url()
        try:
            res = await client.get(f"{base_url}/api/tags", timeout=5.0)
            if res.status_code == 200:
                data = res.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                has_model = any(settings.OLLAMA_MODEL in m for m in models)
                return {
                    "online": True,
                    "target_model": settings.OLLAMA_MODEL,
                    "model_available": has_model,
                    "installed_models": models,
                    "active_url": base_url,
                    "message": "Ollama local operativo con aceleración GPU." if has_model else f"Ollama en línea. Falta descargar: ollama pull {settings.OLLAMA_MODEL}"
                }
            return {
                "online": False,
                "target_model": settings.OLLAMA_MODEL,
                "model_available": False,
                "installed_models": [],
                "active_url": base_url,
                "message": f"Ollama respondió con código {res.status_code}."
            }
        except Exception as e:
            self.active_base_url = None
            logger.debug(f"AI_CHAT | Could not reach Ollama at {base_url}: {e}")
            return {
                "online": False,
                "target_model": settings.OLLAMA_MODEL,
                "model_available": False,
                "installed_models": [],
                "active_url": base_url,
                "message": f"Servidor Ollama no detectado en {base_url}. Inicia con: ollama serve"
            }

    async def build_trading_context_summary(self) -> str:
        """Extract a compact, accurate snapshot of current bot state for the LLM prompt."""
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # 1. Performance stats
        stats = {}
        try:
            stats = await statistics_service.get_all_symbols_stats()
        except Exception:
            pass

        tot_profit = stats.get("total_profit", 0.0)
        win_rate = stats.get("win_rate", 0.0)
        total_trades = stats.get("total_trades", 0)
        raw_dd = stats.get("drawdown", 0.0)
        drawdown_val = float(raw_dd.get("max_drawdown", 0.0) if isinstance(raw_dd, dict) else (raw_dd or 0.0))

        # 2. Daily metrics
        daily_pnl = getattr(risk_manager, "daily_pnl", 0.0)
        fee_pct = getattr(settings, "EFFECTIVE_FEE_PCT", 0.075)
        fee_name = "BNB 25% discount" if getattr(settings, "USE_BNB_FEE_DISCOUNT", True) else "Estándar 0.10%"

        # 3. Active positions
        pos_lines = []
        for sym, pos_data in risk_manager.position_data.items():
            entry_p = risk_manager.entry_prices.get(sym, 0.0)
            curr_q = float(pos_data.get("current_qty", 0.0))
            if entry_p > 0 and curr_q > 0:
                cur_p = float(pos_data.get("current_price", entry_p) or entry_p)
                unrealized_usd = (cur_p - entry_p) * curr_q
                unrealized_pct = ((cur_p - entry_p) / entry_p) * 100.0 if entry_p > 0 else 0.0
                sl = float(pos_data.get("sl_price", 0.0))
                tp_hits = int(pos_data.get("tp_hits", 0))
                sign = "+" if unrealized_usd >= 0 else ""
                pos_lines.append(
                    f"  - {sym}: Cantidad={curr_q}, Entrada=${entry_p:.4f}, Actual=${cur_p:.4f}, "
                    f"PnL No Realizado={sign}${unrealized_usd:.2f} ({sign}{unrealized_pct:.2f}%), "
                    f"StopLoss (BE+Fees)=${sl:.4f}, TPs alcanzados={tp_hits}"
                )

        if not pos_lines:
            pos_text = "  Ninguna posición abierta actualmente (100% liquidez en espera)."
        else:
            pos_text = "\n".join(pos_lines)

        # 4. Market Regimes
        regime_lines = []
        for sym, reg in regime_service.current_regimes.items():
            reg_name = reg.value if hasattr(reg, "value") else str(reg)
            regime_lines.append(f"  - {sym}: {reg_name}")
        regime_text = "\n".join(regime_lines) if regime_lines else "  Monitoreo estándar activo."

        # 5. Recent closed cycles / trades from database
        recent_trades_summary = []
        try:
            cursor = await db.execute("SELECT symbol, side, price, quantity, timestamp FROM orders ORDER BY timestamp DESC LIMIT 8")
            rows = await cursor.fetchall()
            for r in rows:
                d = dict(r)
                recent_trades_summary.append(
                    f"  - {d.get('timestamp')}: {d.get('side')} {d.get('symbol')} "
                    f"cant={d.get('quantity')} @ ${float(d.get('price', 0)):.4f}"
                )
        except Exception:
            pass
        trades_text = "\n".join(recent_trades_summary) if recent_trades_summary else "  Sin transacciones recientes registradas."

        context = f"""=== VINBOT REAL-TIME TRADING SNAPSHOT ({now_str}) ===
• PnL Neto Diario: ${daily_pnl:+.4f} USD
• Ganancia Total Histórica: ${tot_profit:+.2f} USD | Drawdown: -${abs(drawdown_val):.2f} USD
• Win Rate: {win_rate:.1f}% en {total_trades} operaciones ejecutadas
• Comisión Binance Efectiva: {fee_pct}% por operación ({fee_name})
• Política de Stop Loss: Break-Even + Comisiones de ida y vuelta garantizadas (Factor {settings.ROUND_TRIP_FEE_FACTOR:.6f}x)
• Estrategia Activa: {settings.TRADING_STRATEGY} | Modo Core-Satellite 70/30: {'Habilitado' if settings.ENABLE_MARKET_SCANNER else 'Deshabilitado'}
• Posiciones Activas en Cartera:
{pos_text}
• Regímenes de Mercado Detectados:
{regime_text}
• Últimas Órdenes Registradas:
{trades_text}
============================================================="""
        return context

    def _build_system_prompt(self, context_summary: str) -> str:
        return f"""Eres "VinBot Quant Analyst", el asesor cuantitativo de trading y director de riesgos algorítmico integrado en VinBot.
Estás ejecutándote localmente en la máquina del usuario (Acer Predator con aceleración por GPU NVIDIA GTX 1060).

{context_summary}

DIRECTRICES DE RESPUESTA:
1. Responde siempre en español de manera concisa, analítica, profesional y directa.
2. Utiliza siempre los números reales del SNAPSHOT para responder sobre PnL, comisiones, posiciones y rendimientos. Si un dato no está, indícalo con honestidad sin inventar.
3. Al analizar comisiones, recuerda que VinBot utiliza un factor Break-Even que cubre tanto la compra como la venta (ida y vuelta), protegiendo el margen neto.
4. Para recomendaciones estratégicas:
   - Si el régimen es "Ranging" (Rango lateral): Recomienda RSI Scalping o bandas de Bollinger con Take Profits rápidos.
   - Si el régimen es "Trending" (Tendencia fuerte): Recomienda Trend Following, dejar correr ganancias con Trailing TP y respetar el filtro direccional de BTC.
   - Si hay alta volatilidad: Recomienda cautela, reducir tamaño de posición y ceñir el Stop Loss.
5. Formatea tus respuestas usando Markdown limpio (listas, negritas, métricas destacadas y tablas cortas cuando sea útil). No generes respuestas excesivamente largas a menos que te pidan un desglose profundo."""

    async def ask_analyst(self, user_message: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Send user query and trading state context to Ollama local LLM.
        Returns a dict with 'reply', 'model', and 'status'.
        """
        if not settings.ENABLE_AI_CHAT:
            return {
                "status": "disabled",
                "reply": "El Chatbot IA está desactivado en la configuración (ENABLE_AI_CHAT=False).",
                "model": settings.OLLAMA_MODEL
            }

        # Check status first
        status = await self.check_ollama_status()
        if not status["online"]:
            return {
                "status": "offline",
                "reply": (
                    f"⚠️ **El motor de IA local no está accesible** en `{settings.OLLAMA_BASE_URL}`.\n\n"
                    f"Para activarlo en tu PC Predator con la NVIDIA GTX 1060:\n"
                    f"1. Abre una terminal y ejecuta:\n"
                    f"   ```bash\n"
                    f"   ollama serve\n"
                    f"   ```\n"
                    f"2. Asegúrate de tener el modelo descargado:\n"
                    f"   ```bash\n"
                    f"   ollama run {settings.OLLAMA_MODEL}\n"
                    f"   ```\n"
                    f"*(Nota: Puedes cambiar de modelo en `.env` definiendo `OLLAMA_MODEL=qwen2.5:3b` si buscas máxima velocidad)*."
                ),
                "model": settings.OLLAMA_MODEL
            }

        context_summary = await self.build_trading_context_summary()
        system_prompt = self._build_system_prompt(context_summary)

        messages = [{"role": "system", "content": system_prompt}]

        # Append limited prior conversation history (last 6 turns to keep context fast in GTX 1060 VRAM)
        if history and isinstance(history, list):
            for turn in history[-6:]:
                role = turn.get("role", "user")
                content = turn.get("content", "")
                if role in ("user", "assistant") and content:
                    messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": user_message})

        client = self._get_client()
        base_url = await self._resolve_base_url()
        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.4, # Lower temperature for analytical precision
                "top_p": 0.9,
                "num_ctx": 2048,   # Faster inference on GTX 1060 VRAM
                "num_predict": 512, # Cap generation for fast responsive replies
            }
        }

        try:
            logger.info(f"AI_CHAT | Querying local Ollama ({settings.OLLAMA_MODEL}) on GTX 1060...")
            res = await client.post(
                f"{base_url}/api/chat",
                json=payload,
                timeout=httpx.Timeout(settings.OLLAMA_TIMEOUT_SECONDS, connect=10.0)
            )
            
            if res.status_code == 200:
                data = res.json()
                reply = data.get("message", {}).get("content", "").strip()
                if not reply:
                    reply = "El modelo no generó ninguna respuesta."
                return {
                    "status": "success",
                    "reply": reply,
                    "model": settings.OLLAMA_MODEL,
                    "total_duration_ms": round(data.get("total_duration", 0) / 1_000_000, 1)
                }
            elif res.status_code == 404:
                return {
                    "status": "model_missing",
                    "reply": (
                        f"⚠️ El modelo `{settings.OLLAMA_MODEL}` no está descargado en tu Ollama local.\n\n"
                        f"Por favor descárgalo con:\n"
                        f"```bash\nollama pull {settings.OLLAMA_MODEL}\n```"
                    ),
                    "model": settings.OLLAMA_MODEL
                }
            else:
                return {
                    "status": "error",
                    "reply": f"Error del servidor Ollama (Código {res.status_code}): {res.text}",
                    "model": settings.OLLAMA_MODEL
                }
        except httpx.TimeoutException:
            logger.error("AI_CHAT | Request to Ollama timed out.")
            return {
                "status": "timeout",
                "reply": "⏱️ La consulta tardó más del tiempo límite. En la GTX 1060, considera usar `qwen2.5:3b` para respuestas casi instantáneas.",
                "model": settings.OLLAMA_MODEL
            }
        except Exception as e:
            logger.error(f"AI_CHAT | Error querying Ollama: {e}")
            return {
                "status": "error",
                "reply": f"Fallo al comunicarse con Ollama: {str(e)}",
                "model": settings.OLLAMA_MODEL
            }

    async def close(self):
        if self.client and not self.client.is_closed:
            await self.client.aclose()
            self.client = None


ai_chat_service = AIChatService()

