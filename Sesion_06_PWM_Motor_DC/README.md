# Sesión 06 — PWM, puente H y control de motor DC

**Reto 06 — Smart Motor Controller**
_Angel Rugerio Jiménez · 201720 — Axel García Arellano · 201251 · Lab. de Elementos Programables_

---

## 1. Objetivo

Desarrollar un **controlador de motor DC** con la Raspberry Pi Pico, PWM y un puente H L298N. No basta con que el motor gire: el controlador decide **cómo llega a cada estado** — hacia dónde gira, qué tan rápido, qué tan suave acelera y frena, y en qué condiciones se le permite invertir el sentido.

Hasta la Sesión 04 los GPIO solo tenían dos estados. Aquí aparece un tercer tipo de salida: una que sigue siendo digital, pero que al conmutar muy rápido entrega una **energía promedio** ajustable. Eso separa el problema en dos preguntas con dos pines distintos:

| Pregunta | Pin | Tipo de señal |
|---|---|---|
| **¿Hacia dónde?** | `IN1`, `IN2` | Lógica: `0` / `1` |
| **¿Qué tan rápido?** | `ENA` | PWM: duty cycle 0–100 % |

## 2. Circuito

El montaje físico y el de Wokwi son el mismo, y los pines no cambian entre uno y otro:

| Pico | L298N | Función |
|---|---|---|
| GP2 | IN1 | Dirección |
| GP3 | IN2 | Dirección |
| GP4 | ENA | Velocidad (PWM a 100 Hz) |
| GND | GND | Tierra común |

El motor va a `OUT1/OUT2` y el L298N se alimenta con una **fuente externa** en `Vs/GND`, con el jumper de `ENA` retirado para que el PWM tenga efecto. El motor **nunca** se conecta a un GPIO: la Pico entrega 3.3 V y muy poca corriente, y el motor, como carga inductiva, genera ruido y picos. **La Pico decide; el puente H entrega la potencia.** La tierra común es obligatoria: sin ella, `IN1/IN2/ENA` no tienen referencia y el L298N no interpreta las señales.

El circuito de Wokwi ([`wokwi/diagram.json`](./wokwi/diagram.json)) parte de la plantilla oficial del curso. La plantilla también traía tres botones (GP14/GP15/GP16) y un potenciómetro (GP26); **se dejaron** aunque no se usan para nada ahora.

## 3. Qué es PWM

**PWM (Pulse Width Modulation)** conmuta la salida entre 0 V y 3.3 V a frecuencia fija y varía **qué fracción del periodo** permanece en alto. Esa fracción es el **duty cycle**:

$$D = \frac{t_{on}}{T} \qquad V_{avg} = D \cdot 3.3\ \text{V}$$

Al 50 % la salida pasa la mitad del periodo en alto y la mitad en bajo; el promedio es ≈1.65 V, pero **en ningún instante hay 1.65 V en el pin**: PWM no es un voltaje analógico. Es la inercia del motor la que "promedia" los pulsos y los convierte en una velocidad. Duty alto → más energía promedio → más velocidad.

En MicroPython el duty se escribe con `duty_u16()`, que recibe un entero de 16 bits ($0 \dots 65535$): $\text{duty} = \lfloor D \cdot 65535 \rfloor$.

### Frecuencia: 100 Hz en vez de 1 kHz

En la clase se usó `ENA.freq(1000)`. En el motor físico, a 1 kHz y con duty bajo, **el motor no arrancaba**. Con ayuda del hermano de Angel (ingeniero mecatrónico y en sistemas) se probó a **100 Hz** y funcionó, así que el controlador usa `PWM_FREQ = 100` ($T = 10\ \text{ms}$).

> [!NOTE]
> Esto se encontró **probando**, no midiendo: no se midió corriente ni se vio la señal en un osciloscopio. Lo que sigue es la explicación más probable, con base en cómo funcionan el motor y el L298N.

