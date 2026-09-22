/*
 * Copyright (c) 2024 CybICS
 * SPDX-License-Identifier: Apache-2.0
 *
 * Front-panel input.  See ui_input.h for why this is a runtime abstraction
 * rather than a build-time one.
 */

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/logging/log.h>
#include <errno.h>

#include "ui_input.h"
#include "hw_version.h"

LOG_MODULE_REGISTER(ui_input, LOG_LEVEL_INF);

/*
 * Polling beats interrupts here.  The switch bounces for up to 20 ms by its
 * datasheet (SHOU HAN 7x7x5-6P-L WX: contact chatter <=10 ms new, <=20 ms at
 * end of life), so an edge interrupt would fire several times per press and
 * still need the same debounce state machine behind it.  Polling five pins
 * every 20 ms costs a handful of register reads and keeps the whole thing in
 * one place.
 */

/*
 * A press has to read the same way three times in a row -- 60 ms -- before it
 * counts.  That clears the datasheet's 20 ms worst case with room to spare and
 * is still far below the ~150 ms at which a person starts to feel lag.
 */
#define DEBOUNCE_SAMPLES 3

/*
 * Deliberately no auto-repeat.  With five screens, holding a direction to
 * scroll saves nobody anything, and repeat is exactly what made the old
 * one-second poll feel broken: hold the button for three seconds, advance
 * three screens.  One press, one screen.
 */

/* One polled contact. */
struct source {
	const struct gpio_dt_spec *spec;
	const char *name;
	enum ui_event event;
	/* Debounce state. */
	bool stable_pressed;
	bool candidate;
	uint8_t agree;
	/* Cleared when the pin could not be configured. */
	bool enabled;
};

static const struct gpio_dt_spec display_in =
	GPIO_DT_SPEC_GET(DT_NODELABEL(display_in), gpios);
static const struct gpio_dt_spec nav_up = GPIO_DT_SPEC_GET(DT_NODELABEL(nav_up), gpios);
static const struct gpio_dt_spec nav_down = GPIO_DT_SPEC_GET(DT_NODELABEL(nav_down), gpios);
static const struct gpio_dt_spec nav_left = GPIO_DT_SPEC_GET(DT_NODELABEL(nav_left), gpios);
static const struct gpio_dt_spec nav_right = GPIO_DT_SPEC_GET(DT_NODELABEL(nav_right), gpios);

/*
 * Index 0 is the centre / v1.0 button and is the only source a v1.0 board
 * has.  source_count is set by ui_input_init() to 1 or 5 accordingly, so the
 * four direction pins are never even configured on a board that does not have
 * them -- on v1.0 PC6, PC7, PD8 and PD9 are unconnected, and reading four
 * floating inputs would invent presses out of nothing.
 */
static struct source sources[] = {
	{ .spec = &display_in, .name = "centre", .event = UI_EVENT_NEXT },
	{ .spec = &nav_right, .name = "right", .event = UI_EVENT_NEXT },
	{ .spec = &nav_down, .name = "down", .event = UI_EVENT_NEXT },
	{ .spec = &nav_left, .name = "left", .event = UI_EVENT_PREV },
	{ .spec = &nav_up, .name = "up", .event = UI_EVENT_PREV },
};

#define SOURCE_CENTRE_ONLY 1
#define SOURCE_ALL ARRAY_SIZE(sources)

static size_t source_count = SOURCE_CENTRE_ONLY;
static const char *backend_name = "1 button";

/*
 * Read one contact as a logical "pressed".
 *
 * The four direction pins are GPIO_ACTIVE_LOW in the devicetree, so Zephyr
 * already returns 1 for pressed.  display_in cannot be: it is active high on
 * v1.0 and active low on v1.1, and the devicetree has no way to say "depends
 * on a strap read at boot".  It is therefore declared active high and
 * inverted here for the boards that need it.
 */
static bool read_pressed(const struct source *src)
{
	int level = gpio_pin_get_dt(src->spec);

	if (level < 0) {
		return false;
	}

	if (src->spec == &display_in && hw_version_switch_active_low()) {
		return level == 0;
	}

	return level != 0;
}

/* Returns true on a release-to-press transition. */
static bool debounce(struct source *src)
{
	bool now = read_pressed(src);

	if (now != src->candidate) {
		src->candidate = now;
		src->agree = 1;
		return false;
	}

	if (src->agree < DEBOUNCE_SAMPLES) {
		src->agree++;
	}

	if (src->agree < DEBOUNCE_SAMPLES || now == src->stable_pressed) {
		return false;
	}

	src->stable_pressed = now;

	/* Only the press edge is an event; the release is not. */
	return now;
}

bool ui_input_poll(enum ui_event *ev)
{
	/*
	 * Round-robin the starting point so that two contacts closed in the
	 * same poll do not always let the same one win.  It cannot happen on a
	 * switch with one stick, but it costs one byte to not depend on that.
	 */
	static size_t next;

	for (size_t n = 0; n < source_count; n++) {
		size_t i = (next + n) % source_count;
		struct source *src = &sources[i];

		if (!src->enabled || !debounce(src)) {
			continue;
		}

		LOG_DBG("%s pressed", src->name);
		*ev = src->event;
		next = (i + 1) % source_count;
		return true;
	}

	return false;
}

int ui_input_init(void)
{
	int err = 0;

	if (hw_version_get() == HW_REV_1_0) {
		source_count = SOURCE_CENTRE_ONLY;
		backend_name = "1 button";
	} else {
		source_count = SOURCE_ALL;
		backend_name = "5-way switch";
	}

	for (size_t i = 0; i < source_count; i++) {
		struct source *src = &sources[i];
		/*
		 * The v1.0 button has R36 pulling PA8 down on the board, so an
		 * internal pull-up there would fight it and the pin would read
		 * pressed for ever.  Every contact of the navigation switch
		 * needs one, because the switch only ever pulls to GND.
		 */
		gpio_flags_t extra = hw_version_switch_active_low() ? GPIO_PULL_UP : 0;
		int ret;

		if (!device_is_ready(src->spec->port)) {
			LOG_ERR("%s: GPIO port not ready", src->name);
			err = -ENODEV;
			continue;
		}

		ret = gpio_pin_configure_dt(src->spec, GPIO_INPUT | extra);
		if (ret < 0) {
			LOG_ERR("%s: configure failed: %d", src->name, ret);
			err = ret;
			continue;
		}

		src->enabled = true;
		/*
		 * Seed the debounce state from the pin rather than from zero,
		 * so a switch already held at boot does not count as a press
		 * the moment the first three samples agree.
		 */
		src->stable_pressed = read_pressed(src);
		src->candidate = src->stable_pressed;
		src->agree = DEBOUNCE_SAMPLES;
	}

	LOG_INF("Front panel: %s (%u contacts)", backend_name, (unsigned int)source_count);

	return err;
}

const char *ui_input_backend_name(void)
{
	return backend_name;
}
