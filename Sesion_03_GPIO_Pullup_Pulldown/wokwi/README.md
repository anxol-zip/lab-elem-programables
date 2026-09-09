# Simulaciones de Wokwi — Sesión 03

Esta carpeta **no contiene código ni firmware**: solo describe el circuito y apunta a los
binarios que produce `cpp/`. El mismo `.uf2` que se simula aquí es el que se copia a la
Pico física, así que la prueba en Wokwi y la prueba en hardware corren **exactamente el
mismo binario**.

```
wokwi/
├── diagram.json                    ← circuito canónico (una sola copia)
├── cpp/
│   ├── button_read/
│   │   ├── wokwi.toml              → ../../../cpp/button_read/build/button_read.uf2
│   │   └── diagram.json            → symlink a ../../diagram.json
│   └── traffic_light/
│       ├── wokwi.toml              → ../../../cpp/traffic_light/build/traffic_light.uf2
│       └── diagram.json            → symlink a ../../diagram.json
└── micropython/
    └── diagram.json                ← igual, pero con attrs.env (para el IDE web)
```

El circuito es **el mismo en los cuatro escenarios** (los dos lenguajes × los dos
programas). `button_read` simplemente no usa los LEDs. Por eso hay un único
`diagram.json` real y los demás son symlinks: la extensión exige un `diagram.json` junto a
cada `wokwi.toml`, pero no tiene por qué ser un archivo distinto.

## Circuito simulado

Placa: `wokwi-pi-pico` (RP2040).

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
RP2040, activado por software (`Pin.PULL_UP` / `gpio_pull_up()`).

> Verificado contra el `connections.json` del profesor: el pinout coincide pin por pin.
> Única diferencia cosmética: él coloca la resistencia del lado del cátodo y aquí va del
> lado del ánodo. Eléctricamente es idéntico (es una serie).

---

## C/C++ — extensión de Wokwi en VS Code

### Cómo resuelve las rutas la extensión

Esto es lo que hace que el esquema de arriba funcione (verificado en el código de
`wokwi.wokwi-vscode` v3.7.0):

1. La **carpeta raíz** de una simulación es la que contiene el `wokwi.toml`, **no** la
   carpeta abierta en VS Code.
2. `firmware` y `elf` se resuelven con `Uri.joinPath(raíz, ruta)`, que normaliza `..`.
   Por eso `'../../../cpp/button_read/build/button_read.uf2'` es válido y no hace falta
   copiar nada.
3. El `diagram.json` se busca **junto al `wokwi.toml`**. De ahí los symlinks.
4. `Wokwi: Select Config File` hace `findFiles("**/wokwi.toml")` en todo el workspace y
   **recuerda la elección** en el estado del workspace. Es el mecanismo para tener varios
   escenarios y cambiar entre ellos.

### Procedimiento

0. **Requisito:** la extensión es comercial. Pide licencia (hay periodo de prueba gratis)
   con `Wokwi: Request a New License` la primera vez.

1. Abrir `Sesion_03.code-workspace` en VS Code.

2. Compilar el firmware que se va a simular:

   ```bash
   cd cpp
   ./build.sh              # los dos proyectos
   ```

3. `F1` → **`Wokwi: Select Config File`** → elegir el escenario:

   | Escenario | Config a elegir |
   |---|---|
   | DO 01 — lectura del botón | `wokwi/cpp/button_read/wokwi.toml` |
   | CHALLENGE — semáforo | `wokwi/cpp/traffic_light/wokwi.toml` |

4. `F1` → **`Wokwi: Start Simulator`**.

5. La salida de `printf()` aparece en la terminal serial que abre la extensión. Llega por
   **UART0**, que es lo que simula Wokwi; el `CMakeLists.txt` ya trae
   `pico_enable_stdio_uart(... 1)`, así que no hay que recompilar nada distinto para la
   placa física.

6. Presionar el botón en el diagrama con el mouse para disparar la secuencia.

Para cambiar de escenario: repetir el paso 3. La selección queda guardada, así que las
siguientes veces basta con `Wokwi: Start Simulator`.

> **Al recompilar:** la extensión vigila el `.uf2` para recargarlo solo, pero el patrón de
> vigilancia se construye con la ruta relativa tal cual, y VS Code no vigila de forma
> confiable rutas que salen de la carpeta con `..`. Si recompilas y la simulación sigue
> mostrando el binario viejo, reinicia el simulador a mano (`Wokwi: Start Simulator` otra
> vez). No es un error de configuración.

> **Symlinks:** si clonas este repo en Windows sin symlinks habilitados, los
> `diagram.json` de `cpp/*/` se materializan como archivos de texto con una ruta adentro y
> la extensión dirá *"diagram.json is not valid JSON"*. Solución en Linux/macOS:
> `cp wokwi/diagram.json wokwi/cpp/button_read/diagram.json` (y lo mismo para
> `traffic_light`).

### Depuración con GDB (opcional)

El `elf` ya está declarado en los `wokwi.toml`. Para usar el debugger de VS Code hay que
agregar `gdbServerPort = 3333` a la sección `[wokwi]` y arrancar con
`Wokwi: Start Simulator and Wait for Debugger`.

---

## MicroPython — IDE web de Wokwi

**La extensión de VS Code no simula MicroPython.** No es una limitación de este proyecto:
la extensión solo carga un binario de firmware (`.uf2` / `.hex` / `.bin`) en el chip y no
tiene forma de montar un sistema de archivos con los `.py` del proyecto. (Revisado el
bundle de la v3.7.0: no hay ninguna referencia a MicroPython ni a LittleFS.)

Así que los `.py` se prueban en **wokwi.com**, que sí trae el firmware de MicroPython y un
editor de `main.py`:

1. Entrar a <https://wokwi.com/projects/new/micropython-pi-pico>.
2. Pestaña `diagram.json` → pegar el contenido de
   [`micropython/diagram.json`](./micropython/diagram.json). Ese archivo ya trae fijada la
   versión de firmware en `attrs.env`, así que la simulación arranca reproducible.
3. Pestaña `main.py` → pegar el script a probar:
   - `../micropython/01_button_read.py` (DO 01)
   - `../micropython/02_button_debounce.py` (DO 02)
   - `../micropython/03_semaforo_peatonal.py` (CHALLENGE)
4. Play ▶ y ver el monitor serial abajo.

Es el mismo archivo que después se copia como `main.py` a la Pico física, así que la
prueba sigue siendo sobre el código real del repo — la diferencia con C/C++ es que aquí
hay que pegarlo a mano en vez de referenciarlo.

> **Alternativa** (no recomendada para la entrega): en VS Code se puede poner un `.uf2` de
> MicroPython como `firmware` en un `wokwi.toml`. Arranca, pero cae en el REPL vacío
> porque no hay `main.py` que cargar; habría que pegar el código en el REPL por la
> terminal serial en cada corrida. Para evidencia del reto, el IDE web es más limpio.

---

## Qué capturar para `evidence/`

| Escenario | Dónde se corre | Captura |
|---|---|---|
| `01_button_read.py` | wokwi.com | `wokwi_button.png` |
| `02_button_debounce.py` | wokwi.com | `wokwi_debounce.png` |
| `03_semaforo_peatonal.py` | wokwi.com | `wokwi_semaforo.png` |
| `traffic_light.c` | VS Code | `wokwi_cpp.png` |

## Enlaces a las simulaciones publicadas

- MicroPython — semáforo peatonal: _(pegar aquí el link de wokwi.com)_
- C/C++ — semáforo peatonal: _(se corre local en VS Code, no genera link)_
