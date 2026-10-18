# Sesión 08 — Procesamiento multihilo / Dual-Core

**Reto 08 — Sistema multitarea**
_Angel Rugerio Jiménez · 201720 · Lab. de Elementos Programables_

## 1. Objetivo y qué es multitarea

Una tarea **monitorea un sensor crítico** (potenciómetro en GP26) cada 20 ms mientras otras atienden botón, LEDs y serial, **sin que ninguna bloquee a las demás**.

**Multitarea** es organizar el programa en tareas con su propio ritmo en vez de una sola fila con `sleep`. Se hizo de dos formas:

| Archivo | Dónde corre | Cómo |
|---|---|---|
| `main_wokwi.py` | Wokwi (1 núcleo) | **Cooperativa:** el `while` revisa con `ticks_ms()` a qué tarea le toca; ninguna duerme |
| `main_dualcore_physical.py` | Pico 2 W (2 núcleos) | **Paralela:** el sensor corre en Core 1 con `_thread`; Core 0 atiende lo demás |

| Tarea | Periodo | Wokwi | Pico física |
|---|---|---|---|
| Sensor: ADC → filtro → % → estado | 20 ms | loop único | **Core 1** |
| Botón: ACK / reset | 50 ms | loop único | Core 0 |
| LEDs + heartbeat | 200 ms | loop único | Core 0 |
| Serial | 1000 ms | loop único | Core 0 |

## 2. Qué simula Wokwi y qué prueba la Pico física

**Wokwi** simula un solo núcleo: valida la **lógica** (periodos, filtro, umbrales, ACK) y que ninguna tarea congela a las otras, pero no puede probar dual-core.

**La Pico física** prueba el **paralelismo**: Core 1 sigue midiendo aunque Core 0 esté imprimiendo. Los núcleos comparten el diccionario `shared`, y todo acceso va entre `lock.acquire()` / `lock.release()` para que Core 0 nunca lea datos a medio actualizar. El cálculo se hace fuera del lock para tenerlo el menor tiempo posible.

Simulación: [`wokwi/enlace.md`](./wokwi/enlace.md) · Circuito: [`wokwi/diagram.json`](./wokwi/diagram.json) (plantilla del curso).

| Elemento | Pin | Función |
|---|---|---|
| Potenciómetro (3V3 / GND) | GP26 / ADC0 | Sensor crítico |
| LED verde / amarillo / rojo | GP13 / GP14 / GP15 | NORMAL / WARNING / ALARM |
| LED azul | GP12 | Heartbeat |
| Botón a GND (`PULL_UP`) | GP16 | ACK en ALARM / reset del contador fuera de ALARM |

<!-- TODO Angel: anotar el valor de las resistencias de la placa si no son 330 Ω. -->

## 3. Umbrales y botón

| Estado | % de la señal **filtrada** | LED |
|---|---|---|
| NORMAL | < 50 % | Verde |
| WARNING | 50 % a < 75 % | Amarillo |
| ALARM | ≥ 75 % | Rojo: parpadea sin ACK, fijo con ACK |

Los umbrales son constantes (`WARNING`, `ALARM`) al inicio de ambos archivos. El botón solo cuenta el flanco `1 → 0` (una pulsación = un evento): **en ALARM** reconoce la alarma (`ack=True`); **fuera de ALARM** reinicia el contador de muestras. Al salir de ALARM el ACK se borra solo.

## 4. Qué hace el filtro

Promedio móvil de las últimas 8 lecturas (`append` + `pop(0)`, como en el Reto 07). Con una lectura cada 20 ms la ventana cubre $8 \times 20\ \text{ms} = 160\ \text{ms}$: quita el ruido del ADC con un retraso que no se percibe (en el Reto 07 eran 3 s).

<!-- TODO Angel: con el potenciómetro quieto en la placa, anotar el rango de raw vs filtered (p. ej. "raw varió X cuentas, filtered Y"). En Wokwi raw = filtered porque el pot simulado no tiene ruido. -->

