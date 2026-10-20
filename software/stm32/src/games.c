/*
 * Copyright (c) 2024 CybICS
 * SPDX-License-Identifier: Apache-2.0
 *
 * Front-panel games, see games.h.
 *
 * Custom characters: each game loads CGRAM slots 1-7 when it starts.  Slot 0
 * stays unused, because its code would end a C string.  The other screens
 * use only the character ROM, so nothing needs restoring when a game ends.
 */

#include "games.h"

#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/util.h>

#include "persist.h"

LOG_MODULE_REGISTER(games, LOG_LEVEL_INF);

#define CG(slot) ((char)(slot))	/* custom character in a string */
#define ROM_LEFT ((char)0x7F)
#define ROM_RIGHT ((char)0x7E)

/* Ignore presses this long after a game ends, so a late press does not restart it. */
#define OVER_HOLD_MS 800

enum game_id {
	GAME_PRESSURE,
	GAME_RUNNER,
	GAME_REFLEX,
	GAME_COUNT,
};

struct game {
	const char *name;
	uint16_t persist_id;
	bool lower_is_better;
	/* Every direction is a move, so left cannot mean "give up". */
	bool uses_left;
	void (*start)(int64_t now);
	void (*key)(enum ui_key key, int64_t now);
	/* Advance to now and draw; return true once the game is over. */
	bool (*step)(int64_t now, char *line0, char *line1);
	/* The result to compare with the best, valid once step() returned true. */
	uint32_t (*score)(void);
	/* Score as shown, at most 6 characters. */
	void (*format)(uint32_t score, char *buf, size_t len);
	/* First line of the game-over screen. */
	const char *(*over_text)(void);
};

static struct lcd_hd44780 *panel;
static enum { MODE_OFF, MODE_MENU, MODE_PLAY, MODE_OVER } mode;
static enum game_id selected;
static uint32_t best[GAME_COUNT];	/* 0: no score yet */
static bool new_best;
static int64_t over_since;
static uint8_t leds[GAME_LED_COUNT];
static uint32_t rng_state = 1;

static uint32_t rnd(void)
{
	/* xorshift32: plenty for a game, and needs no entropy driver. */
	rng_state ^= rng_state << 13;
	rng_state ^= rng_state >> 17;
	rng_state ^= rng_state << 5;
	return rng_state;
}

/* A number from lo to hi, both included. */
static int rnd_range(int lo, int hi)
{
	return lo + (int)(rnd() % (uint32_t)(hi - lo + 1));
}

static void load_chars(const uint8_t (*chars)[8], size_t count)
{
	for (size_t i = 0; i < count; i++) {
		lcd_create_char(panel, (uint8_t)(i + 1), chars[i]);
	}
}

static void leds_clear(void)
{
	memset(leds, 0, sizeof(leds));
}

static void leds_show(void)
{
	game_leds_set(leds);
}

/*
 * Format into a panel line, cut at LCD_COLS.  Cutting is what a 16-column
 * panel does anyway, so it is not worth a truncation warning per call.
 */
static void __printf_like(2, 3) put(char *line, const char *fmt, ...)
{
	va_list ap;

	va_start(ap, fmt);
	vsnprintf(line, LCD_COLS + 1, fmt, ap);
	va_end(ap);
}

/* Pad or cut a line to exactly LCD_COLS characters. */
static void pad(char *line)
{
	size_t len = strlen(line);

	if (len < LCD_COLS) {
		memset(line + len, ' ', LCD_COLS - len);
	}
	line[LCD_COLS] = '\0';
}

/*
 * Pressure Keeper.
 *
 * The player is the PLC.  The compressor moves gas from the storage tank
 * (GST) into the high-pressure tank (HPT), the plant draws it out again, and
 * the draw swings more and more as time goes on.  Up and down set the
 * compressor in six stages; the centre pauses.
 *
 * Two things make it more than "match the number": the compressor spins up
 * and down over a few hundred milliseconds, so a late correction overshoots,
 * and the GST refills slower than a busy plant drains it -- running the
 * compressor flat out to be safe empties the storage, and then there is
 * nothing left to pump.
 *
 * Units are tenths of a percent.  The game steps every 50 ms.
 */
