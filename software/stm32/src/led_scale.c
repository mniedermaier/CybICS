/*
 * Copyright (c) 2024 CybICS
 * SPDX-License-Identifier: Apache-2.0
 *
 * Overall LED brightness, see led_scale.h.
 */

#include "led_scale.h"

#include "persist.h"

#include <errno.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(led_scale, LOG_LEVEL_INF);

/* Read by the LED thread every PWM period, written by the display thread. */
static atomic_t scale = ATOMIC_INIT(LED_SCALE_DEFAULT);
static uint8_t stored = LED_SCALE_DEFAULT;

static bool valid(uint8_t value)
{
	return value >= LED_SCALE_MIN && value <= LED_SCALE_MAX &&
	       (value - LED_SCALE_MIN) % LED_SCALE_STEP == 0;
}

int led_scale_init(void)
{
	uint8_t value;
	ssize_t ret = persist_read(PERSIST_ID_LED_SCALE, &value, sizeof(value));

	if (ret == sizeof(value) && valid(value)) {
		stored = value;
		atomic_set(&scale, value);
		LOG_INF("LED brightness %u %% (saved)", value);
	} else {
		/* Nothing saved yet, or a value from a range this build does not know. */
		LOG_INF("LED brightness %u %% (default)", LED_SCALE_DEFAULT);
	}

	return ret < 0 && ret != -ENOENT ? (int)ret : 0;
}

uint8_t led_scale_get(void)
{
	return (uint8_t)atomic_get(&scale);
}

void led_scale_adjust(int delta)
{
	int value = (int)atomic_get(&scale) + delta;

	value = CLAMP(value, LED_SCALE_MIN, LED_SCALE_MAX);
	atomic_set(&scale, value);
}

int led_scale_save(void)
{
	uint8_t value = led_scale_get();
	int ret;

	if (value == stored) {
		return 0;
	}

	ret = persist_write(PERSIST_ID_LED_SCALE, &value, sizeof(value));
	if (ret < 0) {
		return ret;
	}

	stored = value;
	LOG_INF("LED brightness %u %% saved", value);
	return 0;
}
