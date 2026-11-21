"""SIGMA · Sprint 1 y Sprint 2: API Flask + SQLite (HU-1 registro de intervenciones, HU-3 estado de máquinas)."""
import os
import sqlite3
from datetime import datetime
from functools import wraps

from flask import Flask, g, jsonify, request, session
from werkzeug.security import check_password_hash

from db import BASE, init_db

app = Flask(__name__, static_folder="static", static_url_path="")
app.secret_key = os.environ.get("SIGMA_SECRET", "cambiar-en-produccion")
app.config["DB_PATH"] = os.environ.get("SIGMA_DB", os.path.join(BASE, "sigma.db"))


def db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DB_PATH"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def cerrar_db(_):
    con = g.pop("db", None)
    if con:
        con.close()


def ahora():
    return datetime.now().isoformat(timespec="seconds")


def registrar(usuario, accion):
    db().execute("INSERT INTO actividad (fecha, usuario, accion) VALUES (?,?,?)", (ahora(), usuario, accion))
    db().commit()


def requiere(rol=None):
    """Exige sesión iniciada y, si se indica, un rol. Los intentos no autorizados quedan registrados."""
    def deco(f):
        @wraps(f)
        def interno(*a, **kw):
            uid = session.get("uid")
            u = db().execute("SELECT * FROM usuarios WHERE id=?", (uid,)).fetchone() if uid else None
            if not u:
                return jsonify(error="Debes iniciar sesión."), 401
            if rol and u["rol"] != rol:
                registrar(u["nombre"], "Intento no autorizado: %s %s" % (request.method, request.path))
                return jsonify(error="Solo el %s puede realizar esta acción." % rol), 403
            g.user = u
            return f(*a, **kw)
        return interno
    return deco


@app.get("/")
def inicio():
    return app.send_static_file("index.html")


@app.get("/api/usuarios")
def usuarios():
    return jsonify([dict(r) for r in db().execute("SELECT id, nombre FROM usuarios ORDER BY id")])


@app.post("/api/login")
def login():
    d = request.get_json(silent=True) or {}
    u = db().execute("SELECT * FROM usuarios WHERE id=?", (d.get("usuario_id"),)).fetchone()
    if not u or not check_password_hash(u["clave_hash"], d.get("clave", "")):
        registrar(u["nombre"] if u else "Desconocido", "Intento de acceso fallido")
        return jsonify(error="Usuario o clave incorrectos."), 401
    session["uid"] = u["id"]
    registrar(u["nombre"], "Inicio de sesión")
    return jsonify(id=u["id"], n=u["nombre"], r=u["rol"])


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify(ok=True)


@app.get("/api/yo")
@requiere()
def yo():
    return jsonify(id=g.user["id"], n=g.user["nombre"], r=g.user["rol"])


@app.get("/api/equipos")
@requiere()
def equipos():
    return jsonify([dict(r) for r in db().execute(
        "SELECT id, nombre AS n, ubicacion AS u, estado AS e FROM equipos ORDER BY id")])


@app.post("/api/equipos/<eid>/estado")
@requiere("supervisor")
def cambiar_estado(eid):
    e = db().execute("SELECT * FROM equipos WHERE id=?", (eid,)).fetchone()
    if not e:
        return jsonify(error="El equipo no existe."), 404
    nuevo = "inactivo" if e["estado"] == "activo" else "activo"
    db().execute("UPDATE equipos SET estado=? WHERE id=?", (nuevo, eid))
    db().commit()
    registrar(g.user["nombre"], "Estado de %s cambiado a %s" % (eid, nuevo))
    return jsonify(id=eid, e=nuevo)


@app.get("/api/intervenciones")
@requiere()
def listar_intervenciones():
    filas = db().execute(
        "SELECT i.*, u.nombre AS tec FROM intervenciones i JOIN usuarios u ON u.id=i.tecnico_id "
        "ORDER BY i.fecha_inicio DESC, i.id DESC").fetchall()
    res = []
    for r in filas:
        acs = db().execute(
            "SELECT a.fecha AS t, u.nombre AS u, a.texto AS x FROM acciones a "
            "JOIN usuarios u ON u.id=a.tecnico_id WHERE a.intervencion_id=? ORDER BY a.id", (r["id"],)).fetchall()
        cons = db().execute(
            "SELECT rp.codigo, rp.nombre, c.cantidad, c.costo_total, c.fecha "
            "FROM consumos c JOIN repuestos rp ON rp.id=c.repuesto_id "
            "WHERE c.intervencion_id=? ORDER BY c.id", (r["id"],)).fetchall()
        res.append({"id": r["id"], "eq": r["equipo_id"], "tipo": r["tipo"], "falla": r["falla"],
                    "est": r["estado"], "ini": r["fecha_inicio"], "fin": r["fecha_termino"],
                    "tec": r["tec"], "ac": [dict(a) for a in acs], "consumos": [dict(c) for c in cons]})
    return jsonify(res)


