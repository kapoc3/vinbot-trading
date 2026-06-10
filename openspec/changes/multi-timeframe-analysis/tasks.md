# Multi-Timeframe Analysis - Tasks

## Configuración

- [ ] 1.1 Añadir MULTI_TF_ENABLED (bool, default: True) en app/core/config.py
- [ ] 1.2 Añadir ACTIVE_TIMEFRAMES (str, default: "1m,15m,1h") en app/core/config.py
- [ ] 1.3 Añadir MAX_CANDLES_PER_TF (int, default: 500) en app/core/config.py
- [ ] 1.4 Añadir MIN_CONFLUENCE_LEVEL (str, default: "MEDIA") en app/core/config.py
- [ ] 1.5 Añadir ALLOW_LOW_CONFLUENCE_TRADES (bool, default: False) en app/core/config.py

## Multi-Timeframe Data Manager

- [ ] 2.1 Crear app/services/backtest/multi_timeframe_manager.py
- [ ] 2.2 Implementar clase MultiTimeframeData con dictionary de SymbolData por timeframe
- [ ] 2.3 Implementar método fetch_all_timeframes(symbol, timeframes)
- [ ] 2.4 Implementar método update_from_1m_stream(kline) para actualizar todos
- [ ] 2.5 Implementar buffer management (limitar a MAX_CANDLES_PER_TF)
- [ ] 2.6 Implementar cleanup para símbolos no monitoreados

## Indicator Aggregation

- [ ] 3.1 Añadir método get_all_rsi(symbol) en MultiTimeframeData
- [ ] 3.2 Añadir método get_all_ema(symbol, period) en MultiTimeframeData
- [ ] 3.3 Implementar get_trend_direction(symbol, timeframe) - precio vs EMA
- [ ] 3.4 Implementar get_alignment(symbol) - análisis cross-timeframe
- [ ] 3.5 Implementar get_indicators_state(symbol) para debugging

## Signal Confirmation Logic

- [ ] 4.1 Crear SignalConfirmer en app/services/strategy_factory.py
- [ ] 4.2 Implementar método confirm_signal(symbol, signal_type, timeframe_1m_data)
- [ ] 4.3 Implementar lógica de EMA confirmation (arriba/abajo de precio)
- [ ] 4.4 Implementar cálculo de nivel de confluencia (ALTA/MEDIA/BAJA)
- [ ] 4.5 Implementar cálculo de position_multiplier según confluencia
- [ ] 4.6 Añadir logging de decisiones de confirmación

## Confluence Filter Integration

- [ ] 5.1 Modificar DynamicStrategyProxy.analyze() para incluir confluence check
- [ ] 5.2 Añadir paso de confirmación después de obtener señal de estrategia
- [ ] 5.3 Aplicar position_multiplier al tamaño calculado
- [ ] 5.4 Bloquear señales con confluencia menor a MIN_CONFLUENCE_LEVEL
- [ ] 5.5 Integrar con filtros existentes (BTC directional, RS filter)

## Historical Data Fetch Enhancement

- [ ] 6.1 Modificar data_fetcher para soportar múltiples timeframes en paralelo
- [ ] 6.2 Implementar cache por timeframe (separar cache de cada timeframe)
- [ ] 6.3 Añadir manejo de gaps de datos entre timeframes

## Observabilidad

- [ ] 7.1 Añadir métricas Prometheus: confluence_level_total (labels: symbol, level)
- [ ] 7.2 Añadir métricas: signals_blocked_by_confluence_total
- [ ] 7.3 Añadir logs estructurados para cada evaluación de confluencia

## Testing

- [ ] 8.1 Tests unitarios para MultiTimeframeData
- [ ] 8.2 Tests unitarios para SignalConfirmer
- [ ] 8.3 Tests de integración con estrategias existentes
- [ ] 8.4 Tests de comparación: estrategia con/sin multi-TF

## Documentación

- [ ] 9.1 Actualizar README.md con nueva funcionalidad
- [ ] 9.2 Documentar niveles de confluencia y sus efectos
- [ ] 9.3 Crear guía de configuración recomendada