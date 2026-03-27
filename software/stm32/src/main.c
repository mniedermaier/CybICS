/*
 * Copyright (c) 2024 CybICS
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/uart.h>
#include <zephyr/drivers/i2c.h>
#include <zephyr/logging/log.h>
#include <errno.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include "lcd_hd44780.h"
#include "version.h"
#include <pb_encode.h>
#include <pb_decode.h>
#include "proto/cybics.pb.h"

/* Register logging module */
LOG_MODULE_REGISTER(cybics, LOG_LEVEL_INF);

/* Menu options */
#define LOGIN_PASSWORD "cyb"
#define MENU_STATUS '1'
#define MENU_FLAG '2'
#define MENU_CONTROLS '3'
#define MENU_FREERTOS '4'
#define MENU_MCU '5'
#define MENU_HELP '6'
#define MENU_LOGOUT '7'

/* Thread stack sizes - increased for Newlib printf which is stack-heavy */
#define STACKSIZE_DEFAULT 1024
#define STACKSIZE_HEARTBEAT 1024
#define STACKSIZE_DISPLAY 2048
#define STACKSIZE_PHYSICAL 2048
#define STACKSIZE_I2C 1024
#define STACKSIZE_OUTPUT 1024
#define STACKSIZE_UART 2048

/* Thread priorities (Zephyr uses lower number = higher priority, opposite of FreeRTOS) */
#define PRIORITY_DEFAULT 7      // Normal
#define PRIORITY_HEARTBEAT 14   // Idle (lowest)
#define PRIORITY_DISPLAY 7      // Normal
#define PRIORITY_PHYSICAL 5     // Above normal
#define PRIORITY_I2C 7          // Normal
#define PRIORITY_OUTPUT 0       // Realtime (highest)
#define PRIORITY_UART 10        // Low

/* Global variables */
uint8_t RxData[20] = {0};
uint8_t TxData[cybics_PressureData_size] = {0};  /* Serialized PressureData protobuf */
uint8_t TxDataUID[14] = {0};  /* 12 hex chars + mode flag + null */
char rpiIP[15] = {'U','N','K','N','O','W','N',0,0,0,0,0,0,0,0};
uint8_t GSTpressure = 0;
uint8_t HPTpressure = 0;

uint8_t C_on = 0;
uint8_t C_off = 0;
uint8_t S_green = 0;
uint8_t S_red = 0;
uint8_t S_sen = 0;
uint8_t SV_green = 0;
uint8_t SV_red = 0;
uint8_t BO_red = 0;
uint8_t BO_green = 0;
uint8_t BO_sen = 0;
uint8_t GST_full = 0;
uint8_t GST_normal = 0;
uint8_t GST_low = 0;
uint8_t HPT_critical = 0;
uint8_t HPT_high = 0;
uint8_t HPT_normal = 0;
uint8_t HPT_low = 0;
uint8_t HPT_empty = 0;

/* Device handles */
static const struct device *uart_dev;
static const struct device *i2c_dev;

/* I2C slave configuration */
#define I2C_SLAVE_ADDRESS 0x20

/* I2C slave state */
static uint8_t i2c_rx_index = 0;
static uint8_t i2c_tx_index = 0;
static volatile bool i2c_first_message_received = false;

/* I2C slave callbacks */
static int i2c_write_requested(struct i2c_target_config *config)
{
	i2c_rx_index = 0;
	return 0;
}

static int i2c_write_received(struct i2c_target_config *config, uint8_t val)
{
	/*
	 * Store all received bytes in RxData (matching FreeRTOS behavior).
	 * For read_i2c_block_data(addr, reg, len): first byte is register
	 * For write_i2c_block_data(addr, reg, data): first byte is register, rest is data
	 *
	 * RxData layout after write_i2c_block_data(0x20, 0x00, ['I','P',':'] + IP):
	 *   RxData[0] = 0x00 (register)
	 *   RxData[1] = 'I'
	 *   RxData[2] = 'P'
	 *   RxData[3] = ':'
	 *   RxData[4...] = IP address
	 */
	if (i2c_rx_index < sizeof(RxData)) {
		RxData[i2c_rx_index] = val;
	}
	i2c_rx_index++;
	return 0;
}

static volatile uint8_t i2c_debug_reg = 0xFF;

static int i2c_read_requested(struct i2c_target_config *config, uint8_t *val)
{
	/*
	 * For read_i2c_block_data(addr, reg, len), the master first writes
	 * the register byte, then issues a repeated start to read.
	 * RxData[0] contains the register address from the write phase.
	 */
	i2c_tx_index = 0;
	i2c_debug_reg = RxData[0];

	if (RxData[0] == 0x00) {
		/* Register 0x00: TxData (GST/HPT pressure values) */
		*val = TxData[i2c_tx_index++];
	} else if (RxData[0] == 0x01) {
		/* Register 0x01: TxDataUID (STM32 UID + mode flag, 13 bytes) */
		*val = TxDataUID[i2c_tx_index++];
	} else {
		*val = 0;
	}
	return 0;
}

static int i2c_read_processed(struct i2c_target_config *config, uint8_t *val)
{
	if (RxData[0] == 0x00) {
		if (i2c_tx_index < sizeof(TxData)) {
			*val = TxData[i2c_tx_index++];
		} else {
			*val = 0;
		}
	} else if (RxData[0] == 0x01) {
		/* Send 13 bytes: 12 hex chars + mode flag (not the null terminator) */
		if (i2c_tx_index < 13) {
			*val = TxDataUID[i2c_tx_index++];
		} else {
			*val = 0;
		}
	} else {
		*val = 0;
	}
	return 0;
}

