## 1. Backend: Dashboard API

- [x] 1.1 Crear el nuevo archivo de router en `app/api/dashboard.py` (o similar dentro del API de v1) y registrar sus rutas en `main.py`.
- [x] 1.2 Extraer y formatear el PnL actual y el estado general utilizando `services/statistics.py` y `services/regime_service.py`.
- [x] 1.3 Implementar la consulta optimizada a SQLite (`vinbot.db`) para obtener el historial de las últimas 10 transacciones.
- [x] 1.4 Añadir un decorador o lógica de caché en el endpoint para almacenar la respuesta por 5 segundos y evitar saturación.

## 2. Frontend: Web Dashboard UI

- [x] 2.1 Crear la carpeta para los recursos estáticos `app/static/dashboard/`.
- [x] 2.2 Escribir `index.html` definiendo el esqueleto de la UI (tarjetas para PnL, tarjeta de estado de mercado, tabla de transacciones).
- [x] 2.3 Escribir `styles.css` aplicando un diseño moderno, legible e idealmente adaptado a las convenciones de observabilidad (modo oscuro).
- [x] 2.4 Implementar la lógica JS en `app.js` para realizar el fetch a `/api/v1/dashboard` y poblar el DOM con la respuesta JSON.
- [x] 2.5 Añadir la función de *polling* en `app.js` para consultar periódicamente (cada 10 segundos) la API y refrescar la vista.

## 3. Integración y Pruebas

- [x] 3.1 Añadir la directiva en FastAPI (`StaticFiles`) para servir el frontend desde la ruta `/dashboard`.
- [ ] 3.2 Probar manualmente la UI para comprobar el *auto-refresh* y validar el correcto funcionamiento del caché de 5 segundos de la API.
