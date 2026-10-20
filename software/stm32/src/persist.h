/*
 * Copyright (c) 2024 CybICS
 * SPDX-License-Identifier: Apache-2.0
 *
 * Settings that survive a reset: the overall LED brightness and the game
 * high scores.
 *
 * They live in the "storage" partition at the end of flash, through Zephyr's
 * NVS.  Reflashing the firmware does not touch it: OpenOCD only erases the
 * pages the image covers, and the image ends far below the partition.
 */

#ifndef PERSIST_H
#define PERSIST_H

#include <stddef.h>
#include <stdint.h>
#include <sys/types.h>

/* Entry IDs.  Permanent once a board has saved one: never renumber them. */
#define PERSIST_ID_LED_SCALE		1
#define PERSIST_ID_BEST_PRESSURE	2
#define PERSIST_ID_BEST_RUNNER		3
#define PERSIST_ID_BEST_REFLEX		4

/*
 * Mount the storage partition.  Call once from main() before anything reads
 * a setting.  Returns 0, or a negative errno; reads and writes then fail with
 * -ENODEV and every setting stays at its default until the next reset.
 */
int persist_init(void);

/* Read an entry.  Returns the number of bytes read, or a negative errno. */
ssize_t persist_read(uint16_t id, void *data, size_t len);

/*
 * Write an entry.  Returns 0, or a negative errno.  Erasing a page stalls the
 * CPU for some 20 ms on this single-bank part, so write when a value is
 * confirmed rather than every time it changes.
 */
int persist_write(uint16_t id, const void *data, size_t len);

#endif /* PERSIST_H */
