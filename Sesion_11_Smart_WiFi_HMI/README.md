# Sesión 11 — Wi-Fi, HTTP y sockets

**Challenge 11 — Smart Wi-Fi HMI**
_Angel Rugerio Jiménez · 201720 · Lab. de Elementos Programables_

## 1. Objetivo y circuito

Una HMI **web** para la Pico 2 W conectada en modo **STA** a la misma red Wi-Fi que la laptop. Desde el navegador, un slider fija el brillo del LED de GP15 con cualquier entero de 0 a 100 % y un botón virtual alterna el LED de GP14. La OLED muestra el mismo estado de forma local, y `/api/status` lo entrega en JSON. Incluye los cuatro bonus: indicador de conexión, control de ambos LEDs, hora por NTP y lectura del ADC (sección 4).

```text
Chrome (laptop) ──Wi-Fi──► router ──Wi-Fi──► Pico 2 W :80
   GET /api/pwm?value=37 → route() → set_pwm(37) → duty_u16(24247) → LED GP15
   GET /api/led2/toggle  → route() → toggle_led2()                → LED GP14
   GET /api/all?state=1  → route() → set_all(1)                   → GP15 100 % + GP14 ON
                                    └→ show_oled() → I2C GP4/GP5 → OLED 0x3C
Potenciómetro → ADC GP26 → read_adc_percent() → /api/status + OLED
```

| Elemento | Pin | Función |
| -------- | --- | ------- |
| LED + 330 Ω | GP15 | PWM a 1 kHz (slider) |
| LED + 330 Ω | GP14 | Salida digital (TOGGLE LED 2) |
| OLED SDA | GP4 | Datos del bus I2C0 |
| OLED SCL | GP5 | Reloj del bus I2C0 |
| OLED VCC / GND | 3V3 / GND | Alimentación del módulo |
| Potenciómetro 10 kΩ | GP26 / ADC0 | Sensor analógico (3V3 / GND / señal), bonus |
| LED integrado | `"LED"` | Indicador de conexión Wi-Fi, bonus |

Archivos en la raíz de la Pico: `main.py`, `ssd1306.py` y `secrets.py`. Este último **no está en el repo**: se crea copiando [`secrets_template.py`](./secrets_template.py) con el SSID y la contraseña reales, y el [`.gitignore`](./.gitignore) lo excluye.

> **Práctica en hardware físico.** Wokwi solo permite conexiones salientes (Public Gateway), así que no sirve para abrir desde el navegador un servidor simulado.

## 2. Endpoints

| Ruta | Respuesta |
| ---- | --------- |
| `GET /` | Dashboard HTML |
| `GET /api/status` | JSON con `ip`, `pwm`, `led2`, `requests` y, por los bonus, `adc` y `time` |
| `GET /api/pwm?value=N` | `N` entero 0–100 → cambia el PWM y regresa el JSON actualizado; fuera de rango, faltante o no numérico → **400** |
| `GET /api/led2/toggle` | Alterna GP14 y regresa el JSON actualizado |
| `GET /api/all?state=1` / `state=0` | Enciende o apaga los dos LEDs (bonus); otro valor o sin `state` → **400** |
| `GET /favicon.ico` | **204** (Chrome lo pide solo) |
| cualquier otra | **404** |

```json
{"ip": "192.168.1.75", "pwm": 37, "led2": 1, "requests": 12, "adc": 42.3, "time": "14:25:39"}
```

Los errores también responden en JSON, por ejemplo `{"error": "value fuera de rango 0..100"}`. Todas las respuestas llevan `Content-Length` (medido en bytes, después de `encode()`) y `Connection: close`. Si ocurre una excepción dentro del ciclo, se imprime como `SERVER ERROR` y el servidor sigue atendiendo.

### Validación de `/api/pwm`

`set_pwm()` satura a 0–100, así que `value=150` terminaría en 100 sin avisar. Por eso la validación se hace en `route()`, **antes** de llamar a `set_pwm()`:

```python
try:
    value = int(params["value"])
except (KeyError, ValueError):
    return error_response("400 Bad Request", "value debe ser un entero 0..100")

if not 0 <= value <= 100:
    return error_response("400 Bad Request", "value fuera de rango 0..100")
```

## 3. Preguntas

**¿Qué significa STA?**
*Station*: la Pico se conecta como cliente a una red Wi-Fi que ya existe y el router le asigna una IP local. La laptop se queda en su red normal, con Internet, y llega a la Pico por esa IP. En modo AP la Pico crearía su propia red y la laptop tendría que cambiarse a ella.

**¿Qué hacen `bind()`, `listen()` y `accept()`?**
`bind(("0.0.0.0", 80))` asocia el socket al puerto 80 en cualquier interfaz de la Pico. `listen(2)` lo convierte en socket pasivo que acepta conexiones, con una cola de hasta 2 en espera. `accept()` toma la siguiente conexión y regresa **un socket nuevo** para hablar solo con ese cliente; ese es el que se cierra al terminar, mientras el servidor sigue escuchando. Con `settimeout(1)`, `accept()` se rinde cada segundo y el ciclo imprime cada 5 s que el servidor sigue vivo.

