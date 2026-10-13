# Sesión 08 - SHOW 0
# Problema intencional: un programa bloqueante responde tarde.
# Se usa como comparación antes de la versión multitarea.

from machine import Pin, ADC
from time import sleep_ms

adc = ADC(26)
led_normal = Pin(13, Pin.OUT)
led_warning = Pin(14, Pin.OUT)
led_alarm = Pin(15, Pin.OUT)
heartbeat = Pin(12, Pin.OUT)
button = Pin(16, Pin.IN, Pin.PULL_UP)


def set_leds(state):
    led_normal.value(state == "NORMAL")
    led_warning.value(state == "WARNING")
    led_alarm.value(state == "ALARM")


def classify(percent):
    if percent < 50:
        return "NORMAL"
    elif percent < 75:
        return "WARNING"
    else:
        return "ALARM"


print("SHOW 0: versión BLOQUEANTE")
print("Intenta mover el sensor y pulsar el botón rápidamente.")

while True:
    raw = adc.read_u16()
    percent = raw * 100 / 65535
    state = classify(percent)
    set_leds(state)

    # El botón solo se revisa una vez por cada vuelta del loop.
    if button.value() == 0:
        print(">>> botón detectado")

    print("raw=", raw,
          "percent=", round(percent, 1),
          "state=", state)

    # BLOQUEO INTENCIONAL:
    # durante 1 segundo no se vuelve a leer sensor ni botón.
    sleep_ms(1000)

    heartbeat.toggle()
