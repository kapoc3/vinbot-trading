---
name: vinbot-env-setup
description: Guía de configuración, reconstrucción de archivos .env (.env, .env.classic, .env.scalper, .env.grid), proxies estáticos (Smart Split-Routing) y despliegue en Docker para VinBot Trading. Activar cuando el usuario pida configurar variables de entorno, migrar a otra máquina, cambiar proxies de Binance o levantar el servicio en Docker.
---

# VinBot Environment & Deployment Setup Skill

Esta skill instruye a un agente Antigravity sobre cómo crear, auditar o reconfigurar los archivos de entorno y el despliegue Docker de `vinbot-trading` en cualquier máquina nueva.

## 1. Arquitectura de Archivos `.env` Requeridos por Docker Compose

El archivo `docker-compose.yml` levanta **3 instancias especializadas del bot** más la pila de observabilidad (Prometheus, Grafana, Loki, Postgres y Nginx). Como los archivos `.env*` están excluidos de Git por seguridad (`.gitignore`), en una máquina nueva se deben generar **4 archivos** a partir de `.env.example`:

| Archivo | Servicio Docker | Propósito y Ajustes Clave |
| :--- | :--- | :--- |
| `.env` | Base / Local | Configuración base montada en `bot-classic` y usada para tests locales (`ML_ENABLED=False` en tests unitarios locales, `True` en contenedores). |
| `.env.classic` | `bot-classic` (`vinbot-classic`) | Estrategia `TRADING_STRATEGY=Auto` (combina RSI Divergence, Bollinger, MACD según ADX/ATR), `RSI_OVERSOLD=35.0`, `RSI_OVERBOUGHT=65.0`, `ML_ENABLED=True`, `ML_AUTO_TRAIN_ENABLED=True`. |
| `.env.scalper` | `bot-scalper` (`vinbot-scalper`) | Operativa rápida de corto plazo: `TRADING_STRATEGY=Auto` o `RsiWithDivergence`, `STOP_LOSS_PCT=1.5`, `TAKE_PROFIT_PCT=3.0`, `MAX_HOLD_HOURS=2`, `ML_ENABLED=True`. |
| `.env.grid` | `bot-grid` (`vinbot-grid`) | Operativa de malla en mercados laterales: `ENABLE_GRID_BOT=True`, `GRID_SYMBOL=SOLUSDT` (o par elegido), `ML_ENABLED=True`. |

### Comando rápido de inicialización en una máquina nueva:
```bash
cp .env.example .env
cp .env.example .env.classic
cp .env.example .env.scalper
cp .env.example .env.grid
```

---

## 2. Configuración de Enrutamiento Inteligente (Smart Split-Routing con IPs Estáticas)

Cuando el bot corre en una máquina con **IP pública dinámica residencial**, la API Key de Binance configurada con *"Restrict access to trusted IPs only"* rechazará órdenes si cambia la IP del ISP (`Error -2015`).

Para evitarlo sin consumir ancho de banda excesivo del proxy:

1. **Variables en `.env*`**:
   ```env
   BINANCE_PROXY_URLS="http://USUARIO:PASSWORD@IP_EUROPA_1:PUERTO,http://USUARIO:PASSWORD@IP_EUROPA_2:PUERTO,http://USUARIO:PASSWORD@IP_EUROPA_3:PUERTO"
   BINANCE_PROXY_SIGNED_ONLY=True
   WS_PING_INTERVAL=20
   WS_PING_TIMEOUT=10
   WS_READ_TIMEOUT=45
   ```
2. **Reglas críticas para el Agente al configurar `BINANCE_PROXY_URLS`**:
   - **Prohibido usar IPs de Estados Unidos (`US`)**: `api.binance.com` devuelve `HTTP 451`. Usar únicamente IPs de Europa (España, Polonia, Alemania, Países Bajos, Reino Unido), Japón o Latinoamérica.
   - **Verificación de latencia antes de guardar**: Siempre probar cada proxy contra `https://api.binance.com/api/v3/time` y ordenarlos en `BINANCE_PROXY_URLS` de menor a mayor latencia para evitar retrasos de failover en la primera petición.
   - **Whitelist en Binance**: Indicar al usuario las IPs sin puerto separadas por espacio (ej. `64.137.96.74 84.247.60.125 45.38.107.97`) para pegarlas en el panel *API Management* de Binance.

---

## 3. Configuración del Modelo ML Local Auto-Entrenado

Para activar el entrenamiento automático sin fugas de datos (*Purged Walk-Forward TimeSeriesSplit*):
```env
ML_ENABLED=True
ML_AUTO_TRAIN_ENABLED=True
ML_RETRAIN_INTERVAL_HOURS=12
ML_MODEL_PATH=data/ml_models
ML_CONFIDENCE_THRESHOLD=0.5
ML_TRAIN_THRESHOLD_PCT=2.0
ML_TRAIN_HORIZON=10
```
- Al arrancar (`run_trading_bot` en `app/main.py`), el bot descarga 500 velas históricas por símbolo, calcula features estacionarias (`app/services/ml/feature_engineering.py`), entrena el modelo RandomForest en un hilo secundario (`asyncio.to_thread`) y guarda el archivo `.pkl` en `./data/ml_models/{SYMBOL}_model.pkl`.
- Nota: Si se van a correr los tests unitarios con `pytest` en el host local, `.env` debe mantener `ML_ENABLED=False` porque `tests/test_ml.py::TestMLConfig::test_ml_config_defaults` verifica ese valor por defecto. En `.env.classic`, `.env.scalper` y `.env.grid` se puede dejar `ML_ENABLED=True`.

---

## 4. Pasos de Verificación y Despliegue para el Agente

1. Verificar que los 4 archivos (`.env`, `.env.classic`, `.env.scalper`, `.env.grid`) existen y tienen `BINANCE_API_KEY`, `BINANCE_SECRET_KEY`, `BINANCE_ENV=prod` y `BINANCE_PROXY_URLS` válidos.
2. Probar conectividad de los proxies hacia `https://api.binance.com/api/v3/time`.
3. Ejecutar la suite de pruebas (`poetry run pytest tests/ -v`).
4. Levantar o reconstruir los servicios Docker:
   ```bash
   docker compose up -d --build
   ```
5. Verificar salud de contenedores y métricas:
   - Dashboard Web: `http://localhost:8000/dashboard`
   - Grafana: `http://localhost:3001`
   - Prometheus: `http://localhost:9090`

