/*
 * Copyright (c) 2024 CybICS
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/uart.h>
#include <zephyr/drivers/i2c.h>
#include <zephyr/sys/printk.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include "display.h"
#include "colors.h"

/* Logging */
#define LOG_ERR 0x03
#define LOG_WAR 0x02
#define LOG_INF 0x01
#define LOG_DEB 0x00
#define showLogLevel LOG_DEB

/* Menu options */
#define LOGIN_PASSWORD "cyb"
#define MENU_STATUS '1'
#define MENU_FLAG '2'
#define MENU_CONTROLS '3'
#define MENU_FREERTOS '4'
#define MENU_MCU '5'
#define MENU_HELP '6'
#define MENU_LOGOUT '7'

/* Thread stack sizes */
#define STACKSIZE_DEFAULT 512
#define STACKSIZE_HEARTBEAT 512
#define STACKSIZE_DISPLAY 1024
#define STACKSIZE_PHYSICAL 1024
#define STACKSIZE_I2C 512
#define STACKSIZE_OUTPUT 512
#define STACKSIZE_UART 1024

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
uint8_t TxData[20] = {'X','X','X',':',' ','0','0','0',' ','H','P','T',':',' ','0','0','0'};
uint8_t TxDataUID[13] = {0};
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

/* Mutex for UART */
K_MUTEX_DEFINE(uart_mutex);

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

