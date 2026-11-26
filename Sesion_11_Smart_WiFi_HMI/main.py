# =========================================================================
#  RETO 11 - Smart Wi-Fi HMI
#  Sesion 11: Wi-Fi, HTTP y sockets
#  Angel Rugerio Jiménez #201720
# =========================================================================
#
#  Archivos en la raiz de la Pico: main.py, ssd1306.py y secrets.py
#  (secrets.py NO se sube a GitHub: copiar secrets_template.py y llenarlo)

import network
import socket
import json

from machine import Pin, PWM, I2C, ADC
from time import sleep_ms, ticks_ms, ticks_diff, localtime, time
from secrets import WIFI_SSID, WIFI_PASSWORD
from ssd1306 import SSD1306_I2C

# Bonus 3: NTP. Algunos firmwares no traen ntptime; sin el, no hay hora
try:
    import ntptime
except ImportError:
    ntptime = None

# ===== Hardware =====
LED_PWM_PIN = 15        # GP15 - LED con brillo variable (slider)
LED2_PIN = 14           # GP14 - LED digital (boton virtual)
ADC_PIN = 26            # GP26 - ADC0, cursor del potenciometro (bonus)
SDA_PIN = 4
SCL_PIN = 5
I2C_FREQ = 400_000
OLED_ADDR = 0x3C        # Si el scan reporta 0x3D, cambiarlo aqui
PORT = 80               # HTTP

# ===== Hora (bonus 3) =====
UTC_OFFSET = -6         # Puebla: UTC-6 todo el año (Mexico quito el horario de verano en 2022)
NTP_RETRY = 300_000     # ms -> si NTP fallo, reintentar cada 5 min

led_pwm = PWM(Pin(LED_PWM_PIN))
led_pwm.freq(1000)                      # 1 kHz: sin parpadeo visible
led2 = Pin(LED2_PIN, Pin.OUT)
adc = ADC(ADC_PIN)

# Bonus 1: LED integrado = indicador de conexion Wi-Fi.
# En la Pico W / Pico 2 W ese LED cuelga del chip Wi-Fi y se pide como "LED".
led_wifi = Pin("LED", Pin.OUT)

# ===== OLED: mismo arranque que el Reto 10 =====
i2c = I2C(0, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=I2C_FREQ)
devices = i2c.scan()
print("I2C:", [hex(address) for address in devices])

if OLED_ADDR not in devices:
    raise RuntimeError(f"OLED {hex(OLED_ADDR)} no detectada: revisa SDA/SCL/VCC/GND")

oled = SSD1306_I2C(128, 64, i2c, addr=OLED_ADDR)

# ===== Estado del sistema =====
# Lo leen las tres "vistas": la pagina web, la OLED y /api/status
pwm_percent = 0
led2_state = 0
request_count = 0
time_ok = False         # True cuando NTP ya ajusto el reloj


# ===== Wi-Fi (modo STA) =====
def get_sta_interface():
    # El nombre de la constante cambio entre versiones de MicroPython
    try:
        return network.WLAN(network.WLAN.IF_STA)
    except AttributeError:
        return network.WLAN(network.STA_IF)


def connect_wifi(ssid, password, timeout_ms=20000):
    wlan = get_sta_interface()
    wlan.active(True)

    if wlan.isconnected():
        return wlan

    try:
        wlan.disconnect()
        sleep_ms(200)
    except Exception:
        pass

    print("Conectando a:", ssid)
    wlan.connect(ssid, password)

    start = ticks_ms()
    while not wlan.isconnected():
        if ticks_diff(ticks_ms(), start) >= timeout_ms:
            raise RuntimeError(f"Timeout Wi-Fi (status={wlan.status()})")
        sleep_ms(250)

    print("Wi-Fi conectado | IP:", wlan.ifconfig()[0])
    return wlan


# ===== Servidor =====
# 0.0.0.0 = escuchar en cualquier interfaz de la Pico, puerto 80
def create_server(port=80):
    addr = socket.getaddrinfo("0.0.0.0", port)[0][-1]
    server = socket.socket()

    try:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except Exception:
        pass

    server.bind(addr)
    server.listen(2)

    # accept() se rinde cada segundo: asi el loop sigue vivo sin clientes
    try:
        server.settimeout(1)
    except Exception:
        pass

    return server