#define PK_STEP_MS 50
#define PK_STAGES 5
#define PK_FLOW_PER_STAGE 5	/* per step at full spin */
#define PK_REFILL 9		/* GST per step */
#define PK_CRITICAL 850		/* blows out after PK_CRITICAL_MS above this */
#define PK_CRITICAL_MS 1500
#define PK_EMPTY 80		/* the plant fails after PK_EMPTY_MS below this */
#define PK_EMPTY_MS 3000

static const uint8_t pk_chars[][8] = {
	/* slots 1-4: a bar cell 1-4 columns full */
	{ 0x00, 0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x00 },
	{ 0x00, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x00 },
	{ 0x00, 0x1C, 0x1C, 0x1C, 0x1C, 0x1C, 0x1C, 0x00 },
	{ 0x00, 0x1E, 0x1E, 0x1E, 0x1E, 0x1E, 0x1E, 0x00 },
	/* slot 5: a full cell, the same height */
	{ 0x00, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x00 },
};

static struct {
	int hpt, gst;
	int flow, stage;
	int demand, demand_target;
	int critical_ms, empty_ms;
	int64_t start, next_step, next_demand, paused_at;
	bool paused, blown;
	uint32_t seconds;
} pk;

static void pk_start(int64_t now)
{
	load_chars(pk_chars, ARRAY_SIZE(pk_chars));
	memset(&pk, 0, sizeof(pk));
	pk.hpt = 500;
	pk.gst = 800;
	pk.stage = 2;
	pk.flow = 2 * PK_FLOW_PER_STAGE;
	pk.demand = pk.demand_target = 8;
	pk.start = pk.next_step = pk.next_demand = now;
}

static void pk_key(enum ui_key key, int64_t now)
{
	if (key == UI_KEY_CENTRE) {
		if (pk.paused) {
			/* Shift the clock past the pause. */
			int64_t gap = now - pk.paused_at;

			pk.start += gap;
			pk.next_step += gap;
			pk.next_demand += gap;
		} else {
			pk.paused_at = now;
		}
		pk.paused = !pk.paused;
	} else if (pk.paused) {
		return;
	} else if (key == UI_KEY_UP && pk.stage < PK_STAGES) {
		pk.stage++;
	} else if (key == UI_KEY_DOWN && pk.stage > 0) {
		pk.stage--;
	}
}

/* One 50 ms step of the plant.  Returns true when it fails. */
static bool pk_tick(int64_t now)
{
	uint32_t elapsed_s = (uint32_t)((now - pk.start) / 1000);

	/* The plant's draw wanders, wider and jumpier the longer the game runs. */
	if (now >= pk.next_demand) {
		int high = MIN(10 + (int)elapsed_s / 8, 24);

		pk.demand_target = rnd_range(4, high);
		if (rnd() % 5 == 0) {
			pk.demand_target = high + 6;	/* a big consumer switches on */
		}
		pk.next_demand = now + rnd_range(1500, 3000);
	}
	pk.demand += pk.demand > pk.demand_target ? -1 : (pk.demand < pk.demand_target);

	/* The compressor spins towards its stage, a quarter of the way per step. */
	int target = pk.stage * PK_FLOW_PER_STAGE;
	int diff = target - pk.flow;

	pk.flow += diff / 4 != 0 ? diff / 4 : (diff > 0) - (diff < 0);

	int moved = MIN(pk.flow, pk.gst);

	pk.gst = MIN(1000, pk.gst - moved + PK_REFILL);
	pk.hpt = CLAMP(pk.hpt + moved - pk.demand, 0, 1000);

	pk.critical_ms = pk.hpt > PK_CRITICAL ? pk.critical_ms + PK_STEP_MS : 0;
	pk.empty_ms = pk.hpt < PK_EMPTY ? pk.empty_ms + PK_STEP_MS : 0;

	if (pk.hpt >= 1000 || pk.critical_ms >= PK_CRITICAL_MS) {
		pk.blown = true;
		return true;
	}
	return pk.empty_ms >= PK_EMPTY_MS;
}

