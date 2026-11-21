"""Creación e inicialización de la base de datos SQLite de SIGMA."""
import os
import sqlite3
from werkzeug.security import generate_password_hash

BASE = os.path.dirname(os.path.abspath(__file__))
CLAVE_DEMO = "sigma123"  # solo para desarrollo; cambiar en producción


def init_db(path):
    con = sqlite3.connect(path)
    with open(os.path.join(BASE, "schema.sql"), encoding="utf-8") as f:
        con.executescript(f.read())
    if con.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
        h = generate_password_hash(CLAVE_DEMO)
        con.executemany(
            "INSERT INTO usuarios (nombre, rol, clave_hash) VALUES (?,?,?)",
            [("Técnico · Turno A", "tecnico", h), ("Técnico · Turno B", "tecnico", h),
             ("Supervisor de mantenimiento", "supervisor", h)])
        con.executemany(
            "INSERT INTO equipos (id, nombre, ubicacion) VALUES (?,?,?)",
            [("EQ-001", "Compresor de aire", "Sala de máquinas"), ("EQ-002", "Prensa hidráulica", "Línea 1"),
             ("EQ-003", "Cinta transportadora", "Línea 2"), ("EQ-004", "Torno CNC", "Taller"),
             ("EQ-005", "Horno de curado", "Línea 3"), ("EQ-006", "Montacargas", "Bodega")])
        con.executemany(
            "INSERT INTO repuestos (codigo, nombre, stock, costo_unitario) VALUES (?,?,?,?)",
            [("REP-001", "Manguera hidráulica", 10, 18500), ("REP-002", "Sello de pistón", 25, 4200),
             ("REP-003", "Correa de transmisión", 8, 12900)])
    con.commit()
    con.close()


if __name__ == "__main__":
    ruta = os.path.join(BASE, "sigma.db")
    init_db(ruta)
    print("Base de datos lista en", ruta)