# ===== TODO 1 - PWM =====
# 0..100 % -> 0..65535 (resolucion de duty_u16)
def set_pwm(percent):
    global pwm_percent

    percent = max(0, min(100, int(percent)))
    duty = percent * 65535 // 100
    led_pwm.duty_u16(duty)
    pwm_percent = percent

    print(f"PWM = {percent}% | duty_u16 = {duty}")


# ===== TODO 2 - LED 2 =====
def toggle_led2():
    global led2_state

    led2_state = 1 - led2_state         # 0 -> 1, 1 -> 0
    led2.value(led2_state)

    print("LED2 =", "ON" if led2_state else "OFF")


# ===== Bonus 2 - Ambos LEDs =====
# state = 1 -> LED PWM al 100 % y LED2 ON; state = 0 -> los dos apagados
def set_all(state):
    global led2_state

    set_pwm(100 if state else 0)
    led2_state = state
    led2.value(led2_state)

    print("ALL =", "ON" if state else "OFF")


# ===== Bonus 4 - ADC =====
# Misma conversion que el Reto 10: 0..65535 -> 0..100 %
def read_adc_percent():
    return round(adc.read_u16() * 100 / 65535, 1)


# ===== Bonus 3 - NTP =====
# ntptime.settime() pone el reloj de la Pico en UTC.
# Si NTP no responde NO es error del sistema: solo no hay hora.
def sync_time():
    global time_ok

    if ntptime is None:
        print("NTP: este firmware no trae ntptime")
        return

    try:
        ntptime.settime()
        time_ok = True
        print("NTP OK | hora local:", clock_text())
    except Exception as exc:
        print("NTP no respondio:", exc)


# Hora local HH:MM:SS (UTC + UTC_OFFSET), o --:--:-- si no hay NTP
def clock_text():
    if not time_ok:
        return "--:--:--"

    t = localtime(time() + UTC_OFFSET * 3600)
    return "{:02d}:{:02d}:{:02d}".format(t[3], t[4], t[5])


# ===== TODO 3 - OLED =====
# Regla de la S10: limpiar -> dibujar -> show
def show_oled(ip):
    oled.fill(0)

    # Franja superior invertida, como los encabezados del Reto 10.
    # La hora (HH:MM) va a la derecha del titulo: asi no le quita renglon a nada
    oled.fill_rect(0, 0, 128, 11, 1)
    oled.text("WIFI HMI", 2, 2, 0)
    oled.text(clock_text()[:5], 86, 2, 0)

    oled.text(ip, 2, 14)
    oled.text(f"PWM: {pwm_percent}%", 2, 24)
    oled.text("LED2: " + ("ON" if led2_state else "OFF"), 2, 34)
    oled.text(f"REQ: {request_count}", 2, 44)
    oled.text("ADC: {:.1f}%".format(read_adc_percent()), 2, 54)

    oled.show()


def status_dict(ip):
    return {
        "ip": ip,
        "pwm": pwm_percent,
        "led2": led2_state,
        "requests": request_count,
        "adc": read_adc_percent(),
        "time": clock_text() if time_ok else None,
    }