static bool pk_step(int64_t now, char *line0, char *line1)
{
	bool over = false;

	while (!pk.paused && !over && now >= pk.next_step) {
		over = pk_tick(pk.next_step);
		pk.next_step += PK_STEP_MS;
	}
	if (!pk.paused) {
		pk.seconds = (uint32_t)((now - pk.start) / 1000);
	}

	/* "HPT" + a ten-cell bar + the percentage. */
	int columns = pk.hpt * 50 / 1000;

	strcpy(line0, "HPT");
	for (int c = 0; c < 10; c++) {
		int fill = CLAMP(columns - c * 5, 0, 5);

		line0[3 + c] = fill == 0 ? ' ' : CG(fill);
	}
	snprintf(line0 + 13, 4, "%3u", (uint8_t)(pk.hpt / 10));

	if (pk.paused) {
		put(line1, "PAUSE  OK:resume");
	} else {
		put(line1, "C:%d GST%3d%% %3us", pk.stage, pk.gst / 10,
			 (unsigned int)MIN(pk.seconds, 999U));
	}

	/* The plant LEDs show the game's plant. */
	leds_clear();
	leds[pk.hpt < 100 ? GL_HPT_EMPTY : pk.hpt < 350 ? GL_HPT_LOW :
	     pk.hpt < 650 ? GL_HPT_NORMAL : pk.hpt <= PK_CRITICAL ? GL_HPT_HIGH :
	     GL_HPT_CRITICAL] = 100;
	leds[pk.gst < 250 ? GL_GST_LOW : pk.gst < 750 ? GL_GST_NORMAL : GL_GST_FULL] = 100;
	leds[pk.stage > 0 ? GL_C_ON : GL_C_OFF] = 100;
	leds[pk.hpt >= 350 && pk.hpt < 650 ? GL_S_GREEN : GL_S_RED] = 100;
	leds[over && pk.blown ? GL_BO_RED : GL_BO_GREEN] = 100;
	leds[GL_SV_GREEN] = 100;
	/* Blink the critical LED while the blow-out timer runs. */
	if (pk.critical_ms > 0 && (now / 150) % 2) {
		leds[GL_HPT_CRITICAL] = 0;
	}
	leds_show();

	return over;
}

static uint32_t pk_score(void)
{
	return pk.seconds;
}

static void fmt_seconds(uint32_t score, char *buf, size_t len)
{
	snprintf(buf, len, "%us", (unsigned int)score);
}

static const char *pk_over_text(void)
{
	return pk.blown ? "BLOW-OUT!" : "Starved!";
}

/*
 * Pipe Runner.
 *
 * A jump-and-run along a pipeline.  Valves sit on the pipe and have to be
 * jumped; from ten points on, sparks fly at head height and have to be run
 * under -- so jumping everything does not work either.  Up or the centre
 * jumps.  Every obstacle passed is a point, and the game speeds up with
 * every one.
 *
 * The field is the left 13 columns, the score sits on the right of the top
 * row.  The runner stays in column 1.
 */
#define RUN_FIELD 13
#define RUN_COL 1
#define RUN_AIR_STEPS 3
#define RUN_SPARKS_FROM 10

static const uint8_t run_chars[][8] = {
	/* slot 1, 2: running */
	{ 0x0C, 0x0C, 0x00, 0x0E, 0x1C, 0x0C, 0x1A, 0x13 },
	{ 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x0C, 0x0C, 0x0E },
	/* slot 3: jumping */
	{ 0x0C, 0x0C, 0x00, 0x1E, 0x0D, 0x1F, 0x10, 0x00 },
	/* slot 4: a valve on the pipe */
	{ 0x0E, 0x04, 0x11, 0x1B, 0x1F, 0x1B, 0x11, 0x1F },
	/* slot 5: a spark */
	{ 0x04, 0x15, 0x0E, 0x1F, 0x0E, 0x15, 0x04, 0x00 },
	/* slot 6: the pipe */
	{ 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1F },
	/* slot 7: crashed */
	{ 0x00, 0x00, 0x00, 0x00, 0x11, 0x0A, 0x04, 0x1F },
};

static struct {
	bool ground[RUN_FIELD];
	bool air[RUN_FIELD];
	int air_steps;		/* > 0 while in the air */
	int gap;		/* columns until the next obstacle */
	bool last_was_air;
	uint32_t points;
	int64_t next_step;
	bool crashed;
	uint32_t frame;
} run;

static int run_period_ms(void)
{
	return MAX(90, 220 - (int)run.points * 4);
}

static void run_start(int64_t now)
{
	load_chars(run_chars, ARRAY_SIZE(run_chars));
	memset(&run, 0, sizeof(run));
	run.gap = 6;
	run.next_step = now + 600;	/* a moment to get ready */
}

