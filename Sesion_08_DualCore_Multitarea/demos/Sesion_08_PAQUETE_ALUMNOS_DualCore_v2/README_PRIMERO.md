# Sesión 08 — Procesamiento Multihilo / Dual-Core

## Idea de la sesión

Esta sesión tiene dos caminos:

1. **Wokwi**: simula multitarea cooperativa en un solo núcleo usando `ticks_ms()` y tareas periódicas.
2. **Pico física**: si tienes la placa conectada por USB, prueba `_thread` para separar la adquisición rápida en el segundo núcleo real.

> Wokwi permite validar la lógica y los periodos de tareas, pero la prueba de dual-core real se realiza en la Raspberry Pi Pico física.

## Orden de trabajo

1. Abre `WOKWI_TEMPLATE/` en Wokwi.
2. Copia `CODIGOS_SHOW/00_bloqueo.py` en `main.py`: observa el problema de bloquear 1 segundo.
3. Copia `CODIGOS_SHOW/01_wokwi_multitarea.py`: compara la respuesta sin bloqueos largos.
4. Lleva el sensor a **ALARM (>75%)**: el LED rojo parpadea.
5. Presiona el botón: el sistema muestra **ACK=True** y el rojo queda fijo.
6. Realiza el DO con `CODIGOS_SHOW/03_DO08_starter.py`.
7. Si tienes Pico física, ejecuta `CODIGOS_SHOW/02_dualcore_fisico_thread.py` en Thonny o VS Code con MicroPython.

## Circuito Wokwi

- Potenciómetro → GP26 / ADC0
- LED verde → GP13 / NORMAL
- LED amarillo → GP14 / WARNING
- LED rojo → GP15 / ALARM
- LED azul → GP12 / heartbeat
- Botón → GP16 / acknowledge de alarma

### Comportamiento del botón

El botón usa `PULL_UP`:

- libre → `1`
- presionado → `0`

El ACK solo tiene efecto cuando el sistema está en **ALARM**.

- ALARM sin ACK → rojo parpadea
- ALARM con ACK → rojo fijo
- si la señal sale de ALARM, el ACK se limpia automáticamente

## Idea clave

Reconocer una alarma **no elimina la condición de alarma**. Solo confirma que el operador ya la vio.

## Entrega

Sube todo a GitHub en una carpeta:

```text
Sesion_08_DualCore_Multitarea/
├── README.md
├── main_wokwi.py
├── main_dualcore_physical.py   # si se realizó prueba física
├── wokwi/
│   ├── diagram.json
│   └── enlace.md
└── evidence/
    ├── serial_wokwi.png
    ├── serial_pico.png         # si aplica
    └── circuito.png
```
