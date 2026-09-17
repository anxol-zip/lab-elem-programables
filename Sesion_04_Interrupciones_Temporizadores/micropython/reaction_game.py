# =========================================================================
#  RE 04 - Juego de tiempo de reacción
#  Sesion 04: Interrupciones y temporizadores
#  Angel Rugerio Jimenez #201720
# =========================================================================

from machine import Pin, Timer
from time import ticks_ms, ticks_diff, sleep_ms
from random import randint

# Componentes físicos
led_senal = Pin(15, Pin.OUT)   # LED que debes presionar al ver encendido
led_espera = Pin(14, Pin.OUT)  # LED que indica que la ronda está en espera
boton_jugador = Pin(16, Pin.IN, Pin.PULL_UP)

# Parámetros ajustables
INTENTOS_SERIE = 5     # Nivel 3: la serie se cierra a los 5 intentos válidos
DEBOUNCE_MS = 80       # Nivel 2: ventana antirrebote dentro de la ISR
ESPERA_MIN_MS = 1000   # Rango del tiempo aleatorio antes de la señal
ESPERA_MAX_MS = 10000
PAUSA_RESULTADO_MS = 1800

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

# Nivel 3: registro de la serie
tiempos = []          # tiempos válidos, en ms
salidas_falsas = 0    # cuántas veces se presionó antes de la señal

# Iniciación del temporizador (con la mala practica de Wicho de ponerlo en -1)
temporizador = Timer(-1)


# Callback: Se ejecuta cuando el tiempo aleatorio termina (¡momento de presionar!)
def encender_senal(t):
    global estado_actual, tiempo_inicio_ms
    led_senal.on()
    led_espera.off()
    tiempo_inicio_ms = ticks_ms()  # Guarda el cronómetro exacto en que encendió la luz
    estado_actual = ESTADO_LISTO


# Prepara una nueva ronda y reinicia las banderas lógicas
def iniciar_ronda():
    global estado_actual, resultado_listo, salida_falsa, numero_ronda
    numero_ronda += 1
    led_senal.off()
    led_espera.on()

    resultado_listo = False
    salida_falsa = False

    demora_ms = randint(ESPERA_MIN_MS, ESPERA_MAX_MS)  # Entre 1 y 10 segundos
    print(20 * "=")
    print(f"\nRonda {numero_ronda} - intento {len(tiempos) + 1} de {INTENTOS_SERIE}")
    print("Espera la luz de reacción. No presiones antes.")

    # Inicia la cuenta regresiva oculta para esta ronda
    temporizador.init(mode=Timer.ONE_SHOT, period=demora_ms, callback=encender_senal)

    # El estado se abre AL FINAL, cuando el temporizador ya está armado: si se
    # abriera antes, un click durante los print() cancelaría una cuenta que
    # todavía no existe y la nueva quedaría corriendo fuera de la ronda.
    estado_actual = ESTADO_ESPERANDO


# Interrupción IRQ: Evalúa cuándo presionaste el botón respecto al estado del juego
def detectar_pulsacion(pin):
    global estado_actual, tiempo_reaccion_ms, resultado_listo, salida_falsa, ultimo_click_ms

    ahora = ticks_ms()

    # Debounce (antirrebote de 80ms)
    if ticks_diff(ahora, ultimo_click_ms) < DEBOUNCE_MS:
        return
    ultimo_click_ms = ahora

    # ÉXITO: Presionaste después de que la luz encendió
    if estado_actual == ESTADO_LISTO:
        tiempo_reaccion_ms = ticks_diff(ahora, tiempo_inicio_ms)
        led_senal.off()
        resultado_listo = True
        estado_actual = ESTADO_TERMINADO

    # FALLO: Presionaste antes de que encendiera la luz
    elif estado_actual == ESTADO_ESPERANDO:
        temporizador.deinit()  # Cancela la señal que estaba programada para encender
        salida_falsa = True
        resultado_listo = True
        estado_actual = ESTADO_TERMINADO


# Nivel 3: imprime la tabla de la serie con promedio, mejor y peor tiempo
def imprimir_resumen():
    mejor = min(tiempos)
    peor = max(tiempos)
    promedio = sum(tiempos) // len(tiempos)

    print()
    print(34 * "=")
    print("RESUMEN DE LA SERIE")
    print(34 * "=")
    print("| Intento | Tiempo (ms) | Observacion |")
    print("|---------|-------------|-------------|")

    for i, t in enumerate(tiempos):
        if t == mejor:
            nota = "mejor"
        elif t == peor:
            nota = "peor"
        else:
            nota = ""
        print(f"| {i + 1:^7} | {t:^11} | {nota:^11} |")

    print(34 * "=")
    print(f"Mejor tiempo   : {mejor} ms")
    print(f"Peor tiempo    : {peor} ms")
    print(f"Promedio       : {promedio} ms")
    print(f"Salidas falsas : {salidas_falsas}")
    print(f"Rondas jugadas : {numero_ronda} (5 validas + {salidas_falsas} anuladas)")
    print(34 * "=")


# Bloquea hasta que el botón esté libre: una presión sostenida no encadena rondas
def esperar_boton_libre():
    while boton_jugador.value() == 0:
        sleep_ms(10)


# Configuración del botón para disparar la interrupción al ser presionado
boton_jugador.irq(trigger=Pin.IRQ_FALLING, handler=detectar_pulsacion)

print("JUEGO DE LOS REFLEJOS")
print(f"Serie de {INTENTOS_SERIE} intentos validos. Las salidas falsas repiten la ronda.")
iniciar_ronda()

# Bucle principal: Solo gestiona la consola y reinicia el juego basándose en los resultados
while True:
    if resultado_listo:
        if salida_falsa:
            salidas_falsas += 1
            print("SALIDA EN FALSO: Presionaste antes de la señal. La ronda no cuenta.")
        else:
            tiempos.append(tiempo_reaccion_ms)
            print(f"Tiempo de reacción: {tiempo_reaccion_ms} ms")

        sleep_ms(PAUSA_RESULTADO_MS)  # Pausa de legibilidad para ver el resultado

        # Seguro: Obliga al usuario a soltar el botón antes de iniciar la nueva ronda
        esperar_boton_libre()

        # Nivel 3: al completar la serie se cierra con la tabla y se arranca otra
        if len(tiempos) >= INTENTOS_SERIE:
            imprimir_resumen()
            print("\nPresiona el boton para jugar otra serie.")

            # Espera un click nuevo estando en ESTADO_TERMINADO (la ISR los ignora)
            while boton_jugador.value() == 1:
                sleep_ms(10)
            esperar_boton_libre()

            tiempos = []
            salidas_falsas = 0
            numero_ronda = 0

        iniciar_ronda()

    sleep_ms(20)  # Pausa de estabilización del bucle infinito
