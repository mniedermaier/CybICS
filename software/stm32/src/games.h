/*
 * Copyright (c) 2024 CybICS
 * SPDX-License-Identifier: Apache-2.0
 *
 * Front-panel games, v1.1 and newer.
 *
 * Three small games for the LCD and the 5-way switch, reached from the
 * "Games" screen.  They borrow the plant LEDs while they run, so the board
 * itself becomes part of the game:
 *
 *   Pressure Keeper  be the PLC: run the compressor by hand and keep the
 *                    high-pressure tank in range while demand swings
 *   Pipe Runner      jump the valves on a pipeline, duck the sparks
 *   Alarm Reflex     an alarm lights a part of the plant, press towards it
 *
 * The plant simulation keeps running underneath; only the LCD and the LEDs
 * belong to the game until it is left.  High scores are kept in flash.
 *
 * All of it runs in the display thread: games_render() is called on every
 * pass of its loop and advances the game by the time that has passed.
 */

#ifndef GAMES_H
#define GAMES_H

#include <stdbool.h>
#include <stdint.h>

#include "lcd_hd44780.h"
#include "ui_input.h"

/* The plant LEDs, in the order of pwm_leds in main.c. */
enum game_led {
	GL_GST_LOW,
	GL_GST_NORMAL,
	GL_GST_FULL,
	GL_C_ON,
	GL_C_OFF,
	GL_HPT_CRITICAL,
	GL_HPT_HIGH,
	GL_HPT_NORMAL,
	GL_HPT_LOW,
	GL_HPT_EMPTY,
	GL_BO_RED,
	GL_BO_GREEN,
	GL_S_RED,
	GL_S_GREEN,
	GL_SV_RED,
	GL_SV_GREEN,
	GAME_LED_COUNT,
};

/* Load the high scores.  Call once from main(), after persist_init(). */
void games_init(void);

/* Open the game menu on this panel.  The games take over its custom characters. */
void games_open(struct lcd_hd44780 *lcd);

/* True from games_open() until the player leaves the menu. */
bool games_active(void);

/* A switch press while games_active(). */
void games_key(enum ui_key key);

/* Advance the game to now and fill both lines, LCD_COLS characters each. */
void games_render(char *line0, char *line1);

/*
 * Provided by main.c: drive the plant LEDs from a game, each 0-100 % of its
 * colour's share, until game_leds_release() hands them back to the plant.
 */
void game_leds_set(const uint8_t level[GAME_LED_COUNT]);
void game_leds_release(void);

#endif /* GAMES_H */
