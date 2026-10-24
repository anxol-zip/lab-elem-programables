# BACKUP - SOLO THONNY / USB (SIN JUMPER)
# Este archivo permite practicar el parser y los LEDs si no hay jumper.
# IMPORTANTE: NO demuestra el UART hardware; solo el protocolo de comandos.

from machine import Pin

led1 = Pin(13, Pin.OUT)
led2 = Pin(14, Pin.OUT)


def status_frame():
    return "STATUS,LED1,{},LED2,{}".format(led1.value(), led2.value())


def handle(frame):
    frame = frame.strip().upper()

    if frame == "PING":
        return "ACK,PONG"

    if frame == "GET,STATUS":
        return status_frame()

    parts = frame.split(",")
    if len(parts) == 3 and parts[0] == "SET":
        _, device, value = parts
        if value not in ("0", "1"):
            return "ERR,BAD_VALUE"
        val = int(value)
        if device == "LED1":
            led1.value(val)
        elif device == "LED2":
            led2.value(val)
        elif device == "ALL":
            led1.value(val); led2.value(val)
        else:
            return "ERR,BAD_DEVICE"
        return "ACK,{},{}".format(device, value)

    return "ERR,UNKNOWN_FRAME"


print("BACKUP USB ONLY - no prueba UART fisico")
while True:
    try:
        cmd = input("CMD> ")
    except KeyboardInterrupt:
        break
    print("RESP:", handle(cmd))
