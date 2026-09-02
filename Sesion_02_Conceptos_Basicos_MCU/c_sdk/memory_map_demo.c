#include <stdio.h>
#include <stdlib.h>
#include "pico/stdlib.h"

const uint32_t flash_const = 0x12345678;
uint32_t global_counter = 0;

int main() {
    stdio_init_all();
    sleep_ms(3000); // Da tiempo a abrir el monitor serial antes de imprimir

    printf("Prueba en Pi Pico W con C_SDK");
    printf(" ");

    uint32_t stack_value = 0xABCDEF01;
    uint8_t *heap_buffer = (uint8_t *) malloc(1024);

    printf("Flash const: %p\n", (void *) &flash_const);
    printf("Global var : %p\n", (void *) &global_counter);
    printf("Stack var  : %p\n", (void *) &stack_value);
    printf("Heap ptr   : %p\n", (void *) heap_buffer);

    free(heap_buffer);
    while (true) sleep_ms(1000);
}