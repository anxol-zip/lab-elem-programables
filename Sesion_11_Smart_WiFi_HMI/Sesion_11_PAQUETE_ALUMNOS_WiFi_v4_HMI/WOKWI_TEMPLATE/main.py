# SHOW 1 - Wokwi: cliente HTTP simple y robusto
# Objetivo: Wi-Fi -> DNS -> TCP -> HTTP -> 200 OK
import network
import socket
from machine import Pin
from time import sleep_ms, ticks_ms, ticks_diff


def get_sta_interface():
    try:
        return network.WLAN(network.WLAN.IF_STA)
    except AttributeError:
        return network.WLAN(network.STA_IF)


# LED externo en GP15: se enciende si recibimos HTTP 200.
led = Pin(15, Pin.OUT)
led.off()

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

print("\n   IP:", wlan.ifconfig()[0])

HOST = "example.com"
PORT = 80

print("2) Resolviendo DNS:", HOST)
addr = socket.getaddrinfo(HOST, PORT)[0][-1]
print("   Destino:", addr)

s = socket.socket()
try:
    try:
        s.settimeout(8)
    except Exception:
        pass

    print("3) Abriendo TCP...")
    s.connect(addr)

    request = (
        "GET / HTTP/1.1\r\n"
        "Host: example.com\r\n"
        "Connection: close\r\n"
        "\r\n"
    )

    print("4) Enviando GET...")
    s.write(request.encode())

    # IMPORTANTE: una sola lectura para este ejemplo.
    data = s.recv(1024)
    if not data:
        raise RuntimeError("Respuesta HTTP vacia")

    # La primera linea contiene el estado HTTP.
    status_line = data.split(b"\r\n", 1)[0].decode()
    print("5) HTTP STATUS:", status_line)

    if " 200 " in status_line:
        led.on()
        print("SHOW 1 OK - LED ON")
    else:
        print("Respuesta recibida, pero no fue 200")

finally:
    s.close()
