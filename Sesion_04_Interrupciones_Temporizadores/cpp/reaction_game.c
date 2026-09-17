/* =========================================================================
 *  RE 04 - Juego de tiempo de reaccion (version C / Pico SDK)
 *  Sesion 04: Interrupciones y temporizadores
 *  Angel Rugerio Jimenez #201720
 * ========================================================================= */

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include "pico/stdlib.h"

/* --- Pines --------------------------------------------------------------*/
#define LED_SIGNAL_PIN   15
#define LED_WAIT_PIN     14
#define BUTTON_PIN       16

/* --- Parametros ajustables ----------------------------------------------*/
#define ATTEMPTS_PER_RUN   5u      // Nivel 3: la serie se cierra a los 5 validos
#define DEBOUNCE_MS        80u     // Nivel 2: ventana antirrebote en la ISR
#define WAIT_MIN_MS        1000u   // Rango del retardo aleatorio antes de la senal
#define WAIT_MAX_MS        10000u
#define RESULT_PAUSE_MS    1800u
#define POLL_MS            20u

/* --- Maquina de estados --------------------------------------------------*/
typedef enum {
    STATE_WAITING = 0,   // S0 - aun no se debe presionar
    STATE_READY,         // S1 - la senal esta encendida, se puede presionar
    STATE_DONE           // S2/S3 - ronda cerrada, la ISR ignora el boton
} game_state_t;

/* --- Estado compartido ISR <-> main --------------------------------------
 *  Todo lo que escribe una interrupcion va marcado volatile para que el
 *  compilador no lo cachee en un registro dentro del bucle principal.       */
static volatile game_state_t state = STATE_DONE;
static volatile uint32_t signal_time_ms = 0;   // instante en que encendio la senal
static volatile uint32_t reaction_ms = 0;      // resultado de la ronda
static volatile bool result_ready = false;     // bandera ISR -> main
static volatile bool false_start = false;      // se presiono antes de la senal
static volatile uint32_t last_click_ms = 0;    // referencia del debounce

static volatile alarm_id_t signal_alarm = 0;   // alarma armada para la ronda

/* --- Registro de la serie (Nivel 3) --------------------------------------*/
static uint32_t times[ATTEMPTS_PER_RUN];
static uint     times_count = 0;
static uint     false_starts = 0;
static uint     round_number = 0;

/* --- Prototipos ----------------------------------------------------------*/
static void     gpio_setup(void);
static uint32_t now_ms(void);
static int64_t  signal_alarm_cb(alarm_id_t id, void *user_data);
static void     button_isr(uint gpio, uint32_t events);
static void     start_round(void);
static void     print_summary(void);
static void     wait_button_released(void);
static void     wait_button_pressed(void);

/* --- Utilidad de tiempo --------------------------------------------------*/
static uint32_t now_ms(void) {
    return to_ms_since_boot(get_absolute_time());
}

/* --- Configuracion de GPIO -----------------------------------------------*/
static void gpio_setup(void) {
    gpio_init(LED_SIGNAL_PIN);
    gpio_set_dir(LED_SIGNAL_PIN, GPIO_OUT);
    gpio_put(LED_SIGNAL_PIN, 0);

    gpio_init(LED_WAIT_PIN);
    gpio_set_dir(LED_WAIT_PIN, GPIO_OUT);
    gpio_put(LED_WAIT_PIN, 0);

    /* Boton a GND con pull-up interno: libre = 1, presionado = 0 */
    gpio_init(BUTTON_PIN);
    gpio_set_dir(BUTTON_PIN, GPIO_IN);
    gpio_pull_up(BUTTON_PIN);
}

/* --- Callback del temporizador (equivalente a Timer.ONE_SHOT) ------------
 *  Enciende la senal y guarda el instante exacto en que lo hizo.
 *  Corre en contexto de interrupcion: nada de printf aqui.                  */
static int64_t signal_alarm_cb(alarm_id_t id, void *user_data) {
    (void)id;
    (void)user_data;

    gpio_put(LED_SIGNAL_PIN, 1);
    gpio_put(LED_WAIT_PIN, 0);
    signal_time_ms = now_ms();
    state = STATE_READY;

    return 0;   // 0 = no reagendar, es un disparo unico
}

/* --- ISR del boton (flanco de bajada) ------------------------------------
 *  Solo mide y levanta banderas. La decision de que imprimir es del main.   */
static void button_isr(uint gpio, uint32_t events) {
    (void)gpio;
    (void)events;

    uint32_t now = now_ms();

    /* Debounce: pulsos mas rapidos que DEBOUNCE_MS son rebote mecanico */
    if (now - last_click_ms < DEBOUNCE_MS) {
        return;
    }
    last_click_ms = now;

    if (state == STATE_READY) {
        /* EXITO: se presiono despues de que encendio la senal */
        reaction_ms = now - signal_time_ms;
        gpio_put(LED_SIGNAL_PIN, 0);
        result_ready = true;
        state = STATE_DONE;
    } else if (state == STATE_WAITING) {
        /* FALLO: salida en falso, se cancela la senal que estaba agendada */
        cancel_alarm(signal_alarm);
        false_start = true;
        result_ready = true;
        state = STATE_DONE;
    }
    /* En STATE_DONE el boton se ignora: sostenerlo no encadena rondas */
}

