# Backtest Comparison

## Purpose

Framework para comparar múltiples estrategias o configuraciones side-by-side.

## ADDED Requirements

### Requirement: Multi-Strategy Comparison

El sistema SHALL ejecutar múltiples estrategias con los mismos datos históricos y comparar resultados.

#### Scenario: Compare two strategies

- **WHEN** se comparan RSI y Bollinger Bands estrategias
- **THEN** retorna tabla comparativa con métricas de ambas

#### Scenario: Compare strategy parameters

- **WHEN** se comparan mismo estrategia con diferentes RSI periods (14 vs 21)
- **THEN** retorna comparación detallada

### Requirement: Comparison Output

El sistema SHALL generar resultado de comparación estructurado:

#### Scenario: Comparison table

- **WHEN** se completa comparación
- **THEN** retorna con campos:
  - strategy_name
  - total_pnl, pnl_pct
  - win_rate, profit_factor
  - sharpe_ratio, max_drawdown
  - total_trades
  - ranking_score (basado en múltiples métricas)

### Requirement: Best Strategy Selection

El sistema SHALL identificar la mejor estrategia basada en ranking score.

#### Scenario: Ranking calculation

- **WHEN** se comparan estrategias
- **THEN** ranking_score = weighted sum de:
  - 30% Sharpe Ratio
  - 30% Total PnL
  - 20% Win Rate
  - 20% Drawdown (invertido - mejor = menor)

#### Scenario: Best strategy

- **WHEN** se calcula ranking
- **THEN** best_strategy = estrategia con mayor ranking_score

### Requirement: Parameter Sweep

El sistema SHALL realizar sweep de parámetros para una estrategia.

#### Scenario: RSI period sweep

- **WHEN** se solicita RSI period sweep de 7 a 21
- **THEN** ejecuta backtest para cada periodo
- **AND** retorna mejor periodo según ranking

#### Scenario: Multiple parameters

- **WHEN** se sweep múltiples parámetros (RSI period, overbought, oversold)
- **THEN** ejecuta búsqueda de grid (puede ser lento)
- **AND** retorna mejor configuración