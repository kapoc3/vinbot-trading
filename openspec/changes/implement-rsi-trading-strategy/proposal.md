## Why

El bot de trading "VinBot" ha sido equipado con un núcleo asíncrono robusto que le permite conectarse y recibir datos de mercado en tiempo real desde Binance, así como enviar órdenes. Sin embargo, en la actualidad no posee inteligencia ni lógica para tomar decisiones automatizadas. Implementar el Índice de Fuerza Relativa (RSI), uno de los indicadores técnicos de momentum más confiables, aportará al bot la capacidad fundamental de generar señales de compra (cuando el mercado está sobrevendido) y venta (cuando está sobrecomprado), permitiéndole operar de forma autónoma.

## What Changes

Se añadirá un módulo de análisis técnico dedicado al mantenimiento del historial de precios y cálculo de indicadores matemáticos. Sobre este módulo se construirá la estrategia RSI funcional, que evaluará cada nueva vela (kline) entrante. Cuando el RSI caiga por debajo de un umbral definido (ej. 30), el bot enviará una orden de compra; cuando el RSI supere otro umbral determinado (ej. 70), el bot enviará una orden de venta.

## Capabilities

### New Capabilities
- `technical-indicators`: Componente responsable de almacenar el histórico de precios y calcular matemáticamente indicadores técnicos como el RSI.
- `rsi-trading-strategy`: Lógica de decisión específica que recibe el RSI, evalúa los umbrales de sobrecompra/sobreventa, gestiona el estado de la posición (para no comprar múltipes veces o vender en vacío) y genera señales de trading.

### Modified Capabilities
- `trading-execution-engine`: Se actualizará para reaccionar a las señales emitidas por la estrategia en vez de depender de llamadas manuales, enlazando directamente la señal con la colocación de la orden en Binance.

## Impact

- **Dependencias**: Posible introducción de librerías para cálculo numérico ligero u operaciones sobre arrays (aunque el RSI se puede implementar con matemáticas estándar de Python si se quiere evitar dependencias pesadas como `pandas`).
- **Arquitectura de Memoria**: El bot tendrá que mantener en memoria persistente un historial de precios de cierre para poder calcular el RSI en vivo (los últimos "n" periodos).
- **Control de Riesgo**: Debe integrarse lógica básica para saber si la posición actual de trading ya está abierta para el par de monedas, con el fin de evitar "spam" de órdenes hacia Binance al cruzar los umbrales.
