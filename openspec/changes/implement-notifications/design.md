## Context

Necesitamos una forma ligera y asíncrona de comunicación. Telegram es la opción ideal debido a su API sencilla de usar mediante HTTP POST y su soporte para formato Markdown.

## Goals / Non-Goals

**Goals:**
- Enviar notificaciones de órdenes (Símbolo, Lado, Cantidad, Precio).
- Enviar alertas de gestión de riesgo (SL/TP, Daily Loss).
- Reportar errores críticos del sistema.
- Implementar un sistema de "cola" asíncrona simple para no bloquear la ejecución del trading mientras se envía el mensaje.

**Non-Goals:**
- No se implementarán comandos interactivos de Telegram (mensajes del usuario al bot) en esta fase inicial.
- No se enviarán gráficos o archivos multimedia, solo texto/emojis.

## Decisions

### 1. Uso de `httpx` para peticiones asíncronas
**Decisión**: Utilizaremos el cliente `httpx` ya presente en el proyecto para realizar las peticiones a la API de Telegram.
**Razón**: Evita añadir dependencias pesadas y se integra perfectamente con el loop de `asyncio` existente.

### 2. Singleton Notification Service
**Decisión**: El servicio será una instancia única global que otros módulos importarán.
**Razón**: Centraliza la configuración y el manejo de excepciones de red de forma eficiente.

### 3. Formato MarkdownV2
**Decisión**: Usaremos MarkdownV2 para enviar mensajes con negritas, códigos y emojis atractivos.
**Razón**: Mejora la legibilidad de los reportes de ejecución.

## Risks / Trade-offs

- **[Riesgo: Rate Limiting de Telegram]** → **Mitigación**: Implementar un bloque `try/except` que capture errores de red y loguee fallos, evitando que el bot se detenga si Telegram no responde.
- **[Riesgo: Exposición de Token]** → **Mitigación**: El token DEBE residir exclusivamente en el `.env`, nunca en el código fuente.
