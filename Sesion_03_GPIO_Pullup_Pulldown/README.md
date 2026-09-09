# Sesión 03 — GPIO, pull-up/pull-down y debounce

**Reto 03 — Semáforo peatonal interactivo**
_Angel Rugerio Jiménez · 201720 · Lab. de Elementos Programables_

---

## 1. Objetivo

Construir un semáforo peatonal interactivo sobre la Raspberry Pi Pico donde un **botón**
(petición del peatón) dispara una secuencia de estados, cumpliendo siempre la condición de
seguridad de que **autos y peatones nunca tienen verde al mismo tiempo**.

El reto cubre los tres bloques de la sesión:

- **Entrada** — leer un botón con pull-up interno (`¿qué ocurre?`)
- **Decisión** — debounce + máquina de estados (`¿qué hago?`)
- **Salida** — cinco LEDs que representan los dos semáforos (`¿cómo respondo?`)

## 2. Circuito

Armado **por etapas**, no de golpe:

- **Etapa A — botón:** `GP16 — BOTÓN — GND`, sin resistencia externa (pull-up interno).
- **Etapa B — LEDs:** `GPIO → 330 Ω → LED → GND`, uno por cada luz.

| Elemento | Pin | Componente |
|---|---|---|
| Auto rojo | GP15 | LED rojo + 330 Ω |
| Auto amarillo | GP14 | LED amarillo + 330 Ω |
| Auto verde | GP13 | LED verde + 330 Ω |
| Peatón rojo | GP12 | LED rojo + 330 Ω |
| Peatón verde | GP11 | LED verde + 330 Ω |
| Botón | GP16 | Pushbutton a GND |

El diagrama completo está en [`wokwi/diagram.json`](./wokwi/diagram.json) y es **el mismo
para los cuatro escenarios** (los dos lenguajes × los dos programas): el hardware no cambia
entre lenguajes, y `button_read` simplemente no usa los LEDs.

> [!WARNING]
> Las entradas de la Pico son de lógica **3.3 V**. Nunca conectar 5 V directo a un GPIO.

## 3. Funcionamiento

El botón deja de ser "un número" y se convierte en una **petición**. La lógica es una
máquina de estados de cuatro estados:

| Estado | Autos | Peatón | Duración |
|---|---|---|---|
| **S0 REPOSO** | VERDE | ROJO | hasta que alguien pulse |
| **S1 TRANSICIÓN** | AMARILLO | ROJO | 1500 ms |
| **S2 CRUCE** | ROJO | VERDE | 4000 ms |
| **S3 FIN** | ROJO | VERDE parpadeando | 4 × 300 ms |

Flujo: `REPOSO → BOTÓN → TRANSICIÓN → CRUCE → FIN → REPOSO`

### Invariante de seguridad

> **Auto verde y peatón verde NUNCA pueden estar activos al mismo tiempo.**

En este proyecto la invariante no se dejó como comentario: está **implementada**.
`set_lights()` revisa cada combinación antes de aplicarla y, si detectara
`car_green && ped_green`, bloquea el cambio, imprime la alerta por serial y cae al estado
seguro (todo rojo). Además, al terminar S3 el peatón vuelve a rojo y se espera
`RECOVERY_MS` **antes** de devolver el verde a los autos, para que los dos verdes no se
traslapen ni por un instante.

### Abstracción

El código no piensa en `0,0,1,1,0` sino en acciones del sistema: `cars_go()`,
`cars_prepare_to_stop()`, `pedestrians_go()`, `pedestrians_hurry()`. Eso hace la secuencia
legible y reduce las probabilidades de escribir una combinación peligrosa por error.

### Tiempos ajustables

Todos los tiempos son constantes al inicio del archivo (`TRANSITION_MS`, `CROSSING_MS`,
`BLINK_TIMES`, `BLINK_MS`, `RECOVERY_MS`). Se pueden modificar sin tocar la lógica y sin
romper la seguridad, porque la invariante depende del **orden de los estados**, no de su
duración.

## 4. Pull-up / Pull-down

Una entrada digital necesita una **referencia** cuando nadie la usa. Si GP16 no está
conectado ni a 0 V ni a 3.3 V, el pin queda **flotante**: no es que "cambie solo", es que
**su valor no está garantizado**.

```text
      PULL-UP                    PULL-DOWN
       3.3 V                       3.3 V
         |                           |
        [R]                         BTN
         |                           |
         ├── GP16                    ├── GP16
         |                           |
        BTN                         [R]
         |                           |
        GND                         GND
```

| Configuración | Botón libre | Botón presionado |
|---|---|---|
| **Pull-up** | `1` | `0` |
| **Pull-down** | `0` | `1` |

En esta sesión se usa **pull-up interno**: `GP16 — botón — GND`. Por eso **presionado se
lee como `0`**: al cerrar el botón, el pin se conecta directamente a GND y esa conexión le
gana al resistor interno de pull-up.

