# SESION 11 v3 — Wi-Fi, HTTP y sockets SIN CONFUSIONES

Esta version usa una sola estrategia principal:

- **Wokwi:** la Pico 2 W funciona como CLIENTE HTTP usando `Wokwi-GUEST`.
- **Hardware fisico:** la Pico W/Pico 2 W se conecta como **STA a tu Wi-Fi normal** y publica un servidor/dashboard local.

## Lo mas importante
**No tienes que desconectar tu laptop del Internet.**

```text
                 ROUTER / WIFI DE CASA
                    /              \
                   /                \
            LAPTOP / PC         PICO W / PICO 2 W
            Teams + Chrome       servidor HTTP
                   \                /
                    \--- red local-/
```

## Antes de la clase: prueba exactamente en este orden

### A. Wokwi
1. Abre `WOKWI_TEMPLATE/`.
2. Copia `diagram.json` y `main.py` en un proyecto Pico 2 W MicroPython.
3. Ejecuta.
4. Debes ver: `HTTP STATUS: HTTP/1.1 200 OK`.
5. El LED verde debe encenderse.

No intentes abrir desde Chrome un servidor que corre dentro de Wokwi: para conexiones entrantes Wokwi requiere Private IoT Gateway. En esta sesion Wokwi se usa solo como **cliente**.

### B. Pico fisica
#### PASO 1 — crear `secrets.py`
1. Abre `secrets_template.py`.
2. Escribe tu SSID y password.
3. Guarda una copia con nombre **`secrets.py`**.
4. En Thonny elige **Archivo > Guardar como > Raspberry Pi Pico**.
5. Guarda `secrets.py` en la raiz de la Pico.

Ejemplo:
```python
WIFI_SSID = "MiCasa"
WIFI_PASSWORD = "mi-password"
```

**No subas `secrets.py` a GitHub.**

#### PASO 2 — solo Wi-Fi
Ejecuta `CODIGOS_SHOW/02_fisico_wifi_STA.py`.

Debes ver:
```text
Wi-Fi conectado
IP: 192.168.x.x
SHOW 2 OK
```

Si esto falla, NO sigas al servidor.

#### PASO 3 — servidor minimo
Ejecuta `CODIGOS_SHOW/03_fisico_servidor_hello_STA.py`.

Thonny imprimira una URL, por ejemplo:
```text
http://192.168.1.75/
```

Abrela EN LA MISMA LAPTOP, sin cambiar de Wi-Fi.
Debes ver `Hello Pico`.

#### PASO 4 — dashboard
Solo despues de que Hello Pico funcione, ejecuta:
`CODIGOS_SHOW/04_fisico_dashboard_STA.py`.

Prueba OFF, 25 %, 50 %, 75 %, 100 % y API STATUS.

#### PASO 5 — OLED opcional
Si ya tienes la OLED conectada, guarda tambien `ssd1306.py` en la raiz de la Pico y ejecuta:
`CODIGOS_SHOW/05_fisico_dashboard_OLED_STA.py`.

## Archivos que deben existir en la Pico
Para SHOW 2/3/4:
```text
/
└── secrets.py
```

Para SHOW 5 con OLED:
```text
/
├── secrets.py
└── ssd1306.py
```

Los SHOW pueden ejecutarse desde el editor de Thonny; no es obligatorio guardarlos como `main.py` durante la clase.

## Si el servidor no abre
Revisa en este orden:
1. ¿SHOW 2 obtuvo una IP?
2. ¿Laptop y Pico estan en la misma red normal, no una red Guest?
3. Escribe `http://IP/` completo, no `https://`.
4. Desactiva temporalmente VPN/Surfshark si bloquea acceso LAN.
5. Evita una red institucional con aislamiento entre clientes; usa tu Wi-Fi de casa o un hotspot donde laptop y Pico se conecten al mismo hotspot.
6. Primero prueba SHOW 3. Si `Hello Pico` no abre, el problema es red; no es el dashboard.

## Por que `accept()` parece esperar
Un servidor necesita esperar clientes. En v3 el socket tiene timeout corto y la consola imprime periodicamente `Esperando navegador...`, para que sea evidente que el programa sigue vivo.
