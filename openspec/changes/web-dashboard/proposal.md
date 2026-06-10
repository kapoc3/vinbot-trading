## Why

Actualmente, VinBot registra métricas en Prometheus, Loki y Grafana, pero el usuario desea una aplicación web unificada, accesible y específica que consolide las ganancias financieras (PnL diario) y el comportamiento detallado del bot en tiempo real (estrategias activas, historial de trades) de forma amigable sin depender exclusivamente del stack de observabilidad general.

## What Changes

- Creación de una API (Dashboard API) dentro de FastAPI para servir datos financieros y de estado consolidados.
- Desarrollo de un frontend (Web Dashboard UI) para visualizar métricas clave.
- Integración de los componentes de ganancias (PnL) y estado del bot (últimos trades, estrategia activa, régimen actual del mercado) en una sola interfaz gráfica.

## Capabilities

### New Capabilities
- `dashboard-api`: API dedicada a proveer datos consolidados de ganancias, estado del bot, y operaciones recientes para su consumo en el frontend.
- `web-dashboard-ui`: Aplicación frontend web (posiblemente React, Vue o HTML/JS vanilla) para visualizar las métricas y comportamiento de forma accesible.

### Modified Capabilities

## Impact

- `app/api/`: Se añadirán nuevos endpoints específicos para alimentar el dashboard.
- Frontend: Se creará un nuevo directorio para alojar los archivos de la aplicación web.
- Backend Services: Los módulos que gestionan estadísticas (`statistics.py`) y cartera (`portfolio/`) podrían requerir adaptaciones menores para exponer los datos agregados hacia la API de manera óptima.
