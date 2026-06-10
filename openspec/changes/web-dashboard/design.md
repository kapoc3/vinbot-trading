## Context

Actualmente VinBot cuenta con observabilidad basada en un stack LGTM (Loki, Grafana, Tempo, Prometheus). Aunque efectivo para análisis técnico y alertas, carece de una vista unificada, amigable y enfocada exclusivamente en los resultados financieros (PnL) y el comportamiento inmediato del bot (estado, estrategia activa). Se necesita un dashboard web específico y ligero para este propósito.

## Goals / Non-Goals

**Goals:**
- Exponer un nuevo endpoint en FastAPI (`/api/v1/dashboard`) que consolide: PnL diario/acumulado, estado actual del bot, régimen de mercado activo y resumen de las últimas operaciones.
- Construir un frontend web (SPA) ligero que consuma esta API y muestre los datos de forma visual y moderna.
- Servir la interfaz web de manera eficiente, idealmente aprovechando la misma infraestructura existente.

**Non-Goals:**
- Reemplazar los dashboards de Grafana (Grafana se mantendrá para observabilidad profunda de métricas del sistema).
- Implementar la capacidad de crear órdenes manuales o modificar la configuración del bot desde esta interfaz (solo lectura por ahora).

## Decisions

- **Arquitectura Backend (API)**: Se añadirá un nuevo router `dashboard.py` dentro de la aplicación FastAPI actual (`app/api/v1/`). Esto es óptimo porque el bot ya tiene cargado el estado en memoria y evita la complejidad de crear un microservicio separado.
- **Arquitectura Frontend (Web UI)**: Se creará una SPA (Single Page Application) utilizando React/Vite o Vanilla JS. Para simplificar el despliegue, la aplicación FastAPI servirá los archivos compilados del frontend desde un directorio `static/` integrado, o se levantará un contenedor Nginx en `docker-compose.yml`.
- **Integración de Datos**: La API del dashboard actuará como orquestador consultando múltiples servicios internos: `services/statistics.py` (para PnL), `services/regime_service.py` (para estado del mercado), y consultas SQLite a `vinbot.db` (para el historial de transacciones).

## Risks / Trade-offs

- **[Seguridad] Exponer datos financieros sensibles en un endpoint no protegido.** -> *Mitigación*: Implementar autenticación básica (Basic Auth) o proteger la ruta del frontend/API si se despliega públicamente; por defecto, limitarlo a la red local.
- **[Rendimiento] Consultas concurrentes de la UI podrían afectar el motor de trading.** -> *Mitigación*: Implementar caché temporal (e.g., 5-10 segundos) en el endpoint del dashboard para evitar múltiples lecturas a disco/BD.