static int i2c_stop(struct i2c_target_config *config)
{
	/* Mark that we've received our first I2C message */
	if (i2c_rx_index > 0) {
		i2c_first_message_received = true;
	}
	/* Reset indices for next transaction */
	i2c_rx_index = 0;
	i2c_tx_index = 0;
	return 0;
}

static const struct i2c_target_callbacks i2c_callbacks = {
	.write_requested = i2c_write_requested,
	.write_received = i2c_write_received,
	.read_requested = i2c_read_requested,
	.read_processed = i2c_read_processed,
	.stop = i2c_stop,
};

static struct i2c_target_config i2c_target_cfg = {
	.address = I2C_SLAVE_ADDRESS,
	.callbacks = &i2c_callbacks,
};

/* Semaphore to signal initialization is complete */
K_SEM_DEFINE(init_sem, 0, 1);

/* GPIO device tree specifications */
static const struct gpio_dt_spec heartbeat_led = GPIO_DT_SPEC_GET(DT_NODELABEL(heartbeat_led), gpios);
static const struct gpio_dt_spec c_sig = GPIO_DT_SPEC_GET(DT_NODELABEL(c_sig), gpios);
static const struct gpio_dt_spec c_on_led = GPIO_DT_SPEC_GET(DT_NODELABEL(c_on), gpios);
static const struct gpio_dt_spec c_off_led = GPIO_DT_SPEC_GET(DT_NODELABEL(c_off), gpios);
static const struct gpio_dt_spec sv_sig = GPIO_DT_SPEC_GET(DT_NODELABEL(sv_sig), gpios);
static const struct gpio_dt_spec sv_red_led = GPIO_DT_SPEC_GET(DT_NODELABEL(sv_red), gpios);
static const struct gpio_dt_spec sv_green_led = GPIO_DT_SPEC_GET(DT_NODELABEL(sv_green), gpios);
static const struct gpio_dt_spec s_sen_pin = GPIO_DT_SPEC_GET(DT_NODELABEL(s_sen), gpios);
static const struct gpio_dt_spec s_red_led = GPIO_DT_SPEC_GET(DT_NODELABEL(s_red), gpios);
static const struct gpio_dt_spec s_green_led = GPIO_DT_SPEC_GET(DT_NODELABEL(s_green), gpios);
static const struct gpio_dt_spec bo_sen_pin = GPIO_DT_SPEC_GET(DT_NODELABEL(bo_sen), gpios);
static const struct gpio_dt_spec bo_red_led = GPIO_DT_SPEC_GET(DT_NODELABEL(bo_red), gpios);
static const struct gpio_dt_spec bo_green_led = GPIO_DT_SPEC_GET(DT_NODELABEL(bo_green), gpios);
static const struct gpio_dt_spec gst_sig = GPIO_DT_SPEC_GET(DT_NODELABEL(gst_sig), gpios);
static const struct gpio_dt_spec gst_low_led = GPIO_DT_SPEC_GET(DT_NODELABEL(gst_low), gpios);
static const struct gpio_dt_spec gst_normal_led = GPIO_DT_SPEC_GET(DT_NODELABEL(gst_normal), gpios);
static const struct gpio_dt_spec gst_full_led = GPIO_DT_SPEC_GET(DT_NODELABEL(gst_full), gpios);
static const struct gpio_dt_spec hpt_empty_led = GPIO_DT_SPEC_GET(DT_NODELABEL(hpt_empty), gpios);
static const struct gpio_dt_spec hpt_low_led = GPIO_DT_SPEC_GET(DT_NODELABEL(hpt_low), gpios);
static const struct gpio_dt_spec hpt_normal_led = GPIO_DT_SPEC_GET(DT_NODELABEL(hpt_normal), gpios);
static const struct gpio_dt_spec hpt_high_led = GPIO_DT_SPEC_GET(DT_NODELABEL(hpt_high), gpios);
static const struct gpio_dt_spec hpt_critical_led = GPIO_DT_SPEC_GET(DT_NODELABEL(hpt_critical), gpios);
static const struct gpio_dt_spec d_enable = GPIO_DT_SPEC_GET(DT_NODELABEL(d_enable), gpios);
static const struct gpio_dt_spec d_rs = GPIO_DT_SPEC_GET(DT_NODELABEL(d_rs), gpios);
static const struct gpio_dt_spec d_d4 = GPIO_DT_SPEC_GET(DT_NODELABEL(d_d4), gpios);
static const struct gpio_dt_spec d_d5 = GPIO_DT_SPEC_GET(DT_NODELABEL(d_d5), gpios);
static const struct gpio_dt_spec d_d6 = GPIO_DT_SPEC_GET(DT_NODELABEL(d_d6), gpios);
static const struct gpio_dt_spec d_d7 = GPIO_DT_SPEC_GET(DT_NODELABEL(d_d7), gpios);
static const struct gpio_dt_spec display_in = GPIO_DT_SPEC_GET(DT_NODELABEL(display_in), gpios);
static const struct gpio_dt_spec button = GPIO_DT_SPEC_GET(DT_NODELABEL(button), gpios);


/* Thread: Default Task */
void thread_default(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	while (1) {
		k_msleep(1);
	}
}

/* Thread: Heartbeat */
void thread_heartbeat(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	/* Wait for initialization to complete */
	k_sem_take(&init_sem, K_FOREVER);
	k_sem_give(&init_sem);

	LOG_INF("Starting thread_heartbeat");

	while (1) {
		gpio_pin_toggle_dt(&heartbeat_led);
		k_msleep(1000);
	}
}

