# Sesión 08 — Procesamiento multihilo / Dual-Core

**Reto 08 — Sistema multitarea**
_Angel Rugerio Jiménez · 201720 · Lab. de Elementos Programables_

---

## 1. Objetivo

Construir un sistema donde una tarea **monitorea un sensor crítico a alta velocidad** y otras tareas actualizan LEDs, alarma, botón y terminal **sin bloquear el programa**.

Hasta la Sesión 07 el monitor hacía todo en una sola fila y después dormía (`sleep_ms(300)`): mientras dormía no veía nada. Aquí el programa se separa en **tareas con su propio ritmo**:

```
sensor (20 ms) → filtro → % → estado ──▶ datos compartidos ──▶ LEDs + heartbeat (200 ms)
                                                      ▲          serial (1000 ms)
                                    botón ACK (50 ms) ┘
```

El sistema se implementa dos veces:

| Archivo | Dónde corre | Qué demuestra |
|---|---|---|
| `main_wokwi.py` | Wokwi (un núcleo) | **Concurrencia:** tareas que se turnan sin bloquearse, con `ticks_ms()` |
| `main_dualcore_physical.py` | Pico 2 W física (dos núcleos) | **Paralelismo:** el sensor en Core 1 y la interfaz en Core 0, con `_thread` + `lock` |

## 2. Qué es multitarea

**Concurrencia** es organizar varias tareas para que avancen en el mismo intervalo de tiempo, aunque se **intercalen** en un solo procesador. **Paralelismo** es ejecutarlas **en el mismo instante** en núcleos distintos. La versión de Wokwi es concurrente pero no paralela; la versión física es las dos cosas.

### 2.1 Multitarea cooperativa (Wokwi)

Cada tarea guarda **cuándo le toca** (`next_sensor`, `next_ui`…). El `while True` pregunta a todas en cada vuelta y solo ejecuta las que ya llegaron a su momento:

```python
def due(now, target):
    return ticks_diff(now, target) >= 0

while True:
    now = ticks_ms()
    if due(now, next_sensor):
        sensor_task()
        next_sensor = now + sensor_period
    # ... botón, UI y log igual ...
    sleep_ms(2)
```

Las tareas hacen su trabajo y **regresan rápido**: ninguna tiene `sleep` largo, porque en un solo núcleo si una tarea se bloquea, se bloquean todas. El único `sleep` es de 2 ms, para no girar el loop en vacío.

| Tarea | Periodo | Por qué ese ritmo |
|---|---|---|
| Sensor | 20 ms (50 Hz) | Es la crítica: tiene que ver cambios rápidos |
| Botón | 50 ms (20 Hz) | Más rápido que un clic humano, más lento que el rebote |
| UI | 200 ms (5 Hz) | Suficiente para el ojo; es también el ritmo del parpadeo de alarma |
| Log | 1000 ms (1 Hz) | Legible para una persona; imprimir es lento |

### 2.2 Dual-core real (Pico física)

`_thread.start_new_thread(sensor_core, ())` lanza la adquisición en el **Core 1**. El programa principal sigue en el **Core 0** con las tareas de botón, UI y log (mismo planificador de 2.1, sin la tarea del sensor).

Los dos núcleos se comunican por el diccionario `shared`. Como ahora leen y escriben **al mismo tiempo**, todo acceso va protegido con `lock`:

```python
lock.acquire()
shared["raw"] = raw
shared["state"] = state
# ...
lock.release()
```

Decisiones de diseño en esta versión:

- **El cálculo va fuera del lock;** dentro solo se copian resultados. Mientras un núcleo tiene el lock, el otro espera.
- **Core 0 lee todo en un solo `acquire()`** (`read_shared()`): los valores que imprime y con los que decide los LEDs son del mismo instante.
- **En `button_task()`, revisar el estado y escribir el ACK van en el mismo `acquire()`:** si se soltara el lock entre las dos cosas, Core 1 podría salir de ALARM en medio y el ACK quedaría puesto sobre una alarma que ya no existe.
- **Core 1 no imprime ni toca LEDs:** si hiciera trabajo lento dejaría de ser una tarea rápida. Su `sleep_ms(20)` ya no es problema porque solo duerme a su propio núcleo.

## 3. Qué simula Wokwi y qué prueba la Pico física

