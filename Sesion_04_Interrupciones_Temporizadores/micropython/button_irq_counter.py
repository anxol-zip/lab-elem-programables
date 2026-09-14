# =========================================================================
#  DO 01 - Botón con IRQ y contador
#  Sesion 04: Interrupciones y temporizadores
#  Angel Rugerio Jimenez #201720
# =========================================================================

from machine import Pin 
from time import ticks_ms, ticks_diff, sleep_ms

sleep_ms(10) # Estabilización inicial de la placa

# Configuración del pin de entrada con resistencia pull-up interna
boton_entrada = Pin(16, Pin.IN, Pin.PULL_UP)
contador_clicks = 0
ultimo_tiempo_ms = 0

# Función de interrupción (IRQ) que se ejecuta al instante de presionar el botón
def detectar_click(pin):
    global contador_clicks, ultimo_tiempo_ms
    ahora = ticks_ms()
    
    # Debounce (antirrebote): Ignora pulsaciones si pasaron menos de 80ms desde la última
    if ticks_diff(ahora, ultimo_tiempo_ms) > 80:
        contador_clicks += 1
        ultimo_tiempo_ms = ahora

# La interrupción salta en el "flanco de bajada" (IRQ_FALLING), cuando el voltaje cae a 0 al presionar
boton_entrada.irq(trigger = Pin.IRQ_FALLING, handler = detectar_click)

# El bucle principal está liberado y solo se dedica a imprimir el estado
while True:
    print("Clicks detectados:", contador_clicks)
    sleep_ms(500)