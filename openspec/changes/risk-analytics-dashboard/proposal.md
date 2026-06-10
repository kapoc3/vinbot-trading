## Why

Actualmente no hay forma de visualizar en tiempo real el riesgo del portfolio, exposición por símbolo, drawdown, o métricas de performance. Los traders necesitan un dashboard que muestre métricas de riesgo y analytics para tomar decisiones informadas.

## What Changes

- **Risk Metrics**: VaR, Expected Shortfall, Drawdown en tiempo real.
- **Exposure Dashboard**: Exposición por símbolo, sector, lado (long/short).
- **Performance Analytics**: Sharpe ratio, Sortino, Max Drawdown.
- **Position Analytics**: PnL por posición, unrealized vs realized.
- **Real-time Updates**: WebSocket o polling para datos en vivo.

## Capabilities

### New Capabilities

- **risk-metrics-calculator**: Calcula VaR, drawdown, exposure.
- **analytics-dashboard-api**: Endpoints para dashboard.
- **position-tracker**: Tracking de posiciones y PnL.

### Modified Capabilities

- **prometheus-metrics**: Añadir métricas de riesgo.
- **api-endpoints**: Nuevo endpoint /analytics.

## Impact

- **Código Afectado**:
  - `app/services/analytics/` - Nuevo módulo
  - `app/api/v1/endpoints/analytics.py` - Nuevo endpoint
  - `app/core/metrics.py` - Métricas de riesgo
- **Configuración**: Parámetros de cálculo de riesgo