# Evidencia — Sesión 03

Capturas y fotos que respaldan las tablas de pruebas del README de la sesión.
Están separadas igual que los entornos: lo que se validó **simulando** y lo que se validó
**en la placa**.

## Simulación — wokwi.com (RP2040)

| Archivo | Qué debe mostrar | Estado |
|---|---|---|
| `wokwi_button.png` | Monitor serial de `01_button_read.py` con la transición `1 → 0` al presionar | ⬜ |
| `wokwi_debounce.png` | Monitor serial de `02_button_debounce.py`: un click largo genera **un** solo evento | ⬜ |
| `wokwi_semaforo.png` | `03_semaforo_peatonal.py` en estado S2 (auto rojo + peatón verde) | ⬜ |
| `wokwi_cpp.png` | `traffic_light.c` corriendo el mismo circuito en el IDE web | ⬜ |

Los links permanentes de cada simulación van en la tabla final de
[`../wokwi/README.md`](../wokwi/README.md).

## Hardware — Pico 2 W (RP2350)

| Archivo | Qué debe mostrar | Estado |
|---|---|---|
| `hardware_circuito.jpg` | El circuito armado en protoboard, con los 5 LEDs y el botón visibles | ⬜ |
| `hardware_s0.jpg` | S0 REPOSO — auto verde + peatón rojo | ⬜ |
| `hardware_s1.jpg` | S1 TRANSICIÓN — auto amarillo + peatón rojo | ⬜ |
| `hardware_s2.jpg` | S2 CRUCE — auto rojo + peatón verde (la invariante en acción) | ⬜ |
| `hardware_semaforo.mp4` | Video: una presión → secuencia completa → vuelta a S0 | ⬜ |
| `hardware_serial_micropython.png` | `mpremote` corriendo `01_button_read.py` sobre la placa | ⬜ |
| `hardware_serial_cpp.png` | Monitor serial de `traffic_light.c` flasheado en la placa | ⬜ |

> El video vale más que las fotos de estados sueltas: demuestra la **secuencia**, que es lo
> que se está evaluando. Las fotos por estado son el respaldo si el video no se puede subir.
