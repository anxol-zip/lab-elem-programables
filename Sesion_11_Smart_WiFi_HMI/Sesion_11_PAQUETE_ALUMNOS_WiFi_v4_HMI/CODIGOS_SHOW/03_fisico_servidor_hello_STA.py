# ================================================================
# SESIÓN 11 - SHOW 3
# FÍSICO: SERVIDOR HTTP MÍNIMO "HELLO PICO"
# ================================================================
#
# OBJETIVO DIDÁCTICO
# ------------------
# Esta prueba separa dos problemas:
#
# 1) ¿La Pico entra al Wi-Fi?        -> connect_wifi()
# 2) ¿La laptop puede llegar a Pico? -> servidor HTTP
#
# NO añadimos PWM, OLED ni dashboard todavía.
# Primero demostramos el servidor más pequeño posible.
# ================================================================

import network
import socket

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
# BLOQUE A - CONEXIÓN Wi-Fi
# ================================================================

def get_sta_interface():
    """Devuelve la interfaz Wi-Fi en modo Station."""

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
    """Conecta la Pico al router y devuelve wlan."""

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
            print("Wi-Fi status:", status)
            last_status = status


        if ticks_diff(
            ticks_ms(),
            start
        ) >= timeout_ms:

            raise RuntimeError(
                "No se pudo conectar al Wi-Fi. "
                "status={}".format(status)
            )

        sleep_ms(250)


    print("Wi-Fi conectado")
    print("IP:", wlan.ifconfig()[0])

    return wlan


# ================================================================
# BLOQUE B - CREAR SERVIDOR TCP EN PUERTO 80
# ================================================================

def create_server(port=80):
    """
    Crea un socket servidor.

    0.0.0.0 significa:
    escuchar en cualquier interfaz local de la Pico.

    Puerto 80 = HTTP.
    """

    addr = socket.getaddrinfo(
        "0.0.0.0",
        port
    )[0][-1]

    server = socket.socket()


    # Permite reutilizar el puerto después de reiniciar.
    try:
        server.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )
    except Exception:
        pass


    # Asociamos el socket a la IP/puerto local.
    server.bind(addr)

    # Hasta 2 conexiones pendientes.
    server.listen(2)


    # MUY IMPORTANTE:
    # accept() normalmente espera indefinidamente.
    # Con timeout regresa cada segundo para que
    # podamos imprimir "Servidor vivo".
    try:
        server.settimeout(1)
    except Exception:
        pass


    return server


# ================================================================
# BLOQUE C - RESPUESTA HTTP
# ================================================================

def send_response(
    client,
    body,
    content_type="text/html; charset=utf-8",
    status="200 OK"
):
    """
    Construye una respuesta HTTP correcta.

    Content-Length:
    indica cuántos bytes contiene el cuerpo.

    Connection: close:
    le dice al navegador que cerraremos la conexión
    después de responder.
    """

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
# PROGRAMA PRINCIPAL
# ================================================================

# 1) Entrar a TU Wi-Fi.
wlan = connect_wifi(
    WIFI_SSID,
    WIFI_PASSWORD
)

ip = wlan.ifconfig()[0]


# 2) Crear servidor.
server = create_server(80)


print()
print("========================================")
print(" SERVIDOR HELLO LISTO")
print("========================================")
print("1) NO cambies el Wi-Fi de la laptop.")
print("2) Abre exactamente:")
print("   http://{}/".format(ip))
print("3) Usa http://, NO https://")
print()


last_wait = ticks_ms()


# ================================================================
# LOOP DEL SERVIDOR
# ================================================================

while True:

    client = None

    try:
        # Esperamos una conexión del navegador.
        client, remote = server.accept()


        # Leemos la petición HTTP.
        raw = client.recv(1024)

        # Primera línea esperada:
        # GET / HTTP/1.1
        first_line = raw.split(
            b"\r\n",
            1
        )[0]

        print(
            "Peticion:",
            first_line
        )


        # Página HTML mínima.
        body = (
            "<!doctype html>"
            "<html>"
            "<body>"
            "<h1>Hello Pico</h1>"
            "<p>Servidor HTTP funcionando.</p>"
            "<p>IP: {}</p>"
            "</body>"
            "</html>"
        ).format(ip)


        send_response(
            client,
            body
        )

        print(
            "Respuesta enviada a:",
            remote
        )


    except OSError:
        # Normalmente será el timeout de accept().
        # NO significa que el servidor falló.
        if ticks_diff(
            ticks_ms(),
            last_wait
        ) >= 5000:

            print(
                "Esperando navegador en "
                "http://{}/ ...".format(ip)
            )

            last_wait = ticks_ms()


    except Exception as exc:
        print(
            "SERVER ERROR:",
            exc
        )


    finally:
        # Cada petición usa una conexión corta.
        if client:

            try:
                client.close()
            except Exception:
                pass
