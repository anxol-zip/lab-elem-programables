# =========================================================================
#  CHALLENGE 09 - UART Command Center con Thonny
#  Sesion 09: Comunicacion UART
#  Angel Rugerio Jiménez #201720
# =========================================================================
#  Ruta de datos:
#  Thonny/USB -> input() -> UART TX GP0 -> jumper -> UART RX GP1 -> parser -> LEDs -> respuesta
#  Conexion: jumper GP0(TX) -> GP1(RX), LED1 en GP13, LED2 en GP14
# =========================================================================

from machine import UART, Pin, Timer
from time import sleep_ms, ticks_ms, ticks_diff

# ===== Hardware =====
uart = UART(0, baudrate=9600, bits=8, parity=None, stop=1, tx=Pin(0), rx=Pin(1))  # 9600 8N1
led1 = Pin(13, Pin.OUT)     # GP13 - LED1
led2 = Pin(14, Pin.OUT)     # GP14 - LED2

LEDS = {"LED1": led1, "LED2": led2}

# Un timer periodico por LED para BLINK (no bloquea el input() del loop principal)
blink_timers = {"LED1": Timer(-1), "LED2": Timer(-1)}

# ===== Parametros =====
BLINK_MIN = 50          # ms, periodo minimo aceptado en BLINK
BLINK_MAX = 5000        # ms, periodo maximo aceptado en BLINK

HELP_TEXT = "PING | GET,STATUS | SET,<LED1|LED2|ALL>,<0|1> | TOGGLE,<LED1|LED2> | BLINK,<LED1|LED2>,<ms> | HELP"


# ===== Transporte UART (version robusta v3 del profe) =====
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


# ===== Acciones sobre los LEDs =====
def stop_blink(name):
    """Un SET o TOGGLE manda sobre un BLINK activo: se detiene el timer."""
    blink_timers[name].deinit()


def status_frame():
    return "STATUS,LED1,{},LED2,{}".format(led1.value(), led2.value())


def set_output(device, value):
    output_value = int(value)

    if device == "ALL":
        for name in LEDS:
            stop_blink(name)
            LEDS[name].value(output_value)
    else:
        stop_blink(device)
        LEDS[device].value(output_value)


def toggle_output(device):
    stop_blink(device)
    LEDS[device].toggle()
    return LEDS[device].value()


def start_blink(device, period):
    pin = LEDS[device]
    blink_timers[device].init(mode=Timer.PERIODIC, period=period,
                              callback=lambda t: pin.toggle())


# ===== Parser de tramas =====
def handle_frame(frame):
    parts = [p.strip() for p in frame.upper().split(",")]
    cmd = parts[0]

    # --- Nivel 1 ---
    if cmd == "PING":
        if len(parts) != 1:
            return "ERR,BAD_FIELDS"
        return "ACK,PONG"

    if cmd == "GET":
        if len(parts) != 2:
            return "ERR,BAD_FIELDS"
        if parts[1] != "STATUS":
            return "ERR,BAD_GET"
        return status_frame()

    # --- Nivel 1 + Nivel 2 (ALL y validaciones) ---
    if cmd == "SET":
        if len(parts) != 3:
            return "ERR,BAD_FIELDS"
        device, value = parts[1], parts[2]
        if device not in LEDS and device != "ALL":
            return "ERR,BAD_DEVICE"
        if value not in ("0", "1"):
            return "ERR,BAD_VALUE"
        set_output(device, value)
        return "ACK,{},{}".format(device, value)

    # --- Nivel 3 (bonus) ---
    if cmd == "TOGGLE":
        if len(parts) != 2:
            return "ERR,BAD_FIELDS"
        device = parts[1]
        if device not in LEDS:
            return "ERR,BAD_DEVICE"
        return "ACK,{},{}".format(device, toggle_output(device))

    if cmd == "BLINK":
        if len(parts) != 3:
            return "ERR,BAD_FIELDS"
        device, period = parts[1], parts[2]
        if device not in LEDS:
            return "ERR,BAD_DEVICE"
        if not period.isdigit() or not BLINK_MIN <= int(period) <= BLINK_MAX:
            return "ERR,BAD_PERIOD"
        start_blink(device, int(period))
        return "ACK,BLINK,{},{}".format(device, period)

    if cmd == "HELP":
        if len(parts) != 1:
            return "ERR,BAD_FIELDS"
        return "ACK,HELP: " + HELP_TEXT

    return "ERR,UNKNOWN_FRAME"


# ===== Programa principal =====
print("CHALLENGE 09 - UART Command Center")
print("Jumper requerido: GP0(TX) -> GP1(RX) | UART0 9600 8N1")
print("Comandos:", HELP_TEXT)

while True:
    try:
        command = input("CMD> ").strip()
    except KeyboardInterrupt:
        for name in LEDS:
            stop_blink(name)
        print("Programa detenido")
        break

    if not command:
        continue

    print("USB CMD :", command)
    received = uart_roundtrip(command)

    if received is None:
        print("UART RX : SIN DATOS. Revisa GP0->GP1")
        continue

    print("UART RX :", received)
    print("RESP    :", handle_frame(received))
