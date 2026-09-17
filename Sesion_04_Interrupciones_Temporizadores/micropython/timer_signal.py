# =========================================================================
#  DO 02 - Señal de timer
#  Sesion 04: Interrupciones y temporizadores
#  Angel Rugerio Jimenez #201720
#
#  Demuestra que el temporizador NO bloquea: el main loop sigue imprimiendo
#  durante los 10 segundos de espera y el cambio de LED ocurre solo.
# =========================================================================

from machine import Pin, Timer
from time import sleep_ms

# Configuración de los pines de salida para cada LED
led_senal = Pin(15, Pin.OUT)   # GP15 - se enciende cuando el timer dispara
led_espera = Pin(14, Pin.OUT)  # GP14 - encendido mientras se espera

# Creación de la instancia del temporizador
timer = Timer(-1)

# Bandera global para comunicar el temporizador con el bucle principal
timer_disparado = False

# Función que se ejecuta automáticamente cuando el tiempo se agota
def timer_callback(t):
    global timer_disparado
    timer_disparado = True

# Configuración del estado inicial de los LEDs
led_senal.off()
led_espera.on()
print("Esperando 10 segundos para el cambio de LED...")

# Arranque del temporizador: 10'000 ms (10s) en modo de ejecución única
timer.init(
    mode = Timer.ONE_SHOT,
    period = 10000,
    callback = timer_callback
)

contador = 0

# Bucle principal continuo (no se detiene por el temporizador)
while True:
    print("MAIN TRABAJANDO:", contador)
    contador += 1

    # Revisa si la función callback ya cambió la bandera
    if timer_disparado:
        timer_disparado = False # Reinicio de la bandera para no repetir la acción

        # Inversión del estado físico de los componentes
        led_senal.on()
        led_espera.off()

        print("TIMER DISPARADO")
        print("GP15 (senal) =", led_senal.value())
        print("GP14 (espera) =", led_espera.value())
        print()

    # Pausa de medio segundo para cada ciclo del bucle principal
    sleep_ms(500)