/* Custom characters for startup animation */
static const uint8_t char_logo_tl[8] = {0x00, 0x00, 0x00, 0x01, 0x03, 0x07, 0x0F, 0x0F};  /* Top-left corner */
static const uint8_t char_logo_tr[8] = {0x00, 0x00, 0x00, 0x10, 0x18, 0x1C, 0x1E, 0x1E};  /* Top-right corner */
static const uint8_t char_logo_bl[8] = {0x0F, 0x0F, 0x07, 0x03, 0x01, 0x00, 0x00, 0x00};  /* Bottom-left corner */
static const uint8_t char_logo_br[8] = {0x1E, 0x1E, 0x1C, 0x18, 0x10, 0x00, 0x00, 0x00};  /* Bottom-right corner */
static const uint8_t char_block_full[8] = {0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F};  /* Full block */
static const uint8_t char_block_left[8] = {0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x10};  /* Left edge */
static const uint8_t char_block_right[8] = {0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01}; /* Right edge */
static const uint8_t char_gear[8] = {0x00, 0x0E, 0x11, 0x0E, 0x0E, 0x11, 0x0E, 0x00};  /* Gear/cog */

/**
 * @brief Play startup animation on LCD for ~10 seconds
 */
static void play_startup_animation(struct lcd_hd44780 *lcd)
{
	int i;

	/* Create custom characters */
	lcd_create_char(lcd, 0, char_logo_tl);
	lcd_create_char(lcd, 1, char_logo_tr);
	lcd_create_char(lcd, 2, char_logo_bl);
	lcd_create_char(lcd, 3, char_logo_br);
	lcd_create_char(lcd, 4, char_block_full);
	lcd_create_char(lcd, 5, char_block_left);
	lcd_create_char(lcd, 6, char_block_right);
	lcd_create_char(lcd, 7, char_gear);

	/* Phase 1: Animated logo sequence (~5 seconds) */
	lcd_clear(lcd);
	k_msleep(300);

	/* Sweep effect: lines coming from both sides */
	for (i = 0; i < 8; i++) {
		lcd_set_cursor(lcd, 0, i);
		lcd_putc(lcd, '=');
		lcd_set_cursor(lcd, 0, 15 - i);
		lcd_putc(lcd, '=');
		lcd_set_cursor(lcd, 1, i);
		lcd_putc(lcd, '=');
		lcd_set_cursor(lcd, 1, 15 - i);
		lcd_putc(lcd, '=');
		k_msleep(80);
	}
	k_msleep(200);

	/* Clear with fade effect */
	for (i = 0; i < 8; i++) {
		lcd_set_cursor(lcd, 0, i);
		lcd_putc(lcd, ' ');
		lcd_set_cursor(lcd, 0, 15 - i);
		lcd_putc(lcd, ' ');
		lcd_set_cursor(lcd, 1, i);
		lcd_putc(lcd, ' ');
		lcd_set_cursor(lcd, 1, 15 - i);
		lcd_putc(lcd, ' ');
		k_msleep(50);
	}
	k_msleep(200);

	/* Draw expanding box */
	lcd_set_cursor(lcd, 0, 7);
	lcd_putc(lcd, 0);  /* Top-left */
	lcd_putc(lcd, 1);  /* Top-right */
	lcd_set_cursor(lcd, 1, 7);
	lcd_putc(lcd, 2);  /* Bottom-left */
	lcd_putc(lcd, 3);  /* Bottom-right */
	k_msleep(400);

	/* Add horizontal lines expanding from center */
	for (i = 1; i <= 5; i++) {
		lcd_set_cursor(lcd, 0, 7 - i);
		lcd_putc(lcd, '-');
		lcd_set_cursor(lcd, 0, 8 + i);
		lcd_putc(lcd, '-');
		lcd_set_cursor(lcd, 1, 7 - i);
		lcd_putc(lcd, '-');
		lcd_set_cursor(lcd, 1, 8 + i);
		lcd_putc(lcd, '-');
		k_msleep(100);
	}
	k_msleep(300);

	/* Add gear icons with animation */
	lcd_set_cursor(lcd, 0, 1);
	lcd_putc(lcd, 7);
	k_msleep(150);
	lcd_set_cursor(lcd, 0, 14);
	lcd_putc(lcd, 7);
	k_msleep(150);
	lcd_set_cursor(lcd, 1, 1);
	lcd_putc(lcd, 7);
	k_msleep(150);
	lcd_set_cursor(lcd, 1, 14);
	lcd_putc(lcd, 7);
	k_msleep(400);

	/* Spinning effect on gears */
	for (i = 0; i < 4; i++) {
		lcd_set_cursor(lcd, 0, 1);
		lcd_putc(lcd, (i % 2) ? 7 : '*');
		lcd_set_cursor(lcd, 0, 14);
		lcd_putc(lcd, (i % 2) ? '*' : 7);
		lcd_set_cursor(lcd, 1, 1);
		lcd_putc(lcd, (i % 2) ? '*' : 7);
		lcd_set_cursor(lcd, 1, 14);
		lcd_putc(lcd, (i % 2) ? 7 : '*');
		k_msleep(200);
	}
	k_msleep(300);

	/* Phase 2: Typewriter effect for "CybICS" */
	lcd_clear(lcd);
	k_msleep(200);
	lcd_set_cursor(lcd, 0, 5);
	const char *logo = "CybICS";
	for (i = 0; logo[i] != '\0'; i++) {
		lcd_putc(lcd, logo[i]);
		k_msleep(200);
	}
	k_msleep(800);

	/* Phase 3: Loading bar animation - loops until I2C message received */
	lcd_clear(lcd);
	lcd_set_cursor(lcd, 0, 1);
	lcd_print(lcd, "Waiting for Pi");

	/* Draw loading bar frame */
	lcd_set_cursor(lcd, 1, 0);
	lcd_print(lcd, "[              ]");

	/* Animate loading bar until I2C message is received */
	i = 0;
	while (!i2c_first_message_received) {
		/* Calculate position in the bar (ping-pong effect) */
		int pos = i % 28;  /* 0-27 for back and forth */
		if (pos >= 14) {
			pos = 27 - pos;  /* Reverse direction */
		}

		/* Clear the bar */
		lcd_set_cursor(lcd, 1, 1);
		lcd_print(lcd, "              ");

		/* Draw moving segment (3 chars wide) */
		for (int j = 0; j < 3; j++) {
			int p = pos + j;
			if (p >= 0 && p < 14) {
				lcd_set_cursor(lcd, 1, 1 + p);
				lcd_putc(lcd, '=');
			}
		}

		/* Animate dots on top line */
		lcd_set_cursor(lcd, 0, 15);
		lcd_putc(lcd, "\\|/-"[i % 4]);  /* Spinning indicator */

		i++;
		k_msleep(100);
	}

	/* Show connected message briefly */
	lcd_clear(lcd);
	lcd_set_cursor(lcd, 0, 2);
	lcd_print(lcd, "Pi Connected!");
	lcd_set_cursor(lcd, 1, 0);
	lcd_print(lcd, "[==============]");
	k_msleep(800);

	/* Phase 4: System ready with flash effect */
	for (int flash = 0; flash < 3; flash++) {
		lcd_clear(lcd);
		k_msleep(100);
		lcd_set_cursor(lcd, 0, 2);
		lcd_print(lcd, "** READY **");
		lcd_set_cursor(lcd, 1, 5);
		lcd_print(lcd, "CybICS");
		k_msleep(300);
	}

	/* Hold ready message */
	k_msleep(500);
	lcd_clear(lcd);
}

