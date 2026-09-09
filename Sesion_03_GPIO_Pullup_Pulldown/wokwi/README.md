# Simulación — Sesión 03

Toda la simulación de esta sesión se corre en **wokwi.com** (el IDE web). Esta carpeta
solo contiene el **circuito**; el código vive en `../micropython/` y `../cpp/`.

```
wokwi/
├── diagram.json                ← circuito para los proyectos de C/C++
└── diagram_micropython.json    ← el mismo circuito + firmware de MicroPython fijado
```

Los dos archivos describen **el mismo circuito**. La única diferencia es el campo
`attrs.env` de la placa, que en la variante de MicroPython fija la versión de firmware
(`micropython-20260406-v1.28.0`) para que la simulación arranque reproducible.

## Por qué online y no en VS Code

La extensión de Wokwi para VS Code sí funciona, pero para este reto no sirve:

- **No simula MicroPython.** Solo carga un binario (`.uf2` / `.hex` / `.bin`) en el chip;
  no monta un sistema de archivos con los `.py` del proyecto. Y MicroPython es el lenguaje
  principal del reto.
- **Obliga a compilar para el chip equivocado.** Wokwi simula un RP2040 (`wokwi-pi-pico`),
  pero la placa física de este proyecto es una **Pico 2 W (RP2350)**. Un `.uf2` no sirve
  para las dos: o compilas para simular, o compilas para la placa.
- Es comercial (pide licencia).

El IDE web resuelve las tres: trae MicroPython, compila el C/C++ en la nube para RP2040 sin
tocar el proyecto local, y es gratis.

## Separación de responsabilidades

| | Dónde corre | Chip | Para qué |
|---|---|---|---|
| **Simulación** | wokwi.com | RP2040 | Validar la lógica y capturar evidencia del comportamiento |
| **Hardware** | Pico 2 W física | RP2350 | Evidencia real: fotos, video, monitor serial |

El código fuente es **el mismo** en los dos lados. Lo que cambia es quién lo compila y para
qué chip. Los `.uf2` de `../cpp/*/build/` son **solo para la placa física**.

## Circuito

Placa: `wokwi-pi-pico`.

| Elemento | Pin | Componente |
|---|---|---|
| Auto rojo | GP15 | LED rojo + 330 Ω |
| Auto amarillo | GP14 | LED amarillo + 330 Ω |
| Auto verde | GP13 | LED verde + 330 Ω |
| Peatón rojo | GP12 | LED rojo + 330 Ω |
| Peatón verde | GP11 | LED verde + 330 Ω |
| Botón | GP16 | Pushbutton a GND (pull-up interno) |

Los LEDs van `GPIO → 330 Ω → ánodo · cátodo → GND`, cada uno a un pin de GND distinto.
El botón va `GP16 — botón — GND`, sin resistencia externa: el pull-up es el interno del
chip, activado por software (`Pin.PULL_UP` / `gpio_pull_up()`).

> Verificado contra el `connections.json` del profesor: el pinout coincide pin por pin.
> Única diferencia cosmética: él coloca la resistencia del lado del cátodo y aquí va del
> lado del ánodo. Eléctricamente es idéntico (es una serie).

---

## Procedimiento — MicroPython

1. Abrir <https://wokwi.com/projects/new/micropython-pi-pico>.
2. Pestaña `diagram.json` → pegar el contenido de
   [`diagram_micropython.json`](./diagram_micropython.json).
3. Pestaña `main.py` → pegar el script a probar:

   | Prueba | Archivo |
   |---|---|
   | DO 01 — lectura del botón | [`../micropython/01_button_read.py`](../micropython/01_button_read.py) |
   | DO 02 — debounce | [`../micropython/02_button_debounce.py`](../micropython/02_button_debounce.py) |
   | CHALLENGE — semáforo | [`../micropython/03_semaforo_peatonal.py`](../micropython/03_semaforo_peatonal.py) |

4. ▶ Play. El monitor serial aparece abajo.
5. Clic en el botón del diagrama para dispararlo.
6. *Save* para obtener un link permanente, y anotarlo en la tabla de abajo.

## Procedimiento — C/C++

1. Abrir <https://wokwi.com/projects/new/pi-pico>. Es una plantilla del **Pico SDK** que
   compila en la nube; no hace falta toolchain local.
2. Pestaña `diagram.json` → pegar [`diagram.json`](./diagram.json).
3. Pestaña `main.c` → pegar el contenido de
   [`../cpp/button_read/button_read.c`](../cpp/button_read/button_read.c) o
   [`../cpp/traffic_light/traffic_light.c`](../cpp/traffic_light/traffic_light.c).
4. ▶ Play (compila y luego simula).

> El `CMakeLists.txt` del IDE web es suyo, no el del repo. Los proyectos de `../cpp/` no se
> suben ahí: se pega el `.c` y ya. Esos proyectos existen para compilar hacia la Pico 2 W.

---

## Qué capturar para `../evidence/`

| Escenario | Archivo de evidencia |
|---|---|
| `01_button_read.py` — transición `1 → 0` en el serial | `wokwi_button.png` |
| `02_button_debounce.py` — click largo = un solo evento | `wokwi_debounce.png` |
| `03_semaforo_peatonal.py` — estado S2 (auto rojo + peatón verde) | `wokwi_semaforo.png` |
| `traffic_light.c` — misma secuencia en C | `wokwi_cpp.png` |

## Links de las simulaciones publicadas

| Escenario | Link |
|---|---|
| MicroPython — lectura del botón | _(pegar link)_ |
| MicroPython — debounce | _(pegar link)_ |
| MicroPython — semáforo | _(pegar link)_ |
| C/C++ — semáforo | _(pegar link)_ |
