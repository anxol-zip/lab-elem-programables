# SESION 09 - DO09 / CHALLENGE STARTER (THONNY + LOOPBACK)
# Conexion: GP0(TX) -> GP1(RX) con un jumper.
# Thonny entrega el comando por USB; el comando cruza el UART antes de procesarse.

from machine import UART, Pin
from time import sleep_ms, ticks_ms, ticks_diff

uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
led1 = Pin(13, Pin.OUT)
led2 = Pin(14, Pin.OUT)


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


def status_frame():
    # TODO 1: regresar STATUS,LED1,x,LED2,y
    return "TODO"


def set_output(device, value):
    # TODO 2:
    # - value solo puede ser "0" o "1"
    # - controlar LED1, LED2 o ALL
    # - regresar True si fue valido
    return False


def handle_frame(frame):
    frame = frame.upper()

    # TODO 3: PING -> ACK,PONG

    # TODO 4: GET,STATUS -> status_frame()

    # TODO 5: SET,DISPOSITIVO,VALOR
    # Pista: parts = frame.split(",")

    # TODO 6: devolver ERR,... para tramas no validas
    return "ERR,NOT_IMPLEMENTED"


print("DO09 listo")
print("Jumper: GP0(TX) -> GP1(RX)")

while True:
    try:
        command = input("CMD> ").strip()
    except KeyboardInterrupt:
        print("Programa detenido")
        break

    if not command:
        continue

    received = uart_roundtrip(command)

    print("USB CMD :", command)

    if received is None:
        print("UART RX : SIN DATOS. Revisa GP0->GP1")
        continue

    print("UART RX :", received)
    print("RESP    :", handle_frame(received))
