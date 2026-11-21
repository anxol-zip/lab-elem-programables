# ================================================================
# SESIÓN 11 - SHOW 1
# WOKWI: CLIENTE HTTP SIMPLE
# ================================================================
#
# OBJETIVO DIDÁCTICO
# ------------------
# Seguir el camino completo:
#
# Wi-Fi -> DNS -> TCP -> HTTP -> respuesta "200 OK"
#
# El LED de GP15 se enciende cuando recibimos una respuesta HTTP 200.
# ================================================================

import network
import socket

from machine import Pin
from time import sleep_ms, ticks_ms, ticks_diff


def get_sta_interface():
    """Devuelve la interfaz Wi-Fi en modo Station (STA)."""
    try:
        return network.WLAN(network.WLAN.IF_STA)
    except AttributeError:
        return network.WLAN(network.STA_IF)


# ------------------------------------------------
# PASO 1. LED indicador
# ------------------------------------------------
# Este LED NO controla Internet.
# Solo será una evidencia visual de que HTTP respondió correctamente.
led = Pin(15, Pin.OUT)
led.off()


# ------------------------------------------------
# PASO 2. Conexión Wi-Fi
# ------------------------------------------------
wlan = get_sta_interface()
wlan.active(True)
wlan.connect("Wokwi-GUEST", "")

print("1) Conectando a Wokwi-GUEST", end="")

start = ticks_ms()

while not wlan.isconnected():

    if ticks_diff(ticks_ms(), start) > 15000:
        raise RuntimeError("Timeout Wi-Fi")

    print(".", end="")
    sleep_ms(250)

print()
print("   IP:", wlan.ifconfig()[0])


# ------------------------------------------------
# PASO 3. DNS
# ------------------------------------------------
# Nosotros conocemos un nombre: example.com
# DNS lo traduce a una dirección IP.
HOST = "example.com"
PORT = 80

print("2) Resolviendo DNS:", HOST)

addr = socket.getaddrinfo(
    HOST,
    PORT
)[0][-1]

print("   Destino:", addr)


# ------------------------------------------------
# PASO 4. Crear un socket TCP
# ------------------------------------------------
s = socket.socket()

try:
    try:
        # El timeout evita esperar para siempre.
        s.settimeout(8)
    except Exception:
        pass

    print("3) Abriendo TCP...")

    # Aquí comienza la conexión con el servidor remoto.
    s.connect(addr)


    # ------------------------------------------------
    # PASO 5. Construir una petición HTTP GET
    # ------------------------------------------------
    request = (
        "GET / HTTP/1.1\r\n"
        "Host: example.com\r\n"
        "Connection: close\r\n"
        "\r\n"
    )

    print("4) Enviando GET...")

    # En sockets bloqueantes MicroPython permite usar write().
    s.write(request.encode())


    # ------------------------------------------------
    # PASO 6. Leer UNA respuesta
    # ------------------------------------------------
    # Una lectura es suficiente para obtener la primera línea
    # de la respuesta en este ejemplo.
    data = s.recv(1024)

    if not data:
        raise RuntimeError("Respuesta HTTP vacia")


    # La primera línea tiene algo como:
    # HTTP/1.1 200 OK
    status_line = data.split(
        b"\r\n",
        1
    )[0].decode()

    print("5) HTTP STATUS:", status_line)


    # ------------------------------------------------
    # PASO 7. Evidencia visual
    # ------------------------------------------------
    if " 200 " in status_line:

        led.on()
        print("SHOW 1 OK - LED ON")

    else:
        print(
            "Hubo respuesta HTTP, pero no fue 200 OK."
        )

finally:
    # Siempre cerramos el socket.
    s.close()
