	# Sesión 10 — Comunicación I2C + OLED HMI

**Challenge 10 — Smart I2C HMI Monitor**
_Angel Rugerio Jiménez · 201720 · Lab. de Elementos Programables_

## 1. Objetivo y circuito

Integrar en un solo sistema un **bus I2C**, una pantalla **OLED SSD1306**, un sensor analógico, un botón y un LED de alarma. Al arrancar, la Pico escanea el bus y valida que la OLED responda. Después mide el potenciómetro, clasifica el valor y lo muestra en una HMI de 3 páginas que se recorre con el botón.

```text
Potenciómetro → ADC GP26 → % + classify() → framebuffer → I2C GP4/GP5 → OLED 0x3C
                                         └→ LED ALARM GP15
Botón GP16 → flanco 1 → 0 → cambia de página
```

| Elemento | Pin | Función |
| -------- | --- | ------- |
| OLED SDA | GP4 | Datos del bus (I2C0) |
| OLED SCL | GP5 | Reloj del bus (I2C0) |
| OLED VCC / GND | 3V3 / GND | Alimentación del módulo |
| Potenciómetro | GP26 / ADC0 | Sensor analógico (3V3 / GND / señal) |
| Botón a GND (`PULL_UP`) | GP16 | Cambia de página |
| LED rojo + 330 Ω | GP15 | Alarma |

Bus: `I2C(0, scl=Pin(5), sda=Pin(4), freq=400_000)`, es decir, **400 kHz** (Fast-mode).

Simulación: [`wokwi/enlace.md`](./wokwi/enlace.md) · Circuito: [`wokwi/diagram.json`](./wokwi/diagram.json) (Pico W: mismo pinout que la Pico 2 W).

> **Práctica realizada solo en Wokwi.** No cuento con una OLED SSD1306 física, y la sesión permite cubrir toda la práctica en simulación.

## 2. Conceptos

- **I2C** (Inter-Integrated Circuit): bus serial **síncrono** de dos líneas. A diferencia de UART, que une dos extremos, varios dispositivos comparten las mismas líneas.
- **SDA / SCL**: SDA es la línea bidireccional de datos y SCL el reloj, que lo genera el **controlador** (la Pico). Los periféricos son **targets**.
- **Dirección**: número de 7 bits con el que el controlador elige con quién habla. `0x3C` y `60` son el mismo valor en dos bases: $3 \times 16 + 12 = 60$.
- **ACK / NACK**: el receptor confirma cada byte. `i2c.scan()` se apoya en esto: la dirección que responde con ACK entra en la lista.
- **Pull-ups**: los nodos solo pueden tirar la línea a LOW; el nivel alto lo pone una resistencia a 3V3. Muchos módulos OLED comerciales ya las incluyen.
- **Framebuffer**: `text()`, `rect()` y `fill_rect()` dibujan en RAM. La imagen llega al panel solo con `oled.show()`, que manda los 1024 bytes ($128 \times 64 / 8$) por I2C. Por eso el ciclo siempre es **limpiar → dibujar → show**.

## 3. Resultado de `i2c.scan()`

| Decimal | Hexadecimal | Dirección de la OLED |
| ------- | ----------- | -------------------- |
| 60      | 0x3c        | 0x3c                 |

Si la OLED no aparece en `OLED_ADDR`, el programa se detiene con un mensaje claro en lugar de un error del driver:

```text
RuntimeError: OLED 0x3c no detectada: revisa SDA/SCL/VCC/GND
```

## 4. Las 3 páginas de la HMI

| Página | Contenido | Captura |
| ------ | --------- | ------- |
| **1 · LIVE** | Porcentaje ADC, estado y barra con marcas en 50 % y 75 % | [`live.png`](./evidence/live.png) |
| **2 · I2C** | Pines SDA/SCL, frecuencia, número de dispositivos y direcciones | [`i2c.png`](./evidence/i2c.png) |
| **3 · STATS** | Mínimo, máximo y número de muestras | [`stats.png`](./evidence/stats.png) |

Cada página tiene una franja superior invertida con su título y número (`1/3`). En LIVE se prioriza lo que el operador debe entender en un segundo: primero el valor, luego el estado y al final la barra, que se lee sin tener que leer el número.

## 5. Lógica de ALARM y botón

| Estado | Condición | LED | En la pantalla |
| ------ | --------- | --- | -------------- |
| NORMAL | < 50 % | Apagado | Texto normal |
| WARNING | 50 % a < 75 % | Apagado | Texto normal |
| ALARM | ≥ 75 % | **Encendido** | Renglón del estado invertido |

Los umbrales son constantes (`WARNING`, `ALARM`) al inicio de `main.py`. El LED se actualiza en cada muestra, sin importar qué página esté visible, y los datos de STATS siguen acumulándose en todas las páginas.

El botón solo cuenta el flanco `1 → 0`, así que una pulsación avanza una página aunque se mantenga presionado: `page = (page + 1) % PAGES`.

### Actualización sin `sleep()` largos

