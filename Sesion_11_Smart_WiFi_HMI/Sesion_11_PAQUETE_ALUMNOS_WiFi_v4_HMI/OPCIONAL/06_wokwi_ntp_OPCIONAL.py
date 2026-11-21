# OPCIONAL - NTP en Wokwi
# Ejecutar solamente despues de que SHOW 0 funcione.
import network
from time import sleep_ms, ticks_ms, ticks_diff, localtime

try:
    import ntptime
except ImportError:
    raise RuntimeError("Este firmware no incluye ntptime")

try:
    wlan = network.WLAN(network.WLAN.IF_STA)
except AttributeError:
    wlan = network.WLAN(network.STA_IF)

wlan.active(True)
wlan.connect("Wokwi-GUEST", "")
start = ticks_ms()
while not wlan.isconnected():
    if ticks_diff(ticks_ms(), start) > 15000:
        raise RuntimeError("Timeout Wi-Fi")
    sleep_ms(250)

print("Wi-Fi OK. Intentando NTP...")
try:
    ntptime.settime()
    print("UTC:", localtime())
except OSError as exc:
    print("NTP no respondio:", exc)
    print("Es opcional: la sesion puede continuar.")
