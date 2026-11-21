# ================================================================
# SESIÓN 11 - SHOW 2
# FÍSICO: CONECTAR LA PICO A TU Wi-Fi (MODO STA)
# ================================================================
#
# OBJETIVO DIDÁCTICO
# ------------------
# Antes de crear un servidor web, primero debemos demostrar que:
#
#   PICO -> TU ROUTER -> obtiene una IP local
#
# La laptop NO cambia de red.
# Teams/Zoom/Internet pueden seguir funcionando.
#
# ARCHIVO NECESARIO EN LA PICO
# ----------------------------
# /secrets.py
#
# con:
# WIFI_SSID = "nombre_de_tu_red"
# WIFI_PASSWORD = "tu_password"
# ================================================================

import network

from time import (
    sleep_ms,
    ticks_ms,
    ticks_diff
)

from secrets import (
    WIFI_SSID,
    WIFI_PASSWORD
)


def get_sta_interface():
    """
    Crea la interfaz Wi-Fi en modo STA.

    STA = Station:
    la Pico se conecta a una red existente.
    """

    try:
        return network.WLAN(
            network.WLAN.IF_STA
        )

    except AttributeError:
        # Compatibilidad con versiones anteriores.
        return network.WLAN(
            network.STA_IF
        )


def connect_wifi(
    ssid,
    password,
    timeout_ms=20000
):
    """
    Conecta la Pico a la red indicada.

    Devuelve el objeto wlan cuando la conexión
    ya está lista.
    """

    # 1) Crear interfaz STA.
    wlan = get_sta_interface()

    # 2) Encender el hardware Wi-Fi.
    wlan.active(True)


    # Si ya estaba conectada, reutilizamos esa conexión.
    if wlan.isconnected():

        print("Wi-Fi ya conectado")
        print(
            "IP:",
            wlan.ifconfig()[0]
        )

        return wlan


    # Intentamos limpiar una conexión anterior.
    try:
        wlan.disconnect()
        sleep_ms(200)

    except Exception:
        # Si no había conexión previa, no pasa nada.
        pass


    # 3) Solicitar conexión.
    print("Conectando a:", ssid)

    wlan.connect(
        ssid,
        password
    )


    # 4) Esperar hasta conectar o alcanzar el timeout.
    start = ticks_ms()
    last_status = None

    while not wlan.isconnected():

        status = wlan.status()

        # Solo imprimimos cuando cambia el estado
        # para no llenar la terminal.
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
                "Revisa SSID, password y 2.4 GHz. "
                "status={}".format(status)
            )

        sleep_ms(250)


    # 5) Conexión exitosa.
    print("Wi-Fi conectado")
    print(
        "IP:",
        wlan.ifconfig()[0]
    )

    return wlan


# ================================================================
# PROGRAMA PRINCIPAL
# ================================================================

# Llamamos a la función usando las credenciales
# guardadas en secrets.py.
wlan = connect_wifi(
    WIFI_SSID,
    WIFI_PASSWORD
)

# ifconfig()[0] = dirección IP local de la Pico.
ip = wlan.ifconfig()[0]


print()
print("================================")
print(" SHOW 2 OK")
print("================================")
print("Pico IP:", ip)
print("Tu laptop NO cambia de Wi-Fi.")
print("Ahora ambos deben estar en la misma red.")
