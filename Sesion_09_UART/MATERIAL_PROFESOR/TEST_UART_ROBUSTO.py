# TEST UART ROBUSTO - Sesión 09
# Conexión física: GP0(TX) -> GP1(RX)

from machine import UART, Pin
from time import sleep_ms, ticks_ms, ticks_diff

uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))


def clear_rx():
    while uart.any():
        uart.read()


def receive_complete_line(timeout_ms=1000):
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


def uart_roundtrip(text, timeout_ms=1000):
    clear_rx()
    uart.write((text + "\n").encode())
    return receive_complete_line(timeout_ms)


print("TEST UART ROBUSTO")
print("Jumper: GP0(TX) -> GP1(RX)")
print("Escribe EXIT para terminar.")

while True:
    text = input("TX> ").strip()

    if text.upper() == "EXIT":
        break

    if not text:
        continue

    rx = uart_roundtrip(text)

    print("TX :", repr(text))
    print("RX :", repr(rx))
    print("OK :", rx == text)
    print("---")
