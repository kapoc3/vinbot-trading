## Context

VinBot actualmente solo usa datos de timeframe 1m para todas las decisiones de trading. Esto causa:
1. Señales falsas en mercados laterales
2. Entradas prematuras en tendencias
3. No hay visibilidad de la tendencia general del mercado

Este diseño propone integrar análisis de múltiples timeframes para confirmar señales.

## Goals / Non-Goals

**Goals:**
- Obtener datos de múltiples timeframes (1m, 5m, 15m, 1h) en paralelo
- Calcular indicadores técnicos en cada timeframe
- Evaluar si la señal del timeframe principal tiene confirmación de timeframes superiores
- Filtrar señales que no tienen confluencia positiva
- Definir reglas claras de confirmación (ej: EMA 20 timeframe superior debe confirmar dirección)

**Non-Goals:**
- No se implementará trading en múltiples timeframes simultáneamente (solo confirmación)
- No se creará sistema de scalping multi-timeframe
- No se modificará el timeframe de operación principal (sigue siendo 1m)
- No se implementará análisis de timeframes inferiores (menos de 1m)

## Decisions

### D1: Arquitectura de Datos

**Decisión**: Usar un MultiTimeframeManager que mantiene una instancia de SymbolData por cada timeframe.

```python
class MultiTimeframeManager:
    timeframes = {
        "1m": SymbolData(symbol),
        "5m": SymbolData(symbol),
        "15m": SymbolData(symbol),
        "1h": SymbolData(symbol)
    }
```

**Rationale**: Reutilizar la clase SymbolData existente simplifica el desarrollo y mantiene consistencia.

### D2: Confirmación de Señales

**Decisión**: La confirmación se basa en la dirección de EMA 20 del timeframe superior.

**Alternativas consideradas**:
- Usar RSI de timeframes superiores: Menos efectivo para confirmar tendencia
- Usar ADX: Requiere más datos y más lento de calcular

**Rationale**: EMA es simple, rápido de calcular y ampliamente usado para determinar tendencia.

**Reglas de confirmación:**
- Signal 1m BUY confirmada si EMA 20 de 5m/15m está por encima del precio
- Signal 1m SELL confirmada si EMA 20 de 5m/15m está por debajo del precio
-fuertes requieren EMA 15m también alineada

### D3: Niveles de Confluencia

**Decisión**: Tres niveles de confluencia que determinan si ejecutamos la señal:

| Nivel | Descripción | Requisito |
|-------|-------------|-----------|
| ALTA | Confirmación fuerte | EMA 1h Y 15m confirman |
| MEDIA | Confirmación parcial | Solo 15m confirma |
| BAJA | Sin confirmación | Ningún timeframe confirma |

**Rationale**: Permitir operativa con confirmación parcial pero con menor tamaño de posición.

### D4: Parallel Data Fetch

**Decisión**: Obtener datos históricos de todos los timeframes en paralelo al inicio.

**Rationale**: Evita delays secuenciales y permite tener todos los datos listos antes de empezar a operar.

### D5: Configuración de Timeframes

**Decisión**: Timeframes configurables, pero default incluye: 1m (operación), 15m (confirmación), 1h (宏观).

**Rationale**: 1h captura la tendencia macro, 15m es el balance entre ruido y tendencia, 1m es el timeframe de operación.

## Risks / Trade-offs

### R1: Latencia y Ancho de Banda

**Riesgo**: Obtener datos de múltiples timeframes puede aumentar latencia y uso de API.

**Mitigación**:
- Cachear datos históricos
- Limitar requests a los timeframes configurados
- Usar WebSocket cuando sea posible

### R2: Complexity en el Código

**Riesgo**: Añadir lógica multi-timeframe aumenta complejidad y potencial de bugs.

**Mitigación**:
- Mantener la lógica encapsulada en MultiTimeframeManager
- Tests específicos para cada escenario de confirmación

### R3: Signal Reduction

**Riesgo**: El filtro puede rechazar demasiadas señales válidas.

**Mitigación**:
- Permitir configurar nivel mínimo de confluencia
- Logging de señales rechazadas por falta de confirmación

### R4: Memory Usage

**Riesgo**: Mantener datos de múltiples timeframes consume más memoria.

**Mitigación**:
- Limitar buffer de datos (ej: 500 candles por timeframe)
- Limpiar datos no usados

## Migration Plan

1. **Fase 1**: Crear MultiTimeframeManager y estructura de datos
2. **Fase 2**: Implementar obtención de datos históricos para múltiples timeframes
3. **Fase 3**: Añadir cálculo de EMA por timeframe
4. **Fase 4**: Implementar lógica de confirmación
5. **Fase 5**: Integrar en strategy factory como filtro
6. **Fase 6**: Tests y validación

## Open Questions

1. **Q1**: ¿Cuántos candles mantener por timeframe? → Proposal: 500 (suficiente para indicadores)
2. **Q2**: ¿Qué hacer si un timeframe no tiene datos suficientes? → Proposal: Usar solo los disponibles, warn si menos de 50
3. **Q3**: ¿Cómo manejartimeframes con gaps? → Proposal: Interpolación lineal o skip con warning