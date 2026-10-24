# SESION 09 - SHOW 2
# Thonny es la consola del operador por USB.
# El comando SI cruza el UART hardware mediante GP0(TX)->GP1(RX).

from machine import UART, Pin
from time import sleep_ms, ticks_ms, ticks_diff

uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
led1 = Pin(13, Pin.OUT)


def clear_rx():
    """Vacía datos viejos del buffer RX antes de una nueva prueba."""
    while uart.any():
        uart.read()


def receive_complete_line(timeout_ms=1000):
    """
    Lee byte por byte hasta encontrar '\n'.
    Evita procesar una trama parcial cuando uart.any() se activa
    apenas llega el primer carácter.
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

    # Si expiró el tiempo, NO aceptamos una trama incompleta.
    return None


def uart_roundtrip(text, timeout_ms=1000):
    clear_rx()

    # Enviar una trama completa terminada en LF.
    uart.write((text + "\n").encode())

    # Esperar explícitamente hasta recibir LF.
    return receive_complete_line(timeout_ms)


def handle_command(command):
    command = command.upper()

    if command == "LED1 ON":
        led1.on()
        return "ACK:LED1=ON"

    if command == "LED1 OFF":
        led1.off()
        return "ACK:LED1=OFF"

    if command == "STATUS":
        return "STATUS:LED1={}".format(led1.value())

    if command == "PING":
        return "PONG"

    return "ERR:UNKNOWN_COMMAND"


print("SHOW 2 listo")
print("Jumper requerido: GP0(TX) -> GP1(RX)")
print("Comandos: PING | LED1 ON | LED1 OFF | STATUS")

while True:
    try:
        operator_command = input("CMD> ").strip()
    except KeyboardInterrupt:
        print("Programa detenido")
        break

    if not operator_command:
        continue

    print("USB CMD :", operator_command)

    uart_received = uart_roundtrip(operator_command)

    if uart_received is None:
        print("UART RX : SIN DATOS. Revisa el jumper GP0->GP1")
        continue

    print("UART RX :", uart_received)
    print("RESP    :", handle_command(uart_received))