# ===== Pagina HTML (la del starter) =====
# oninput solo actualiza el numero en el navegador mientras se arrastra;
# onchange manda UNA peticion a la Pico al soltar el slider.
HTML_TEMPLATE = """<!doctype html>
<html>
<head>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Pico Smart HMI</title>
<style>
body {
    font-family: Arial, sans-serif;
    background: #08131f;
    color: #eef7ff;
    margin: 0;
    padding: 18px;
}
.card {
    max-width: 620px;
    margin: auto;
    background: #13263a;
    padding: 24px;
    border-radius: 18px;
}
h1 {
    margin-top: 0;
    color: #62e6f0;
}
.panel {
    background: #0d1d2d;
    padding: 16px;
    margin: 14px 0;
    border-radius: 14px;
}
input[type=range] {
    width: 100%;
}
button {
    padding: 12px 18px;
    border: 0;
    border-radius: 10px;
    background: #1b9aaa;
    color: white;
    font-weight: bold;
    cursor: pointer;
}
.dot {
    display: inline-block;
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: #666;
}
code {
    color: #8be9fd;
}
</style>
</head>
<body>
<div class='card'>
<h1>Pico Smart HMI</h1>
<p>IP: <code>__IP__</code></p>
<p><span id='connDot' class='dot'></span> Conexion: <b id='connState'>...</b></p>
<p>Hora de la Pico (NTP): <b id='timeValue'>__TIME__</b></p>

<div class='panel'>
<h3>LED PWM - GP15</h3>
<p>Valor: <b id='pwmValue'>__PWM__%</b></p>
<input id='pwmSlider' type='range' min='0' max='100' value='__PWM__'
    oninput='previewPWM(this.value)'
    onchange='applyPWM(this.value)'>
</div>

<div class='panel'>
<h3>LED 2 - GP14</h3>
<p><span id='led2Dot' class='dot'></span> Estado: <b id='led2State'>__LED2_TEXT__</b></p>
<button onclick='toggleLed2()'>TOGGLE LED 2</button>
</div>

<div class='panel'>
<h3>Ambos LEDs</h3>
<button onclick='setAll(1)'>ALL ON</button>
<button onclick='setAll(0)'>ALL OFF</button>
</div>

<div class='panel'>
<h3>ADC - GP26</h3>
<p>Valor: <b id='adcValue'>__ADC__%</b></p>
</div>

<div class='panel'>
<p>Requests: <b id='requestValue'>__REQ__</b></p>
<button onclick='refreshStatus()'>REFRESH STATUS</button>
</div>

<script>
function previewPWM(value) {
    document.getElementById('pwmValue').textContent = value + '%';
}

// Bonus 1: verde si la Pico respondio, rojo si la peticion fallo
function setConnection(ok) {
    document.getElementById('connState').textContent = ok ? 'ONLINE' : 'SIN RESPUESTA';
    document.getElementById('connDot').style.background = ok ? '#43e97b' : '#ff5c5c';
}

function updateStatus(data) {
    document.getElementById('pwmSlider').value = data.pwm;
    document.getElementById('pwmValue').textContent = data.pwm + '%';
    document.getElementById('led2State').textContent = data.led2 ? 'ON' : 'OFF';
    document.getElementById('led2Dot').style.background = data.led2 ? '#43e97b' : '#666';
    document.getElementById('requestValue').textContent = data.requests;
    document.getElementById('adcValue').textContent = data.adc + '%';
    document.getElementById('timeValue').textContent = data.time || 'sin NTP';
    setConnection(true);
}

function getJSON(url) {
    fetch(url, {cache: 'no-store'})
        .then(function(response) { return response.json(); })
        .then(updateStatus)
        .catch(function() { setConnection(false); });
}

function applyPWM(value) { getJSON('/api/pwm?value=' + value); }
function toggleLed2()    { getJSON('/api/led2/toggle'); }
function setAll(state)   { getJSON('/api/all?state=' + state); }
function refreshStatus() { getJSON('/api/status'); }

refreshStatus();
// Cada 3 s: refresca el ADC y comprueba que la Pico siga respondiendo
setInterval(refreshStatus, 3000);
</script>
</div>
</body>
</html>
"""


def html_page(ip):
    page = HTML_TEMPLATE
    page = page.replace("__IP__", ip)
    page = page.replace("__PWM__", str(pwm_percent))
    page = page.replace("__REQ__", str(request_count))
    page = page.replace("__LED2_TEXT__", "ON" if led2_state else "OFF")
    page = page.replace("__ADC__", str(read_adc_percent()))
    page = page.replace("__TIME__", clock_text() if time_ok else "sin NTP")
    return page


# "/api/pwm?value=73" -> path = "/api/pwm", params = {"value": "73"}
def split_target(target):
    if "?" in target:
        path, query = target.split("?", 1)
    else:
        path, query = target, ""

    params = {}
    for item in query.split("&"):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        params[key] = value

    return path, params


# ===== TODO 4 - Router =====
# Cada ruta regresa (status, content_type, body)
def json_response(ip):
    return "200 OK", "application/json", json.dumps(status_dict(ip))


def error_response(status, message):
    return status, "application/json", json.dumps({"error": message})


