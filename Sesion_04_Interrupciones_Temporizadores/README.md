# Sesión 04 — Interrupciones, temporizadores y medición de tiempo de reacción

**Reto 04 — Juego de reflejos**
_Angel Rugerio Jiménez · 201720 · Lab. de Elementos Programables_

---

## 1. Objetivo

Construir un **juego de reflejos** sobre la Raspberry Pi Pico: un **temporizador** enciende un LED en un instante impredecible y una **interrupción** captura el momento exacto en que se presiona el botón. La diferencia entre los dos instantes es el **tiempo de reacción en milisegundos**.

La sesión anterior reaccionaba al mundo físico **preguntando** (`while` + `gpio_get`). Aquí el programa deja de preguntar: el hardware avisa. Eso obliga a separar tres responsabilidades:

| Quién | Qué hace | Qué NO hace |
|---|---|---|
| **Timer** | Genera la señal y arranca el cronómetro | No sabe nada del jugador |
| **ISR** | Captura el instante del flanco y levanta una bandera | No imprime ni decide |
| **Main loop** | Imprime, acumula estadísticas y agenda la ronda siguiente | No mide el tiempo |

> [!IMPORTANT]
> La ISR nunca llama a `print()` / `printf()`. Una interrupción se mide en microsegundos; una impresión por USB, en milisegundos: si la ISR imprimiera, el acto de medir alteraría la medición.

## 2. Circuito

Un solo montaje para toda la práctica — los tres programas de MicroPython y el de C usan el mismo hardware:

| Elemento | Pin | Conexión | Color |
|---|---|---|---|
| LED señal | GP15 | `GP15 → 330 Ω → LED → GND` | verde — *presiona ahora* |
| LED espera | GP14 | `GP14 → 330 Ω → LED → GND` | rojo — *todavía no* |
| Botón | GP16 | `GP16 → botón → GND` | — |

**Pull-up interno por código** (`Pin.PULL_UP` / `gpio_pull_up()`), GND común, sin resistencias externas en el botón. La interrupción dispara en **flanco de bajada** (`IRQ_FALLING` / `GPIO_IRQ_EDGE_FALL`): la transición `1 → 0` que produce el botón al cerrar contra GND.

En [`wokwi/`](./wokwi/) hay dos variantes del **mismo circuito**: `diagram.json` (C/C++, RP2040) y `diagram_micropython.json`, que solo cambia el tipo de placa y fija el firmware para que la simulación arranque.

| Simulación publicada | Link |
|---|---|
| MicroPython — contador con IRQ | _pendiente_ |
| MicroPython — señal por timer | _pendiente_ |
| MicroPython — juego de reflejos | _pendiente_ |
| C/C++ — juego de reflejos | _pendiente_ |

> [!WARNING]
> Las entradas de la Pico son de lógica **3.3 V**. Nunca conectar 5 V directo a un GPIO.

## 3. Qué es una interrupción

Cuando ocurre un evento en un pin, el procesador **suspende** lo que ejecutaba, salta a una función registrada de antemano (la **ISR**), la ejecuta y regresa a donde se quedó.

| | Polling (`while gpio_get(...)`) | Interrupción |
|---|---|---|
| Quién detecta | El programa, preguntando | El hardware, avisando |
| Latencia | Hasta un ciclo completo del bucle | Microsegundos, acotada |
| Si el bucle está ocupado | **Se pierde el evento** | Se atiende igual |
| Costo cuando no pasa nada | CPU quemada preguntando | Cero |

Aquí no es un lujo, es el **único modo honesto de medir**: con polling el número reportado incluiría el retraso del propio bucle y dejaría de ser el tiempo de reacción del jugador para volverse una propiedad del programa.

```python
boton_jugador.irq(trigger=Pin.IRQ_FALLING, handler=detectar_pulsacion)   # MicroPython
```
```c
gpio_set_irq_enabled_with_callback(BUTTON_PIN, GPIO_IRQ_EDGE_FALL, true, &button_isr);  // C
```

