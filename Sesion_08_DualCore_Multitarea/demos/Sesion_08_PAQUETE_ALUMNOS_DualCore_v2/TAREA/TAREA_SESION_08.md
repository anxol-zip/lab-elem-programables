# Tarea / entrega — Sesión 08

## Objetivo

Construir un sistema multitarea donde una tarea monitorea un sensor analógico a alta velocidad y otras tareas actualizan interfaz, terminal y botón sin bloquear el programa.

## Entrega mínima

En GitHub, crear la carpeta:

```text
Sesion_08_DualCore_Multitarea/
```

Debe contener:

- `README.md`
- `main_wokwi.py`
- `main_dualcore_physical.py` si hicieron prueba física
- carpeta `wokwi/` con `diagram.json` o enlace al proyecto
- carpeta `evidence/` con capturas del circuito y serial

## Requisitos del programa

1. Leer ADC en GP26.
2. Convertir la lectura a porcentaje.
3. Aplicar filtro de promedio móvil.
4. Clasificar estado: NORMAL, WARNING, ALARM.
5. Actualizar LEDs sin bloqueos largos.
6. Mostrar datos por terminal cada segundo.
7. Incluir heartbeat para comprobar que el sistema está vivo.
8. Implementar **ACK de alarma** con botón:
   - ALARM sin ACK → LED rojo parpadea.
   - ALARM con ACK → LED rojo fijo.
   - salir de ALARM → ACK vuelve a `False`.
9. Detectar una sola pulsación usando el cambio `1 -> 0`.
10. Si hay Pico física, probar la versión con `_thread`.

## Tabla de pruebas obligatoria

| Prueba | Resultado esperado | PASS/FAIL |
|---|---|---|
| Potenciómetro bajo | NORMAL / LED verde | |
| Potenciómetro medio | WARNING / LED amarillo | |
| Potenciómetro alto | ALARM / rojo parpadea | |
| Botón fuera de ALARM | No reconoce alarma | |
| Botón durante ALARM | ACK=True / rojo fijo | |
| Salir de ALARM | ACK vuelve a False | |
| Heartbeat | LED azul cambia sin congelarse | |
| Serial | Muestra datos cada segundo | |
| Sensor a 20 ms | ~50 muestras por segundo | |
| Filtro | Reduce variaciones rápidas | |
| Pico física | `_thread` mantiene adquisición y UI | |

## Preguntas de análisis

1. ¿Cuál es la diferencia entre multitarea cooperativa en Wokwi y dual-core real?
2. ¿Por qué no usamos `sleep_ms(1000)` dentro de la tarea crítica del sensor?
3. ¿Por qué una tarea puede ejecutarse cada 20 ms y el terminal cada 1000 ms?
4. ¿Por qué se necesita `lock` cuando dos núcleos comparten datos?
5. ¿Qué diferencia hay entre **reconocer una alarma** y **eliminar la condición de alarma**?
6. ¿Qué evidencia demuestra que el sistema no se bloquea?