@app.post("/api/intervenciones")
@requiere("tecnico")
def crear_intervencion():
    d = request.get_json(silent=True) or {}
    falla, acciones = (d.get("falla") or "").strip(), (d.get("acciones") or "").strip()
    tipo, estado = d.get("tipo"), d.get("estado", "En proceso")
    if not falla or not acciones:
        return jsonify(error="Completa la falla y las acciones realizadas."), 400
    if tipo not in ("Correctiva", "Preventiva") or estado not in ("En proceso", "Cerrada"):
        return jsonify(error="Tipo o estado no válido."), 400
    if not db().execute("SELECT 1 FROM equipos WHERE id=?", (d.get("equipo_id"),)).fetchone():
        return jsonify(error="El equipo no existe."), 404
    t = ahora()
    cur = db().execute(
        "INSERT INTO intervenciones (equipo_id, tipo, falla, estado, tecnico_id, fecha_inicio, fecha_termino) "
        "VALUES (?,?,?,?,?,?,?)",
        (d["equipo_id"], tipo, falla, estado, g.user["id"], t, t if estado == "Cerrada" else None))
    db().execute("INSERT INTO acciones (intervencion_id, tecnico_id, fecha, texto) VALUES (?,?,?,?)",
                 (cur.lastrowid, g.user["id"], t, acciones))
    db().commit()
    registrar(g.user["nombre"], "Intervención registrada en %s (%s)" % (d["equipo_id"], estado))
    return jsonify(id=cur.lastrowid), 201


@app.post("/api/intervenciones/<int:iid>/acciones")
@requiere("tecnico")
def continuar_intervencion(iid):
    d = request.get_json(silent=True) or {}
    texto, cerrar = (d.get("texto") or "").strip(), bool(d.get("cerrar"))
    i = db().execute("SELECT * FROM intervenciones WHERE id=?", (iid,)).fetchone()
    if not i:
        return jsonify(error="La intervención no existe."), 404
    if i["estado"] == "Cerrada":
        return jsonify(error="La intervención ya está cerrada."), 409
    if not texto and not cerrar:
        return jsonify(error="Escribe la acción realizada."), 400
    t = ahora()
    if texto:
        db().execute("INSERT INTO acciones (intervencion_id, tecnico_id, fecha, texto) VALUES (?,?,?,?)",
                     (iid, g.user["id"], t, texto))
    if cerrar:
        db().execute("UPDATE intervenciones SET estado='Cerrada', fecha_termino=? WHERE id=?", (t, iid))
    db().commit()
    registrar(g.user["nombre"], "Intervención %d %s" % (iid, "cerrada" if cerrar else "con nueva acción"))
    return jsonify(ok=True)


@app.get("/api/actividad")
@requiere("supervisor")
def actividad():
    return jsonify([dict(r) for r in db().execute(
        "SELECT fecha AS t, usuario AS u, accion AS a FROM actividad ORDER BY id DESC LIMIT 200")])


# ---------------- Sprint 2: HU-2 repuestos y HU-4 reportes ----------------
@app.get("/api/repuestos")
@requiere()
def listar_repuestos():
    return jsonify([dict(r) for r in db().execute(
        "SELECT id, codigo, nombre, stock, costo_unitario FROM repuestos ORDER BY nombre")])


@app.post("/api/repuestos")
@requiere("supervisor")
def crear_repuesto():
    d = request.get_json(silent=True) or {}
    codigo, nombre = (d.get("codigo") or "").strip().upper(), (d.get("nombre") or "").strip()
    try:
        stock, costo = int(d.get("stock", 0)), float(d.get("costo_unitario", 0))
    except (TypeError, ValueError):
        return jsonify(error="Stock y costo deben ser valores numéricos válidos."), 400
    if not codigo or not nombre or stock < 0 or costo < 0:
        return jsonify(error="Código y nombre son obligatorios; stock y costo no pueden ser negativos."), 400
    try:
        cur = db().execute("INSERT INTO repuestos(codigo,nombre,stock,costo_unitario) VALUES(?,?,?,?)",
                           (codigo, nombre, stock, costo))
        db().commit()
    except sqlite3.IntegrityError:
        db().rollback()
        return jsonify(error="Ya existe un repuesto con ese código."), 409
    registrar(g.user["nombre"], "Repuesto %s creado" % codigo)
    return jsonify(id=cur.lastrowid), 201


