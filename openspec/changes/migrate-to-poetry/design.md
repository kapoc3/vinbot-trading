## Goals

- Migrar todas las librerías actuales a `pyproject.toml`.
- Configurar Poetry para que no cree entornos virtuales dentro del contenedor Docker (usar el Python global del container).
- Asegurar que el comando de arranque siga siendo funcional.

## Decisions

### 1. Herramienta: Poetry
**Decisión**: Usar Poetry como gestor de dependencias.
**Razón**: Es el estándar de la industria que más se asemeja a la experiencia de Maven/POM, separando dependencias de desarrollo de las de producción.

### 2. Configuración en Docker
**Decisión**: Instalar Poetry via pip y luego ejecutar `poetry install --no-root`.
**Razón**: Facilita la construcción de la imagen sin necesidad de scripts de instalación externos complejos.

## Tasks

### Phase 1: Inicialización
- Crear `pyproject.toml` con las dependencias actuales.
- Generar `poetry.lock`.

### Phase 2: Refactor Docker
- Actualizar `Dockerfile` para instalar Poetry.
- Cambiar la lógica de copia de archivos para priorizar los archivos de Poetry.

### Phase 3: Verificación
- Construir la imagen y verificar que el bot arranca y los tests (si existieran) pasan.
- Eliminar `requirements.txt`.
