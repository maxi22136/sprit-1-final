# SIGMA · Gestión de mantención de activos (Manufacturas Andina S.A.)

Sprint 1 · RQY1101 Ingeniería de Requisitos · DuocUC

Historias de usuario incluidas:
- **HU-1** Registro de fallas, reparaciones y mantenciones (el técnico registra, otro turno continúa, se cierra con fecha de término).
- **HU-3** Actualización del estado de la máquina (solo el supervisor; los intentos no autorizados quedan registrados).

## Cómo ejecutarlo
```
python -m venv .venv
source .venv/bin/activate        # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Abrir http://127.0.0.1:5000. La base de datos `sigma.db` se crea sola la primera vez.

Usuarios de prueba (clave: `sigma123`): Técnico · Turno A, Técnico · Turno B y Supervisor de mantenimiento.

## Pruebas
```
python -m unittest discover -s tests -v
```

## Estructura
- `app.py`: API (Flask) y reglas de negocio.
- `db.py` y `schema.sql`: base de datos SQLite y datos iniciales.
- `static/index.html`: interfaz móvil (ingreso, panel con disponibilidad, plano de planta, equipos, historial en línea de tiempo).
- `tests/test_api.py`: pruebas funcionales.
- `docs/`: diseño de la base de datos y registro de pruebas.

## Primer commit
```
git init
git add .
git commit -m "Sprint 1: base de datos, API y primeras interfaces (HU-1 y HU-3)"
git branch -M main
git remote add origin <URL-del-repositorio>
git push -u origin main
```

## Sprint 2 · HU-2 y HU-4

Se completa la gestión básica de repuestos y el reporte de mantenimiento:

- `GET /api/repuestos`: consulta de inventario para usuarios autenticados.
- `POST /api/repuestos`: alta de repuestos (solo supervisor; código único).
- `POST /api/repuestos/<id>/stock`: ajuste de existencias (solo supervisor; nunca permite stock negativo).
- `POST /api/intervenciones/<id>/consumos`: consumo asociado a una intervención abierta; descuenta stock y registra cantidad, fecha y costo histórico en una operación transaccional.
- `GET /api/intervenciones/<id>/consumos`: consulta de consumos de una intervención.
- `GET /api/reportes/resumen`: indicadores de equipos, intervenciones, inventario y costos (solo supervisor).

La interfaz agrega las secciones **Repuestos** y **Reportes**. El técnico puede registrar consumos en intervenciones abiertas y consultar el detalle en el historial. El supervisor puede crear repuestos, ajustar stock y consultar/exportar el resumen CSV.

Pruebas Sprint 2:
```
python -m unittest discover -s tests -v
```

La base de datos usa SQLite y conserva el costo de cada consumo como dato histórico, aunque el costo unitario del catálogo cambie después.
