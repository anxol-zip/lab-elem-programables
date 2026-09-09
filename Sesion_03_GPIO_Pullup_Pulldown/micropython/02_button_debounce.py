# =========================================================================
#  DO 02 - Boton con debounce + wait for release
#  Sesion 03: GPIO, pull-up/pull-down y debounce
#  Angel Rugerio Jimenez #201720
# =========================================================================
#
#  PROBLEMA: un boton mecanico no cambia de estado limpiamente. Al cerrar,
#  los contactos rebotan durante unos milisegundos y el pin entrega una
#  rafaga de 1/0. Fisicamente hubo UNA presion, pero el programa podria
#  contar varias.
#
#  WAIT FOR RELEASE: despues de aceptar el click esperamos a que el boton
#  se suelte. Regla practica: 1 presion = 1 peticion, sin importar cuanto
#  tiempo se mantenga apretado.

from machine import Pin
from time import sleep_ms

BUTTON_PIN = 16
DEBOUNCE_MS = 30      # ventana de rebote a ignorar
POLL_MS = 10          # periodo de muestreo del polling

button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

clicks = 0
last = 1              # estado anterior; arranca en 1 = boton libre (pull-up)

print("DO 02 - Debounce + wait for release en GP{}".format(BUTTON_PIN))
print("Presiona el boton: cada presion debe contar como UN evento")
print("-" * 46)

while True:
    now = button.value()

    # Flanco de bajada: el boton acaba de pasar de libre (1) a presionado (0)
    if last == 1 and now == 0:
        sleep_ms(DEBOUNCE_MS)

        # Segunda lectura: si el rebote ya paso, esto sigue en 0
        if button.value() == 0:
            clicks += 1
            print("CLICK valido #{}".format(clicks))

            # Wait for release: no aceptamos otro click hasta soltar
            while button.value() == 0:
                sleep_ms(POLL_MS)

            print("   boton liberado - listo para la siguiente peticion")

    last = now
    sleep_ms(POLL_MS)