**¿Cómo se transforma 0–100 % a `duty_u16()`?**
`duty_u16()` recibe un entero de 16 bits, 0 a 65535. Primero se satura el porcentaje a 0–100 y después se escala:

$$\text{duty} = \left\lfloor \frac{p \cdot 65535}{100} \right\rfloor \qquad 37\,\% \to 24247 \qquad 100\,\% \to 65535$$

**¿Qué hace el slider HTML?**
`<input type="range" min="0" max="100">` deja elegir cualquier entero del rango. Usa dos eventos: `oninput` solo actualiza el número en la página mientras se arrastra, y `onchange` manda **una** petición `/api/pwm?value=N` al soltarlo, para no saturar a la Pico con decenas de peticiones por segundo.

**¿Por qué se usa `fetch()`?**
Para pedirle datos a la Pico desde JavaScript **sin recargar la página**: `fetch()` llama al endpoint, recibe el JSON y `updateStatus()` cambia solo los elementos que lo necesitan (slider, porcentaje, estado y punto del LED2, contador, ADC y hora). Con enlaces normales cada clic recargaría todo el HTML. También permite saber si la Pico dejó de responder: si el `fetch()` falla, la página lo marca en rojo (bonus 1).

**¿Qué diferencia existe entre HTML y JSON?**
HTML es una página para que la lea una **persona** en el navegador (`Content-Type: text/html`). JSON es una estructura de datos para que la lea **otro programa** (`application/json`): el JavaScript del dashboard, un script o cualquier otro cliente. El mismo servidor entrega los dos: `/` es HTML y `/api/*` es JSON.

**¿Cómo se integra I2C/OLED con el servidor web?**
Las dos interfaces leen las mismas variables de estado (`pwm_percent`, `led2_state`, `request_count`, más el ADC y la hora). Al arrancar, el programa escanea el bus I2C y se detiene con un mensaje claro si la OLED no está en `0x3C`, igual que en el Reto 10. Después de responder cada petición, `show_oled()` redibuja la pantalla (limpiar → dibujar → `show()`), así la OLED y `/api/status` siempre muestran lo mismo. Cuando no llegan peticiones, el timeout de 1 s de `accept()` se aprovecha para redibujarla, así que el servidor nunca se bloquea esperando a la pantalla.

## 4. Bonus

| Bonus | Cómo se implementó |
| ----- | ------------------ |
| **Indicador de conexión** | Dos lados. En la Pico, el LED integrado (`Pin("LED")`, que en la Pico W / 2 W cuelga del chip Wi-Fi) refleja `wlan.isconnected()`, revisado cada segundo. En la página, un punto verde **ONLINE** cuando la Pico responde y rojo **SIN RESPUESTA** cuando un `fetch()` falla. La página consulta `/api/status` cada 3 s para detectarlo |
| **Ambos LEDs** | `/api/all?state=1` pone el PWM al 100 % y el LED2 en ON; `state=0` apaga los dos. Botones **ALL ON** y **ALL OFF** en la página. Solo acepta `0` o `1` |
| **NTP y hora en la OLED** | Al arrancar, `ntptime.settime()` ajusta el reloj de la Pico en UTC. La hora local es UTC − 6 (Puebla no tiene horario de verano desde 2022). Aparece como `HH:MM` a la derecha del título de la OLED, como `HH:MM:SS` en la página y en `"time"` de `/api/status`. Si NTP no responde, o si el firmware no trae `ntptime`, la OLED muestra `--:--`, el JSON regresa `"time": null`, el resto del sistema sigue igual y se reintenta cada 5 min |
| **ADC real** | Potenciómetro en GP26, con la misma conversión del Reto 10 (`read_u16() * 100 / 65535`). Aparece en `/api/status` (`"adc"`), en la página y en la última línea de la OLED |

La OLED se redibuja después de cada petición y también una vez por segundo cuando no llega ninguna (aprovechando el timeout de `accept()`), para que el ADC se vea en vivo. La consulta cada 3 s de la página hace que el contador de requests suba solo mientras el dashboard esté abierto.

## 5. Resultados de la tabla de pruebas