**La ISR es corta:** lee el reloj, compara contra el estado del juego y levanta una bandera. Imprimir, acumular la tabla y agendar la ronda es trabajo del `while`, que puede tardar lo que quiera sin afectar la medida. Las variables compartidas con el `main` van marcadas **`volatile`** en C; sin eso el compilador puede cachear `result_ready` en un registro —nadie la escribe dentro del bucle— y el juego se colgaría en la primera ronda. En MicroPython el problema no existe, pero hay que declarar `global` en cada handler.

## 4. Qué es un temporizador

Un contador del hardware que corre **en paralelo** al programa y dispara un callback al vencer. No es un `sleep`: `sleep_ms(5000)` detiene el programa; un timer de 5000 ms lo deja trabajando y avisa al terminar. Esa es la demostración de [`timer_signal.py`](./micropython/timer_signal.py): durante los 10 s de espera la consola sigue imprimiendo `MAIN TRABAJANDO: n` y solo entonces aparece `TIMER DISPARADO`.

| Acción | MicroPython | C / Pico SDK |
|---|---|---|
| Armar un disparo único | `Timer(-1).init(mode=Timer.ONE_SHOT, period=ms, callback=cb)` | `add_alarm_in_ms(ms, cb, NULL, false)` |
| Cancelarlo | `temporizador.deinit()` | `cancel_alarm(signal_alarm)` |
| Reloj en ms | `ticks_ms()` / `ticks_diff()` | `to_ms_since_boot(get_absolute_time())` |

> [!NOTE]
> `ticks_ms()` **desborda**, por eso las restas se hacen con `ticks_diff()`, que maneja el *wraparound*.

El retardo es **aleatorio entre 1 y 10 s**, así que el jugador no puede anticiparse contando; y el instante en que el callback enciende el LED es el mismo que se guarda como `t0`: el cronómetro arranca dentro del callback, ni antes ni después.

## 5. El juego

`S0 ESPERA → S1 SEÑAL → S2 RESPUESTA → S3 RESULTADO → S0`

| Estado | Qué pasa | LED señal | LED espera | El botón… |
|---|---|---|---|---|
| **S0 ESPERA** | Timer armado con retardo aleatorio | apagado | encendido | …es **salida en falso** |
| **S1 SEÑAL** | El callback encendió el LED y guardó `t0` | encendido | apagado | …**mide** el tiempo |
| **S2 RESPUESTA** | La ISR calculó `t1 - t0` y levantó la bandera | apagado | apagado | …se ignora |
| **S3 RESULTADO** | El main imprime y agenda la ronda siguiente | apagado | apagado | …se ignora |

S2 y S3 son un solo estado en el código (`ESTADO_TERMINADO` / `STATE_DONE`); lo que los distingue no es el hardware sino quién tiene el turno. Que la ISR **ignore** el botón ahí es lo que impide que un botón sostenido encadene rondas.

**Nivel 2 — una defensa por cada error del usuario:**

1. **Salida en falso.** Si el botón llega en `S0`, la ISR **cancela la alarma** agendada y cierra la ronda. Cancelarla importa: si no, el LED se encendería después, fuera de contexto.
2. **Debounce de 80 ms dentro de la ISR.** Sin filtro, el primer rebote mediría el tiempo y el segundo lo tomaría como salida en falso de la ronda siguiente.
3. **Botón sostenido.** Tras imprimir el resultado, el main **espera a que el pin vuelva a `1`** antes de la ronda siguiente.

**Nivel 3 — serie de 5 intentos.** La serie se cierra a los 5 intentos **válidos**; las salidas en falso **no consumen intento**, se cuentan aparte y la ronda se repite, para que el promedio mida reflejos y no anticipación. Al completar la serie se imprime la tabla con mejor, peor, promedio y salidas falsas.

## 6. Pruebas

