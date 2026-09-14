# =========================================================================
#  DO 02 - Señal de timer
#  Sesion 04: Interrupciones y temporizadores
#  Angel Rugerio Jimenez #201720
# =========================================================================

from machine import Pin, Timer
from time import sleep_ms
 
# Configuración de los pines de salida para cada LED
led_naranja = Pin(15, Pin.OUT)
led_rosa = Pin(14, Pin.OUT)

# Creación de la instancia del temporizador
timer = Timer(-1)
 
# Bandera global para comunicar el temporizador con el bucle principal
timer_disparado = False
 
# Función que se ejecuta automáticamente cuando el tiempo se agota
def timer_callback(t):
    global timer_disparado
    timer_disparado = True
 
# Configuración del estado inicial de los LEDs
led_naranja.off()
led_rosa.on()
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
        led_naranja.on()
        led_rosa.off()
 
        print("TIMER DISPARADO")
        print("GP15 (Naranja) =", led_naranja.value())
        print("GP14 (Rosa) =", led_rosa.value())
        print()
 
    # Pausa de medio segundo para cada ciclo del bucle principal
    sleep_ms(500)