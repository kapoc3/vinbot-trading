## Why

El sistema actual de VinBot opera exclusivamente en timeframe de 1 minuto (1m), lo cual genera muchas señales falsas en mercados con ruido. Las estrategias funcionan mejor cuando hay confirmación entre múltiples timeframes: una señal de compra en 1m confirmada por tendencia alcista en 15m o 1h tiene mayor probabilidad de éxito. Se necesita un sistema de análisis multi-timeframe que valide señales antes de ejecutar órdenes.

## What Changes

- **Gestor de Múltiples Timeframes**: Sistema para obtener y mantener datos de múltiples timeframes (1m, 5m, 15m, 1h) simultáneamente.
- **Confirmación de Señales**: Lógica que evalúa si la señal del timeframe principal (1m) está alineada con las tendencias de timeframes superiores.
- **Filtro de Confluencia**: Sistema que prioriza señales que tienen confirmación de múltiples timeframes.
- **Indicadores Agregados**: Cálculo de indicadores (RSI, EMA, ADX) en cada timeframe para análisis de tendencia.
- **API de Timeframe**: Endpoints para consultar el estado de cada timeframe y la confluencia actual.

## Capabilities

### New Capabilities

- **multi-timeframe-data**: Sistema de gestión de datos para múltiples timeframes paralelos.
- **signal-confirmation**: Lógica de confirmación de señales usando timeframes superiores.
- **confluence-filter**: Filtro que evalúa la fuerza de la señal basada en confirmación multi-timeframe.
- **indicator-aggregation**: Cálculo unificado de indicadores técnicos a través de todos los timeframes.

### Modified Capabilities

- **trading-strategy**: Actualizar estrategia para incluir validación multi-timeframe antes de generar señales.

## Impact

- **Código Afectado**:
  - `app/services/market_data.py`: Extensión para soportar múltiples timeframes
  - `app/services/indicators.py`: Cálculo de indicadores por timeframe
  - `app/services/strategy_factory.py`: Integración de filtro de confluencia
  - `app/main.py`: Obtención de datos de múltiples timeframes
- **Configuración**: Nuevos parámetros para definir qué timeframes usar y niveles de confirmación
- **Rendimiento**: Mayor uso de memoria y ancho de banda por mantener múltiples streams