# Sesión 09 — Comunicación UART

**Challenge 09 — UART Command Center con Thonny**
_Angel Rugerio Jiménez · 201720 · Lab. de Elementos Programables_

## 1. Objetivo y ruta de datos

Controlar dos LEDs y consultar su estado con tramas de texto (`SET,LED1,1`, `GET,STATUS`…) que **cruzan el UART hardware real** de la Pico 2 W antes de ser interpretadas.

```text
VS Code/USB → input() → UART TX GP0 → jumper → UART RX GP1 → parser → LEDs → respuesta en el vREPL de MicroPico
```

| Elemento | Pin  | Función                            |
| -------- | ---- | ---------------------------------- |
| UART0 TX | GP0  | Transmite la trama                 |
| UART0 RX | GP1  | Recibe la trama (jumper desde GP0) |
| LED1     | GP13 | Salida controlada                  |
| LED2     | GP14 | Salida controlada                  |

## 2. Conceptos

- **UART** (Universal Asynchronous Receiver-Transmitter): periférico que envía bytes bit por bit por un solo cable, **sin señal de reloj compartida**. Por eso es _asíncrono_: emisor y receptor solo se ponen de acuerdo en la velocidad y el formato de antemano.
- **TX / RX**: TX es el pin que transmite y RX el que recibe. Entre dos dispositivos se cruzan: el TX de uno va al RX del otro (y comparten GND).
- **Baud rate**: símbolos por segundo; en UART, bits por segundo. Aquí 9600 baud → cada bit dura $1/9600 \approx 104\ \mu s$. Si los dos lados no usan el mismo baud rate, el receptor muestrea en momentos equivocados y lee basura.
- **8N1**: el formato de cada byte — **8** bits de datos, **N**o paridad, **1** bit de stop. Con el bit de start son 10 bits por byte, así que 9600 baud ≈ 960 bytes/s. En el código se declara explícito: `UART(0, baudrate=9600, bits=8, parity=None, stop=1, ...)`.
- **Trama**: un mensaje completo con estructura acordada. Aquí: campos separados por `,` y terminados en `\n`. El `\n` marca el fin de la trama: el receptor sabe que ya llegó todo.
- **ACK / ERR**: la respuesta confirma qué pasó. `ACK,...` = trama válida y ejecutada; `STATUS,...` = respuesta a una consulta; `ERR,...` = trama rechazada, con el motivo.

### Por qué Thonny usa USB/REPL y no el UART

`print()` e `input()` viajan por el **USB** de la Pico (el REPL de MicroPython), que es otra interfaz distinta de UART0. Lo que sale con `uart.write()` sale físicamente por GP0 y **no aparece en Thonny**. Por eso Thonny se usa como consola del operador y el UART se prueba aparte.

### Cómo el loopback comprueba el UART sin adaptador

El jumper GP0 → GP1 conecta el TX de la Pico con su propio RX: todo byte transmitido vuelve a entrar. Si `UART RX` muestra exactamente lo mismo que `USB CMD`, el periférico, los pines y la configuración funcionan, sin necesidad de un adaptador USB–UART. Si se quita el jumper, el programa responde `UART RX : SIN DATOS. Revisa GP0 -> GP1`: la trama no se interpreta si no cruzó el cable.

## 3. Recepción robusta (corrección v3)

`uart.any()` se vuelve verdadero con el primer byte; un `readline()` en ese momento podía devolver una trama a medias (`STATUS` → `STATU`). `receive_complete_line()` lee byte por byte, acumula en un `bytearray` y **solo entrega la trama al recibir `\n`**; si no llega completa en 1000 ms devuelve `None` y la trama se descarta. Antes de enviar, `clear_rx()` vacía restos de pruebas anteriores.

## 4. Protocolo

| Trama                           | Respuesta                        | Nivel |
| ------------------------------- | -------------------------------- | ----- |
| `PING`                          | `ACK,PONG`                       | 1     |
| `GET,STATUS`                    | `STATUS,LED1,x,LED2,y`           | 1     |
| `SET,LED1,0/1` · `SET,LED2,0/1` | `ACK,LEDn,v`                     | 1     |
| `SET,ALL,0/1`                   | `ACK,ALL,v`                      | 2     |
| `TOGGLE,LED1/LED2`              | `ACK,LEDn,<valor nuevo>`         | 3     |
| `BLINK,LED1/LED2,<ms>`          | `ACK,BLINK,LEDn,ms` (50–5000 ms) | 3     |
| `HELP`                          | `ACK,HELP: <lista de comandos>`  | 3     |

Las tramas no distinguen mayúsculas y toleran espacios alrededor de cada campo (`set, led2 ,0` es válida).

