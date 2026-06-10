# Backtest Metrics

## Purpose

Biblioteca de cálculo de métricas de performance para resultados de backtesting.

## ADDED Requirements

### Requirement: Basic Metrics

El sistema SHALL calcular métricas básicas de trading:

#### Scenario: Calculate total PnL

- **WHEN** se tienen lista de trades
- **THEN** total_pnl = sum de todos los PnL de trades cerrados

#### Scenario: Calculate win rate

- **WHEN** se tienen lista de trades
- **THEN** win_rate = (trades winners / total trades) * 100

#### Scenario: Calculate profit factor

- **WHEN** se tienen lista de trades
- **THEN** profit_factor = gross_profit / gross_loss

### Requirement: Advanced Metrics

El sistema SHALL calcular métricas avanzadas:

#### Scenario: Sharpe Ratio

- **WHEN** se tienen retornos diarios
- **THEN** sharpe = (mean returns - risk_free_rate) / std_dev_returns
- **AND** se anualiza multiplicando por sqrt(252)

#### Scenario: Maximum Drawdown

- **WHEN** se tiene equity curve
- **THEN** max_drawdown = max(drawdown desde peak) como porcentaje

#### Scenario: Expectancy

- **WHEN** se tienen todos los trades
- **THEN** expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)

#### Scenario: Average Trade

- **WHEN** se tienen trades
- **THEN** avg_trade = total_pnl / numero_trades

#### Scenario: Consecutive Wins/Losses

- **WHEN** se tienen trades
- **THEN** max_consecutive_wins = max secuencia de wins
- **AND** max_consecutive_losses = max secuencia de losses

### Requirement: Trade Statistics

El sistema SHALL calcular estadísticas detalladas de trades:

#### Scenario: Trade count

- **WHEN** se procesan trades
- **THEN** total_trades = numero total de trades
- **AND** winning_trades = numero de trades con PnL > 0
- **AND** losing_trades = numero de trades con PnL < 0

#### Scenario: Trade duration

- **WHEN** se procesan trades
- **THEN** avg_trade_duration = promedio de tiempo en posición
- **AND** max_trade_duration = tiempo máximo en posición
- **AND** min_trade_duration = tiempo mínimo en posición

### Requirement: Time-based Metrics

El sistema SHALL calcular métricas basadas en tiempo:

#### Scenario: Annualized Return

- **WHEN** se tiene PnL y duración del backtest
- **AND** annualized_return = (total_pnl / initial_capital) * (365 / days)

#### Scenario: Daily Returns

- **WHEN** se tiene lista de trades
- **THEN** daily_returns = array de retornos diarios
- **AND**可以用来 calcular métricas de volatilidad

### Requirement: Metrics Output Format

El sistema SHALL retornar métricas en formato estructurado:

#### Scenario: Metrics dictionary

- **WHEN** se calculan todas las métricas
- **THEN** se retorna diccionario con:
  - total_pnl, total_pnl_pct
  - win_rate, profit_factor
  - sharpe_ratio, max_drawdown
  - expectancy, avg_trade
  - total_trades, winning_trades, losing_trades
  - max_consecutive_wins, max_consecutive_losses
  - avg_trade_duration_hours