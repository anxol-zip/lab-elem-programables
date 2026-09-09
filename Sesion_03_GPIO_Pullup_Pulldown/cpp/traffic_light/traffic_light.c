/* =========================================================================
 *  Reto 03 - Semaforo peatonal interactivo
 *  Sesion 03: GPIO, pull-up/pull-down y debounce
 *  Angel Rugerio Jimenez #201720
 * =========================================================================
 *
 *  Pinout
 *  -------------------------------------------------
 *   Auto rojo      GP15      Peaton rojo    GP12
 *   Auto amarillo  GP14      Peaton verde   GP11
 *   Auto verde     GP13      Boton          GP16
 *
 *  Maquina de estados
 *  -------------------------------------------------
 *   S0 REPOSO      autos VERDE      peaton ROJO
 *   S1 TRANSICION  autos AMARILLO   peaton ROJO
 *   S2 CRUCE       autos ROJO       peaton VERDE
 *   S3 FIN         autos ROJO       peaton VERDE parpadeando
 *
 *  Seguridad
 *   Auto verde y peaton verde NUNCA deben estar encendidos a la vez.
 *   NOTA: set_lights() en esta version NO implementa un chequeo en
 *   tiempo de ejecucion (ver nota tecnica al final de la respuesta). La
 *   invariante se sostiene solo porque las funciones de estado
 *   (cars_go, cars_prepare_to_stop, pedestrians_go, pedestrians_hurry)
 *   nunca la violan por construccion.
 * ========================================================================= */

#include <stdbool.h>
#include <stdio.h>
#include "pico/stdlib.h"

/* --- Pines --------------------------------------------------------------*/
#define CAR_RED_PIN     15
#define CAR_YELLOW_PIN  14
#define CAR_GREEN_PIN   13
#define PED_RED_PIN     12
#define PED_GREEN_PIN   11
#define BUTTON_PIN      16

/* --- Tiempos (ajustables sin tocar la logica) ----------------------------*/
#define TRANSITION_MS   1500u   // S1 - amarillo, los autos frenan
#define CROSSING_MS     4000u   // S2 - el peaton cruza
#define BLINK_TIMES     4u      // S3 - parpadeos de aviso
#define BLINK_MS        300u
#define RECOVERY_MS     500u    // colchon antes de devolver el verde a los autos
#define DEBOUNCE_MS     30u
#define POLL_MS         10u

/* --- Prototipos -----------------------------------------------------------*/
static void gpio_setup(void);
static void set_lights(bool car_r, bool car_y, bool car_g, bool ped_r, bool ped_g);
static void cars_go(void);
static void cars_prepare_to_stop(void);
static void pedestrians_go(void);
static void pedestrians_hurry(void);
static void crossing_sequence(void);

/* --- Configuracion de GPIO -------------------------------------------------*/
static void gpio_setup(void) {
    const uint out_pins[5] = {CAR_RED_PIN, CAR_YELLOW_PIN, CAR_GREEN_PIN,
                               PED_RED_PIN, PED_GREEN_PIN};

    for (int i = 0; i < 5; i++) {
        gpio_init(out_pins[i]);
        gpio_set_dir(out_pins[i], GPIO_OUT);
    }

    gpio_init(BUTTON_PIN);
    gpio_set_dir(BUTTON_PIN, GPIO_IN);
    gpio_pull_up(BUTTON_PIN);
}

/* --- Funciones ------------------------------------------------------------*/

static void set_lights(bool car_r, bool car_y, bool car_g, bool ped_r, bool ped_g) {
    if (car_g && ped_g) {
        printf("!! set_lights() rechazado: auto VERDE + peaton VERDE simultaneos\n");
        return;
    }
    gpio_put(CAR_RED_PIN, car_r);
    gpio_put(CAR_YELLOW_PIN, car_y);
    gpio_put(CAR_GREEN_PIN, car_g);
    gpio_put(PED_RED_PIN, ped_r);
    gpio_put(PED_GREEN_PIN, ped_g);
}

/* S0 REPOSO - los autos pasan, el peaton espera. */
static void cars_go(void) {
    set_lights(0, 0, 1, 1, 0);
    printf("S0 REPOSO      | autos VERDE    | peaton ROJO\n");
}

/* S1 TRANSICION - los autos frenan. */
static void cars_prepare_to_stop(void) {
    set_lights(0, 1, 0, 1, 0);
    printf("S1 TRANSICION  | autos AMARILLO | peaton ROJO\n");
}

/* S2 CRUCE - el peaton pasa, los autos detenidos. */
static void pedestrians_go(void) {
    set_lights(1, 0, 0, 0, 1);
    printf("S2 CRUCE       | autos ROJO     | peaton VERDE\n");
}

/* S3 FIN - aviso de fin de cruce; los autos siguen en rojo. */
static void pedestrians_hurry(void) {
    printf("S3 FIN         | autos ROJO     | peaton VERDE parpadeando\n");
    for (unsigned int i = 0; i < BLINK_TIMES; i++) {
        gpio_put(PED_GREEN_PIN, 0);
        sleep_ms(BLINK_MS);
        gpio_put(PED_GREEN_PIN, 1);
        sleep_ms(BLINK_MS);
    }
}

/* Secuencia completa disparada por una peticion del peaton. */
static void crossing_sequence(void) {
    printf(">> PETICION DE CRUCE ACEPTADA\n");

    cars_prepare_to_stop();
    sleep_ms(TRANSITION_MS);

    pedestrians_go();
    sleep_ms(CROSSING_MS);

    pedestrians_hurry();

    set_lights(1, 0, 0, 1, 0);
    sleep_ms(RECOVERY_MS);

    cars_go();
    printf(">> SECUENCIA COMPLETA - sistema en reposo\n\n");
}

/* --- Main -------------------------------------------------------------- */
int main(void) {
    stdio_init_all();
    gpio_setup();

    printf("====================================================\n");
    printf("Reto 03 - Semaforo peatonal interactivo\n");
    printf("Boton en GP%d con pull-up interno (presionado = 0)\n", BUTTON_PIN);
    printf("====================================================\n");

    cars_go();

    bool last = true;  // boton libre por el pull-up

    while (true) {
        bool now = gpio_get(BUTTON_PIN);

        if (last && !now) {
            sleep_ms(DEBOUNCE_MS);

            if (gpio_get(BUTTON_PIN) == 0) {
                crossing_sequence();

                while (gpio_get(BUTTON_PIN) == 0) {
                    sleep_ms(POLL_MS);
                }
            }
        }

        last = now;
        sleep_ms(POLL_MS);
    }

    return 0;
}