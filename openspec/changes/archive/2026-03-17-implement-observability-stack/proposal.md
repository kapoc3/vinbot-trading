## Why

Un bot de trading necesita monitoreo en tiempo real para asegurar que está operando correctamente. Actualmente, solo tenemos logs y notificaciones de Telegram, lo cual es útil para eventos críticos pero no permite analizar tendencias de rendimiento (RSI, PnL acumulado), latencia de red de Binance o el estado de salud del sistema de forma visual e histórica.

## What Changes

- **Instrumentación del Código**: Se integrará OpenTelemetry (o librerías específicas) para exportar trazas (Tempo), logs estructurados (Loki) y métricas (Prometheus) de negocio y técnicas.
- **Nueva Infraestructura**: Se añadirán contenedores de **Prometheus** (métricas), **Loki** (logs), **Tempo** (trazas) y **Grafana** (visualización) al `docker-compose.yml`. Todo el stack LGTM (Loki, Grafana, Tempo, Metrics).
- **Dashboards**: Configuración automática de dashboards en Grafana para correlacionar logs, métricas y trazas fácilmente.

## Capabilities

### New Capabilities
- `system-observability`: Visualización correlacionada de métricas, logs centrales (Loki) y trazas de peticiones (Tempo).
- `alerts-visualizer`: Paneles dedicados a mostrar brechas de riesgo o eventos de SL/TP.

## Impact

- **Confiabilidad**: Identificación rápida de fallos si las métricas de red o de API fallan.
- **Análisis**: Capacidad de analizar el comportamiento del RSI y la efectividad de las órdenes a lo largo del tiempo.
- **Operatividad**: Un solo panel para ver el estado de todos los servicios.