static void run_key(enum ui_key key, int64_t now)
{
	ARG_UNUSED(now);

	if ((key == UI_KEY_UP || key == UI_KEY_CENTRE) && run.air_steps == 0) {
		run.air_steps = RUN_AIR_STEPS;
	}
}

static void run_tick(void)
{
	/* An obstacle leaving the field is one passed. */
	if (run.ground[0] || run.air[0]) {
		run.points++;
	}
	memmove(run.ground, run.ground + 1, RUN_FIELD - 1);
	memmove(run.air, run.air + 1, RUN_FIELD - 1);
	run.ground[RUN_FIELD - 1] = false;
	run.air[RUN_FIELD - 1] = false;

	if (--run.gap <= 0) {
		bool spark = run.points >= RUN_SPARKS_FROM && rnd() % 3 == 0;

		if (spark) {
			run.air[RUN_FIELD - 1] = true;
		} else {
			run.ground[RUN_FIELD - 1] = true;
		}
		/*
		 * Three columns is the shortest gap a jump can land in and
		 * take off from again; a spark right after a valve needs one
		 * more, because the jump over the valve has to come down first.
		 */
		run.gap = rnd_range(spark != run.last_was_air ? 4 : 3, 8);
		run.last_was_air = spark;
	}

	if (run.air_steps > 0) {
		run.air_steps--;
	}
	run.frame++;

	bool up = run.air_steps > 0;

	if ((run.ground[RUN_COL] && !up) || (run.air[RUN_COL] && up)) {
		run.crashed = true;
	}
}

static bool run_step(int64_t now, char *line0, char *line1)
{
	while (!run.crashed && now >= run.next_step) {
		run_tick();
		run.next_step += run_period_ms();
	}

	bool up = run.air_steps > 0;

	for (int c = 0; c < RUN_FIELD; c++) {
		line0[c] = run.air[c] ? CG(5) : ' ';
		line1[c] = run.ground[c] ? CG(4) : CG(6);
	}
	if (run.crashed) {
		(up ? line0 : line1)[RUN_COL] = CG(7);
	} else if (up) {
		line0[RUN_COL] = CG(3);
	} else {
		line1[RUN_COL] = CG(1 + run.frame % 2);
	}
	snprintf(line0 + RUN_FIELD, 4, "%3u", (unsigned int)MIN(run.points, 999U));
	line1[RUN_FIELD] = '\0';
	strcat(line1, "   ");

	/* The speed climbs the HPT column; a jump lights the compressor. */
	static const enum game_led speed[] = {
		GL_HPT_EMPTY, GL_HPT_LOW, GL_HPT_NORMAL, GL_HPT_HIGH, GL_HPT_CRITICAL,
	};

	leds_clear();
	for (size_t i = 0; i <= MIN(run.points / 8, ARRAY_SIZE(speed) - 1); i++) {
		leds[speed[i]] = 100;
	}
	leds[up ? GL_C_ON : GL_C_OFF] = 100;
	if (run.crashed) {
		leds[GL_BO_RED] = leds[GL_S_RED] = leds[GL_SV_RED] = 100;
	} else {
		leds[GL_S_GREEN] = 100;
	}
	leds_show();

	return run.crashed;
}

static uint32_t run_score(void)
{
	return run.points;
}

static void fmt_points(uint32_t score, char *buf, size_t len)
{
	snprintf(buf, len, "%upt", (unsigned int)score);
}

static const char *run_over_text(void)
{
	return "Crashed!";
}

/*
 * Alarm Reflex.
 *
 * An alarm lights one part of the plant, and the operator acknowledges it by
 * pressing towards it: up for the blow-out valve at the top of the board,
 * down for the system valve at the bottom, left for the storage tank, right
 * for the system.  Five alarms; the score is the average reaction time.  A
 * press before the alarm, or towards the wrong part, counts as a slow one.
 */
#define RX_ROUNDS 5
#define RX_PENALTY_MS 1000
#define RX_TIMEOUT_MS 1500
#define RX_SHOW_MS 900

static const uint8_t rx_chars[][8] = {
	/* slot 1: arrow up, slot 2: arrow down */
	{ 0x04, 0x0E, 0x15, 0x04, 0x04, 0x04, 0x04, 0x00 },
	{ 0x04, 0x04, 0x04, 0x04, 0x15, 0x0E, 0x04, 0x00 },
};

