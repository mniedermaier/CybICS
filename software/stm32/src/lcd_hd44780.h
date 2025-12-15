/*
 * Copyright (c) 2024 CybICS
 * SPDX-License-Identifier: Apache-2.0
 *
 * HD44780 LCD Driver for Zephyr - 4-bit mode
 */

#ifndef LCD_HD44780_H
#define LCD_HD44780_H

#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>
#include <stdint.h>

/* LCD dimensions */
#define LCD_COLS 16
#define LCD_ROWS 2

/* HD44780 Commands */
#define LCD_CMD_CLEAR           0x01
#define LCD_CMD_HOME            0x02
#define LCD_CMD_ENTRY_MODE      0x04
#define LCD_CMD_DISPLAY_CTRL    0x08
#define LCD_CMD_SHIFT           0x10
#define LCD_CMD_FUNCTION_SET    0x20
#define LCD_CMD_SET_CGRAM       0x40
#define LCD_CMD_SET_DDRAM       0x80

/* Entry mode flags */
#define LCD_ENTRY_INCREMENT     0x02
#define LCD_ENTRY_SHIFT         0x01

/* Display control flags */
#define LCD_DISPLAY_ON          0x04
#define LCD_CURSOR_ON           0x02
#define LCD_BLINK_ON            0x01

/* Function set flags */
#define LCD_8BIT_MODE           0x10
#define LCD_2LINE               0x08
#define LCD_5x10_DOTS           0x04

/* LCD device structure */
struct lcd_hd44780 {
    const struct gpio_dt_spec *rs;
    const struct gpio_dt_spec *en;
    const struct gpio_dt_spec *d4;
    const struct gpio_dt_spec *d5;
    const struct gpio_dt_spec *d6;
    const struct gpio_dt_spec *d7;
    uint8_t display_control;
    uint8_t display_mode;
};

/**
 * @brief Initialize the LCD
 * @param lcd Pointer to LCD device structure
 * @return 0 on success, negative errno on failure
 */
int lcd_init(struct lcd_hd44780 *lcd);

/**
 * @brief Clear the display
 * @param lcd Pointer to LCD device structure
 */
void lcd_clear(struct lcd_hd44780 *lcd);

/**
 * @brief Return cursor to home position
 * @param lcd Pointer to LCD device structure
 */
void lcd_home(struct lcd_hd44780 *lcd);

/**
 * @brief Set cursor position
 * @param lcd Pointer to LCD device structure
 * @param row Row (0 or 1)
 * @param col Column (0-15)
 */
void lcd_set_cursor(struct lcd_hd44780 *lcd, uint8_t row, uint8_t col);

/**
 * @brief Print a string to the LCD
 * @param lcd Pointer to LCD device structure
 * @param str String to print
 */
void lcd_print(struct lcd_hd44780 *lcd, const char *str);

/**
 * @brief Print a single character
 * @param lcd Pointer to LCD device structure
 * @param c Character to print
 */
void lcd_putc(struct lcd_hd44780 *lcd, char c);

/**
 * @brief Turn display on
 * @param lcd Pointer to LCD device structure
 */
void lcd_display_on(struct lcd_hd44780 *lcd);

/**
 * @brief Turn display off
 * @param lcd Pointer to LCD device structure
 */
void lcd_display_off(struct lcd_hd44780 *lcd);

#endif /* LCD_HD44780_H */
