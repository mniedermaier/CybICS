/*
 * Copyright (c) 2024 CybICS
 * SPDX-License-Identifier: Apache-2.0
 *
 * Front-panel input, abstracted away from which board it runs on.
 *
 * The two board revisions do not share an input device:
 *
 *   v1.0   one discrete push-button on PA8.  3V3 -> R37 -> SW3 -> PA8 with
 *          R36 to GND, so pressed reads high and an internal pull-up would
 *          fight the divider.
 *   v1.1+  a 5-way navigation switch whose common is tied to GND, so every
 *          contact reads low when pressed and every pin needs the internal
 *          pull-up.  The centre press is still PA8; the four directions are
 *          PC6, PC7, PD8 and PD9, which do not exist on a v1.0 board.
 *
 * One firmware image serves both, so none of that can be decided at build
 * time and the devicetree cannot express it either.  This module reads the
 * revision once at start-up, configures whichever pins that board actually
 * has, and turns them into events.  The display thread consumes events and
 * never learns which board it is running on.
 *
 * The vocabulary is deliberately small.  Every event a v1.1 board can
 * produce, a v1.0 board can also reach, because the navigation switch is
 * allowed to make the UI quicker and never to make part of it unreachable.
 */

#ifndef UI_INPUT_H
#define UI_INPUT_H

#include <zephyr/kernel.h>
#include <stdbool.h>

enum ui_event {
	/* Advance one screen.  v1.0 button, v1.1 centre / down / right. */
	UI_EVENT_NEXT,
	/* Go back one screen.  v1.1 up / left only -- see below. */
	UI_EVENT_PREV,
};

/*
 * UI_EVENT_PREV is the one event a v1.0 board cannot emit, and that is
 * intentional rather than an oversight: with five screens, "back" is the same
 * as pressing "next" four more times.  Nothing is reachable only with the
 * navigation switch.
 */

/*
 * How often ui_input_poll() expects to be called.  The debounce window is
 * counted in polls, so the caller's sleep sets the response time.
 */
#define UI_INPUT_POLL_INTERVAL_MS 20

/*
 * Configure the pins this board has.  Call once, after hw_version_init() and
 * before the first poll.  Returns 0, or a negative errno if a pin could not be
 * configured; in that case the remaining pins still work and the module stays
 * usable.
 */
int ui_input_init(void);

/*
 * Sample every contact once and report at most one press.
 *
 * Returns true and fills *ev when a contact has just been pressed, false
 * otherwise.  Call it every UI_INPUT_POLL_INTERVAL_MS from a single thread.
 *
 * This is a function the caller drives rather than a thread of its own on
 * purpose.  A thread would want its own stack, and this board links at 90 % of
 * its 36 KB of RAM -- the display thread already has a stack and a loop, and
 * lending them costs nothing.
 */
bool ui_input_poll(enum ui_event *ev);

/* "1 button" or "5-way switch", for the boot log. Never NULL. */
const char *ui_input_backend_name(void);

#endif /* UI_INPUT_H */
