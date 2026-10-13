# Sesión 08 - SHOW 1 MEJORADO
# Multitarea cooperativa simulada en Wokwi usando ticks_ms().
# No usa dual-core real: varias tareas comparten un solo núcleo sin bloqueos largos.

from machine import Pin, ADC
from time import ticks_ms, ticks_diff, sleep_ms

adc = ADC(26)
led_normal = Pin(13, Pin.OUT)
led_warning = Pin(14, Pin.OUT)
led_alarm = Pin(15, Pin.OUT)
heartbeat = Pin(12, Pin.OUT)
button = Pin(16, Pin.IN, Pin.PULL_UP)

raw_value = 0
percent_value = 0
state = "INIT"
sample_count = 0
alarm_ack = False
last_button = 1
alarm_blink = False

sensor_period = 20      # 50 Hz
ui_period = 200         # 5 Hz
log_period = 1000       # 1 Hz
button_period = 50      # 20 Hz

next_sensor = ticks_ms()
next_ui = ticks_ms()
next_log = ticks_ms()
next_button = ticks_ms()


def due(now, target):
    return ticks_diff(now, target) >= 0


def classify(percent):
    if percent < 50:
        return "NORMAL"
    elif percent < 75:
        return "WARNING"
    else:
        return "ALARM"


def sensor_task():
    global raw_value, percent_value, state, sample_count, alarm_ack

    raw_value = adc.read_u16()
    percent_value = raw_value * 100 / 65535
    new_state = classify(percent_value)

    # Cuando la condición de alarma desaparece, se borra el ACK anterior.
    if new_state != "ALARM":
        alarm_ack = False

    state = new_state
    sample_count += 1


def ui_task():
    global alarm_blink

    heartbeat.toggle()

    if state == "NORMAL":
        led_normal.on()
        led_warning.off()
        led_alarm.off()

    elif state == "WARNING":
        led_normal.off()
        led_warning.on()
        led_alarm.off()

    elif state == "ALARM":
        led_normal.off()
        led_warning.off()

        if alarm_ack:
            # Alarma reconocida: condición sigue activa, LED rojo queda fijo.
            led_alarm.on()
        else:
            # Alarma no reconocida: LED rojo parpadea.
            alarm_blink = not alarm_blink
            led_alarm.value(alarm_blink)


def log_task():
    print("raw=", raw_value,
          "percent=", round(percent_value, 1),
          "state=", state,
          "samples=", sample_count,
          "ack=", alarm_ack)


def button_task():
    global alarm_ack, last_button

    current_button = button.value()

    # Detecta una sola pulsación: flanco 1 -> 0.
    if last_button == 1 and current_button == 0:
        if state == "ALARM":
            alarm_ack = True
            print(">>> ALARMA RECONOCIDA | ACK=True")
        else:
            print(">>> Botón presionado, pero no hay ALARM")

    last_button = current_button


print("SHOW 1: multitarea cooperativa sin bloqueos largos")
print("ALARM sin ACK = rojo parpadea | ACK = rojo fijo")

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