/* --- Prepara una ronda nueva ---------------------------------------------*/
static void start_round(void) {
    round_number++;

    gpio_put(LED_SIGNAL_PIN, 0);
    gpio_put(LED_WAIT_PIN, 1);

    result_ready = false;
    false_start = false;

    /* Retardo aleatorio: el jugador no puede anticiparse */
    uint32_t delay_ms = WAIT_MIN_MS + (uint32_t)(rand() % (WAIT_MAX_MS - WAIT_MIN_MS + 1));

    printf("====================\n");
    printf("\nRonda %u - intento %u de %u\n",
           round_number, times_count + 1, ATTEMPTS_PER_RUN);
    printf("Espera la luz de reaccion. No presiones antes.\n");

    signal_alarm = add_alarm_in_ms(delay_ms, signal_alarm_cb, NULL, false);

    /* El estado se abre AL FINAL, cuando la alarma ya existe: si se abriera
     * antes, un click durante los printf() haria que la ISR cancelara el id
     * de la ronda anterior y la alarma nueva quedaria corriendo fuera de la
     * ronda, encendiendo la senal en un estado que ya se cerro.            */
    state = STATE_WAITING;
}

/* --- Tabla de la serie, promedio, mejor y peor (Nivel 3) -----------------*/
static void print_summary(void) {
    uint32_t best = times[0];
    uint32_t worst = times[0];
    uint32_t total = 0;

    for (uint i = 0; i < times_count; i++) {
        if (times[i] < best)  best = times[i];
        if (times[i] > worst) worst = times[i];
        total += times[i];
    }

    uint32_t average = total / times_count;

    printf("\n==================================\n");
    printf("RESUMEN DE LA SERIE\n");
    printf("==================================\n");
    printf("| Intento | Tiempo (ms) | Observacion |\n");
    printf("|---------|-------------|-------------|\n");

    for (uint i = 0; i < times_count; i++) {
        const char *note = "";
        if (times[i] == best)       note = "mejor";
        else if (times[i] == worst) note = "peor";

        printf("| %7u | %11u | %-11s |\n", i + 1, times[i], note);
    }

    printf("==================================\n");
    printf("Mejor tiempo   : %u ms\n", best);
    printf("Peor tiempo    : %u ms\n", worst);
    printf("Promedio       : %u ms\n", average);
    printf("Salidas falsas : %u\n", false_starts);
    printf("Rondas jugadas : %u (%u validas + %u anuladas)\n",
           round_number, times_count, false_starts);
    printf("==================================\n");
}

/* --- Bloqueos por sondeo (fuera de la ISR) -------------------------------*/
static void wait_button_released(void) {
    while (gpio_get(BUTTON_PIN) == 0) {   // pull-up: 0 = presionado
        sleep_ms(10);
    }
}

static void wait_button_pressed(void) {
    while (gpio_get(BUTTON_PIN) == 1) {
        sleep_ms(10);
    }
}

/* --- Programa principal --------------------------------------------------*/
int main(void) {
    stdio_init_all();
    gpio_setup();

    /* Semilla del generador: el reloj del micro al arrancar */
    srand(time_us_32());

    /* La ISR se registra una sola vez para el flanco de bajada del boton */
    gpio_set_irq_enabled_with_callback(BUTTON_PIN, GPIO_IRQ_EDGE_FALL, true, &button_isr);

    sleep_ms(2000);   // margen para abrir el monitor serial antes de la ronda 1

    printf("JUEGO DE LOS REFLEJOS (C / Pico SDK)\n");
    printf("Serie de %u intentos validos. Las salidas falsas repiten la ronda.\n",
           ATTEMPTS_PER_RUN);

    start_round();

    /* El main loop nunca mide: solo reacciona a las banderas de la ISR */
    while (true) {
        if (result_ready) {
            if (false_start) {
                false_starts++;
                printf("SALIDA EN FALSO: Presionaste antes de la senal. La ronda no cuenta.\n");
            } else {
                times[times_count++] = reaction_ms;
                printf("Tiempo de reaccion: %u ms\n", reaction_ms);
            }

            sleep_ms(RESULT_PAUSE_MS);   // pausa de legibilidad

            /* Seguro: un boton sostenido no arranca la ronda siguiente */
            wait_button_released();

            if (times_count >= ATTEMPTS_PER_RUN) {
                print_summary();
                printf("\nPresiona el boton para jugar otra serie.\n");

                wait_button_pressed();    // la ISR ignora este click (STATE_DONE)
                wait_button_released();

                times_count = 0;
                false_starts = 0;
                round_number = 0;
            }

            start_round();
        }

        sleep_ms(POLL_MS);
    }
}
