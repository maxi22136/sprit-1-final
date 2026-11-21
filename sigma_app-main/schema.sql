PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS usuarios (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL UNIQUE,
  rol TEXT NOT NULL CHECK (rol IN ('tecnico','supervisor','bodega','jefatura')),
  clave_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS equipos (
  id TEXT PRIMARY KEY,
  nombre TEXT NOT NULL,
  ubicacion TEXT NOT NULL,
  estado TEXT NOT NULL DEFAULT 'activo' CHECK (estado IN ('activo','inactivo'))
);

CREATE TABLE IF NOT EXISTS intervenciones (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  equipo_id TEXT NOT NULL REFERENCES equipos(id),
  tipo TEXT NOT NULL CHECK (tipo IN ('Correctiva','Preventiva')),
  falla TEXT NOT NULL,
  estado TEXT NOT NULL DEFAULT 'En proceso' CHECK (estado IN ('En proceso','Cerrada')),
  tecnico_id INTEGER NOT NULL REFERENCES usuarios(id),
  fecha_inicio TEXT NOT NULL,
  fecha_termino TEXT,
  -- Regla de negocio: una intervención no se cierra sin fecha de término
  CHECK (estado <> 'Cerrada' OR fecha_termino IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS acciones (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  intervencion_id INTEGER NOT NULL REFERENCES intervenciones(id),
  tecnico_id INTEGER NOT NULL REFERENCES usuarios(id),
  fecha TEXT NOT NULL,
  texto TEXT NOT NULL
);

-- Tablas para el Sprint 2 (HU-2 repuestos y HU-4 reportes)
CREATE TABLE IF NOT EXISTS repuestos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  codigo TEXT NOT NULL UNIQUE,
  nombre TEXT NOT NULL,
  stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
  costo_unitario REAL NOT NULL CHECK (costo_unitario >= 0)
);

CREATE TABLE IF NOT EXISTS consumos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  intervencion_id INTEGER NOT NULL REFERENCES intervenciones(id),
  repuesto_id INTEGER NOT NULL REFERENCES repuestos(id),
  cantidad INTEGER NOT NULL CHECK (cantidad > 0),
  costo_total REAL NOT NULL CHECK (costo_total >= 0),
  fecha TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS actividad (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  fecha TEXT NOT NULL,
  usuario TEXT NOT NULL,
  accion TEXT NOT NULL
);

-- Integridad: el historial no se puede borrar
CREATE TRIGGER IF NOT EXISTS no_borrar_intervenciones BEFORE DELETE ON intervenciones
BEGIN SELECT RAISE(ABORT, 'El historial no se puede borrar'); END;
CREATE TRIGGER IF NOT EXISTS no_borrar_acciones BEFORE DELETE ON acciones
BEGIN SELECT RAISE(ABORT, 'El historial no se puede borrar'); END;
CREATE TRIGGER IF NOT EXISTS no_borrar_consumos BEFORE DELETE ON consumos
BEGIN SELECT RAISE(ABORT, 'El historial no se puede borrar'); END;
