# Backtesting Engine - Tasks

## Configuración e Instalación

- [ ] 1.1 Añadir dependencias en pyproject.toml: pandas, matplotlib (opcionales)
- [ ] 1.2 Crear app/core/config.py parámetros: BACKTEST_CACHE_DIR, BACKTEST_INITIAL_CAPITAL, BACKTEST_SLIPPAGE, BACKTEST_COMMISSION

## Historical Data Fetch

- [ ] 2.1 Crear app/services/backtest/data_fetcher.py
- [ ] 2.2 Implementar método fetch_klines_binance(symbol, timeframe, start, end)
- [ ] 2.3 Implementar cache con CSV storage
- [ ] 2.4 Implementar load_from_cache(symbol, timeframe, start, end)
- [ ] 2.5 Soportar timeframes: 1m, 5m, 15m, 1h, 4h, 1d
- [ ] 2.6 Manejar rate limits de Binance

## Backtest Engine Core

- [ ] 3.1 Crear app/services/backtest/engine.py
- [ ] 3.2 Crear clase BacktestResult para almacenar resultados
- [ ] 3.3 Implementar método run(strategy, symbol, data, config)
- [ ] 3.4 Implementar TradeSimulator con slippage y comisiones
- [ ] 3.5 Implementar position tracking (open/close)
- [ ] 3.6 Implementar capital management (position sizing)
- [ ] 3.7 Soportar múltiples estrategias (RSI, Bollinger, MACD, etc.)
- [ ] 3.8 Integrar con estrategias existentes del proyecto

## Backtest Metrics

- [ ] 4.1 Crear app/services/backtest/metrics.py
- [ ] 4.2 Implementar calculate_total_pnl(trades)
- [ ] 4.3 Implementar calculate_win_rate(trades)
- [ ] 4.4 Implementar calculate_profit_factor(trades)
- [ ] 4.5 Implementar calculate_sharpe_ratio(returns)
- [ ] 4.6 Implementar calculate_max_drawdown(equity_curve)
- [ ] 4.7 Implementar calculate_expectancy(trades)
- [ ] 4.8 Implementar calculate_trade_duration(trades)
- [ ] 4.9 Implementar calculate_consecutive_wins_losses(trades)

## Backtest Comparison

- [ ] 5.1 Crear app/services/backtest/comparison.py
- [ ] 5.2 Implementar compare_strategies(strategies, data, config)
- [ ] 5.3 Implementar calculate_ranking_score(metrics)
- [ ] 5.4 Implementar parameter_sweep(strategy, param_grid, data)
- [ ] 5.5 Soportar parallel execution (multiprocessing)

## Backtest Reports

- [ ] 6.1 Crear app/services/backtest/reporter.py
- [ ] 6.2 Implementar generate_html_report(result)
- [ ] 6.3 Generar equity curve chart (matplotlib)
- [ ] 6.4 Generar drawdown chart
- [ ] 6.5 Generar trade distribution histogram
- [ ] 6.6 Generar metrics summary table
- [ ] 6.7 Implementar save_report(result, filepath)
- [ ] 6.8 Añadir CSS styling embebido

## API Endpoint

- [ ] 7.1 Crear app/api/v1/endpoints/backtest.py
- [ ] 7.2 Implementar POST /api/v1/backtest/run
- [ ] 7.3 Implementar POST /api/v1/backtest/compare
- [ ] 7.4 Implementar GET /api/v1/backtest/report/{id}

## CLI Command

- [ ] 8.1 Crear app/cli/backtest.py
- [ ] 8.2 Implementar comando: vinbot backtest run --strategy RSI --symbol BTCUSDT --days 365
- [ ] 8.3 Implementar comando: vinbot backtest compare --strategies RSI,BB,MACD
- [ ] 8.4 Implementar comando: vinbot backtest report --output report.html

## Testing

- [ ] 9.1 Tests unitarios para data_fetcher (mock Binance API)
- [ ] 9.2 Tests unitarios para metrics calculation
- [ ] 9.3 Tests de integración para engine completo
- [ ] 9.4 Tests para comparison module

## Documentación

- [ ] 10.1 Actualizar README.md con sección de backtesting
- [ ] 10.2 Crear ejemplos de uso en docs/
- [ ] 10.3 Documentar formato de datos para cache