| Wokwi valida | Pico física valida |
|---|---|
| El algoritmo: periodos, filtro, umbrales, ACK, flanco del botón | Que la adquisición corre **en paralelo** en el segundo núcleo |
| Que ninguna tarea bloquea a las demás | Que el `lock` protege los datos compartidos entre núcleos |
| | Ruido real del ADC y rebote real del botón |

Wokwi simula un solo núcleo de la Pico, así que **no puede probar dual-core**: la versión con `_thread` solo se valida en la placa.

## 4. Circuito

| Elemento | Pin | Función |
|---|---|---|
| Potenciómetro | GP26 / ADC0 | Sensor crítico (`SIG → GP26`, `VCC → 3V3`, `GND → GND`) |
| LED verde | GP13 | NORMAL |
| LED amarillo | GP14 | WARNING |
| LED rojo | GP15 | ALARM (parpadea sin ACK, fijo con ACK) |
| LED azul | GP12 | Heartbeat |
| Botón | GP16 → GND | ACK de alarma (`PULL_UP`: libre = 1, presionado = 0) |

Cada LED con su resistencia (`GPx → R → LED → GND`). [`wokwi/diagram.json`](./wokwi/diagram.json) es la plantilla oficial del curso, sin cambios.

<!-- TODO Angel: si la placa física usa resistencias distintas (en la S07 eran de 1 kΩ), anotarlo aquí. -->

## 5. Umbrales

| Estado | Rango | LED |
|---|---|---|
| NORMAL | 0 % a < 50 % | Verde |
| WARNING | 50 % a < 75 % | Amarillo |
| ALARM | 75 % a 100 % | Rojo |

`classify()` pregunta del umbral más alto al más bajo, igual que en el Reto 07. Los valores 50 / 75 son los de la clase y están como constantes (`WARNING`, `ALARM`) al inicio de ambos archivos.

## 6. Filtro

Promedio móvil sobre las últimas `BUFFER_SIZE = 8` lecturas, la misma ventana deslizante del Reto 07 (`append` + `pop(0)`, dividiendo entre `len(buffer)` mientras se llena). El porcentaje y el estado salen de la lectura **filtrada**.

Lo que cambia es el tiempo: con una lectura cada 20 ms, la ventana cubre

$$T_{ventana} = N \cdot T_s = 8 \cdot 20\ \text{ms} = 160\ \text{ms}$$

contra los 3 s del Reto 07 (10 × 300 ms). Muestrear rápido permite filtrar el ruido sin pagar casi nada de retraso.

## 7. ACK de alarma

| Situación | LED rojo | `ack` |
|---|---|---|
| ALARM sin reconocer | Parpadea | `False` |
| ALARM reconocida (botón) | Fijo | `True` |
| La señal sale de ALARM | Apagado | Vuelve a `False` automáticamente |
| Botón fuera de ALARM | Sin cambio | Sin efecto (mensaje informativo) |

El botón solo cuenta el **cambio** `1 → 0` (flanco de bajada): se compara la lectura actual con `last_button`, así que mantenerlo presionado genera un solo evento. Leerlo cada 50 ms también filtra el rebote, que dura bastante menos.

## 8. Pruebas

<!-- TODO Angel: llenar PASS/FAIL con lo observado en Wokwi y en la placa. -->

| Prueba | Resultado esperado | Wokwi | Físico |
|---|---|---|---|
| Potenciómetro bajo | NORMAL / LED verde | | |
| Potenciómetro medio | WARNING / LED amarillo | | |
| Potenciómetro alto | ALARM / rojo parpadea | | |
| Botón fuera de ALARM | No reconoce alarma | | |
| Botón durante ALARM | ACK=True / rojo fijo | | |
| Salir de ALARM | ACK vuelve a False | | |
| Heartbeat | LED azul cambia sin congelarse | | |
| Serial | Muestra datos cada segundo | | |
| Sensor a 20 ms | ~50 muestras por segundo | | |
| Filtro | Reduce variaciones rápidas | | |
| Pico física | `_thread` mantiene adquisición y UI | — | |

**Muestras por segundo.** Ambos programas imprimen `rate=`, las muestras tomadas desde la línea anterior del log (≈ 1 s).

<!-- TODO Angel: anotar los valores de rate= observados en Wokwi y en la placa. -->

| Versión | `rate=` observado |
|---|---|
| Wokwi (cooperativa) | |
| Pico física (Core 1) | |

