## Context

El sistema actual de VinBot tiene un flujo de trading donde las señales de salida (SELL) se generan exclusivamente cuando RSI supera el umbral de sobrebought (70). Este enfoque tiene las siguientes limitaciones:

1. **RSI Overbought prolongado**: En tendencias alcistas fuertes, el RSI puede mantenerse en sobrebought durante muchos días, causando que el bot no capture ganancias completas.
2. **Sin trailing take profit**: No hay mecanismo para ajustar el take profit dinámicamente según la fuerza de la tendencia.
3. **Sin límite de tiempo**: Las posiciones pueden mantenerse indefinidamente en mercados laterales.
4. **Partial TP estático**: Los niveles de partial take profit son fijos (ej: 1%, 2%, 3%) sin considerar la volatilidad del mercado.

Este diseño propone implementar un sistema de exit strategies avanzado que complementa el RSI con múltiples métodos de salida.

## Goals / Non-Goals

**Goals:**
- Implementar trailing take profit basado en ATR para capturar más ganancias en tendencias fuertes.
- Añadir time-based exits para evitar posiciones demasiado prolongadas.
- Implementar RSI divergence como señal de salida anticipada.
- Crear sistema de exit por fuerza de señal original.
- Hacer niveles de partial TP dinámicos según volatilidad.
- Mantener backward compatibility con la configuración existente.

**Non-Goals:**
- No se implementará machine learning para predicción de exits.
- No se modificará la lógica de entrada (solo exit).
- No se добавит nuovo exchange support.
- No se creará backtesting para estas estrategias (está fuera del scope de este change).

## Decisions

### D1: Trailing Take Profit basado en ATR

**Decisión**: Utilizar ATR (Average True Range) multiplicado por un factor configurable como trailing distance para el take profit.

**Alternativas consideradas**:
- % fijo del precio: Simple pero no considera volatilidad
- SAR parabólico: Computacionalmente más complejo
- trailing stop basado en precio máximo: No considera cambios de volatilidad

**Rationale**: ATR es el estándar de la industria para medir volatilidad y ajustar stops/takes dinámicamente. Permite al sistema ser adaptativo a diferentes condiciones de mercado.

**Configuración**:
- `TRAILING_TP_ENABLED`: bool (default: True)
- `TRAILING_TP_ATR_MULTIPLIER`: float (default: 2.0) - múltiplo del ATR para distancia
- `TRAILING_TP_ACTIVATION_PCT`: float (default: 1.5) - % de profit donde se activa el trailing

### D2: Time-Based Exit

**Decisión**: Implementar max_hours como configuración por símbolo, con默认值 de 4 horas (240 minutos de candles 1m).

**Alternativas consideradas**:
- Basado en número de candles: Dependiente del timeframe
- Basado en cambio de régimen: Ya existe régimen detection, pero no cubre timing

**Rationale**: Un max hold time es simple de configurar y entender. 4 horas es un buen balance para capturar momentum sin exponer demasiado capital.

**Configuración**:
- `MAX_HOLD_HOURS`: int (default: 4)
- `TIME_EXIT_ENABLED`: bool (default: True)

### D3: RSI Divergence Exit

**Decisión**: Extender la lógica existente de RSI Divergence (usada para entradas) para detectar divergencias bajistas como señal de salida.

**Alternativas consideradas**:
- Usar MACD cross down: Ya existe en estrategia MACD pero no integrado
- Price action patterns: Más complejo de implementar

**Rationale**: La lógica de divergence ya existe en divergence_strategy.py. Solo hay que adaptarla para detectar divergencias bajistas (precio hace higher high, RSI hace lower high).

**Implementación**:
- Reutilizar `DivergenceDetector` existente
- Añadir método `detect_bearish_divergence(symbol)` en indicators.py
- Integrar en risk_manager.check_exit_conditions()

### D4: Signal Strength Exit

**Decisión**: Categorizar las señales de entrada en fuerza (strong/moderate/weak) y ajustar el exit strategy según la fuerza.

**Alternativas consideradas**:
- Usar confidence score de estrategias: Las estrategias actuales no tienen scores
- Machine learning para confidence: Fuera de scope

**Rationale**: Si entramos muy cerca del umbral (ej: RSI en 31 vs oversold 30), la señal es más débil que RSI en 20.，我们可以 ajustar el exit para salir antes en señales débiles.

**Implementación**:
- Calcular "signal_strength" = distance from threshold normalized
- Si signal_strength < 0.3 (débil), añadir exit anticipado

### D5: Dynamic Partial TP

**Decisión**: Los niveles de partial TP se ajustan según ATR relativo (ATR/current_price). Mayor volatilidad = niveles más separados.

**Alternativas consideradas**:
- Múltiplos fijos de ATR: Similar pero con valores diferentes
- Volumen como factor: No correlaciona directamente con profit

**Rationale**: En mercados volátiles, los precios se mueven más, así que los targets de profit deben ser más amplios para ser realistas.

**Implementación**:
- `BASE_TP_LEVELS`: str = "1.0:30,2.0:30,3.0:40" (default actual)
- Nuevo cálculo: `adjusted_level = base_level * (1 + atr_pct * volatility_multiplier)`

## Risks / Trade-offs

### R1: Conflicto entre Exit Strategies

**Riesgo**: Múltiples exit conditions pueden contradictirse (ej: trailing TP dice BUY pero RSI divergence dice SELL).

**Mitigación**: Implementar priority order: Time-based (force exit) > Trailing TP > RSI Divergence > RSI Overbought.

### R2: Over-trading por Time-Based Exits

**Riesgo**: Salir por tiempo puede causar más trades y más comisiones.

**Mitigación**: Añadir cooldown entre exits por tiempo y nueva entrada (ej: 15 minutos).

### R3: Performance Impact

**Riesgo**: Cálculos adicionales de indicators en cada tick pueden afectar latency.

**Mitigación**: Cachear valores de divergencia y ATR, solo recalcular en kline close (no en cada tick).

### R4: Configuración Compleja

**Riesgo**: Demasiados parámetros de configuración pueden ser confusos.

**Mitigación**: Proveer valores por defecto sensatos y crear preset modes ("aggressive", "balanced", "conservative").

## Migration Plan

1. **Fase 1**: Añadir nuevos campos de configuración en `app/core/config.py` con valores por defecto que mantengan comportamiento actual.
2. **Fase 2**: Implementar trailing TP en `risk_manager.py` como extensión de `check_sl_tp()`.
3. **Fase 3**: Implementar time-based exit en `risk_manager.py`.
4. **Fase 4**: Añadir bearish divergence detection en `indicators.py`.
5. **Fase 5**: Integrar signal strength calculation en `strategy_factory.py`.
6. **Fase 6**: Implementar dynamic partial TP levels.
7. **Fase 7**: Testing en paper trading con testnet.
8. **Fase 8**: Deploy a producción con monitoreo intensivo.

## Open Questions

1. **Q1**: ¿Cuál debería ser el comportamiento default si ambos trailing TP y固定 TP se activan? → Proposal: Usar el que dé mejor precio (trailing).
2. **Q2**: ¿Debería el time-based exit considerarse como pérdida o como cierre normal? → Proposal: Contar como cierre normal (no llamar a SL logic).
3. **Q3**: ¿Cómo manejar el estado si el trailing TP activa pero luego el precio vuelve? → Proposal: No hay reversión una vez activado el trailing, solo sigue actualizando el stop.