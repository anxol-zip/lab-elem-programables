# =========================================================================
#  RE 04 - Juego de tiempo de reacción
#  Sesion 04: Interrupciones y temporizadores
#  Angel Rugerio Jimenez #201720
# =========================================================================

from machine import Pin, Timer
from time import ticks_ms, ticks_diff, sleep_ms
from random import randint
 
# Componentes físicos
led_reaccion = Pin(14, Pin.OUT) # LED que debes presionar al ver encendido
led_espera = Pin(15, Pin.OUT)   # LED que indica que la ronda está en espera
boton_jugador = Pin(16, Pin.IN, Pin.PULL_UP)
 
# Constantes numéricas para la máquina de estados
ESTADO_ESPERANDO = 0
ESTADO_LISTO = 1
ESTADO_TERMINADO = 2
 
# Variables globales de control
estado_actual = ESTADO_TERMINADO
tiempo_inicio_ms = 0
tiempo_reaccion_ms = 0
resultado_listo = False
salida_falsa = False
ultimo_click_ms = 0
numero_ronda = 0
 
# Iniciación del temporizador (con la mala practica de Wicho de ponerlo en -1)
temporizador = Timer(-1)
 
# Callback: Se ejecuta cuando el tiempo aleatorio termina (¡momento de presionar!)
def encender_senal(t):
    global estado_actual, tiempo_inicio_ms
    led_reaccion.on()
    led_espera.off()
    tiempo_inicio_ms = ticks_ms() # Guarda el cronómetro exacto en que encendió la luz
    estado_actual = ESTADO_LISTO
 
# Prepara una nueva ronda y reinicia las banderas lógicas
def iniciar_ronda():
    global estado_actual, resultado_listo, salida_falsa, numero_ronda
    numero_ronda += 1
    led_reaccion.off()
    led_espera.on()
    
    resultado_listo = False
    salida_falsa = False
    estado_actual = ESTADO_ESPERANDO
 
    demora_ms = randint(1000, 10000) # El tiempo de espera será entre 1 y 10 segundos
    print(20 * "=") 
    print(f"\nRonda {numero_ronda}")
    print("Espera la luz de reacción. No presiones antes.")
    
    # Inicia la cuenta regresiva oculta para esta ronda
    temporizador.init(mode = Timer.ONE_SHOT, period = demora_ms, callback = encender_senal)
 
# Interrupción IRQ: Evalúa cuándo presionaste el botón respecto al estado del juego
def detectar_pulsacion(pin):
    global estado_actual, tiempo_reaccion_ms, resultado_listo, salida_falsa, ultimo_click_ms
 
    ahora = ticks_ms()
    
    # Debounce (antirrebote de 80ms)
    if ticks_diff(ahora, ultimo_click_ms) < 80:
        return
    ultimo_click_ms = ahora
 
    # ÉXITO: Presionaste después de que la luz encendió
    if estado_actual == ESTADO_LISTO:
        tiempo_reaccion_ms = ticks_diff(ahora, tiempo_inicio_ms)
        led_reaccion.off()
        resultado_listo = True
        estado_actual = ESTADO_TERMINADO
 
    # FALLO: Presionaste antes de que encendiera la luz
    elif estado_actual == ESTADO_ESPERANDO:
        temporizador.deinit() # Cancela la señal que estaba programada para encender
        salida_falsa = True
        resultado_listo = True
        estado_actual = ESTADO_TERMINADO
 
# Configuración del botón para disparar la interrupción al ser presionado
boton_jugador.irq(trigger = Pin.IRQ_FALLING, handler = detectar_pulsacion)
 
print("JUEGO DE LOS REFLEJOS")
iniciar_ronda()
 
# Bucle principal: Solo gestiona la consola y reinicia el juego basándose en los resultados
while True:
    if resultado_listo:
        if salida_falsa:
            print("SALIDA EN FALSO: Presionaste antes de la señal.")
        else:
            print(f"Tiempo de reacción: {tiempo_reaccion_ms} ms")
 
        sleep_ms(1800) # Pausa de legibilidad para ver el resultado
 
        # Seguro: Obliga al usuario a soltar el botón antes de iniciar la nueva ronda
        while boton_jugador.value() == 0:
            sleep_ms(10)
           
        iniciar_ronda()
       
    sleep_ms(20) # Pausa de estabilización del bucle infinito