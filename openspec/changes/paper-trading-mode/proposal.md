## Why

Actualmente el bot opera directamente con dinero real en Binance. Antes de ejecutar estrategias nuevas o cambios de configuración, no hay forma de validar el comportamiento en condiciones reales sin arriesgar capital. Se necesita un modo de Paper Trading que simule operaciones completas sin ejecutar órdenes reales.

## What Changes

- **Modo Paper Trading**: Sistema que simula todo el flujo de trading (señales, ejecuciones, PnL) sin enviar órdenes a Binance.
- **Balance Virtual**: Sistema de capital virtual con tracking de posiciones y PnL.
- **Simulación de Ejecución**: Simulación de fills, slippage, y comisiones.
- **Logging de Decisiones**: Registro detallado de cada decisión tomada para debugging.
- **Modo Híbrido**: Capacidad de operar algunos símbolos en paper y otros en real.
- **Comparación**: Comparación de performance real vs paper para validación.

## Capabilities

### New Capabilities

- **paper-trading-engine**: Motor de simulación de trading sin ejecución real.
- **virtual-balance**: Sistema de balance virtual con posiciones.
- **paper-mode-api**: API para controlar modo paper.

### Modified Capabilities

- **trading-engine**: Actualizar para soportar modo simulación.

## Impact

- **Código Afectado**:
  - `app/services/trading_engine.py` - Añadir modo simulación
  - `app/main.py` - Configuración de modo
  - `app/api/v1/endpoints/` - Endpoints de control
- **Configuración**: Nuevos parámetros para paper trading