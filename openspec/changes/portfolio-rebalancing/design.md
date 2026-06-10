## Context

El sistema actual usa posiciones fixed o equal weight. Para optimizar el capital, necesitamos un sistema que ajuste el tamaño de posición según el riesgo/volatility de cada símbolo.

## Goals / Non-Goals

**Goals:**
- Asignar capital basado en volatilidad (ATR)
- Rebalancear cuando desviación > threshold
- Limitar exposición máxima por símbolo
- Evitar overexposición a activos correlacionados

**Non-Goals:**
- No ejecutará trades automáticamente para rebalancear
- No predecirá correlaciones futuras

## Decisions

### D1: Allocation Method

**Decisión**: Usar inverse volatility weighting con límite máximo.

**Rationale**: Común en portfolios de trading, reduce exposición a símbolos volatiles.

### D2: Rebalancing Trigger

**Decisión**: Rebalancear cuando desviación > 20% del target.

**Rationale**: Suficiente para evitar trading excesivo, pero sensible a cambios.

### D3: Correlation Handling

**Decisión**: Excluir símbolos con correlación > 0.8 de posiciones largas simultáneas.

**Rationale**: Reduce riesgo de concentración.

## Migration Plan

1. Añadir config (allocation method, thresholds)
2. Crear portfolio allocator
3. Crear correlation matrix calculator
4. Integrar en strategy_factory para position sizing
5. Testing