## Why

El sistema actual de VinBot solo utiliza RSI como señal de salida (overbought), lo cual es insuficiente en mercados con tendencias fuertes donde el RSI puede permanecer en sobrecompra por períodos prolongados. Esto causa que el bot no capture ganancias completas en tendencias alcistas y cierre posiciones prematuramente. Se necesitan estrategias de salida más sofisticadas para maximizar la rentabilidad y proteger el capital.

## What Changes

- **Trailing Take Profit Dinámico**: Implementar trailing take profit basado en ATR que ajuste el nivel de toma de ganancias automáticamente según la volatilidad del mercado, permitiendo capturar más ganancias en tendencias fuertes.
- **Time-Based Exits**: Añadir exits basados en tiempo (max hold time) para evitar posiciones que se quedan demasiado tiempo en mercados laterales.
- **RSI Divergence Exit**: Utilizar divergencias RSI también como señal de salida (actualmente solo se usa para entrada), detectando cuando el precio hace nuevos highs pero el RSI no confirma.
- **Exit por Fuerza de Señal**: Implementar exit basado en la fuerza/confianza de la señal original (por ejemplo, salir antes si RSI estava muy cerca del umbral de sobrecompra).
- **Partial TP con Niveles Dinámicos**: Los niveles de partial take profit actuales son estáticos; hacerlos dinámicos basados en volatilidad.

## Capabilities

### New Capabilities

- **trailing-take-profit**: Sistema de trailing take profit basado en ATR que ajusta automáticamente los niveles de salida según la volatilidad del mercado.
- **time-based-exit**: Lógica de exit basada en tiempo máximo de posición para evitar hold prolongado.
- **rsi-divergence-exit**: Detección de divergencias bajistas RSI como señal de salida anticipada.
- **signal-strength-exit**: Sistema de exits basado en la fuerza de la señal de entrada.
- **dynamic-partial-tp**: Partial take profit con niveles dinámicos basados en ATR/volilidad.

### Modified Capabilities

- **trading-strategy**: Actualizar estrategia de salida para incluir múltiples métodos de exit.
- **risk-management**: Extender risk_manager para soportar nuevos tipos de exit y trailing TP.

## Impact

- **Código Afectado**:
  - `app/services/risk_manager.py`: Extensión para nuevos tipos de exit
  - `app/services/strategy_factory.py`: Integración de nuevos exit strategies
  - `app/services/indicators.py`: Añadir cálculo de divergencias
  - `app/main.py`: Integración de trailing TP checks
- **Configuración**: Nuevos parámetros en `app/core/config.py` para configurar time-based exits, trailing TP multiplier, etc.
- **Dependencias**: Sin nuevas dependencias externas requeridas.