/* Thread: Display */
void thread_display(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	uint8_t shifting = 0;
	uint8_t displayScreen = 0;
	uint32_t secondsAfterStart = 0;
	uint8_t wifiPressed = 0;
	char displayText[20];
	int ret;

	/* Wait for initialization to complete */
	k_sem_take(&init_sem, K_FOREVER);
	k_sem_give(&init_sem);

	LOG_INF("Display thread: initializing LCD...");

	/* Setup LCD with new Zephyr driver */
	struct lcd_hd44780 lcd = {
		.rs = &d_rs,
		.en = &d_enable,
		.d4 = &d_d4,
		.d5 = &d_d5,
		.d6 = &d_d6,
		.d7 = &d_d7,
	};

	ret = lcd_init(&lcd);
	if (ret < 0) {
		LOG_ERR("Display thread: LCD init FAILED!");
		return;
	}

	LOG_INF("Display thread: LCD initialized OK");

	/* Play startup animation (~10 seconds) */
	LOG_INF("Display thread: playing startup animation");
	play_startup_animation(&lcd);
	LOG_INF("Display thread: startup animation complete");

	/* Get unique ID from STM32 UID registers (same as LL_GetUID_Word0/1/2) */
	volatile uint32_t *uid = (volatile uint32_t *)0x1FFF7590;
	/*
	 * IMPORTANT: Use lower 16 bits only to ensure exactly 12 hex chars.
	 * %04lx means "minimum 4 digits" not "maximum 4 digits", so unmasked
	 * 32-bit values would overflow the buffer and corrupt the mode flag.
	 */
	snprintf((char*)TxDataUID, sizeof(TxDataUID), "%04lx%04lx%04lx",
		(unsigned long)(uid[0] & 0xFFFF),
		(unsigned long)(uid[1] & 0xFFFF),
		(unsigned long)(uid[2] & 0xFFFF));
	TxDataUID[12] = '0'; /* default STA mode */

	/* Debug: print UID (full values and truncated for SSID) */
	LOG_INF("STM32 UID: %08lx %08lx %08lx -> SSID: %s",
		(unsigned long)uid[0], (unsigned long)uid[1], (unsigned long)uid[2], TxDataUID);

	LOG_INF("Display thread: starting main loop");

	while (1) {
		/* Switch between station and AP mode of Wifi */
		if (gpio_pin_get_dt(&button)) {
			if (!wifiPressed) {
				if (TxDataUID[12] == '0') {
					TxDataUID[12] = '1';
					LOG_INF("WiFi: STA -> AP");
				} else {
					TxDataUID[12] = '0';
					LOG_INF("WiFi: AP -> STA");
				}
				snprintf(rpiIP, sizeof(rpiIP), "%-14s", "Unknown");
				shifting = 0;
				wifiPressed = 1;
			}
		} else {
			wifiPressed = 0;
		}

		/* Switch between displays if Display button is pressed */
		if (gpio_pin_get_dt(&display_in)) {
			displayScreen++;
			if (displayScreen > 4) {
				displayScreen = 0;
			}
		}

		secondsAfterStart++;

		/* Display showing CybICS string and uptime */
		if (displayScreen == 0) {
			snprintf(displayText, sizeof(displayText), "CybICS %-9s", FIRMWARE_VERSION_STRING);
			lcd_set_cursor(&lcd, 0, 0);
			lcd_print(&lcd, displayText);
			snprintf(displayText, sizeof(displayText), "%16u", secondsAfterStart);
			lcd_set_cursor(&lcd, 1, 0);
			lcd_print(&lcd, displayText);
		}
		/* Display WiFi configuration */
		else if (displayScreen == 1) {
			if (TxDataUID[12] == '0') {
				snprintf(displayText, sizeof(displayText), "%-16s", "Wifi STA mode");
				lcd_set_cursor(&lcd, 0, 0);
				lcd_print(&lcd, displayText);
				snprintf(displayText, sizeof(displayText), "IP: %-12s", &rpiIP[shifting]);
				lcd_set_cursor(&lcd, 1, 0);
				lcd_print(&lcd, displayText);

				if (strlen(rpiIP) > 12) {
					shifting++;
				}
				if (shifting > 3) {
					shifting = 0;
				}
			} else if (TxDataUID[12] == '1') {
				snprintf(displayText, sizeof(displayText), "%-16s", "AP mode: cybics-");
				lcd_set_cursor(&lcd, 0, 0);
				lcd_print(&lcd, displayText);
				snprintf(displayText, sizeof(displayText), "%-16s", TxDataUID);
				displayText[12] = ' '; /* removing the 1, which is not part of the UID */
				lcd_set_cursor(&lcd, 1, 0);
				lcd_print(&lcd, displayText);
			} else {
				snprintf(displayText, sizeof(displayText), "%-16s", "WiFi error");
				lcd_set_cursor(&lcd, 0, 0);
				lcd_print(&lcd, displayText);
			}
		}
		/* Display showing real pressure values */
		else if (displayScreen == 2) {
			snprintf(displayText, sizeof(displayText), "%-16s", "Physical/real:  ");
			lcd_set_cursor(&lcd, 0, 0);
			lcd_print(&lcd, displayText);
			snprintf(displayText, sizeof(displayText), "GST:%03d HPT:%03d ", GSTpressure, HPTpressure);
			lcd_set_cursor(&lcd, 1, 0);
			lcd_print(&lcd, displayText);
		}
		/* Display showing status */
		else if (displayScreen == 3) {
			snprintf(displayText, sizeof(displayText), "%-16s", "Status:");
			lcd_set_cursor(&lcd, 0, 0);
			lcd_print(&lcd, displayText);
			if (BO_sen > 0) {
				snprintf(displayText, sizeof(displayText), "%-16s", "Danger! BlowOut");
			} else if ((HPTpressure > 50) && (HPTpressure < 100) && SV_green) {
				snprintf(displayText, sizeof(displayText), "%-16s", "Operational");
			} else if ((HPTpressure > 50) && (HPTpressure < 100)) {
				snprintf(displayText, sizeof(displayText), "%-16s", "SV closed");
			} else if (HPTpressure > 100) {
				snprintf(displayText, sizeof(displayText), "%-16s", "Pressure too high");
			} else if (HPTpressure <= 50) {
				snprintf(displayText, sizeof(displayText), "%-16s", "Pressure too low");
			}
			lcd_set_cursor(&lcd, 1, 0);
			lcd_print(&lcd, displayText);
		}
		/* Display showing build information */
		else if (displayScreen == 4) {
			/* BUILD_DATE and BUILD_TIME are defined by CMake */
			snprintf(displayText, sizeof(displayText), "Build %s", BUILD_DATE);
			lcd_set_cursor(&lcd, 0, 0);
			lcd_print(&lcd, displayText);
			snprintf(displayText, sizeof(displayText), "%-16s", BUILD_TIME);
			lcd_set_cursor(&lcd, 1, 0);
			lcd_print(&lcd, displayText);
		}

		k_msleep(1000);
	}
}

