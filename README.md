# SIGMA · Gestión de mantención de activos (Manufacturas Andina S.A.)

**Sprint 1 y Sprint 2 · RQY1101 Ingeniería de Requisitos · DuocUC**

## Historias de usuario

**Sprint 1**
- **HU-1:** Registro de fallas, reparaciones y mantenciones, permitiendo continuar intervenciones entre turnos y cerrarlas.
- **HU-3:** Actualización del estado de las máquinas, exclusiva del supervisor, registrando intentos no autorizados.

**Sprint 2**
- **HU-2:** Gestión de repuestos, control de inventario y registro de consumos asociados a intervenciones.
- **HU-4:** Reportes de mantenimiento con indicadores de equipos, intervenciones y costos.

## Cómo ejecutarlo

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Abrir: http://127.0.0.1:5000

La base de datos SQLite (`sigma.db`) se crea automáticamente.

## Usuarios de prueba

Contraseña: `sigma123`

- Técnico · Turno A
- Técnico · Turno B
- Supervisor de mantenimiento

## Pruebas

```bash
python -m unittest discover -s tests -v
```

- `test_api.py`: pruebas del Sprint 1.
- `test_sprint2.py`: pruebas del Sprint 2.

## Estructura del proyecto

- `app.py`: API Flask y reglas de negocio.
- `db.py` y `schema.sql`: conexión y estructura de la base de datos.
- `static/index.html`: interfaz gráfica.
- `tests/`: pruebas funcionales y automatizadas.
- `docs/`: diseño de base de datos y registros de pruebas.

## Actualización de GitHub

```bash
git add .
git commit -m "Sprint 2: gestión de repuestos y reportes"
git push origin main
```

## Resultado esperado

Aplicación integrada y funcional, con las cuatro historias de usuario implementadas, persistencia de datos, interfaces operativas y pruebas registradas.

**Proyecto académico · DuocUC · Manufacturas Andina S.A.**
