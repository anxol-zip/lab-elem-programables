# =========================================================================
#  Reto 03 - Semaforo peatonal interactivo
#  Sesion 03: GPIO, pull-up/pull-down y debounce
#  Angel Rugerio Jimenez #201720
# =========================================================================
#
#  Pinout
#  -------------------------------------------------
#   Auto rojo      GP15      Peaton rojo    GP12
#   Auto amarillo  GP14      Peaton verde   GP11
#   Auto verde     GP13      Boton          GP16
#
#  Maquina de estados
#  -------------------------------------------------
#   S0 REPOSO      autos VERDE      peaton ROJO
#   S1 TRANSICION  autos AMARILLO   peaton ROJO
#   S2 CRUCE       autos ROJO       peaton VERDE
#   S3 FIN         autos ROJO       peaton VERDE parpadeando
#
#  Seguridad
#   Auto verde y peaton verde NUNCA pueden estar encendidos a la vez.
#   Aqui no se deja como comentario: set_lights() lo verifica en cada
#   cambio de estado y se niega a aplicar una combinacion peligrosa.

from machine import Pin
from time import sleep_ms

# --- Pines -------------------------------------------------------------
CAR_RED_PIN = 15
CAR_YELLOW_PIN = 14
CAR_GREEN_PIN = 13
PED_RED_PIN = 12
PED_GREEN_PIN = 11
BUTTON_PIN = 16

# --- Tiempos (Nivel 3: ajustables sin tocar la logica) ------------------
TRANSITION_MS = 1500   # S1 - amarillo, los autos frenan
CROSSING_MS = 4000     # S2 - el peaton cruza
BLINK_TIMES = 4        # S3 - parpadeos de aviso "se acaba el tiempo"
BLINK_MS = 300
RECOVERY_MS = 500      # colchon antes de devolver el verde a los autos
DEBOUNCE_MS = 30
POLL_MS = 10

# --- Configuracion de GPIO ---------------------------------------------
car_red = Pin(CAR_RED_PIN, Pin.OUT)
car_yellow = Pin(CAR_YELLOW_PIN, Pin.OUT)
car_green = Pin(CAR_GREEN_PIN, Pin.OUT)
ped_red = Pin(PED_RED_PIN, Pin.OUT)
ped_green = Pin(PED_GREEN_PIN, Pin.OUT)

button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)


# --- Funciones ---------------------------------------------------------

def set_lights(car_r, car_y, car_g, ped_r, ped_g):
    if car_g and ped_g:
        print("!! set_lights() rechazado: auto VERDE + peaton VERDE simultaneos")
        return
    
    car_red.value(car_r)
    car_yellow.value(car_y)
    car_green.value(car_g)
    ped_red.value(ped_r)
    ped_green.value(ped_g)


def cars_go():
    """S0 REPOSO - los autos pasan, el peaton espera."""
    set_lights(0, 0, 1, 1, 0)
    print("S0 REPOSO      | autos VERDE    | peaton ROJO")


def cars_prepare_to_stop():
    """S1 TRANSICION - los autos frenan."""
    set_lights(0, 1, 0, 1, 0)
    print("S1 TRANSICION  | autos AMARILLO | peaton ROJO")


def pedestrians_go():
    """S2 CRUCE - el peaton pasa, los autos detenidos."""
    set_lights(1, 0, 0, 0, 1)
    print("S2 CRUCE       | autos ROJO     | peaton VERDE")


def pedestrians_hurry():
    """S3 FIN - aviso de fin de cruce; los autos siguen en rojo."""
    print("S3 FIN         | autos ROJO     | peaton VERDE parpadeando")
    for _ in range(BLINK_TIMES):
        ped_green.value(0)
        sleep_ms(BLINK_MS)
        ped_green.value(1)
        sleep_ms(BLINK_MS)


def crossing_sequence():
    """Secuencia completa disparada por una peticion del peaton."""
    print(">> PETICION DE CRUCE ACEPTADA")

    cars_prepare_to_stop()
    sleep_ms(TRANSITION_MS)

    pedestrians_go()
    sleep_ms(CROSSING_MS)

    pedestrians_hurry()

    set_lights(1, 0, 0, 1, 0)
    sleep_ms(RECOVERY_MS)

    cars_go()
    print(">> SECUENCIA COMPLETA - sistema en reposo\n")


# --- Main -------------------------------------------------------------
# Encabezado por serial: separa el arranque del sistema de la traza de estados
print("=" * 52) 
print("Reto 03 - Semaforo peatonal interactivo")
print("Boton en GP{} con pull-up interno (presionado = 0)".format(BUTTON_PIN))
print("=" * 52)

cars_go()

last = 1   # boton libre por el pull-up

while True:
    now = button.value()

    if last == 1 and now == 0:
        sleep_ms(DEBOUNCE_MS)

        if button.value() == 0:
            crossing_sequence()

            while button.value() == 0:
                sleep_ms(POLL_MS)

    last = now
    sleep_ms(POLL_MS)
