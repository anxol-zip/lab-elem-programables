# Sesión 07 — ADC y acondicionamiento de señal

**Reto 07 — Smart Analog Monitor**
_Angel Rugerio Jiménez · 201720 · Lab. de Elementos Programables_

---

## 1. Objetivo

Construir un **monitor analógico** con la Raspberry Pi Pico: leer una señal en GP26 / ADC0, convertirla a voltaje y porcentaje, suavizarla con un **promedio móvil**, clasificarla en **NORMAL / WARNING / ALARM** y encender el LED que corresponde.

Hasta la Sesión 06 la Pico **producía** niveles intermedios con PWM. Ahora los **lee**: deja de preguntar "¿encendido o apagado?" y empieza a preguntar "¿cuánto?". El potenciómetro simula la salida de un sensor ya acondicionado (luz, temperatura, presión, nivel):

```
señal analógica → ADC → raw → promedio móvil → voltaje / % → estado → LED + serial
```

## 2. Circuito

| Elemento | Pin | Conexión |
|---|---|---|
| Potenciómetro 50 kΩ (B50K) | GP26 / ADC0 | `SIG → GP26`, `VCC → 3V3`, `GND → GND` |
| LED verde (NORMAL) | GP13 | `GP13 → resistencia → LED → GND` |
| LED amarillo (WARNING) | GP14 | `GP14 → resistencia → LED → GND` |
| LED rojo (ALARM) | GP15 | `GP15 → resistencia → LED → GND` |

Los extremos del potenciómetro van a **3V3** y **GND**, y el cursor a GP26: el cursor entrega un voltaje entre 0 V y 3.3 V según su posición. **Nunca 5 V en GP26**: las entradas ADC de la Pico solo toleran hasta 3.3 V, por eso el potenciómetro se alimenta de `3V3` y no de `VBUS`.

[`wokwi/diagram_pot.json`](./wokwi/diagram_pot.json) es este circuito, el de `main.py` y la placa física: las mismas conexiones que la plantilla del curso, con dos diferencias. La placa es una **Pico W** con MicroPython 1.28, y las resistencias de los LEDs son de **1 kΩ** en vez de 330 Ω (los LEDs brillan menos, la lógica no cambia). [`wokwi/diagram.json`](./wokwi/diagram.json) es la variante del bonus, con el potenciómetro cambiado por un sensor de gas (sección 6.1).

## 3. Qué es el ADC y qué significa `read_u16()`

Un **ADC** (convertidor analógico-digital) hace dos cosas:

1. **Muestreo:** toma el voltaje del pin en un instante. Aquí el periodo de muestreo lo pone el programa: una lectura cada `PERIODO_MS = 300 ms (de forma inicial)`.
2. **Cuantización:** convierte ese voltaje en un número entero.

`sensor.read_u16()` devuelve ese número **normalizado a 16 bits**: de `0` (0 V) a `65535` (3.3 V), porque $2^{16} - 1 = 65535$. Solo GP26, GP27 y GP28 tienen ADC (canales 0, 1 y 2); esta práctica usa **GP26 / ADC0**.

```python
sensor = ADC(Pin(26))
raw = sensor.read_u16()    # 0 a 65535
```

> [!NOTE]
> El ADC de la Pico (RP2040 en Wokwi, RP2350 en la placa) es de **12 bits**: 4096 niveles reales. MicroPython escala la lectura a 16 bits, así que `raw` avanza de 16 en 16 aproximadamente. La resolución real es $3.3\ \text{V} / 4096 \approx 0.8\ \text{mV}$.

## 4. Conversión: raw → voltaje → porcentaje

El ADC entrega un número, pero **no sabe qué sensor hay conectado**: el significado lo pone el programa. Las dos conversiones son reglas de tres sobre el rango $0 \dots 65535$:

$$V = \frac{raw \cdot V_{REF}}{65535} \qquad \% = \frac{raw \cdot 100}{65535} \qquad V_{REF} = 3.3\ \text{V}$$

```python
def to_voltage(raw):
    return raw * VREF / 65535

def to_percent(raw):
    return raw * 100 / 65535
```

| raw | Voltaje | % |
|---|---|---|
| 0 | 0.00 V | 0.0 % |
| 16383 | 0.82 V | 24.999 % |
| 32767 | 1.65 V | 49.999 % |
| 49151 | 2.47 V | 74.9996 % |
| 65535 | 3.30 V | 100.0 % |

Es la conversión de la Sesión 06 al revés: allá `duty = percent * 65535 / 100` (de porcentaje a 16 bits), aquí `percent = raw * 100 / 65535` (de 16 bits a porcentaje).

## 5. El filtro: promedio móvil

