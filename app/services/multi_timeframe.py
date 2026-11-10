"""
Multi-Timeframe Analysis Module.
"""
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

from app.core.config import get_settings
from app.services.indicators import get_symbol_data, SymbolData

logger = logging.getLogger(__name__)
settings = get_settings()


class ConfluenceLevel(Enum):
    """Nivel de confluencia multi-timeframe."""
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"


class TrendDirection(Enum):
    """Dirección de tendencia por timeframe."""
    UP = "UP"
    DOWN = "DOWN"
    RANGING = "RANGING"


@dataclass
class ConfirmationResult:
    """Resultado de la evaluación de confirmación de señal."""
    confirmed: bool
    confluence_level: ConfluenceLevel
    position_multiplier: float
    reason: str
    ema_1h_direction: Optional[str] = None
    ema_15m_direction: Optional[str] = None
    ema_1m_direction: Optional[str] = None


class MultiTimeframeManager:
    """
    Gestor de datos y análisis multi-timeframe.
    Mantiene datos de múltiples timeframes para análisis de confluencia.
    """

    def __init__(self):
        self.enabled = settings.MULTI_TF_ENABLED
        self.timeframes = self._parse_timeframes(settings.ACTIVE_TIMEFRAMES)
        self.max_candles = settings.MAX_CANDLES_PER_TF

        # Dictionary de SymbolData por timeframe
        # {symbol: {timeframe: SymbolData}}
        self.symbol_data: Dict[str, Dict[str, SymbolData]] = {}
        self._1m_counters: Dict[str, int] = {}
        self._1m_buffer: Dict[str, List[Dict[str, float]]] = {}

        # Track symbols being monitored
        self.monitored_symbols: set = set()

        logger.info(f"MultiTimeframeManager initialized: {self.enabled}, timeframes: {self.timeframes}")

    def _parse_timeframes(self, tf_string: str) -> List[str]:
        """Parse timeframes from config string."""
        return [t.strip() for t in tf_string.split(",")]

    def register_symbol(self, symbol: str):
        """Registrar símbolo para monitoreo multi-timeframe."""
        if symbol not in self.symbol_data:
            self.symbol_data[symbol] = {}
            for tf in self.timeframes:
                # Crear nueva instancia de SymbolData para cada timeframe
                self.symbol_data[symbol][tf] = SymbolData(self.max_candles)
            self.monitored_symbols.add(symbol)
            logger.info(f"Registered {symbol} for multi-TF analysis on timeframes: {self.timeframes}")

    def unregister_symbol(self, symbol: str):
        """Dejar de monitorear un símbolo."""
        if symbol in self.symbol_data:
            self.symbol_data.pop(symbol, None)
            self.monitored_symbols.discard(symbol)
            logger.info(f"Unregistered {symbol} from multi-TF analysis")

    def add_kline(self, symbol: str, timeframe: str, kline: Dict[str, Any]):
        """Añadir un kline a un timeframe específico (con agregación automática de 1m a 15m/1h)."""
        if symbol not in self.symbol_data or timeframe not in self.symbol_data[symbol]:
            return

        self.symbol_data[symbol][timeframe].add_kline(kline)

        # Automatically roll up 1m closed candles into 15m and 1h buffers
        if timeframe == "1m":
            c = float(kline.get("c", 0))
            h = float(kline.get("h", c))
            l = float(kline.get("l", c))
            v = float(kline.get("v", 0))
            buf = self._1m_buffer.setdefault(symbol, [])
            buf.append({"c": c, "h": h, "l": l, "v": v})
            if len(buf) > 60:
                buf.pop(0)
            count = self._1m_counters.get(symbol, 0) + 1
            self._1m_counters[symbol] = count

            if count % 15 == 0 and "15m" in self.symbol_data[symbol] and len(buf) >= 15:
                w15 = buf[-15:]
                self.symbol_data[symbol]["15m"].add_kline({
                    "c": w15[-1]["c"],
                    "h": max(x["h"] for x in w15),
                    "l": min(x["l"] for x in w15),
                    "v": sum(x["v"] for x in w15),
                })
            if count % 60 == 0 and "1h" in self.symbol_data[symbol] and len(buf) >= 60:
                w60 = buf[-60:]
                self.symbol_data[symbol]["1h"].add_kline({
                    "c": w60[-1]["c"],
                    "h": max(x["h"] for x in w60),
                    "l": min(x["l"] for x in w60),
                    "v": sum(x["v"] for x in w60),
                })

    def get_symbol_data(self, symbol: str, timeframe: str) -> Optional[SymbolData]:
        """Obtener datos de un símbolo en un timeframe específico."""
        return self.symbol_data.get(symbol, {}).get(timeframe)

    # ==================== Indicator Aggregation ====================

    def get_all_rsi(self, symbol: str) -> Dict[str, Optional[float]]:
        """Obtener RSI para todos los timeframes."""
        result = {}
        for tf in self.timeframes:
            data = self.symbol_data.get(symbol, {}).get(tf)
            if data:
                result[tf] = data.get_rsi()
            else:
                result[tf] = None
        return result

    def get_all_ema(self, symbol: str, period: int = 20) -> Dict[str, Optional[float]]:
        """Obtener EMA para todos los timeframes."""
        result = {}
        for tf in self.timeframes:
            data = self.symbol_data.get(symbol, {}).get(tf)
            if data:
                result[tf] = data.get_ema(period)
            else:
                result[tf] = None
        return result

    def get_trend_direction(self, symbol: str, timeframe: str) -> TrendDirection:
        """Determinar dirección de tendencia basada en precio vs EMA 20."""
        data = self.symbol_data.get(symbol, {}).get(timeframe)
        if not data or not data.closes or len(data.closes) < 20:
            return TrendDirection.RANGING

        current_price = data.closes[-1]
        ema_20 = data.get_ema(20)

        if ema_20 is None:
            return TrendDirection.RANGING

        # Calculate distance
        distance_pct = ((current_price - ema_20) / ema_20) * 100

        if distance_pct > 0.12:
            return TrendDirection.UP
        elif distance_pct < -0.12:
            return TrendDirection.DOWN
        else:
            return TrendDirection.RANGING

    def get_alignment(self, symbol: str) -> str:
        """Obtener alineación cross-timeframe."""
        trends = {}
        for tf in self.timeframes:
            trends[tf] = self.get_trend_direction(symbol, tf)

        # Check alignment
        up_count = sum(1 for t in trends.values() if t == TrendDirection.UP)
        down_count = sum(1 for t in trends.values() if t == TrendDirection.DOWN)

        if up_count == len(self.timeframes):
            return "STRONG_BULLISH"
        elif down_count == len(self.timeframes):
            return "STRONG_BEARISH"
        elif up_count > down_count and up_count > 0:
            return "MIXED_BULLISH"
        elif down_count > up_count and down_count > 0:
            return "MIXED_BEARISH"
        else:
            return "MIXED"

    def get_indicators_state(self, symbol: str) -> Dict[str, Any]:
        """Exportar estado completo de indicadores por timeframe."""
        state = {
            "symbol": symbol,
            "timeframes": {}
        }

        for tf in self.timeframes:
            data = self.symbol_data.get(symbol, {}).get(tf)
            if data and data.closes:
                state["timeframes"][tf] = {
                    "price": data.closes[-1],
                    "rsi": data.get_rsi(),
                    "ema_20": data.get_ema(20),
                    "adx": data.get_adx(),
                    "trend": self.get_trend_direction(symbol, tf).value
                }

        state["overall_alignment"] = self.get_alignment(symbol)
        return state


