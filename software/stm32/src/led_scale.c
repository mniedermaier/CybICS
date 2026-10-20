/*
 * Copyright (c) 2024 CybICS
 * SPDX-License-Identifier: Apache-2.0
 *
 * Overall LED brightness, see led_scale.h.
 */

#include "led_scale.h"

#include <zephyr/kernel.h>
#include <zephyr/drivers/flash.h>
#include <zephyr/fs/nvs.h>
#include <zephyr/logging/log.h>
#include <zephyr/storage/flash_map.h>

LOG_MODULE_REGISTER(led_scale, LOG_LEVEL_INF);

/* NVS entry holding the scale.  IDs are permanent once a board has saved one. */
#define NVS_ID_LED_SCALE 1

static struct nvs_fs fs;
static bool mounted;
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
	struct flash_pages_info info;
	uint8_t value;
	int ret;

	fs.flash_device = FIXED_PARTITION_DEVICE(storage_partition);
	if (!device_is_ready(fs.flash_device)) {
		LOG_ERR("flash device not ready");
		return -ENODEV;
	}

	fs.offset = FIXED_PARTITION_OFFSET(storage_partition);
	ret = flash_get_page_info_by_offs(fs.flash_device, fs.offset, &info);
	if (ret < 0) {
		LOG_ERR("no page info for the storage partition: %d", ret);
		return ret;
	}

	/* 4 KB of 2 KB pages: the two sectors NVS needs at the least. */
	fs.sector_size = info.size;
	fs.sector_count = FIXED_PARTITION_SIZE(storage_partition) / info.size;

	ret = nvs_mount(&fs);
	if (ret < 0) {
		LOG_ERR("mounting the storage partition failed: %d", ret);
		return ret;
	}
	mounted = true;

	ret = nvs_read(&fs, NVS_ID_LED_SCALE, &value, sizeof(value));
	if (ret == sizeof(value) && valid(value)) {
		stored = value;
		atomic_set(&scale, value);
		LOG_INF("LED brightness %u %% (saved)", value);
	} else {
		/* Nothing saved yet, or a value from a range this build does not know. */
		LOG_INF("LED brightness %u %% (default)", LED_SCALE_DEFAULT);
	}

	return 0;
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
	ssize_t ret;

	if (!mounted) {
		return -ENODEV;
	}
	if (value == stored) {
		return 0;
	}

	ret = nvs_write(&fs, NVS_ID_LED_SCALE, &value, sizeof(value));
	if (ret < 0) {
		LOG_ERR("saving LED brightness failed: %d", (int)ret);
		return (int)ret;
	}

	stored = value;
	LOG_INF("LED brightness %u %% saved", value);
	return 0;
}
