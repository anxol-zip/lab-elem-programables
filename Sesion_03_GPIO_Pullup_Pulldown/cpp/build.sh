#!/usr/bin/env bash
# =========================================================================
#  Compila los proyectos de C/C++ de la Sesion 03 para la PICO 2 W FISICA.
#
#  Por que existe: el toolchain de la Pico (arm-none-eabi-gcc, ninja y el
#  cmake del SDK) vive en ~/.pico-sdk/ y solo lo inyecta en el PATH la
#  extension "Raspberry Pi Pico" de VS Code. Fuera de VS Code hay que
#  exportarlo a mano, o cmake usa el gcc del sistema y falla.
#
#  Este binario es SOLO para la placa fisica (RP2350). La simulacion del
#  mismo codigo se corre en wokwi.com, que compila aparte para RP2040.
#
#  Uso:
#     ./build.sh                  compila los dos proyectos
#     ./build.sh button_read      compila solo uno
#     ./build.sh --clean          borra los build/ y recompila todo
#
#  Si el enlazado falla con "dangerous relocation: unsupported relocation"
#  o "Unknown destination type (ARM/Thumb)" al compilar newlib, es el bug
#  del toolchain 15_2_Rel1 (GCC 15.2 / binutils 2.44) con el multilib de
#  Cortex-M33 del RP2350. Solucion: instalar 14_2_Rel1 desde la extension
#  de VS Code ("Switch SDK") y recompilar con:
#     TOOLCHAIN_VERSION=14_2_Rel1 ./build.sh --clean
# =========================================================================

set -euo pipefail

SDK_VERSION="2.3.1"
TOOLCHAIN_VERSION="${TOOLCHAIN_VERSION:-15_2_Rel1}"
CMAKE_VERSION="v4.3.4"
NINJA_VERSION="v1.13.2"
PICOTOOL_VERSION="2.3.1"

PICO_ROOT="${HOME}/.pico-sdk"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Toolchain -----------------------------------------------------------
export PICO_SDK_PATH="${PICO_ROOT}/sdk/${SDK_VERSION}"
export PICO_TOOLCHAIN_PATH="${PICO_ROOT}/toolchain/${TOOLCHAIN_VERSION}"
export PATH="${PICO_TOOLCHAIN_PATH}/bin:${PICO_ROOT}/picotool/${PICOTOOL_VERSION}/picotool:${PICO_ROOT}/cmake/${CMAKE_VERSION}/bin:${PICO_ROOT}/ninja/${NINJA_VERSION}:${PATH}"

if [[ ! -d "${PICO_SDK_PATH}" ]]; then
    echo "ERROR: no se encontro el SDK en ${PICO_SDK_PATH}"
    echo "Instalalo con la extension 'Raspberry Pi Pico' de VS Code."
    exit 1
fi

# --- Argumentos ----------------------------------------------------------
CLEAN=0
PROJECTS=()
for arg in "$@"; do
    case "$arg" in
        --clean) CLEAN=1 ;;
        *)       PROJECTS+=("$arg") ;;
    esac
done
if [[ ${#PROJECTS[@]} -eq 0 ]]; then
    PROJECTS=(button_read traffic_light)
fi

# --- Compilacion ---------------------------------------------------------
for project in "${PROJECTS[@]}"; do
    src="${HERE}/${project}"

    if [[ ! -f "${src}/CMakeLists.txt" ]]; then
        echo "ERROR: ${project} no es un proyecto valido (falta CMakeLists.txt)"
        exit 1
    fi

    echo ""
    echo "=================================================="
    echo " Compilando ${project}"
    echo "=================================================="

    [[ ${CLEAN} -eq 1 ]] && rm -rf "${src}/build"

    cmake -S "${src}" -B "${src}/build" -G Ninja -DCMAKE_BUILD_TYPE=Debug
    cmake --build "${src}/build"

    echo ""
    echo "OK -> ${src}/build/${project}.uf2"
done

echo ""
echo "Listo. Copia el .uf2 a la Pico 2 W en modo BOOTSEL para flashearla."
