/*
 * Copyright (c) 2024 CybICS
 * SPDX-License-Identifier: Apache-2.0
 *
 * Hardware revision detection from the PCB version straps.  See hw_version.h
 * for the wiring and hardware/README.md#version-coding for the code table.
 */

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/logging/log.h>
#include <errno.h>

#include "hw_version.h"

LOG_MODULE_REGISTER(hw_version, LOG_LEVEL_INF);

/* Bit 0 first, so straps[i] is bit i of the code. */
static const struct gpio_dt_spec straps[HW_VERSION_STRAP_BITS] = {
	GPIO_DT_SPEC_GET(DT_NODELABEL(hw_ver0), gpios),
	GPIO_DT_SPEC_GET(DT_NODELABEL(hw_ver1), gpios),
	GPIO_DT_SPEC_GET(DT_NODELABEL(hw_ver2), gpios),
	GPIO_DT_SPEC_GET(DT_NODELABEL(hw_ver3), gpios),
	GPIO_DT_SPEC_GET(DT_NODELABEL(hw_ver4), gpios),
};

static uint8_t cached_code = HW_VERSION_CODE_NO_STRAPS;
static enum hw_revision cached_rev = HW_REV_UNKNOWN;

static enum hw_revision decode(uint8_t code)
{
	switch (code) {
	case HW_VERSION_CODE_NO_STRAPS:
		return HW_REV_1_0;
	case HW_VERSION_CODE_V1_1:
		return HW_REV_1_1;
	default:
		return HW_REV_UNKNOWN;
	}
}

int hw_version_init(void)
{
	uint8_t code = 0;
	int err = 0;

	for (int bit = 0; bit < HW_VERSION_STRAP_BITS; bit++) {
		const struct gpio_dt_spec *strap = &straps[bit];

		if (!device_is_ready(strap->port)) {
			LOG_ERR("version strap bit %d: GPIO port not ready", bit);
			err = -ENODEV;
			break;
		}

		/*
		 * The pull-up comes from the devicetree flags, but pass it
		 * explicitly as well: gpio_pin_configure_dt() ORs the two, and
		 * being explicit here keeps the read correct even if someone
		 * later drops the flag from the overlay.
		 */
		int ret = gpio_pin_configure_dt(strap, GPIO_INPUT | GPIO_PULL_UP);

		if (ret < 0) {
			LOG_ERR("version strap bit %d: configure failed: %d", bit, ret);
			err = ret;
			break;
		}

		/*
		 * The pull-up needs a moment to charge the pin and whatever
		 * stray capacitance hangs off it before the first read. A
		 * 10k pull-up against a few tens of pF settles in well under
		 * a microsecond, so this is generous.
		 */
		k_busy_wait(10);

		ret = gpio_pin_get_dt(strap);
		if (ret < 0) {
			LOG_ERR("version strap bit %d: read failed: %d", bit, ret);
			err = ret;
			break;
		}

		code |= (uint8_t)((ret ? 1U : 0U) << bit);
	}

	if (err < 0) {
		/*
		 * Reading the straps failed.  Assume the newest known board
		 * rather than the oldest: a v1.0 board has no straps to fail
		 * on, so a failure here almost certainly means newer hardware.
		 */
		cached_code = HW_VERSION_CODE_V1_1;
		cached_rev = HW_REV_1_1;
		LOG_ERR("version straps unreadable, assuming %s", hw_version_name());
		return err;
	}

	cached_code = code;
	cached_rev = decode(code);

	LOG_INF("Hardware revision: %s (straps 0b%c%c%c%c%c = %u)",
		hw_version_name(),
		(code & 0x10) ? '1' : '0',
		(code & 0x08) ? '1' : '0',
		(code & 0x04) ? '1' : '0',
		(code & 0x02) ? '1' : '0',
		(code & 0x01) ? '1' : '0',
		code);

	if (cached_rev == HW_REV_UNKNOWN) {
		LOG_WRN("Strap code %u is not a revision this firmware knows; "
			"treating the board as v1.1 or newer", code);
	}

	return 0;
}

uint8_t hw_version_code(void)
{
	return cached_code;
}

enum hw_revision hw_version_get(void)
{
	return cached_rev;
}

const char *hw_version_name(void)
{
	switch (cached_rev) {
	case HW_REV_1_0:
		return "v1.0";
	case HW_REV_1_1:
		return "v1.1";
	default:
		return "unknown";
	}
}

bool hw_version_switch_active_low(void)
{
	/* Everything except a confirmed pre-v1.1 board uses the GND-tied switch. */
	return cached_rev != HW_REV_1_0;
}
