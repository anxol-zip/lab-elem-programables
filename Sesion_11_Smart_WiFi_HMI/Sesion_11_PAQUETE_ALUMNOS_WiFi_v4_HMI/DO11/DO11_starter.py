# ================================================================
# DO11 - STARTER
# SMART Wi-Fi HMI FINAL
# ================================================================
#
# RETO
# ----
# Construir una HMI web donde:
#
# 1) Un SLIDER web 0..100 controle el brillo del LED PWM (GP15).
# 2) Un BOTÓN VIRTUAL cambie ON/OFF un segundo LED (GP14).
# 3) La OLED I2C muestre:
#       IP
#       PWM
#       LED2
#       número de requests
# 4) /api/status entregue esos datos en JSON.
#
# ARCHIVOS EN LA RAÍZ DE LA PICO
# ------------------------------
# /secrets.py
# /ssd1306.py
#
# HARDWARE
# --------
# GP15 -> LED PWM
# GP14 -> LED 2 digital
# GP4  -> OLED SDA
# GP5  -> OLED SCL
# ================================================================

import network
import socket
import json

from machine import (
    Pin,
    PWM,
    I2C
)

from time import (
    sleep_ms,
    ticks_ms,
    ticks_diff
)

from secrets import (
    WIFI_SSID,
    WIFI_PASSWORD
)

from ssd1306 import SSD1306_I2C


# ================================================================
# BLOQUE 1 - Wi-Fi
# YA ESTÁ RESUELTO
# ================================================================

def get_sta_interface():

    try:
        return network.WLAN(
            network.WLAN.IF_STA
        )

    except AttributeError:
        return network.WLAN(
            network.STA_IF
        )


def connect_wifi(
    ssid,
    password,
    timeout_ms=20000
):

    wlan = get_sta_interface()
    wlan.active(True)


    if wlan.isconnected():
        return wlan


    try:
        wlan.disconnect()
        sleep_ms(200)
    except Exception:
        pass


    print("Conectando a:", ssid)

    wlan.connect(
        ssid,
        password
    )

    start = ticks_ms()


    while not wlan.isconnected():

        if ticks_diff(
            ticks_ms(),
            start
        ) >= timeout_ms:

            raise RuntimeError(
                "Timeout Wi-Fi"
            )

        sleep_ms(250)


    print(
        "Wi-Fi conectado | IP:",
        wlan.ifconfig()[0]
    )

    return wlan


# ================================================================
# BLOQUE 2 - SERVIDOR
# YA ESTÁ RESUELTO
# ================================================================

def create_server(port=80):

    addr = socket.getaddrinfo(
        "0.0.0.0",
        port
    )[0][-1]

    server = socket.socket()


    try:
        server.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )
    except Exception:
        pass


    server.bind(addr)
    server.listen(2)


    try:
        server.settimeout(1)
    except Exception:
        pass


    return server


# ================================================================
# BLOQUE 3 - HARDWARE
# ================================================================

# LED 1: brillo variable.
led_pwm = PWM(
    Pin(15)
)

led_pwm.freq(1000)


# LED 2: solo ON / OFF.
led2 = Pin(
    14,
    Pin.OUT
)


# OLED de la sesión I2C.
i2c = I2C(
    0,
    sda=Pin(4),
    scl=Pin(5),
    freq=400000
)

devices = i2c.scan()

if 0x3C not in devices:

    raise RuntimeError(
        "OLED 0x3C no encontrada"
    )


oled = SSD1306_I2C(
    128,
    64,
    i2c
)


# Estado del sistema.
pwm_percent = 0
led2_state = 0
request_count = 0


# ================================================================
# TODO 1 - PWM
# ================================================================

def set_pwm(percent):

    global pwm_percent

    # TODO:
    # 1) limitar percent a 0..100
    # 2) convertir a 0..65535
    # 3) llamar led_pwm.duty_u16(...)
    # 4) guardar pwm_percent
    pass


# ================================================================
# TODO 2 - LED 2
# ================================================================

def toggle_led2():

    global led2_state

    # TODO:
    # cambiar 0 -> 1
    # cambiar 1 -> 0
    # actualizar led2.value(...)
    pass


