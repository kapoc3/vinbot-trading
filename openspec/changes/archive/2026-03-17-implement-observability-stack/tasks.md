## 1. Instrumentación (Código)

- [x] 1.1 Añadir `prometheus-fastapi-instrumentator` y dependencias de `opentelemetry` al `pyproject.toml`.
- [x] 1.2 Configurar el instrumentador y el proveedor de trazas de OTLP en `app/main.py`.
- [x] 1.3 Crear métricas personalizadas en un nuevo archivo `app/core/metrics.py`.
- [x] 1.4 Integrar las métricas de negocio (RSI, PnL) y trazas en los servicios existentes.

## 2. Infraestructura (Docker)

- [x] 2.1 Añadir contenedor de `prometheus` al `docker-compose.yml`.
- [x] 2.2 Configurar archivo de recolección de métricas `prometheus.yml`.
- [x] 2.3 Añadir contenedor de `loki` para logs y configurar `promtail` para enviar los logs desde `/app/logs/*.log`.
- [x] 2.4 Añadir contenedor de `tempo` para trazas distribuidas vía OTLP (puerto 4317).
- [x] 2.5 Añadir contenedor de `grafana` al `docker-compose.yml` (con provisioning automático de datasources).

## 3. Visualización y Dashboarding (Opcional - Fase 2)

- [x] 3.1 Provisionar Data Sources de Grafana (Prometheus, Loki, Tempo).
- [x] 3.2 Crear un dashboard intermedio interactivo de Grafana con información correlacionada (Panel de métricas, Panel de Logs, Trazas de ejecuciones).
