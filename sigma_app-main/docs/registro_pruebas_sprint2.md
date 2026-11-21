# Registro de pruebas · Sprint 2

Historias identificadas en `docs/diseno_bd.md`: HU-2 (repuestos y consumos) y HU-4 (reportes). Ejecutar con `python -m unittest discover -s tests -v`.

| ID | Tipo | Caso | Resultado esperado |
|---|---|---|---|
| S2-01 | Individual/API | Consultar repuestos sin sesión | HTTP 401 |
| S2-02 | Individual/API | Supervisor crea repuesto válido | HTTP 201 y registro persistido |
| S2-03 | Individual/API | Crear código de repuesto duplicado | HTTP 409; no duplica |
| S2-04 | Seguridad | Técnico intenta crear repuesto | HTTP 403 |
| S2-05 | Individual/API | Técnico consume repuesto en intervención abierta | HTTP 201; stock disminuye y costo queda registrado |
| S2-06 | Integridad | Consumir más unidades que las disponibles | HTTP 409; stock permanece igual |
| S2-07 | Validación | Cantidad cero o negativa | HTTP 400 |
| S2-08 | Integridad | Consumir en intervención cerrada | HTTP 409 |
| S2-09 | Seguridad/Reporte | Técnico consulta reportes | HTTP 403 |
| S2-10 | Reporte | Supervisor consulta resumen tras un consumo | HTTP 200; costo acumulado correcto |
| S2-11 | Inventario | Ajuste de stock que lo dejaría negativo | HTTP 409; stock sin cambios |
| S2-12 | Inventario | Supervisor aumenta stock | HTTP 200 y nuevo saldo persistido |

## Validaciones finales de integración

1. Iniciar sesión como técnico, crear intervención, registrar consumo y comprobar el saldo actualizado.
2. Abrir Historial y comprobar que aparecen acciones y repuestos consumidos con cantidades y costos.
3. Cerrar la intervención e intentar registrar otro consumo: debe rechazarse.
4. Iniciar sesión como supervisor, crear repuesto, ajustar stock y consultar Reportes.
5. Comprobar que el costo de repuestos del reporte coincide con la suma de consumos persistidos.
6. Reiniciar el servidor y volver a consultar inventario, historial y reportes: los datos deben mantenerse en SQLite.

## Estado de ejecución en esta entrega

Los casos anteriores están implementados como pruebas automatizadas en `tests/test_sprint2.py`. La sintaxis Python y JavaScript fue validada. La ejecución real de la suite quedó pendiente en este entorno porque Flask no está instalado y no fue posible descargar dependencias por falta de conexión a Internet. No marcar como aprobadas hasta ejecutar el comando en un entorno con las dependencias instaladas.