/* Thread: Physical simulation */
void thread_physical(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	uint8_t HPTuse = 0;

	/* Wait for initialization to complete */
	k_sem_take(&init_sem, K_FOREVER);
	k_sem_give(&init_sem);

	LOG_INF("Starting thread_physical");

	int cState, svState, gstState;
	uint16_t HPTdelay = 0;
	uint16_t GSTdelay = 0;
	uint16_t BOdelay = 0;

	while (1) {
		cState = gpio_pin_get_dt(&c_sig);
		svState = gpio_pin_get_dt(&sv_sig);
		gstState = gpio_pin_get_dt(&gst_sig);

		/* When compressor is running */
		if(cState) {
			C_on = 1;
			C_off = 0;
			if(HPTdelay > 100) {
				if(HPTpressure < 255) {
					if(GSTpressure >= 50) {
						GSTpressure = GSTpressure - 2;
						HPTpressure++;
					}
				}
				HPTdelay = 0;
			}
		} else {
			C_on = 0;
			C_off = 1;
			if(HPTdelay > 100) {
				HPTuse = rand() % 3;
				if(((HPTpressure - HPTuse) >= 0) & svState) {
					HPTpressure = HPTpressure - HPTuse;
				}
				HPTdelay = 0;
			}
		}

		if(GSTdelay > 100) {
			if((GSTpressure < 251) & (gstState)) {
				GSTpressure = GSTpressure + (rand() % 4);
			}
			GSTdelay = 0;
		}

		if(svState) {
			SV_green = 1;
			SV_red = 0;
		} else {
			SV_green = 0;
			SV_red = 1;
		}

		/* HPT Pressure levels */
		if(HPTpressure < 1) {
			HPT_critical = 0; HPT_high = 0; HPT_normal = 0; HPT_low = 0; HPT_empty = 1;
		} else if(HPTpressure < 50) {
			HPT_critical = 0; HPT_high = 0; HPT_normal = 0; HPT_low = 1; HPT_empty = 0;
		} else if(HPTpressure < 100) {
			HPT_critical = 0; HPT_high = 0; HPT_normal = 1; HPT_low = 0; HPT_empty = 0;
		} else if(HPTpressure < 150) {
			HPT_critical = 0; HPT_high = 1; HPT_normal = 0; HPT_low = 0; HPT_empty = 0;
		} else {
			HPT_critical = 1; HPT_high = 0; HPT_normal = 0; HPT_low = 0; HPT_empty = 0;
		}

		/* Blowout if the HPTpressure if over 220 */
		if((HPTpressure > 220) || ((HPTpressure > 200) & (BO_sen > 0))) {
			BO_red = 1;
			BO_green = 0;
			BO_sen = 1;
			if(BOdelay > 100) {
				HPTuse = rand() % 2;
				if((HPTpressure - HPTuse) >= 0) {
					HPTpressure = HPTpressure - HPTuse;
				}
				BOdelay = 0;
			}
		} else {
			BO_red = 0;
			BO_green = 1;
			BO_sen = 0;
		}

		/* System operating */
		if((HPTpressure > 50) && (HPTpressure < 100) && svState) {
			S_red = 0;
			S_green = 1;
			S_sen = 1;
		} else {
			S_red = 1;
			S_green = 0;
			S_sen = 0;
		}

		/* Gas Storage Tank */
		if(GSTpressure < 50) {
			GST_low = 1; GST_normal = 0; GST_full = 0;
		} else if(GSTpressure < 150) {
			GST_low = 0; GST_normal = 1; GST_full = 0;
		} else {
			GST_low = 0; GST_normal = 0; GST_full = 1;
		}

		/* Initialize protobuf pressure data and serialize to TxData */
		cybics_PressureData cybics_pressure_data = cybics_PressureData_init_default;
		cybics_pressure_data.gst_pressure = GSTpressure;
		cybics_pressure_data.hpt_pressure = HPTpressure;
		pb_ostream_t stream = pb_ostream_from_buffer(TxData, sizeof(TxData));
		if (!pb_encode(&stream, cybics_PressureData_fields, &cybics_pressure_data)) {
			LOG_ERR("Failed to serialize pressure data");
		}

		HPTdelay++;
		GSTdelay++;
		BOdelay++;
		k_msleep(10);
	}
}

