# =========================================================================
#  RE 06 + BONUS - Smart Motor Controller con botones
#  Sesion 06: PWM + Puente H (L298N) + Motor DC
#  Angel Rugerio Jiménez #201720
#  Axel Garcia Arellano #201251
#
#  El controlador de challenge_secuencia.py, pero manejado con botones:
#    FORWARD (GP14): arranca hacia adelante a 25 %; cada click extra sube
#                    un nivel (25 -> 50 -> 75 -> 100 %).
#    REVERSE (GP15): lo mismo hacia atras.
#    STOP    (GP16): rampa a 0 % y STOP. Interrumpe cualquier aceleracion.
#  Cambiar de FORWARD a REVERSE (o al reves) pasa siempre por 0 %.
#
#  Botones: GPx -> boton -> GND, con pull-up interno (sin resistencias).
#  El potenciometro de GP26 esta en el diagrama de Wokwi pero no se usa:
#  leerlo requiere ADC, que se ve en la siguiente sesion.
# =========================================================================

from machine import Pin, PWM
from time import sleep_ms, ticks_ms, ticks_diff

# ---------------- Ajustes del motor fisico (iguales a challenge_secuencia.py) ----------------
PWM_FREQ = 100          # Hz. Frecuencia baja = mas torque en motores chicos
MIN_DUTY = 40           # % real minimo con el que el motor SI gira (zona muerta)
KICK_MS = 120           # empujon al 100 % cuando arranca desde 0

# Pines del puente H
IN1 = Pin(2, Pin.OUT)   # GP2 - direccion
IN2 = Pin(3, Pin.OUT)   # GP3 - direccion
ENA = PWM(Pin(4))       # GP4 - velocidad por PWM
ENA.freq(PWM_FREQ)

# Todo en 0 desde el inicio para que el motor no se mueva al encender la Pico
IN1.value(0)
IN2.value(0)
ENA.duty_u16(0)

# Botones con pull-up interno (presionado = 0)
btn_forward = Pin(14, Pin.IN, Pin.PULL_UP)
btn_reverse = Pin(15, Pin.IN, Pin.PULL_UP)
btn_stop = Pin(16, Pin.IN, Pin.PULL_UP)

# Parametros
PASO_RAMPA = 5          # % que cambia la velocidad en cada paso
DELAY_RAMPA_MS = 100    # tiempo entre pasos
PAUSA_INVERSION_MS = 500  # motor detenido antes de cambiar el sentido
PASO_NIVEL = 25         # cada click en la misma direccion sube 25 %
DEBOUNCE_MS = 80        # ventana antirrebote dentro de la ISR

# Constantes numericas para la direccion
DETENIDO = 0
ADELANTE = 1
REVERSA = 2

# Constantes numericas para los comandos de los botones
NINGUNO = 0
CMD_FORWARD = 1
CMD_REVERSE = 2
CMD_STOP = 3

# Variables globales de control
velocidad_actual = 0
direccion_actual = DETENIDO
comando_pendiente = NINGUNO   # lo escribe la ISR, lo consume el main loop
ultimo = [0, 0, 0]            # ultimo flanco aceptado de FORWARD, REVERSE y STOP


# ---------------- Funciones base (iguales a challenge_secuencia.py) ----------------
# Traduce el % logico (0-100) a duty real saltando la zona muerta.
def duty_real(percent):
    if percent == 0:
        return 0
    real = MIN_DUTY + (100 - MIN_DUTY) * percent / 100
    return int(real * 65535 / 100)


def set_speed(percent):
    global velocidad_actual
    percent = int(max(0, min(100, percent)))   # saturacion: 0 <= percent <= 100

    # Si venimos de 0 y vamos a movernos, empujon para vencer la inercia
    if velocidad_actual == 0 and percent > 0:
        ENA.duty_u16(65535)
        sleep_ms(KICK_MS)

    ENA.duty_u16(duty_real(percent))
    velocidad_actual = percent


def forward():
    global direccion_actual
    IN1.value(1)
    IN2.value(0)
    direccion_actual = ADELANTE


def reverse():
    global direccion_actual
    IN1.value(0)
    IN2.value(1)
    direccion_actual = REVERSA


def stop():
    global direccion_actual
    set_speed(0)
    IN1.value(0)
    IN2.value(0)
    direccion_actual = DETENIDO