### El rebote (bounce)

Un botón mecánico no cambia de estado limpiamente: los contactos rebotan unos
milisegundos y el pin entrega una ráfaga de `1/0`. Físicamente fue **una** presión, pero el
programa podría contar varias. La solución usada es debounce por software: detectar el
flanco de bajada, esperar 30 ms y **volver a leer**; si sigue en `0`, el click es real.
Después se hace **wait for release** para que una presión larga no encadene secuencias.
Regla práctica: **1 presión = 1 petición**.

### Mismo concepto, dos lenguajes

| Acción | MicroPython | C/C++ (Pico SDK) |
|---|---|---|
| Entrada con pull-up | `Pin(16, Pin.IN, Pin.PULL_UP)` | `gpio_set_dir(16, GPIO_IN); gpio_pull_up(16);` |
| Leer botón | `button.value()` | `gpio_get(16)` |
| Salida | `Pin(15, Pin.OUT)` | `gpio_set_dir(15, GPIO_OUT)` |
| Escribir LED | `led.value(1)` | `gpio_put(15, 1)` |

## 5. Pruebas realizadas

> [!NOTE]
> Marcar PASS/FAIL después de ejecutar cada prueba y guardar la captura correspondiente en
> [`evidence/`](./evidence/). Los resultados aún no se llenan porque falta correr la
> simulación.

### DO 01 — Validación del botón (`01_button_read.py`)

| Estado físico | Lectura esperada (pull-up) | Resultado |
|---|---|---|
| Botón libre | `1` | ⬜ |
| Botón presionado | `0` | ⬜ |

### DO 02 — Validación del debounce (`02_button_debounce.py`)

| Prueba | Resultado esperado | Resultado |
|---|---|---|
| Click corto | 1 evento | ⬜ |
| Click largo (2 s) | 1 evento | ⬜ |
| Clicks repetidos rápidos | Sistema estable, sin eventos fantasma | ⬜ |

### CHALLENGE — Validación del semáforo (`03_semaforo_peatonal.py`)

| Prueba | Esperado | Resultado |
|---|---|---|
| Encender el sistema | Autos verde / peatón rojo (S0) | ⬜ |
| Pulsar una vez | Ejecuta una secuencia completa S1→S2→S3→S0 | ⬜ |
| Mantener el botón presionado | No repite la secuencia inmediatamente | ⬜ |
| Pulsar varias veces seguidas | Sistema estable | ⬜ |
| Durante el cruce | Nunca auto verde + peatón verde | ⬜ |
| Cambiar `CROSSING_MS` a 6000 | Cruce más largo, secuencia sigue siendo segura | ⬜ |

### Transferencia a C/C++

| Prueba | Esperado | Resultado |
|---|---|---|
| `button_read.c` | Mismo `1 / 0` que la versión MicroPython | ⬜ |
| `traffic_light.c` | Misma secuencia de estados y misma invariante | ⬜ |

## 6. Problemas encontrados

> [!NOTE]
> Llenar esta sección con lo que realmente pase al correr las pruebas. Los puntos de abajo
> son los que ya se resolvieron al armar el proyecto.

- **Lectura invertida.** Con pull-up, `presionado = 0`. La primera intuición es escribir
  `if button.value() == 1`, que resulta en un semáforo que se dispara al soltar en lugar de
  al presionar.
- **Board de compilación.** El proyecto de C/C++ apunta a `PICO_BOARD pico` (RP2040) porque
  es el chip que simula Wokwi. Para la Pico 2 W física hay que cambiarlo a `pico2_w`.
- **Serial en C/C++.** `stdio_init_all()` necesita un margen de ~2 s antes del primer
  `printf`, o los primeros mensajes se pierden porque el monitor todavía no se conectó.
- **VS Code no compilaba nada (el problema principal).** La causa fue el
  `.vscode/settings.json` de la **carpeta de la sesión**, que contenía:

  ```json
  { "cmake.sourceDirectory": ".../Sesion_03_GPIO_Pullup_Pulldown/cpp/button_read" }
  ```

  Con eso, CMake Tools leía el `CMakeLists.txt` de `cpp/button_read/` pero configuraba el
  build en `Sesion_03_GPIO_Pullup_Pulldown/build/`, usando el **cmake del sistema**
  (`/usr/bin/cmake`) en lugar del cmake del SDK, y sin las variables `PICO_SDK_PATH` /
  `PICO_TOOLCHAIN_PATH` que solo se definen en los `settings.json` de cada proyecto.
  El resultado era una carpeta `build/` basura en la raíz de la sesión, con el CMake
  file-API respondiendo `"no buildsystem generated"` a cada consulta de la extensión.

  **Solución:** borrar esa `build/` de la raíz y quitar `cmake.sourceDirectory` del
  `settings.json` de la sesión. La carpeta de la sesión **no es** un proyecto de CMake;
  cada proyecto de C vive en su propia carpeta con su `CMakeLists.txt`, su
  `pico_sdk_import.cmake` y su `.vscode/`. Hay que abrir esas carpetas (o el
  `Sesion_03.code-workspace`), no la de la sesión.