/* Logging function */
void logging(unsigned char logLevel, const char *fmt, ...)
{
	if(showLogLevel <= logLevel) {
		if(logLevel == LOG_ERR) {
			printk("%sERR: %s%s\r\n", CRED, fmt, CRST);
		} else if(logLevel == LOG_WAR) {
			printk("%sWAR: %s%s\r\n", CYEL, fmt, CRST);
		} else if(logLevel == LOG_INF) {
			printk("%sINF: %s%s\r\n", CBLU, fmt, CRST);
		} else if(logLevel == LOG_DEB) {
			printk("%sDEB: %s%s\r\n", CMAG, fmt, CRST);
		} else {
			printk("%s???: %s%s\r\n", CRED, fmt, CRST);
		}
	}
}

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

	logging(LOG_DEB, "Starting thread_heartbeat");

	while (1) {
		gpio_pin_toggle_dt(&heartbeat_led);
		k_msleep(1000);
	}
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

	k_msleep(10);

	const struct gpio_dt_spec data_pins[] = {d_d4, d_d5, d_d6, d_d7};
	Lcd_HandleTypeDef lcd = Lcd_create(data_pins, &d_rs, &d_enable, LCD_4_BIT_MODE);

	logging(LOG_DEB, "Starting thread_display");

	// Get unique ID - for Zephyr on STM32, we'd need to use device-specific registers
	// For now, use a placeholder
	snprintf((char*)TxDataUID, sizeof(TxDataUID), "%012lx", (unsigned long)0x123456789ABC);
	TxDataUID[12] = '0'; // default STA

	while (1) {
		// Switch between station and AP mode of Wifi
		if(gpio_pin_get_dt(&button)) {
			if(!wifiPressed) {
				if(TxDataUID[12] == '0') {
					TxDataUID[12] = '1';
				} else {
					TxDataUID[12] = '0';
				}
				snprintf(rpiIP, sizeof(rpiIP), "%-14s", "Unknown");
				shifting = 0;
				wifiPressed = 1;
			}
		} else {
			wifiPressed = 0;
		}

		// Switch between displays if Display button is pressed
		if(gpio_pin_get_dt(&display_in)) {
			displayScreen++;
			if(displayScreen > 3) {
				displayScreen = 0;
			}
		}

		secondsAfterStart++;

		// Display showing CybICS string and IP
		if(0 == displayScreen) {
			snprintf(displayText, sizeof(displayText), "%-16s", "CybICS v1.1.2");
			Lcd_cursor(&lcd, 0, 0);
			Lcd_string(&lcd, displayText);
			snprintf(displayText, sizeof(displayText), "%16u", secondsAfterStart);
			Lcd_cursor(&lcd, 1, 0);
			Lcd_string(&lcd, displayText);
		}
		// Display WiFi configuration
		else if(1 == displayScreen) {
			if(TxDataUID[12] == '0') {
				snprintf(displayText, sizeof(displayText), "%-16s", "Wifi STA mode");
				Lcd_cursor(&lcd, 0, 0);
				Lcd_string(&lcd, displayText);
				snprintf(displayText, sizeof(displayText), "IP: %-12s", &rpiIP[shifting]);
				Lcd_cursor(&lcd, 1, 0);
				Lcd_string(&lcd, displayText);

				if(strlen(rpiIP) > 12) {
					shifting++;
				}
				if(shifting > 3) {
					shifting = 0;
				}
			} else if(TxDataUID[12] == '1') {
				snprintf(displayText, sizeof(displayText), "%-16s", "AP mode: cybics-");
				Lcd_cursor(&lcd, 0, 0);
				Lcd_string(&lcd, displayText);
				snprintf(displayText, sizeof(displayText), "%-16s", TxDataUID);
				displayText[12] = ' '; // removing the 1, which is not part of the UID
				Lcd_cursor(&lcd, 1, 0);
				Lcd_string(&lcd, displayText);
			} else {
				snprintf(displayText, sizeof(displayText), "%-16s", "WiFi error");
				Lcd_cursor(&lcd, 0, 0);
				Lcd_string(&lcd, displayText);
			}
		}
		// Display showing real pressure values
		else if(2 == displayScreen) {
			snprintf(displayText, sizeof(displayText), "%-16s", "Physical/real:  ");
			Lcd_cursor(&lcd, 0, 0);
			Lcd_string(&lcd, displayText);
			snprintf(displayText, sizeof(displayText), "GST:%03d HPT:%03d ", GSTpressure, HPTpressure);
			Lcd_cursor(&lcd, 1, 0);
			Lcd_string(&lcd, displayText);
		}
		// Display showing status
		else if(3 == displayScreen) {
			snprintf(displayText, sizeof(displayText), "%-16s", "Status:");
			Lcd_cursor(&lcd, 0, 0);
			Lcd_string(&lcd, displayText);
			if(BO_sen > 0) {
				snprintf(displayText, sizeof(displayText), "%-16s", "Danger! BlowOut");
			} else if((HPTpressure > 50) && (HPTpressure < 100) && SV_green) {
				snprintf(displayText, sizeof(displayText), "%-16s", "Operational");
			} else if((HPTpressure > 50) && (HPTpressure < 100)) {
				snprintf(displayText, sizeof(displayText), "%-16s", "SV closed");
			} else if(HPTpressure > 100) {
				snprintf(displayText, sizeof(displayText), "%-16s", "Pressure too high");
			} else if(HPTpressure <= 50) {
				snprintf(displayText, sizeof(displayText), "%-16s", "Pressure too low");
			}
			Lcd_cursor(&lcd, 1, 0);
			Lcd_string(&lcd, displayText);
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
	k_msleep(20);

	logging(LOG_DEB, "Starting thread_physical");

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

		/* Update TX Data */
		snprintf((char*)TxData, sizeof(TxData), "GST: %03d HPT: %03d", GSTpressure, HPTpressure);

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

	k_msleep(30);
	logging(LOG_DEB, "Starting thread_i2c");

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

	k_msleep(1);

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

	char statusMsg[50];
	char password[20];
	char input[2];
	uint8_t loggedIn = 0;
	uint8_t rxIndex = 0;
	uint8_t showMenu = 1;
	uint8_t passwordEntry = 0;

	k_msleep(1000);
	logging(LOG_DEB, "Starting thread_uart");

	while (1) {
		if (!loggedIn) {
			if (!passwordEntry) {
				logging(LOG_INF, "Please enter password:");
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
							logging(LOG_INF, "Login successful!");
							showMenu = 1;
						} else {
							logging(LOG_ERR, "Invalid password. Please try again.");
							passwordEntry = 0;
						}
					} else {
						rxIndex++;
					}
				}
			} else {
				logging(LOG_ERR, "Password too long. Please try again.");
				rxIndex = 0;
				memset(password, 0, sizeof(password));
				passwordEntry = 0;
			}
			k_msleep(10);
			continue;
		}

		if (showMenu) {
			logging(LOG_INF, "\r\n=== CybICS Menu ===");
			logging(LOG_INF, "1. System Status");
			logging(LOG_INF, "2. Display Flag");
			logging(LOG_INF, "3. System Controls");
			logging(LOG_INF, "4. Zephyr Stats");
			logging(LOG_INF, "5. MCU Information");
			logging(LOG_INF, "6. Help");
			logging(LOG_INF, "7. Logout");
			logging(LOG_INF, "Enter choice (1-7): ");
			showMenu = 0;
		}

		if (uart_poll_in(uart_dev, (unsigned char*)input) == 0) {
			switch(input[0]) {
				case MENU_STATUS:
					logging(LOG_INF, "\r\n=== System Status ===");
					snprintf(statusMsg, sizeof(statusMsg), "GST Pressure: %d", GSTpressure);
					logging(LOG_INF, statusMsg);
					snprintf(statusMsg, sizeof(statusMsg), "HPT Pressure: %d", HPTpressure);
					logging(LOG_INF, statusMsg);
					snprintf(statusMsg, sizeof(statusMsg), "Compressor: %s", C_on ? "ON" : "OFF");
					logging(LOG_INF, statusMsg);
					snprintf(statusMsg, sizeof(statusMsg), "System Valve: %s", SV_green ? "OPEN" : "CLOSED");
					logging(LOG_INF, statusMsg);
					snprintf(statusMsg, sizeof(statusMsg), "System Status: %s", S_green ? "OPERATIONAL" : "NOT OPERATIONAL");
					logging(LOG_INF, statusMsg);
					snprintf(statusMsg, sizeof(statusMsg), "Blow Out: %s", BO_sen ? "ACTIVE" : "INACTIVE");
					logging(LOG_INF, statusMsg);
					showMenu = 1;
					break;

				case MENU_FLAG:
					logging(LOG_INF, "\r\n=== CybICS Flag ===");
					logging(LOG_INF, "CybICS(U#RT)");
					showMenu = 1;
					break;

				case MENU_CONTROLS:
					logging(LOG_INF, "\r\n=== System Controls ===");
					logging(LOG_INF, "Current Status:");
					logging(LOG_INF, "----------------");
					snprintf(statusMsg, sizeof(statusMsg), "Compressor: %s", C_on ? "Running" : "Stopped");
					logging(LOG_INF, statusMsg);
					snprintf(statusMsg, sizeof(statusMsg), "System Valve: %s", SV_green ? "Open" : "Closed");
					logging(LOG_INF, statusMsg);
					showMenu = 1;
					break;

				case MENU_FREERTOS:
					logging(LOG_INF, "\r\n=== Zephyr Statistics ===");
					logging(LOG_INF, "Thread Statistics:");
					logging(LOG_INF, "----------------");
					// Zephyr thread stats would go here
					logging(LOG_INF, "System running on Zephyr RTOS");
					showMenu = 1;
					break;

				case MENU_MCU:
					logging(LOG_INF, "\r\n=== MCU Information ===");
					logging(LOG_INF, "STM32G070RB on Zephyr RTOS");
					showMenu = 1;
					break;

				case MENU_HELP:
					logging(LOG_INF, "\r\n=== Help ===");
					logging(LOG_INF, "1. System Status - Shows current system parameters");
					logging(LOG_INF, "2. Display Flag - Shows the CybICS flag");
					logging(LOG_INF, "3. System Controls - Shows control status");
					logging(LOG_INF, "4. Zephyr Stats - Shows Zephyr thread statistics");
					logging(LOG_INF, "5. MCU Information - Shows MCU info");
					logging(LOG_INF, "6. Help - Shows this help message");
					logging(LOG_INF, "7. Logout - Logs out of the system");
					showMenu = 1;
					break;

				case MENU_LOGOUT:
					loggedIn = 0;
					passwordEntry = 0;
					logging(LOG_INF, "\r\nLogged out successfully.");
					break;

				default:
					logging(LOG_ERR, "\r\nInvalid choice. Please try again.");
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

/* Main function */
int main(void)
{
	printk("CybICS Zephyr Port Starting...\n");

	/* Get device bindings */
	uart_dev = DEVICE_DT_GET(DT_NODELABEL(usart1));
	if (!device_is_ready(uart_dev)) {
		printk("UART device not ready\n");
		return -1;
	}

	i2c_dev = DEVICE_DT_GET(DT_NODELABEL(i2c1));
	if (!device_is_ready(i2c_dev)) {
		printk("I2C device not ready\n");
		return -1;
	}

	/* Configure GPIO pins as outputs */
	gpio_pin_configure_dt(&heartbeat_led, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&c_on_led, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&c_off_led, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&sv_red_led, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&sv_green_led, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&s_sen_pin, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&s_red_led, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&s_green_led, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&bo_sen_pin, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&bo_red_led, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&bo_green_led, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&gst_low_led, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&gst_normal_led, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&gst_full_led, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&hpt_empty_led, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&hpt_low_led, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&hpt_normal_led, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&hpt_high_led, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&hpt_critical_led, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&d_enable, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&d_rs, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&d_d4, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&d_d5, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&d_d6, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&d_d7, GPIO_OUTPUT_INACTIVE);

	/* Configure GPIO pins as inputs */
	gpio_pin_configure_dt(&c_sig, GPIO_INPUT);
	gpio_pin_configure_dt(&sv_sig, GPIO_INPUT);
	gpio_pin_configure_dt(&gst_sig, GPIO_INPUT);
	gpio_pin_configure_dt(&display_in, GPIO_INPUT);
	gpio_pin_configure_dt(&button, GPIO_INPUT);

	printk("CybICS initialization complete\n");

	/* Threads are auto-started by K_THREAD_DEFINE */
	return 0;
}
