---
name: binance-trading-api
description: Especialista en la API de Binance para trading algorítmico, consulta de mercado y gestión de cuenta.
---

# Binance Trading API Skill

Este skill proporciona instrucciones detalladas para interactuar con la API de Binance Spot, incluyendo la gestión de autenticación, límites de velocidad y endpoints principales.

## Información de Conectividad Base

- **Producción**: `https://api.binance.com`
- **Alternativos**: `https://api1.binance.com`, `https://api2.binance.com`, `https://api3.binance.com`, `https://api4.binance.com`
- **Testnet**: `https://testnet.binance.vision/api`
- **Solo Datos de Mercado**: `https://data-api.binance.vision`

## Seguridad y Autenticación

Binance utiliza un sistema de **API Key** y **Secret Key**.

1.  **Headers**: Todas las peticiones autenticadas deben incluir el header `X-MBX-APIKEY`.
2.  **Firma (Signature)**: Los endpoints de tipo `TRADE` y `USER_DATA` requieren una firma HMAC-SHA256.
    -   **Payload**: Concatenación de query string y body.
    -   **Algoritmo**: HMAC-SHA256 usando el `secretKey`.
    -   **Timestamp**: Parámetro `timestamp` obligatorio en milisegundos.
    -   **recvWindow**: Parámetro opcional para definir la ventana de validez del request (default 5000ms).

## Límites de Velocidad (Rate Limits)

Binance utiliza un sistema basado en **Pesos (Weights)**.

-   **Límite de IP**: Generalmente 6,000 puntos de peso por minuto.
-   **Headers de Monitoreo**: Revisa `X-MBX-USED-WEIGHT-(intervalo)` en las respuestas.
-   **Exceso de Límites**: Un código HTTP 429 indica exceso de peso; un 418 indica ban de IP.

## Endpoints Principales (Spot v3)

### Mercado (Públicos)
- `GET /api/v3/ping`: Probar conectividad.
- `GET /api/v3/time`: Obtener la hora del servidor (crucial para sincronización).
- `GET /api/v3/exchangeInfo`: Reglas de trading y detalles de símbolos.
- `GET /api/v3/depth`: Libro de órdenes (Order Book).
- `GET /api/v3/ticker/price`: Precio actual de un símbolo (ej: `BTCUSDT`).
- `GET /api/v3/klines`: Datos de velas (candlesticks).

### Trading (Autenticados)
- `POST /api/v3/order`: Crear una nueva orden (Market, Limit, etc.).
- `POST /api/v3/order/test`: Probar una orden sin ejecutarla realmente.
- `DELETE /api/v3/order`: Cancelar una orden activa.
- `GET /api/v3/openOrders`: Listar todas las órdenes abiertas.

### Cuenta (Autenticados)
- `GET /api/v3/account`: Información de cuenta y balances.
- `GET /api/v3/myTrades`: Historial de trades propios.

## Guía de Implementación

Al implementar lógica de trading con Binance:
1.  **Sincronización**: Siempre sincroniza el tiempo local con el servidor de Binance (`/api/v3/time`) para evitar errores de timestamp.
2.  **Manejo de Símbolos**: Usa siempre mayúsculas (ej: `ETHBTC`).
3.  **Manejo de Errores**: Implementa lógica para manejar errores `-1021` (tiempo fuera de ventana) y `-2010` (saldo insuficiente).
4.  **Weights**: Los endpoints de mercado tienen pesos bajos (1-40), pero consultar información masiva de trades o exchangeInfo puede ser costoso.