@app.post("/api/repuestos/<int:rid>/stock")
@requiere("supervisor")
def ajustar_stock(rid):
    d = request.get_json(silent=True) or {}
    try:
        cambio = int(d.get("cambio"))
    except (TypeError, ValueError):
        return jsonify(error="El ajuste debe ser un número entero."), 400
    r = db().execute("SELECT * FROM repuestos WHERE id=?", (rid,)).fetchone()
    if not r:
        return jsonify(error="El repuesto no existe."), 404
    if r["stock"] + cambio < 0:
        return jsonify(error="Stock insuficiente: el inventario no puede quedar negativo."), 409
    db().execute("UPDATE repuestos SET stock=stock+? WHERE id=?", (cambio, rid))
    db().commit()
    registrar(g.user["nombre"], "Stock de %s ajustado en %+d" % (r["codigo"], cambio))
    return jsonify(id=rid, stock=r["stock"] + cambio)


@app.post("/api/intervenciones/<int:iid>/consumos")
@requiere("tecnico")
def consumir_repuesto(iid):
    d = request.get_json(silent=True) or {}
    try:
        rid, cantidad = int(d.get("repuesto_id")), int(d.get("cantidad"))
    except (TypeError, ValueError):
        return jsonify(error="Selecciona un repuesto y una cantidad válida."), 400
    if cantidad <= 0:
        return jsonify(error="La cantidad debe ser mayor que cero."), 400
    con = db()
    i = con.execute("SELECT * FROM intervenciones WHERE id=?", (iid,)).fetchone()
    r = con.execute("SELECT * FROM repuestos WHERE id=?", (rid,)).fetchone()
    if not i:
        return jsonify(error="La intervención no existe."), 404
    if i["estado"] == "Cerrada":
        return jsonify(error="No se pueden cargar repuestos a una intervención cerrada."), 409
    if not r:
        return jsonify(error="El repuesto no existe."), 404
    if r["stock"] < cantidad:
        return jsonify(error="Stock insuficiente. Disponible: %d." % r["stock"]), 409
    t = ahora()
    costo = round(float(r["costo_unitario"]) * cantidad, 2)
    try:
        actualizado = con.execute("UPDATE repuestos SET stock=stock-? WHERE id=? AND stock>=?", (cantidad, rid, cantidad))
        if actualizado.rowcount != 1:
            con.rollback()
            return jsonify(error="Stock insuficiente; actualiza el inventario e inténtalo nuevamente."), 409
        con.execute("INSERT INTO consumos(intervencion_id,repuesto_id,cantidad,costo_total,fecha) VALUES(?,?,?,?,?)",
                    (iid, rid, cantidad, costo, t))
        con.commit()
    except sqlite3.Error:
        con.rollback()
        raise
    registrar(g.user["nombre"], "Consumo de %d unidad(es) de %s en intervención %d" % (cantidad, r["codigo"], iid))
    return jsonify(ok=True, costo_total=costo, stock_restante=r["stock"] - cantidad), 201


@app.get("/api/intervenciones/<int:iid>/consumos")
@requiere()
def consumos_intervencion(iid):
    if not db().execute("SELECT 1 FROM intervenciones WHERE id=?", (iid,)).fetchone():
        return jsonify(error="La intervención no existe."), 404
    filas = db().execute("SELECT c.id,c.cantidad,c.costo_total,c.fecha,r.codigo,r.nombre "
                         "FROM consumos c JOIN repuestos r ON r.id=c.repuesto_id "
                         "WHERE c.intervencion_id=? ORDER BY c.id", (iid,)).fetchall()
    return jsonify([dict(x) for x in filas])


@app.get("/api/reportes/resumen")
@requiere("supervisor")
def reporte_resumen():
    con = db()
    equipos = con.execute("SELECT estado,COUNT(*) total FROM equipos GROUP BY estado").fetchall()
    intervenciones = con.execute("SELECT estado,COUNT(*) total FROM intervenciones GROUP BY estado").fetchall()
    costos = con.execute("SELECT COALESCE(SUM(costo_total),0) total FROM consumos").fetchone()["total"]
    repuestos = con.execute("SELECT COUNT(*) total, COALESCE(SUM(stock),0) unidades, "
                            "SUM(CASE WHEN stock=0 THEN 1 ELSE 0 END) agotados FROM repuestos").fetchone()
    por_tipo = con.execute("SELECT tipo,COUNT(*) total FROM intervenciones GROUP BY tipo").fetchall()
    por_equipo = con.execute("SELECT e.id,e.nombre,COUNT(i.id) total FROM equipos e "
                             "LEFT JOIN intervenciones i ON i.equipo_id=e.id GROUP BY e.id,e.nombre ORDER BY total DESC").fetchall()
    return jsonify({"equipos": {r["estado"]: r["total"] for r in equipos},
                    "intervenciones": {r["estado"]: r["total"] for r in intervenciones},
                    "costo_repuestos": round(float(costos or 0), 2),
                    "inventario": dict(repuestos), "por_tipo": [dict(r) for r in por_tipo],
                    "por_equipo": [dict(r) for r in por_equipo]})


init_db(app.config["DB_PATH"])

if __name__ == "__main__":
    app.run(debug=True)
