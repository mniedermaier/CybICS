/*
 * Copyright (c) 2024 CybICS
 * SPDX-License-Identifier: Apache-2.0
 *
 * HD44780 LCD Driver for Zephyr - 4-bit mode
 */

#include "lcd_hd44780.h"
#include <zephyr/kernel.h>

/* Row offsets for 16x2 LCD */
static const uint8_t row_offsets[] = {0x00, 0x40};

/**
 * @brief Pulse the enable pin to latch data
 */
static void lcd_pulse_enable(struct lcd_hd44780 *lcd)
{
    gpio_pin_set_dt(lcd->en, 1);
    k_busy_wait(1);  /* Enable pulse width >450ns */
    gpio_pin_set_dt(lcd->en, 0);
    k_busy_wait(50); /* Commands need >37us to settle */
}

/**
 * @brief Write 4 bits to the LCD
 */
static void lcd_write_nibble(struct lcd_hd44780 *lcd, uint8_t nibble)
{
    gpio_pin_set_dt(lcd->d4, (nibble >> 0) & 0x01);
    gpio_pin_set_dt(lcd->d5, (nibble >> 1) & 0x01);
    gpio_pin_set_dt(lcd->d6, (nibble >> 2) & 0x01);
    gpio_pin_set_dt(lcd->d7, (nibble >> 3) & 0x01);
    lcd_pulse_enable(lcd);
}

/**
 * @brief Write a byte to the LCD (as two nibbles)
 */
static void lcd_write_byte(struct lcd_hd44780 *lcd, uint8_t data, bool rs)
{
    gpio_pin_set_dt(lcd->rs, rs ? 1 : 0);

    /* High nibble first */
    lcd_write_nibble(lcd, data >> 4);
    /* Then low nibble */
    lcd_write_nibble(lcd, data & 0x0F);
}

/**
 * @brief Send command to LCD
 */
static void lcd_command(struct lcd_hd44780 *lcd, uint8_t cmd)
{
    lcd_write_byte(lcd, cmd, false);
}

/**
 * @brief Send data to LCD
 */
static void lcd_data(struct lcd_hd44780 *lcd, uint8_t data)
{
    lcd_write_byte(lcd, data, true);
}

int lcd_init(struct lcd_hd44780 *lcd)
{
    /* Verify all GPIO devices are ready */
    if (!device_is_ready(lcd->rs->port) ||
        !device_is_ready(lcd->en->port) ||
        !device_is_ready(lcd->d4->port) ||
        !device_is_ready(lcd->d5->port) ||
        !device_is_ready(lcd->d6->port) ||
        !device_is_ready(lcd->d7->port)) {
        return -ENODEV;
    }

    /* Configure all pins as outputs */
    gpio_pin_configure_dt(lcd->rs, GPIO_OUTPUT_INACTIVE);
    gpio_pin_configure_dt(lcd->en, GPIO_OUTPUT_INACTIVE);
    gpio_pin_configure_dt(lcd->d4, GPIO_OUTPUT_INACTIVE);
    gpio_pin_configure_dt(lcd->d5, GPIO_OUTPUT_INACTIVE);
    gpio_pin_configure_dt(lcd->d6, GPIO_OUTPUT_INACTIVE);
    gpio_pin_configure_dt(lcd->d7, GPIO_OUTPUT_INACTIVE);

    /* Wait for LCD to power up (>40ms after Vcc rises to 2.7V) */
    k_msleep(50);

    /* Set RS low for commands */
    gpio_pin_set_dt(lcd->rs, 0);
    gpio_pin_set_dt(lcd->en, 0);

    /*
     * HD44780 initialization sequence for 4-bit mode
     * See HD44780 datasheet Figure 24
     */

    /* Step 1: Wait >15ms after Vcc rises to 4.5V (we already waited 50ms) */

    /* Step 2: Send 0x03 (Function Set: 8-bit mode) */
    lcd_write_nibble(lcd, 0x03);
    k_msleep(5);  /* Wait >4.1ms */

    /* Step 3: Send 0x03 again */
    lcd_write_nibble(lcd, 0x03);
    k_busy_wait(150);  /* Wait >100us */

    /* Step 4: Send 0x03 again */
    lcd_write_nibble(lcd, 0x03);
    k_busy_wait(150);

    /* Step 5: Send 0x02 to switch to 4-bit mode */
    lcd_write_nibble(lcd, 0x02);
    k_busy_wait(150);

    /* Now in 4-bit mode, can send full commands */

    /* Function Set: 4-bit mode, 2 lines, 5x8 font */
    lcd_command(lcd, LCD_CMD_FUNCTION_SET | LCD_2LINE);
    k_busy_wait(50);

    /* Display Control: Display off */
    lcd->display_control = 0;
    lcd_command(lcd, LCD_CMD_DISPLAY_CTRL | lcd->display_control);
    k_busy_wait(50);

    /* Clear Display */
    lcd_clear(lcd);

    /* Entry Mode Set: Increment cursor, no shift */
    lcd->display_mode = LCD_ENTRY_INCREMENT;
    lcd_command(lcd, LCD_CMD_ENTRY_MODE | lcd->display_mode);
    k_busy_wait(50);

    /* Display Control: Display on, cursor off, blink off */
    lcd->display_control = LCD_DISPLAY_ON;
    lcd_command(lcd, LCD_CMD_DISPLAY_CTRL | lcd->display_control);
    k_busy_wait(50);

    return 0;
}

void lcd_clear(struct lcd_hd44780 *lcd)
{
    lcd_command(lcd, LCD_CMD_CLEAR);
    k_msleep(2);  /* Clear command takes 1.52ms */
}

void lcd_home(struct lcd_hd44780 *lcd)
{
    lcd_command(lcd, LCD_CMD_HOME);
    k_msleep(2);  /* Home command takes 1.52ms */
}

void lcd_set_cursor(struct lcd_hd44780 *lcd, uint8_t row, uint8_t col)
{
    if (row >= LCD_ROWS) {
        row = LCD_ROWS - 1;
    }
    if (col >= LCD_COLS) {
        col = LCD_COLS - 1;
    }
    lcd_command(lcd, LCD_CMD_SET_DDRAM | (col + row_offsets[row]));
}

void lcd_print(struct lcd_hd44780 *lcd, const char *str)
{
    while (*str) {
        lcd_data(lcd, *str++);
    }
}

void lcd_putc(struct lcd_hd44780 *lcd, char c)
{
    lcd_data(lcd, c);
}

void lcd_display_on(struct lcd_hd44780 *lcd)
{
    lcd->display_control |= LCD_DISPLAY_ON;
    lcd_command(lcd, LCD_CMD_DISPLAY_CTRL | lcd->display_control);
}

void lcd_display_off(struct lcd_hd44780 *lcd)
{
    lcd->display_control &= ~LCD_DISPLAY_ON;
    lcd_command(lcd, LCD_CMD_DISPLAY_CTRL | lcd->display_control);
}

void lcd_create_char(struct lcd_hd44780 *lcd, uint8_t location, const uint8_t charmap[8])
{
    location &= 0x7;  /* Only 8 locations (0-7) */
    lcd_command(lcd, LCD_CMD_SET_CGRAM | (location << 3));
    for (int i = 0; i < 8; i++) {
        lcd_data(lcd, charmap[i]);
    }
    /* Return to DDRAM mode */
    lcd_command(lcd, LCD_CMD_SET_DDRAM);
}
