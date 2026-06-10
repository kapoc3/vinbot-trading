## Why

Actualmente, VinBot no tiene forma de validar estrategias de trading antes de ejecutarlas en producción. Cualquier cambio en estrategias o parámetros se despliega directamente con dinero real, lo cual representa un alto riesgo. Se necesita un sistema de backtesting que permita simular estrategias con datos históricos de Binance para validar su rentabilidad y comportamiento antes de exponer capital real.

## What Changes

- **Motor de Backtesting**: Framework completo para ejecutar estrategias contra datos históricos con simulación de ordenes.
- **Datos Históricos**: Sistema de descarga y almacenamiento de candles históricos de Binance (1m, 5m, 15m, 1h, 4h, 1d).
- **Simulación de Ejecución**: Simulación realista de fills, slippage, y comisiones.
- **Métricas de Performance**: Cálculo de PnL, Sharpe, Drawdown, Win Rate, Profit Factor, expectancy.
- **Comparación de Estrategias**: Framework para comparar múltiples estrategias side-by-side.
- **Reporte Visual**: Generación de reportes HTML con gráficos de equity, drawdown, trades.
- **API de Backtest**: Endpoint REST para запускать backtests desde la aplicación.

## Capabilities

### New Capabilities

- **historical-data-fetch**: Sistema de descarga y cache de datos históricos de Binance por símbolo y timeframe.
- **backtest-engine**: Motor de ejecución de estrategias contra datos históricos con simulación de ordenes.
- **backtest-metrics**: Biblioteca de cálculo de métricas de performance (Sharpe, Drawdown, Win Rate, etc.).
- **backtest-comparison**: Framework para comparar múltiples estrategias o configuraciones.
- **backtest-reports**: Generación de reportes visuales (HTML) con gráficos de equity y estadísticas.

### Modified Capabilities

- Ninguna - el sistema de backtesting es completamente nuevo y no modifica la lógica de trading en producción.

## Impact

- **Nuevo Código**:
  - `app/services/backtest/` - Módulo completo de backtesting
  - `app/api/v1/endpoints/backtest.py` - API REST para ejecutar backtests
  - CLI command para ejecutar backtests desde terminal
- **Dependencias**: `pandas` para manejo de datos, `matplotlib` para gráficos (solo en modo backtest)
- **Configuración**: Parámetros de backtest en config (default symbols, timeframes, date ranges)
- **Base de Datos**: Tabla para almacenar resultados de backtests (opcional, para history)