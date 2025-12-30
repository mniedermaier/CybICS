/*
 * Copyright (c) 2024 CybICS
 * SPDX-License-Identifier: Apache-2.0
 */

#ifndef VERSION_H
#define VERSION_H

/* Firmware version for display - update this for releases */
#define FIRMWARE_VERSION_MAJOR 1
#define FIRMWARE_VERSION_MINOR 1
#define FIRMWARE_VERSION_PATCH 2

/* Helper macros for stringification */
#define _STRINGIFY(x) #x
#define STRINGIFY(x) _STRINGIFY(x)

/* Version as string for display (generated from major.minor.patch) */
#define FIRMWARE_VERSION_STRING "v" STRINGIFY(FIRMWARE_VERSION_MAJOR) "." \
                                    STRINGIFY(FIRMWARE_VERSION_MINOR) "." \
                                    STRINGIFY(FIRMWARE_VERSION_PATCH)

/*
 * Build identifier for flash comparison - changes with every build.
 * BUILD_DATE and BUILD_TIME are defined by CMake in YYYY.MM.DD and HH:MM:SS format.
 * Falls back to __DATE__ __TIME__ if CMake definitions are missing.
 */
#ifndef BUILD_DATE
#define BUILD_DATE __DATE__
#endif
#ifndef BUILD_TIME
#define BUILD_TIME __TIME__
#endif
#define FIRMWARE_BUILD_ID BUILD_DATE " " BUILD_TIME

/* Magic marker to identify valid version block */
#define FIRMWARE_VERSION_MAGIC 0x43594249  /* "CYBI" in ASCII */

#endif /* VERSION_H */
