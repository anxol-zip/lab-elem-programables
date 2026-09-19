# Escape Room de Hardware - Primer Examen Parcial
# # Angel Rugerio Jiménez y Axel García Arellano

from machine import Pin, Timer
from time import ticks_ms, ticks_diff, sleep_ms

# ---------------- Pines ----------------
btn_a = Pin(18, Pin.IN, Pin.PULL_UP)   # Boton A (presionado = 0)
btn_b = Pin(16, Pin.IN, Pin.PULL_UP)   # Boton B (presionado = 0)
led_rojo = Pin(12, Pin.OUT)
led_amarillo = Pin(13, Pin.OUT)
led_verde = Pin(14, Pin.OUT)

# ---------------- Tiempos (ms) ----------------
T_ESPERA_B = 5000    # ventana para presionar B
T_ACCESO = 3000      # verde encendido
T_BLOQUEO = 10000    # bloqueo de seguridad
T_REBOTE = 250       # antirrebote: ignora flancos muy seguidos
MAX_FALLOS = 3

# ---------------- Estados ----------------
BLOQUEADO = 0
ESPERANDO_B = 1
ACCESO = 2
BLOQUEO_SEGURIDAD = 3

estado = BLOQUEADO
fallos = 0
ultimo = [0, 0]      # ultimo flanco aceptado de A y de B (ticks_ms)

# ---------------- Timers ONE_SHOT ----------------
tim_espera = Timer(-1)    # 5 s esperando B
tim_acceso = Timer(-1)    # 3 s de acceso
tim_bloqueo = Timer(-1)   # 10 s de bloqueo


# ---------------- Utilidades ----------------
def leds(rojo, amarillo, verde):
    led_rojo.value(rojo)
    led_amarillo.value(amarillo)
    led_verde.value(verde)


def cancelar_timers():
    tim_espera.deinit()
    tim_acceso.deinit()
    tim_bloqueo.deinit()


def banner():
    print("\n==============================")
    print("[LISTO] SISTEMA BLOQUEADO")
    print("Secuencia correcta: A -> B")
    print("==============================")


# ---------------- Cambios de estado ----------------
def ir_bloqueado(mostrar_banner):
    global estado
    cancelar_timers()
    estado = BLOQUEADO
    leds(1, 0, 0)
    if mostrar_banner:
        banner()


def entrar_bloqueo_seguridad():
    global estado
    cancelar_timers()
    estado = BLOQUEO_SEGURIDAD
    leds(1, 0, 0)
    print("\n[BLOQUEO] 3 errores detectados")
    print("[BLOQUEO] Sistema bloqueado 10 segundos")
    tim_bloqueo.init(mode=Timer.ONE_SHOT, period=T_BLOQUEO, callback=fin_bloqueo)


def registrar_fallo(mensaje):
    global fallos
    tim_espera.deinit()
    fallos += 1
    print("\n" + mensaje)
    print("[ERROR] Intentos fallidos:", fallos)
    if fallos >= MAX_FALLOS:
        entrar_bloqueo_seguridad()
    else:
        ir_bloqueado(False)
        print("[LISTO] Intenta nuevamente con A -> B")


# ---------------- Eventos de botones ----------------
def evento_a(pin):
    global estado
    if estado == BLOQUEADO:
        estado = ESPERANDO_B
        leds(0, 1, 0)
        print("\n[A] Boton A detectado")
        print("[ESPERA] Presiona B antes de 5 segundos")
        tim_espera.init(mode=Timer.ONE_SHOT, period=T_ESPERA_B, callback=timeout)
    elif estado == ESPERANDO_B:
        # No reinicia la ventana de 5 s
        print("[INFO] A ignorado: ya se espera B")
    elif estado == ACCESO:
        print("[INFO] A ignorado: acceso activo")
    else:
        print("[INFO] A ignorado: bloqueo de seguridad")


def evento_b(pin):
    global estado
    if estado == ESPERANDO_B:
        tim_espera.deinit()
        estado = ACCESO
        leds(0, 0, 1)
        print("\n[B] Boton B detectado")
        print("[OK] ACCESO CONCEDIDO")
        print("[TIMER] Acceso activo durante 3 segundos")
        tim_acceso.init(mode=Timer.ONE_SHOT, period=T_ACCESO, callback=fin_acceso)
    elif estado == BLOQUEADO:
        registrar_fallo("[ERROR] B fue presionado antes que A")
    elif estado == ACCESO:
        print("[INFO] B ignorado: acceso activo")
    else:
        print("[INFO] B ignorado: bloqueo de seguridad")


# ---------------- Eventos de timers ----------------
def timeout(t):
    if estado == ESPERANDO_B:   # evita actuar si B ya llego
        registrar_fallo("[TIMEOUT] No se presiono B antes de 5 segundos")


def fin_acceso(t):
    if estado == ACCESO:
        print("\n[TIMER] Fin del acceso")
        ir_bloqueado(True)


def fin_bloqueo(t):
    global fallos
    if estado == BLOQUEO_SEGURIDAD:
        fallos = 0
        print("\n[TIMER] Fin del bloqueo")
        print("[RESET] Intentos fallidos = 0")
        ir_bloqueado(True)


# ---------------- Antirrebote ----------------
# Ignora flancos si paso menos de T_REBOTE ms desde el ultimo aceptado
def irq_a(pin):
    ahora = ticks_ms()
    if ticks_diff(ahora, ultimo[0]) < T_REBOTE:
        return
    ultimo[0] = ahora
    evento_a(pin)


def irq_b(pin):
    ahora = ticks_ms()
    if ticks_diff(ahora, ultimo[1]) < T_REBOTE:
        return
    ultimo[1] = ahora
    evento_b(pin)


# ---------------- Inicio ----------------
btn_a.irq(trigger=Pin.IRQ_FALLING, handler=irq_a)
btn_b.irq(trigger=Pin.IRQ_FALLING, handler=irq_b)
ir_bloqueado(True)

# El programa principal no revisa botones: todo ocurre por interrupciones
while True:
    sleep_ms(20)
