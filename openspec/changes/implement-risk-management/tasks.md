## 1. Configuración y Estructura

- [x] 1.1 Añadir variables de riesgo al `.env` y cargarlas en `app/core/config.py` (SL, TP, Max Daily Loss).
- [x] 1.2 Crear el servicio `app/services/risk_manager.py` para centralizar la lógica de control.
- [x] 1.3 Extender la base de datos para persistir el `entry_price` por cada símbolo.

## 2. Implementación de Monitoreo de Riesgo

- [x] 2.1 Implementar lógica para calcular el PyL (Profit and Loss) actual de una posición basándose en el precio de entrada guardado.
- [x] 2.2 Implementar chequeo de Stop Loss y Take Profit en tiempo real dentro del flujo de `dummy_strategy_callback`.
- [x] 2.3 Implementar tracker de pérdida acumulada diaria y lógica de reseteo a las 00:00 UTC.

## 3. Integración y Seguridad (Circuit Breaker)

- [x] 3.1 Modificar la estrategia RSI para que no ejecute señales de compra si el `risk_manager` indica que el límite de pérdida diaria ha sido alcanzado.
- [x] 3.2 Modificar el `TradingEngine` para registrar el precio de entrada exacto en la persistencia tras una compra exitosa.
- [x] 3.3 Implementar una función de "Liquidación por Riesgo" que cierre la posición y actualice el flag `in_position` a False.

## 4. Pruebas y Monitoreo

- [x] 4.1 Test local: Simular un precio de mercado bajo el Stop Loss y verificar la salida automática.
- [x] 4.2 Añadir endpoint `/api/v1/bot/risk-status` para ver el PyL actual y el porcentaje consumido del límite diario.
- [x] 4.3 Logs: Asegurar que cada intervención de riesgo (SL/TP/Daily) tenga un log de nivel WARNING/INFO muy claro.