# ================================================================
# TODO 3 - OLED
# ================================================================

def show_oled(ip):

    # TODO:
    # Mostrar, como mínimo:
    #
    # WIFI HMI
    # IP
    # PWM: XX%
    # LED2: ON/OFF
    # REQ: N
    pass


# ================================================================
# BLOQUE 4 - ESTADO JSON
# ================================================================

def status_dict(ip):

    return {
        "ip": ip,
        "pwm": pwm_percent,
        "led2": led2_state,
        "requests": request_count,
    }


# ================================================================
# BLOQUE 5 - HTML
# YA ESTÁ DADO: ustedes implementan las rutas
# ================================================================

HTML_TEMPLATE = """<!doctype html>
<html>
<head>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Pico Smart HMI</title>

<style>
body {
    font-family: Arial, sans-serif;
    background: #08131f;
    color: #eef7ff;
    margin: 0;
    padding: 18px;
}

.card {
    max-width: 620px;
    margin: auto;
    background: #13263a;
    padding: 24px;
    border-radius: 18px;
}

h1 {
    margin-top: 0;
    color: #62e6f0;
}

.panel {
    background: #0d1d2d;
    padding: 16px;
    margin: 14px 0;
    border-radius: 14px;
}

input[type=range] {
    width: 100%;
}

button {
    padding: 12px 18px;
    border: 0;
    border-radius: 10px;
    background: #1b9aaa;
    color: white;
    font-weight: bold;
    cursor: pointer;
}

.dot {
    display: inline-block;
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: #666;
}

code {
    color: #8be9fd;
}
</style>
</head>

<body>
<div class='card'>

<h1>Pico Smart HMI</h1>

<p>
IP:
<code>__IP__</code>
</p>


<div class='panel'>

<h3>LED PWM - GP15</h3>

<p>
Valor:
<b id='pwmValue'>__PWM__%</b>
</p>

<input
    id='pwmSlider'
    type='range'
    min='0'
    max='100'
    value='__PWM__'
    oninput='previewPWM(this.value)'
    onchange='applyPWM(this.value)'
>

</div>


<div class='panel'>

<h3>LED 2 - GP14</h3>

<p>
<span
    id='led2Dot'
    class='dot'>
</span>

Estado:
<b id='led2State'>__LED2_TEXT__</b>
</p>

<button onclick='toggleLed2()'>
TOGGLE LED 2
</button>

</div>


<div class='panel'>

<p>
Requests:
<b id='requestValue'>__REQ__</b>
</p>

<button onclick='refreshStatus()'>
REFRESH STATUS
</button>

</div>


<script>

function previewPWM(value) {

    document.getElementById(
        'pwmValue'
    ).textContent = value + '%';
}


function updateStatus(data) {

    document.getElementById(
        'pwmSlider'
    ).value = data.pwm;

    document.getElementById(
        'pwmValue'
    ).textContent = data.pwm + '%';

    document.getElementById(
        'led2State'
    ).textContent = (
        data.led2 ? 'ON' : 'OFF'
    );

    document.getElementById(
        'led2Dot'
    ).style.background = (
        data.led2 ? '#43e97b' : '#666'
    );

    document.getElementById(
        'requestValue'
    ).textContent = data.requests;
}


function applyPWM(value) {

    fetch(
        '/api/pwm?value=' + value,
        {cache:'no-store'}
    )
    .then(function(response) {
        return response.json();
    })
    .then(updateStatus);
}


function toggleLed2() {

    fetch(
        '/api/led2/toggle',
        {cache:'no-store'}
    )
    .then(function(response) {
        return response.json();
    })
    .then(updateStatus);
}


function refreshStatus() {

    fetch(
        '/api/status',
        {cache:'no-store'}
    )
    .then(function(response) {
        return response.json();
    })
    .then(updateStatus);
}

refreshStatus();

</script>

</div>
</body>
</html>
"""


