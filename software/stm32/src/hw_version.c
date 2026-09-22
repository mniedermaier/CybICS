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
#include <stdio.h>
#include <string.h>

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

/*
 * PA8, the front-panel switch pin.  Used to break the one tie the straps
 * cannot: see probe_button_pin_is_v1_0() below.
 */
static const struct gpio_dt_spec display_in =
	GPIO_DT_SPEC_GET(DT_NODELABEL(display_in), gpios);

static uint8_t cached_code = HW_VERSION_CODE_NO_STRAPS;
static bool cached_straps_missing;
static unsigned int cached_straps_fitted;
static enum hw_revision cached_rev = HW_REV_UNKNOWN;
/* At most 4 characters plus NUL; filled in by hw_version_init(). */
static char cached_short[5] = "?";

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

static void set_short_name(void)
{
	switch (cached_rev) {
	case HW_REV_1_0:
		strcpy(cached_short, "v1.0");
		break;
	case HW_REV_1_1:
		strcpy(cached_short, "v1.1");
		break;
	default:
		/* The code is 5 bits, so at most "?31" -- always fits. */
		snprintf(cached_short, sizeof(cached_short), "?%u", cached_code);
		break;
	}
}

/*
 * Decide from PA8 alone whether this board has the v1.0 button circuit.
 *
 * The straps cannot answer this.  Code 0b11111 means "no straps fitted", and
 * a v1.0 board -- which has no strap footprints at all -- reads exactly the
 * same as a v1.1 board someone forgot to populate.  PA8 can tell them apart,
 * because the two revisions load it differently:
 *
 *   v1.0   R36, 10k to GND, always present.
 *   v1.1+  R54, 1k in series to the navigation switch, which is open unless
 *          somebody is pressing the centre.  Nothing else touches the pin.
 *
 * So: enable the internal pull-down and read, then the internal pull-up and
 * read.  A pin that follows the pull is floating and the board is v1.1 or
 * newer.  A pin that stays low against the pull-up has R36 on it and the
 * board is v1.0.
 *
 * The margin is thin in one direction and that is worth stating.  Against the
 * 25k end of the STM32G0's internal pull-up, R36 holds the pin at
 * 3.3 * 10/(10+25) = 0.94 V, and V_IL is 0.3*VDD = 0.99 V -- 50 mV of room.
 * At the 40k typical value it is 0.66 V and comfortable.  So a genuine v1.0
 * board with unlucky silicon could read as v1.1.  That is why this runs only
 * when the strap code is already ambiguous, and never overrides a board that
 * states its revision properly.
 *
 * It is also wrong if somebody is holding the switch down during boot, in
 * either direction.  Nothing can be done about that, and it is logged.
 *
 * Returns true if the pin looks like v1.0 (something pulls it down), false if
 * it looks floating, and falls back to true -- the conservative answer, since
 * that is what the code meant before this probe existed -- on any GPIO error.
 */
static bool probe_button_pin_is_v1_0(void)
{
	int with_pulldown;
	int with_pullup;

	if (!device_is_ready(display_in.port)) {
		LOG_ERR("PA8 probe: GPIO port not ready");
		return true;
	}

	if (gpio_pin_configure_dt(&display_in, GPIO_INPUT | GPIO_PULL_DOWN) < 0) {
		LOG_ERR("PA8 probe: pull-down configure failed");
		return true;
	}
	/* 10k against a few tens of pF settles in well under a microsecond. */
	k_busy_wait(100);
	with_pulldown = gpio_pin_get_dt(&display_in);

	if (gpio_pin_configure_dt(&display_in, GPIO_INPUT | GPIO_PULL_UP) < 0) {
		LOG_ERR("PA8 probe: pull-up configure failed");
		return true;
	}
	k_busy_wait(100);
	with_pullup = gpio_pin_get_dt(&display_in);

	if (with_pulldown < 0 || with_pullup < 0) {
		LOG_ERR("PA8 probe: read failed");
		return true;
	}

	LOG_DBG("PA8 probe: pull-down reads %d, pull-up reads %d", with_pulldown, with_pullup);

	if (with_pulldown != 0) {
		/*
		 * Something is driving the pin high while we pull it down.  On
		 * v1.0 that is the button being held; on v1.1 it cannot happen
		 * at all.  Either way the probe learned nothing.
		 */
		LOG_WRN("PA8 probe: pin high against the pull-down, "
			"button held during boot?  Assuming v1.0.");
		return true;
	}

	/* Low against the pull-up means R36 is there, i.e. a v1.0 board. */
	return with_pullup == 0;
}

/*
 * One strap pin, classified by what is actually soldered to it.
 *
 * A single read cannot tell a missing resistor from a missing footprint, and
 * reading every strap the same way is what lets this count the resistors
 * rather than guess at them.  Pull the pin down and read, then pull it up and
 * read:
 *
 *   fitted   1k to GND wins against the internal pull-up (25k..60k on the
 *            STM32G0), so the pin reads low both times.  3.3 * 1/26 = 0.13 V
 *            worst case against a V_IL of 0.99 V, which is not close.
 *   absent   nothing but the pin, so it follows whichever pull is on.
 *   fault    high while being pulled down: something is driving it.  Not a
 *            state this board can produce, so it is reported rather than
 *            folded into one of the other two.
 */