def route(target, ip):
    path, params = split_target(target)

    # Chrome lo pide solo; 204 = "no hay nada que mandar"
    if path == "/favicon.ico":
        return "204 No Content", "text/plain", ""

    if path == "/":
        return "200 OK", "text/html; charset=utf-8", html_page(ip)

    if path == "/api/status":
        return json_response(ip)

    if path == "/api/pwm":
        # Se valida ANTES de llamar set_pwm(): set_pwm satura a 0..100,
        # y sin esto value=150 se volveria 100 en silencio en vez de un 400
        try:
            value = int(params["value"])
        except (KeyError, ValueError):
            return error_response("400 Bad Request", "value debe ser un entero 0..100")

        if not 0 <= value <= 100:
            return error_response("400 Bad Request", "value fuera de rango 0..100")

        set_pwm(value)
        return json_response(ip)

    if path == "/api/led2/toggle":
        toggle_led2()
        return json_response(ip)

    # Bonus 2: /api/all?state=1 enciende ambos, /api/all?state=0 los apaga
    if path == "/api/all":
        state = params.get("state")
        if state not in ("0", "1"):
            return error_response("400 Bad Request", "state debe ser 0 o 1")

        set_all(int(state))
        return json_response(ip)

    return error_response("404 Not Found", "ruta no existe: " + path)


# ===== Respuesta HTTP =====
# Content-Length en BYTES (despues de encode) + Connection: close
def send_response(client, status, content_type, body):
    if isinstance(body, str):
        body = body.encode()

    header = (
        "HTTP/1.1 {}\r\n"
        "Content-Type: {}\r\n"
        "Content-Length: {}\r\n"
        "Connection: close\r\n"
        "Cache-Control: no-store\r\n"
        "\r\n"
    ).format(status, content_type, len(body))

    client.write(header.encode())
    if body:
        client.write(body)


# ===== Inicio =====
wlan = connect_wifi(WIFI_SSID, WIFI_PASSWORD)
ip = wlan.ifconfig()[0]

sync_time()
last_ntp = ticks_ms()

set_pwm(0)
led2.value(led2_state)
led_wifi.value(wlan.isconnected())
show_oled(ip)

server = create_server(PORT)

print()
print("====================================")
print(" RETO 11 - SMART Wi-Fi HMI")
print("====================================")
print(f"Abre: http://{ip}/   (http, NO https)")
print()

last_wait = ticks_ms()

# Servidor iterativo: un cliente a la vez.
# accept() -> recv() -> route() -> send_response() -> close()
while True:
    client = None

    try:
        client, remote = server.accept()
        raw = client.recv(2048)

        if not raw:
            continue

        # Primera linea: "GET /api/pwm?value=37 HTTP/1.1"
        first_line = raw.split(b"\r\n", 1)[0].decode()
        parts = first_line.split(" ")
        target = parts[1] if len(parts) >= 2 else "/"

        request_count += 1

        status, content_type, body = route(target, ip)
        send_response(client, status, content_type, body)

        print(f"{remote[0]} -> {target} -> {status}")

        # La OLED refleja el estado despues de cada peticion
        show_oled(ip)

    except OSError:
        # Timeout de accept(): nadie se conecto en este segundo.
        # Se aprovecha para actualizar lo que cambia sin peticiones:
        # el LED de conexion y el ADC en la OLED (~1 vez por segundo)
        # (try propio: un error aqui ya no lo atraparia el except de abajo)
        try:
            led_wifi.value(wlan.isconnected())

            # Sin hora todavia: reintentar NTP de vez en cuando, no en cada vuelta
            if not time_ok and ticks_diff(ticks_ms(), last_ntp) >= NTP_RETRY:
                sync_time()
                last_ntp = ticks_ms()

            show_oled(ip)
        except Exception as exc:
            print("IDLE ERROR:", exc)

        if ticks_diff(ticks_ms(), last_wait) >= 5000:
            print(f"Servidor vivo: http://{ip}/")
            last_wait = ticks_ms()

    except Exception as exc:
        # Cualquier otro error se reporta, pero el servidor sigue
        print("SERVER ERROR:", exc)

    finally:
        if client:
            try:
                client.close()
            except Exception:
                pass
