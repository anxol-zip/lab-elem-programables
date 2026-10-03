# Sesión 07 — ADC y acondicionamiento de señal

**Reto 07 — Smart Analog Monitor**
_Angel Rugerio Jiménez · 201720 — Axel García Arellano · 201251 · Lab. de Elementos Programables_

---

## 1. Objetivo

Construir un **monitor analógico** con la Raspberry Pi Pico: leer una señal en GP26 / ADC0, convertirla a voltaje y porcentaje, suavizarla con un **promedio móvil**, clasificarla en **NORMAL / WARNING / ALARM** y encender el LED que corresponde.

Hasta la Sesión 06 la Pico **producía** niveles intermedios con PWM. Ahora los **lee**: deja de preguntar "¿encendido o apagado?" y empieza a preguntar "¿cuánto?". El potenciómetro simula la salida de un sensor ya acondicionado (luz, temperatura, presión, nivel); lo que se evalúa no es mover la perilla, sino cómo una señal se convierte en una decisión:

```
señal analógica → ADC → raw → promedio móvil → voltaje / % → estado → LED + serial
```

## 2. Circuito

| Elemento | Pin | Conexión |
|---|---|---|
| Potenciómetro 10 kΩ | GP26 / ADC0 | `SIG → GP26`, `VCC → 3V3`, `GND → GND` |
| LED verde (NORMAL) | GP13 | `GP13 → resistencia → LED → GND` |
| LED amarillo (WARNING) | GP14 | `GP14 → resistencia → LED → GND` |
| LED rojo (ALARM) | GP15 | `GP15 → resistencia → LED → GND` |

Los extremos del potenciómetro van a **3V3** y **GND**, y el cursor a GP26: el cursor entrega un voltaje entre 0 V y 3.3 V según su posición. **Nunca 5 V en GP26**: las entradas ADC de la Pico solo toleran hasta 3.3 V, por eso el potenciómetro se alimenta de `3V3` y no de `VBUS`.

[`wokwi/diagram.json`](./wokwi/diagram.json) tiene las mismas conexiones que la plantilla del curso, con dos diferencias: la placa es una **Pico W** con MicroPython 1.28, y las resistencias de los LEDs son de **1 kΩ** en vez de 330 Ω (los LEDs brillan menos, la lógica no cambia).

## 3. Qué es el ADC y qué significa `read_u16()`

Un **ADC** (convertidor analógico-digital) hace dos cosas:

1. **Muestreo:** toma el voltaje del pin en un instante. Aquí el periodo de muestreo lo pone el programa: una lectura cada `PERIODO_MS = 300 ms`.
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

> [!NOTE]
> **Por qué en la consola aparece `%: 50.0 | state: NORMAL`.** La mitad exacta de 65535 es 32767.5, que no es una lectura posible. Con `raw = 32767` el porcentaje real es **49.999 %**: `round(…, 1)` lo muestra como `50.0`, pero no alcanza el umbral de `WARNING = 50`. El estado es correcto; lo que se redondea es solo lo que se imprime.

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

### DO 02 — Tres configuraciones de umbrales

> [!NOTE]
> Llenar al probar en Wokwi cambiando `WARNING` y `ALARM` al inicio de `main.py`.

| Configuración | WARNING | ALARM | Observación |
|---|---|---|---|
| A (base) | 50 | 75 | |
| B | 40 | 60 | |
| C | | | |

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

La prueba se corre en la simulación (wokwi.com, RP2040) y en la placa física (Pico 2 W, RP2350) con el mismo `main.py`. **Wokwi es evidencia de lógica; el hardware es evidencia de implementación.** En Wokwi el potenciómetro es casi ideal; el ruido que justifica el filtro se ve de verdad en la placa.

> [!NOTE]
> Llenar con ✅ / ❌ al correr cada prueba.

| Prueba | Resultado esperado | Wokwi | Físico |
|---|---|---|---|
| ADC mínimo | raw cercano a 0 / 0 % | | |
| ADC medio | raw cercano a 32767 / 50 % | | |
| ADC máximo | raw cercano a 65535 / 100 % | | |
| Filtro | La señal filtrada cambia suavemente | | |
| Normal | LED verde activo | | |
| Warning | LED amarillo activo | | |
| Alarm | LED rojo activo | | |
| Recuperación | Vuelve de ALARM a NORMAL al bajar la señal | | |

