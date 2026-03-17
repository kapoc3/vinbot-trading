## Context

El sistema base cuenta con todo el Core de conectividad para recibir señales y colocar órdenes (trading engine, binance client, etc). Sin embargo, el actuador actual es un método `dummy_strategy_callback` que no ejecuta lógica, sólo loggea. Agregar la primera estrategia formal (RSI) completará un bot autómata end-to-end, probando arquitectónicamente que la capa de red con Binance interactúa de manera segura con el motor lógico interno.

## Goals / Non-Goals

**Goals:**
- Implementar el cálculo efectivo del indicador RSI clásico (usualmente en periodos ej. 14).
- Determinar si el mercado está sobrecomprado (>70) para vender y sobrevendido (<30) para comprar.
- Dotar al módulo de la capacidad de precargar historial REST y combinarlo con el real-time WS (WebSockets) antes de tomar ninguna decisión computacional.
- Controlar el lado de negocio en base a estados simples (ej. `in_position`) para prevenir falsos positivos repetidos y spamming al `/v3/order`.

**Non-Goals:**
- No se incorporará en este change soporte multi-estrategia dinámico complejo. La lógica del RSI se unirá directamente (por el momento de manera estática).
- No se sumarán bibliotecas súper robustas/pesadas como `pandas` o `polars` que rompan compatibilidad en hardware pequeño, para el RSI se intentará utilizar lógica liviana.
- No se agregará lógica compleja de Risk/Money Management, el tamaño de la orden (quantity) puede determinarse estáticamente o como un porcentaje base de hardcode simple para simplificar la funcionalidad.

## Decisions

### 1. Cálculo del RSI: Custom Nativo vs Librerías
**Decisión**: Optamos por un método ligero en Python nativo para el RSI, acompañado de estructuras listas de tamaño fijo tipo `collections.deque(maxlen=100)`.
**Razón**: El bot actual opera con pocos pares a la vez, se busca que su huella de RAM y dependencias (paquetes a mantener) quede en un nivel puramente core (`fastapi`, `httpx`).

### 2. Sincronización de Klines (Velas)
**Decisión**: Antes de procesar el stream real-time WS, la estrategia hará un poll (a través del `MarketDataService.get_historical_klines`) de las N últimas velas (usualmente 50 o 100 periodos). Esto llenará (Warm-up) el historial para poder tener un cálculo de EMA / Promedios real para ser comparado.
**Razón**: El cálculo del RSI se volverá totalmente impreciso y falso si la plataforma sube e instintivamente ejecuta una decisión de mercado en el minuto ceró. Se necesitan datos históricos precedentes de las X velas anteriores.

### 3. Modelo de Estados ('in_position')
**Decisión**: La estrategia mantendrá una lógica simple de control para alternar entre Buy y Sell, sin sobrecometer repetidas ocasiones.
**Razón**: Un límite es imperativo para evitar saturar de orders el rate-limiting the Binance. Se generará una compra que seteará un estado `in_position=True` esperando entonces a una eventual venta.

## Risks / Trade-offs

- **[Riesgo: Caída del Servidor y Pérdida de Estado 'in_position']** → **Mitigación**: Aceptamos que un reinicio local pueda descoordinar visualmente si el bot estaba in-position temporalmente, aunque un simple chequeo de `AccountManager` de existencia base del par podría paliarlo en otra versión, inicializaremos todo a `False` pero limitando la compra.
- **[Riesgo: Cálculo Lento en Python Nativo]** → **Mitigación**: Para streams asíncronos y pocos pares no es un issue perceptible para la latencia entre ticks, que sucede 1 vez por minuto en klines de 1 min, ni siquiera sub-milisegundos son requeridos.
