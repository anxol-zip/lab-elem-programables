cmake_minimum_required(VERSION 3.13)

include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

project(memory_map_demo C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

add_executable(memory_map_demo
    memory_map_demo.c
)

pico_set_board(memory_map_demo pico2_w)

pico_enable_stdio_usb(memory_map_demo 1)
pico_enable_stdio_uart(memory_map_demo 0)

target_link_libraries(memory_map_demo pico_stdlib)

pico_add_extra_outputs(memory_map_demo)
