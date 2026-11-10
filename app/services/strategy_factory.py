import logging
from typing import Dict, Any, Optional, List
from app.services.rsi_strategy import RSIStrategy
from app.services.divergence_strategy import RsiDivergenceStrategy
from app.services.bollinger_strategy import BollingerBandsStrategy
from app.services.macd_strategy import MacdMaCrossStrategy
from app.services.breakout_strategy import BreakoutStrategy
from app.services.regime_service import regime_service, MarketRegime
from app.services.indicators import get_symbol_data
from app.services.persistence import persistence
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class StrategyManager:
    """Orchestrator to choose and switch strategies at runtime."""
    def __init__(self):
        self.strategy_type = settings.TRADING_STRATEGY
        self.rsi_only = RSIStrategy()
        self.rsi_divergence = RsiDivergenceStrategy()
        self.bollinger = BollingerBandsStrategy()
        self.macd_cross = MacdMaCrossStrategy()
        self.breakout = BreakoutStrategy()
        
        # Local cache for active strategies per symbol (for 'Auto' mode)
        self.symbol_strategies: Dict[str, Any] = {}
        # Strategy locks for when a position is open
        self.strategy_locks: Dict[str, bool] = {}

    def get_strategy(self, symbol: str) -> Any:
        """Returns the appropriate strategy instance for a given symbol."""
        if self.strategy_type != "Auto":
            if self.strategy_type == "RsiWithDivergence":
                return self.rsi_divergence
            if self.strategy_type == "BollingerBands":
                return self.bollinger
            if self.strategy_type == "MacdMaCross":
                return self.macd_cross
            if self.strategy_type == "Breakout":
                return self.breakout
            return self.rsi_only

        # Auto Mode Logic
        if symbol not in self.symbol_strategies:
            self.symbol_strategies[symbol] = self.rsi_only # Default starting point

        return self.symbol_strategies[symbol]

    def re_evaluate_regime(self, symbol: str):
        """Re-evaluate the market regime and update the active strategy for symbol."""
        if self.strategy_type != "Auto":
            return

        # Check for Lock: Strategy MUST NOT switch while in position
        current_in_pos = self.get_strategy(symbol).positions.get(symbol, False)
        if current_in_pos:
            if not self.strategy_locks.get(symbol, False):
                logger.info(f"STRATEGY | Locking {symbol} strategy because POSITION IS OPEN.")
                self.strategy_locks[symbol] = True
            return

        # Unlock if no position is open
        if self.strategy_locks.get(symbol, False):
            logger.info(f"STRATEGY | Unlocking {symbol} strategy (position closed).")
            self.strategy_locks[symbol] = False

        # Classify the regime
        regime = regime_service.classify_regime(symbol)
        
        new_strat = self.rsi_only # Default for ranging
        if regime == MarketRegime.TRENDING:
            # Check trend strength
            adx = regime_service.get_adx_value(symbol)
            if adx > 40:
                new_strat = self.macd_cross # Strong trend needs confirmation
            else:
                new_strat = self.rsi_divergence # Normal trend follows momentum
        elif regime == MarketRegime.RANGING:
            new_strat = self.bollinger
        elif regime == MarketRegime.HIGH_VOLATILITY:
            # Could add a 'Pause' strategy or just stay in safety
            new_strat = self.rsi_divergence # Trend confirmers are safer in high volatility

        old_strat = self.symbol_strategies.get(symbol)
        if new_strat != old_strat:
            logger.info(f"STRATEGY | Switching {symbol} to: {new_strat.__class__.__name__} based on regime {regime.value}")
            # Ensure position status is maintained between strategy swap
            new_strat.positions[symbol] = False # Known from unlock check above
            self.symbol_strategies[symbol] = new_strat
            
            # Send strategy switch alert only if explicitly enabled (avoids 1m regime noise)
            if settings.NOTIFY_STRATEGY_CHANGES:
                import asyncio
                from app.services.notifications import notification_service
                old_name = notification_service.escape_markdown(old_strat.__class__.__name__ if old_strat else "Ninguna")
                new_name = notification_service.escape_markdown(new_strat.__class__.__name__)
                sym_esc = notification_service.escape_markdown(symbol)
                reg_esc = notification_service.escape_markdown(regime.value)
                msg = f"🔄 *VinBot Cambio de Estrategia \\({sym_esc}\\)*\nRegimen: `{reg_esc}`\nAnterior: `{old_name}`\nNueva: `{new_name}`"
                asyncio.create_task(notification_service.send_message(msg))

    async def load_initial_states(self, symbols: List[str]):
        """Load states for both strategies."""
        await self.rsi_only.load_initial_state(symbols)
        await self.rsi_divergence.load_initial_state(symbols)
        await self.bollinger.load_initial_state(symbols)
        await self.macd_cross.load_initial_state(symbols)
        await self.breakout.load_initial_state(symbols)

