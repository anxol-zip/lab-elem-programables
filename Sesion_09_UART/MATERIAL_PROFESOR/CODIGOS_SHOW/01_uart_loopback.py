# SESION 09 - SHOW 1
# UART LOOPBACK REAL: GP0(TX) conectado con un jumper a GP1(RX)

from machine import UART, Pin
from time import sleep_ms, ticks_ms, ticks_diff

uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))


def clear_rx():
    """Vacía datos viejos del buffer RX."""
    while uart.any():
        uart.read()


def receive_complete_line(timeout_ms=1000):
    """
    Espera una línea COMPLETA. No devuelve datos hasta recibir '\n'.
    """
    buffer = bytearray()
    start = ticks_ms()

    while ticks_diff(ticks_ms(), start) < timeout_ms:

        while uart.any():
            byte = uart.read(1)

            if not byte:
                break

            if byte == b"\n":
                return buffer.decode().rstrip("\r")

            buffer.extend(byte)

        sleep_ms(1)

    return None


counter = 0
print("Conecta GP0(TX) -> GP1(RX)")
print("SHOW 1: loopback UART real")

while True:
    clear_rx()
    message = "LOOP,{}".format(counter)

    uart.write(message + "\n")
    received = receive_complete_line()

    print("TX:", message)
    print("RX:", received if received is not None else "SIN DATOS")
    print("---")

    counter += 1
    sleep_ms(1000)