struct rx_target {
	enum ui_key key;
	const char *name;
	char arrow;
	enum game_led leds[4];
	size_t led_count;
};

static const struct rx_target rx_targets[] = {
	{ UI_KEY_UP, "Blow-out", CG(1), { GL_BO_RED, GL_BO_GREEN }, 2 },
	{ UI_KEY_DOWN, "Valve", CG(2), { GL_SV_RED, GL_SV_GREEN }, 2 },
	{ UI_KEY_LEFT, "GST", ROM_LEFT, { GL_GST_LOW, GL_GST_NORMAL, GL_GST_FULL }, 3 },
	{ UI_KEY_RIGHT, "System", ROM_RIGHT, { GL_S_RED, GL_S_GREEN }, 2 },
};

static struct {
	enum { RX_WAIT, RX_ALARM, RX_RESULT } phase;
	int round;
	int target;
	uint32_t total_ms;
	uint32_t last_ms;
	const char *verdict;	/* NULL: a clean reaction */
	int64_t phase_at;	/* when the phase began (the alarm: when it lit) */
	int64_t alarm_at;	/* RX_WAIT: when the alarm goes off */
} rx;

static void rx_wait(int64_t now)
{
	rx.phase = RX_WAIT;
	rx.phase_at = now;
	rx.alarm_at = now + rnd_range(1200, 3500);
}

static void rx_start(int64_t now)
{
	load_chars(rx_chars, ARRAY_SIZE(rx_chars));
	memset(&rx, 0, sizeof(rx));
	rx_wait(now);
}

static void rx_result(int64_t now, uint32_t ms, const char *verdict)
{
	rx.last_ms = ms;
	rx.total_ms += ms;
	rx.verdict = verdict;
	rx.round++;
	rx.phase = RX_RESULT;
	rx.phase_at = now;
}

static void rx_key(enum ui_key key, int64_t now)
{
	if (rx.phase == RX_WAIT) {
		rx_result(now, RX_PENALTY_MS, "Too early!");
	} else if (rx.phase == RX_ALARM) {
		if (key == rx_targets[rx.target].key) {
			rx_result(now, (uint32_t)(now - rx.phase_at), NULL);
		} else {
			rx_result(now, RX_PENALTY_MS, "Wrong way!");
		}
	}
}

static bool rx_step(int64_t now, char *line0, char *line1)
{
	const struct rx_target *t = &rx_targets[rx.target];

	if (rx.phase == RX_WAIT && now >= rx.alarm_at) {
		rx.phase = RX_ALARM;
		rx.phase_at = now;
		rx.target = rnd_range(0, ARRAY_SIZE(rx_targets) - 1);
		t = &rx_targets[rx.target];
	} else if (rx.phase == RX_ALARM && now - rx.phase_at >= RX_TIMEOUT_MS) {
		rx_result(now, RX_TIMEOUT_MS, "Too slow!");
	} else if (rx.phase == RX_RESULT && now - rx.phase_at >= RX_SHOW_MS) {
		if (rx.round >= RX_ROUNDS) {
			return true;
		}
		rx_wait(now);
	}

	leds_clear();
	switch (rx.phase) {
	case RX_WAIT:
		put(line0, "Alarm %d/%d", rx.round + 1, RX_ROUNDS);
		put(line1, "Stand by...");
		leds[GL_SV_GREEN] = leds[GL_S_GREEN] = leds[GL_BO_GREEN] = 30;
		break;
	case RX_ALARM:
		put(line0, "ALARM! %c %c %c", t->arrow, t->arrow, t->arrow);
		put(line1, "%s", t->name);
		/* Flash the alarmed part at 8 Hz. */
		for (size_t i = 0; i < t->led_count; i++) {
			leds[t->leds[i]] = (now / 60) % 2 ? 100 : 0;
		}
		break;
	case RX_RESULT:
		put(line0, "%s", rx.verdict ? rx.verdict : "Acknowledged");
		put(line1, "%u ms", (unsigned int)rx.last_ms);
		break;
	}
	leds_show();

	return false;
}

static uint32_t rx_score(void)
{
	return rx.total_ms / RX_ROUNDS;
}

static void fmt_ms(uint32_t score, char *buf, size_t len)
{
	snprintf(buf, len, "%ums", (unsigned int)score);
}

static const char *rx_over_text(void)
{
	return "Average";
}