/* Thread: I2C handler */
void thread_i2c(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	/* Wait for initialization to complete */
	k_sem_take(&init_sem, K_FOREVER);
	k_sem_give(&init_sem);

	LOG_INF("Starting thread_i2c");

	while (1) {
		if(RxData[1] == 'I' && RxData[2] == 'P') {
			for(uint8_t counter = 0; counter < sizeof(rpiIP); counter++) {
				rpiIP[counter] = RxData[counter + 4];
			}
		}
		k_msleep(100);
	}
}

/* Thread: Write Output (LED control with PWM) */
void thread_write_output(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	/* Wait for initialization to complete */
	k_sem_take(&init_sem, K_FOREVER);
	k_sem_give(&init_sem);

	LOG_INF("Starting thread_write_output");

	while (1) {
		// Clear (turn off) most LEDs
		gpio_pin_set_dt(&gst_full_led, 1);
		gpio_pin_set_dt(&gst_low_led, 1);
		gpio_pin_set_dt(&c_off_led, 1);
		gpio_pin_set_dt(&hpt_critical_led, 1);
		gpio_pin_set_dt(&hpt_high_led, 1);
		gpio_pin_set_dt(&hpt_low_led, 1);
		gpio_pin_set_dt(&hpt_empty_led, 1);
		gpio_pin_set_dt(&bo_red_led, 1);
		gpio_pin_set_dt(&sv_red_led, 1);
		gpio_pin_set_dt(&s_red_led, 1);

		k_msleep(14);

		// Update outputs based on state variables
		gpio_pin_set_dt(&c_on_led, C_on ? 0 : 1);
		gpio_pin_set_dt(&c_off_led, C_off ? 0 : 1);
		gpio_pin_set_dt(&sv_red_led, SV_red ? 0 : 1);
		gpio_pin_set_dt(&sv_green_led, SV_green ? 0 : 1);
		gpio_pin_set_dt(&gst_full_led, GST_full ? 0 : 1);
		gpio_pin_set_dt(&gst_normal_led, GST_normal ? 0 : 1);
		gpio_pin_set_dt(&gst_low_led, GST_low ? 0 : 1);
		gpio_pin_set_dt(&hpt_critical_led, HPT_critical ? 0 : 1);
		gpio_pin_set_dt(&hpt_high_led, HPT_high ? 0 : 1);
		gpio_pin_set_dt(&hpt_normal_led, HPT_normal ? 0 : 1);
		gpio_pin_set_dt(&hpt_low_led, HPT_low ? 0 : 1);
		gpio_pin_set_dt(&hpt_empty_led, HPT_empty ? 0 : 1);
		gpio_pin_set_dt(&s_red_led, S_red ? 0 : 1);
		gpio_pin_set_dt(&s_green_led, S_green ? 0 : 1);
		gpio_pin_set_dt(&s_sen_pin, S_sen ? 1 : 0); // Sensor outputs not inverted
		gpio_pin_set_dt(&bo_red_led, BO_red ? 0 : 1);
		gpio_pin_set_dt(&bo_green_led, BO_green ? 0 : 1);
		gpio_pin_set_dt(&bo_sen_pin, BO_sen ? 1 : 0); // Sensor outputs not inverted

		k_msleep(1);
	}
}