# ==================== Signal Confirmation ====================

    def confirm_signal(self, symbol: str, signal_type: str) -> ConfirmationResult:
        """
        Evaluar si una señal tiene confirmación de timeframes superiores.

        Args:
            symbol: Símbolo a evaluar
            signal_type: "BUY" o "SELL"

        Returns:
            ConfirmationResult con nivel de confluencia y multiplicador
        """
        if not self.enabled:
            return ConfirmationResult(
                confirmed=True,
                confluence_level=ConfluenceLevel.ALTA,
                position_multiplier=1.0,
                reason="Multi-TF disabled"
            )

        # Get trend directions
        trend_1h = self.get_trend_direction(symbol, "1h")
        trend_15m = self.get_trend_direction(symbol, "15m")
        trend_1m = self.get_trend_direction(symbol, "1m")

        ema_1h = self._get_ema_direction(symbol, "1h")
        ema_15m = self._get_ema_direction(symbol, "15m")
        ema_1m = self._get_ema_direction(symbol, "1m")

        # Evaluate confirmation
        if signal_type == "BUY":
            confirm_1h = trend_1h == TrendDirection.UP
            confirm_15m = trend_15m == TrendDirection.UP
            not_bearish_1h = trend_1h != TrendDirection.DOWN
            not_bearish_15m = trend_15m != TrendDirection.DOWN
        else:  # SELL
            confirm_1h = trend_1h == TrendDirection.DOWN
            confirm_15m = trend_15m == TrendDirection.DOWN
            not_bearish_1h = False
            not_bearish_15m = False

        # SELL signals close existing Spot positions and should never be blocked by higher-TF trend
        if signal_type == "SELL":
            return ConfirmationResult(
                confirmed=True,
                confluence_level=ConfluenceLevel.ALTA,
                position_multiplier=1.0,
                reason=f"ALTA: Salida SELL permitida ({trend_15m.value}/{trend_1h.value})",
                ema_1h_direction=ema_1h,
                ema_15m_direction=ema_15m,
                ema_1m_direction=ema_1m,
            )

        # Determine confluence level for BUY
        data_1m = self.symbol_data.get(symbol, {}).get("1m")
        rsi_1m = data_1m.get_rsi() if data_1m else None

        if confirm_1h and confirm_15m:
            level = ConfluenceLevel.ALTA
            multiplier = 1.0
            reason = f"ALTA: EMA 1h y 15m confirman {signal_type}"
        elif confirm_15m or (confirm_1h and not_bearish_15m):
            level = ConfluenceLevel.MEDIA
            multiplier = 0.85
            reason = f"MEDIA: Timeframe superior confirma {signal_type} (15m={trend_15m.value}, 1h={trend_1h.value})"
        elif not_bearish_1h and not_bearish_15m:
            # Lateral / Ranging market on 15m & 1h: allow mean-reversion BUY with cautious sizing
            level = ConfluenceLevel.MEDIA
            multiplier = 0.8
            reason = f"MEDIA: Mercado en rango (15m={trend_15m.value}, 1h={trend_1h.value}) permite entrada"
        elif not_bearish_15m and (rsi_1m is None or rsi_1m <= 50.0):
            # 15m has stabilized in RANGING even if 1h is still recovering from DOWN
            level = ConfluenceLevel.MEDIA
            multiplier = 0.75
            reason = f"MEDIA: 15m estabilizado en rango ({trend_15m.value}/{trend_1h.value}) permite rebote"
        else:
            # Both 15m and 1h are bearish (or 15m is DOWN): only allow on deep oversold bounce
            if rsi_1m is not None and rsi_1m < 28.0:
                level = ConfluenceLevel.MEDIA
                multiplier = 0.75
                reason = f"MEDIA: Sobreventa extrema (RSI={rsi_1m:.1f}) habilita rebote"
                return ConfirmationResult(
                    confirmed=True,
                    confluence_level=level,
                    position_multiplier=multiplier,
                    reason=reason,
                    ema_1h_direction=ema_1h,
                    ema_15m_direction=ema_15m,
                    ema_1m_direction=ema_1m
                )

            if settings.ALLOW_LOW_CONFLUENCE_TRADES:
                level = ConfluenceLevel.BAJA
                multiplier = 0.65
                reason = f"BAJA: Sin confirmación - usando 65% (permitido)"
            else:
                level = ConfluenceLevel.BAJA
                multiplier = 0.0
                reason = f"BAJA: Tendencia macro bajista ({trend_15m.value}/{trend_1h.value}) - señal bloqueada"

            return ConfirmationResult(
                confirmed=settings.ALLOW_LOW_CONFLUENCE_TRADES,
                confluence_level=level,
                position_multiplier=multiplier,
                reason=reason,
                ema_1h_direction=ema_1h,
                ema_15m_direction=ema_15m,
                ema_1m_direction=ema_1m
            )

        return ConfirmationResult(
            confirmed=True,
            confluence_level=level,
            position_multiplier=multiplier,
            reason=reason,
            ema_1h_direction=ema_1h,
            ema_15m_direction=ema_15m,
            ema_1m_direction=ema_1m
        )

    def _get_ema_direction(self, symbol: str, timeframe: str) -> Optional[str]:
        """Get EMA direction as string for logging."""
        trend = self.get_trend_direction(symbol, timeframe)
        return trend.value


# Global instance
multi_tf_manager = MultiTimeframeManager()