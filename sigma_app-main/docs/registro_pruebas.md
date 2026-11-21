# Registro de pruebas funcionales · Sprint 1

Comando: `python -m unittest discover -s tests -v` · Resultado: **11 pruebas, todas aprobadas**

| N° | Historia | Prueba | Resultado |
|---|---|---|---|
| 1 | HU-1 | El técnico registra una intervención y se guardan fecha, hora y técnico responsable | Aprobada |
| 2 | HU-1 | No se guarda sin falla ni acciones realizadas | Aprobada |
| 3 | HU-1 | Un técnico de otro turno ve y continúa la intervención en estado "En proceso" | Aprobada |
| 4 | HU-1 | Al cerrar se guarda la fecha de término y no se aceptan más acciones | Aprobada |
| 5 | HU-3 | El supervisor cambia el estado de una máquina (activo/inactivo) | Aprobada |
| 6 | HU-3 | Un técnico no puede cambiar el estado y el intento queda registrado | Aprobada |
| 7 | Seguridad | Una clave incorrecta se rechaza y queda registrada | Aprobada |
| 8 | Seguridad | Sin sesión no hay acceso; el registro de actividad es solo del supervisor | Aprobada (2 pruebas) |
| 9 | Base de datos | El historial no se puede borrar | Aprobada |
| 10 | Base de datos | No se puede cerrar una intervención sin fecha de término | Aprobada |

Capturas de la aplicación funcionando: carpeta `docs/capturas`.