static const struct game games[GAME_COUNT] = {
	[GAME_PRESSURE] = { "Pressure Keeper", PERSIST_ID_BEST_PRESSURE, false, false,
			    pk_start, pk_key, pk_step, pk_score, fmt_seconds, pk_over_text },
	[GAME_RUNNER] = { "Pipe Runner", PERSIST_ID_BEST_RUNNER, false, false,
			  run_start, run_key, run_step, run_score, fmt_points, run_over_text },
	[GAME_REFLEX] = { "Alarm Reflex", PERSIST_ID_BEST_REFLEX, true, true,
			  rx_start, rx_key, rx_step, rx_score, fmt_ms, rx_over_text },
};

void games_init(void)
{
	for (int i = 0; i < GAME_COUNT; i++) {
		uint32_t value;

		if (persist_read(games[i].persist_id, &value, sizeof(value)) == sizeof(value)) {
			best[i] = value;
		}
	}
}

void games_open(struct lcd_hd44780 *lcd)
{
	panel = lcd;
	mode = MODE_MENU;
	/* Seed from the moment the player opened the menu: differs every time. */
	rng_state = k_cycle_get_32() | 1;
}

bool games_active(void)
{
	return mode != MODE_OFF;
}

static void start_selected(int64_t now)
{
	new_best = false;
	mode = MODE_PLAY;
	games[selected].start(now);
	LOG_INF("%s started", games[selected].name);
}

void games_key(enum ui_key key)
{
	int64_t now = k_uptime_get();

	switch (mode) {
	case MODE_MENU:
		if (key == UI_KEY_UP) {
			selected = (enum game_id)((selected + GAME_COUNT - 1) % GAME_COUNT);
		} else if (key == UI_KEY_DOWN) {
			selected = (enum game_id)((selected + 1) % GAME_COUNT);
		} else if (key == UI_KEY_CENTRE || key == UI_KEY_RIGHT) {
			start_selected(now);
		} else {
			mode = MODE_OFF;
			game_leds_release();
		}
		break;
	case MODE_PLAY:
		if (key == UI_KEY_LEFT && !games[selected].uses_left) {
			mode = MODE_MENU;	/* give up */
		} else {
			games[selected].key(key, now);
		}
		break;
	case MODE_OVER:
		if (now - over_since < OVER_HOLD_MS) {
			break;
		}
		if (key == UI_KEY_CENTRE) {
			start_selected(now);
		} else if (key == UI_KEY_LEFT) {
			mode = MODE_MENU;
		}
		break;
	case MODE_OFF:
		break;
	}
}

static void game_over(int64_t now)
{
	const struct game *g = &games[selected];
	uint32_t score = g->score();
	bool better = g->lower_is_better ? score < best[selected] : score > best[selected];

	mode = MODE_OVER;
	over_since = now;

	/* A reflex score of 0 ms cannot happen; 0 is "no best yet" for every game. */
	if (score > 0 && (best[selected] == 0 || better)) {
		best[selected] = score;
		new_best = true;
		persist_write(g->persist_id, &score, sizeof(score));
	}
	LOG_INF("%s over, score %u%s", g->name, (unsigned int)score, new_best ? ", new best" : "");
}

void games_render(char *line0, char *line1)
{
	const struct game *g = &games[selected];
	int64_t now = k_uptime_get();
	char score[8];
	char top[8];

	line0[0] = '\0';
	line1[0] = '\0';

	switch (mode) {
	case MODE_MENU:
		put(line0, "%c%s", ROM_RIGHT, g->name);
		if (best[selected] > 0) {
			g->format(best[selected], top, sizeof(top));
		} else {
			snprintf(top, sizeof(top), "-");
		}
		put(line1, "Best %-6.6sOK:go", top);
		leds_clear();
		leds_show();
		break;
	case MODE_PLAY:
		if (g->step(now, line0, line1)) {
			game_over(now);
		}
		break;
	case MODE_OVER:
		g->format(g->score(), score, sizeof(score));
		g->format(best[selected], top, sizeof(top));
		put(line0, "%-10.10s%6s", g->over_text(), score);
		if (new_best) {
			put(line1, "NEW BEST! OK:new");
		} else {
			put(line1, "Best %-6.6sOK:go", top);
		}
		break;
	case MODE_OFF:
		break;
	}

	pad(line0);
	pad(line1);
}