Cada prueba se corre en la simulación (wokwi.com, RP2040) y en la placa física (Pico 2 W, RP2350). El código fuente es el mismo, así que una discrepancia entre columnas apunta al hardware, no a la lógica.

### DO 01 — Botón (`button_irq_counter.py`)

| Prueba | Esperado | Wokwi | Física |
|---|---|---|---|
| Botón libre | Lectura `1` | ⬜ | ⬜ |
| Botón presionado | `1 → 0`, dispara `IRQ_FALLING` | ⬜ | ⬜ |
| 5 clics seguidos | `1, 2, 3, 4, 5` sin saltos | ⬜ | ⬜ |
| Clic sostenido | Un solo evento (debounce) | ⬜ | ⬜ |

### DO 02 — Temporizador (`timer_signal.py`)

| Prueba | Esperado | Wokwi | Física |
|---|---|---|---|
| Durante los 10 s de espera | El main sigue imprimiendo `MAIN TRABAJANDO: n` | ⬜ | ⬜ |
| Al cumplirse el periodo | `TIMER DISPARADO`, GP15 = 1 y GP14 = 0 | ⬜ | ⬜ |
| Después del disparo | No se repite (es `ONE_SHOT`) | ⬜ | ⬜ |

### RE 04 — Juego (`reaction_game.py` y `reaction_game.c`)

| Prueba | Esperado | uPy | C | Física |
|---|---|---|---|---|
| Arranque | LED espera encendido, señal apagada | ⬜ | ⬜ | ⬜ |
| Presionar antes de la señal | Marca salida en falso y la ronda no cuenta | ⬜ | ⬜ | ⬜ |
| Esperar la señal y presionar | Imprime el tiempo en ms | ⬜ | ⬜ | ⬜ |
| Mantener el botón presionado | No repite la ronda inmediatamente | ⬜ | ⬜ | ⬜ |
| Reiniciar ronda | Nuevo tiempo de espera aleatorio | ⬜ | ⬜ | ⬜ |
| Completar 5 intentos | Imprime la tabla con promedio y mejor tiempo | ⬜ | ⬜ | ⬜ |

Capturas del serial en [`wokwi/screenshots/`](./wokwi/screenshots/) (simulación) y en [`evidence/`](./evidence/) (placa física y fotos del montaje).

> [!NOTE]
> La simulación valida la **lógica**; el hardware valida la **implementación**. Desde Wokwi no se puede afirmar nada sobre latencia real, rebote físico ni tiempo humano exacto.

## 7. Resultados en ms

> [!NOTE]
> Pendiente de llenar con la corrida real. Los valores se leen directo de la consola: el programa ya imprime el resumen calculado.

| Intento | MicroPython (Wokwi) | C/C++ (Wokwi) | Física (Pico 2 W) |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |
| **Mejor** | | | |
| **Peor** | | | |
| **Promedio** | | | |
| **Salidas falsas** | | | |

**Análisis** _(llenar al tener las tres series)_ — tres cosas que conviene comparar:

- **Dispersión dentro de una serie.** Un rango amplio entre el mejor y el peor no es ruido del sistema: es el jugador. La medición del micro es estable al milisegundo; la atención humana no.
- **MicroPython vs C.** Si el promedio de C sale más bajo, hay que preguntarse cuánto es el intérprete y cuánto es haber jugado la segunda serie ya entrenado: el orden de las pruebas contamina el resultado.
- **Simulación vs hardware.** En Wokwi el botón es un click de mouse y el LED es un pixel: se mide la reacción a la pantalla, no al circuito.

## 8. Problemas encontrados

> [!NOTE]
> Completar con lo que salga al correr las pruebas. Lo de abajo es lo que ya se resolvió al armar el proyecto.

