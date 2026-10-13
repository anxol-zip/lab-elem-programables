# Sesión 08 - DO 08 STARTER v2
# Completa el sistema multitarea simulado en Wokwi.
# Objetivo: adquisición rápida + filtro + UI + ACK sin bloqueos largos.

from machine import Pin, ADC
from time import ticks_ms, ticks_diff, sleep_ms

adc = ADC(26)
led_normal = Pin(13, Pin.OUT)
led_warning = Pin(14, Pin.OUT)
led_alarm = Pin(15, Pin.OUT)
heartbeat = Pin(12, Pin.OUT)
button = Pin(16, Pin.IN, Pin.PULL_UP)

raw_value = 0
filtered_value = 0
percent_value = 0
state = "INIT"
sample_count = 0
alarm_ack = False
last_button = 1
alarm_blink = False

buffer = []
BUFFER_SIZE = 8

sensor_period = 20
ui_period = 200
log_period = 1000
button_period = 50

next_sensor = ticks_ms()
next_ui = ticks_ms()
next_log = ticks_ms()
next_button = ticks_ms()


def due(now, target):
    return ticks_diff(now, target) >= 0


def moving_average(new_value):
    # TODO 1:
    # Agrega new_value al buffer.
    # Mantén máximo BUFFER_SIZE valores.
    # Regresa el promedio entero.
    return new_value


def classify(percent):
    # TODO 2:
    # NORMAL si percent < 50
    # WARNING si percent < 75
    # ALARM en caso contrario
    return "NORMAL"


def sensor_task():
    global raw_value, filtered_value, percent_value
    global state, sample_count, alarm_ack

    # TODO 3:
    # 1) Leer ADC
    # 2) Filtrar con moving_average()
    # 3) Convertir a porcentaje
    # 4) Clasificar el estado
    # 5) Incrementar sample_count
    # 6) Si ya no hay ALARM, borrar el ACK anterior
    pass


def ui_task():
    global alarm_blink

    # TODO 4:
    # - heartbeat debe cambiar siempre
    # - NORMAL: verde
    # - WARNING: amarillo
    # - ALARM sin ACK: rojo parpadea
    # - ALARM con ACK: rojo fijo
    pass


def log_task():
    print("raw=", raw_value,
          "filtered=", filtered_value,
          "percent=", round(percent_value, 1),
          "state=", state,
          "samples=", sample_count,
          "ack=", alarm_ack)


def button_task():
    global alarm_ack, last_button

    # TODO 5:
    # Detecta únicamente una nueva pulsación (flanco 1 -> 0).
    # Si state == "ALARM", cambia alarm_ack a True.
    # Si no existe ALARM, imprime un mensaje informativo.
    pass


print("DO 08: completa el sistema multitarea")
print("Objetivo: ALARM parpadea hasta que el usuario la reconoce")

while True:
    now = ticks_ms()

    if due(now, next_sensor):
        sensor_task()
        next_sensor = now + sensor_period

    if due(now, next_ui):
        ui_task()
        next_ui = now + ui_period

    if due(now, next_log):
        log_task()
        next_log = now + log_period

    if due(now, next_button):
        button_task()
        next_button = now + button_period

    sleep_ms(2)
