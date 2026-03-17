## Why
El objetivo es construir un servicio de trading algorítmico robusto, escalable y asíncrono que permita operar en Binance de forma automatizada. Se requiere una arquitectura que minimice la latencia, maneje correctamente los límites de velocidad de la API y proporcione una base sólida para implementar estrategias de trading complejas. Usar FastAPI permite aprovechar la asincronía nativa de Python para manejar múltiples streams de datos y ejecución de órdenes en paralelo.

## What Changes
Se implementará un nuevo microservicio llamado "VinBot Trading Core" basado en FastAPI. Este servicio actuará como el orquestador central para la conectividad con Binance, la gestión de datos de mercado y la ejecución de órdenes.

## Capabilities

### New Capabilities
- `binance-connectivity`: Gestión centralizada de la conexión con Binance Spot API (Producción y Testnet), incluyendo autenticación HMAC-SHA256 y sincronización de tiempo.
- `market-data-streamer`: Servicio asíncrono para consumir datos de mercado en tiempo real vía WebSockets y REST (Klines, Ticker, Order Book).
- `trading-execution-engine`: Motor para la creación, cancelación y monitoreo de órdenes con soporte para diferentes tipos (Market, Limit).
- `account-monitor`: Seguimiento en tiempo real de balances de cuenta y estado de margen.
- `api-management-interface`: Endpoints de FastAPI para controlar el bot, consultar estados y configurar parámetros de trading.

### Modified Capabilities
<!-- No modified capabilities for this new project -->

## Impact
- **Dependencias**: FastAPI, HTTPX, Pydantic, y autenticación HMAC-SHA256 personalizada.
- **Infraestructura**: Loop de eventos asíncrono para ejecución 24/7.
- **Seguridad**: Manejo seguro de API Keys y Secrets (vía variables de entorno).
