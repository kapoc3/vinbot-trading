## Why

A medida que el bot opera de forma autónoma, el riesgo de pérdidas catastróficas aumenta debido a la volatilidad del mercado o fallos en la lógica de la estrategia. Actualmente, el bot no tiene límites de pérdida (Stop Loss), objetivos de ganancia (Take Profit), ni un control sobre el máximo de pérdida diaria permitido. Implementar una gestión de riesgo robusta es crítico para preservar el capital y asegurar la viabilidad a largo plazo del sistema de trading.

## What Changes

Se introducirá un módulo de gestión de riesgo que actuará como un filtro final antes de que cualquier orden sea enviada al `TradingEngine`. Además, se implementará un sistema de monitoreo activo de posiciones abiertas para ejecutar salidas automáticas basadas en el precio.

## Capabilities

### New Capabilities
- `risk-monitor`: Seguimiento del PyL (Profit and Loss) en tiempo real de las posiciones abiertas y del balance diario.
- `daily-drawdown-protector`: Interruptor de seguridad que detiene todas las operaciones si la pérdida del día supera un umbral porcentual predefinido.
- `trade-guard`: Lógica para validar cada señal de trading contra las reglas de riesgo (ej: tamaño máximo de posición, exposición total).

### Modified Capabilities
- `rsi-trading-strategy`: Se integrará con el `risk-monitor` para recibir señales de clausura de posición no solo por RSI, sino por Stop Loss o Take Profit.
- `trading-execution-engine`: Se añadirá un paso de validación obligatorio con el `trade-guard` antes de la ejecución.

## Impact

- **Configuración**: Se añadirán nuevas variables al `.env` (STOP_LOSS_PCT, TAKE_PROFIT_PCT, MAX_DAILY_LOSS_PCT).
- **Flujo de Ejecución**: Cada actualización de precio iniciará un chequeo de riesgo para las posiciones abiertas.
- **Seguridad**: Mayor robustez ante movimientos bruscos del mercado (Flash crashes).
