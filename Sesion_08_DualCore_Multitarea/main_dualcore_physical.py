# =========================================================================
#  RETO 08 - Sistema multitarea (version Pico fisica, dual-core)
#  Sesion 08: Procesamiento multihilo / Dual-Core
#  Angel Rugerio Jiménez #201720
#
#  Mismo sistema que main_wokwi.py, pero ahora en PARALELO real:
#    Core 1 (hilo de _thread) -> ADC -> promedio movil -> % -> estado, cada 20 ms
#    Core 0 (programa principal) -> boton, LEDs, heartbeat y serial
#  Los dos nucleos se comunican por el diccionario shared, protegido con lock.
# =========================================================================

from machine import Pin, ADC
from time import ticks_ms, ticks_diff, sleep_ms
import _thread

# ===== Hardware =====
adc = ADC(26)                           # GP26 - ADC0, cursor del potenciometro
led_normal = Pin(13, Pin.OUT)           # GP13 - LED verde    (NORMAL)
led_warning = Pin(14, Pin.OUT)          # GP14 - LED amarillo (WARNING)
led_alarm = Pin(15, Pin.OUT)            # GP15 - LED rojo     (ALARM)
heartbeat = Pin(12, Pin.OUT)            # GP12 - LED azul     (sistema vivo)
button = Pin(16, Pin.IN, Pin.PULL_UP)   # GP16 - boton ACK: libre = 1, presionado = 0

# ===== Parametros =====
WARNING = 50        # % a partir del cual el estado es WARNING
ALARM = 75          # % a partir del cual el estado es ALARM
BUFFER_SIZE = 8     # Lecturas que promedia el filtro -> 8 x 20 ms = 160 ms de ventana

sensor_period = 20      # ms -> 50 Hz (Core 1)
button_period = 50      # ms -> 20 Hz (Core 0)
ui_period = 200         # ms -> 5 Hz  (Core 0)
log_period = 1000       # ms -> 1 Hz  (Core 0)

# ===== Datos compartidos entre nucleos =====
# Core 1 escribe raw/filtered/percent/state/samples; Core 0 escribe ack.
# Todo acceso a shared va entre lock.acquire() y lock.release().
lock = _thread.allocate_lock()

shared = {
    "raw": 0,
    "filtered": 0,
    "percent": 0.0,
    "state": "INIT",
    "samples": 0,
    "ack": False,
}

# Solo los usa Core 0: no necesitan lock
last_button = 1
alarm_blink = False
last_samples = 0

next_ui = ticks_ms()
next_button = ticks_ms()
next_log = ticks_ms()

# Ventana del promedio movil: solo la usa Core 1, tampoco necesita lock
buffer = []


def due(now, target):
    return ticks_diff(now, target) >= 0


def moving_average(new_value):
    buffer.append(new_value)
    if len(buffer) > BUFFER_SIZE:
        buffer.pop(0)
    return sum(buffer) // len(buffer)


def classify(percent):
    if percent >= ALARM:
        return "ALARM"
    elif percent >= WARNING:
        return "WARNING"
    else:
        return "NORMAL"


# ===== CORE 1: tarea critica =====
# Lee, filtra, clasifica y publica. No imprime ni toca LEDs: si hiciera trabajo
# lento, dejaria de ser una tarea rapida. Todo el calculo va FUERA del lock;
# dentro solo se copian los resultados, para tener el lock el menor tiempo posible.
def sensor_core():
    while True:
        raw = adc.read_u16()
        filtered = moving_average(raw)
        percent = filtered * 100 / 65535
        state = classify(percent)

        lock.acquire()
        shared["raw"] = raw
        shared["filtered"] = filtered
        shared["percent"] = percent
        shared["state"] = state
        shared["samples"] += 1
        if state != "ALARM":
            shared["ack"] = False   # la condicion desaparecio: el ACK ya no vale
        lock.release()

        sleep_ms(sensor_period)     # este sleep solo duerme a Core 1


# Copia de todos los datos en un solo acquire: los 6 valores son del MISMO instante
def read_shared():
    lock.acquire()
    snapshot = (
        shared["raw"],
        shared["filtered"],
        shared["percent"],
        shared["state"],
        shared["samples"],
        shared["ack"],
    )
    lock.release()
    return snapshot


# ===== CORE 0: tareas secundarias =====
def ui_task():
    global alarm_blink

    raw, filtered, percent, state, samples, ack = read_shared()
    heartbeat.toggle()

    led_normal.value(state == "NORMAL")
    led_warning.value(state == "WARNING")

    if state == "ALARM":
        if ack:
            led_alarm.on()
        else:
            alarm_blink = not alarm_blink
            led_alarm.value(alarm_blink)
    else:
        led_alarm.off()


# Revisar el estado y escribir el ACK va en el MISMO acquire: si se soltara el
# lock entre las dos cosas, Core 1 podria salir de ALARM justo en medio y el
# ACK quedaria puesto sobre una alarma que ya no existe.
def button_task():
    global last_button

    current = button.value()

    if last_button == 1 and current == 0:
        lock.acquire()
        if shared["state"] == "ALARM":
            shared["ack"] = True
            accepted = True
        else:
            accepted = False
        lock.release()

        # print fuera del lock: imprimir es lento y Core 1 tendria que esperar
        if accepted:
            print(">>> CORE 0: ALARMA RECONOCIDA | ACK=True")
        else:
            print(">>> CORE 0: boton presionado, pero no hay ALARM")

    last_button = current


def log_task():
    global last_samples

    raw, filtered, percent, state, samples, ack = read_shared()
    rate = samples - last_samples
    last_samples = samples

    print("CORE0 | raw=", raw,
          "filtered=", filtered,
          "percent=", round(percent, 1),
          "state=", state,
          "samples_core1=", samples,
          "rate=", rate, "/s",
          "ack=", ack)


# ===== Inicio =====
print("RETO 08 - Sistema multitarea (Pico fisica, dual-core)")
print("Core 1: sensor cada 20 ms | Core 0: boton 50 ms, UI 200 ms, log 1000 ms")
print("Umbrales: WARNING >=", WARNING, "% | ALARM >=", ALARM, "% | Filtro:", BUFFER_SIZE, "lecturas")

_thread.start_new_thread(sensor_core, ())
print("Core 1 iniciado. Core 0 mantiene UI, boton y serial.")

while True:
    now = ticks_ms()

    if due(now, next_button):
        button_task()
        next_button = now + button_period

    if due(now, next_ui):
        ui_task()
        next_ui = now + ui_period

    if due(now, next_log):
        log_task()
        next_log = now + log_period

    sleep_ms(2)
