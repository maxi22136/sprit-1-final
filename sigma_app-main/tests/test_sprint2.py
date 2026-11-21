"""Pruebas de aceptación del Sprint 2: HU-2 repuestos y HU-4 reportes."""
import os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app as sigma
from db import CLAVE_DEMO, init_db

TEC, SUP = 1, 3
class Sprint2Test(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix='.db'); os.close(fd); os.remove(self.path)
        sigma.app.config.update(DB_PATH=self.path, TESTING=True)
        init_db(self.path)
    def tearDown(self):
        if os.path.exists(self.path): os.remove(self.path)
    def login(self, uid):
        c=sigma.app.test_client(); self.assertEqual(c.post('/api/login',json={'usuario_id':uid,'clave':CLAVE_DEMO}).status_code,200); return c
    def intervention(self,c):
        return c.post('/api/intervenciones',json={'equipo_id':'EQ-002','tipo':'Correctiva','falla':'Fuga','acciones':'Inspección','estado':'En proceso'}).get_json()['id']
    def test_listado_repuestos_requiere_sesion(self):
        self.assertEqual(sigma.app.test_client().get('/api/repuestos').status_code,401)
        self.assertEqual(len(self.login(TEC).get('/api/repuestos').get_json()),3)
    def test_supervisor_crea_repuesto_y_codigo_es_unico(self):
        c=self.login(SUP); d={'codigo':'REP-004','nombre':'Rodamiento','stock':4,'costo_unitario':2500}
        self.assertEqual(c.post('/api/repuestos',json=d).status_code,201)
        self.assertEqual(c.post('/api/repuestos',json=d).status_code,409)
    def test_tecnico_no_puede_crear_repuesto(self):
        self.assertEqual(self.login(TEC).post('/api/repuestos',json={'codigo':'X','nombre':'X'}).status_code,403)
    def test_consumo_descuenta_stock_y_registra_costo(self):
        c=self.login(TEC); iid=self.intervention(c); r=c.get('/api/repuestos').get_json()[0]
        res=c.post(f'/api/intervenciones/{iid}/consumos',json={'repuesto_id':r['id'],'cantidad':2})
        self.assertEqual(res.status_code,201); self.assertEqual(res.get_json()['stock_restante'],r['stock']-2)
        cons=c.get(f'/api/intervenciones/{iid}/consumos').get_json()
        self.assertEqual(cons[0]['cantidad'],2); self.assertEqual(cons[0]['costo_total'],r['costo_unitario']*2)
    def test_stock_insuficiente_no_modifica_inventario(self):
        c=self.login(TEC); iid=self.intervention(c); r=c.get('/api/repuestos').get_json()[0]
        res=c.post(f'/api/intervenciones/{iid}/consumos',json={'repuesto_id':r['id'],'cantidad':r['stock']+1})
        self.assertEqual(res.status_code,409)
        self.assertEqual(next(x for x in c.get('/api/repuestos').get_json() if x['id']==r['id'])['stock'],r['stock'])
    def test_no_permite_cantidad_cero_o_negativa(self):
        c=self.login(TEC); iid=self.intervention(c); r=c.get('/api/repuestos').get_json()[0]
        for n in (0,-1): self.assertEqual(c.post(f'/api/intervenciones/{iid}/consumos',json={'repuesto_id':r['id'],'cantidad':n}).status_code,400)
    def test_no_consumir_en_intervencion_cerrada(self):
        c=self.login(TEC); iid=self.intervention(c); c.post(f'/api/intervenciones/{iid}/acciones',json={'cerrar':True})
        r=c.get('/api/repuestos').get_json()[0]
        self.assertEqual(c.post(f'/api/intervenciones/{iid}/consumos',json={'repuesto_id':r['id'],'cantidad':1}).status_code,409)
    def test_reporte_solo_supervisor_y_agrega_costos(self):
        t=self.login(TEC); iid=self.intervention(t); r=t.get('/api/repuestos').get_json()[0]
        t.post(f'/api/intervenciones/{iid}/consumos',json={'repuesto_id':r['id'],'cantidad':1})
        self.assertEqual(t.get('/api/reportes/resumen').status_code,403)
        report=self.login(SUP).get('/api/reportes/resumen')
        self.assertEqual(report.status_code,200); self.assertEqual(report.get_json()['costo_repuestos'],r['costo_unitario'])
    def test_ajuste_stock_supervisor_y_no_negativo(self):
        c=self.login(SUP); r=c.get('/api/repuestos').get_json()[0]
        self.assertEqual(c.post(f'/api/repuestos/{r["id"]}/stock',json={'cambio':-999}).status_code,409)
        self.assertEqual(c.post(f'/api/repuestos/{r["id"]}/stock',json={'cambio':3}).get_json()['stock'],r['stock']+3)

if __name__=='__main__': unittest.main()
