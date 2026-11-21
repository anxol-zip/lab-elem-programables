# ================================================================
# SESIÓN 11 - SHOW 4
# FÍSICO: DASHBOARD BÁSICO + PWM
# ================================================================
#
# OBJETIVO DIDÁCTICO
# ------------------
# Pasar de "Hello Pico" a un servidor que:
#
#   navegador -> ruta HTTP -> función -> hardware
#
# Este SHOW usa botones fijos (0, 25, 50, 75, 100 %).
# El DO11 final reemplazará esos botones por un SLIDER 0..100.
# ================================================================

import network
import socket
import json

from machine import Pin, PWM

from time import (
    sleep_ms,
    ticks_ms,
    ticks_diff
)

from secrets import (
    WIFI_SSID,
    WIFI_PASSWORD
)


# ================================================================
# 1. Wi-Fi
# ================================================================

def get_sta_interface():
    """Interfaz Wi-Fi en modo Station."""

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
    """Conecta la Pico al mismo Wi-Fi que la laptop."""

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
    """Crea un servidor TCP/HTTP en el puerto indicado."""

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
# 3. Hardware PWM
# ================================================================

LED_PIN = 15

led = PWM(
    Pin(LED_PIN)
)

# 1 kHz es suficiente para que el parpadeo no sea visible.
led.freq(1000)


# Variables de estado del sistema.
pwm_percent = 0
request_count = 0


def set_pwm(percent):
    """
    Convierte un porcentaje 0..100 al rango duty_u16 0..65535.
    """

    global pwm_percent


    # Protección: nunca dejamos salir del rango.
    percent = max(
        0,
        min(100, int(percent))
    )


    # Regla de tres:
    #   0 %   -> 0
    #   100 % -> 65535
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
# 4. HTML
# ================================================================

def html_page(ip):
    """
    Construye la página principal.

    En este SHOW usamos botones fijos.
    """

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

<p>
<a href='/api/status'>API STATUS</a>
</p>

</div>
</body>
</html>""".format(
        ip=ip,
        pwm=pwm_percent,
        req=request_count
    )


# ================================================================
# 5. Router de URLs
# ================================================================

def route(path, ip):
    """
    Decide qué hacer según la ruta pedida por Chrome.
    """

    # Chrome suele pedir favicon automáticamente.
    if path == "/favicon.ico":
        return (
            "204 No Content",
            "text/plain",
            ""
        )


    # Ejemplo:
    # /pwm/50
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

        # Después de cambiar PWM regresaremos a "/".
        return (
            "302 Found",
            "text/plain",
            "REDIRECT:/"
        )


    # API máquina-a-máquina.
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


    # Página principal.
    if path == "/":

        return (
            "200 OK",
            "text/html; charset=utf-8",
            html_page(ip)
        )


    # Cualquier ruta no definida.
    return (
        "404 Not Found",
        "text/plain",
        "404 - Not Found"
    )


# ================================================================
# 6. Enviar respuesta
# ================================================================

def send_dashboard_response(
    client,
    status,
    content_type,
    body
):
    """Envía respuesta normal o redirección HTTP."""

    # Caso especial:
    # después de /pwm/N regresamos al dashboard.
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
            "Connection: close\r\n"
            "\r\n"
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
# 7. Arranque
# ================================================================

wlan = connect_wifi(
    WIFI_SSID,
    WIFI_PASSWORD
)

ip = wlan.ifconfig()[0]

# Estado inicial.
set_pwm(0)

server = create_server(80)


print()
print("========================================")
print(" DASHBOARD BÁSICO LISTO")
print("========================================")
print("Laptop y Pico siguen en el MISMO Wi-Fi.")
print("Abre: http://{}/".format(ip))
print()


last_wait = ticks_ms()


# ================================================================
# 8. Loop HTTP
# ================================================================

while True:

    client = None

    try:
        # Esperar navegador.
        client, remote = server.accept()


        # Leer petición.
        raw = client.recv(1024)

        if not raw:
            continue


        # Primera línea:
        # GET /pwm/50 HTTP/1.1
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

        # Eliminamos query string si existiera.
        path = path.split(
            "?",
            1
        )[0]


        # Contador de peticiones.
        request_count += 1


        # Procesar ruta.
        status, content_type, body = route(
            path,
            ip
        )


        # Responder.
        send_dashboard_response(
            client,
            status,
            content_type,
            body
        )


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
