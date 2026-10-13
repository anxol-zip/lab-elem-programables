# Cambios de la versión 2

Se mantienen el circuito, la presentación y la actividad general.

Cambios de código:

- `00_bloqueo.py`: ahora el botón ayuda a demostrar visualmente la mala respuesta de un loop bloqueante.
- `01_wokwi_multitarea.py`: ACK visible; rojo parpadea antes del ACK y queda fijo después; botón detectado por flanco.
- `02_dualcore_fisico_thread.py`: Core 0 ya no duerme 1 segundo completo; UI, botón y logger tienen periodos independientes y el botón responde rápido.
- `03_DO08_starter.py`: el reto incluye filtro + ACK + parpadeo de alarma + detección de una sola pulsación.
- `WOKWI_TEMPLATE/main.py`: actualizado al SHOW 1 mejorado.
- README y tarea: actualizados para explicar el comportamiento del ACK.
