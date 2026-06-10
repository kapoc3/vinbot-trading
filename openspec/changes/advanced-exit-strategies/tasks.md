# Advanced Exit Strategies - Tasks

## Configuración

- [ ] 1.1 Añadir TRAILING_TP_ENABLED (bool, default: True) en app/core/config.py
- [ ] 1.2 Añadir TRAILING_TP_ATR_MULTIPLIER (float, default: 2.0) en app/core/config.py
- [ ] 1.3 Añadir TRAILING_TP_ACTIVATION_PCT (float, default: 1.5) en app/core/config.py
- [ ] 1.4 Añadir MAX_HOLD_HOURS (int, default: 4) en app/core/config.py
- [ ] 1.5 Añadir TIME_EXIT_ENABLED (bool, default: True) en app/core/config.py
- [ ] 1.6 Añadir TIME_EXIT_COOLDOWN_MINUTES (int, default: 15) en app/core/config.py
- [ ] 1.7 Añadir DYNAMIC_PARTIAL_TP_ENABLED (bool, default: True) en app/core/config.py
- [ ] 1.8 Añadir SIGNAL_STRENGTH_EXIT_ENABLED (bool, default: True) en app/core/config.py

## Trailing Take Profit

- [ ] 2.1 Crear clase TrailingTakeProfit en app/services/risk_manager.py
- [ ] 2.2 Implementar método activate(entry_price, current_price) que establece highest_price
- [ ] 2.3 Implementar método update(current_price, atr) que recalcula trailing_level
- [ ] 2.4 Implementar método should_trigger(current_price) que retorna bool
- [ ] 2.5 Integrar en risk_manager.check_sl_tp() como parte del flujo de exit
- [ ] 2.6 Persistir estado de trailing TP (highest_price, trailing_level, is_active) por símbolo

## Time-Based Exit

- [ ] 3.1 Añadir campo entry_time a position_data en risk_manager.py
- [ ] 3.2 Modificar set_entry_price() para guardar timestamp de entrada
- [ ] 3.3 Implementar método check_time_exit(symbol) que calcula tiempo transcurrido
- [ ] 3.4 Implementar cooldown logic para evitar re-entrada inmediata
- [ ] 3.5 Integrar check_time_exit() en dummy_strategy_callback flow
- [ ] 3.6 Persistir entry_time en SQLite a través de persistence service

## RSI Divergence Exit

- [ ] 4.1 Añadir método detect_bearish_divergence(symbol) en app/services/indicators.py
- [ ] 4.2 Implementar lógica de higher high (precio) vs lower high (RSI)
- [ ] 4.3 Añadir validación de diferencia mínima (3% precio, 2% RSI)
- [ ] 4.4 Integrar en risk_manager.check_sl_tp() después de trailing TP check
- [ ] 4.5 Añadir logging de divergence detection

## Signal Strength Exit

- [ ] 5.1 Crear método calculate_signal_strength(strategy_name, indicator_value, threshold) en risk_manager.py
- [ ] 5.2 Implementar clasificación: STRONG, MODERATE, WEAK
- [ ] 5.3 Modificar set_entry_price() para guardar signal_strengthclassification
- [ ] 5.4 Implementar método get_adjusted_exit_threshold(symbol) que ajusta según strength
- [ ] 5.5 Integrar en estrategia de exit (modificar RSIStrategy.analyze para usar threshold dinámico)

## Dynamic Partial TP

- [ ] 6.1 Crear método calculate_dynamic_tp_levels(entry_price, atr_pct) en risk_manager.py
- [ ] 6.2 Implementar fórmula: adjusted_level = base_level * (1 + volatility_factor)
- [ ] 6.3 Modificar _get_tp_targets() para usar niveles dinámicos si DYNAMIC_PARTIAL_TP_ENABLED
- [ ] 6.4 Persistir calculated_levels junto con position_data
- [ ] 6.5 Añadir logging de niveles calculados con ATR info

## Testing

- [ ] 7.1 Crear tests unitarios para TrailingTakeProfit
- [ ] 7.2 Crear tests unitarios para time-based exit logic
- [ ] 7.3 Crear tests unitarios para bearish divergence detection
- [ ] 7.4 Crear tests unitarios para signal strength classification
- [ ] 7.5 Crear tests unitarios para dynamic TP level calculation
- [ ] 7.6 Testing de integración con paper trading en testnet

## Observability

- [ ] 8.1 Añadir métrica Prometheus: exit_type_total (labels: symbol, exit_reason)
- [ ] 8.2 Añadir métrica: signal_strength_distribution
- [ ] 8.3 Añadir logs estructurados para cada tipo de exit

## Documentación

- [ ] 9.1 Actualizar README.md con nuevas configuraciones
- [ ] 9.2 Crear guía de configuración de exit strategies
- [ ] 9.3 Documentar preset modes (aggressive, balanced, conservative)