El starter usaba un `sleep_ms(100)` por ciclo, y una pulsación corta podía caer entre dos lecturas del botón. Por eso se reutilizó el scheduler cooperativo del Reto 08: cada tarea corre a su propio ritmo con `ticks_ms()` y el único `sleep` es de 2 ms.

| Tarea | Periodo | Qué hace |
| ----- | ------- | -------- |
| Sensor | 100 ms | ADC → % → estado → min/max/samples → LED |
| Botón | 50 ms | Detecta el flanco y cambia de página |
| Display | 100 ms | `fill(0)` → dibuja la página → `show()` |
| Log | 1000 ms | Imprime el estado en el REPL |

Cada `show()` tarda alrededor de 23 ms a 400 kHz ($1025 \times 9 / 400\,000$), así que cabe de sobra en un periodo de 100 ms.

## 6. ¿Por qué varios dispositivos comparten SDA/SCL?

Porque la selección no se hace con un cable, sino con la **dirección**. Después del START, el controlador envía la dirección en el bus: todos los targets la escuchan, pero solo responde con ACK aquel cuya dirección coincide, y los demás ignoran la transacción. Las salidas son open-drain, así que ningún nodo fuerza un nivel alto contra otro. Por eso una OLED en `0x3C` y un MPU6050 en `0x68` pueden vivir en los mismos GP4/GP5, siempre que sus direcciones sean distintas.

## 7. Resultados de la tabla de pruebas

| Prueba                                                       | Resultado esperado                       | PASS/FAIL | Evidencia                      |
| ------------------------------------------------------------ | ---------------------------------------- | --------- | ------------------------------ |
| Scan I2C                                                     | OLED detectada (normalmente `0x3C`)      | ✅         | [imagen](./evidence/scan.png)  |
| LIVE < 50 %                                                  | NORMAL                                   | ✅         | [video](./evidence/video.mp4)  |
| LIVE 50–74.9 %                                               | WARNING                                  | ✅         | [video](./evidence/video.mp4)  |
| LIVE ≥ 75 %                                                  | ALARM + LED ON                           | ✅         | [imagen](./evidence/live.png)  |
| Botón 1 vez                                                  | Cambia una página                        | ✅         | [video](./evidence/video.mp4)  |
| Ciclo de botón                                               | LIVE → I2C → STATS → LIVE                | ✅         | [video](./evidence/video.mp4)  |
| Página I2C                                                   | Muestra la(s) dirección(es) detectada(s) | ✅         | [imagen](./evidence/i2c.png)   |
| STATS                                                        | min/max/samples cambian                  | ✅         | [imagen](./evidence/stats.png) |
| Cambiar dirección de OLED desde `diagram.json` (diagnóstico) | Scan no muestra `0x3C` / mensaje claro   | ✅         | [imagen](./evidence/diag.png)  |

Como la práctica es en simulación, "desconectar la OLED" se reproduce cambiando `i2cAddress` a `0x3d` en `diagram.json`: el scan ya no encuentra `0x3C` y el programa se detiene con el mensaje de la sección 3.

## 8. Problemas encontrados

- **`SyntaxError` con la placa `board-pi-pico-2w` de Wokwi.** Con esta placa, recién agregada a Wokwi, el programa se detenía antes de ejecutar nada con `SyntaxError: invalid syntax` en la línea 145, que es una línea válida. El mismo `main.py` corrió sin cambios al usar `board-pi-pico-w`, la placa de los retos 07 y 08. No se pudo identificar la causa exacta, pero no está en el código ni en el cableado: el error aparece al compilar, antes de tocar cualquier pin, y las dos placas comparten pinout.

## 9. Conclusión

Esta ha sido una de las practicas más interesantes de todas. El poder ver la información en el serial de la placa es una cosa, pero, verla representada en una pantalla, le da otra esencia. Esto es el primer paso para el desarrollo de interfaces de usuario, que comunican la información de una mejor manera. La verdad me gustó bastante, y voy a explorar un poco más las capacidades o actividades que se pueden realizar con una pantalla. Eso si, para poder hacerlo, primero consigo una OLED en físico. Finalmente, solo para añadir, busqué experimentar con la nueva placa de Wokwi, la Raspberry Pi Pico 2 W (que es la que tengo en físico), pero tal parece que aún no esta del todo pulida; ojalá poder usarla después.

## Evidencias y cómo correrlo

| Evidencia            | Archivo                                      |
| -------------------- | -------------------------------------------- |
| Scan en el REPL      | [`evidence/scan.png`](./evidence/scan.png)   |
| Página LIVE          | [`evidence/live.png`](./evidence/live.png)   |
| Página I2C           | [`evidence/i2c.png`](./evidence/i2c.png)     |
| Página STATS         | [`evidence/stats.png`](./evidence/stats.png) |
| Diagnóstico sin OLED | [`evidence/diag.png`](./evidence/diag.png)   |

**Wokwi:** proyecto Pico W + MicroPython; pegar `wokwi/diagram.json`, `main.py` y `ssd1306.py`. Botón con click o tecla `A`.
