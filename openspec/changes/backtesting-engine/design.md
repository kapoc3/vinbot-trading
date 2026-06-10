## Context

VinBot actualmente opera en tiempo real sin forma de validar estrategias. Antes de desplegar cualquier cambio de estrategia o parámetros, necesitamos un sistema de backtesting que permita:

1. Descargar datos históricos de Binance
2. Ejecutar estrategias contra esos datos
3. Simular fills de ordenes con comportamiento realista
4. Calcular métricas de performance
5. Comparar estrategias y generar reportes

## Goals / Non-Goals

**Goals:**
- Sistema de backtesting completo que pueda ejecutarse desde CLI y API
- Descarga automática de datos históricos de Binance
- Simulación realista de ejecución (slippage, comisiones, fills)
- Métricas completas: PnL, Sharpe, Drawdown, Win Rate, Profit Factor
- Reportes HTML con visualizaciones

**Non-Goals:**
- No se implementará live trading desde el backtester (solo simulación)
- No se guardarán resultados en DB para este change (futuro)
- No se implementará walk-forward optimization (futuro)
- No se integrará con el trading engine de producción

## Decisions

### D1: Arquitectura del Backtest Engine

**Decisión**: El backtest engine será un módulo independiente que recibe datos históricos y ejecuta estrategias, pero no modificará el código de producción.

**Alternativas consideradas**:
- Modificar el trading engine para soportar modo simulación: Riesgoso, puede afectar producción
- Ejecutar estrategias directamente con datos históricos: Puede no reflejar el comportamiento real

**Rationale**: Mantener separación clara entre backtesting y trading real evita bugs que afecten producción.

```
┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
│ Binance API │───▶│ Historical Data  │───▶│ Backtest     │
│ (download)  │    │ (cache CSV/DB)   │    │ Engine       │
└──────────────┘    └──────────────────┘    └──────┬───────┘
                                                  │
                                                  ▼
                                         ┌──────────────┐
                                         │ Strategy     │
                                         │ (RSI, BB,    │
                                         │ MACD, etc.)  │
                                         └──────┬───────┘
                                                │
                                                ▼
                                         ┌──────────────┐
                                         │ Trade       │
                                         │ Simulator   │
                                         │ (fills,     │
                                         │ slippage)   │
                                         └──────┬───────┘
                                                │
                                                ▼
                                         ┌──────────────┐
                                         │ Metrics      │
                                         │ Calculator   │
                                         └──────────────┘
```

### D2: Formato de Datos

**Decisión**: Usar pandas DataFrames para manejar datos históricos y resultados.

**Rationale**: pandas es el estándar de la industria para análisis de datos financieros, ofrece operaciones vectorizadas eficientes, y se integra bien con matplotlib para visualización.

### D3: Simulación de Slippage

**Decisión**: Aplicar slippage variable basado en liquidez del símbolo (configurable).

**Alternativas consideradas**:
- Slippage fijo: Muy simplista
- Slippage basado en volumen real: No disponible en datos históricos

**Rationale**: Un slippage del 0.1% para major pairs y 0.2% para altcoins es un compromiso razonable.

### D4: Comisiones

**Decisión**: Usar estructura de comisiones de Binance (0.1% maker/taker) como default, pero configurables.

**Rationale**: Binance tiene las comisiones más bajas, usar esto como baseline da resultados conservadores.

### D5: Parallel Execution

**Decisión**: Soporte para ejecutar múltiples estrategias/configuraciones en paralelo usando multiprocessing.

**Rationale**: Backtesting puede ser intensivo en CPU, paralelizar acelera significativamente.

## Risks / Trade-offs

### R1: Diferencia entre Backtest y Real

**Riesgo**: El backtest puede dar resultados diferentes al trading real debido a:
- Fill at different prices
- Slippage not accurately modeled
- Market impact on larger orders
- Liquidity issues not captured in historical data

**Mitigación**:
- Documentar limitaciones claramente
- Usar slippage conservador
- Añadir warning en reportes
- Sugerir paper trading después de backtest positivo

### R2: Look-ahead Bias

**Riesgo**: Usar indicadores que calculan sobre datos futuros inadvertidamente.

**Mitigación**: El engine procesará datos secuencialmente, sin acceso a datos futuros en cada punto temporal.

### R3: Performance con Muchos Datos

**Riesgo**: Descargar y procesar años de datos puede ser lento.

**Mitigación**: Implementar caching de datos descargados, permitir rango de fechas configurable.

### R4: Dependencias Adicionales

**Riesgo**: Añadir pandas/matplotlib aumenta el footprint del proyecto.

**Mitigación**: Marcar como dependencias opcionales, solo requeridas para backtesting.

## Migration Plan

1. **Fase 1**: Crear módulo de descarga de datos históricos (historical_data_fetch)
2. **Fase 2**: Implementar backtest engine básico con soporte para estrategias existentes
3. **Fase 3**: Añadir simulador de trades (fills, slippage, comisiones)
4. **Fase 4**: Implementar cálculo de métricas
5. **Fase 5**: Añadir generación de reportes HTML
6. **Fase 6**: Crear CLI y API endpoint
7. **Fase 7**: Testing y validación

## Open Questions

1. **Q1**: ¿Cuántos datos históricos descargar por defecto? → Proposal: 1 año para major pairs, 6 meses para altcoins
2. **Q2**: ¿Guardar resultados en DB o solo en memoria? → Proposal: Solo en memoria para MVP, DB optional en futuro
3. **Q3**: ¿Cómo manejar gaps en datos (exchanges down)? → Proposal: Interpolar o skip con warning
4. **Q4**: ¿Soporte para multi-strategies en un backtest? → Proposal: No por ahora, una estrategia por backtest