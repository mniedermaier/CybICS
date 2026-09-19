/*
 * Copyright (c) 2024 CybICS
 * SPDX-License-Identifier: Apache-2.0
 *
 * Hardware revision detection from the PCB version straps.
 *
 * From board v1.1 the PCB carries its revision as a 5-bit code on PC11..PC15,
 * one 10k resistor to GND per bit, read against the internal pull-up:
 * fitted = 0, omitted = 1.  The authoritative table lives in
 * hardware/README.md#version-coding; keep the two in step when a revision is
 * added.
 *
 * This exists because v1.1 changed the display button from a discrete
 * push-button (pressed = high, via an external divider) to a 5-way navigation
 * switch whose common is tied to GND (pressed = low).  One firmware image has
 * to serve both, so the polarity is chosen at runtime from the straps rather
 * than at build time.
 */

#ifndef HW_VERSION_H
#define HW_VERSION_H

#include <stdint.h>
#include <stdbool.h>

/* Number of strap bits, PC11..PC15. */
#define HW_VERSION_STRAP_BITS 5

/*
 * All straps high.  A pre-v1.1 board has no strap footprints, so its pins
 * float and the pull-ups win.  Never assign this code to a real revision.
 * Note that a v1.1 board assembled without any straps is indistinguishable
 * from a v1.0 board.
 */
#define HW_VERSION_CODE_NO_STRAPS 0x1F

/* Strap code of each known revision. */
#define HW_VERSION_CODE_V1_1 0x01

enum hw_revision {
	/* Pre-v1.1: no straps fitted, discrete push-button, pressed = high. */
	HW_REV_1_0 = 0,
	/* v1.1: navigation switch against GND, pressed = low. */
	HW_REV_1_1,
	/*
	 * A code this firmware does not know.  Codes are only ever assigned
	 * going forward, so an unknown one is a board newer than this build.
	 * It is treated like the newest revision we do know, which is the
	 * choice most likely to work; the alternative, falling back to v1.0,
	 * would break the navigation switch on every future board.
	 */
	HW_REV_UNKNOWN,
};

/*
 * Read the straps and cache the result.  Call once from main() before any
 * thread queries the revision.  Returns 0 on success, or a negative errno if
 * a strap pin could not be configured -- in which case the revision falls
 * back to the newest known one and the accessors below still work.
 */
int hw_version_init(void);

/* Raw 5-bit strap code, 0..31.  Valid only after hw_version_init(). */
uint8_t hw_version_code(void);

/* Decoded revision.  Valid only after hw_version_init(). */
enum hw_revision hw_version_get(void);

/* Human-readable revision, e.g. "v1.1" or "unknown". Never NULL. */
const char *hw_version_name(void);

/*
 * Same, but never longer than four characters, for the 16-column LCD:
 * "v1.0", "v1.1", or "?nn" with the raw code for an unrecognised board.
 * Built once in hw_version_init(), so it is safe to read from any thread.
 */
const char *hw_version_short(void);

/*
 * True when the board's front-panel switch pulls its pins low when pressed,
 * i.e. from v1.1 onwards.  False on a v1.0 board, where the discrete button
 * drives its pin high through an external divider.
 */
bool hw_version_switch_active_low(void);

#endif /* HW_VERSION_H */
