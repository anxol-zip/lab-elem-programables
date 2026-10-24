# WOKWI OPCIONAL
# Solo diagnostico visual. No es la ruta oficial de la sesion.
# `print()` usa la consola USB del simulador. `uart.write()` se mantiene como referencia.

from machine import UART, Pin
from time import sleep_ms

uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
led1 = Pin(13, Pin.OUT)
led2 = Pin(14, Pin.OUT)

print("Wokwi backup iniciado")

for i in range(6):
    msg = "HELLO,{}".format(i)
    uart.write(msg + "\n")
    print("USB DEBUG:", msg)
    led1.toggle()
    led2.value(not led1.value())
    sleep_ms(800)

print("Fin del diagnostico. La clase principal usa Thonny + Pico fisica.")