enum strap_state {
	STRAP_FITTED,
	STRAP_ABSENT,
	STRAP_FAULT,
};

static enum strap_state probe_strap(const struct gpio_dt_spec *strap, int bit)
{
	int pulled_down;
	int pulled_up;

	if (gpio_pin_configure_dt(strap, GPIO_INPUT | GPIO_PULL_DOWN) < 0) {
		LOG_ERR("strap bit %d: pull-down configure failed", bit);
		return STRAP_FAULT;
	}
	/* 1k against a few tens of pF settles far inside this. */
	k_busy_wait(100);
	pulled_down = gpio_pin_get_dt(strap);

	if (gpio_pin_configure_dt(strap, GPIO_INPUT | GPIO_PULL_UP) < 0) {
		LOG_ERR("strap bit %d: pull-up configure failed", bit);
		return STRAP_FAULT;
	}
	k_busy_wait(100);
	pulled_up = gpio_pin_get_dt(strap);

	if (pulled_down < 0 || pulled_up < 0) {
		LOG_ERR("strap bit %d: read failed", bit);
		return STRAP_FAULT;
	}

	if (pulled_down != 0) {
		return STRAP_FAULT;
	}

	return (pulled_up == 0) ? STRAP_FITTED : STRAP_ABSENT;
}

int hw_version_init(void)
{
	uint8_t code = 0;
	unsigned int fitted = 0;
	unsigned int faults = 0;
	int err = 0;

	for (int bit = 0; bit < HW_VERSION_STRAP_BITS; bit++) {
		const struct gpio_dt_spec *strap = &straps[bit];
		enum strap_state state;

		if (!device_is_ready(strap->port)) {
			LOG_ERR("version strap bit %d: GPIO port not ready", bit);
			err = -ENODEV;
			break;
		}

		state = probe_strap(strap, bit);

		switch (state) {
		case STRAP_FITTED:
			fitted++;
			/* bit stays 0 */
			break;
		case STRAP_FAULT:
			faults++;
			LOG_ERR("version strap bit %d: pin driven, cannot be read", bit);
			err = -EIO;
			__fallthrough;
		case STRAP_ABSENT:
			code |= (uint8_t)(1U << bit);
			break;
		}
	}

	if (err == -ENODEV) {
		/*
		 * Reading the straps failed outright.  Assume the newest known
		 * board rather than the oldest: a v1.0 board has no straps to
		 * fail on, so a failure here almost certainly means newer
		 * hardware.
		 */
		cached_code = HW_VERSION_CODE_V1_1;
		cached_rev = HW_REV_1_1;
		set_short_name();
		LOG_ERR("version straps unreadable, assuming %s", hw_version_name());
		return err;
	}

	cached_code = code;
	cached_rev = decode(code);
	cached_straps_fitted = fitted;

	/*
	 * Nothing soldered to any of the five.  That is what a v1.0 board looks
	 * like -- it has no strap footprints at all -- and also what a v1.1
	 * board looks like if the straps were left off the BOM.  The code alone
	 * cannot separate them, so ask PA8, which the two revisions load
	 * differently.
	 */
	if (fitted == 0 && !probe_button_pin_is_v1_0()) {
		cached_rev = HW_REV_1_1;
		cached_straps_missing = true;
	}

	set_short_name();

	LOG_INF("Hardware revision: %s (straps 0b%c%c%c%c%c = %u, %u of %d resistors fitted)",
		hw_version_name(),
		(code & 0x10) ? '1' : '0',
		(code & 0x08) ? '1' : '0',
		(code & 0x04) ? '1' : '0',
		(code & 0x02) ? '1' : '0',
		(code & 0x01) ? '1' : '0',
		code, fitted, HW_VERSION_STRAP_BITS);

	if (faults > 0) {
		LOG_ERR("%u version strap pin(s) are being driven and were read as absent; "
			"the revision above may be wrong", faults);
	}

	if (cached_straps_missing) {
		LOG_WRN("No version strap resistor is fitted, but PA8 has no pull-down: "
			"this is a v1.1 or newer board assembled without its straps.  "
			"Fit R41-R44 and leave R40 off to make the board state its revision.");
	}

	if (cached_rev == HW_REV_UNKNOWN) {
		LOG_WRN("Strap code %u is not a revision this firmware knows; "
			"treating the board as v1.1 or newer", code);
	}

	return err;
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

const char *hw_version_short(void)
{
	return cached_short;
}

unsigned int hw_version_straps_fitted(void)
{
	return cached_straps_fitted;
}

bool hw_version_straps_missing(void)
{
	return cached_straps_missing;
}

bool hw_version_switch_active_low(void)
{
	/* Everything except a confirmed pre-v1.1 board uses the GND-tied switch. */
	return cached_rev != HW_REV_1_0;
}
