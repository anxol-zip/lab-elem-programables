# Sesión 02 — Conceptos básicos de microcontroladores

Evidencia del RETO 02: relación entre **código → memoria → registros → GPIO** en la
Raspberry Pi Pico 2 W (RP2350), comparando MicroPython y C/C++.

## Contenido de esta carpeta

| Carpeta | Contenido |
|---|---|
| `infographic/` | Infografía técnica (PDF) que responde las 7 preguntas del Challenge 02 |
| `micropython/` | `memory_probe.py` — DO 01: medición de memoria libre con `gc` |
| `c_sdk/` | `memory_map_demo.c` + `CMakeLists.txt` — DO 02: direcciones de memoria en C |
| `wokwi/` | Enlaces a las simulaciones usadas para validar la lógica |
| `evidence/` | Capturas del monitor serial en Wokwi (evidencia física pendiente) |

## DO 01 — Medición de memoria en MicroPython

Script: [`micropython/memory_probe.py`](./micropython/memory_probe.py)

Reserva un `bytearray` de 10 000 bytes y luego de 20 000, comparando `gc.mem_free()` antes y
después de cada reserva y tras liberar con `del` + `gc.collect()`.

| Momento                      | Memoria libre reportada (B) |
| ---------------------------- | --------------------------- |
| Inicial                      | *200'672*                   |
| Después de reservar 10 000 B | *190'656*                   |
| Después de reservar 20 000 B | *170'640*                   |
| Después de liberar           | *200'672*                   |

**Análisis:**
- ¿Qué cambia cuando reservamos más memoria? ***La memoria libre que reporta el sistema es aún menor, algo lógico, porque estamos reservando más***
- ¿Qué hace `gc.collect()`? ***Ejecuta el recolector de basura: recorre el heap y libera la memoria de los objetos que ya no tienen ninguna referencia activa (por ejemplo, el `bytearray` después de un `del`), devolviéndola al pool disponible. Sin llamarlo, `del` solo quita la referencia — no garantiza que `mem_free()` refleje de inmediato el espacio recuperado.***
- ¿Por qué esto importa en sistemas embebidos? ***Porque no hay swap ni un sistema operativo que gestione memoria virtual como en una PC: la RAM disponible (520 KB en el RP2350) es fija y compartida entre stack, heap y buffers. Un heap fragmentado o no liberado a tiempo puede agotar la memoria a medio programa (`MemoryError`) justo cuando se está leyendo un sensor o controlando un actuador — en un MCU cada byte cuenta y afecta directamente qué tan predecible es el comportamiento en tiempo real.***

## DO 02 — Mapa de memoria observable en C/C++

Código: [`c_sdk/memory_map_demo.c`](./c_sdk/memory_map_demo.c) · Board target: `pico2_w`

Imprime por serial la dirección de una variable `const` (candidata a Flash), una variable global
(SRAM), una variable local (stack) y un puntero reservado con `malloc` (heap).

| Variable         | Tipo                  | Dirección observada | Región probable |
| ---------------- | --------------------- | ------------------- | --------------- |
| `flash_const`    | `const uint32_t`      | *10004A3C*          | Flash / XIP     |
| `global_counter` | `uint32_t` global     | *20001040*          | SRAM            |
| `stack_value`    | `uint32_t` local      | *20041FF4*          | Stack           |
| `heap_buffer`    | `uint8_t*` (`malloc`) | *20001198*          | Heap            |

## Evidencia Wokwi

Ver [`wokwi/Wokwi.md`](./wokwi/Wokwi.md) para los enlaces a ambas simulaciones y la nota de
alcance (ambas corren sobre RP2040 simulado, no sobre el RP2350 real).

## Evidencia de ejecución (Wokwi)

> [!NOTE] Aún no se cuenta con la Raspberry Pi Pico 2 W física — toda la evidencia de esta
> entrega es de simulación en Wokwi. Validación en hardware físico pendiente.

- Captura de Wokwi + monitor serial con MicroPython: [`evidence/python.png`](./evidence/python.png)
- Captura de Wokwi + monitor serial con C/C++ (Pico SDK): [`evidence/c.png`](./evidence/c.png)

## Referencias

- Presentación de Sesión 02 del Laboratorio de Elementos Programables
