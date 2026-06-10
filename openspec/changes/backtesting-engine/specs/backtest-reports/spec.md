# Backtest Reports

## Purpose

Generación de reportes visuales (HTML) con gráficos de equity, drawdown y estadísticas.

## ADDED Requirements

### Requirement: HTML Report Generation

El sistema SHALL generar un reporte HTML autocontenido con visualizaciones.

#### Scenario: Generate report

- **WHEN** se llama generate_report(backtest_result)
- **THEN** retorna HTML string con:
  - Gráfico de equity curve
  - Gráfico de drawdown
  - Tabla de métricas
  - Lista de trades (scrollable)
  - Configuración usada

### Requirement: Equity Curve Chart

El sistema SHALL generar gráfico de evolución del capital en el tiempo.

#### Scenario: Equity chart data

- **WHEN** se genera el chart
- **AND** usa datos de: timestamp, equity_value para cada punto temporal
- **THEN** el gráfico muestra línea suave con área preenchida

#### Scenario: Equity chart styling

- **WHEN** se renderiza el chart
- **THEN** eje Y muestra valores de capital
- **AND** eje X muestra fechas
- **AND** tooltip muestra valor y fecha en hover

### Requirement: Drawdown Chart

El sistema SHALL generar gráfico de drawdown desde peak.

#### Scenario: Drawdown data

- **WHEN** se calcula drawdown chart
- **AND** usa datos de: timestamp, drawdown_pct (negativo)
- **THEN** el gráfico muestra área negativa desde 0

### Requirement: Trade Distribution Chart

El sistema SHALL generar histograma de PnL por trade.

#### Scenario: Trade distribution

- **WHEN** se genera histogram
- **AND** agrupa trades por rango de PnL (ej: -$100 a -$50, -$50 a $0, etc.)
- **THEN** muestra barras con trades winners en verde, losers en rojo

### Requirement: Statistics Summary

El sistema SHALL incluir tabla de resumen de métricas en el reporte.

#### Scenario: Metrics table

- **WHEN** se genera el reporte
- **AND** incluye:
  - Total PnL ($ y %)
  - Win Rate (%)
  - Profit Factor
  - Sharpe Ratio
  - Max Drawdown (%)
  - Total Trades
  - Avg Trade Duration

### Requirement: Report Styling

El sistema SHALL usar styling profesional para el reporte.

#### Scenario: Report theme

- **WHEN** se renderiza el HTML
- **THEN** usa theme oscuro con acentos en verde/rojo
- **AND** es responsive para mobile
- **AND** tiene CSS embebido (sin dependencias externas)

### Requirement: Save Report to File

El sistema SHALL guardar el reporte HTML a archivo.

#### Scenario: Save to file

- **WHEN** se llama save_report(result, "report.html")
- **THEN** escribe archivo HTML en el path especificado
- **AND** retorna path del archivo guardado