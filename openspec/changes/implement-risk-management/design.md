## Context

El sistema actual es reactivo al RSI. Necesitamos que sea proactivo en la protección del capital. La gestión de riesgo operará en dos niveles: Nivel de Trade (SL/TP) y Nivel de Cuenta (Pérdida Diaria).

## Goals / Non-Goals

**Goals:**
- Implementar Stop Loss (SL) porcentual dinámico.
- Implementar Take Profit (TP) porcentual dinámico.
- Limitar la pérdida diaria máxima (Daily Drawdown).
- Evitar nuevas entradas si el límite diario ha sido alcanzado.
- Persistir el "precio base" de compra para calcular el PyL tras reinicios.

**Non-Goals:**
- No se implementarán Trailing Stop Loss complejos en esta fase.
- No se gestionará el riesgo de múltiples posiciones simultáneas para el mismo símbolo (se mantiene 1 posición Max).
- No se pretende hacer Hedging.

## Decisions

### 1. Monitoreo de SL/TP en el Loop de WebSocket
**Decisión**: El chequeo de SL/TP se realizará en cada actualización de precio del WebSocket (`MarketUpdate`), no solo en el cierre de vela.
**Razón**: El riesgo debe ser mitigado en tiempo real. Esperar al cierre de vela (1m) podría resultar en pérdidas mucho mayores a las configuradas.

### 2. Persistencia del Precio de Entrada
**Decisión**: Se extenderá la tabla `bot_state` o se usará la tabla `orders` para recuperar el precio medio de entrada al reiniciar el bot.
**Razón**: Es vital conocer el precio de compra original para calcular el PyL actual.

### 3. Circuit Breaker Diario
**Decisión**: Se implementará un flag en DB `daily_loss_reached`. Este flag se reseteará al inicio de cada día (UTC). 
**Razón**: Evita que el bot siga operando en un día de mala racha o condiciones de mercado anómalas.

## Risks / Trade-offs

- **[Riesgo: Slippage en Stop Loss de Mercado]** → **Mitigación**: Usaremos órdenes MARKET para asegurar la salida inmediata, aceptando que el precio final puede variar ligeramente del umbral exacto.
- **[Riesgo: Falsas salidas por volatilidad momentánea (Whipsaws)]** → **Mitigación**: Configuración de umbrales razonables (ej: 2-3% mínimo).
