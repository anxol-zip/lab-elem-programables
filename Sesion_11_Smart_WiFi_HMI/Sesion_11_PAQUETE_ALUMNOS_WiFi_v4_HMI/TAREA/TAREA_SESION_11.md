# TAREA SESIÓN 11 — Smart Wi-Fi HMI FINAL

## Objetivo

Construir una interfaz HMI web para una Pico W/Pico 2 W conectada en **modo STA** a la misma red que la laptop.

El sistema debe integrar **Wi-Fi + HTTP + PWM + salida digital + OLED I2C**.

---

## Requisitos obligatorios

### 1. Wi-Fi

- La Pico debe conectarse al Wi-Fi en modo STA.
- Debe imprimir su IP local.
- `secrets.py` no debe subirse a GitHub.

### 2. Slider PWM

El dashboard debe incluir un control:

```html
<input type="range" min="0" max="100">
```

Debe permitir seleccionar **cualquier valor entero entre 0 y 100 %**.

Ejemplos que deben funcionar:

```text
7 %
37 %
63 %
91 %
100 %
```

No se acepta limitarlo únicamente a 0/25/50/75/100.

El slider controla el brillo del LED de GP15 mediante `duty_u16()`.

### 3. Segundo LED + botón virtual

El dashboard debe incluir un botón:

```text
TOGGLE LED 2
```

Cada clic debe alternar el LED de GP14:

```text
OFF -> ON -> OFF -> ON ...
```

La página debe mostrar visualmente su estado.

### 4. OLED I2C

Usar la OLED SSD1306 de la sesión anterior:

```text
GP4 -> SDA
GP5 -> SCL
```

Debe mostrar como mínimo:

```text
IP
PWM actual
LED2 ON/OFF
número de requests
```

### 5. API JSON

`/api/status` debe devolver al menos:

```json
{
  "ip": "192.168.1.75",
  "pwm": 63,
  "led2": 1,
  "requests": 12
}
```

### 6. Endpoints

La solución debe implementar:

```text
/
 /api/status
 /api/pwm?value=N
 /api/led2/toggle
```

donde `N` debe estar entre 0 y 100.

### 7. Robustez HTTP

- `Content-Length`
- `Connection: close`
- ruta desconocida -> 404
- valor PWM inválido -> 400
- el servidor no debe detenerse después de un error

---

## Pruebas mínimas

| Prueba | Resultado |
|---|---|
| Abrir `/` | Dashboard visible |
| Slider = 0 | LED PWM apagado |
| Slider = 37 | Brillo intermedio |
| Slider = 100 | Brillo máximo |
| TOGGLE LED 2 | GP14 cambia ON/OFF |
| OLED | refleja PWM y LED2 |
| `/api/status` | JSON correcto |
| `/api/pwm?value=150` | error 400 |
| `/ruta-que-no-existe` | error 404 |

---

## Entrega GitHub

```text
Sesion_11_Smart_WiFi_HMI/
├── main.py
├── ssd1306.py
├── secrets_template.py
├── .gitignore
├── README.md
└── evidence/
    ├── wifi_ip.png
    ├── dashboard.png
    ├── slider_37.png
    ├── slider_100.png
    ├── led2_on.png
    ├── oled_status.jpg
    ├── api_status.png
    └── error_404.png
```

## README

Explicar brevemente:

1. ¿Qué significa STA?
2. ¿Qué hacen `bind()`, `listen()` y `accept()`?
3. ¿Cómo se transforma 0–100 % a `duty_u16()`?
4. ¿Qué hace el slider HTML?
5. ¿Por qué se usa `fetch()`?
6. ¿Qué diferencia existe entre HTML y JSON?
7. ¿Cómo se integra I2C/OLED con el servidor web?
8. Tabla PASS/FAIL.

## Bonus

- indicador visual adicional para conexión;
- endpoint para encender/apagar ambos LEDs;
- NTP y hora en OLED;
- ADC real incluido en `/api/status`.