- **`#include "pico/stdlib.h"` marcado en rojo.** Consecuencia del punto anterior, y no
  un error de compilación sino de **IntelliSense**. El `c_cpp_properties.json` que genera
  la extensión de Pico apunta a `${workspaceFolder}/build/compile_commands.json` y a
  `${workspaceFolder}/build/generated/pico_base/pico/config_autogen.h`, que solo existen
  **después** de configurar CMake al menos una vez, y `${workspaceFolder}` es la carpeta
  abierta en VS Code. Si se abre `Sesion_03_GPIO_Pullup_Pulldown/`, esas rutas no
  resuelven. Se resolvió compilando una vez y abriendo cada proyecto por separado.

- **Toolchain fuera del PATH.** `arm-none-eabi-gcc`, `ninja` y el `cmake` del SDK viven en
  `~/.pico-sdk/` y solo los inyecta la extensión dentro de VS Code. Desde una terminal
  normal hay que exportarlos a mano; por eso se agregó `cpp/build.sh`, que no depende de
  VS Code en absoluto.

## 7. Conclusión

La diferencia entre la Sesión 02 y esta es que el programa dejó de ser una secuencia fija y
ahora **reacciona al mundo físico**. Lo que más costó no fue el código, sino aceptar dos
cosas que no son obvias: que una entrada sin referencia no tiene un valor "aleatorio" sino
un valor **no garantizado**, y que un botón mecánico no entrega un flanco limpio.

El debounce y el wait-for-release son la traducción en software de esa realidad eléctrica.
Y la invariante de seguridad enseñó algo distinto: en un sistema embebido no basta con que
el programa "haga lo que quiero" — hay estados que simplemente **no deben poder existir**,
y conviene que el código los bloquee explícitamente en vez de confiar en que la secuencia
esté bien escrita.

La versión en C/C++ confirma que lo aprendido es el **concepto**, no la sintaxis:
`button.value()` y `gpio_get(BUTTON)` son la misma idea, y el circuito no cambió ni un cable.

---

## Contenido de esta carpeta

| Carpeta / archivo | Contenido |
|---|---|
| `micropython/01_button_read.py` | DO 01 — lectura del botón con pull-up interno |
| `micropython/02_button_debounce.py` | DO 02 — debounce + wait for release |
| `micropython/03_semaforo_peatonal.py` | CHALLENGE — semáforo completo |
| `cpp/button_read/button_read.c` | Proyecto Pico SDK: lectura equivalente del botón en C |
| `cpp/traffic_light/traffic_light.c` | Proyecto Pico SDK: semáforo completo en C |
| `cpp/build.sh` | Compila los proyectos de C desde una terminal normal |
| `wokwi/` | Circuito + un `wokwi.toml` por escenario, apuntando al firmware de `cpp/` |
| `evidence/` | Capturas de Wokwi y foto del hardware |

### Cómo correrlo

**MicroPython** — copiar el script deseado como `main.py` en la Pico (o pegarlo en el IDE
web de Wokwi) y abrir el monitor serial.

**C/C++** — desde una terminal normal:

```bash
cd cpp
./build.sh                 # compila los dos proyectos
./build.sh button_read     # o solo uno
```

El script exporta el toolchain de `~/.pico-sdk/` y deja el `.uf2` en
`cpp/<proyecto>/build/`. Ese archivo se copia a la Pico en modo BOOTSEL.

**Desde VS Code:** abrir `cpp/button_read/` o `cpp/traffic_light/` como carpeta
(*File → Open Folder*), **no** la carpeta de la sesión. La extensión de Pico espera un
proyecto por ventana y sus rutas de IntelliSense son relativas a la carpeta abierta.
Alternativa: abrir `Sesion_03.code-workspace`, que ya registra los dos proyectos como
carpetas independientes del mismo workspace.

> Si `#include "pico/stdlib.h"` sale subrayado en rojo: compilar una vez
> (`./build.sh`) y recargar la ventana. IntelliSense necesita el `build/` para resolver
> los headers del SDK.

**Simulación en Wokwi** — los `wokwi.toml` de `wokwi/cpp/*/` apuntan por ruta relativa al
`.uf2` de `cpp/`, así que la simulación corre **el mismo binario** que se flashea en la Pico
física. En VS Code: `Wokwi: Select Config File` → elegir el escenario → `Wokwi: Start
Simulator`. MicroPython se prueba en wokwi.com porque la extensión no simula MicroPython.

Procedimiento completo en [`wokwi/README.md`](./wokwi/README.md).
