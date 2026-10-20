/*
 * Copyright (c) 2024 CybICS
 * SPDX-License-Identifier: Apache-2.0
 *
 * Overall LED brightness, set from the front panel and kept across resets.
 *
 * The per-colour shares in main.c make the colours match each other; this is
 * one factor on top of all of them, so a board can be made brighter for a
 * sunlit room or dimmer for a dark one without touching that balance.  100 %
 * is the calculated balance itself, and the range is 50-150 % in 10 % steps.
 *
 * The value lives in the "storage" partition at the end of flash, through
 * Zephyr's NVS.  Reflashing the firmware does not touch it: OpenOCD only
 * erases the pages the image covers, and the image ends far below the
 * partition.
 */

#ifndef LED_SCALE_H
#define LED_SCALE_H

#include <stdint.h>

#define LED_SCALE_MIN 50
#define LED_SCALE_MAX 150
#define LED_SCALE_STEP 10
#define LED_SCALE_DEFAULT 100

/*
 * Mount the storage and load the saved value.  Call once from main() before
 * any thread reads the scale.  Returns 0, or a negative errno if the storage
 * could not be mounted -- the scale then stays at the default and changes are
 * kept until the next reset only.
 */
int led_scale_init(void);

/* Current scale in percent, LED_SCALE_MIN..LED_SCALE_MAX. */
uint8_t led_scale_get(void);

/* Change the scale by delta percent, clamped to the range.  Not saved. */
void led_scale_adjust(int delta);

/*
 * Write the current scale to flash if it differs from what is stored.
 * Returns 0, or a negative errno.  Erasing a page stalls the CPU for some
 * 20 ms on this single-bank part, so call this when the user confirms rather
 * than on every step.
 */
int led_scale_save(void);

#endif /* LED_SCALE_H */
