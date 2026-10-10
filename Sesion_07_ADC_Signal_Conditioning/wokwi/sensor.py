# =========================================================================
#  RETO 07 (BONUS) - Smart Analog Monitor con sensor de gas
#  Sesion 07: ADC y acondicionamiento de senal
#  Angel Rugerio Jiménez #201720
#
#  El mismo monitor de main.py, pero la senal viene del sensor de gas
#  (wokwi-gas-sensor, tipo MQ-2) en lugar del potenciometro: su salida
#  analogica AOUT va a GP26 (ADC0). Solo se probo en Wokwi.
#
#  El algoritmo no cambia: raw -> promedio movil -> voltaje y % ->
#  NORMAL / WARNING / ALARM -> LED. Lo que cambia es el SIGNIFICADO:
#  mas gas -> mas voltaje en AOUT -> mas %. El % es del rango del ADC,
#  no una concentracion en ppm (eso requiere calibrar el sensor).
# =========================================================================

from machine import Pin, ADC
from time import sleep_ms

# ===== Hardware =====
sensor = ADC(Pin(26))           # GP26 - ADC0, salida AOUT del sensor de gas
green = Pin(13, Pin.OUT)        # GP13 - LED verde    (NORMAL)
yellow = Pin(14, Pin.OUT)       # GP14 - LED amarillo (WARNING)
red = Pin(15, Pin.OUT)          # GP15 - LED rojo     (ALARM)

# ===== Parametros =====
VREF = 3.3          # V. Voltaje de referencia del ADC de la Pico
# Umbrales del DO 02: A = 50/75 (base), B = 40/60, C = 60/80
WARNING = 50        # % a partir del cual el estado es WARNING (gas en aumento)
ALARM = 75          # % a partir del cual el estado es ALARM (concentracion peligrosa)
WINDOW_SIZE = 10    # Lecturas que promedia el filtro
PERIODO_MS = 300    # Tiempo entre lecturas -> el filtro cubre 10 x 300 ms = 3 s

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
print("RETO 07 (BONUS) - Smart Analog Monitor con sensor de gas")
print("Sensor: gas, AOUT -> GP26 (ADC0) | LEDs: GP13 verde, GP14 amarillo, GP15 rojo")
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
