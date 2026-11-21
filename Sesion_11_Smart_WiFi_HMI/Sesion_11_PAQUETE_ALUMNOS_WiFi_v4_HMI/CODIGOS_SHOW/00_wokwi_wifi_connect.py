# ================================================================
# SESIÓN 11 - SHOW 0
# WOKWI: CONEXIÓN Wi-Fi BÁSICA
# ================================================================
#
# OBJETIVO DIDÁCTICO
# ------------------
# Comprobar únicamente que la Pico 2 W virtual puede:
#   1) activar su interfaz Wi-Fi,
#   2) conectarse a Wokwi-GUEST,
#   3) obtener una dirección IP.
#
# IMPORTANTE
# ----------
# En este SHOW todavía NO usamos sockets ni HTTP.
# Si esta prueba falla, no tiene sentido avanzar al SHOW 1.
# ================================================================

import network
from time import sleep_ms, ticks_ms, ticks_diff


def get_sta_interface():
    """
    Devuelve la interfaz Wi-Fi en modo STA (Station).

    STA significa que la Pico se conecta a una red que ya existe.
    En Wokwi esa red se llama Wokwi-GUEST.

    El try/except mantiene compatibilidad con diferentes versiones
    de MicroPython que usan nombres ligeramente distintos.
    """
    try:
        return network.WLAN(network.WLAN.IF_STA)
    except AttributeError:
        return network.WLAN(network.STA_IF)


# ------------------------------------------------
# PASO 1. Crear y activar la interfaz Wi-Fi
# ------------------------------------------------
wlan = get_sta_interface()
wlan.active(True)


# ------------------------------------------------
# PASO 2. Pedir conexión a la red virtual de Wokwi
# ------------------------------------------------
# Wokwi-GUEST no necesita contraseña.
wlan.connect("Wokwi-GUEST", "")


# ------------------------------------------------
# PASO 3. Esperar la conexión, pero con timeout
# ------------------------------------------------
print("Conectando a Wokwi-GUEST", end="")

start = ticks_ms()

while not wlan.isconnected():

    # Evitamos un while infinito si algo sale mal.
    if ticks_diff(ticks_ms(), start) > 15000:
        raise RuntimeError(
            "Timeout Wi-Fi: la Pico no pudo conectarse."
        )

    print(".", end="")
    sleep_ms(250)


# ------------------------------------------------
# PASO 4. Mostrar el resultado
# ------------------------------------------------
print()
print("Wi-Fi conectado")

# ifconfig()[0] contiene la dirección IP de la Pico.
print("IP virtual:", wlan.ifconfig()[0])

print("SHOW 0 OK")