- **El motor es una bobina.** Su corriente no sube de golpe cuando llega el pulso: crece con la constante de tiempo $\tau = L/R$ del devanado. A 1 kHz, un duty de 40 % deja el pulso en alto solo **0.4 ms**; si eso es del orden de $\tau$, la corriente se apaga antes de llegar a su valor final. A 100 Hz el mismo 40 % dura **4 ms**: la corriente alcanza su valor completo en cada pulso, y como el **torque es proporcional a la corriente**, el motor recibe más empuje con el mismo duty.
- **El L298N es un puente lento.** Está hecho con transistores bipolares (no MOSFET): conmuta en microsegundos y pierde un poco en cada transición. A 100 Hz hay 10 veces menos transiciones por segundo que a 1 kHz.

**Costo de bajar la frecuencia:** 100 Hz cae dentro del rango audible, así que el motor **zumba**, y el giro tiene un poco más de rizo. Para este reto es aceptable: lo importante es que el motor responda a todos los niveles.

## 4. Qué hacen IN1, IN2 y ENA

| IN1 | IN2 | Motor |
|---|---|---|
| 0 | 0 | STOP |
| 1 | 0 | FORWARD |
| 0 | 1 | REVERSE |
| 1 | 1 | Freno — **no se usa** |

- **`IN1` / `IN2`** cierran pares opuestos de interruptores del puente H: invierten la polaridad sobre el motor y con ello el sentido de giro. Son señales lógicas puras; no controlan velocidad.
- **`ENA`** habilita el canal A del puente. Si recibe PWM, el puente deja pasar la potencia solo durante el tiempo en alto de cada periodo: **ENA es el pin de la velocidad**.

`forward()`, `reverse()` y `stop()` encapsulan esas combinaciones, así que el resto del programa se lee como un controlador (`forward()`, `ramp_to(0, 100)`) y no como una lista de `0` y `1`. Ninguna función escribe `IN1 = IN2 = 1`.

## 5. Velocidad: porcentaje lógico y duty real

En el motor físico apareció una **zona muerta**: por debajo de **≈40 % de duty** el motor solo zumbaba sin girar. Dos causas se suman:

- **Caída del L298N.** Sus transistores bipolares se "comen" alrededor de 1.8 V típicos y hasta 3.2 V a 1 A (caída total del puente, hoja de datos del L298). Con una fuente de 5–6 V, al motor le llega bastante menos de lo que marca la fuente, y a duty bajo no alcanza.
- **Fricción estática.** Para **empezar** a girar, el motor necesita más torque del que necesita para **seguir** girando.

Si `set_speed(25)` pusiera 25 % real, la prueba de "velocidad baja" sería un motor quieto. Por eso el controlador separa dos cosas:

- **Porcentaje lógico** (0–100 %): lo que pide el programa y lo que se imprime en consola.
- **Duty real**: lo que llega a `ENA`. El 0 % sigue siendo apagado, y del 1 al 100 % lógico se reparte **solo en la zona útil**, entre `MIN_DUTY = 40 %` y 100 %:

$$D_{real} = D_{min} + (100 - D_{min}) \cdot \frac{p}{100} \qquad (p > 0)$$

```python
def duty_real(percent):
    if percent == 0:
        return 0
    real = MIN_DUTY + (100 - MIN_DUTY) * percent / 100
    return int(real * 65535 / 100)
```

| Lógico (consola) | Duty real en ENA | `duty_u16` |
|---|---|---|
| 0 % | 0 % | 0 |
| 25 % | 55 % | 36044 |
| 50 % | 70 % | 45874 |
| 75 % | 85 % | 55704 |
| 100 % | 100 % | 65535 |

Los cuatro niveles del requisito siguen siendo **cuatro velocidades distintas y crecientes**; lo que cambia es que las cuatro caen donde el motor sí se mueve. `set_speed()` conserva la saturación de la clase (`max(0, min(100, percent))`): ninguna llamada saca el duty de rango.

### Empujón de arranque (*kick*)

Aun con la zona muerta compensada, **el motor no arrancaba desde reposo**: la fricción estática pide un pico de torque que un duty intermedio no da. La solución, propuesta por el hermano de Angel: cuando la velocidad pasa de 0 a cualquier valor mayor, `set_speed()` pone **100 % durante `KICK_MS = 120 ms`** y después baja al duty que corresponde.

```python
if velocidad_actual == 0 and percent > 0:
    ENA.duty_u16(65535)
    sleep_ms(KICK_MS)
```