/* Thread: UART menu interface */
void thread_uart(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	char password[20];
	char input[2];
	uint8_t loggedIn = 0;
	uint8_t rxIndex = 0;
	uint8_t showMenu = 1;
	uint8_t passwordEntry = 0;

	/* Wait for initialization to complete */
	k_sem_take(&init_sem, K_FOREVER);
	k_sem_give(&init_sem);

	LOG_INF("Starting thread_uart");

	while (1) {
		if (!loggedIn) {
			if (!passwordEntry) {
				LOG_INF("Please enter password:");
				rxIndex = 0;
				memset(password, 0, sizeof(password));
				passwordEntry = 1;
			}

			// Non-blocking password input
			if (rxIndex < sizeof(password) - 1) {
				if (uart_poll_in(uart_dev, (unsigned char*)&password[rxIndex]) == 0) {
					uart_poll_out(uart_dev, password[rxIndex]);

					if (password[rxIndex] == '\r' || password[rxIndex] == '\n') {
						password[rxIndex] = '\0';
						if (strcmp(password, LOGIN_PASSWORD) == 0) {
							loggedIn = 1;
							LOG_INF("Login successful!");
							showMenu = 1;
						} else {
							LOG_ERR("Invalid password. Please try again.");
							passwordEntry = 0;
						}
					} else {
						rxIndex++;
					}
				}
			} else {
				LOG_ERR("Password too long. Please try again.");
				rxIndex = 0;
				memset(password, 0, sizeof(password));
				passwordEntry = 0;
			}
			k_msleep(10);
			continue;
		}

		if (showMenu) {
			LOG_INF("=== CybICS Menu ===");
			LOG_INF("1. System Status");
			LOG_INF("2. Display Flag");
			LOG_INF("3. System Controls");
			LOG_INF("4. Zephyr Stats");
			LOG_INF("5. MCU Information");
			LOG_INF("6. Help");
			LOG_INF("7. Logout");
			LOG_INF("Enter choice (1-7):");
			showMenu = 0;
		}

		if (uart_poll_in(uart_dev, (unsigned char*)input) == 0) {
			switch(input[0]) {
				case MENU_STATUS:
					LOG_INF("=== System Status ===");
					LOG_INF("GST Pressure: %d", GSTpressure);
					LOG_INF("HPT Pressure: %d", HPTpressure);
					LOG_INF("Compressor: %s", C_on ? "ON" : "OFF");
					LOG_INF("System Valve: %s", SV_green ? "OPEN" : "CLOSED");
					LOG_INF("System Status: %s", S_green ? "OPERATIONAL" : "NOT OPERATIONAL");
					LOG_INF("Blow Out: %s", BO_sen ? "ACTIVE" : "INACTIVE");
					showMenu = 1;
					break;

				case MENU_FLAG:
					LOG_INF("=== CybICS Flag ===");
					LOG_INF("CybICS(U#RT)");
					showMenu = 1;
					break;

				case MENU_CONTROLS:
					LOG_INF("=== System Controls ===");
					LOG_INF("Current Status:");
					LOG_INF("----------------");
					LOG_INF("Compressor: %s", C_on ? "Running" : "Stopped");
					LOG_INF("System Valve: %s", SV_green ? "Open" : "Closed");
					showMenu = 1;
					break;

				case MENU_FREERTOS:
					LOG_INF("=== Zephyr Statistics ===");
					LOG_INF("Thread Statistics:");
					LOG_INF("----------------");
					LOG_INF("System running on Zephyr RTOS");
					showMenu = 1;
					break;

				case MENU_MCU:
					LOG_INF("=== MCU Information ===");
					LOG_INF("STM32G070RB on Zephyr RTOS");
					showMenu = 1;
					break;

				case MENU_HELP:
					LOG_INF("=== Help ===");
					LOG_INF("1. System Status - Shows current system parameters");
					LOG_INF("2. Display Flag - Shows the CybICS flag");
					LOG_INF("3. System Controls - Shows control status");
					LOG_INF("4. Zephyr Stats - Shows Zephyr thread statistics");
					LOG_INF("5. MCU Information - Shows MCU info");
					LOG_INF("6. Help - Shows this help message");
					LOG_INF("7. Logout - Logs out of the system");
					showMenu = 1;
					break;

				case MENU_LOGOUT:
					loggedIn = 0;
					passwordEntry = 0;
					LOG_INF("Logged out successfully.");
					break;

				default:
					LOG_ERR("Invalid choice. Please try again.");
					showMenu = 1;
					break;
			}
		}

		k_msleep(10);
	}
}

/* Define threads */
K_THREAD_DEFINE(default_tid, STACKSIZE_DEFAULT, thread_default, NULL, NULL, NULL, PRIORITY_DEFAULT, 0, 0);
K_THREAD_DEFINE(heartbeat_tid, STACKSIZE_HEARTBEAT, thread_heartbeat, NULL, NULL, NULL, PRIORITY_HEARTBEAT, 0, 0);
K_THREAD_DEFINE(display_tid, STACKSIZE_DISPLAY, thread_display, NULL, NULL, NULL, PRIORITY_DISPLAY, 0, 0);
K_THREAD_DEFINE(physical_tid, STACKSIZE_PHYSICAL, thread_physical, NULL, NULL, NULL, PRIORITY_PHYSICAL, 0, 0);
K_THREAD_DEFINE(i2c_tid, STACKSIZE_I2C, thread_i2c, NULL, NULL, NULL, PRIORITY_I2C, 0, 0);
K_THREAD_DEFINE(output_tid, STACKSIZE_OUTPUT, thread_write_output, NULL, NULL, NULL, PRIORITY_OUTPUT, 0, 0);
K_THREAD_DEFINE(uart_tid, STACKSIZE_UART, thread_uart, NULL, NULL, NULL, PRIORITY_UART, 0, 0);

/* Helper to configure GPIO with error checking */
static int configure_gpio_output(const struct gpio_dt_spec *spec, const char *name)
{
	if (!device_is_ready(spec->port)) {
		LOG_ERR("GPIO port not ready for %s", name);
		return -ENODEV;
	}
	int ret = gpio_pin_configure_dt(spec, GPIO_OUTPUT_INACTIVE);
	if (ret < 0) {
		LOG_ERR("Failed to configure %s: %d", name, ret);
		return ret;
	}
	return 0;
}

