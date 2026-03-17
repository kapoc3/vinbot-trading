## Why

Actualmente, el bot de trading "VinBot" mantiene su estado operativo (historial de órdenes, balances y, lo más crítico, si está en una posición abierta `in_position`) exclusivamente en memoria volátil. Si el proceso del bot se reinicia por una actualización, fallo del sistema o pérdida de conexión, el bot pierde la noción de si ha comprado un activo, lo que podría llevar a compras dobles o a quedar atrapado en una posición sin vender. La persistencia es fundamental para garantizar la resiliencia operativa y la coherencia del estado del bot a través de reinicios.

## What Changes

Se implementará una capa de persistencia ligera. Se guardará el estado de las estrategias (flags como `in_position`) y un registro de las órdenes ejecutadas en un almacenamiento local persistente (SQLite o archivos JSON). Al iniciar, el bot cargará este estado guardado para restaurar su contexto de trading antes de comenzar el procesamiento de datos.

## Capabilities

### New Capabilities
- `state-persistence-layer`: Capacidad de guardar y recuperar diccionarios de estado de componentes del sistema de forma atómica.
- `trade-repository`: Gestión de un almacenamiento persistente para el historial detallado de órdenes, permitiendo auditoría y recuperación de contexto.

### Modified Capabilities
- `rsi-trading-strategy`: Se modificará para leer su estado inicial (`in_position` por símbolo) desde la capa de persistencia al arrancar, en lugar de inicializarse siempre en `False`.
- `trading-execution-engine`: Se actualizará para asegurar que cada orden confirmada se registre inmediatamente en el almacenamiento persistente.

## Impact

- **Dependencias**: Se añadirá `aiosqlite` o similar si se opta por una base de datos SQL asíncrona ligera, o se usará gestión de archivos JSON si se prefiere simplicidad absoluta.
- **Flujo de Inicio**: El proceso de "Warm-up" ahora incluirá un paso inicial de "Recovery" para leer el último estado conocido.
- **Almacenamiento**: El proyecto requerirá una carpeta de datos (ej: `data/`) o un archivo de base de datos (`vinbot.db`) en el directorio raíz.