strategy_manager = StrategyManager()
# To maintain backward compatibility with main.py which expected 'current_strategy' as singleton:
# We now provide an instance that redirects 'analyze' and 'update_position' per symbol.
class DynamicStrategyProxy:
    def __init__(self):
        self.highest_prices: Dict[str, float] = {}
        self.position_multipliers: Dict[str, float] = {}

    def get_position_multiplier(self, symbol: str) -> float:
        """Return the latest conviction multiplier (ML Ensemble + Multi-TF Confluence) for symbol."""
        return self.position_multipliers.get(symbol, 1.0)

    def analyze(self, symbol: str) -> Optional[str]:
        self.position_multipliers[symbol] = 1.0
        confluence_mult = 1.0
        ensemble_mult = 1.0

        # 1. Trailing Stop Evaluation
        if settings.ENABLE_TRAILING_STOP:
            strategy = strategy_manager.get_strategy(symbol)
            in_position = strategy.positions.get(symbol, False)
            
            if in_position:
                symbol_data = get_symbol_data(symbol)
                if not symbol_data.closes:
                    return None
                    
                current_price = symbol_data.closes[-1]
                atr = symbol_data.get_atr()
                
                # Retrieve or initialize high watermark
                highest = self.highest_prices.get(symbol, current_price)
                if current_price > highest:
                    highest = current_price
                    self.highest_prices[symbol] = highest
                    # Persist the new high
                    # Note: Using asyncio within a synchronous 'analyze' call can be tricky, 
                    # but persistence here is mostly for recovery after crashes.
                
                if atr is not None:
                    stop_level = highest - (atr * settings.ATR_TRAILING_MULTIPLIER)
                    if current_price < stop_level:
                        logger.info(f"RISK | TRAILING STOP TRIGGERED for {symbol} at {current_price:.2f} (Stop: {stop_level:.2f}, ATR: {atr:.2f})")
                        return "SELL"

        # 2. Normal Strategy Analysis
        signal = strategy_manager.get_strategy(symbol).analyze(symbol)
        ai_triggered = False

        # 2.5 Proactive Local AI Trigger (High-Conviction Autonomous BUY / Profit-Protection SELL)
        if signal is None and getattr(settings, "ML_ENABLED", False):
            try:
                from app.services.ml.predictor import ml_predictor, get_prediction_with_confidence
                from app.services.ml.feature_engineering import extract_features
                from app.services.risk_manager import risk_manager

                symbol_data = get_symbol_data(symbol)
                if symbol_data and symbol_data.closes and len(symbol_data.closes) >= 50:
                    features = extract_features(symbol_data)
                    if features:
                        ml_res = get_prediction_with_confidence(symbol, features)
                        if ml_res and isinstance(features, dict) and "_ml_buy_prob" in features:
                            ml_sig, ml_conf = ml_res
                            buy_prob = float(features.get("_ml_buy_prob", 0.0))
                            sell_prob = float(features.get("_ml_sell_prob", 0.0))
                            snap = ml_predictor.live_stats.get(symbol, {}).get("snapshot") or {}
                            obi = float(snap.get("obi", 0.0))
                            live_eval = int(snap.get("live_evaluated", 0))
                            live_acc = float(snap.get("live_accuracy", 0.0))
                            cur_rsi = symbol_data.get_rsi() or 50.0
                            cur_price = symbol_data.closes[-1]
                            in_pos = strategy_manager.get_strategy(symbol).positions.get(symbol, False)

                            if not in_pos:
                                # Autonomous AI BUY when Triple-Barrier P(TP) strongly dominates P(SL) and OBI/RSI support entry
                                accuracy_ok = (live_eval < 5) or (live_acc >= 55.0)
                                if (
                                    ml_sig == "BUY"
                                    and buy_prob >= 0.50
                                    and buy_prob >= sell_prob * 1.8
                                    and accuracy_ok
                                    and obi >= -0.12
                                    and cur_rsi <= 56.0
                                ):
                                    logger.info(
                                        f"AI TRIGGER | {symbol} Autonomous AI BUY initiated "
                                        f"(P(TP)={buy_prob*100:.1f}%, P(SL)={sell_prob*100:.1f}%, OBI={obi:+.2f}, RSI={cur_rsi:.1f}, LiveAcc={live_acc:.1f}%)"
                                    )
                                    signal = "BUY"
                                    ai_triggered = True
                            else:
                                # Autonomous AI Profit-Protection SELL when position is in net profit and AI detects reversal
                                entry_p = risk_manager.entry_prices.get(symbol, 0.0)
                                if (
                                    ml_sig == "SELL"
                                    and sell_prob >= 0.48
                                    and sell_prob >= buy_prob * 1.6
                                    and entry_p > 0
                                    and cur_price >= entry_p * 1.0035
                                    and cur_rsi >= 54.0
                                ):
                                    logger.info(
                                        f"AI TRIGGER | {symbol} Autonomous AI Profit-Lock SELL initiated at {cur_price:.4f} "
                                        f"(Entry={entry_p:.4f}, P(SL)={sell_prob*100:.1f}%, RSI={cur_rsi:.1f})"
                                    )
                                    signal = "SELL"
                                    ai_triggered = True
            except Exception as e:
                logger.warning(f"AI TRIGGER | Error evaluating proactive AI signal for {symbol}: {e}")

        # 3. Volume Confirmation Veto (Only for BUY signals, strategy-aware)
        if signal == "BUY" and settings.ENABLE_VOLUME_CONFIRMATION:
            symbol_data = get_symbol_data(symbol)
            vwap = symbol_data.get_vwap(settings.VWAP_PERIOD)
            obv = symbol_data.get_obv()
            obv_sma = symbol_data.get_obv_sma(20)
            current_price = symbol_data.closes[-1] if symbol_data.closes else 0.0
            active_strat_name = strategy_manager.get_strategy(symbol).__class__.__name__

            if active_strat_name in ("MacdMaCrossStrategy", "BreakoutStrategy") and not ai_triggered:
                # Trend/Breakout strategies require price above VWAP or strong accumulation
                if vwap is not None and current_price < vwap * 0.999:
                    logger.info(f"VETO | {symbol} {active_strat_name} BUY vetoed: Price {current_price:.2f} below VWAP {vwap:.2f}")
                    return None
                if obv is not None and obv_sma is not None and obv < obv_sma:
                    logger.info(f"VETO | {symbol} {active_strat_name} BUY vetoed: OBV {obv:.2f} below average {obv_sma:.2f}")
                    return None
            else:
                # Mean-reversion strategies (BollingerBands, RSI, Divergence) buy BELOW VWAP by design.
                # Only veto if volume is completely dead (<25% of 20-bar avg) with no lower-wick rejection and weak RSI.
                vols = list(symbol_data.volumes)
                if len(vols) >= 20:
                    avg_vol = sum(vols[-20:]) / 20.0
                    cur_vol = vols[-1]
                    cur_rsi = symbol_data.get_rsi() or 50.0
                    if avg_vol > 0 and cur_vol < avg_vol * 0.25 and cur_rsi > 26.0 and (obv is not None and obv_sma is not None and obv < obv_sma):
                        logger.info(
                            f"VETO | {symbol} {active_strat_name} BUY vetoed: Dead volume ({cur_vol:.2f} < 25% of avg {avg_vol:.2f}) and weak OBV"
                        )
                        return None

        # 4. BTC Directional Filter Veto (Macro Regime)
        if signal == "BUY" and settings.ENABLE_BTC_DIRECTIONAL_FILTER:
            quote = "USDC" if "USDC" in symbol else "USDT"
            benchmark = f"BTC{quote}"
            btc_data = get_symbol_data(benchmark)
            btc_ema = btc_data.get_ema(settings.BTC_DIRECTION_EMA)
            current_btc_price = btc_data.closes[-1] if btc_data.closes else 0.0
            
            if btc_ema is not None and current_btc_price < btc_ema:
                logger.info(f"VETO | {symbol} BUY vetoed: {benchmark} Macro Trend is Bearish (Price {current_btc_price:.2f} < EMA {btc_ema:.2f})")
                return None

        # 5. Relative Strength Filter Veto (vs BTC)
        quote = "USDC" if "USDC" in symbol else "USDT"
        benchmark = f"BTC{quote}"
        if signal == "BUY" and symbol != benchmark and settings.ENABLE_RELATIVE_STRENGTH_FILTER:
            symbol_data = get_symbol_data(symbol)
            btc_data = get_symbol_data(benchmark)
            
            alt_roc = symbol_data.get_roc(settings.RS_LOOKBACK_PERIOD)
            btc_roc = btc_data.get_roc(settings.RS_LOOKBACK_PERIOD)
            
            if alt_roc is not None and btc_roc is not None:
                if alt_roc < btc_roc:
                    logger.info(f"VETO | {symbol} BUY vetoed: Relative Strength Underperformance (Alt ROC {alt_roc:.2f}% < {benchmark} ROC {btc_roc:.2f}%)")
                    return None
            elif alt_roc is None or btc_roc is None:
                # If we don't have enough data history yet, veto for safety
                logger.warning(f"VETO | {symbol} BUY vetoed: Insufficient history for RS calculation (Benchmark: {benchmark})")
                return None

        # 6. Multi-Timeframe Confluence Filter
        if signal is not None and settings.MULTI_TF_ENABLED:
            try:
                from app.services.multi_timeframe import multi_tf_manager, ConfluenceLevel
                confirmation = multi_tf_manager.confirm_signal(symbol, signal)

                if not confirmation.confirmed:
                    logger.info(f"CONFLOUENCE | {symbol} {signal} blocked: {confirmation.reason}")
                    return None

                if confirmation.confluence_level == ConfluenceLevel.MEDIA:
                    confluence_mult = max(0.7, confirmation.position_multiplier)
                    logger.info(f"CONFLOUENCE | {symbol} {signal} confirmed with MEDIA ({confirmation.reason}, mult={confluence_mult:.2f}x)")
                elif confirmation.confluence_level == ConfluenceLevel.ALTA:
                    confluence_mult = 1.0
                    logger.info(f"CONFLOUENCE | {symbol} {signal} confirmed with ALTA ({confirmation.reason})")
                else:
                    confluence_mult = max(0.65, confirmation.position_multiplier)
                    logger.info(f"CONFLOUENCE | {symbol} {signal} confirmed ({confirmation.reason}, mult={confluence_mult:.2f}x)")
            except Exception as e:
                logger.warning(f"CONFLOUENCE | Error in confluence check: {e}")

        # 7. ML Ensemble Filter
        if signal is not None and settings.ML_ENABLED:
            try:
                from app.services.ml.ensemble import ensemble_predict
                from app.services.ml.predictor import get_prediction_with_confidence
                from app.services.ml.feature_engineering import extract_features

                # Get features using full OHLCV SymbolData (no close duplication or fake volume)
                symbol_data = get_symbol_data(symbol)
                if symbol_data and symbol_data.closes and len(symbol_data.closes) >= 50:
                    features = extract_features(symbol_data)
                    if features:
                        ml_result = get_prediction_with_confidence(symbol, features)
                        if ml_result:
                            ml_signal, ml_confidence = ml_result

                            # Combine with strategy signal
                            final_signal, multiplier = ensemble_predict(
                                symbol, signal, features, ml_signal, ml_confidence
                            )
                            ensemble_mult = multiplier

                            if final_signal != signal:
                                logger.info(f"ENSEMBLE | {symbol} signal adjusted: {signal} -> {final_signal} (mult: {multiplier})")

                            signal = final_signal

            except Exception as e:
                logger.warning(f"ENSEMBLE | Error in ML ensemble: {e}")

        # 8. 4th Brain (Kronos Foundation Model) Confluence & Protection Veto
        if signal is not None and getattr(settings, "ML_ENABLED", False):
            try:
                from app.services.ml.kronos_client import kronos_client
                kronos_pred = kronos_client.cached_predictions.get(symbol)
                if kronos_pred and isinstance(kronos_pred, dict):
                    k_dir = kronos_pred.get("direction", "NEUTRAL")
                    k_conf = float(kronos_pred.get("confidence", 0.5))
                    k_move = float(kronos_pred.get("expected_pct", 0.0))

                    if signal == "BUY":
                        # If Kronos predicts a severe breakdown (>0.40% drop with >=70% confidence), veto the buy
                        if k_dir == "BEARISH" and k_conf >= 0.70 and k_move <= -0.40:
                            logger.info(
                                f"KRONOS VETO | {symbol} BUY blocked: Kronos foundation model forecasts breakdown ({k_move:+.2f}%, conf={k_conf*100:.0f}%)"
                            )
                            return None
                        # If Kronos aligns with the buy, boost conviction multiplier
                        elif k_dir == "BULLISH" and k_conf >= 0.65:
                            ensemble_mult = min(1.35, ensemble_mult * 1.15)
                            logger.info(
                                f"KRONOS BOOST | {symbol} BUY confirmed by Kronos ({k_move:+.2f}%, conf={k_conf*100:.0f}%), mult -> {ensemble_mult:.2f}x"
                            )
            except Exception as e:
                logger.debug(f"Kronos evaluation error in strategy factory for {symbol}: {e}")

        if signal is not None:
            combined_mult = round(max(0.3, min(1.5, confluence_mult * ensemble_mult)), 4)
            self.position_multipliers[symbol] = combined_mult
            try:
                from app.core.metrics import trading_position_multiplier
                trading_position_multiplier.labels(symbol=symbol).set(combined_mult)
            except Exception:
                pass

        return signal
    
    async def update_position(self, symbol: str, in_position: bool):
        # Update underlying strategies
        await strategy_manager.rsi_only.update_position(symbol, in_position)
        await strategy_manager.rsi_divergence.update_position(symbol, in_position)
        await strategy_manager.bollinger.update_position(symbol, in_position)
        await strategy_manager.macd_cross.update_position(symbol, in_position)
        await strategy_manager.breakout.update_position(symbol, in_position)
        
        # Update high watermark state
        if in_position:
            # Entering trade: set initial highest price
            symbol_data = get_symbol_data(symbol)
            current_price = symbol_data.closes[-1] if symbol_data.closes else 0.0
            self.highest_prices[symbol] = current_price
            await persistence.set_state(f"{symbol.lower()}_highest_price", current_price)
        else:
            # Exiting trade: clear state
            self.highest_prices[symbol] = 0.0
            await persistence.set_state(f"{symbol.lower()}_highest_price", 0.0)

    async def load_initial_state(self, symbols: List[str]):
        await strategy_manager.load_initial_states(symbols)
        # Recover high watermarks
        for symbol in symbols:
            key = f"{symbol.lower()}_highest_price"
            price = await persistence.get_state(key, 0.0)
            if price > 0:
                self.highest_prices[symbol] = price
                logger.info(f"RECOVERY | {symbol} recovered Trailing High Watermark: {price:.2f}")

current_strategy = DynamicStrategyProxy()