Una vez que el eje gira, la fricción es menor y el duty normal basta para mantenerlo. Tiene dos consecuencias que hay que decir:

- **Toda rampa que arranca desde 0 empieza con ese pulso.** La aceleración es progresiva **después** de los primeros 120 ms, no desde el primer instante. Se decidió así porque sin el pulso la rampa progresiva no existía: el motor se quedaba quieto.
- **No contradice el cambio seguro de dirección.** El pulso solo ocurre desde **reposo** (`velocidad_actual == 0`), nunca con el motor girando en sentido contrario: la regla de la sección 7 garantiza que antes de invertir ya se está en 0 % y detenido.

## 6. Cómo funciona la rampa

Un escalón de 0 a 100 % exige al motor pasar de reposo a velocidad máxima de golpe: pico de corriente y tirón mecánico. La rampa reparte ese cambio en pasos pequeños. **No es una función del motor: es un algoritmo** que genera una secuencia de velocidades en el tiempo.

```python
def ramp_to(start, end, step=10, delay_ms=100):
    if start == end:
        set_speed(end)
        return

    if start < end:
        paso = step
        etiqueta = "Acelerando"
    else:
        paso = -step            # si start > end el paso debe ser negativo
        etiqueta = "Desacelerando"

    for speed in range(start, end, paso):
        set_speed(speed)
        print(f"{etiqueta}: {speed} %")
        sleep_ms(delay_ms)

    set_speed(end)
    print(f"{etiqueta}: {end} %")
```

Una sola función sirve para **acelerar y desacelerar**: el signo del paso sale de comparar `start` con `end`. El detalle está en que `range()` **excluye** su límite: con `range(0, 75, 10)` la rampa terminaría en 70. Por eso, al salir del `for` se fija `end` explícitamente: la rampa **siempre** termina exacta, sea o no múltiplo del paso.

| Llamada (paso 10) | Secuencia |
|---|---|
| `ramp_to(0, 100)` | `0, 10, 20, …, 90, 100` |
| `ramp_to(100, 0)` | `100, 90, …, 10, 0` |
| `ramp_to(0, 75)` | `0, 10, …, 70, 75` |
| `ramp_to(75, 0)` | `75, 65, …, 5, 0` |

**Parámetros elegidos:** paso de **5 %** cada **100 ms**. Una rampa completa 0 → 100 % dura:

$$t_{rampa} = \frac{|end - start|}{step} \cdot delay = \frac{100}{5} \cdot 100\ \text{ms} = 2\ \text{s}$$

Dos segundos se ven claramente en la simulación y en el motor físico. Todos los parámetros (`PWM_FREQ`, `MIN_DUTY`, `KICK_MS`, `PASO_RAMPA`, `DELAY_RAMPA_MS`, `MANTENER_MS`, `PAUSA_INVERSION_MS`) están al inicio de `main.py` para ajustarlos sin tocar la lógica.

## 7. Cambio seguro de dirección

**No se invierte directo de FORWARD 100 % a REVERSE 100 %.** Un motor girando se comporta como generador: produce una fuerza contraelectromotriz en el sentido de su giro. Si en ese instante se invierte la polaridad, esa fuerza **se suma** a la fuente en vez de oponerse, y el resultado es un pico de corriente que calienta el L298N, más el esfuerzo mecánico de frenar y arrancar en sentido contrario al mismo tiempo.

```
      NO                          SÍ
FORWARD 100 %               FORWARD
      ↓                        ↓ desacelerar (rampa)
REVERSE 100 %               0 % + pausa
                               ↓ cambiar IN1/IN2
                            REVERSE
                               ↓ acelerar (rampa)
```

La regla no depende de que la secuencia "lo haga bien": está **dentro** de la única función autorizada para cambiar el sentido.

```python
def cambiar_direccion(nueva):
    if nueva == direccion_actual:
        return

    if velocidad_actual > 0:
        print("[SEGURIDAD] Bajando a 0 % antes de cambiar de direccion")
        ramp_to(velocidad_actual, 0, PASO_RAMPA, DELAY_RAMPA_MS)

    stop()
    sleep_ms(PAUSA_INVERSION_MS)
    ...
```