## 5. Resultados de la tabla de pruebas

<!-- TODO Angel: PASS/FAIL según lo observado. -->

| Prueba | Resultado esperado | Wokwi | Físico |
|---|---|---|---|
| Potenciómetro bajo | NORMAL / LED verde | | |
| Potenciómetro medio | WARNING / LED amarillo | | |
| Potenciómetro alto | ALARM / rojo parpadea | | |
| Botón fuera de ALARM | No reconoce alarma (reinicia contador) | | |
| Botón durante ALARM | ACK=True / rojo fijo | | |
| Salir de ALARM | ACK vuelve a False | | |
| Heartbeat | LED azul cambia sin congelarse | | |
| Serial | Muestra datos cada segundo | | |
| Sensor a 20 ms | ~50 muestras por segundo (`rate=`) | | |
| Filtro | Reduce variaciones rápidas | | |
| Pico física | `_thread` mantiene adquisición y UI | — | |

`rate=` observado: Wokwi ___ /s · Pico ___ /s. <!-- TODO Angel -->

## 6. Preguntas de análisis

1. **Cooperativa vs dual-core real.** En Wokwi hay un núcleo y las tareas se turnan: si una tarda, retrasa a todas. En la Pico el sensor tiene un núcleo propio y corre al mismo tiempo que la interfaz.
2. **¿Por qué no `sleep_ms(1000)` en la tarea del sensor?** Durante ese segundo no se mide nada y una ALARM se detectaría hasta 1 s tarde; en un solo núcleo además se congelarían botón, LEDs y serial.
3. **¿Por qué 20 ms el sensor y 1000 ms el serial?** Cada tarea corre al ritmo que necesita: el sensor tiene que ver cambios rápidos; el serial lo lee una persona, y imprimir es lento.
4. **¿Por qué `lock`?** Con dos núcleos la lectura y la escritura ocurren a la vez; sin lock, Core 0 podría leer un `raw` nuevo con un `state` viejo. El lock deja entrar a un solo núcleo a la vez.
5. **Reconocer vs eliminar la alarma.** El ACK solo confirma que el operador la vio (rojo fijo); la condición sigue mientras la señal esté ≥ 75 %. Se elimina cuando la señal baja, y entonces el ACK se borra.
6. **¿Qué demuestra que no se bloquea?** El heartbeat cambia parejo cada 200 ms, el serial imprime cada segundo con `rate=` ≈ 50, y el botón responde al instante, todo al mismo tiempo.

## 7. Problemas encontrados

- **Prevención: globales creadas después de lanzar el hilo** (error que reportó Axel García en su placa). En la Pico los dos núcleos corren sin GIL: si Core 0 crea una variable global nueva mientras Core 1 busca otra, Core 1 puede morir con un `NameError` falso y el sistema se queda en `INIT`. En la primera versión de este código la global `now` se creaba dentro del `while`, después de `start_new_thread`; ahora se crea antes.
<!-- TODO Angel: lo que haya fallado al probar (p. ej. "OSError: core1 in use" al re-correr). -->

## 8. Conclusión

<!-- TODO Angel: conclusión en primera persona. -->

## Evidencias y cómo correrlo

| Evidencia | Archivo |
|---|---|
| Serial Wokwi (estados + ACK + reset) | [`evidence/serial_wokwi.png`](./evidence/serial_wokwi.png) |
| Serial Pico (`samples_core1`, `rate=`) | [`evidence/serial_pico.png`](./evidence/serial_pico.png) |
| Circuito | [`evidence/circuito.png`](./evidence/circuito.png) |

- **Wokwi:** proyecto Pico + MicroPython; pegar `wokwi/diagram.json` y `main_wokwi.py` como `main.py`. Botón con click o tecla `A`.
- **Pico:** `mpremote run main_dualcore_physical.py`. Si al re-correr sale `OSError: core1 in use`, reinicio suave (Ctrl-D) y otra vez.
