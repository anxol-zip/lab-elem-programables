# Sesion 03 - Proyecto Pico SDK: traffic_light

cmake_minimum_required(VERSION 3.13)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# == DO NOT EDIT THE FOLLOWING LINES for the Raspberry Pi Pico VS Code Extension to work ==
if(WIN32)
    set(USERHOME $ENV{USERPROFILE})
else()
    set(USERHOME $ENV{HOME})
endif()
set(sdkVersion 2.3.1)
set(toolchainVersion 15_2_Rel1)
set(picotoolVersion 2.3.1)
set(picoVscode ${USERHOME}/.pico-sdk/cmake/pico-vscode.cmake)
if (EXISTS ${picoVscode})
    include(${picoVscode})
endif()
# ====================================================================================

# RP2040: es el chip que simula Wokwi (parte wokwi-pi-pico).
# Para compilar hacia la Pico 2 W fisica, cambiar a: pico2_w
set(PICO_BOARD pico CACHE STRING "Board type")

include(pico_sdk_import.cmake)

project(traffic_light C CXX ASM)

pico_sdk_init()

add_executable(traffic_light traffic_light.c)

pico_set_program_name(traffic_light "traffic_light")
pico_set_program_version(traffic_light "1.0")

# Serial por USB y por UART: asi el monitor funciona tanto en Wokwi
# como en la placa fisica sin recompilar.
pico_enable_stdio_uart(traffic_light 1)
pico_enable_stdio_usb(traffic_light 1)

target_link_libraries(traffic_light pico_stdlib)

target_include_directories(traffic_light PRIVATE ${CMAKE_CURRENT_LIST_DIR})

pico_add_extra_outputs(traffic_light)
