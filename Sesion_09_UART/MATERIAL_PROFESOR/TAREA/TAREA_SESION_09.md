# Challenge 09 — UART Command Center con Thonny

## Escenario
Thonny funciona como consola del operador por USB. Cada comando que escribas se envía al **UART0 físico** de la Pico, cruza el jumper GP0(TX)→GP1(RX), vuelve a entrar por UART y entonces es interpretado por el programa.

Ruta de datos:
```text
Thonny/USB → input() → UART TX GP0 → jumper → UART RX GP1 → parser → LEDs → respuesta en Thonny
```

## Nivel 1 — obligatorio
Implementar:
- `PING`
- `SET,LED1,1` / `SET,LED1,0`
- `SET,LED2,1` / `SET,LED2,0`
- `GET,STATUS`

Toda instrucción válida debe producir `ACK,...` o `STATUS,...`.

## Nivel 2 — obligatorio
Agregar:
- `SET,ALL,1`
- `SET,ALL,0`
- validación de número de campos
- validación de dispositivo
- validación de valor `0/1`
- `ERR,...` ante tramas inválidas

## Nivel 3 — bonus
Agregar una trama propia:
- `TOGGLE,LED1`
- `BLINK,LED2,500`
- `HELP`

## Pruebas mínimas
1. `PING`
2. `SET,LED1,1`
3. `SET,LED1,0`
4. `SET,LED2,1`
5. `SET,ALL,1`
6. `GET,STATUS`
7. `SET,LED3,1`
8. `SET,LED1,9`
9. texto libre

## Evidencia
La consola debe mostrar para cada prueba algo similar a:
```text
CMD> SET,LED1,1
USB CMD : SET,LED1,1
UART RX : SET,LED1,1
RESP    : ACK,LED1,1
```

## Entrega GitHub
```text
Sesion_09_UART/
├── README.md
├── main.py
├── tabla_pruebas.csv
└── evidencia/
    ├── thonny.png
    └── loopback_fisico.jpg
```

El README debe explicar UART, TX/RX, baud rate, 8N1, por qué Thonny usa USB/REPL y cómo el loopback permite comprobar UART sin un adaptador externo.