# ---------------- Rampa ----------------
# Igual a la de challenge_secuencia.py, con una diferencia: si llega un
# STOP a mitad de una ACELERACION, la rampa se abandona para que el main
# loop atienda el STOP de inmediato. Las desaceleraciones nunca se cortan:
# ya van hacia 0 %.
def ramp_to(start, end, step=10, delay_ms=100):
    if start == end:
        set_speed(end)
        return

    if start < end:
        paso = step
        etiqueta = "Acelerando"
    else:
        paso = -step            # si start > end el paso debe ser negativo
        etiqueta = "Desacelerando"

    for speed in range(start, end, paso):
        if start < end and comando_pendiente == CMD_STOP:
            print("[STOP] Aceleracion interrumpida")
            return
        set_speed(speed)
        print(f"{etiqueta}: {speed} %")
        sleep_ms(delay_ms)

    set_speed(end)
    print(f"{etiqueta}: {end} %")


# ---------------- Cambio seguro de direccion (igual a challenge_secuencia.py) ----------------
def cambiar_direccion(nueva):
    if nueva == direccion_actual:
        return

    if velocidad_actual > 0:
        print("[SEGURIDAD] Bajando a 0 % antes de cambiar de direccion")
        ramp_to(velocidad_actual, 0, PASO_RAMPA, DELAY_RAMPA_MS)

    stop()
    sleep_ms(PAUSA_INVERSION_MS)

    if nueva == ADELANTE:
        print("[DIRECCION] FORWARD")
        forward()
    elif nueva == REVERSA:
        print("[DIRECCION] REVERSE")
        reverse()


# ---------------- Interrupciones de los botones ----------------
# La ISR solo registra que boton se presiono: la rampa tarda cientos de ms
# y no puede correr dentro de una interrupcion. El trabajo lo hace el main.
def registrar(indice, comando):
    global comando_pendiente
    ahora = ticks_ms()
    if ticks_diff(ahora, ultimo[indice]) < DEBOUNCE_MS:
        return
    ultimo[indice] = ahora
    comando_pendiente = comando


def irq_forward(pin):
    registrar(0, CMD_FORWARD)


def irq_reverse(pin):
    registrar(1, CMD_REVERSE)


def irq_stop(pin):
    registrar(2, CMD_STOP)


# ---------------- Acciones del main loop ----------------
# FORWARD / REVERSE: si el motor ya va en esa direccion, sube un nivel;
# si no, cambio seguro de direccion y arranque en el primer nivel.
def mover(direccion, nombre):
    print(f"\n[BOTON] {nombre}")

    if direccion_actual == direccion:
        nivel = velocidad_actual + PASO_NIVEL
        if nivel > 100:
            print(f"[INFO] {nombre} ignorado: ya esta al 100 %")
            return
    else:
        cambiar_direccion(direccion)
        nivel = PASO_NIVEL

    ramp_to(velocidad_actual, nivel, PASO_RAMPA, DELAY_RAMPA_MS)
    if velocidad_actual == nivel:
        print(f"[NIVEL] {nivel} %")


def detener():
    print("\n[BOTON] STOP")
    if velocidad_actual > 0:
        ramp_to(velocidad_actual, 0, PASO_RAMPA, DELAY_RAMPA_MS)
    stop()
    print("[STOP] Motor detenido")


# ---------------- Inicio ----------------
btn_forward.irq(trigger=Pin.IRQ_FALLING, handler=irq_forward)
btn_reverse.irq(trigger=Pin.IRQ_FALLING, handler=irq_reverse)
btn_stop.irq(trigger=Pin.IRQ_FALLING, handler=irq_stop)

print("RE 06 - SMART MOTOR CONTROLLER CON BOTONES")
print("GP14=FORWARD  GP15=REVERSE  GP16=STOP  (teclas F, R, S en Wokwi)")
print("Cada click en la misma direccion sube 25 %")
stop()

# El main loop no pregunta por los botones: solo ejecuta lo que dejo la ISR
while True:
    if comando_pendiente != NINGUNO:
        comando = comando_pendiente
        comando_pendiente = NINGUNO

        if comando == CMD_FORWARD:
            mover(ADELANTE, "FORWARD")
        elif comando == CMD_REVERSE:
            mover(REVERSA, "REVERSE")
        elif comando == CMD_STOP:
            detener()

    sleep_ms(20)
