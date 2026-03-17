## 1. Configuración Inicial

- [x] 1.1 Añadir `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID` al `.env.example` y `app/core/config.py`.
- [x] 1.2 Crear el servicio `app/services/notifications.py` con el método base `send_message(text)`.

## 2. Implementación de Alertas

- [x] 2.1 Integrar notificaciones en `TradingEngine.place_market_order` para confirmar transacciones.
- [x] 2.2 Integrar notificaciones en `RiskManager` para alertar sobre Stop Loss, Take Profit y límites diarios.
- [x] 2.3 Añadir notificación de arranque y parada en el `lifespan` de `main.py`.

## 3. Pulido y Formato

- [x] 3.1 Mejorar el formateo de los mensajes usando Markdown y emojis.
- [x] 3.2 Implementar manejo de errores para que un fallo en Telegram no bloquee el bot.

## 4. Verificación

- [x] 4.1 Test de notificación manual mediante un endpoint temporal.
- [x] 4.2 Probar el arranque del bot y verificar recepción del mensaje "ONLINE".
