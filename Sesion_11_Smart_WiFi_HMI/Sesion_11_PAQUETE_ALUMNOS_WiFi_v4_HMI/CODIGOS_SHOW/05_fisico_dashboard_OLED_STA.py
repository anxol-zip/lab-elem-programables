# ================================================================
# SESIÓN 11 - SHOW 5
# FÍSICO: DASHBOARD BÁSICO + OLED SSD1306
# ================================================================
#
# OBJETIVO DIDÁCTICO
# ------------------
# Integrar dos temas del curso:
#
# Wi-Fi / HTTP + I2C / OLED
#
# El navegador controla PWM y la OLED muestra:
#   IP
#   PWM actual
#   número de requests
#
# REQUIERE EN LA RAÍZ DE LA PICO:
#   /secrets.py
#   /ssd1306.py
#
# CONEXIÓN OLED:
#   SDA -> GP4
#   SCL -> GP5
#   VCC -> 3V3
#   GND -> GND
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
# 1. Wi-Fi
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
    """Conecta la Pico al Wi-Fi del salón/casa."""

    wlan = get_sta_interface()
    wlan.active(True)


    if wlan.isconnected():

        print("Wi-Fi ya conectado")
        print("IP:", wlan.ifconfig()[0])

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
    last_status = None


    while not wlan.isconnected():

        status = wlan.status()

        if status != last_status:

            print(
                "Wi-Fi status:",
                status
            )

            last_status = status


        if ticks_diff(
            ticks_ms(),
            start
        ) >= timeout_ms:

            raise RuntimeError(
                "No se pudo conectar. "
                "status={}".format(status)
            )

        sleep_ms(250)


    print("Wi-Fi conectado")
    print("IP:", wlan.ifconfig()[0])

    return wlan


# ================================================================
# 2. Servidor
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
# 3. PWM
# ================================================================

LED_PIN = 15

led = PWM(
    Pin(LED_PIN)
)

led.freq(1000)

pwm_percent = 0
request_count = 0


def set_pwm(percent):

    global pwm_percent

    percent = max(
        0,
        min(100, int(percent))
    )

    duty = int(
        percent * 65535 / 100
    )

    led.duty_u16(duty)
    pwm_percent = percent

    print(
        "PWM = {}% | duty_u16 = {}"
        .format(percent, duty)
    )


# ================================================================
# 4. OLED I2C
# ================================================================

# Creamos I2C0:
# GP4 = SDA
# GP5 = SCL
i2c = I2C(
    0,
    sda=Pin(4),
    scl=Pin(5),
    freq=400000
)


# scan() comprueba qué direcciones responden.
devices = i2c.scan()

print(
    "I2C:",
    [hex(x) for x in devices]
)


# La SSD1306 suele estar en 0x3C.
if 0x3C not in devices:

    raise RuntimeError(
        "OLED 0x3C no encontrada. "
        "Revisa SDA/SCL/VCC/GND."
    )


oled = SSD1306_I2C(
    128,
    64,
    i2c
)


def show_oled(ip):
    """Actualiza la información local del sistema."""

    oled.fill(0)

    oled.text(
        "WIFI DASHBOARD",
        5,
        0
    )

    oled.text(
        ip,
        3,
        18
    )

    oled.text(
        "PWM: {}%".format(
            pwm_percent
        ),
        3,
        36
    )

    oled.text(
        "REQ: {}".format(
            request_count
        ),
        3,
        52
    )

    # Los cambios del framebuffer se envían
    # realmente a la OLED aquí.
    oled.show()


# ================================================================
# 5. HTML + ROUTER
# ================================================================

def html_page(ip):

    return """<!doctype html>
<html>
<head>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Pico Dashboard</title>
<style>
body{{font-family:Arial;background:#0b1320;color:#eef6ff;text-align:center;padding:18px}}
.card{{max-width:560px;margin:auto;background:#142236;padding:22px;border-radius:16px}}
a{{display:inline-block;margin:6px;padding:12px 16px;border-radius:10px;background:#1b7f8c;color:white;text-decoration:none}}
code{{color:#8be9fd}}
</style>
</head>
<body>
<div class='card'>
<h2>Pico Wi-Fi Dashboard</h2>
<p>IP: <code>{ip}</code></p>
<p>PWM actual: <b>{pwm}%</b></p>
<p>Requests: {req}</p>
<p>
<a href='/pwm/0'>OFF</a>
<a href='/pwm/25'>25%</a>
<a href='/pwm/50'>50%</a>
</p>
<p>
<a href='/pwm/75'>75%</a>
<a href='/pwm/100'>100%</a>
</p>
<p><a href='/api/status'>API STATUS</a></p>
</div>
</body>
</html>""".format(
        ip=ip,
        pwm=pwm_percent,
        req=request_count
    )


def route(path, ip):

    if path == "/favicon.ico":
        return (
            "204 No Content",
            "text/plain",
            ""
        )


    if path.startswith("/pwm/"):

        try:
            value = int(
                path.split("/")[2]
            )

        except Exception:
            return (
                "400 Bad Request",
                "text/plain",
                "PWM invalido"
            )


        if value not in (
            0,
            25,
            50,
            75,
            100
        ):
            return (
                "400 Bad Request",
                "text/plain",
                "Usa 0,25,50,75,100"
            )


        set_pwm(value)

        return (
            "302 Found",
            "text/plain",
            "REDIRECT:/"
        )


    if path == "/api/status":

        body = json.dumps({
            "ip": ip,
            "pwm": pwm_percent,
            "requests": request_count,
        })

        return (
            "200 OK",
            "application/json",
            body
        )


    if path == "/":

        return (
            "200 OK",
            "text/html; charset=utf-8",
            html_page(ip)
        )


    return (
        "404 Not Found",
        "text/plain",
        "404 - Not Found"
    )


def send_dashboard_response(
    client,
    status,
    content_type,
    body
):

    if (
        status == "302 Found"
        and isinstance(body, str)
        and body.startswith("REDIRECT:")
    ):

        location = body.split(
            ":",
            1
        )[1]

        header = (
            "HTTP/1.1 303 See Other\r\n"
            "Location: {}\r\n"
            "Content-Length: 0\r\n"
            "Connection: close\r\n\r\n"
        ).format(location)

        client.write(
            header.encode()
        )

        return


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
# 6. ARRANQUE
# ================================================================

wlan = connect_wifi(
    WIFI_SSID,
    WIFI_PASSWORD
)

ip = wlan.ifconfig()[0]

set_pwm(0)

# Primera actualización de OLED.
show_oled(ip)

server = create_server(80)


print()
print(
    "Dashboard + OLED: "
    "http://{}/".format(ip)
)

last_wait = ticks_ms()


# ================================================================
# 7. LOOP HTTP
# ================================================================

while True:

    client = None

    try:
        client, remote = server.accept()

        raw = client.recv(1024)

        if not raw:
            continue


        first_line = raw.split(
            b"\r\n",
            1
        )[0].decode()


        parts = first_line.split(" ")

        path = (
            parts[1]
            if len(parts) >= 2
            else "/"
        )

        path = path.split(
            "?",
            1
        )[0]


        # Esta petición ya cuenta como request atendido.
        request_count += 1


        status, content_type, body = route(
            path,
            ip
        )


        send_dashboard_response(
            client,
            status,
            content_type,
            body
        )


        # OLED refleja el estado actualizado.
        show_oled(ip)


        print(
            "{} -> {} -> {}"
            .format(
                remote,
                path,
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
