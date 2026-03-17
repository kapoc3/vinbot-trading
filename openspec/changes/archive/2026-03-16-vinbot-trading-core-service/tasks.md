## 1. Project Initialization

- [x] 1.1 Establecer la estructura de carpetas (app/, core/, api/, services/) según el skill `fastapi-templates`.
- [x] 1.2 Crear archivo `requirements.txt` con `fastapi`, `uvicorn`, `httpx`, `pydantic-settings`, y `websockets`.
- [x] 1.3 Configurar variables de entorno en `.env.example` (API_KEY, SECRET_KEY, USE_TESTNET).

## 2. Binance Connectivity & Security

- [x] 2.1 Implementar utilidad de firma HMAC-SHA256 para peticiones autenticadas.
- [x] 2.2 Crear cliente base asíncrono que maneje la sincronización de tiempo con `/api/v3/time`.
- [x] 2.3 Implementar lógica de reintento y manejo de errores para el código -1021 (timestamp).

## 3. Market Data & WebSockets

- [x] 3.1 Implementar servicio para consulta de Klines históricos vía REST.
- [x] 3.2 Crear gestor de conexiones WebSocket para stream de Klines en tiempo real.
- [x] 3.3 Implementar lógica de reconexión automática para WebSockets.

## 4. Trading Execution Engine

- [x] 4.1 Implementar función para crear órdenes de tipo MARKET (Buy/Sell).
- [x] 4.2 Implementar función para cancelar órdenes activas.
- [x] 4.3 Crear repositorio de órdenes para persistencia en memoria/logs.

## 5. Account monitoring & Testnet

- [x] 5.1 Implementar endpoint para consultar balances individuales y totales.
- [x] 5.2 Configurar switch de Testnet para cambiar URLs base dinámicamente.

## 6. FastAPI Endpoints & Background Tasks

- [x] 6.1 Crear los routers de FastAPI para `/health`, `/account` y `/bot`.
- [x] 6.2 Integrar el loop de trading como una `Background Task` de FastAPI usando el evento `startup`.
- [x] 6.3 Implementar el endpoint `/health` que reporte el estado de conexión y offset de tiempo.
