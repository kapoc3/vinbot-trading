## Why

Actualmente el proyecto usa `requirements.txt`, un método simple pero limitado para la gestión de dependencias. Migrar a Poetry (`pyproject.toml`) proporciona una estructura similar a Maven (`pom.xml`), permitiendo un control más estricto de las versiones, gestión de entornos y una definición más clara de los metadatos del bot.

## What Changes

- Reemplazo de `requirements.txt` por `pyproject.toml`.
- Introducción de `poetry.lock` para garantizar instalaciones deterministas.
- Actualización del `Dockerfile` para usar Poetry como gestor de paquetes.

## Capabilities

- `dependency-management`: Gestión avanzada de dependencias con resolución de conflictos.
- `project-metadata`: Definición centralizada de versión, autores y descripción del bot.

## Impact

- **Seguridad**: Mayor control sobre las sub-dependencias.
- **Docker**: Las builds serán más predecibles y fáciles de cachear.
- **Desarrollo**: Los desarrolladores podrán replicar exactamente el mismo entorno con un solo comando.
