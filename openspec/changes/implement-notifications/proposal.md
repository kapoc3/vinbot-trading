## Why

Actualmente, el bot opera de forma "silenciosa". Aunque guarda logs y persiste datos en la base de datos, el usuario no recibe actualizaciones inmediatas sobre eventos críticos como ejecuciones de órdenes, disparos de Stop Loss o errores del sistema. Implementar un sistema de notificaciones (específicamente vía Telegram) permitirá un monitoreo remoto y proactivo sin necesidad de revisar constantemente los logs del servidor.

## What Changes

Se añadirá un servicio de notificaciones asíncrono que se integrará con los componentes existentes (`TradingEngine`, `RiskManager`, `RSIStrategy`) para enviar mensajes en tiempo real.

## Capabilities

### New Capabilities
- `notification-service`: Un servicio centralizado para enviar mensajes formateados a través de la API de Telegram.
- `alert-system`: Lógica para categorizar y filtrar alertas (INFO, WARNING, ERROR).

### Modified Capabilities
- `trading-execution-engine`: Notificará cada vez que una orden sea enviada o completada.
- `risk-manager`: Enviará alertas inmediatas cuando se activen SL, TP o el Circuit Breaker diario.
- `main-bot-loop`: Notificará cambios de estado del bot (arranque, parada por error).

## Impact

- **Configuración**: Se añadirán variables al `.env` (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`).
- **Experiencia de Usuario**: El usuario recibirá reportes de ejecución con precios y PyL directamente en su móvil.
- **Mantenibilidad**: Mejor capacidad de respuesta ante fallos críticos de conexión o API.