`set_speed()` guarda la velocidad en `velocidad_actual` y las funciones de dirección guardan `direccion_actual`, con constantes numéricas (`DETENIDO`, `ADELANTE`, `REVERSA`) como en la máquina de estados del examen. Así, aunque alguien pidiera `cambiar_direccion(REVERSA)` con el motor al 100 %, el controlador bajaría primero a 0 % por su cuenta.

## 8. Secuencia del controlador

Cada ciclo de `main.py` tiene dos etapas y se repite indefinidamente, para poder grabar la evidencia en cualquier momento:

**Etapa 1 — Prueba de velocidades** (requisito 4): FORWARD y rampa a **25 → 50 → 75 → 100 %**, sosteniendo 2 s cada nivel. Entre niveles también hay rampa: ningún cambio de velocidad es un escalón. Al final, rampa a 0 % y STOP.

**Etapa 2 — CHALLENGE 06** (TODO 2 del starter):

| Paso | Acción | Código |
|---|---|---|
| 1 | FORWARD | `cambiar_direccion(ADELANTE)` |
| 2 | Rampa 0 → 100 % | `ramp_to(0, 100, …)` |
| 3 | Mantener 2 s | `mantener(MANTENER_MS)` |
| 4 | Rampa 100 → 0 % | `ramp_to(100, 0, …)` |
| 5 | REVERSE (ya en 0 %) | `cambiar_direccion(REVERSA)` |
| 6 | Rampa 0 → 75 % | `ramp_to(0, 75, …)` |
| 7 | Mantener 2 s | `mantener(MANTENER_MS)` |
| 8 | Rampa 75 → 0 % | `ramp_to(75, 0, …)` |
| 9 | STOP | `stop()` |

Salida del serial (se omiten las líneas de cada paso de rampa):

```
DO 04 - SMART MOTOR CONTROLLER
Pines: GP2=IN1, GP3=IN2, GP4=ENA/PWM (100 Hz)
Zona muerta compensada: 1 % logico = 40 % real
====================
CICLO 1

--- PRUEBA DE VELOCIDADES ---
[DIRECCION] FORWARD
[NIVEL] 25 %
[MANTENER] 25 % durante 2000 ms
...
[NIVEL] 100 %
[MANTENER] 100 % durante 2000 ms
[STOP] Motor detenido

--- CHALLENGE 06 ---
[DIRECCION] FORWARD
[MANTENER] 100 % durante 2000 ms
[DIRECCION] REVERSE
[MANTENER] 75 % durante 2000 ms
[STOP] Motor detenido
```

## 9. Pruebas

La prueba se corrió en la simulación (wokwi.com, RP2040) y en la placa física (Pico 2 W, RP2350) con el mismo `main.py`. **Wokwi es evidencia de lógica; el hardware es evidencia de implementación.** En la simulación el motor es un modelo visual, así que la zona muerta, la frecuencia y el empujón no cambian nada ahí: solo tienen efecto en el motor real.

| Prueba | Resultado esperado | Wokwi | Físico |
|---|---|---|---|
| STOP | Motor detenido | ✅ | ✅ |
| FORWARD | Giro correcto | ✅ | ✅ |
| REVERSE | Giro contrario | ✅ | ✅ |
| 25 % | Velocidad baja | ✅ | ✅ |
| 50 % | Velocidad media | ✅ | ✅ |
| 75 % | Velocidad alta | ✅ | ✅ |
| 100 % | Velocidad máxima | ✅ | ✅ |
| Ramp UP | Incremento progresivo (tras el empujón de 120 ms) | ✅ | ✅ |
| Ramp DOWN | Reducción progresiva | ✅ | ✅ |
| Cambio de dirección | Pasa primero por 0 % | ✅ | ✅ |

**Verificación de la lógica fuera de la placa.** El `main.py` se corrió en la computadora con `machine.Pin` y `machine.PWM` reemplazados por objetos que registran cada escritura. Sobre dos ciclos completos: **0** cambios de `IN1/IN2` con el duty distinto de 0, **0** instantes con `IN1 = IN2 = 1`, y todos los duty dentro de $0 \dots 65535$.

## 10. Evidencias

