/* =========================================================================
   Prueba de transferencia - Lectura de boton en C/C++ (Pico SDK)
   Sesion 03: GPIO, pull-up/pull-down y debounce
   Angel Rugerio Jimenez #201720

   Mismo hardware que 01_button_read.py, distinta sintaxis:

     MicroPython                          C / Pico SDK
     Pin(16, Pin.IN, Pin.PULL_UP)   ==>   gpio_set_dir(16, GPIO_IN);
                                          gpio_pull_up(16);
     button.value()                 ==>   gpio_get(16)

   Circuito:  GP16 --- BOTON --- GND      (pull-up interno, presionado = 0)
   ========================================================================= */

#include <stdio.h>
#include "pico/stdlib.h"

#define BUTTON 16

int main(void) {
    stdio_init_all();
    sleep_ms(2000);   // margen para que el monitor serial se conecte

    gpio_init(BUTTON);
    gpio_set_dir(BUTTON, GPIO_IN);
    gpio_pull_up(BUTTON);   // equivalente a Pin.PULL_UP

    printf("Lectura de boton en GP%d con pull-up interno\n", BUTTON);
    printf("Esperado -> boton libre = 1 | boton presionado = 0\n");

    while (true) {
        int value = gpio_get(BUTTON);
        printf("GP%d = %d  (%s)\n", BUTTON, value, value == 0 ? "PRESIONADO" : "libre");
        sleep_ms(200);
    }
}
