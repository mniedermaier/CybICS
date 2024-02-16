/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2023 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32g0xx_hal.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Exported types ------------------------------------------------------------*/
/* USER CODE BEGIN ET */

/* USER CODE END ET */

/* Exported constants --------------------------------------------------------*/
/* USER CODE BEGIN EC */

/* USER CODE END EC */

/* Exported macro ------------------------------------------------------------*/
/* USER CODE BEGIN EM */

/* USER CODE END EM */

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

/* USER CODE BEGIN EFP */

/* USER CODE END EFP */

/* Private defines -----------------------------------------------------------*/
#define ST_heartbeat_Pin GPIO_PIN_3
#define ST_heartbeat_GPIO_Port GPIOC
#define C_sig_Pin GPIO_PIN_0
#define C_sig_GPIO_Port GPIOA
#define SV_sig_Pin GPIO_PIN_1
#define SV_sig_GPIO_Port GPIOA
#define S_sen_Pin GPIO_PIN_2
#define S_sen_GPIO_Port GPIOA
#define BO_sen_Pin GPIO_PIN_3
#define BO_sen_GPIO_Port GPIOA
#define GST_sig_Pin GPIO_PIN_5
#define GST_sig_GPIO_Port GPIOA
#define D_enable_Pin GPIO_PIN_10
#define D_enable_GPIO_Port GPIOB
#define D_rs_Pin GPIO_PIN_11
#define D_rs_GPIO_Port GPIOB
#define D_d4_Pin GPIO_PIN_12
#define D_d4_GPIO_Port GPIOB
#define D_d5_Pin GPIO_PIN_13
#define D_d5_GPIO_Port GPIOB
#define D_d6_Pin GPIO_PIN_14
#define D_d6_GPIO_Port GPIOB
#define D_d7_Pin GPIO_PIN_15
#define D_d7_GPIO_Port GPIOB
#define Display_in_Pin GPIO_PIN_8
#define Display_in_GPIO_Port GPIOA
#define SV_red_Pin GPIO_PIN_12
#define SV_red_GPIO_Port GPIOA
#define SV_green_Pin GPIO_PIN_15
#define SV_green_GPIO_Port GPIOA
#define S_red_Pin GPIO_PIN_8
#define S_red_GPIO_Port GPIOC
#define S_green_Pin GPIO_PIN_9
#define S_green_GPIO_Port GPIOC
#define BO_green_Pin GPIO_PIN_0
#define BO_green_GPIO_Port GPIOD
#define BO_red_Pin GPIO_PIN_1
#define BO_red_GPIO_Port GPIOD
#define HPT_empty_Pin GPIO_PIN_2
#define HPT_empty_GPIO_Port GPIOD
#define HPT_low_Pin GPIO_PIN_3
#define HPT_low_GPIO_Port GPIOD
#define HPT_normal_Pin GPIO_PIN_4
#define HPT_normal_GPIO_Port GPIOD
#define HPT_high_Pin GPIO_PIN_5
#define HPT_high_GPIO_Port GPIOD
#define HPT_critical_Pin GPIO_PIN_6
#define HPT_critical_GPIO_Port GPIOD
#define C_off_Pin GPIO_PIN_3
#define C_off_GPIO_Port GPIOB
#define C_on_Pin GPIO_PIN_4
#define C_on_GPIO_Port GPIOB
#define GST_low_Pin GPIO_PIN_5
#define GST_low_GPIO_Port GPIOB
#define GST_normal_Pin GPIO_PIN_6
#define GST_normal_GPIO_Port GPIOB
#define GST_full_Pin GPIO_PIN_9
#define GST_full_GPIO_Port GPIOB
#define button_Pin GPIO_PIN_10
#define button_GPIO_Port GPIOC

/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
