# SESION 09 - SHOW 0
# USB/REPL vs UART hardware
# No requiere jumper. Thonny solo ve el print() por USB.

from machine import UART, Pin
from time import sleep_ms

uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))

counter = 0
print("SHOW 0 listo: USB DEBUG visible en Thonny")

while True:
    message = "HELLO,{}".format(counter)

    # Sale por el UART hardware (GP0/TX):
    uart.write(message + "\n")

    # Sale por USB/REPL y por eso SI aparece en Thonny:
    print("USB DEBUG -> UART TX:", message)

    counter += 1
    sleep_ms(1000)
