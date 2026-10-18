# =========================================================================
#  RETO 08 - Sistema multitarea (version Wokwi)
#  Sesion 08: Procesamiento multihilo / Dual-Core
#  Angel Rugerio Jiménez #201720
# =========================================================================

from machine import Pin, ADC
from time import ticks_ms, ticks_diff, sleep_ms

# ===== Hardware =====
adc = ADC(28)                           # GP28 - ADC2, cursor del potenciometro
led_normal = Pin(13, Pin.OUT)           # GP13 - LED verde    (NORMAL)
led_warning = Pin(14, Pin.OUT)          # GP14 - LED amarillo (WARNING)
led_alarm = Pin(15, Pin.OUT)            # GP15 - LED rojo     (ALARM)
heartbeat = Pin(12, Pin.OUT)            # GP12 - LED azul     (sistema vivo)
button = Pin(16, Pin.IN, Pin.PULL_UP)   # GP16 - boton ACK: libre = 1, presionado = 0

# ===== Parametros =====
WARNING = 50        # % a partir del cual el estado es WARNING
ALARM = 75          # % a partir del cual el estado es ALARM
BUFFER_SIZE = 8     # Lecturas que promedia el filtro -> 8 x 20 ms = 160 ms de ventana

sensor_period = 20      # ms -> 50 Hz
button_period = 50      # ms -> 20 Hz
ui_period = 200         # ms -> 5 Hz
log_period = 1000       # ms -> 1 Hz

# ===== Estado compartido entre tareas =====
raw_value = 0
filtered_value = 0
percent_value = 0
state = "INIT"
sample_count = 0
last_sample_count = 0   # sample_count en el log anterior -> muestras por segundo
alarm_ack = False
last_button = 1
alarm_blink = False

# Ventana del promedio movil
buffer = []

# Cuando le toca a cada tarea
next_sensor = ticks_ms()
next_ui = ticks_ms()
next_log = ticks_ms()
next_button = ticks_ms()


# ¿Ya llego (o ya paso) el momento target? ticks_diff es seguro aunque ticks_ms() de la vuelta
def due(now, target):
    return ticks_diff(now, target) >= 0


# ===== Filtro =====
# Igual que en el Reto 07: entra la lectura nueva y, si la ventana ya esta
# llena, sale la mas vieja. Se divide entre len(buffer) para que las primeras
# lecturas no salgan mas bajas mientras se llena.
def moving_average(new_value):
    buffer.append(new_value)
    if len(buffer) > BUFFER_SIZE:
        buffer.pop(0)
    return sum(buffer) // len(buffer)


# ===== Decision =====
# Del umbral mas alto al mas bajo
def classify(percent):
    if percent >= ALARM:
        return "ALARM"
    elif percent >= WARNING:
        return "WARNING"
    else:
        return "NORMAL"


# ===== Tareas =====
# Tarea critica: corta y rapida. No imprime ni toca LEDs, solo actualiza datos.
def sensor_task():
    global raw_value, filtered_value, percent_value
    global state, sample_count, alarm_ack

    raw_value = adc.read_u16()
    filtered_value = moving_average(raw_value)
    percent_value = filtered_value * 100 / 65535
    new_state = classify(percent_value)

    # Si la condicion de alarma desaparece, el ACK anterior ya no vale
    if new_state != "ALARM":
        alarm_ack = False

    state = new_state
    sample_count += 1


def ui_task():
    global alarm_blink

    heartbeat.toggle()      # cambia SIEMPRE: si se congela, el programa se bloqueo

    led_normal.value(state == "NORMAL")
    led_warning.value(state == "WARNING")

    if state == "ALARM":
        if alarm_ack:
            led_alarm.on()                  # reconocida: la condicion sigue, rojo fijo
        else:
            alarm_blink = not alarm_blink   # sin reconocer: rojo parpadea
            led_alarm.value(alarm_blink)
    else:
        led_alarm.off()


def log_task():
    global last_sample_count

    rate = sample_count - last_sample_count    # muestras desde el log anterior (~1 s)
    last_sample_count = sample_count

    print("raw=", raw_value,
          "filtered=", filtered_value,
          "percent=", round(percent_value, 1),
          "state=", state,
          "samples=", sample_count,
          "rate=", rate, "/s",
          "ack=", alarm_ack)


# El boton se lee cada 50 ms y solo cuenta el CAMBIO 1 -> 0 (flanco de bajada):
# mantenerlo presionado no genera mas eventos. Leer cada 50 ms tambien filtra
# el rebote, que dura menos que eso.
def button_task():
    global alarm_ack, last_button, sample_count, last_sample_count

    current_button = button.value()

    if last_button == 1 and current_button == 0:
        if state == "ALARM":
            alarm_ack = True                # en ALARM: reconocer
            print(">>> ALARMA RECONOCIDA | ACK=True")
        else:
            sample_count = 0                # fuera de ALARM: reset del contador
            last_sample_count = 0
            print(">>> Sin ALARM: contador de muestras reiniciado")

    last_button = current_button


# ===== Inicio =====
print("RETO 08 - Sistema multitarea (Wokwi, un nucleo)")
print(f"Sensor: {sensor_period} ms | Boton: {button_period} ms | UI: {ui_period} ms | Log: {log_period} ms")
print(f"Umbrales: WARNING >= {WARNING}% | ALARM >= {ALARM}% | Filtro: {BUFFER_SIZE} lecturas")
print("Boton: en ALARM = ACK (rojo fijo) | fuera de ALARM = reset del contador")

# Scheduler cooperativo: cada vuelta revisa a quien le toca, lo corre y sigue.
# El unico sleep es de 2 ms, para no girar el loop en vacio.
while True:
    now = ticks_ms()

    if due(now, next_sensor):
        sensor_task()
        next_sensor = now + sensor_period

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
    