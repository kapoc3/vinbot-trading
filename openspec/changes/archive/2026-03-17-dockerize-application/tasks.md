## 1. Preparación de Archivos Docker

- [x] 1.1 Crear el archivo `.dockerignore` para evitar subir basura a la imagen.
- [x] 1.2 Crear el `Dockerfile` basado en `python:3.12-slim`.
- [x] 1.3 Crear el archivo `docker-compose.yml` para gestionar la ejecución y volúmenes.

## 2. Ajustes de Configuración

- [x] 2.1 Asegurar que `app/core/config.py` maneje correctamente las variables de entorno sin fallar si el archivo `.env` no está presente físicamente dentro del contenedor (Docker suele inyectar las variables directamente).
- [x] 2.2 Configurar la ruta de la base de datos en `app/core/database.py` para que use una subcarpeta persistente (ej: `./data/vinbot.db`) que sea fácil de mapear a un volumen.

## 3. Construcción y Verificación

- [x] 3.1 Construir la imagen localmente: `docker compose build`.
- [x] 3.2 Ejecutar el contenedor y verificar logs: `docker compose up -d`.
- [x] 3.3 Verificar que el API y el bot de trading funcionen correctamente dentro del contenedor mediante los endpoints de salud.

## 4. Documentación

- [x] 4.1 Añadir instrucciones rápidas al `README.md` sobre cómo ejecutar el bot usando Docker.