Una lectura real tiene **ruido**: el valor salta aunque el sensor esté quieto. El promedio móvil reemplaza cada lectura por el promedio de las últimas $N$:

$$\bar{x}_k = \frac{1}{N} \sum_{i=0}^{N-1} x_{k-i} \qquad N = 10$$

```python
def filter_average(raw):
    window.append(raw)              # entra la lectura nueva
    if len(window) > WINDOW_SIZE:
        window.pop(0)               # sale la más vieja
    return sum(window) / len(window)
```

`window` es una **ventana deslizante**: siempre guarda las últimas `WINDOW_SIZE` lecturas. Al arrancar tiene menos de 10 elementos; por eso se divide entre `len(window)` y no entre `WINDOW_SIZE`, para que las primeras lecturas no salgan artificialmente bajas.

**El voltaje, el porcentaje y el estado se calculan sobre `filtered`, no sobre `raw`.** `raw` se imprime solo para ver cuánto ruido quitó el filtro.

**El costo del filtro es retraso.** Un cambio real tarda en reflejarse completo aproximadamente $N \cdot T_s = 10 \cdot 300\ \text{ms} = 3\ \text{s}$. En la verificación del código (sección 8), pasar el potenciómetro de 50 % a 100 % de golpe tardó **6 lecturas (1.8 s)** en llegar a ALARM y **10 lecturas (3 s)** en mostrar el 100 %. Una ventana más grande da una señal más estable pero más lenta; 10 lecturas a 300 ms es un compromiso razonable para un monitor que muestra el estado con LEDs.

## 6. Umbrales elegidos

| Estado | Rango | LED |
|---|---|---|
| **NORMAL** | 0 % a < 50 % | Verde |
| **WARNING** | 50 % a < 75 % | Amarillo |
| **ALARM** | 75 % a 100 % | Rojo |

```python
def classify(percent):
    if percent >= ALARM:          # del umbral más alto al más bajo
        return "ALARM"
    elif percent >= WARNING:
        return "WARNING"
    else:
        return "NORMAL"
```

El orden del `if` importa: si se preguntara primero `>= WARNING`, un 80 % entraría ahí y nunca llegaría a ALARM.

```python
def update_outputs(state):
    green.value(state == "NORMAL")
    yellow.value(state == "WARNING")
    red.value(state == "ALARM")
```

Cada comparación ya es `True`/`False`, que `value()` toma como `1`/`0`: las tres líneas garantizan que **solo un LED está encendido a la vez**, sin `if` extra.

**Por qué 50 y 75.** Son los valores de la clase y dividen el rango en tres zonas: la mitad inferior es operación normal, el siguiente cuarto es una advertencia con margen para reaccionar, y el último cuarto exige acción. Para un sensor real dependerían de qué significa el porcentaje: un umbral es una decisión de ingeniería, no un número mágico.

### _DO 02 — Tres configuraciones de umbrales_

> [!Note]
> Se uso un sensor de gas para cambiar al potenciometro, corriendo todo en Wokwi y no en la placa física.

| Configuración | WARNING | ALARM | Observación |
|---|---|---|---|
| A (base) | 50 | 75 | Funcionamiento normal |
| B | 40 | 60 | Cambio más repentino al estado de "ALARM" |
| C | 60 | 80 | Umbral más amplio de aceptación antes de pasar a "ALARM" |

### 6.1 Bonus — Cambiar el sensor: gas en lugar de potenciómetro

La presentación propone cambiar el potenciómetro por otro sensor para demostrar que **el algoritmo no depende del potenciómetro**. Aquí se usó el sensor de gas de Wokwi (`wokwi-gas-sensor`, tipo MQ-2), solo en simulación, con [`wokwi/diagram.json`](./wokwi/diagram.json) y [`wokwi/sensor.py`](./wokwi/sensor.py):

| Sensor de gas | Pico | Antes (potenciómetro) |
|---|---|---|
| `AOUT` (salida analógica) | GP26 / ADC0 | `SIG` |
| `VCC` | 3V3 | `VCC` |
| `GND` | GND | `GND` |

**Qué cambia en el código: prácticamente nada.** `sensor.py` es `main.py` con otros comentarios y otro mensaje de arranque; lectura, filtro, conversión, clasificación y LEDs son idénticos. Eso es justo lo que se quería demostrar: como el programa trabaja sobre un voltaje entre 0 y 3.3 V, no le importa si ese voltaje sale de una perilla o de un sensor.

**Lo que sí cambia es el significado del número:**

