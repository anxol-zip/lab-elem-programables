# DO11 — Smart Wi-Fi HMI final

## Hardware

- Pico W / Pico 2 W
- LED PWM en GP15
- LED 2 digital en GP14
- OLED SSD1306 I2C:
  - SDA -> GP4
  - SCL -> GP5
  - VCC -> 3V3
  - GND -> GND

Si tu shield usa otros pines, cambia las constantes/pines al inicio.

## Archivos que deben existir en la raíz de la Pico

```text
/
├── secrets.py
├── ssd1306.py
└── main.py
```

`secrets.py` NO se sube a GitHub.

## Resultado final

El navegador debe mostrar:

1. Slider de 0 a 100 % para controlar el LED PWM.
2. Valor numérico actual del PWM.
3. Botón virtual `TOGGLE LED 2`.
4. Estado visual ON/OFF del LED2.
5. Contador de requests.
6. Botón para refrescar estado.

La OLED debe mostrar:

```text
SMART WIFI HMI
192.168.x.x
PWM: 73%
LED2: ON
REQ: 15
```

## Endpoints

```text
GET /
GET /api/status
GET /api/pwm?value=0..100
GET /api/led2/toggle
```

## Por qué el slider usa `onchange`

Mientras arrastras, `oninput` solo actualiza el número en el navegador.

Cuando sueltas el slider, `onchange` envía la petición a la Pico.

Así evitamos generar decenas de requests por segundo mientras se mueve el control.
