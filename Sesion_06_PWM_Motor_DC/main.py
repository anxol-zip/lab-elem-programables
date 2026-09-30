# =========================================================================
#  RETO 06 - Smart Motor Controller
#  Sesion 06: PWM + Puente H (L298N) + Motor DC
#  Angel Rugerio Jiménez #201720
#  Axel Garcia Arellano #201251
#
#  IN1/IN2 deciden hacia donde gira el motor, y el ENA (PWM) que tan
#  rapido. Toda la velocidad cambia por rampas <ramp_to()> y el sentido solo se
#  invierte con el motor en 0 %, por seguridad del motor.
#  
#  Dejamos los botones y el potenciometro aunque no se usan, porque pues venian
#  en la plantilla.
# =========================================================================

from machine import Pin, PWM
from time import sleep_ms

# ===== Cosas para el funcionamiento físico =====
# Ajustes del motor físico
PWM_FREQ = 100      # Hz. Frecuencia baja = mas torque en motores pequeños
MIN_DUTY = 40       # % real minimo con el que el motor SI gira (evitar la zona muerta)
KICK_MS = 120       # Empujon al 100 % cuando arranca desde 0 (reposo)

# Pines del puente H
IN1 = Pin(2, Pin.OUT)   # GP2 - direccion
IN2 = Pin(3, Pin.OUT)   # GP3 - direccion
ENA = PWM(Pin(4))       # GP4 - velocidad por PWM
ENA.freq(PWM_FREQ)      # Asignamos la frecuencia

# Todo en 0 desde el inicio para que el motor no se mueva al encender la Pico, por seguridad
IN1.value(0)
IN2.value(0)
ENA.duty_u16(0)

# Parametros de la demostracion
PASO_RAMPA = 5              # % que cambia la velocidad en cada paso
DELAY_RAMPA_MS = 100        # Tiempo entre pasos -> 0 a 100 % en 2 s
MANTENER_MS = 2000          # Tiempo sostenido a velocidad constante
PAUSA_INVERSION_MS = 500    # Motor detenido antes de cambiar el sentido
PAUSA_CICLO_MS = 3000       # Descanso entre una demostracion completa y la siguiente
NIVELES = [25, 50, 75, 100] # Niveles donde se va a sostener el motor

# Constantes numericas para la direccion
DETENIDO = 0
ADELANTE = 1
REVERSA = 2

# Variables globales de control
velocidad_actual = 0
direccion_actual = DETENIDO


# ===== Funciones base =====
# Traduce el % logico (0-100) a duty real saltando la zona muerta
def duty_real(percent):
    if percent == 0:
        return 0
    real = MIN_DUTY + (100 - MIN_DUTY) * percent / 100
    return int(real * 65535 / 100)

def set_speed(percent):
    global velocidad_actual
    percent = int(max(0, min(100, percent)))   # 0 <= percent <= 100

    # Si venimos de 0 y vamos a movernos, metemos el empujon para vencer la inercia
    if velocidad_actual == 0 and percent > 0:
        ENA.duty_u16(65535)
        sleep_ms(KICK_MS)

    ENA.duty_u16(duty_real(percent))
    velocidad_actual = percent


# ===== Funciones de movimiento =====
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


# ===== TODO 1: DO 04 ---> rampas de velocidad =====
# Sube o baja de start a end de step en step. range() excluye su limite,
# asi que al final se fija end a mano: la rampa siempre termina exacta,
# aunque la distancia no sea multiplo del paso (ej. 0 -> 75 con paso 10).
def ramp_to(start, end, step=10, delay_ms=100):
    if start == end:
        set_speed(end)
        return

    if start < end:
        paso = step
        etiqueta = "Acelerando"
    else:
        paso = -step            # Si start > end, el paso debe ser negativo
        etiqueta = "Desacelerando"

    for speed in range(start, end, paso):
        set_speed(speed)
        print(f"{etiqueta}: {speed} %")
        sleep_ms(delay_ms)

    set_speed(end)
    print(f"{etiqueta}: {end} %")


# === Cambio de dirección ===
# Nunca se invierte en movimiento, primero se pone la rampa a 0 %, pausa con el
# motor detenido y solo entonces se cambia IN1/IN2. En realidad, no se usa en 
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


def mantener(ms):
    print(f"[MANTENER] {velocidad_actual} % durante {ms} ms")
    sleep_ms(ms)


# === Etapas de la demostración ===
# Se cambian las velocidades al 25/50/75/100 %. Entre niveles se usan las
# rampas, para que ningun cambio de velocidad sea un escalon.
def prueba_niveles():
    print("\n########## PRUEBA DE VELOCIDADES (DO 04) ##########")
    cambiar_direccion(ADELANTE)
    for nivel in NIVELES:
        ramp_to(velocidad_actual, nivel, PASO_RAMPA, DELAY_RAMPA_MS)
        print(f"[NIVEL] {nivel} %")
        mantener(MANTENER_MS)
    ramp_to(velocidad_actual, 0, PASO_RAMPA, DELAY_RAMPA_MS)
    print("[STOP] Motor detenido")
    stop()
    sleep_ms(PAUSA_INVERSION_MS)


# ===== TODO 2: Secuencia del CHALLENGE 06 ---> forward, rampa, hold, rampa... =====
def secuencia_challenge():
    print("\n########## CHALLENGE 06 ##########")
    cambiar_direccion(ADELANTE)                                 # 1) FORWARD
    ramp_to(0, 100, PASO_RAMPA, DELAY_RAMPA_MS)                 # 2) rampa 0 -> 100
    mantener(MANTENER_MS)                                       # 3) mantener 2 s
    cambiar_direccion(REVERSA)                                  # 4) rampa 100 -> 0 (gracias al if de seguridad) y 5) REVERSE (ya en 0 %)
    ramp_to(0, 75, PASO_RAMPA, DELAY_RAMPA_MS)                  # 6) rampa 0 -> 75
    mantener(MANTENER_MS)                                       # 7) mantener 2 s
    ramp_to(75, 0, PASO_RAMPA, DELAY_RAMPA_MS)                  # 8) rampa 75 -> 0
    print("[STOP] Motor detenido")
    stop()                                                      # 9) STOP


# ===== Inicio =====
print("RETO 06 - SMART MOTOR CONTROLLER")
print(f"Pines: GP2 = IN1, GP3 = IN2, GP4 = ENA/PWM @ ({PWM_FREQ} Hz)")
print(f"Zona muerta compensada: 1 % logico = {MIN_DUTY} % real")
stop()
sleep_ms(1000)

# La demostracion se repite en ciclos
numero_ciclo = 0

while True:
    numero_ciclo += 1
    print(60 * "=")
    print(f"    CICLO {numero_ciclo}")
    prueba_niveles()
    secuencia_challenge()
    sleep_ms(PAUSA_CICLO_MS)
