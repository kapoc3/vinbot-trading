# VinBot Trading

VinBot es un bot de trading algorítmico y cuantitativo construido con **FastAPI** y **Python 3.12**. Se conecta a la API de Binance (REST + WebSockets), detecta regímenes de mercado en tiempo real, ejecuta un pipeline local de Machine Learning estacionario con validación *Walk-Forward* y expone métricas en una pila de observabilidad LGTM (Loki, Grafana, Tempo, Prometheus).

## Arquitectura y Características Principales
- **FastAPI Core**: Backend asíncrono de baja latencia con Dashboard integrado (`/dashboard`).
- **Smart Split-Routing & Failover de Proxies Estáticos**: Enruta las peticiones firmadas (`signed=True`) a través de una lista priorizada de proxies HTTP con IP fija (ej. Webshare Europa: Madrid -> Varsovia -> Londres) con rotación automática en caso de caída, mientras los WebSockets públicos van directo por el ISP local con reconexión automática ante cambios de IP dinámica.
- **Pipeline ML Local Auto-Entrenado**:
  - Features estacionarias invariantes de escala (distancias porcentuales a EMAs, MACD normalizado sobre serie real, ratio de volatilidad `ATR_7 / ATR_21` y pendiente OBV).
  - Entrenamiento `RandomForestClassifier` con `TimeSeriesSplit` purgado (*embargo gap*) y auto-reentrenamiento periódico en segundo plano (`ML_AUTO_TRAIN_ENABLED=True`).
  - Dimensionamiento de posición dinámico escalado por el multiplicador de convicción del Ensemble ML + Confluencia Multi-Timeframe.
- **Detección Autónoma de Régimen**: Clasifica el mercado en `Trending`, `Ranging` o `HighVolatility` usando ADX y ATR, bloqueando cambios de estrategia mientras haya una posición abierta (*Strategy Consistency Lock*).
- **Observabilidad Completa**: Prometheus + Grafana + Loki configurados en `docker-compose.yml`.

---

## Configuración de Archivos `.env` (Guía para Humanos y Agentes Antigravity)

> **Para Agentes Antigravity**: Este repositorio incluye la skill local [`.agents/skills/vinbot-env-setup/SKILL.md`](./.agents/skills/vinbot-env-setup/SKILL.md) (y en `.gemini/skills/vinbot-env-setup/SKILL.md`) con las instrucciones paso a paso para reconstruir y validar automáticamente el entorno en cualquier máquina nueva.

`docker-compose.yml` utiliza **4 archivos de entorno** en la raíz del proyecto (ignorados en Git por seguridad). Para inicializarlos en una máquina nueva a partir de la plantilla documentada [`.env.example`](./.env.example):

```bash
cp .env.example .env
cp .env.example .env.classic
cp .env.example .env.scalper
cp .env.example .env.grid
```

### Perfiles de los 4 Archivos `.env`

| Archivo | Contenedor Docker | Configuración Recomendada |
| :--- | :--- | :--- |
| **`.env`** | Base / Local | Credenciales base. Si ejecutas `pytest` localmente, mantén `ML_ENABLED=False` en este archivo (los tests verifican el default). |
| **`.env.classic`** | `vinbot-classic` | `TRADING_STRATEGY=Auto`, `ML_ENABLED=True`, `ML_AUTO_TRAIN_ENABLED=True`, `STOP_LOSS_PCT=2.0`, `TAKE_PROFIT_PCT=5.0`. |
| **`.env.scalper`** | `vinbot-scalper` | `TRADING_STRATEGY=Auto`, `ML_ENABLED=True`, `ML_AUTO_TRAIN_ENABLED=True`, `STOP_LOSS_PCT=1.5`, `TAKE_PROFIT_PCT=3.0`, `MAX_HOLD_HOURS=2`. |
| **`.env.grid`** | `vinbot-grid` | `ENABLE_GRID_BOT=True`, `GRID_SYMBOL=SOLUSDT`, `ML_ENABLED=True`, `ML_AUTO_TRAIN_ENABLED=True`. |

### Variables Críticas a Configurar en los 4 Archivos

1. **Credenciales de Binance**:
   ```env
   BINANCE_API_KEY=tu_api_key_real
   BINANCE_SECRET_KEY=tu_secret_key_real
   BINANCE_ENV=prod
   TRADING_SYMBOLS=BTCUSDT,ETHUSDT
   ```
2. **Proxies de IP Fija (Smart Split-Routing para IP Residencial Dinámica)**:
   * Nunca uses proxies de EE. UU. (bloqueados con HTTP 451 en Binance Global). Usa proxies europeos verificados:
   ```env
   BINANCE_PROXY_URLS="http://usuario:password@64.137.96.74:6641,http://usuario:password@84.247.60.125:6095,http://usuario:password@45.38.107.97:6014"
   BINANCE_PROXY_SIGNED_ONLY=True
   ```
   * En el panel **API Management** de Binance (*Restrict access to trusted IPs only*), autoriza las IPs de salida sin puerto separadas por espacio:
     `64.137.96.74 84.247.60.125 45.38.107.97`

---

## Ejecución del Bot con Docker

```bash
docker compose up -d --build
```

### Servicios y Puertos Locales
- **Dashboard Web VinBot**: [http://localhost:8000/dashboard](http://localhost:8000/dashboard)
- **Grafana**: [http://localhost:3001](http://localhost:3001) — Dashboards de PnL, Régimen de Mercado, Confianza ML y RSI.
- **Prometheus**: [http://localhost:9090](http://localhost:9090)

## Changelog

Consulta [CHANGELOG.md](./CHANGELOG.md) para el historial completo de cambios.