En la versión cooperativa se espera un poco menos de 50: `next_sensor = now + sensor_period` cuenta el siguiente periodo desde que la tarea **se ejecutó**, no desde que **debía** ejecutarse. Como el loop revisa cada ~2 ms, cada lectura llega entre 0 y ~2 ms tarde y ese retraso se acumula (periodo real ≈ 21 ms → ≈ 48 muestras/s).

## 9. Preguntas de análisis

**1. ¿Cuál es la diferencia entre multitarea cooperativa en Wokwi y dual-core real?**
En Wokwi hay un solo núcleo: las tareas **se turnan**, y cada una tiene que terminar y devolver el control para que corran las demás. Si una tarda, retrasa a todas. En la Pico física el sensor tiene un núcleo para él solo y corre **al mismo tiempo** que la interfaz; lo que una haga no frena a la otra (salvo mientras esperan el lock).

**2. ¿Por qué no usamos `sleep_ms(1000)` dentro de la tarea crítica del sensor?**
Porque durante ese segundo no se tomaría ninguna lectura: cualquier cambio de la señal más corto que eso pasaría sin detectarse, y la alarma reaccionaría hasta un segundo tarde. En la versión cooperativa sería peor: congelaría también LEDs, botón y terminal, porque todos comparten el mismo núcleo.

**3. ¿Por qué una tarea puede ejecutarse cada 20 ms y el terminal cada 1000 ms?**
Porque cada tarea corre al ritmo que su función necesita. El sensor necesita resolución temporal para ver cambios rápidos; la terminal la lee una persona, y más de una línea por segundo no aporta nada. Además imprimir es lento: hacerlo 50 veces por segundo le quitaría tiempo a la tarea crítica.

**4. ¿Por qué se necesita `lock` cuando dos núcleos comparten datos?**
Porque con dos núcleos la escritura y la lectura ocurren realmente al mismo tiempo. Sin lock, Core 0 podría leer `raw` ya actualizado y `state` todavía viejo (por ejemplo `raw=60000` con `state=NORMAL`), una combinación que nunca existió. El lock garantiza que solo un núcleo esté dentro de la sección que toca `shared`, así que cada lectura ve un conjunto de datos completo.

**5. ¿Qué diferencia hay entre reconocer una alarma y eliminar la condición de alarma?**
Reconocer (ACK) solo confirma que el operador ya vio la alarma: el LED deja de parpadear y queda fijo, pero sigue encendido porque la señal sigue arriba del 75 %. La condición solo desaparece cuando la señal baja, y en ese momento el ACK se borra: si vuelve a subir es una alarma nueva y tiene que volver a llamar la atención.

**6. ¿Qué evidencia demuestra que el sistema no se bloquea?**
Tres cosas que se ven al mismo tiempo: el heartbeat azul cambia a ritmo constante (200 ms), la terminal imprime una línea por segundo, y el contador de muestras sube ~50 por línea. Además, el botón responde de inmediato aun con el sensor en ALARM.

## 10. Evidencias

<!-- TODO Angel: subir las capturas y ajustar nombres. -->

| Evidencia | Archivo |
|---|---|
| Simulación Wokwi | [`wokwi/enlace.md`](./wokwi/enlace.md) |
| Serial en Wokwi (cambios de estado + ACK) | [`evidence/serial_wokwi.png`](./evidence/serial_wokwi.png) |
| Serial en la Pico (`samples_core1`) | [`evidence/serial_pico.png`](./evidence/serial_pico.png) |
| Circuito | [`evidence/circuito.png`](./evidence/circuito.png) |

## 11. Problemas encontrados

<!-- TODO Angel: lo que haya fallado al probar. -->

## 12. Conclusión

<!-- TODO Angel: conclusión en primera persona. -->

---

## Contenido y cómo correrlo

| Archivo / carpeta | Contenido |
|---|---|
| `main_wokwi.py` | Sistema multitarea cooperativo (un núcleo) |
| `main_dualcore_physical.py` | El mismo sistema con el sensor en Core 1 (`_thread` + `lock`) |
| `wokwi/diagram.json` | Circuito de la plantilla del curso |
| `wokwi/enlace.md` | Enlace a la simulación publicada |
| `evidence/` | Capturas del serial y del circuito |

**Simulación:** en wokwi.com, proyecto Raspberry Pi Pico + MicroPython; pegar `wokwi/diagram.json` y `main_wokwi.py` (como `main.py`). Mover el potenciómetro arrastrando la perilla; el botón se presiona con click (o tecla `A`).

**Hardware:**

```bash
mpremote run main_dualcore_physical.py     # correr sin instalar nada
```