| # | Prueba | Acción | Esperado | Resultado | Evidencia |
| - | ------ | ------ | -------- | --------- | --------- |
| 1 | Wi-Fi | Arrancar | IP local en Thonny | ⬜ | [`wifi_ip.png`](./evidence/wifi_ip.png) |
| 2 | Dashboard | Abrir `/` | Dashboard visible | ⬜ | [`dashboard.png`](./evidence/dashboard.png) |
| 3 | Slider = 0 | Mover a 0 | LED PWM apagado | ⬜ | — |
| 4 | Slider = 37 | Mover a 37 | Brillo intermedio | ⬜ | [`slider_37.png`](./evidence/slider_37.png) |
| 5 | Slider = 100 | Mover a 100 | Brillo máximo | ⬜ | [`slider_100.png`](./evidence/slider_100.png) |
| 6 | TOGGLE LED 2 | Clic | GP14 cambia ON/OFF | ⬜ | [`led2_on.png`](./evidence/led2_on.png) |
| 7 | OLED | Cambiar PWM y LED2 | Refleja PWM y LED2 | ⬜ | [`oled_status.jpg`](./evidence/oled_status.jpg) |
| 8 | `/api/status` | Abrir la ruta | JSON correcto | ⬜ | [`api_status.png`](./evidence/api_status.png) |
| 9 | PWM inválido | `/api/pwm?value=150` | Error 400 | ⬜ | — |
| 10 | Ruta desconocida | `/ruta-que-no-existe` | Error 404 | ⬜ | [`error_404.png`](./evidence/error_404.png) |
| B1 | Conexión | Abrir el dashboard / apagar la Pico | Punto verde ONLINE / rojo SIN RESPUESTA; LED integrado encendido con Wi-Fi | ⬜ | — |
| B2 | Ambos LEDs | ALL ON / ALL OFF | GP15 al 100 % y GP14 ON / los dos apagados | ⬜ | — |
| B3 | NTP | Arrancar con Internet | Hora local correcta en la OLED, la página y `/api/status` | ⬜ | — |
| B4 | ADC | Mover el potenciómetro | `adc` cambia en `/api/status`, la página y la OLED | ⬜ | — |

Pantalla de la OLED:

```text
WIFI HMI     14:25
192.168.1.75
PWM: 37%
LED2: ON
REQ: 12
ADC: 42.3%
```

El título de la OLED es `WIFI HMI` (el del TODO 3 del starter) y no `SMART WIFI HMI`, para que quepa la hora en la misma franja.

## 6. Problemas encontrados

<!-- Llenar después de las pruebas en físico: qué falló y cómo se resolvió. -->

## 7. Conclusión

<!-- Conclusión personal. -->

## Evidencias y cómo correrlo

| Evidencia | Archivo |
| --------- | ------- |
| IP en Thonny | [`evidence/wifi_ip.png`](./evidence/wifi_ip.png) |
| Dashboard | [`evidence/dashboard.png`](./evidence/dashboard.png) |
| Slider en 37 % | [`evidence/slider_37.png`](./evidence/slider_37.png) |
| Slider en 100 % | [`evidence/slider_100.png`](./evidence/slider_100.png) |
| LED2 encendido | [`evidence/led2_on.png`](./evidence/led2_on.png) |
| OLED con el estado | [`evidence/oled_status.jpg`](./evidence/oled_status.jpg) |
| `/api/status` | [`evidence/api_status.png`](./evidence/api_status.png) |
| Error 404 | [`evidence/error_404.png`](./evidence/error_404.png) |

**Pico física (Pico 2 W + MicroPython):**

1. Armar el circuito de la sección 1. Para el bonus del ADC, el potenciómetro va a 3V3, GND y GP26.
2. Copiar `secrets_template.py`, poner el SSID y la contraseña reales y guardarlo en la **raíz** de la Pico con el nombre exacto `secrets.py` (Thonny: *Archivo → Guardar como → Raspberry Pi Pico*).
3. Guardar `ssd1306.py` y `main.py` en la raíz de la Pico.
4. Ejecutar `main.py`. Thonny imprime el scan I2C, la IP, el resultado de NTP y la URL: `Abre: http://192.168.x.x/`.
5. Abrir esa URL **en la laptop conectada a la misma red**, escribiendo `http://` explícitamente.

La red tiene que tener 2.4 GHz y no puede ser una red de invitados ni institucional con aislamiento de clientes; un hotspot donde se conecten la laptop y la Pico funciona.

**Si algo no abre:**

| Síntoma | Revisar |
| ------- | ------- |
| `RuntimeError: OLED 0x3c no detectada` | Cableado SDA/SCL/VCC/GND; si el scan muestra `0x3d`, cambiar `OLED_ADDR` |
| `Timeout Wi-Fi` | SSID/contraseña en `secrets.py`, red de 2.4 GHz |
| Hay IP pero la página no abre | Misma red, sin VPN, `http://` y no `https://` |
| La hora sale `--:--` | NTP no respondió (la red bloquea NTP o no hay Internet); el resto funciona igual y se reintenta cada 5 min |

## Estructura

```text
Sesion_11_Smart_WiFi_HMI/
├── main.py
├── ssd1306.py
├── secrets_template.py
├── .gitignore            ← excluye secrets.py
├── README.md
└── evidence/
```
