import time
time.sleep(0.1) # Wait for USB to be ready

import os, gc, machine

print("Prueba en Pi Pico W con Python")
print()

print(os.uname())
print('Freq:', machine.freq())
print()

gc.collect()
print('Memoria libre inicial:', gc.mem_free())

buffer = bytearray(10000)
print('Después de reservar 10000 B:', gc.mem_free())

buffer = bytearray(20000)
print('Después de reservar 20000 B:', gc.mem_free())

del buffer
gc.collect()
print('Después de liberar:', gc.mem_free())

print()