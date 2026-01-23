/*
 * Copyright (c) 2024 CybICS
 * SPDX-License-Identifier: Apache-2.0
 */

#ifndef VERSION_H
#define VERSION_H

#include <zephyr/toolchain.h>

/* Firmware version for display - update this for releases */
#define FIRMWARE_VERSION_MAJOR 1
#define FIRMWARE_VERSION_MINOR 2
#define FIRMWARE_VERSION_PATCH 0

/* Version as string for display (uses Zephyr's STRINGIFY macro) */
#define FIRMWARE_VERSION_STRING "v" STRINGIFY(FIRMWARE_VERSION_MAJOR) "." \
                                    STRINGIFY(FIRMWARE_VERSION_MINOR) "." \
                                    STRINGIFY(FIRMWARE_VERSION_PATCH)

/*
 * Build timestamp for display on LCD.
 * BUILD_DATE and BUILD_TIME are defined by CMake in YYYY.MM.DD and HH:MM:SS format.
 * Falls back to __DATE__ __TIME__ if CMake definitions are missing.
 */
#ifndef BUILD_DATE
#define BUILD_DATE __DATE__
#endif
#ifndef BUILD_TIME
#define BUILD_TIME __TIME__
#endif

#endif /* VERSION_H */