- **Más gas → más voltaje en `AOUT` → más %.** La dirección es la misma que con el potenciómetro, así que NORMAL / WARNING / ALARM siguen teniendo sentido sin invertir nada: más gas es más peligro.
- **El % es del rango del ADC, no una concentración.** Pasar de voltaje a ppm (partes por millón) requiere calibrar el sensor con su curva de respuesta, que no es lineal; eso queda fuera de esta práctica. Por eso los umbrales se eligieron **observando** el comportamiento en el DO 02, no a partir de una norma de ppm.
- **El DO 02 cobra sentido con un sensor real:** con el potenciómetro cualquier umbral es arbitrario; con gas, bajar los umbrales (B: 40/60) adelanta la alarma y la vuelve más sensible, y subirlos (C: 60/80) tolera más gas antes de alarmar.

> [!WARNING]
> **En físico no se conecta igual.** Un MQ-2 real se alimenta a **5 V** (su calefactor lo necesita), y entonces `AOUT` puede llegar a 5 V, por arriba del límite de 3.3 V del ADC. Montarlo en la placa exigiría un **divisor de voltaje** entre `AOUT` y GP26, además de un precalentamiento de varios minutos antes de que la lectura sea estable. En Wokwi el sensor se alimentó de 3V3, así que su salida no rebasa el rango.

## 7. Arquitectura del código

Cada paso del acondicionamiento es una función pequeña que se puede probar sola, y el `while` se lee como la descripción del sistema:

```python
while True:
    raw = read_raw()                    # medir
    filtered = filter_average(raw)      # filtrar
    voltage = to_voltage(filtered)      # convertir
    percent = to_percent(filtered)
    state = classify(percent)           # decidir
    update_outputs(state)               # actuar
    print_status(raw, filtered, voltage, percent, state)   # reportar
    sleep_ms(PERIODO_MS)
```

Todos los parámetros (`VREF`, `WARNING`, `ALARM`, `WINDOW_SIZE`, `PERIODO_MS`) están al inicio de `main.py` para ajustarlos sin tocar la lógica.

Salida del serial (cada línea trae los cinco datos que pide la práctica: raw, filtrada, voltaje, porcentaje y estado):

```
RETO 07 - Smart Analog Monitor
Sensor: GP26 (ADC0) | LEDs: GP13 verde, GP14 amarillo, GP15 rojo
Umbrales: WARNING >= 50 % | ALARM >= 75 % | Filtro: 10 lecturas
raw: 0 | filtered: 0 | V: 0.0 | %: 0.0 | state: NORMAL
...
raw: 65535 | filtered: 45874 | V: 2.31 | %: 70.0 | state: WARNING
raw: 65535 | filtered: 49151 | V: 2.47 | %: 75.0 | state: WARNING
raw: 65535 | filtered: 52427 | V: 2.64 | %: 80.0 | state: ALARM
```

En la segunda línea de `75.0 | WARNING` pasa lo mismo que con el 50 %: el filtrado vale 49151, que es 74.9996 %.

## 8. Pruebas

La prueba se corre en la simulación (wokwi.com, RP2040) y en la placa física (Pico 2 W, RP2350) con el mismo `main.py`. **Wokwi es evidencia de lógica; el hardware es evidencia de implementación.**

| Prueba | Resultado esperado | Wokwi | Físico |
|---|---|---|---|
| ADC mínimo | raw cercano a 0 / 0 % | ✅ | ✅ |
| ADC medio | raw cercano a 32767 / 50 % | ✅ | ✅ |
| ADC máximo | raw cercano a 65535 / 100 % | ✅ | ✅ |
| Filtro | La señal filtrada cambia suavemente | ✅ | ✅ |
| Normal | LED verde activo | ✅ | ✅ |
| Warning | LED amarillo activo | ✅ | ✅ |
| Alarm | LED rojo activo | ✅ | ✅ |
| Recuperación | Vuelve de ALARM a NORMAL al bajar la señal | ✅ | ✅ |

### _DO 01 — Cinco posiciones del potenciómetro_

> Probado con el montaje físico, corriendo `01_voltage_percent.py` (código de clase). Rangos tomados de las capturas en [`evidence/DO_01/`](./evidence/DO_01/).

| Posición | Raw | Voltaje | % |
|---|---|---|---|
| Mínima | 192 - 240 | 0.01 | 0.3 - 0.4 |
| 25 % | 16'388 - 16'740 | 0.83 - 0.84 | 25.0 - 25.5 |
| 50 % | 32'824 - 33'496 | 1.65 - 1.69 | 50.1 - 51.1 |
| 75 % | 48'779 - 49'804 | 2.46 - 2.51 | 74.4 - 76.0 |
| Máxima | 65'295 - 65'535 | 3.29 - 3.3 | 99.6 - 100.0 |

## 9. Pregunta de análisis

**¿Por qué conviene filtrar la señal antes de activar una alarma por umbral?**

