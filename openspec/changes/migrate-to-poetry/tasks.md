## 1. Migración de Dependencias

- [x] 1.1 Crear el archivo `pyproject.toml` con FastAPI, Uvicorn, HTTpx, etc.
- [x] 1.2 Ejecutar `poetry lock` para generar el archivo de bloqueo de versiones.

## 2. Actualización de Infraestructura

- [x] 2.1 Modificar el `Dockerfile` para instalar dependencias vía Poetry.
- [ ] 2.2 Actualizar el `.dockerignore` si es necesario.

## 3. Limpieza

- [x] 3.1 Verificar el funcionamiento del bot en el contenedor.
- [x] 3.2 Eliminar definitivamente el archivo `requirements.txt`.
