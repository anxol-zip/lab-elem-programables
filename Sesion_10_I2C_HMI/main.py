# =========================================================================
#  RETO 10 - Smart I2C HMI Monitor
#  Sesion 10: Comunicacion I2C + OLED HMI
#  Angel Rugerio Jiménez #201720
# =========================================================================

from machine import Pin, I2C, ADC
from ssd1306 import SSD1306_I2C
from time import ticks_ms, ticks_diff, sleep_ms

# ===== Hardware =====
SDA_PIN = 4
SCL_PIN = 5
I2C_FREQ = 400_000
OLED_ADDR = 0x3C                        # Si el scan reporta 0x3D, cambiarlo aqui

i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=I2C_FREQ)
adc = ADC(26)                           # GP26 - ADC0, cursor del potenciometro
button = Pin(16, Pin.IN, Pin.PULL_UP)   # GP16 - boton: libre = 1, presionado = 0
led_alarm = Pin(15, Pin.OUT)            # GP15 - LED rojo (solo en ALARM)

# ===== Parametros =====
WARNING = 50        # % a partir del cual el estado es WARNING
ALARM = 75          # % a partir del cual el estado es ALARM
PAGES = 3           # LIVE, I2C, STATS

sensor_period = 100     # ms -> 10 Hz
button_period = 50      # ms -> 20 Hz
display_period = 100    # ms -> 10 Hz
log_period = 1000       # ms -> 1 Hz

# ===== Scan: si la OLED no responde, no tiene caso seguir =====
devices = i2c.scan()
print("RETO 10 - Smart I2C HMI Monitor")
print(f"I2C listo: SDA=GP{SDA_PIN}, SCL=GP{SCL_PIN}, freq={I2C_FREQ // 1000} kHz")
print("Encontrados:", len(devices))
print("Decimal:", devices)
print("Hex:", [hex(address) for address in devices])

if OLED_ADDR not in devices:
    raise RuntimeError(f"OLED {hex(OLED_ADDR)} no detectada: revisa SDA/SCL/VCC/GND")

oled = SSD1306_I2C(128, 64, i2c, addr=OLED_ADDR)

# ===== Estado compartido entre tareas =====
page = 0
last_button = 1
raw_value = 0
percent_value = 0.0
state = "INIT"
samples = 0
min_value = 100.0
max_value = 0.0

# Cuando le toca a cada tarea
next_sensor = ticks_ms()
next_button = ticks_ms()
next_display = ticks_ms()
next_log = ticks_ms()


# ¿Ya llego (o ya paso) el momento target?
def due(now, target):
    return ticks_diff(now, target) >= 0


# ===== Decision =====
# Del umbral mas alto al mas bajo
def classify(percent):
    if percent >= ALARM:
        return "ALARM"
    elif percent >= WARNING:
        return "WARNING"
    else:
        return "NORMAL"


# ===== Dibujo =====
# Todo esto dibuja en RAM (framebuffer). A la OLED llega hasta oled.show().

# Franja superior invertida: titulo de la pagina y en cual vamos
def draw_header(title, number):
    oled.fill_rect(0, 0, 128, 11, 1)
    oled.text(title, 2, 2, 0)
    oled.text(f"{number}/{PAGES}", 102, 2, 0)


# Marco de 120 px, relleno proporcional en los 116 px de adentro y dos marcas
# arriba de la barra para ver donde empiezan WARNING y ALARM
def draw_bar(percent):
    x, y, w, h = 4, 46, 120, 12
    oled.rect(x, y, w, h, 1)
    inner = int((w - 4) * percent / 100)
    oled.fill_rect(x + 2, y + 2, inner, h - 4, 1)

    for mark in (WARNING, ALARM):
        oled.vline(x + 2 + (w - 4) * mark // 100, y - 3, 3, 1)


def draw_live(percent, state):
    draw_header("LIVE", 1)
    oled.text("ADC: {:5.1f}%".format(percent), 2, 16)

    # En ALARM el renglon se invierte: se distingue sin tener que leerlo
    if state == "ALARM":
        oled.fill_rect(0, 28, 128, 12, 1)
        oled.text("STATE: " + state, 2, 30, 0)
    else:
        oled.text("STATE: " + state, 2, 30)

    draw_bar(percent)


def draw_i2c():
    draw_header("I2C", 2)
    oled.text(f"SDA:GP{SDA_PIN} SCL:GP{SCL_PIN}", 2, 16)
    oled.text(f"FREQ: {I2C_FREQ // 1000} kHz", 2, 28)
    oled.text(f"DEV: {len(devices)}", 2, 40)
    oled.text(",".join(hex(address) for address in devices), 2, 52)


def draw_stats():
    draw_header("STATS", 3)
    oled.text("MIN: {:5.1f}%".format(min_value), 2, 16)
    oled.text("MAX: {:5.1f}%".format(max_value), 2, 30)
    oled.text(f"N: {samples}", 2, 44)


def draw_page(page, percent, state):
    if page == 0:
        draw_live(percent, state)
    elif page == 1:
        draw_i2c()
    else:
        draw_stats()


# ===== Tareas =====
# El sensor sigue midiendo aunque la pagina visible sea otra
def sensor_task():
    global raw_value, percent_value, state
    global samples, min_value, max_value

    raw_value = adc.read_u16()
    percent_value = raw_value * 100 / 65535
    state = classify(percent_value)

    samples += 1
    min_value = min(min_value, percent_value)
    max_value = max(max_value, percent_value)

    led_alarm.value(state == "ALARM")


# El boton se lee cada 50 ms y solo cuenta el CAMBIO 1 -> 0 (flanco de bajada):
# una pulsacion = una pagina, aunque se mantenga presionado.
def button_task():
    global page, last_button

    current_button = button.value()

    if last_button == 1 and current_button == 0:
        page = (page + 1) % PAGES
        print("Cambio a PAGE", page + 1)

    last_button = current_button


# Regla mental de la clase: limpiar -> dibujar -> show
def display_task():
    oled.fill(0)
    draw_page(page, percent_value, state)
    oled.show()


def log_task():
    print("raw=", raw_value,
          "percent=", round(percent_value, 1),
          "state=", state,
          "min=", round(min_value, 1),
          "max=", round(max_value, 1),
          "samples=", samples,
          "page=", page + 1)


# ===== Inicio =====
print(f"Umbrales: WARNING >= {WARNING}% | ALARM >= {ALARM}%")
print("Boton: cambia de pagina LIVE -> I2C -> STATS -> LIVE")

# Scheduler cooperativo del Reto 08: cada vuelta revisa a quien le toca.
# El unico sleep es de 2 ms, para no girar el loop en vacio.
while True:
    now = ticks_ms()

    if due(now, next_sensor):
        sensor_task()
        next_sensor = now + sensor_period

    if due(now, next_button):
        button_task()
        next_button = now + button_period

    if due(now, next_display):
        display_task()
        next_display = now + display_period

    if due(now, next_log):
        log_task()
        next_log = now + log_period

    sleep_ms(2)
