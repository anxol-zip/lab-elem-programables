# =========================================================================
#  DO 01 - Botón con IRQ y contador
#  Sesion 04: Interrupciones y temporizadores
#  Angel Rugerio Jimenez #201720
#
#  5 clics seguidos deben imprimir 1, 2, 3, 4, 5 sin saltos,
#  y un clic sostenido debe contar como un solo evento (debounce).
# =========================================================================
from machine import Pin
from time import ticks_ms, ticks_diff, sleep_ms

sleep_ms(10) # Estabilización inicial de la placa

# Configuración del pin de entrada con resistencia pull-up interna
boton_entrada = Pin(16, Pin.IN, Pin.PULL_UP)
contador_clicks = 0
ultimo_tiempo_ms = 0

DEBOUNCE_MS = 80 # Ventana antirrebote: 80-120 ms es el rango recomendado

# Función de interrupción (IRQ) que se ejecuta al instante de presionar el botón
def detectar_click(pin):
    global contador_clicks, ultimo_tiempo_ms
    ahora = ticks_ms()

    # Debounce (antirrebote): Ignora pulsaciones si pasaron menos de 80ms desde la última
    if ticks_diff(ahora, ultimo_tiempo_ms) > DEBOUNCE_MS:
        contador_clicks += 1
        ultimo_tiempo_ms = ahora

# La interrupción salta en el "flanco de bajada" (IRQ_FALLING), cuando el voltaje cae a 0 al presionar
boton_entrada.irq(trigger = Pin.IRQ_FALLING, handler = detectar_click)

print("Contador de clicks con IRQ.")

# El bucle principal está liberado: solo imprime cuando el contador cambió,
# así la consola muestra la secuencia limpia 1, 2, 3, 4, 5
ultimo_impreso = 0

while True:
    if contador_clicks != ultimo_impreso:
        ultimo_impreso = contador_clicks
        print("Clicks detectados:", ultimo_impreso)

    sleep_ms(20)