static int configure_gpio_input(const struct gpio_dt_spec *spec, const char *name)
{
	if (!device_is_ready(spec->port)) {
		LOG_ERR("GPIO port not ready for %s", name);
		return -ENODEV;
	}
	int ret = gpio_pin_configure_dt(spec, GPIO_INPUT);
	if (ret < 0) {
		LOG_ERR("Failed to configure %s: %d", name, ret);
		return ret;
	}
	return 0;
}

/* Main function */
int main(void)
{
	int errors = 0;

	/* Log firmware version */
	LOG_INF("Build: %s %s", BUILD_DATE, BUILD_TIME);

	/*
	 * CRITICAL: Disable UCPD dead battery pulldowns on PD0/PD2
	 * On STM32G0, PD0 and PD2 have internal pulldowns enabled after reset
	 * for USB Type-C Power Delivery. We must disable these to use the pins
	 * as regular GPIOs.
	 * SYSCFG_CFGR1: UCPD1_STROBE (bit 9), UCPD2_STROBE (bit 10)
	 */
	volatile uint32_t *syscfg_cfgr1 = (volatile uint32_t *)0x40010000;
	*syscfg_cfgr1 |= (1 << 9) | (1 << 10);  /* Set UCPD1_STROBE and UCPD2_STROBE */

	LOG_INF("========================================");
	LOG_INF("CybICS Zephyr Port Starting...");
	LOG_INF("========================================");

	/* Get UART device */
	uart_dev = DEVICE_DT_GET(DT_NODELABEL(usart1));
	if (!device_is_ready(uart_dev)) {
		LOG_ERR("UART1 device not ready");
		errors++;
	} else {
		LOG_INF("UART1 ready");
	}

	LOG_INF("Initializing I2C...");
	i2c_dev = DEVICE_DT_GET(DT_NODELABEL(i2c1));
	if (!device_is_ready(i2c_dev)) {
		LOG_ERR("I2C1 device not ready");
		errors++;
	} else {
		LOG_INF("I2C1 ready, registering as slave at 0x20...");
		int ret = i2c_target_register(i2c_dev, &i2c_target_cfg);
		if (ret < 0) {
			LOG_ERR("I2C target register failed: %d", ret);
			errors++;
		} else {
			LOG_INF("I2C slave registered OK");
		}
	}

	/* Configure GPIO pins as outputs with error checking */
	LOG_INF("Configuring GPIO outputs...");

	if (configure_gpio_output(&heartbeat_led, "heartbeat_led") < 0) errors++;
	if (configure_gpio_output(&c_on_led, "c_on_led") < 0) errors++;
	if (configure_gpio_output(&c_off_led, "c_off_led") < 0) errors++;
	if (configure_gpio_output(&sv_red_led, "sv_red_led") < 0) errors++;
	if (configure_gpio_output(&sv_green_led, "sv_green_led") < 0) errors++;
	if (configure_gpio_output(&s_sen_pin, "s_sen_pin") < 0) errors++;
	if (configure_gpio_output(&s_red_led, "s_red_led") < 0) errors++;
	if (configure_gpio_output(&s_green_led, "s_green_led") < 0) errors++;
	if (configure_gpio_output(&bo_sen_pin, "bo_sen_pin") < 0) errors++;
	if (configure_gpio_output(&bo_red_led, "bo_red_led") < 0) errors++;
	if (configure_gpio_output(&bo_green_led, "bo_green_led") < 0) errors++;
	if (configure_gpio_output(&gst_low_led, "gst_low_led") < 0) errors++;
	if (configure_gpio_output(&gst_normal_led, "gst_normal_led") < 0) errors++;
	if (configure_gpio_output(&gst_full_led, "gst_full_led") < 0) errors++;
	if (configure_gpio_output(&hpt_empty_led, "hpt_empty_led") < 0) errors++;
	if (configure_gpio_output(&hpt_low_led, "hpt_low_led") < 0) errors++;
	if (configure_gpio_output(&hpt_normal_led, "hpt_normal_led") < 0) errors++;
	if (configure_gpio_output(&hpt_high_led, "hpt_high_led") < 0) errors++;
	if (configure_gpio_output(&hpt_critical_led, "hpt_critical_led") < 0) errors++;
	if (configure_gpio_output(&d_enable, "d_enable") < 0) errors++;
	if (configure_gpio_output(&d_rs, "d_rs") < 0) errors++;
	if (configure_gpio_output(&d_d4, "d_d4") < 0) errors++;
	if (configure_gpio_output(&d_d5, "d_d5") < 0) errors++;
	if (configure_gpio_output(&d_d6, "d_d6") < 0) errors++;
	if (configure_gpio_output(&d_d7, "d_d7") < 0) errors++;

	/* Configure GPIO pins as inputs */
	LOG_INF("Configuring GPIO inputs...");
	if (configure_gpio_input(&c_sig, "c_sig") < 0) errors++;
	if (configure_gpio_input(&sv_sig, "sv_sig") < 0) errors++;
	if (configure_gpio_input(&gst_sig, "gst_sig") < 0) errors++;
	if (configure_gpio_input(&display_in, "display_in") < 0) errors++;
	if (configure_gpio_input(&button, "button") < 0) errors++;

	LOG_INF("========================================");
	if (errors > 0) {
		LOG_WRN("Initialization completed with %d errors", errors);
	} else {
		LOG_INF("CybICS initialization complete - no errors");
	}
	LOG_INF("========================================");

	/* Signal all threads that initialization is complete */
	/* Do this even if there are errors so threads don't deadlock */
	k_sem_give(&init_sem);

	LOG_INF("Threads starting...");

	/* Threads are auto-started by K_THREAD_DEFINE */
	return 0;
}
