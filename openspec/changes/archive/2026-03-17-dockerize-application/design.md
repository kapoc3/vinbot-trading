## Context

Necesitamos una imagen Docker ligera y segura para el bot de trading. Dado que usamos Python 3.12 y dependencias como `httpx`, `websockets` y `aiosqlite`, una imagen base tipo `python:3.12-slim` es la opción más eficiente.

## Goals / Non-Goals

**Goals:**
- Crear un `Dockerfile` multi-etapa (si es necesario) o simple y optimizado.
- Usar `.dockerignore` para excluir archivos innecesarios (`.git`, `__pycache__`, `.env`).
- Configurar un `docker-compose.yml` para simplificar la ejecución.
- Asegurar la persistencia de la base de datos SQLite mediante volúmenes.

**Non-Goals:**
- No se implementará Kubernetes en esta fase.
- No se migrará a una base de datos externa (como PostgreSQL) todavía, se mantendrá SQLite.

## Decisions

### 1. Imagen base: `python:3.12-slim`
**Decisión**: Utilizar la variante `slim` de la imagen oficial de Python.
**Razón**: Ofrece el equilibrio perfecto entre tamaño de imagen y compatibilidad con las librerías necesarias para compilar algunas dependencias si fuera el caso.

### 2. Manejo de Variables de Entorno
**Decisión**: El contenedor recibirá las variables mediante un archivo `.env` o el bloque `environment` de Compose.
**Razón**: Mantiene la seguridad y sigue las mejores prácticas de Twelve-Factor App.

### 3. Persistencia de Datos
**Decisión**: Mapear el archivo `vinbot.db` a un volumen de Docker.
**Razón**: SQLite guarda todo en un archivo. Si el contenedor se destruye, el volumen mantiene el archivo intacto para el próximo arranque.

## Risks / Trade-offs

- **[Riesgo: Timezones]** → **Mitigación**: Asegurar que el contenedor use UTC (por defecto en la mayoría de imágenes Linux) para que el reseteo de estadísticas diarias coincida con lo esperado.
- **[Riesgo: Rendimiento de Red]** → **Mitigación**: Usar el modo de red por defecto de Docker, que es suficiente para las peticiones de baja latencia de Binance.
