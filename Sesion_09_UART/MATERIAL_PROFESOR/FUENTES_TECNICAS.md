# Fuentes técnicas oficiales

- MicroPython RP2 quick reference: https://docs.micropython.org/en/latest/rp2/quickref.html
- MicroPython machine.UART: https://docs.micropython.org/en/latest/library/machine.UART.html
- Wokwi Raspberry Pi Pico: https://docs.wokwi.com/parts/wokwi-pi-pico
- Wokwi MicroPython: https://docs.wokwi.com/guides/micropython

## Notas usadas en la práctica
- La familia RP2xxx dispone de UART hardware y UART0 puede usarse en GP0/GP1.
- El REPL de MicroPython en Pico se accede normalmente por USB; esto es independiente del UART de GP0/GP1.
- `UART.write()`, `UART.readline()` y `UART.any()` pertenecen a la API `machine.UART`.
- Wokwi documenta conexión del Serial Monitor a UART de la Pico, pero la ruta oficial de esta sesión será Thonny + hardware físico para evitar depender del monitor virtual.
