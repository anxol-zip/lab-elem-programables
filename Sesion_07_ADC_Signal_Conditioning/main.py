# =========================================================================
#  RETO 07 - Smart Analog Monitor
#  Sesion 07: ADC y acondicionamiento de senal
#  Angel Rugerio Jiménez #201720
#  Axel Garcia Arellano #201251
#
#  Lee la senal del potenciometro en GP26 (ADC0) y la acondiciona:
#  raw -> promedio movil -> voltaje y % -> NORMAL / WARNING / ALARM -> LED.
#  El estado lo decide la senal FILTRADA, nunca una lectura aislada.
# =========================================================================

from machine import Pin, ADC
from time import sleep_ms

# ===== Hardware =====
sensor = ADC(Pin(26))           # GP26 - ADC0, cursor del potenciometro
green = Pin(13, Pin.OUT)        # GP13 - LED verde    (NORMAL)
yellow = Pin(14, Pin.OUT)       # GP14 - LED amarillo (WARNING)
red = Pin(15, Pin.OUT)          # GP15 - LED rojo     (ALARM)

# ===== Parametros =====
VREF = 3.3          # V. Voltaje de referencia del ADC de la Pico
WARNING = 50        # % a partir del cual el estado es WARNING
ALARM = 75          # % a partir del cual el estado es ALARM
WINDOW_SIZE = 10    # Lecturas que promedia el filtro
PERIODO_MS = 60    # Tiempo entre lecturas -> el filtro cubre 10 x 300 ms = 3 s

# Ventana deslizante del promedio movil: guarda las ultimas WINDOW_SIZE lecturas
window = []


# ===== Medicion =====
def read_raw():
    return sensor.read_u16()    # 0 a 65535 (16 bits normalizados)


# Regla de tres: 0 -> 0 V y 65535 -> VREF
def to_voltage(raw):
    return raw * VREF / 65535


# Regla de tres: 0 -> 0 % y 65535 -> 100 %
def to_percent(raw):
    return raw * 100 / 65535


# ===== Filtro =====
# Promedio movil: entra la lectura nueva y, si la ventana ya esta llena,
# sale la mas vieja. Mientras se llena se divide entre len(window), no entre
# WINDOW_SIZE, para que las primeras lecturas no salgan mas bajas.
def filter_average(raw):
    window.append(raw)
    if len(window) > WINDOW_SIZE:
        window.pop(0)
    return sum(window) / len(window)


# ===== Decision =====
# Se pregunta del umbral mas alto al mas bajo: si se revisara primero
# WARNING, un 80 % entraria ahi y nunca llegaria a ALARM.
def classify(percent):
    if percent >= ALARM:
        return "ALARM"
    elif percent >= WARNING:
        return "WARNING"
    else:
        return "NORMAL"


# Cada comparacion ya es True/False -> 1/0: solo un LED queda encendido
def update_outputs(state):
    green.value(state == "NORMAL")
    yellow.value(state == "WARNING")
    red.value(state == "ALARM")


# ===== Reporte =====
def print_status(raw, filtered, voltage, percent, state):
    print("raw:", raw, "| filtered:", int(filtered), "| V:", round(voltage, 2), "| %:", round(percent, 1), "| state:", state)


# ===== Inicio =====
print("RETO 07 - Smart Analog Monitor")
print("Sensor: GP26 (ADC0) | LEDs: GP13 verde, GP14 amarillo, GP15 rojo")
print("Umbrales: WARNING >=", WARNING, "% | ALARM >=", ALARM, "% | Filtro:", WINDOW_SIZE, "lecturas")

# Todos los LEDs apagados antes de la primera lectura
update_outputs("")

# El while describe el sistema completo: medir -> filtrar -> convertir -> decidir -> actuar -> reportar
while True:
    raw = read_raw()
    filtered = filter_average(raw)
    voltage = to_voltage(filtered)
    percent = to_percent(filtered)
    state = classify(percent)
    update_outputs(state)
    print_status(raw, filtered, voltage, percent, state)
    sleep_ms(PERIODO_MS)
