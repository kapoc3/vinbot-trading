## Goals

- Exponer un endpoint `/metrics` en el bot.
- Configurar Prometheus para que cada 15s obtenga (scrape) las métricas del bot.
- Configurar Grafana con Prometheus, Loki y Tempo como fuentes de datos (Data Sources).
- Pre-cargar un dashboard de Grafana con métricas de RSI y PnL, junto a paneles de logs.
- Configurar OpenTelemetry y Promtail (o Docker log driver) para enviar trazas y logs.

## Decisions

### 1. Stack: LGTM (Loki, Grafana, Tempo, Metrics/Prometheus)
**Decisión**: Usar el stack completo de observabilidad nativo de Grafana.
**Razón**: Integración nativa sin fricción, permite correlacionar una métrica con su traza y su log correspondiente en la misma vista.

### 2. Instrumentación: OpenTelemetry + Prometheus Instrumentator
**Decisión**: Usar `prometheus-fastapi-instrumentator` para métricas base y OpenTelemetry para las trazas. Configurar Docker para enviar logs a Loki.
**Razón**: Permite exponer automáticamente métricas de HTTP y añadir trazas distribuidas estándar (OTLP).

### 3. Persistencia de Métricas
**Decisión**: Las métricas de Prometheus se guardarán en un volumen Docker dedicado.
**Razón**: Evitar la pérdida de datos históricos al reiniciar contenedores.

## Proposed Metrics
- `trading_rsi`: Gauge del RSI actual por cada símbolo.
- `trading_orders_total`: Counter de órdenes ejecutadas por lado (BUY/SELL).
- `trading_pnl_daily`: Gauge del PnL acumulado el día de hoy.
- `binance_api_latency`: Histograma del tiempo de respuesta de las llamadas a Binance.
