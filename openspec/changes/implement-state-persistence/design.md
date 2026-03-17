## Context

El bot ha alcanzado un nivel de madurez operativa donde realiza análisis técnico y ejecución automática. El mayor riesgo actual es el "reinicio ciego": el bot no sabe qué hizo en el pasado. Necesitamos una forma de "memoria a largo plazo" que sea ligera y no introduzca latencias significativas en el flujo asíncrono.

## Goals / Non-Goals

**Goals:**
- Persistir el estado `in_position` de cada símbolo gestionado por la estrategia RSI.
- Guardar el historial de órdenes de Binance para que persista tras reinicios del servidor.
- Implementar un sistema de guardado asíncrono para no bloquear el loop de trading.
- Recuperación automática del estado al arrancar el proceso FastAPI.

**Non-Goals:**
- No se pretende construir un sistema de BI (Business Intelligence) complejo ni dashboards en este paso.
- No se migrará a una base de datos externa (como PostgreSQL/MySQL) para mantener el bot auto-contenido.
- No se persistirá el historial de Klines (velas), ya que el sistema de "Warm-up" de la API de Binance es suficiente y garantiza datos frescos.

## Decisions

### 1. Motor de Persistencia: SQLite (aiosqlite)
**Decisión**: Usar SQLite a través de la librería `aiosqlite`.
**Razón**: Ofrece la robustez de una base de datos real (transacciones, tipos de datos) sin la sobrecarga de un servidor externo. `aiosqlite` permite interactuar con ella de forma asíncrona, manteniendo la filosofía del proyecto.

### 2. Esquema de Tablas Mínimo
**Decisión**: Dos tablas principales:
1. `bot_state`: Almacenamiento clave-valor para estados como `in_position`.
2. `orders`: Registro detallado de órdenes ejecutadas (id, símbolo, lado, precio, rsi, timestamp).
**Razón**: Separa la lógica de control del bot (estado actual) de la lógica de auditoría (historial).

### 3. Sincronización Estrategia-DB
**Decisión**: La estrategia actualizará la DB en cada cambio de estado. El `TradingEngine` registrará la orden al recibir la confirmación de Binance.
**Razón**: Garantiza que el disco siempre refleje la realidad de la memoria lo más rápido posible.

## Risks / Trade-offs

- **[Riesgo: Corrupción de archivo de BD por apagado repentino]** → **Mitigación**: SQLite es altamente resistente a fallos; se realizarán operaciones atómicas.
- **[Riesgo: I/O de disco afectando latencia]** → **Mitigación**: El volumen de datos es muy pequeño (unas pocas filas por minuto), el impacto de I/O en SSD modernos es despreciable para este caso de uso.