- **El proyecto de C no imprimía nada.** La plantilla de VS Code venía con `pico_enable_stdio_uart(... 0)` **y** `pico_enable_stdio_usb(... 0)`: las dos salidas apagadas. Compilaba perfecto y el monitor serial se quedaba en blanco. Se activó USB, que es por donde escuchan tanto la placa como Wokwi.
- **La plantilla apuntaba a un archivo inexistente** (`add_executable(cpp cpp.cpp)`); se renombró el target a `reaction_game`.
- **Carrera al iniciar la ronda.** El estado se abría como `ESPERANDO` *antes* de armar el temporizador, con tres `print()` de por medio. Un click en esa ventana hacía que la ISR cancelara la alarma de la ronda **anterior** y la nueva quedaba corriendo fuera de contexto. Ahora el estado se abre al final, con la alarma ya armada.
- **Señal y espera estaban invertidos:** `reaction_game.py` usaba GP14 como señal, al revés de `timer_signal.py` y del enunciado. Con dos LEDs el juego "funciona" igual y el error no se ve, pero el circuito documentado y el código decían cosas distintas.
- **Un `.uf2` no sirve para las dos cosas.** Wokwi simula un RP2040 y la placa es una Pico 2 W (RP2350). El binario de `build/` está compilado para `pico2_w` y **no arranca** en la simulación; Wokwi compila el suyo en la nube desde el mismo `.c`.

## 9. Conclusión

Lo que cambia en esta sesión no es la dificultad del código, sino **quién manda**: hasta la Sesión 03 el programa preguntaba y el mundo contestaba; aquí el mundo avisa y el programa tiene que estar listo para ser interrumpido en cualquier punto.

Eso trae un problema que antes no existía: **dos flujos escriben las mismas variables**. De ahí salen `volatile` en C, `global` en MicroPython y la decisión de que la ISR solo levante banderas. Y la máquina de estados dejó de ser una secuencia para volverse un **filtro**: lo que hace que el juego no se rompa no es lo que pasa cuando el jugador hace lo correcto, sino que hay estados en los que el botón **no significa nada**.

---

## Contenido y cómo correrlo

| Archivo / carpeta | Contenido |
|---|---|
| `micropython/button_irq_counter.py` | DO 01 — botón con IRQ, debounce y contador |
| `micropython/timer_signal.py` | DO 02 — `Timer.ONE_SHOT` sin bloquear el main loop |
| `micropython/reaction_game.py` | RE 04 — juego completo, niveles 1, 2 y 3 |
| `cpp/reaction_game.c` + `CMakeLists.txt` | Proyecto Pico SDK: la prueba equivalente en C |
| `wokwi/` | Circuito y capturas de la simulación |
| `evidence/` | Evidencia del hardware: serial y fotos de la placa |

Hay **dos entornos** y no se mezclan: el código fuente es el mismo, pero Wokwi compila para RP2040 en la nube y la placa física es RP2350.

**Simulación:** se pega el circuito de `wokwi/` y el script (o el `.c`) en wokwi.com.

**Hardware — MicroPython:**

```bash
mpremote run micropython/reaction_game.py            # correr sin instalar nada
mpremote cp micropython/reaction_game.py :main.py    # dejarlo autónomo
```

**Hardware — C/C++:** desde VS Code con la extensión *Raspberry Pi Pico* (es la que pone el toolchain de `~/.pico-sdk/` en el PATH): abrir `cpp/` como carpeta → *Compile* → el `.uf2` queda en `cpp/build/reaction_game.uf2` → conectar la Pico en **BOOTSEL** y copiarlo ahí. Monitor serial con `screen /dev/ttyACM0 115200` (salir con `Ctrl-A`, `K`, `y`; requiere estar en el grupo `dialout`). Sin VS Code:

```bash
export PICO_SDK_PATH=~/.pico-sdk/sdk/2.3.1
export PATH=~/.pico-sdk/ninja/v1.13.2:~/.pico-sdk/toolchain/15_2_Rel1/bin:$PATH
cmake -S cpp -B cpp/build -G Ninja -DCMAKE_BUILD_TYPE=Debug && ninja -C cpp/build
```
