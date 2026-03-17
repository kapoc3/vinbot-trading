## 1. Infraestructura de Base de Datos

- [x] 1.1 Añadir `aiosqlite` a `requirements.txt` e instalarlo.
- [x] 1.2 Crear `app/core/database.py` para gestionar la conexión asíncrona y la inicialización de tablas.
- [x] 1.3 Definir el esquema de tablas `bot_state` y `orders` en el script de inicialización.

## 2. Implementación de Repositorios de Persistencia

- [x] 2.1 Crear `app/services/persistence.py` con métodos para `set_state(key, value)` y `get_state(key)`.
- [x] 2.2 Implementar el método `save_order(order_data)` para volcar las respuestas de Binance a la tabla `orders`.

## 3. Integración en Estrategia y Motor

- [x] 3.1 Modificar `RSIStrategy.__init__` para que pueda cargar valores iniciales de `positions` desde la BD.
- [x] 3.2 Actualizar `RSIStrategy.update_position` para que llame a la capa de persistencia automáticamente.
- [x] 3.3 Modificar `TradingEngine.place_market_order` para que registre el éxito de la operación en la BD de órdenes.

## 4. Lifecycle y Verificación

- [x] 4.1 Asegurar que la conexión a la BD se abra y cierre correctamente en el `lifespan` de FastAPI en `main.py`.
- [x] 4.2 Verificar mediante un reinicio de prueba que el bot recupera el flag `in_position` correctamente.
- [x] 4.3 Añadir un endpoint simple `/api/v1/bot/history` para consultar las órdenes guardadas en la BD local.
