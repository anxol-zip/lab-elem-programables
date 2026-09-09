/* =========================================================================
   Prueba de transferencia - Semaforo peatonal completo en C/C++ (Pico SDK)
   Sesion 03: GPIO, pull-up/pull-down y debounce
   Angel Rugerio Jimenez #201720

   Es el mismo programa que 03_semaforo_peatonal.py: mismo circuito, mismos
   pines, misma maquina de estados, misma invariante de seguridad. Solo
   cambia la sintaxis.

     MicroPython                          C / Pico SDK
     Pin(16, Pin.IN, Pin.PULL_UP)   ==>   gpio_set_dir(16, GPIO_IN);
                                          gpio_pull_up(16);
     button.value()                 ==>   gpio_get(16)
     Pin(15, Pin.OUT)               ==>   gpio_set_dir(15, GPIO_OUT)
     led.value(1)                   ==>   gpio_put(15, 1)
     sleep_ms(1000)                 ==>   sleep_ms(1000)

   Etapa A - Boton:  GP16 --- BOTON --- GND        (pull-up interno)
   Etapa B - LEDs :  GPIO --- 330 ohm --- LED --- GND

   Maquina de estados
   -------------------------------------------------
    S0 REPOSO      autos VERDE      peaton ROJO
    S1 TRANSICION  autos AMARILLO   peaton ROJO
    S2 CRUCE       autos ROJO       peaton VERDE
    S3 FIN         autos ROJO       peaton VERDE parpadeando

   INVARIANTE DE SEGURIDAD
    Auto verde y peaton verde NUNCA pueden estar encendidos a la vez.
    set_lights() lo verifica en cada cambio y se niega a aplicar una
    combinacion peligrosa.
   ========================================================================= */

#include <stdio.h>
#include "pico/stdlib.h"

/* --- Pines ----------------------------------------------------------- */
#define CAR_RED     15
#define CAR_YELLOW  14
#define CAR_GREEN   13
#define PED_RED     12
#define PED_GREEN   11
#define BUTTON      16

/* --- Tiempos (Nivel 3: ajustables sin tocar la logica) --------------- */
#define TRANSITION_MS 1500   /* S1 - amarillo, los autos frenan          */
#define CROSSING_MS   4000   /* S2 - el peaton cruza                     */
#define BLINK_TIMES   4      /* S3 - parpadeos de "se acaba el tiempo"   */
#define BLINK_MS      300
#define RECOVERY_MS   500    /* colchon antes de devolver verde a autos  */
#define DEBOUNCE_MS   30
#define POLL_MS       10

/* --- Configuracion de GPIO ------------------------------------------- */
static void gpio_init_out(uint pin) {
    gpio_init(pin);
    gpio_set_dir(pin, GPIO_OUT);
    gpio_put(pin, 0);
}

static void setup_gpio(void) {
    gpio_init_out(CAR_RED);
    gpio_init_out(CAR_YELLOW);
    gpio_init_out(CAR_GREEN);
    gpio_init_out(PED_RED);
    gpio_init_out(PED_GREEN);

    gpio_init(BUTTON);
    gpio_set_dir(BUTTON, GPIO_IN);
    gpio_pull_up(BUTTON);   /* equivalente a Pin.PULL_UP */
}

/* --- Capa de abstraccion --------------------------------------------- */
/* No pensamos en "0,0,1,1,0": pensamos en acciones del sistema.         */

static void set_lights(bool car_r, bool car_y, bool car_g,
                       bool ped_r, bool ped_g) {
    if (car_g && ped_g) {
        /* Estado peligroso: se bloquea y se cae a la combinacion segura */
        printf("!! ESTADO PELIGROSO BLOQUEADO: auto verde + peaton verde\n");
        car_r = true;  car_y = false; car_g = false;
        ped_r = true;  ped_g = false;
    }

    gpio_put(CAR_RED,    car_r);
    gpio_put(CAR_YELLOW, car_y);
    gpio_put(CAR_GREEN,  car_g);
    gpio_put(PED_RED,    ped_r);
    gpio_put(PED_GREEN,  ped_g);
}

static void cars_go(void) {                 /* S0 REPOSO */
    set_lights(false, false, true, true, false);
    printf("S0 REPOSO      | autos VERDE    | peaton ROJO\n");
}

static void cars_prepare_to_stop(void) {    /* S1 TRANSICION */
    set_lights(false, true, false, true, false);
    printf("S1 TRANSICION  | autos AMARILLO | peaton ROJO\n");
}

static void pedestrians_go(void) {          /* S2 CRUCE */
    set_lights(true, false, false, false, true);
    printf("S2 CRUCE       | autos ROJO     | peaton VERDE\n");
}

static void pedestrians_hurry(void) {       /* S3 FIN */
    printf("S3 FIN         | autos ROJO     | peaton VERDE parpadeando\n");
    for (int i = 0; i < BLINK_TIMES; i++) {
        gpio_put(PED_GREEN, 0);
        sleep_ms(BLINK_MS);
        gpio_put(PED_GREEN, 1);
        sleep_ms(BLINK_MS);
    }
}

static void crossing_sequence(void) {
    printf(">> PETICION DE CRUCE ACEPTADA\n");

    cars_prepare_to_stop();
    sleep_ms(TRANSITION_MS);

    pedestrians_go();
    sleep_ms(CROSSING_MS);

    pedestrians_hurry();

    /* Antes de devolver el verde a los autos, el peaton vuelve a rojo.
       Este paso intermedio es lo que garantiza que los dos verdes nunca
       se traslapen ni siquiera por un instante. */
    set_lights(true, false, false, true, false);
    sleep_ms(RECOVERY_MS);

    cars_go();
    printf(">> SECUENCIA COMPLETA - sistema en reposo\n\n");
}

/* --- Programa principal ---------------------------------------------- */
int main(void) {
    stdio_init_all();
    sleep_ms(2000);   /* margen para que el monitor serial se conecte */

    setup_gpio();

    printf("====================================================\n");
    printf("CHALLENGE - Semaforo peatonal interactivo (C/C++)\n");
    printf("Boton en GP%d con pull-up interno (presionado = 0)\n", BUTTON);
    printf("====================================================\n");

    cars_go();

    int last = 1;   /* boton libre por el pull-up */

    while (true) {
        int now = gpio_get(BUTTON);

        /* Flanco de bajada + debounce: una peticion real del peaton */
        if (last == 1 && now == 0) {
            sleep_ms(DEBOUNCE_MS);

            if (gpio_get(BUTTON) == 0) {
                crossing_sequence();

                /* Wait for release: mantener el boton presionado NO
                   encadena una segunda secuencia. */
                while (gpio_get(BUTTON) == 0) {
                    sleep_ms(POLL_MS);
                }
            }
        }

        last = now;
        sleep_ms(POLL_MS);
    }
}
