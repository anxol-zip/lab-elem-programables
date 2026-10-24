# SESIÓN 09 — CORRECCIÓN UART v3

## Qué se corrigió

En la versión anterior se hacía:

```python
if uart.any():
    data = uart.readline()
```

`uart.any()` puede volverse verdadero apenas llega el primer byte.
En un UART configurado de forma no bloqueante, `readline()` puede devolver en ese momento
una línea parcial si todavía no ha llegado el `\n`.

Por eso podían verse casos como:

- `LED1 ON` -> `LED1`
- `STATUS` -> `STATU`

## Solución usada

Ahora la recepción:

1. Vacía el RX anterior.
2. Envía `texto + "\n"`.
3. Lee byte por byte.
4. Acumula los bytes en un `bytearray`.
5. Solo devuelve la trama cuando recibe `\n`.
6. Si no llega una línea completa antes del timeout, devuelve `None`.

## Prueba rápida

Conecta:

`GP0 (TX) -> GP1 (RX)`

Ejecuta `TEST_UART_ROBUSTO.py` y escribe:

- `PING`
- `LED1 ON`
- `STATUS`
- `SET,LED1,1`
- `GET,STATUS`

La columna RX debe coincidir exactamente con TX.
