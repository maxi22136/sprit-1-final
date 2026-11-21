"""Pruebas funcionales del Sprint 1 (HU-1 y HU-3). Ejecutar: python -m unittest discover -v"""
import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app as sigma  # noqa: E402
from db import CLAVE_DEMO, init_db  # noqa: E402

TEC_A, TEC_B, SUP = 1, 2, 3


class BaseTest(unittest.TestCase):
    def setUp(self):
        fd, self.ruta = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.remove(self.ruta)
        sigma.app.config["DB_PATH"] = self.ruta
        init_db(self.ruta)
        sigma.app.config["TESTING"] = True

    def tearDown(self):
        if os.path.exists(self.ruta):
            os.remove(self.ruta)

    def cliente(self, uid):
        c = sigma.app.test_client()
        r = c.post("/api/login", json={"usuario_id": uid, "clave": CLAVE_DEMO})
        self.assertEqual(r.status_code, 200)
        return c

    def nueva(self, c, **kw):
        d = {"equipo_id": "EQ-002", "tipo": "Correctiva", "falla": "Fuga de aceite",
             "acciones": "Se revisó el sello", "estado": "En proceso"}
        d.update(kw)
        return c.post("/api/intervenciones", json=d)


class PruebasHU1(BaseTest):
    def test_login_invalido_se_rechaza_y_se_registra(self):
        c = sigma.app.test_client()
        self.assertEqual(c.post("/api/login", json={"usuario_id": TEC_A, "clave": "mala"}).status_code, 401)
        log = self.cliente(SUP).get("/api/actividad").get_json()
        self.assertTrue(any("acceso fallido" in g["a"] for g in log))

    def test_tecnico_registra_intervencion_con_fecha_y_responsable(self):
        c = self.cliente(TEC_A)
        self.assertEqual(self.nueva(c).status_code, 201)
        i = c.get("/api/intervenciones").get_json()[0]
        self.assertEqual(i["tec"], "Técnico · Turno A")
        self.assertTrue(i["ini"])
        self.assertEqual(i["est"], "En proceso")

    def test_campos_obligatorios(self):
        self.assertEqual(self.nueva(self.cliente(TEC_A), falla="").status_code, 400)

    def test_otro_turno_continua_la_intervencion(self):
        a, b = self.cliente(TEC_A), self.cliente(TEC_B)
        iid = self.nueva(a).get_json()["id"]
        r = b.post("/api/intervenciones/%d/acciones" % iid, json={"texto": "Se cambió la manguera"})
        self.assertEqual(r.status_code, 200)
        i = b.get("/api/intervenciones").get_json()[0]
        self.assertEqual(i["est"], "En proceso")
        self.assertEqual([x["u"] for x in i["ac"]], ["Técnico · Turno A", "Técnico · Turno B"])

    def test_cierre_guarda_fecha_y_bloquea_nuevas_acciones(self):
        c = self.cliente(TEC_A)
        iid = self.nueva(c).get_json()["id"]
        c.post("/api/intervenciones/%d/acciones" % iid, json={"cerrar": True})
        i = c.get("/api/intervenciones").get_json()[0]
        self.assertEqual(i["est"], "Cerrada")
        self.assertTrue(i["fin"])
        r = c.post("/api/intervenciones/%d/acciones" % iid, json={"texto": "x"})
        self.assertEqual(r.status_code, 409)


class PruebasHU3(BaseTest):
    def test_supervisor_cambia_estado(self):
        s = self.cliente(SUP)
        self.assertEqual(s.post("/api/equipos/EQ-001/estado").get_json()["e"], "inactivo")
        self.assertEqual(s.post("/api/equipos/EQ-001/estado").get_json()["e"], "activo")

    def test_tecnico_no_puede_cambiar_estado_y_queda_registrado(self):
        t = self.cliente(TEC_A)
        self.assertEqual(t.post("/api/equipos/EQ-001/estado").status_code, 403)
        eq = {e["id"]: e["e"] for e in t.get("/api/equipos").get_json()}
        self.assertEqual(eq["EQ-001"], "activo")
        log = self.cliente(SUP).get("/api/actividad").get_json()
        self.assertTrue(any("Intento no autorizado" in g["a"] for g in log))

    def test_actividad_solo_para_supervisor(self):
        self.assertEqual(self.cliente(TEC_A).get("/api/actividad").status_code, 403)

    def test_sin_sesion_no_hay_acceso(self):
        self.assertEqual(sigma.app.test_client().get("/api/equipos").status_code, 401)


class PruebasBaseDeDatos(BaseTest):
    def test_historial_no_se_puede_borrar(self):
        self.nueva(self.cliente(TEC_A))
        con = sqlite3.connect(self.ruta)
        with self.assertRaises(sqlite3.DatabaseError):
            con.execute("DELETE FROM intervenciones")
        con.close()

    def test_no_se_cierra_sin_fecha_de_termino(self):
        self.nueva(self.cliente(TEC_A))
        con = sqlite3.connect(self.ruta)
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute("UPDATE intervenciones SET estado='Cerrada', fecha_termino=NULL")
        con.close()


if __name__ == "__main__":
    unittest.main()
