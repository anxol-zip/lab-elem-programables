# Simulación — Sesión 03

Toda la simulación de esta sesión se corre en **wokwi.com** (el IDE web). Esta carpeta
solo contiene el **circuito**; el código vive en `../micropython/` y `../cpp/`.

```
wokwi/
├── diagram.json                ← circuito para los proyectos de C/C++
└── diagram_micropython.json    ← el mismo circuito + firmware de MicroPython fijado
```

Los dos archivos describen **el mismo circuito**. La única diferencia es el campo
`attrs.env` de la placa, que en la variante de MicroPython fija la versión de firmware
(`micropython-20260406-v1.28.0`) para que la simulación arranque.

---

## Links de las simulaciones publicadas

| Escenario | Link |
|---|---|
| MicroPython — lectura del botón | _https://wokwi.com/projects/474718794103988225_ |
| MicroPython — debounce | _https://wokwi.com/projects/474718816219506689_ |
| MicroPython — semáforo | _https://wokwi.com/projects/474710654093435905_ |
| C/C++ — lectura del botón | _https://wokwi.com/projects/474711032994374657_ |
| C/C++ — semáforo | _https://wokwi.com/projects/474718794103988225_ |