### DO 01 — Cinco posiciones del potenciómetro

| Posición | Raw | Voltaje | % |
|---|---|---|---|
| Mínima | | | |
| 25 % | | | |
| 50 % | | | |
| 75 % | | | |
| Máxima | | | |

**Verificación de la lógica fuera de la placa.** `main.py` se corrió en la computadora con `machine.ADC` reemplazado por una secuencia de lecturas conocidas (mínimo, medio, máximo, señal con ruido de ±1.8 % alrededor de 52 %, y caída a 0) y `machine.Pin` registrando los LEDs. Resultados:

- **Bordes de los umbrales:** 49.99 % → NORMAL, 50 % → WARNING, 74.99 % → WARNING, 75 % → ALARM.
- **Filtro:** con la lectura cruda saltando entre 50.6 % y 53.7 %, la filtrada se quedó entre 52.0 % y 52.1 % en cuanto la ventana se llenó con esas lecturas.
- **LEDs:** en las 64 lecturas hubo siempre **exactamente un** LED encendido.
- **Recuperación:** de ALARM a WARNING y a NORMAL al bajar la señal, sin quedarse atorado.

## 9. Pregunta de análisis

**¿Por qué conviene filtrar la señal antes de activar una alarma por umbral?**

Porque una alarma debe responder a lo que **hace la señal**, no a una lectura aislada. Sin filtro, un solo pico de ruido que cruce el 75 % encendería el LED rojo aunque la señal real esté en 70 %: una **falsa alarma**. Y si la señal real está justo en el borde de un umbral, el ruido la haría cruzar de un lado a otro en cada lectura, y el LED parpadearía entre dos estados sin que nada haya cambiado.

El promedio móvil hace que el estado dependa de las últimas 10 lecturas en conjunto: un pico aislado pesa una décima parte y no alcanza a mover el promedio sobre el umbral. El costo es el retraso de la sección 5: el sistema tarda más en reaccionar a un cambio real. Filtrar es elegir cuánta estabilidad se cambia por cuánta rapidez.

> [!NOTE]
> El filtro **reduce** el parpadeo en el borde de un umbral, pero no lo elimina: si el promedio mismo queda en 50.0 %, el ruido residual puede seguir cruzándolo. Si aparece en la placa, se anota en la sección 11.

## 10. Evidencias

| Evidencia | Archivo |
|---|---|
| Simulación Wokwi | [`wokwi/enlace_o_captura.md`](./wokwi/enlace_o_captura.md) |
| Serial con raw, voltaje y porcentaje | [`evidence/serial_raw_voltage.png`](./evidence/serial_raw_voltage.png) |
| Alarma por umbrales (NORMAL / WARNING / ALARM) | [`evidence/threshold_alarm.png`](./evidence/threshold_alarm.png) |
| Montaje físico | [`evidence/hardware_photo.jpg`](./evidence/hardware_photo.jpg) |

## 11. Problemas encontrados

> [!NOTE]
> Completar con lo que salga al correr las pruebas.

- **`%: 50.0` con estado NORMAL.** No es un error: 32767 es 49.999 % y el `round()` del reporte lo muestra como 50.0 (sección 4).

## 12. Conclusión

> [!NOTE]
> Completar al tener los resultados de Wokwi y de la placa.

---

## Contenido y cómo correrlo

| Archivo / carpeta | Contenido |
|---|---|
| `main.py` | Smart Analog Monitor: lectura ADC, filtro, clasificación y LEDs |
| `wokwi/diagram.json` | Circuito de la simulación (Pico W + potenciómetro + 3 LEDs) |
| `wokwi/enlace_o_captura.md` | Enlace a la simulación publicada |
| `evidence/` | Capturas del serial y de los estados, y foto del montaje físico |

**Simulación:** en wokwi.com, proyecto Raspberry Pi Pico + MicroPython; pegar `wokwi/diagram.json` y `main.py`. Para mover el potenciómetro, click sobre él en la simulación y arrastrar la perilla.

**Hardware:**

```bash
mpremote run main.py            # correr sin instalar nada
mpremote cp main.py :main.py    # dejarlo autónomo
```
