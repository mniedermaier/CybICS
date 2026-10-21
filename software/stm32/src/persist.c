/*
 * Copyright (c) 2024 CybICS
 * SPDX-License-Identifier: Apache-2.0
 *
 * Settings that survive a reset, see persist.h.
 */

#include "persist.h"

#include <errno.h>
#include <zephyr/kernel.h>
#include <zephyr/drivers/flash.h>
#include <zephyr/fs/nvs.h>
#include <zephyr/logging/log.h>
#include <zephyr/storage/flash_map.h>

LOG_MODULE_REGISTER(persist, LOG_LEVEL_INF);

static struct nvs_fs fs;
static bool mounted;

int persist_init(void)
{
	struct flash_pages_info info;
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
	return 0;
}

ssize_t persist_read(uint16_t id, void *data, size_t len)
{
	if (!mounted) {
		return -ENODEV;
	}
	return nvs_read(&fs, id, data, len);
}

int persist_write(uint16_t id, const void *data, size_t len)
{
	ssize_t ret;

	if (!mounted) {
		return -ENODEV;
	}
	ret = nvs_write(&fs, id, data, len);
	if (ret < 0) {
		LOG_ERR("saving entry %u failed: %d", id, (int)ret);
		return (int)ret;
	}
	return 0;
}