def html_page(ip):

    # Sustituimos únicamente valores iniciales.
    # El JavaScript actualizará el resto sin recargar.
    page = HTML_TEMPLATE

    page = page.replace(
        "__IP__",
        ip
    )

    page = page.replace(
        "__PWM__",
        str(pwm_percent)
    )

    page = page.replace(
        "__REQ__",
        str(request_count)
    )

    page = page.replace(
        "__LED2_TEXT__",
        "ON" if led2_state else "OFF"
    )

    return page


# ================================================================
# FUNCIÓN AUXILIAR - QUERY STRING
# YA ESTÁ RESUELTA
# ================================================================

def split_target(target):
    """
    Convierte:
      /api/pwm?value=73

    en:
      path   = /api/pwm
      params = {"value": "73"}
    """

    if "?" in target:

        path, query = target.split(
            "?",
            1
        )

    else:

        path = target
        query = ""


    params = {}


    for item in query.split("&"):

        if "=" not in item:
            continue

        key, value = item.split(
            "=",
            1
        )

        params[key] = value


    return path, params


# ================================================================
# TODO 4 - ROUTER
# ================================================================

def route(target, ip):

    path, params = split_target(
        target
    )


    # TODO:
    #
    # /favicon.ico
    #     -> 204
    #
    # /
    #     -> HTML
    #
    # /api/status
    #     -> JSON de status_dict(ip)
    #
    # /api/pwm?value=N
    #     -> validar N entre 0 y 100
    #     -> set_pwm(N)
    #     -> JSON actualizado
    #
    # /api/led2/toggle
    #     -> toggle_led2()
    #     -> JSON actualizado
    #
    # cualquier otra ruta
    #     -> 404

    return (
        "501 Not Implemented",
        "text/plain",
        "TODO"
    )


# ================================================================
# BLOQUE 6 - RESPUESTA HTTP
# YA ESTÁ RESUELTO
# ================================================================

def send_response(
    client,
    status,
    content_type,
    body
):

    if isinstance(body, str):
        body = body.encode()


    header = (
        "HTTP/1.1 {}\r\n"
        "Content-Type: {}\r\n"
        "Content-Length: {}\r\n"
        "Connection: close\r\n"
        "Cache-Control: no-store\r\n"
        "\r\n"
    ).format(
        status,
        content_type,
        len(body)
    )


    client.write(
        header.encode()
    )

    if body:
        client.write(body)


# ================================================================
# BLOQUE 7 - ARRANQUE
# ================================================================

wlan = connect_wifi(
    WIFI_SSID,
    WIFI_PASSWORD
)

ip = wlan.ifconfig()[0]


# Estado inicial.
led2.off()

# TODO: cuando set_pwm esté terminado,
# descomenta:
# set_pwm(0)

# TODO: cuando show_oled esté terminado,
# descomenta:
# show_oled(ip)


server = create_server(80)


print()
print("====================================")
print(" DO11 - SMART Wi-Fi HMI")
print("====================================")
print("Abre:")
print(
    "http://{}/".format(ip)
)
print()


last_wait = ticks_ms()


# ================================================================
# BLOQUE 8 - LOOP HTTP
# YA ESTÁ RESUELTO
# ================================================================

while True:

    client = None

    try:

        client, remote = server.accept()

        raw = client.recv(2048)

        if not raw:
            continue


        first_line = raw.split(
            b"\r\n",
            1
        )[0].decode()


        parts = first_line.split(" ")

        target = (
            parts[1]
            if len(parts) >= 2
            else "/"
        )


        request_count += 1


        status, content_type, body = route(
            target,
            ip
        )


        send_response(
            client,
            status,
            content_type,
            body
        )


        # TODO:
        # cuando show_oled esté terminado,
        # llama show_oled(ip) aquí.


        print(
            "{} -> {} -> {}"
            .format(
                remote,
                target,
                status
            )
        )


    except OSError:

        if ticks_diff(
            ticks_ms(),
            last_wait
        ) >= 5000:

            print(
                "Servidor vivo: "
                "http://{}/".format(ip)
            )

            last_wait = ticks_ms()


    except Exception as exc:

        print(
            "SERVER ERROR:",
            exc
        )


    finally:

        if client:

            try:
                client.close()
            except Exception:
                pass
