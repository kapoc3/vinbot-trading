## 1. Módulo de Indicadores Técnicos

- [x] 1.1 Crear archivo `app/services/indicators.py` para alojar lógica matemática pura.
- [x] 1.2 Implementar función matemática nativa en Python para el cálculo del RSI dado un listado de precios de cierre y un `period` (default 14).
- [x] 1.3 Implementar estructura de memoria tipo `collections.deque` para guardar el historial ordenado de las últimas N velas de un símbolo.

## 2. Precarga y Sincronización de Datos (Warm-up)

- [x] 2.1 En el loop de inicio del bot (`run_trading_bot` en `main.py`), añadir lógica para consultar REST `get_historical_klines` por los últimos 100 periodos.
- [x] 2.2 Parsear los datos históricos obtenidos e inyectarlos secuencialmente en la estructura de memoria de indicadores antes de escuchar el WebSocket.
- [x] 2.3 Conectar el callback del WebSocket (`stream_klines`) de forma que cada vez que una vela se cierre, su precio final se agregue a la memoria.

## 3. Lógica de la Estrategia RSI

- [x] 3.1 Crear el archivo principal de la estrategia `app/services/rsi_strategy.py`.
- [x] 3.2 Implementar la clase o función principal de la estrategia que reciba el valor actual de RSI y tome la decisión de Compra/Venta.
- [x] 3.3 Implementar el tracker o flag interno `in_position` (booleano) dentro de la estrategia para evitar repetir compras o vender operaciones vacías.

## 4. Integración con el Motor de Ejecución

- [x] 4.1 Modificar `dummy_strategy_callback` en `main.py` para que en vez de solo loguear, llame a la lógica de la estrategia RSI inyectando el último dato.
- [x] 4.2 Enlazar las señales de Compra/Venta confirmadas de la estrategia con llamadas directas a `trading_engine.place_market_order()`.
- [x] 4.3 Loggear cada trade ejecutado especificando el símbolo, el precio disparador y el RSI exacto en ese momento.