| Evidencia | Archivo |
|---|---|
| Simulación Wokwi | [`wokwi/enlace_o_captura.md`](./wokwi/enlace_o_captura.md) · [`evidence/simulation.png`](./evidence/simulation.png) |
| Serial de la simulación | [`evidence/serial.png`](./evidence/serial.png) |
| Montaje físico | [`evidence/hardware.jpg`](./evidence/hardware.jpg) · [`evidence/hardware_video.mp4`](./evidence/hardware_video.mp4) |

## 11. Problemas encontrados

- **El motor no arrancaba a duty bajo.** Por debajo de ≈40 % solo zumbaba. Se compensó con la zona muerta: el porcentaje lógico se reparte entre 40 % y 100 % de duty real (sección 5).
- **Ni así arrancaba desde reposo.** La fricción estática pide más torque para empezar que para seguir girando. Se agregó un empujón de 120 ms al 100 % cada vez que el motor sale de 0 % (sección 5).
- **A 1 kHz el motor respondía peor que a 100 Hz.** Se bajó la frecuencia del PWM a 100 Hz después de probar; la explicación más probable está en la sección 3. El costo es un zumbido audible.
- **La rampa `0 → 75` terminaba en 70.** `range()` excluye su límite y 75 no es múltiplo del paso 10. `ramp_to()` fija `end` al salir del `for`.
- **El paso 1 del CHALLENGE no se veía en consola.** La prueba de velocidades dejaba el motor en FORWARD a 0 %, así que `cambiar_direccion(ADELANTE)` no hacía nada y no imprimía `[DIRECCION] FORWARD`. Se agregó un STOP explícito al final de la prueba de velocidades: cada etapa arranca desde el motor detenido.
- **En Wokwi el "motor" es un stepper.** La plantilla usa `chip-l298n` + `chip-stepper-esc` + `wokwi-stepper-motor` porque Wokwi no trae un motor DC con L298N nativo; lo que se ve es un indicador visual del eje, no la física de un motor DC. Por eso la zona muerta, la frecuencia y el empujón solo se pudieron ajustar en el motor real. En la simulación el ESC además toma `VMOT` de los 3.3 V de la Pico, algo que en físico **no** se hace.
- **Jumper de ENA en el L298N físico.** El módulo trae un jumper que fija ENA en alto; con él puesto el motor va siempre al 100 % y el PWM de GP4 no tiene efecto. Hay que retirarlo.

## 12. Conclusión

La velocidad del motor nunca fue un valor analógico: es **tiempo**. El microcontrolador sigue hablando en `0` y `1`, y lo único que cambia es cuánto dura cada uno. Lo que antes era "encender un LED" ahora controla una carga que la Pico no podría alimentar, porque el puente H separa la **decisión** de la **potencia**.

El motor real enseñó lo que la simulación no podía: **un porcentaje no es una velocidad**. Entre el duty que escribe la Pico y el giro del eje están la caída del L298N, la inductancia del devanado y la fricción, y por eso hicieron falta tres ajustes (frecuencia, zona muerta y empujón) que en Wokwi no cambian nada. La simulación validó la lógica; solo el hardware podía validar que esa lógica moviera algo.

Y la parte importante no es mover el motor, sino que el controlador **no deje moverlo mal**. La rampa y el cambio seguro de dirección no son pasos de la secuencia que alguien tiene que acordarse de escribir: están dentro de `ramp_to()` y `cambiar_direccion()`. Una secuencia distinta puede cambiar hacia dónde va el motor, pero ya no puede invertirlo a toda velocidad.

---

## Contenido y cómo correrlo

| Archivo / carpeta | Contenido |
|---|---|
| `main.py` | Reto 06 — controlador completo con rampas y cambio seguro |
| `wokwi/diagram.json` | Circuito de la simulación (plantilla oficial sin botones ni potenciómetro) |
| `wokwi/enlace_o_captura.md` | Enlace a la simulación publicada |
| `evidence/` | Captura de la simulación y evidencia del montaje físico |

**Simulación:** en wokwi.com, proyecto Raspberry Pi Pico + MicroPython; pegar `wokwi/diagram.json` y `main.py`.

**Hardware:**

```bash
mpremote run main.py            # correr sin instalar nada
mpremote cp main.py :main.py    # dejarlo autónomo
```
