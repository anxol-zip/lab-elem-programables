# Sesion 03 - Proyecto Pico SDK: button_read

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

project(button_read C CXX ASM)

pico_sdk_init()

add_executable(button_read button_read.c)

pico_set_program_name(button_read "button_read")
pico_set_program_version(button_read "1.0")

# Serial por USB y por UART: asi el monitor funciona tanto en Wokwi
# como en la placa fisica sin recompilar.
pico_enable_stdio_uart(button_read 1)
pico_enable_stdio_usb(button_read 1)

target_link_libraries(button_read pico_stdlib)

target_include_directories(button_read PRIVATE ${CMAKE_CURRENT_LIST_DIR})

pico_add_extra_outputs(button_read)
