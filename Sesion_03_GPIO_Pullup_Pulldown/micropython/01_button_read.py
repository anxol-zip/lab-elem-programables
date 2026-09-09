# =========================================================================
#  DO 01 - Lectura de boton con pull-up interno
#  Sesion 03: GPIO, pull-up/pull-down y debounce
#  Angel Rugerio Jimenez #201720
# =========================================================================
#
#  Circuito (Etapa A):   GP16 --- BOTON --- GND
#
#  Con PULL-UP INTERNO el pin queda amarrado a 3.3 V cuando nadie lo toca,
#  asi que la lectura por defecto es 1. Al presionar, el boton conecta el
#  pin directamente a GND y esa conexion "le gana" al resistor interno:
#  por eso PRESIONADO se lee como 0 (logica invertida).
#
#  Sin el pull-up el pin quedaria FLOTANTE: no es que cambie solo, es que
#  su valor NO ESTA GARANTIZADO.

from machine import Pin
from time import sleep_ms

BUTTON_PIN = 16

button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

print("DO 01 - Lectura de boton en GP{} con pull-up interno".format(BUTTON_PIN))
print("Esperado -> boton libre = 1 | boton presionado = 0")
print("-" * 46)

while True:
    value = button.value()
    estado = "PRESIONADO" if value == 0 else "libre"
    print("GP{} = {}  ({})".format(BUTTON_PIN, value, estado))
    sleep_ms(200)