| Error               | Cuándo                                               |
| ------------------- | ---------------------------------------------------- |
| `ERR,BAD_FIELDS`    | Número de campos incorrecto (`SET,LED1`, `PING,1`)   |
| `ERR,BAD_DEVICE`    | Dispositivo inexistente (`SET,LED3,1`)               |
| `ERR,BAD_VALUE`     | Valor distinto de `0`/`1` (`SET,LED1,9`)             |
| `ERR,BAD_GET`       | `GET` con algo distinto de `STATUS`                  |
| `ERR,BAD_PERIOD`    | Periodo de `BLINK` no numérico o fuera de 50–5000 ms |
| `ERR,UNKNOWN_FRAME` | Comando desconocido / texto libre                    |

`BLINK` usa un `Timer(-1)` periódico por LED (como en la Sesión 04): el parpadeo sigue mientras `input()` espera el siguiente comando. Un `SET` o `TOGGLE` sobre ese LED detiene el parpadeo.

## 5. Resultados de la tabla de pruebas

Detalle completo en [`tabla_pruebas.csv`](./tabla_pruebas.csv).

| #   | Comando          | Esperado               | Resultado |
| --- | ---------------- | ---------------------- | --------- |
| 1   | `PING`           | `ACK,PONG`             | ✅        |
| 2   | `SET,LED1,1`     | `ACK,LED1,1`           | ✅        |
| 3   | `SET,LED1,0`     | `ACK,LED1,0`           | ✅        |
| 4   | `SET,LED2,1`     | `ACK,LED2,1`           | ✅        |
| 5   | `SET,ALL,1`      | `ACK,ALL,1`            | ✅        |
| 6   | `GET,STATUS`     | `STATUS,LED1,1,LED2,1` | ✅        |
| 7   | `SET,LED3,1`     | `ERR,BAD_DEVICE`       | ✅        |
| 8   | `SET,LED1,9`     | `ERR,BAD_VALUE`        | ✅        |
| 9   | texto libre      | `ERR,UNKNOWN_FRAME`    | ✅        |
| 10  | `SET,LED1`       | `ERR,BAD_FIELDS`       | ✅        |
| 11  | `SET,ALL,0`      | `ACK,ALL,0`            | ✅        |
| 12  | `TOGGLE,LED1`    | `ACK,LED1,1`           | ✅        |
| 13  | `BLINK,LED2,500` | `ACK,BLINK,LED2,500`   | ✅        |
| 14  | `BLINK,LED2,10`  | `ERR,BAD_PERIOD`       | ✅        |
| 15  | `HELP`           | `ACK,HELP: ...`        | ✅        |

## 6. Conclusión

Este challenge me ayudó a entender algo que daba por hecho: que lo que veo en la consola no es lo mismo que lo que sale por los pines. `print()` e `input()` viajan por USB, mientras que el UART es un periférico aparte que manda los bits por un cable físico, y con un simple jumper entre GP0 y GP1 se puede comprobar que de verdad funciona, sin ningún adaptador extra. Ver que `UART RX` repetía exactamente lo que mandaba `USB CMD`, y que al quitar el jumper todo se caía a `SIN DATOS`, fue la prueba más clara de que la trama sí cruzaba el cable.

Lo que más me llamó la atención fue diseñar el protocolo: decidir qué es una trama válida, cuántos campos lleva y qué error regresar en cada caso. Es la misma lógica de cualquier API o sistema que se comunica con otro, solo que aquí a nivel de bytes, y la corrección v3 del profe me dejó claro por qué no basta con leer "lo que haya llegado" (`STATUS` → `STATU`), sino esperar al `\n` que marca el fin del mensaje. También aproveché el bonus para reutilizar los `Timer` de la Sesión 04 con `BLINK`, y fue satisfactorio ver el LED parpadeando mientras seguía mandando comandos sin que nada se bloqueara. Además, cambié Thonny por VS Code con MicroPico, que ya había usado en el examen, y quedé muy cómodo trabajando así. Fue muy divertida de hacer.

## Evidencias y cómo correrlo

| Evidencia                                                   | Archivo                                                            |
| ----------------------------------------------------------- | ------------------------------------------------------------------ |
| Consola vREPL de MicroPico (`USB CMD` / `UART RX` / `RESP`) | [`evidencia/vscode.png`](./evidencia/vscode.png)                   |
| Pico con jumper GP0 → GP1                                   | [`evidencia/loopback_fisico.jpg`](./evidencia/loopback_fisico.jpg) |
| Video del sistema funcionando                               | [`evidencia/video.mp4`](./evidencia/video.mp4)                     |

- **Pico:** jumper GP0 → GP1, abrir `Sesion_09_UART/` en VS Code con MicroPico, `main.py` → **Run**, y escribir los comandos en el vREPL en `CMD>`. **Stop** o Ctrl-C detiene el programa y apaga los timers de `BLINK`.