Porque una alarma debe responder a lo que **hace la señal**, no a una lectura aislada. Sin filtro, un solo pico de ruido que cruce el 75 % encendería el LED rojo aunque la señal real esté en 70 %: una **falsa alarma**. Y si la señal real está justo en el borde de un umbral, el ruido la haría cruzar de un lado a otro en cada lectura, y el LED parpadearía entre dos estados sin que nada haya cambiado.

El promedio móvil hace que el estado dependa de las últimas 10 lecturas en conjunto: un pico aislado pesa una décima parte y no alcanza a mover el promedio sobre el umbral. El costo es el retraso de la sección 5: el sistema tarda más en reaccionar a un cambio real. Filtrar es elegir cuánta estabilidad se cambia por cuánta rapidez.

> [!NOTE]
> El filtro **reduce** el parpadeo en el borde de un umbral, pero no lo elimina: si el promedio mismo queda en 50.0 %, el ruido residual puede seguir cruzándolo.

## 10. Evidencias

| Evidencia                                      | Archivo                                                                                                                                                                                                                                    |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Simulación Wokwi                               | [`wokwi/enlace_o_captura.md`](./wokwi/enlace_o_captura.md)                                                                                                                                                                                 |
| Serial con raw, voltaje y porcentaje           | [`evidence/serial_raw_voltage.png`](./evidence/serial_raw_voltage.png)                                                                                                                                                                     |
| Alarma por umbrales en la placa (LED + serial) | NORMAL: [`evidence/threshold_alarm_0.jpg`](./evidence/threshold_alarm_0.jpg) · WARNING: [`evidence/threshold_alarm_1.jpg`](./evidence/threshold_alarm_1.jpg) · ALARM: [`evidence/threshold_alarm_2.jpg`](./evidence/threshold_alarm_2.jpg) |
| Montaje físico                                 | [`evidence/hardware_photo.jpg`](./evidence/hardware_photo.jpg)                                                                                                                                                                             |
| Video de funcionamiento                        | [`evidence/working.mp4`](./evidence/working.mp4)                                                                                                                                                                                           |

## 11. Problemas encontrados

- **`%: 50.0` con estado NORMAL.** No es un error: 32767 es 49.999 % y el `round()` del reporte lo muestra como 50.0 (sección 4).

## 12. Conclusión

Con esta práctica entendí que el ADC le permite a la Pico dejar de preguntar si algo está encendido o apagado, y empezar a medir cuánto. El número que entrega `read_u16()` por sí solo no dice mucho, así que lo convertí a voltaje y a porcentaje para poder trabajar con él. Al probar en la placa física noté que la lectura nunca se queda quieta: en el 75 % el valor crudo cruzaba el umbral de ALARM una y otra vez sin que yo moviera el potenciómetro. Por eso el promedio móvil fue lo más importante del reto, ya que con él el estado se mantuvo estable, aunque a cambio el sistema tarda unos segundos en reaccionar (algo que puede llegar a molestar o ser peligroso). También vi claro que los umbrales no son números fijos, sino una decisión que depende de qué tan rápido quieres que el sistema avise. Al cambiar el potenciómetro por el sensor de gas en Wokwi, el código casi no cambió, lo que demuestra que el algoritmo no depende del sensor que se use. Al final, la simulación me sirvió para validar la lógica, pero fue en la placa donde realmente se vio por qué hay que acondicionar la señal antes de tomar una decisión.

---

## Contenido y cómo correrlo

| Archivo / carpeta | Contenido |
|---|---|
| `main.py` | Smart Analog Monitor: lectura ADC, filtro, clasificación y LEDs |
| `wokwi/diagram_pot.json` | Circuito de `main.py` (Pico W + potenciómetro + 3 LEDs) |
| `wokwi/diagram.json` | Bonus: el mismo circuito con el sensor de gas en lugar del potenciómetro |
| `wokwi/sensor.py` | Bonus: el monitor adaptado al sensor de gas (solo Wokwi) |
| `wokwi/enlace_o_captura.md` | Enlace a la simulación publicada |
| `evidence/` | Capturas del serial y de los estados, y foto del montaje físico |
| `evidence/DO_01` | Capturas del serial para el DO_01 |

**Simulación:** en wokwi.com, proyecto Raspberry Pi Pico + MicroPython; pegar `wokwi/diagram_pot.json` (como `diagram.json`) y `main.py`. Para mover el potenciómetro, click sobre él en la simulación y arrastrar la perilla. Para el bonus: `wokwi/diagram.json` y `wokwi/sensor.py` (como `main.py`); la concentración de gas se cambia dando click al sensor durante la simulación.

**Hardware:**

```bash
mpremote run main.py            # correr sin instalar nada
mpremote cp main.py :main.py    # dejarlo autónomo
```
