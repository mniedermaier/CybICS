# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.20.0)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(cybics)

# Generate build timestamp in desired format
string(TIMESTAMP BUILD_DATE "%Y.%m.%d")
string(TIMESTAMP BUILD_TIME "%H:%M:%S")
add_definitions(-DBUILD_DATE="${BUILD_DATE}" -DBUILD_TIME="${BUILD_TIME}")

list(APPEND CMAKE_MODULE_PATH ${ZEPHYR_BASE}/modules/nanopb)
include(nanopb)

zephyr_nanopb_sources(app proto/cybics.proto)

target_sources(app PRIVATE
    src/main.c
    src/lcd_hd44780.c
)
