## Why

Actualmente, el bot se ejecuta directamente en el host del usuario, lo que puede llevar a problemas de "en mi máquina funciona" debido a diferencias en versiones de Python, dependencias de sistema o variables de entorno. Dockerizar la aplicación garantiza un entorno consistente, facilita el despliegue en servidores (VPS) y permite aislar el bot de trading del resto del sistema.

## What Changes

Se añadirán archivos de configuración de Docker para empaquetar la aplicación FastAPI junto con sus dependencias y el bot de trading asíncrono.

## Capabilities

### New Capabilities
- `containerized-deployment`: Capacidad de ejecutar todo el bot dentro de un contenedor Docker.
- `orchestrated-stack`: Uso de Docker Compose para manejar volúmenes persistentes y redes de forma sencilla.

### Modified Capabilities
- `persistence-layer`: Se ajustará para manejar la base de datos SQLite dentro de un volumen de Docker para que los datos no se pierdan al reiniciar el contenedor.
- `configuration`: El bot deberá poder leer configuraciones desde variables de entorno pasadas al contenedor.

## Impact

- **Portabilidad**: El bot podrá ejecutarse en cualquier sistema con Docker instalado (Linux, Mac, Windows, Cloud).
- **Aislamiento**: Las dependencias del bot no interferirán con otras aplicaciones de Python en el sistema.
- **Persistencia**: Se usarán volúmenes para asegurar que la base de datos de órdenes y estados (`vinbot.db`) sobreviva a la recreación de contenedores.
