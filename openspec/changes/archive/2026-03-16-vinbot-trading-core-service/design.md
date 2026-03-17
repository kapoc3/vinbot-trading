## Context
Actualmente, el proyecto carece de una infraestructura para trading algorítmico. Se requiere un servicio que no solo exponga una API para control manual, sino que también ejecute procesos en segundo plano para monitorear el mercado y tomar decisiones de trading automáticas 24/7. El uso de FastAPI es fundamental para manejar la concurrencia necesaria entre la API REST y el procesamiento de streams de datos.

## Goals / Non-Goals

**Goals:**
- Proporcionar una arquitectura asíncrona que maneje múltiples pares de trading simultáneamente.
- Implementar un cliente de Binance desacoplado que gestione automáticamente la seguridad (firmas) y los límites de peso (weights).
- Crear un motor de ejecución en segundo plano que no bloquee el hilo principal de la API.
- Logs detallados de cada operación para auditoría y depuración.
- Soporte nativo para Binance Testnet para pruebas seguras.

**Non-Goals:**
- No se implementará una interfaz gráfica (Frontend) en esta etapa.
- No se incluirán estrategias de Machine Learning complejas en la primera versión.
- No se manejará persistencia en base de datos externa tipo SQL en esta fase inicial (se usará log en archivos o memoria).

## Decisions

### 1. Cliente HTTP Asíncrono: HTTPX
**Decisión**: Usar `httpx` en lugar de `requests` o `aiohttp`.
**Razón**: `httpx` es moderno, soporta HTTP/2 y tiene una API muy similar a `requests` pero totalmente asíncrona, lo que facilita la transición y el mantenimiento.

### 2. Gestión de Tareas de Fondo: Asyncio Background Tasks
**Decisión**: Ejecutar las estrategias de trading como tareas de `asyncio` iniciadas en el evento `lifespan` de FastAPI.
**Razón**: Permite que el bot empiece a trabajar en cuanto el API sube, sin necesidad de herramientas externas complejas como Celery para esta fase inicial.

### 3. Autenticación Personalizada vs Librerías
**Decisión**: Implementar la firma HMAC-SHA256 manualmente siguiendo el skill `binance-trading-api`.
**Razón**: Mayor control sobre la gestión de errores específicos de Binance (`-1021`) y reducción de dependencias externas pesadas que pueden volverse obsoletas.

### 4. Estructura de Proyecto: Service-Repository Pattern
**Decisión**: Seguir la estructura del skill `fastapi-templates`.
**Razón**: Facilita el testeo unitario y permite cambiar el proveedor de datos de mercado o ejecución sin afectar la lógica de negocio (estrategia).

## Risks / Trade-offs

- **[Riesgo: Sincronización de Tiempo]** → **Mitigación**: Implementar una función de sincronización que llame a `/api/v3/time` al inicio y aplique un offset a los timestamps locales.
- **[Riesgo: Límites de Velocidad]** → **Mitigación**: Implementar un decorador o middleware que rastree el header `X-MBX-USED-WEIGHT-(interval)` y aplique un pequeño delay si se acerca al 90% del límite.
- **[Riesgo: Desconexión de WebSockets]** → **Mitigación**: Implementar una lógica de reconexión exponencial (exponential backoff).
