# Sesión 09 — Comunicación UART (ruta de clase: Thonny + Pico física)

## Objetivo
Comprender UART, TX/RX, baud rate y diseño de tramas. Para reducir riesgos en esta sesión, la práctica principal se realizará con **Raspberry Pi Pico física + Thonny + USB**, y un **loopback UART GP0 → GP1** usando un jumper.

## ¿Por qué esta ruta?
`print()` aparece en Thonny por USB/REPL. `uart.write()` sale físicamente por el pin TX del UART y **no aparece automáticamente en la consola de Thonny**. Por eso usamos Thonny como interfaz del operador y un jumper GP0→GP1 para verificar el UART hardware real.

## Conexión mínima
- Pico conectada a la computadora por USB.
- GP0 = UART0 TX.
- GP1 = UART0 RX.
- Colocar un jumper **GP0 → GP1** para el loopback.
- GP13 → LED1 (o LED de su shield).
- GP14 → LED2 (o LED de su shield).

> El jumper une TX con RX de la misma Pico. Así todo dato transmitido por UART0 vuelve a entrar por UART0 y podemos verlo después mediante `print()` en Thonny.

## Orden de la sesión
1. `00_usb_vs_uart.py` — diferencia entre `print()` y `uart.write()`.
2. `01_uart_loopback.py` — comprobación física TX→RX.
3. `02_thonny_bridge_comandos.py` — comandos escritos en Thonny que cruzan el UART loopback.
4. `03_tramas_ack_status_thonny.py` — protocolo estructurado con ACK / ERR / STATUS.
5. `DO09_starter_thonny.py` — reto de los estudiantes.

## Comandos finales
```text
PING
GET,STATUS
SET,LED1,1
SET,LED1,0
SET,LED2,1
SET,LED2,0
SET,ALL,1
SET,ALL,0
```

## Respuestas esperadas
```text
ACK,PONG
ACK,LED1,1
STATUS,LED1,1,LED2,0
ERR,UNKNOWN_FRAME
```

## Evidencia mínima
- Captura de Thonny mostrando `USB CMD`, `UART RX` y la respuesta.
- Fotografía de la Pico con el jumper GP0→GP1.
- Código final.
- Tabla PASS/FAIL con al menos 8 pruebas.
- Explicación breve: USB/REPL ≠ UART, TX/RX, baud rate, 8N1, trama y ACK/ERR.

## Wokwi
Se incluye únicamente como **opcional/backup visual**. No dependemos del Serial Monitor UART de Wokwi para impartir esta sesión. Si el monitor virtual no aparece, continúen con Thonny: no afecta la actividad principal.
