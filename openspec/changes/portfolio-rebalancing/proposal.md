## Why

El bot actualmente distribuye el capital uniformemente entre símbolos o usa posiciones fijas. No considera el riesgo individual de cada símbolo, la volatilidad, ni rebalancea dinámicamente según cambios en el portfolio. Se necesita un sistema de rebalanceo automático que optimice la distribución de capital.

## What Changes

- **Capital Allocation por Volatilidad**: Asignar más capital a símbolos menos volátiles.
- **Risk-Weighted Allocation**: Ponderar posiciones según VaR (Value at Risk) de cada símbolo.
- **Rebalancing Triggers**: Rebalancear cuando una posición se desvíe X% del target.
- **Max Position Size**: Limitar exposición máxima por símbolo.
- **Correlation Filter**: Evitar overexposición a símbolos correlacionados.

## Capabilities

### New Capabilities

- **volatility-allocator**: Calcula asignación basada en ATR/volatilidad.
- **risk-allocator**: Asignación basada en riesgo (VaR, Drawdown).
- **rebalance-manager**: Gestiona rebalanceos automáticos.
- **correlation-matrix**: Calcula correlaciones entre símbolos.

### Modified Capabilities

- **strategy-factory**: Usar allocator para tamaño de posición.

## Impact

- **Código Afectado**:
  - `app/services/portfolio/` - Nuevo módulo
  - `app/services/strategy_factory.py` - Integrar allocation
  - `app/core/config.py` - Nuevos parámetros
- **Configuración**: Parámetros de asignación y rebalanceo